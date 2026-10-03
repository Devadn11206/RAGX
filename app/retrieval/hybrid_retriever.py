import asyncio
from typing import List, Dict, Set, Any
from app.security.models import User
from app.core.config import settings
from app.retrieval.base import BaseRetriever, RetrievalResult
from app.retrieval.vector_retriever import vector_retriever
from app.retrieval.lexical_retriever import lexical_retriever
from app.retrieval.graph_retriever import graph_retriever
from app.rag.query_analyzer import query_analyzer
from app.embeddings.sentence_transformer import embedding_service
import logging

logger = logging.getLogger(__name__)

class HybridRetriever(BaseRetriever):
    async def retrieve(self, query: str, user: User, top_k: int, mode: str = "auto") -> List[RetrievalResult]:
        if not settings.HYBRID_RETRIEVAL_ENABLED:
            return await vector_retriever.retrieve(query, user, top_k)
            
        methods_to_use = []
        entities = []
        
        if mode == "auto":
            analysis = query_analyzer.analyze(query)
            methods_to_use = analysis.retrieval_methods
            entities = analysis.entities
            logger.info(f"Hybrid Auto Routing selected methods: {methods_to_use}")
        else:
            methods_to_use = mode.split(",")
            
        tasks = []
        task_names = []
        
        if "vector" in methods_to_use:
            tasks.append(vector_retriever.retrieve(query, user, settings.VECTOR_TOP_K))
            task_names.append("vector")
        
        if "lexical" in methods_to_use:
            tasks.append(lexical_retriever.retrieve(query, user, settings.LEXICAL_TOP_K))
            task_names.append("lexical")
            
        if "graph" in methods_to_use:
            tasks.append(graph_retriever.retrieve(query, user, settings.GRAPH_TOP_K, entities=entities))
            task_names.append("graph")
            
        if not tasks:
            tasks.append(vector_retriever.retrieve(query, user, settings.VECTOR_TOP_K))
            task_names.append("vector")
            
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Merge results with RRF (Reciprocal Rank Fusion)
        rrf_scores = {}
        merged_chunks = {}
        
        for i, res_list in enumerate(results):
            if isinstance(res_list, Exception):
                logger.error(f"Retriever {task_names[i]} failed: {res_list}")
                continue
                
            method_name = task_names[i]
            # Assumes res_list is already sorted by the underlying retriever
            for rank, item in enumerate(res_list):
                score = 1.0 / (settings.RRF_K + rank + 1)
                
                if item.chunk_id in rrf_scores:
                    rrf_scores[item.chunk_id] += score
                    # Aggregate methods
                    existing_methods = set(merged_chunks[item.chunk_id].retrieval_method.split(","))
                    existing_methods.add(method_name)
                    merged_chunks[item.chunk_id].retrieval_method = ",".join(list(existing_methods))
                    
                    if item.graph_evidence:
                        merged_chunks[item.chunk_id].graph_evidence = item.graph_evidence
                else:
                    rrf_scores[item.chunk_id] = score
                    item.retrieval_method = method_name
                    merged_chunks[item.chunk_id] = item
                    
        # Sort by RRF score initially
        fused_results = list(merged_chunks.values())
        for res in fused_results:
            res.score = rrf_scores[res.chunk_id]
            
        fused_results.sort(key=lambda x: x.score, reverse=True)
        
        # 5. Reranking Phase 10
        from app.reranking.service import reranking_engine
        
        final_results, metadata = await reranking_engine.rerank(query, fused_results)
        
        # We can attach metadata to the first result or a class state, but for now we'll 
        # just return the list. The RagService can extract the metadata if we return a tuple,
        # but to keep the interface `retrieve -> List[RetrievalResult]` clean, we'll store it.
        self.last_rerank_metadata = metadata
        
        return final_results

    async def retrieve_detailed_breakdown(self, query: str, user: User) -> Dict[str, Any]:
        analysis = query_analyzer.analyze(query)
        entities = analysis.entities
        
        vector_res = await vector_retriever.retrieve(query, user, settings.VECTOR_TOP_K)
        lexical_res = await lexical_retriever.retrieve(query, user, settings.LEXICAL_TOP_K)
        graph_res = await graph_retriever.retrieve(query, user, settings.GRAPH_TOP_K, entities=entities)
        
        rrf_scores = {}
        merged_chunks = {}
        
        for method_name, res_list in [("vector", vector_res), ("lexical", lexical_res), ("graph", graph_res)]:
            for rank, item in enumerate(res_list):
                score = 1.0 / (settings.RRF_K + rank + 1)
                if item.chunk_id in rrf_scores:
                    rrf_scores[item.chunk_id] += score
                    existing_methods = set(merged_chunks[item.chunk_id].retrieval_method.split(","))
                    existing_methods.add(method_name)
                    merged_chunks[item.chunk_id].retrieval_method = ",".join(list(existing_methods))
                    if item.graph_evidence:
                        merged_chunks[item.chunk_id].graph_evidence = item.graph_evidence
                else:
                    rrf_scores[item.chunk_id] = score
                    item.retrieval_method = method_name
                    merged_chunks[item.chunk_id] = item
                    
        fused = list(merged_chunks.values())
        for res in fused:
            res.score = rrf_scores[res.chunk_id]
        fused.sort(key=lambda x: x.score, reverse=True)
        
        from app.reranking.service import reranking_engine
        final_results, metadata = await reranking_engine.rerank(query, fused)
        
        return {
            "query": query,
            "vector_candidates": [r.dict() for r in vector_res],
            "lexical_candidates": [r.dict() for r in lexical_res],
            "graph_candidates": [r.dict() for r in graph_res],
            "fused_candidates": [r.dict() for r in fused],
            "reranked_candidates": [r.dict() for r in final_results],
            "rerank_metadata": metadata
        }

hybrid_retriever = HybridRetriever()
