import pytest

@pytest.mark.asyncio
async def test_missing_auth_header(client):
    res = await client.post("/api/v1/query", json={"query": "hello"})
    assert res.status_code == 401

@pytest.mark.asyncio
async def test_malformed_jwt(client):
    res = await client.post("/api/v1/query", json={"query": "hello"}, headers={"Authorization": "Bearer invalid.token.here"})
    assert res.status_code == 401

@pytest.mark.asyncio
async def test_expired_jwt(client):
    import jwt
    from datetime import datetime, timedelta, timezone
    payload = {"sub": "user", "tenant_id": "test_tenant_acme", "roles": [], "exp": datetime.now(timezone.utc) - timedelta(hours=1)}
    token = jwt.encode(payload, "super_secret_phase_3_key_change_in_prod", algorithm="HS256")
    res = await client.post("/api/v1/query", json={"query": "hello"}, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 401

@pytest.mark.asyncio
async def test_tampered_jwt(client):
    import jwt
    from datetime import datetime, timedelta, timezone
    payload = {"sub": "user", "tenant_id": "test_tenant_acme", "roles": [], "exp": datetime.now(timezone.utc) + timedelta(hours=1)}
    token = jwt.encode(payload, "wrong_secret", algorithm="HS256")
    res = await client.post("/api/v1/query", json={"query": "hello"}, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 401
