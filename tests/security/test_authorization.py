import pytest

@pytest.mark.asyncio
async def test_unauthorized_role(client, test_users):
    headers = {"Authorization": f"Bearer {test_users['acme_employee']}"}
    res = await client.post("/api/v1/query", json={"query": "Restricted Admin Ops"}, headers=headers)
    assert res.status_code == 200
    # Must not contain restricted doc chunks
    for src in res.json().get("sources", []):
        assert "restricted" not in src["filename"]

@pytest.mark.asyncio
async def test_authorized_role(client, test_users):
    headers = {"Authorization": f"Bearer {test_users['acme_admin']}"}
    res = await client.post("/api/v1/query", json={"query": "Restricted Admin Ops"}, headers=headers)
    assert res.status_code == 200
    sources = res.json().get("sources", [])
    assert any("restricted" in src["filename"] for src in sources)
