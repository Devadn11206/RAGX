from typing import Any

from app.core.config import settings
from app.infrastructure.neo4j import neo4j_client
from app.infrastructure.postgres import postgres_client
from app.infrastructure.qdrant import qdrant_client
from app.infrastructure.redis import redis_client


class HealthService:
    @staticmethod
    def get_basic_health() -> dict[str, str]:
        return {
            "status": "ok",
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION
        }

    @staticmethod
    async def get_detailed_health() -> dict[str, Any]:
        postgres_ok = await postgres_client.ping()
        qdrant_ok = await qdrant_client.ping()
        redis_ok = await redis_client.ping()
        neo4j_ok = await neo4j_client.ping()
        
        services = {
            "postgres": "healthy" if postgres_ok else "unhealthy",
            "qdrant": "healthy" if qdrant_ok else "unhealthy",
            "redis": "healthy" if redis_ok else "unhealthy",
            "neo4j": "healthy" if neo4j_ok else "unhealthy"
        }
        
        all_healthy = all(status == "healthy" for status in services.values())
        
        return {
            "status": "healthy" if all_healthy else "degraded",
            "services": services
        }
