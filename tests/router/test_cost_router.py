import pytest
from app.router.cost_router import cost_router
from app.retrieval.base import RetrievalResult

def make_res(score: float) -> RetrievalResult:
    return RetrievalResult(chunk_id="1", document_id="2", text="t", retrieval_method="vector", score=score)

def test_router_001_simple_factual():
    # ROUTER-001: Simple query + strong retrieval -> SMALL
    decision = cost_router.route("What is the leave limit?", [make_res(0.85)])
    assert decision.tier == "small"

def test_router_002_complex_multi_hop():
    # ROUTER-002: Complex query -> LARGE
    decision = cost_router.route("Which department owns the policy that governs employees in region X and why?", [make_res(0.85)])
    assert decision.tier == "large"

def test_router_003_comparison():
    # ROUTER-003: Moderate comparison -> LARGE (based on rules)
    decision = cost_router.route("Compare the leave policy between departments", [make_res(0.85)])
    assert decision.tier == "large"

def test_router_004_weak_answer_escalates():
    # ROUTER-004: Small model produces weak answer -> ESCALATE
    ans = "I couldn't find the answer in the provided context."
    assert cost_router.evaluate_quality(ans) == False
    decision = cost_router.route("What is the policy?", [make_res(0.85)])
    escalated = cost_router.escalate(decision)
    assert escalated is not None
    assert escalated.tier == "large"
    assert escalated.escalated == True

def test_router_005_valid_answer_no_escalate():
    # ROUTER-005: Valid answer -> NO ESCALATION
    ans = "The leave limit is 14 days."
    assert cost_router.evaluate_quality(ans) == True

def test_simple_weak_retrieval():
    decision = cost_router.route("What is the leave limit?", [make_res(0.60)])
    assert decision.tier == "large"

