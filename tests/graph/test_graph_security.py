import pytest
from httpx import AsyncClient
from app.services.graph_service import graph_service

@pytest.mark.asyncio
async def test_graph_isolation_tenant_service():
    """
    GRAPH-SEC-001: Tenant A cannot retrieve Tenant B graph entities.
    """
    # Try to traverse the graph for "Globex" using Acme's tenant ID
    # Even if they ask for "Globex", the tenant_id in Cypher enforces isolation.
    results = await graph_service.hybrid_search("test_tenant_acme", ["Globex"])
    
    # We should get no results since Globex doesn't belong to Acme
    assert len(results) == 0

@pytest.mark.asyncio
async def test_graph_isolation_api(client: AsyncClient, test_users):
    """
    GRAPH-SEC-003: Tenant A cannot retrieve Tenant B source chunks through graph edges.
    """
    acme_user = test_users["acme_employee"]
    
    headers = {"Authorization": f"Bearer {acme_user}"}
    
    res = await client.post("/api/v1/query", json={"query": "Who founded Globex and what is their salary?"}, headers=headers)
    assert res.status_code == 200
    
    data = res.json()
    # The answer should not contain Globex salary info
    assert "Globex" not in data["sources"]
    
    sources = data.get("sources", [])
    for source in sources:
        assert "Globex" not in source["filename"]
