import math
from typing import List
from app.retrieval.base import RetrievalResult
from app.embeddings.sentence_transformer import embedding_service
import numpy as np
from numpy.linalg import norm

class ScoreNormalizer:
    @staticmethod
    def sigmoid(score: float) -> float:
        return 1.0 / (1.0 + math.exp(-score))
        
    @staticmethod
    def minmax(scores: List[float]) -> List[float]:
        if not scores:
            return []
        min_s = min(scores)
        max_s = max(scores)
        if min_s == max_s:
            return [0.5 for _ in scores]
        return [(s - min_s) / (max_s - min_s) for s in scores]

class MMRSelector:
    @staticmethod
    def select(query: str, candidates: List[RetrievalResult], top_k: int, lambda_param: float = 0.5) -> List[RetrievalResult]:
        """
        Maximal Marginal Relevance selection.
        Prioritizes a combination of relevance to the query (final_score) and novelty compared to already selected chunks.
        """
        if not candidates or top_k <= 0:
            return []
            
        # We need embeddings to compute redundancy (similarity between chunks)
        # We can use the existing embedding_service which is loaded
        chunk_texts = [c.text for c in candidates]
        try:
            query_emb = np.array(embedding_service.embed_query(query))
            chunk_embs = np.array(embedding_service.embed_documents(chunk_texts))
        except Exception:
            # Fallback if embeddings fail
            return sorted(candidates, key=lambda x: x.final_score, reverse=True)[:top_k]
            
        selected = []
        unselected = list(range(len(candidates)))
        
        while len(selected) < top_k and unselected:
            best_mmr = -float('inf')
            best_idx = -1
            
            for idx in unselected:
                # Relevance: normalized final_score (we assume final_score is already well-scaled or we can just use the query cosine similarity)
                # But here we should honor the reranker's final_score as relevance
                relevance = candidates[idx].final_score
                
                # Redundancy: max cosine similarity with already selected chunks
                redundancy = 0.0
                if selected:
                    emb_i = chunk_embs[idx]
                    emb_selected = np.array([chunk_embs[s] for s in selected])
                    # Cosine similarity
                    sims = np.dot(emb_selected, emb_i) / (norm(emb_selected, axis=1) * norm(emb_i) + 1e-9)
                    redundancy = np.max(sims)
                    
                mmr_score = lambda_param * relevance - (1 - lambda_param) * redundancy
                
                if mmr_score > best_mmr:
                    best_mmr = mmr_score
                    best_idx = idx
                    
            selected.append(best_idx)
            unselected.remove(best_idx)
            
        return [candidates[i] for i in selected]
