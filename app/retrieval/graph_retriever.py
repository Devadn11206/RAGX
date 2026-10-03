from typing import List, Dict, Any
from app.services.graph_service import graph_service
from app.security.models import User
from app.security.acl import verify_chunk_acl
from app.retrieval.base import BaseRetriever, RetrievalResult
from app.infrastructure.qdrant import qdrant_client
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class GraphRetriever(BaseRetriever):
    async def retrieve(self, query: str, user: User, top_k: int, entities: List[str] = None) -> List[RetrievalResult]:
        if not entities:
            from app.rag.query_analyzer import query_analyzer
            analysis = query_analyzer.analyze(query)
            entities = analysis.entities
            
        if not entities:
            return []
            
        graph_results = await graph_service.hybrid_search(user.tenant_id, entities)
        if not graph_results:
            return []
            
        # De-duplicate chunks locally
        unique_chunk_ids = list(set([r["chunk_id"] for r in graph_results]))
        
        filtered_results = []
        try:
            q_res = await qdrant_client.client.retrieve(
                collection_name=settings.QDRANT_COLLECTION,
                ids=unique_chunk_ids,
                with_payload=True
            )
            for point in q_res:
                if not verify_chunk_acl(user, point.payload):
                    continue
                    
                chunk_id = point.payload.get("chunk_id")
                relation = next((r for r in graph_results if r["chunk_id"] == chunk_id), None)
                evidence = relation["evidence"] if relation else ""
                
                filtered_results.append(RetrievalResult(
                    chunk_id=chunk_id,
                    document_id=point.payload.get("document_id"),
                    text=point.payload.get("text"),
                    filename=point.payload.get("filename"),
                    page_number=point.payload.get("page_number"),
                    score=1.0, # Static high score for graph prior to RRF
                    retrieval_method="graph",
                    graph_evidence=evidence
                ))
        except Exception as e:
            logger.error(f"Graph chunk payload fetch failed: {e}")
            
        return filtered_results[:top_k]

graph_retriever = GraphRetriever()
