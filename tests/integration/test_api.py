import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_api_upload_invalid_file(test_users):
    acme_user = test_users["acme_employee"]
    headers = {"Authorization": f"Bearer {acme_user}"}
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        files = {'file': ('test.invalid', b'content')}
        response = await ac.post("/api/v1/documents/upload", files=files, headers=headers)
        
    # Should be 400 because of unsupported file type
    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == "UNSUPPORTED_FILE"
