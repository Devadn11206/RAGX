import pytest

@pytest.mark.asyncio
async def test_cross_tenant_query(client, test_users):
    headers = {"Authorization": f"Bearer {test_users['acme_employee']}"}
    res = await client.post("/api/v1/query", json={"query": "Globex Public Info"}, headers=headers)
    assert res.status_code == 200
    for src in res.json().get("sources", []):
        assert "test_tenant_globex" not in src["filename"]
        assert "Globex" not in src["filename"]

@pytest.mark.asyncio
async def test_direct_cross_tenant_access(client, test_users):
    # Acme employee trying to list all docs will only see Acme docs
    headers = {"Authorization": f"Bearer {test_users['acme_employee']}"}
    res = await client.get("/api/v1/documents", headers=headers)
    assert res.status_code == 200
    for doc in res.json():
        assert "globex" not in doc["filename"].lower()
