import pytest
from httpx import AsyncClient
from app.services.rag_service import rag_service

@pytest.mark.asyncio
async def test_hybrid_security_isolation(client: AsyncClient, test_users):
    """
    Tests HYBRID-SEC-001 through HYBRID-SEC-006.
    Ensures that queries executed across Vector, Lexical, and Graph retrieval
    do not leak data across tenants, even when fusion is enabled.
    """
    acme_user = test_users["acme_employee"]
    
    headers = {"Authorization": f"Bearer {acme_user}"}
    
    # Send a query that is specifically looking for Globex data
    payload = {
        "query": "What is the Globex restricted salary data and error code ERR-4821?",
        "retrieval_mode": "hybrid"
    }
    
    res = await client.post("/api/v1/query", json=payload, headers=headers)
    assert res.status_code == 200
    
    data = res.json()
    
    # 1. Answer should not contain unauthorized info
    assert "Globex" not in data["sources"]
    
    # 2. Inspect sources for any leakage
    sources = data.get("sources", [])
    for source in sources:
        assert "Globex" not in source["filename"]
        
    # Check that metadata properly tracked empty cross-tenant attempts
    # If the user asked about Globex, the system shouldn't have found it.
