from typing import List, Dict, Any
from app.infrastructure.qdrant import qdrant_client
from app.core.config import settings
from app.embeddings.sentence_transformer import embedding_service
from qdrant_client.http import models
from app.security.models import User
from app.security.acl import build_acl_filter, verify_chunk_acl
from app.audit.audit_service import audit_service
import uuid

class Retriever:
    def __init__(self):
        self.collection_name = settings.QDRANT_COLLECTION

    async def retrieve(self, query: str, user: User, top_k: int = None) -> List[Dict[str, Any]]:
        top_k = top_k or settings.RAG_TOP_K
        query_vector = embedding_service.embed_query(query)
        
        acl_filter = build_acl_filter(user)
        
        results = await qdrant_client.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            query_filter=acl_filter,
            limit=top_k,
            with_payload=True
        )
        
        # Filter by threshold and Defense-in-depth check
        threshold = settings.MIN_RETRIEVAL_SCORE
        filtered_results = []
        seen_chunk_ids = set()
        
        for hit in results:
            if hit.score >= threshold:
                # Defense in depth
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
                    
                chunk_id = hit.payload.get("chunk_id")
                seen_chunk_ids.add(chunk_id)
                filtered_results.append({
                    "chunk_id": chunk_id,
                    "document_id": hit.payload.get("document_id"),
                    "text": hit.payload.get("text"),
                    "filename": hit.payload.get("filename"),
                    "page_number": hit.payload.get("page_number"),
                    "score": hit.score,
                    "retrieval_method": "vector"
                })

        # --- Phase 8: Graph Retrieval ---
        from app.rag.query_analyzer import query_analyzer
        from app.services.graph_service import graph_service
        
        analysis = query_analyzer.analyze(query)
        graph_used = False
        
        if analysis.is_multi_hop and analysis.entities:
            graph_used = True
            graph_results = await graph_service.hybrid_search(user.tenant_id, analysis.entities)
            
            # Since graph chunks don't have full metadata in the Neo4j payload, we can fetch their metadata from Vector DB 
            # or just append them directly if we assume they exist. For citations we need document_id and filename.
            # Ideally we fetch the missing payload from Qdrant by chunk_id.
            
            if graph_results:
                graph_chunk_ids = [r["chunk_id"] for r in graph_results if r["chunk_id"] not in seen_chunk_ids]
                if graph_chunk_ids:
                    # Fetch full metadata from Qdrant for security verification & citations
                    try:
                        q_res = await qdrant_client.client.retrieve(
                            collection_name=self.collection_name,
                            ids=graph_chunk_ids,
                            with_payload=True
                        )
                        for point in q_res:
                            # Defense in depth for graph chunks
                            if not verify_chunk_acl(user, point.payload):
                                continue
                                
                            chunk_id = point.payload.get("chunk_id")
                            seen_chunk_ids.add(chunk_id)
                            # Find evidence relation for this chunk
                            relation = next((r for r in graph_results if r["chunk_id"] == chunk_id), None)
                            evidence = relation["evidence"] if relation else ""
                            
                            # Give graph results a static high score to prioritize them
                            filtered_results.append({
                                "chunk_id": chunk_id,
                                "document_id": point.payload.get("document_id"),
                                "text": point.payload.get("text"),
                                "filename": point.payload.get("filename"),
                                "page_number": point.payload.get("page_number"),
                                "score": 0.95, 
                                "retrieval_method": "graph",
                                "graph_evidence": evidence
                            })
                    except Exception as e:
                        print(f"Error fetching graph chunk payload from qdrant: {e}")
                        
        # Sort combined results by score
        filtered_results = sorted(filtered_results, key=lambda x: x["score"], reverse=True)
                
        return filtered_results, graph_used
