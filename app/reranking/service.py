import asyncio
import logging
from typing import List, Dict, Any, Tuple
from app.core.config import settings
from app.retrieval.base import RetrievalResult
from app.reranking.cross_encoder import local_cross_encoder_reranker
from app.reranking.scoring import MMRSelector
from app.rag.query_analyzer import query_analyzer

logger = logging.getLogger(__name__)

class RerankingService:
    async def rerank(self, query: str, candidates: List[RetrievalResult]) -> Tuple[List[RetrievalResult], Dict[str, Any]]:
        metadata = {
            "enabled": settings.RERANKING_ENABLED,
            "model": settings.RERANKER_MODEL,
            "candidate_count": len(candidates),
            "final_count": 0,
            "latency_ms": 0,
            "skipped": False,
            "timeout": False,
            "error": None
        }
        
        if not settings.RERANKING_ENABLED or not candidates:
            final_cands = self._apply_diversity_and_limit(sorted(candidates, key=lambda x: x.score, reverse=True))
            metadata["final_count"] = len(final_cands)
            return final_cands, metadata
            
        # 1. Adaptive Reranking Check
        if settings.ADAPTIVE_RERANKING_ENABLED:
            analysis = query_analyzer.analyze(query)
            if analysis.intent == "SIMPLE" and candidates[0].score > 0.90:
                logger.info("Adaptive Reranking: Skipping due to high confidence on simple query.")
                final_cands = self._apply_diversity_and_limit(sorted(candidates, key=lambda x: x.score, reverse=True))
                metadata["skipped"] = True
                metadata["final_count"] = len(final_cands)
                return final_cands, metadata

        # 2. Reranker Execution with Timeout
        import time
        start = time.time()
        
        try:
            # We enforce timeout
            timeout_sec = settings.RERANK_TIMEOUT_MS / 1000.0
            
            if settings.RERANKER_PROVIDER == "local_cross_encoder":
                reranker = local_cross_encoder_reranker
            else:
                reranker = local_cross_encoder_reranker # Fallback
                
            reranked_candidates = await asyncio.wait_for(
                reranker.rerank(query, candidates, top_k=settings.RERANK_CANDIDATE_K),
                timeout=timeout_sec
            )
        except asyncio.TimeoutError:
            logger.error(f"Reranking timeout after {settings.RERANK_TIMEOUT_MS}ms")
            metadata["timeout"] = True
            reranked_candidates = sorted(candidates, key=lambda x: x.score, reverse=True)
        except Exception as e:
            logger.error(f"Reranking engine error: {e}")
            metadata["error"] = str(e)
            reranked_candidates = sorted(candidates, key=lambda x: x.score, reverse=True)
            
        # 3. Selection Strategy
        if settings.RERANK_SELECTION == "mmr":
            selected_candidates = MMRSelector.select(query, reranked_candidates, top_k=settings.RERANK_CANDIDATE_K)
        else:
            selected_candidates = sorted(reranked_candidates, key=lambda x: x.final_score if hasattr(x, 'final_score') and x.final_score is not None else x.score, reverse=True)
            
        # 4. Final Context Constraints (Diversity + Top K limit)
        final_candidates = self._apply_diversity_and_limit(selected_candidates)
        
        metadata["latency_ms"] = int((time.time() - start) * 1000)
        metadata["final_count"] = len(final_candidates)
        
        return final_candidates, metadata

    def _apply_diversity_and_limit(self, candidates: List[RetrievalResult]) -> List[RetrievalResult]:
        doc_counts = {}
        diverse_results = []
        for res in candidates:
            count = doc_counts.get(res.document_id, 0)
            if count < settings.MAX_CHUNKS_PER_DOCUMENT:
                diverse_results.append(res)
                doc_counts[res.document_id] = count + 1
                
            if len(diverse_results) >= settings.MAX_CONTEXT_CHUNKS:
                break
                
        return diverse_results

reranking_engine = RerankingService()
