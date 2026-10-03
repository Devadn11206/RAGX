from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class EvalQuestion(BaseModel):
    question_id: str
    question: str
    reference_answer: str
    source_documents: List[str]
    expected_chunk_ids: List[str]
    question_type: str
    difficulty: str

class EvalDataset(BaseModel):
    dataset_version: str
    questions: List[EvalQuestion]

class JudgeOutput(BaseModel):
    correctness: float
    relevance: float
    faithfulness: float
    reason: str

class QuestionResult(BaseModel):
    run_id: str
    question_id: str
    question: str
    question_type: str
    difficulty: str
    reference_answer: str
    generated_answer: Optional[str] = None
    
    expected_chunk_ids: List[str]
    retrieved_chunk_ids: List[str]
    
    retrieval_hit_at_1: float
    retrieval_hit_at_3: float
    retrieval_hit_at_5: float
    recall_at_5: float
    mrr: float
    
    answer_correctness: Optional[float] = None
    answer_relevance: Optional[float] = None
    faithfulness: Optional[float] = None
    
    retrieval_latency_ms: float
    generation_latency_ms: float
    total_latency_ms: float
    
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    estimated_cost_usd: Optional[float] = None
    
    status: str
    error: Optional[str] = None
