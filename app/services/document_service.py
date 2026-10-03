import hashlib
from datetime import datetime, timezone
import logging
from app.infrastructure.postgres import postgres_client
from app.core.exceptions import RAGXException
from app.schemas.documents import DocumentMetadata
from app.ingestion.loaders.pdf_loader import PDFLoader
from app.ingestion.loaders.text_loader import TextLoader
from app.ingestion.loaders.markdown_loader import MarkdownLoader
from app.ingestion.cleaner import TextCleaner
from app.ingestion.chunker import DocumentChunker
from app.embeddings.sentence_transformer import embedding_service
from app.retrieval.qdrant_store import qdrant_store

logger = logging.getLogger(__name__)

class DocumentService:
    async def init_db(self):
        pool = postgres_client.pool
        if pool:
            async with pool.acquire() as conn:
                # Alter existing table if necessary (this assumes Postgres is okay with adding columns if they don't exist,
                # but ADD COLUMN IF NOT EXISTS requires Postgres 11+)
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS documents (
                        document_id VARCHAR PRIMARY KEY,
                        filename VARCHAR NOT NULL,
                        file_type VARCHAR NOT NULL,
                        file_hash VARCHAR NOT NULL,
                        chunk_count INTEGER NOT NULL,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        status VARCHAR NOT NULL
                    )
                """)
                try:
                    await conn.execute("ALTER TABLE documents ADD COLUMN tenant_id VARCHAR;")
                    await conn.execute("ALTER TABLE documents ADD COLUMN classification VARCHAR;")
                    await conn.execute("ALTER TABLE documents ADD COLUMN allowed_roles VARCHAR[];")
                    await conn.execute("ALTER TABLE documents ADD COLUMN allowed_users VARCHAR[];")
                except Exception:
                    pass # Columns probably already exist

                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS chunks (
                        chunk_id VARCHAR PRIMARY KEY,
                        document_id VARCHAR NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
                        tenant_id VARCHAR NOT NULL,
                        text TEXT NOT NULL,
                        fts_vector tsvector GENERATED ALWAYS AS (to_tsvector('english', text)) STORED
                    )
                """)
                await conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_chunks_fts ON chunks USING GIN(fts_vector);
                    CREATE INDEX IF NOT EXISTS idx_chunks_tenant ON chunks(tenant_id);
                """)

                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS tenant_metadata (
                        tenant_id VARCHAR PRIMARY KEY,
                        corpus_version BIGINT DEFAULT 1
                    )
                """)

                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS audit_events (
                        event_id VARCHAR PRIMARY KEY,
                        request_id VARCHAR,
                        timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
                        user_id VARCHAR NOT NULL,
                        tenant_id VARCHAR NOT NULL,
                        action VARCHAR NOT NULL,
                        document_ids VARCHAR[],
                        chunk_ids VARCHAR[],
                        status VARCHAR NOT NULL,
                        query_hash VARCHAR
                    )
                """)
                
                await conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_audit_tenant_id ON audit_events (tenant_id);
                    CREATE INDEX IF NOT EXISTS idx_audit_user_id ON audit_events (user_id);
                    CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_events (timestamp);
                """)

    async def get_corpus_version(self, tenant_id: str) -> int:
        pool = postgres_client.pool
        if not pool:
            return 1
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT corpus_version FROM tenant_metadata WHERE tenant_id = $1", tenant_id)
            if row:
                return row["corpus_version"]
            # Insert default
            await conn.execute("INSERT INTO tenant_metadata (tenant_id, corpus_version) VALUES ($1, 1) ON CONFLICT DO NOTHING", tenant_id)
            return 1

    async def increment_corpus_version(self, tenant_id: str) -> int:
        pool = postgres_client.pool
        if not pool:
            return 1
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO tenant_metadata (tenant_id, corpus_version)
                VALUES ($1, 2)
                ON CONFLICT (tenant_id) DO UPDATE SET corpus_version = tenant_metadata.corpus_version + 1
                RETURNING corpus_version
            """, tenant_id)
            return row["corpus_version"] if row else 1

    def _get_loader(self, filename: str):
        if filename.endswith(".pdf"):
            return PDFLoader()
        elif filename.endswith(".txt"):
            return TextLoader()
        elif filename.endswith(".md"):
            return MarkdownLoader()
        raise RAGXException(code="UNSUPPORTED_FILE", message=f"Unsupported file type: {filename}", status_code=400)

    async def upload_document(
        self, 
        filename: str, 
        content: bytes, 
        tenant_id: str, 
        classification: str, 
        allowed_roles: list, 
        allowed_users: list
    ):
        if len(content) > 25 * 1024 * 1024:
            raise RAGXException(code="FILE_TOO_LARGE", message="File exceeds maximum upload size", status_code=413)

        file_hash = hashlib.sha256(content).hexdigest()
        document_id = f"doc_{file_hash[:16]}"
        
        # Check if exists
        pool = postgres_client.pool
        if pool:
            async with pool.acquire() as conn:
                row = await conn.fetchrow("SELECT document_id FROM documents WHERE file_hash = $1 AND tenant_id = $2", file_hash, tenant_id)
                if row:
                    raise RAGXException(code="DUPLICATE_DOCUMENT", message="Document already indexed.", status_code=409)

        # Ingest
        loader = self._get_loader(filename)
        raw_doc = loader.load(content, filename, document_id)
        
        for p in raw_doc.pages:
            p.text = TextCleaner.clean(p.text)
            
        chunker = DocumentChunker()
        chunks = chunker.chunk_document(raw_doc)
        
        if not chunks:
            raise RAGXException(code="EMPTY_DOCUMENT", message="No text chunks generated from document.", status_code=400)
            
        # Embed and attach ACL metadata to chunks
        texts = [c.text for c in chunks]
        embeddings = embedding_service.embed_documents(texts)
        
        for c in chunks:
            if not hasattr(c, "metadata"):
                c.metadata = {}
            c.metadata["tenant_id"] = tenant_id
            c.metadata["classification"] = classification
            c.metadata["allowed_roles"] = allowed_roles
            c.metadata["allowed_users"] = allowed_users
            
        # Store Qdrant
        await qdrant_store.upsert_chunks(chunks, embeddings)
        
        # Store Neo4j Graph
        from app.services.graph_service import graph_service
        import asyncio
        
        graph_tasks = []
        for c in chunks:
            graph_tasks.append(graph_service.ingest_chunk(
                tenant_id=tenant_id,
                document_id=document_id,
                chunk_id=c.chunk_id,
                text=c.text
            ))
        
        if graph_tasks:
            # We don't fail the whole document if graph ingestion fails for a chunk
            await asyncio.gather(*graph_tasks, return_exceptions=True)
        
        # Store Postgres
        if pool:
            async with pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO documents (document_id, filename, file_type, file_hash, chunk_count, status, tenant_id, classification, allowed_roles, allowed_users)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                """, document_id, filename, raw_doc.file_type, file_hash, len(chunks), "indexed", tenant_id, classification, allowed_roles, allowed_users)
                
                # Insert chunks for Lexical Search (FTS)
                for c in chunks:
                    await conn.execute("""
                        INSERT INTO chunks (chunk_id, document_id, tenant_id, text)
                        VALUES ($1, $2, $3, $4)
                    """, c.chunk_id, document_id, tenant_id, c.text)
                
        await self.increment_corpus_version(tenant_id)
                
        return {
            "document_id": document_id,
            "filename": filename,
            "chunks_created": len(chunks),
            "status": "indexed"
        }

    async def get_documents(self):
        pool = postgres_client.pool
        if not pool:
            return []
        async with pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM documents ORDER BY created_at DESC")
            return [dict(r) for r in rows]

    async def get_document(self, document_id: str):
        pool = postgres_client.pool
        if not pool:
            raise RAGXException(code="DB_ERROR", message="Database unavailable", status_code=503)
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM documents WHERE document_id = $1", document_id)
            if not row:
                raise RAGXException(code="NOT_FOUND", message="Document not found", status_code=404)
            return dict(row)

    async def delete_document(self, document_id: str):
        pool = postgres_client.pool
        if pool:
            async with pool.acquire() as conn:
                await conn.execute("DELETE FROM documents WHERE document_id = $1", document_id)
                
        # To get tenant_id for the increment, we should fetch it first if we want, but since delete needs to be secure anyway
        # Actually it's easier to invalidate the cache by document_id
        from app.cache.semantic_cache import semantic_cache
        await semantic_cache.invalidate_by_document(document_id)
                
        await qdrant_store.delete_document_chunks(document_id)
        return {"status": "deleted"}

    async def update_permissions(self, document_id: str, tenant_id: str, classification: str, allowed_roles: list, allowed_users: list):
        pool = postgres_client.pool
        if not pool:
            raise RAGXException(code="DB_ERROR", message="Database unavailable", status_code=503)
            
        async with pool.acquire() as conn:
            result = await conn.execute("""
                UPDATE documents 
                SET classification = $1, allowed_roles = $2, allowed_users = $3, updated_at = CURRENT_TIMESTAMP
                WHERE document_id = $4 AND tenant_id = $5
            """, classification, allowed_roles, allowed_users, document_id, tenant_id)
            
            if result == "UPDATE 0":
                raise RAGXException(code="NOT_FOUND", message="Document not found or unauthorized", status_code=404)
                
        await qdrant_store.update_document_permissions(
            document_id=document_id,
            tenant_id=tenant_id,
            classification=classification,
            allowed_roles=allowed_roles,
            allowed_users=allowed_users
        )
        
        await self.increment_corpus_version(tenant_id)
        from app.cache.semantic_cache import semantic_cache
        await semantic_cache.invalidate_by_document(document_id)
        
        return {"status": "updated"}

document_service = DocumentService()
