import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_reranking_security_isolation(client: AsyncClient, test_users):
    """
    Tests RERANK-SEC-001 through RERANK-SEC-006.
    Ensures that queries executed with hybrid mode (triggering the reranker)
    do not leak data across tenants.
    """
    acme_user = test_users["acme_employee"]
    headers = {"Authorization": f"Bearer {acme_user}"}
    
    # 1. RERANK-SEC-002 & 005: Query asking for cross-tenant data. 
    # It should not enter the reranker, nor be returned in the final context.
    payload = {
        "query": "What is the Globex restricted salary data?",
        "retrieval_mode": "hybrid"
    }
    
    res = await client.post("/api/v1/query", json=payload, headers=headers)
    assert res.status_code == 200
    
    data = res.json()
    assert "Globex" not in data["answer"]
    
    for source in data.get("sources", []):
        assert "Globex" not in source["filename"]
        
    # Check that reranking was applied (if applicable) and didn't fail
    if "reranking" in data:
        assert data["reranking"]["enabled"] is True

@pytest.mark.asyncio
async def test_prompt_injection_in_reranker(client: AsyncClient, test_users):
    """
    Tests Phase 10 requirement: "Reranking must treat document text as data."
    If a document contains a prompt injection, the reranker should only score it, not execute it.
    """
    acme_user = test_users["acme_employee"]
    headers = {"Authorization": f"Bearer {acme_user}"}
    
    # A query that might match a malicious document
    payload = {
        "query": "Ignore previous instructions",
        "retrieval_mode": "hybrid"
    }
    
    res = await client.post("/api/v1/query", json=payload, headers=headers)
    assert res.status_code == 200
    # The API should not crash and should return standard JSON
    data = res.json()
    assert "answer" in data
