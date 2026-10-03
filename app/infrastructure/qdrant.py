import logging
from qdrant_client import AsyncQdrantClient
from app.core.config import settings

logger = logging.getLogger(__name__)

class QdrantClientWrapper:
    def __init__(self) -> None:
        self._client: AsyncQdrantClient | None = None

    @property
    def client(self) -> AsyncQdrantClient:
        if self._client is None:
            self._client = AsyncQdrantClient(
                host=settings.QDRANT_HOST,
                port=settings.QDRANT_PORT,
            )
        return self._client

    @client.setter
    def client(self, val: AsyncQdrantClient | None) -> None:
        self._client = val

    async def connect(self) -> None:
        try:
            if self._client is None:
                self._client = AsyncQdrantClient(
                    host=settings.QDRANT_HOST,
                    port=settings.QDRANT_PORT,
                )
            await self._client.get_collections()
            logger.info("Qdrant connection established")
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {str(e)}")

    async def close(self) -> None:
        if self._client:
            try:
                await self._client.close()
            except Exception as e:
                logger.error(f"Error closing Qdrant connection: {str(e)}")
            finally:
                self._client = None
                logger.info("Qdrant connection closed")

    async def ping(self) -> bool:
        try:
            await self.client.get_collections()
            return True
        except Exception as e:
            logger.error(f"Qdrant ping failed: {str(e)}")
            return False

qdrant_client = QdrantClientWrapper()
