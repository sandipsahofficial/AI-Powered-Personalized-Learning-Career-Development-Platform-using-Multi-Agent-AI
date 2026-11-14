import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root_endpoint(async_client: AsyncClient):
    response = await async_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "health" in data


@pytest.mark.asyncio
async def test_overall_health_endpoint(async_client: AsyncClient):
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "services" in data
    assert "database" in data["services"]
    assert "redis" in data["services"]
    assert "llm" in data["services"]


@pytest.mark.asyncio
async def test_database_health_structure(async_client: AsyncClient):
    response = await async_client.get("/api/v1/health/database")
    # Endpoint returns 200 if connected or 503 if DB is offline, but structure is validated
    assert response.status_code in [200, 503]
    data = response.json()
    assert "status" in data
    assert "database" in data


@pytest.mark.asyncio
async def test_redis_health_structure(async_client: AsyncClient):
    response = await async_client.get("/api/v1/health/redis")
    assert response.status_code in [200, 503]
    data = response.json()
    assert "status" in data


@pytest.mark.asyncio
async def test_llm_health_structure(async_client: AsyncClient):
    response = await async_client.get("/api/v1/health/llm")
    assert response.status_code in [200, 502, 503]
    data = response.json()
    assert "status" in data
    assert "ollama_base_url" in data
