from typing import List
from app.infrastructure.postgres import postgres_client
from app.core.config import settings
from app.security.models import User
from app.security.acl import verify_chunk_acl
from app.audit.audit_service import audit_service
from app.retrieval.base import BaseRetriever, RetrievalResult
import logging

logger = logging.getLogger(__name__)

class LexicalRetriever(BaseRetriever):
    async def retrieve(self, query: str, user: User, top_k: int) -> List[RetrievalResult]:
        if not postgres_client.pool:
            await postgres_client.connect()
            
        if not postgres_client.pool:
            logger.error("Postgres pool not initialized for lexical search")
            return []
            
        filtered_results = []
        try:
            async with postgres_client.pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT c.chunk_id, c.document_id, c.tenant_id, c.text, d.filename,
                           d.classification, d.allowed_roles, d.allowed_users,
                           ts_rank(c.fts_vector, plainto_tsquery('english', $1)) as rank
                    FROM chunks c
                    JOIN documents d ON c.document_id = d.document_id
                    WHERE c.tenant_id = $2 AND c.fts_vector @@ plainto_tsquery('english', $1)
                    ORDER BY rank DESC
                    LIMIT $3
                """, query, user.tenant_id, top_k)
                
                for row in rows:
                    payload = {
                        "chunk_id": row["chunk_id"],
                        "document_id": row["document_id"],
                        "tenant_id": row["tenant_id"],
                        "classification": row["classification"],
                        "allowed_roles": row["allowed_roles"],
                        "allowed_users": row["allowed_users"]
                    }
                    
                    if not verify_chunk_acl(user, payload):
                        await audit_service.log_event(
                            request_id="REQ",
                            user_id=user.user_id,
                            tenant_id=user.tenant_id,
                            action="security_violation",
                            status="blocked",
                            chunk_ids=[row["chunk_id"]],
                            document_ids=[row["document_id"]]
                        )
                        continue
                        
                    filtered_results.append(RetrievalResult(
                        chunk_id=row["chunk_id"],
                        document_id=row["document_id"],
                        text=row["text"],
                        filename=row["filename"],
                        page_number=1,
                        score=float(row["rank"]),
                        retrieval_method="lexical"
                    ))
        except Exception as e:
            logger.error(f"Postgres Lexical search failed: {e}")
            return []
            
        return filtered_results

lexical_retriever = LexicalRetriever()
