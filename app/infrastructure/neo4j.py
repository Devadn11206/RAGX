import logging

from neo4j import AsyncDriver, AsyncGraphDatabase

from app.core.config import settings

logger = logging.getLogger(__name__)

class Neo4jClient:
    def __init__(self) -> None:
        self.driver: AsyncDriver | None = None

    async def connect(self) -> None:
        try:
            self.driver = AsyncGraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
            )
            await self.driver.verify_connectivity()
            logger.info("Neo4j connection established")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {str(e)}")
            self.driver = None

    async def close(self) -> None:
        if self.driver:
            await self.driver.close()
            logger.info("Neo4j connection closed")

    async def ping(self) -> bool:
        if not self.driver:
            return False
        try:
            await self.driver.verify_connectivity()
            return True
        except Exception as e:
            logger.error(f"Neo4j ping failed: {str(e)}")
            return False

neo4j_client = Neo4jClient()
