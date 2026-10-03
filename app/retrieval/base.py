from abc import ABC, abstractmethod
from typing import List, Optional
from pydantic import BaseModel, Field
from app.security.models import User

class RetrievalResult(BaseModel):
    chunk_id: str
    document_id: str
    text: str
    score: float  # Legacy/default score (usually retrieval_score)
    retrieval_score: Optional[float] = None
    rerank_score: Optional[float] = None
    final_score: Optional[float] = None
    retrieval_method: str
    filename: Optional[str] = None
    page_number: Optional[int] = None
    graph_evidence: Optional[str] = None

class BaseRetriever(ABC):
    @abstractmethod
    async def retrieve(self, query: str, user: User, top_k: int) -> List[RetrievalResult]:
        pass
