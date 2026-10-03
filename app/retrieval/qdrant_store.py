import logging
import uuid
from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models
from app.core.config import settings
from app.core.exceptions import RAGXException
from app.embeddings.sentence_transformer import embedding_service
from app.infrastructure.qdrant import qdrant_client

logger = logging.getLogger(__name__)

class QdrantStore:
    def __init__(self):
        self.collection_name = settings.QDRANT_COLLECTION

    async def initialize_collection(self):
        client = qdrant_client.client
        if not client:
            return
            
        try:
            exists = await client.collection_exists(self.collection_name)
            if not exists:
                logger.info(f"Creating Qdrant collection: {self.collection_name}")
                embedding_service.initialize()
                await client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=embedding_service.dimension,
                        distance=models.Distance.COSINE
                    )
                )
                await client.create_payload_index(self.collection_name, "document_id", field_schema="keyword")
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant collection: {str(e)}")

    async def upsert_chunks(self, chunks: list, embeddings: list):
        client = qdrant_client.client
        points = []
        for chunk, embedding in zip(chunks, embeddings):
            metadata = getattr(chunk, "metadata", {})
            tenant_id = metadata.get("tenant_id")
            classification = metadata.get("classification")
            
            # INGESTION SECURITY INVARIANT
            if not tenant_id or not chunk.document_id or not classification:
                logger.error(f"SECURITY INVARIANT FAILED: Missing mandatory metadata for chunk {chunk.chunk_id}")
                raise RAGXException(code="INVARIANT_FAILED", message="Missing mandatory security metadata in chunk", status_code=500)
                
            points.append(
                models.PointStruct(
                    id=str(uuid.uuid5(uuid.NAMESPACE_OID, chunk.chunk_id)),
                    vector=embedding,
                    payload={
                        "document_id": chunk.document_id,
                        "chunk_id": chunk.chunk_id,
                        "filename": chunk.filename,
                        "chunk_index": chunk.chunk_index,
                        "page_number": chunk.page_number,
                        "text": chunk.text,
                        "tenant_id": tenant_id,
                        "classification": classification,
                        "allowed_roles": metadata.get("allowed_roles", []),
                        "allowed_users": metadata.get("allowed_users", [])
                    }
                )
            )
        
        await client.upsert(
            collection_name=self.collection_name,
            points=points
        )

    async def update_document_permissions(self, document_id: str, tenant_id: str, classification: str, allowed_roles: list, allowed_users: list):
        client = qdrant_client.client
        
        # We need to retrieve all chunks for this document first to update their payload
        # Qdrant client doesn't have an update payload by filter directly in all versions, 
        # but modern versions have `set_payload`. Let's use `set_payload` with points_selector.
        await client.set_payload(
            collection_name=self.collection_name,
            payload={
                "classification": classification,
                "allowed_roles": allowed_roles,
                "allowed_users": allowed_users
            },
            points=models.Filter(
                must=[
                    models.FieldCondition(
                        key="document_id",
                        match=models.MatchValue(value=document_id)
                    ),
                    models.FieldCondition(
                        key="tenant_id",
                        match=models.MatchValue(value=tenant_id)
                    )
                ]
            )
        )

    async def delete_document_chunks(self, document_id: str):
        client = qdrant_client.client
        await client.delete(
            collection_name=self.collection_name,
            points_selector=models.Filter(
                must=[
                    models.FieldCondition(
                        key="document_id",
                        match=models.MatchValue(value=document_id)
                    )
                ]
            )
        )

qdrant_store = QdrantStore()
