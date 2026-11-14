import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db.session import engine
from app.db.redis import redis_manager


@pytest_asyncio.fixture(autouse=True)
async def cleanup_connections():
    yield
    await engine.dispose()
    await redis_manager.close()


@pytest_asyncio.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
