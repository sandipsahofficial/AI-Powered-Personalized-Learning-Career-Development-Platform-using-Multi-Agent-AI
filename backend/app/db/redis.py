import time
import logging
from typing import Dict, Any, Optional
import redis.asyncio as aioredis
from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisManager:
    _instance: Optional["RedisManager"] = None
    _client: Optional[aioredis.Redis] = None

    @classmethod
    def get_instance(cls) -> "RedisManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_client(self) -> aioredis.Redis:
        if self._client is None:
            self._client = aioredis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_timeout=settings.REDIS_TIMEOUT
            )
        return self._client

    async def close(self):
        if self._client is not None:
            await self._client.close()
            self._client = None

    async def check_connection(self) -> Dict[str, Any]:
        """
        Validates Redis connection, ping latency, and read/write cycle.
        """
        start_time = time.perf_counter()
        try:
            client = self.get_client()
            pong = await client.ping()
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            
            # Temporary test key write/read
            test_key = "infra:health:ping"
            await client.set(test_key, "pong", ex=10)
            read_val = await client.get(test_key)
            rw_success = read_val == "pong"

            info = await client.info()

            return {
                "status": "healthy" if pong and rw_success else "degraded",
                "ping": pong,
                "latency_ms": latency_ms,
                "read_write_verified": rw_success,
                "redis_version": info.get("redis_version", "unknown"),
                "connected_clients": info.get("connected_clients", 0)
            }
        except Exception as e:
            logger.warning(f"Redis health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "host": settings.REDIS_HOST,
                "port": settings.REDIS_PORT
            }


redis_manager = RedisManager.get_instance()
