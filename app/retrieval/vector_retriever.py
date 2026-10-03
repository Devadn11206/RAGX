from typing import List
from app.infrastructure.qdrant import qdrant_client
from app.core.config import settings
from app.embeddings.sentence_transformer import embedding_service
from app.security.models import User
from app.security.acl import build_acl_filter, verify_chunk_acl
from app.audit.audit_service import audit_service
from app.retrieval.base import BaseRetriever, RetrievalResult
import logging

logger = logging.getLogger(__name__)

class VectorRetriever(BaseRetriever):
    def __init__(self):
        self.collection_name = settings.QDRANT_COLLECTION

    async def retrieve(self, query: str, user: User, top_k: int) -> List[RetrievalResult]:
        query_vector = embedding_service.embed_query(query)
        acl_filter = build_acl_filter(user)
        
        try:
            results = await qdrant_client.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=acl_filter,
                limit=top_k,
                with_payload=True
            )
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []
            
        threshold = settings.MIN_RETRIEVAL_SCORE
        filtered_results = []
        for hit in results:
            if hit.score >= threshold:
                if not verify_chunk_acl(user, hit.payload):
                    await audit_service.log_event(
                        request_id="REQ",
                        user_id=user.user_id,
                        tenant_id=user.tenant_id,
                        action="security_violation",
                        status="blocked",
                        chunk_ids=[hit.payload.get("chunk_id")],
                        document_ids=[hit.payload.get("document_id")]
                    )
                    continue
                    
                filtered_results.append(RetrievalResult(
                    chunk_id=hit.payload.get("chunk_id"),
                    document_id=hit.payload.get("document_id"),
                    text=hit.payload.get("text"),
                    filename=hit.payload.get("filename"),
                    page_number=hit.payload.get("page_number"),
                    score=hit.score,
                    retrieval_method="vector"
                ))
                
        return filtered_results

vector_retriever = VectorRetriever()
