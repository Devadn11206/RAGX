import time
import logging
from app.retrieval.hybrid_retriever import hybrid_retriever
from app.rag.context import ContextBuilder
from app.llm.gemini import llm_client
from app.llm.prompts import RAG_SYSTEM_PROMPT
from app.schemas.query import QueryResponse
from app.security.models import User
from app.audit.audit_service import audit_service
from app.cache.semantic_cache import semantic_cache
from app.services.document_service import document_service
from app.embeddings.sentence_transformer import embedding_service
from app.telemetry.service import telemetry_service

logger = logging.getLogger(__name__)

class RagService:
    def __init__(self):
        self.retriever = hybrid_retriever

    def _is_personalized(self, query: str) -> bool:
        q = " " + query.lower() + " "
        personal = [" my salary", " my documents", " my pending", " what is my ", " my leave "]
        return any(p in q for p in personal)

    async def process_query(self, query: str, user: User, top_k: int = None, mode: str = "auto", is_test_run: bool = False) -> QueryResponse:
        start_time = time.time()
        request_id = telemetry_service.start_trace(query, user.tenant_id, user.user_id, is_test_run)
        corpus_version = await document_service.get_corpus_version(user.tenant_id)
        
        is_personalized = self._is_personalized(query)
        
        if not is_personalized:
            # 1. Exact Cache Lookup
            exact_hit = await semantic_cache.get_exact(query, user, corpus_version)
            if exact_hit:
                latency = int((time.time() - start_time) * 1000)
                await audit_service.log_event(request_id, user.user_id, user.tenant_id, "query_cache", "success", [s["document_id"] for s in exact_hit["citations"]], [], query_hash="EXACT_HIT")
                telemetry_service.complete_trace(request_id, latency, "SUCCESS")
                return QueryResponse(
                    query=query, 
                    answer=exact_hit["answer"], 
                    sources=exact_hit["citations"], 
                    retrieval={"top_k": top_k or 5, "results_returned": len(exact_hit["citations"]), "cache_type": "EXACT_HIT", "latency_ms": latency}
                )

            # 2. Semantic Cache Lookup
            normalized_query = semantic_cache._normalize_query(query)
            query_vector = embedding_service.embed_query(normalized_query)
            
            semantic_hit = await semantic_cache.get_semantic(query, user, query_vector, corpus_version)
            if semantic_hit:
                latency = int((time.time() - start_time) * 1000)
                await audit_service.log_event(request_id, user.user_id, user.tenant_id, "query_cache", "success", [s["document_id"] for s in semantic_hit["citations"]], [], query_hash="SEMANTIC_HIT")
                telemetry_service.complete_trace(request_id, latency, "SUCCESS")
                return QueryResponse(
                    query=query, 
                    answer=semantic_hit["answer"], 
                    sources=semantic_hit["citations"], 
                    retrieval={"top_k": top_k or 5, "results_returned": len(semantic_hit["citations"]), "cache_type": "SEMANTIC_HIT", "latency_ms": latency}
                )
        else:
            # For logging/timing, we still embed to keep flow consistent or skip embedding.
            normalized_query = semantic_cache._normalize_query(query)
            query_vector = embedding_service.embed_query(normalized_query)

        # 3. Normal RAG Pipeline
        results = await self.retriever.retrieve(query, user, top_k=top_k, mode=mode)
        graph_used = any("graph" in r.retrieval_method for r in results) if results else False
        vector_used = any("vector" in r.retrieval_method for r in results) if results else False
        lexical_used = any("lexical" in r.retrieval_method for r in results) if results else False
        
        reranking_metadata = getattr(self.retriever, "last_rerank_metadata", None)
        
        router_tier = None
        escalated = False
        estimated_cost = 0.0
        provider = None
        fallback_used = False
        fallback_reason = None
        
        if not results:
            answer = "I couldn't find enough information in the provided documents to answer this question."
            sources = []
        else:
            context = ContextBuilder.build([r.dict() for r in results])
            # Add Graph Evidence directly if available in results
            for res in results:
                if res.graph_evidence:
                    context += f"\nGraph Relation Evidence: {res.graph_evidence}"
                    
            prompt = RAG_SYSTEM_PROMPT.format(context=context, question=query)
            
            from app.router.cost_router import cost_router
            from app.llm.orchestrator import llm_orchestrator
            
            routing_decision = cost_router.route(query, results)
            router_tier = routing_decision.tier
            
            # Initial generation via orchestrator
            llm_res = llm_orchestrator.generate(prompt, model_name=routing_decision.model, request_id=request_id, is_test_run=is_test_run)
            
            # 3.5 Quality Check & Escalation
            if not cost_router.evaluate_quality(llm_res.content):
                escalated_decision = cost_router.escalate(routing_decision)
                if escalated_decision:
                    logger.info(f"Escalating query: {query}")
                    routing_decision = escalated_decision
                    router_tier = routing_decision.tier
                    escalated = True
                    # Re-generate with escalated model
                    esc_res = llm_orchestrator.generate(prompt, model_name=routing_decision.model, request_id=request_id, is_test_run=is_test_run)
                    llm_res.content = esc_res.content
                    llm_res.estimated_cost += esc_res.estimated_cost
                    llm_res.provider = esc_res.provider
                    llm_res.fallback_used = esc_res.fallback_used
                    llm_res.fallback_reason = esc_res.fallback_reason
            
            answer = llm_res.content
            estimated_cost = llm_res.estimated_cost
            provider = llm_res.provider
            fallback_used = llm_res.fallback_used
            fallback_reason = llm_res.fallback_reason
            
            sources = []
            for hit in results:
                sources.append({
                    "document_id": hit.document_id,
                    "chunk_id": hit.chunk_id,
                    "filename": hit.filename,
                    "page_number": hit.page_number,
                    "score": hit.score,
                    "retrieval_method": hit.retrieval_method
                })
        
        await audit_service.log_event(
            request_id=request_id,
            user_id=user.user_id,
            tenant_id=user.tenant_id,
            action="query",
            status="success",
            document_ids=[s["document_id"] for s in sources],
            chunk_ids=[s["chunk_id"] for s in sources]
        )
        
        # 4. Cache Store (don't cache errors)
        if results and not is_personalized and provider != "none":
            await semantic_cache.store(
                query=query,
                query_vector=query_vector,
                answer=answer,
                citations=sources,
                user=user,
                corpus_version=corpus_version,
                source_document_ids=list(set([s["document_id"] for s in sources]))
            )
            
        latency = int((time.time() - start_time) * 1000)
        cache_type = "SECURITY_REJECTED" if is_personalized else "MISS"
        
        telemetry_service.complete_trace(request_id, latency, "SUCCESS")
                
        return QueryResponse(
            query=query,
            answer=answer,
            sources=sources,
            retrieval={
                "request_id": request_id,
                "top_k": top_k or 5,
                "results_returned": len(results),
                "cache_type": cache_type,
                "latency_ms": latency,
                "router_tier": router_tier,
                "escalated": escalated,
                "estimated_cost": estimated_cost,
                "provider": provider,
                "model": routing_decision.model if 'routing_decision' in locals() and routing_decision else None,
                "fallback_used": fallback_used,
                "fallback_reason": fallback_reason,
                "graph_used": graph_used,
                "vector_used": vector_used,
                "lexical_used": lexical_used
            },
            reranking=reranking_metadata
        )

rag_service = RagService()
