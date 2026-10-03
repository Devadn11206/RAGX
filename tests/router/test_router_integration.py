import pytest
from app.services.rag_service import rag_service
from app.security.models import User
from app.llm.orchestrator import llm_orchestrator
from app.llm.models import LLMResponse
from app.core.config import settings

@pytest.mark.asyncio(loop_scope="session")
async def test_router_integration_cache_miss(client):
    user = User(user_id="alice", tenant_id="test_tenant_acme", roles=["employee"])
    
    res = await rag_service.process_query("What is the leave policy limit?", user)
    
    assert res.retrieval.cache_type in ["MISS", "EXACT_HIT", "SEMANTIC_HIT"]
    
@pytest.mark.asyncio(loop_scope="session")
async def test_router_escalation_integration(client, monkeypatch):
    # Test escalation logic when small model produces weak answer
    user = User(user_id="alice", tenant_id="test_tenant_acme", roles=["employee"])
    
    call_count = 0
    def mock_generate(prompt, model_name=None, request_id="unknown", is_test_run=False):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return LLMResponse(
                content="I don't know the details.",
                provider="gemini",
                model=model_name or settings.ROUTER_SMALL_MODEL,
                estimated_cost=0.0001
            )
        return LLMResponse(
            content="ACME Internal Guide contains detailed corporate procedures and guidelines.",
            provider="gemini",
            model=model_name or settings.ROUTER_LARGE_MODEL,
            estimated_cost=0.001
        )
        
    monkeypatch.setattr(llm_orchestrator, "generate", mock_generate)
    res = await rag_service.process_query("ACME Internal Guide", user, mode="vector")
    
    # It should have escalated
    assert res.retrieval.escalated is True
    assert res.retrieval.router_tier == "large"
    assert res.retrieval.estimated_cost > 0.0001
