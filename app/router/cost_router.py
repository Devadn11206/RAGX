import math
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.retrieval.base import RetrievalResult

class RoutingDecision(BaseModel):
    tier: str
    model: str
    reason: str
    confidence: float
    escalated: bool = False

class CostAwareRouter:
    def __init__(self):
        self.small_model = settings.ROUTER_SMALL_MODEL
        self.large_model = settings.ROUTER_LARGE_MODEL

    def _analyze_query(self, query: str) -> str:
        q = query.lower()
        complex_keywords = ["compare", "difference", "why", "analyze", "evaluate", "multiple", "across", "relationship"]
        if any(k in q for k in complex_keywords) or len(q.split()) > 15:
            return "COMPLEX"
        return "SIMPLE"

    def _analyze_retrieval(self, results: List[RetrievalResult]) -> float:
        if not results:
            return 0.0
        return max(r.score for r in results)

    def route(self, query: str, results: List[RetrievalResult]) -> RoutingDecision:
        if not settings.ROUTER_ENABLED:
            return RoutingDecision(tier="large", model=self.large_model, reason="Router disabled", confidence=1.0)
            
        complexity = self._analyze_query(query)
        top_score = self._analyze_retrieval(results)
        
        if complexity == "SIMPLE" and top_score >= 0.70:
            return RoutingDecision(
                tier="small",
                model=self.small_model,
                reason="Simple query with strong retrieval",
                confidence=0.9
            )
        elif complexity == "SIMPLE" and top_score < 0.70:
            return RoutingDecision(
                tier="large",
                model=self.large_model,
                reason="Simple query but weak retrieval",
                confidence=0.7
            )
        else:
            return RoutingDecision(
                tier="large",
                model=self.large_model,
                reason="Complex reasoning required",
                confidence=0.9
            )
            
    def evaluate_quality(self, answer: str) -> bool:
        if not answer or answer.strip() == "":
            return False
        
        lower_ans = answer.lower()
        weak_phrases = ["i don't know", "i couldn't find", "there is no information", "i cannot answer"]
        
        if any(p in lower_ans for p in weak_phrases):
            return False
            
        return True

    def escalate(self, current_decision: RoutingDecision) -> Optional[RoutingDecision]:
        if current_decision.tier == "small":
            return RoutingDecision(
                tier="large",
                model=self.large_model,
                reason="Escalated due to weak initial answer",
                confidence=1.0,
                escalated=True
            )
        return None

cost_router = CostAwareRouter()
