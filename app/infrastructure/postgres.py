import logging

import asyncpg

from app.core.config import settings

logger = logging.getLogger(__name__)

class PostgresClient:
    def __init__(self) -> None:
        self.pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        try:
            self.pool = await asyncpg.create_pool(
                user=settings.POSTGRES_USER,
                password=settings.POSTGRES_PASSWORD,
                database=settings.POSTGRES_DB,
                host=settings.POSTGRES_HOST,
                port=settings.POSTGRES_PORT,
            )
            logger.info("PostgreSQL connection established")
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {str(e)}")
            self.pool = None

    async def close(self) -> None:
        if self.pool:
            await self.pool.close()
            logger.info("PostgreSQL connection closed")

    async def ping(self) -> bool:
        if not self.pool:
            return False
        try:
            async with self.pool.acquire() as connection:
                await connection.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"PostgreSQL ping failed: {str(e)}")
            return False

postgres_client = PostgresClient()
