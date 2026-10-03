from pydantic import BaseModel
from typing import List, Optional

class QueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = None
    retrieval_mode: Optional[str] = "auto"

class Citation(BaseModel):
    document_id: str
    chunk_id: str
    filename: str
    page_number: Optional[int]
    score: float
    retrieval_method: Optional[str] = "vector"

class RetrievalInfo(BaseModel):
    request_id: Optional[str] = None
    top_k: int
    results_returned: int
    cache_type: Optional[str] = "MISS"
    latency_ms: Optional[int] = 0
    router_tier: Optional[str] = None
    escalated: Optional[bool] = False
    estimated_cost: Optional[float] = 0.0
    provider: Optional[str] = None
    model: Optional[str] = None
    fallback_used: Optional[bool] = False
    fallback_reason: Optional[str] = None
    graph_used: Optional[bool] = False
    lexical_used: Optional[bool] = False
    vector_used: Optional[bool] = False

class RerankingInfo(BaseModel):
    enabled: bool
    model: str
    candidate_count: int
    final_count: int
    latency_ms: int
    skipped: Optional[bool] = False
    timeout: Optional[bool] = False
    error: Optional[str] = None

class QueryResponse(BaseModel):
    query: str
    answer: str
    sources: List[Citation]
    retrieval: RetrievalInfo
    reranking: Optional[RerankingInfo] = None
