from abc import ABC, abstractmethod
from typing import List
from app.retrieval.base import RetrievalResult

class Reranker(ABC):
    @abstractmethod
    async def rerank(self, query: str, candidates: List[RetrievalResult], top_k: int) -> List[RetrievalResult]:
        """
        Rerank a list of candidates against a query.
        Must preserve original metadata, graph evidence, etc.
        Must populate `rerank_score` and `final_score` on each returned RetrievalResult.
        """
        pass
