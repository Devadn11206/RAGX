import logging

import redis.asyncio as redis

from app.core.config import settings

logger = logging.getLogger(__name__)

class RedisClient:
    def __init__(self) -> None:
        self.client: redis.Redis | None = None

    async def connect(self) -> None:
        try:
            self.client = redis.from_url(settings.REDIS_URL, decode_responses=True)
            await self.client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            self.client = None

    async def close(self) -> None:
        if self.client:
            await self.client.aclose()
            logger.info("Redis connection closed")

    async def ping(self) -> bool:
        if not self.client:
            return False
        try:
            return await self.client.ping()
        except Exception as e:
            logger.error(f"Redis ping failed: {str(e)}")
            return False

redis_client = RedisClient()
