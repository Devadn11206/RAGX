import pytest

@pytest.mark.asyncio
async def test_role_spoofing_in_body(client, test_users):
    headers = {"Authorization": f"Bearer {test_users['acme_employee']}"}
    # Attempting to inject roles in the body
    res = await client.post("/api/v1/query", json={"query": "Restricted Admin Ops", "roles": ["admin"]}, headers=headers)
    assert res.status_code == 200
    # The server should ignore body roles and use the JWT (employee), denying restricted content
    for src in res.json().get("sources", []):
        assert "restricted" not in src["filename"]
