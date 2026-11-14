import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_system_info_endpoint(async_client: AsyncClient):
    response = await async_client.get("/api/v1/system/info")
    assert response.status_code == 200
    data = response.json()
    
    assert "platform" in data
    assert "runtime" in data
    assert "network" in data
    assert "server_time_utc" in data
    
    # Critical security verification: NO credentials or secrets in output
    raw_text = response.text.lower()
    assert "password" not in raw_text
    assert "secret" not in raw_text
    assert "key" not in raw_text or "cors_origins_count" in raw_text
