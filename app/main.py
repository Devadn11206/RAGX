import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.exceptions import RAGXException, ragx_exception_handler, global_exception_handler
from app.api.routes.health import router as health_router
from app.api.routes.documents import router as documents_router
from app.api.routes.query import router as query_router

from app.infrastructure.postgres import postgres_client
from app.infrastructure.qdrant import qdrant_client
from app.infrastructure.redis import redis_client
from app.infrastructure.neo4j import neo4j_client
from app.services.document_service import document_service
from app.retrieval.qdrant_store import qdrant_store
from app.embeddings.sentence_transformer import embedding_service
from app.reranking.cross_encoder import local_cross_encoder_reranker

setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting RAGX API...")
    await postgres_client.connect()
    await qdrant_client.connect()
    await redis_client.connect()
    await neo4j_client.connect()
    
    # Phase 1 Inits
    await document_service.init_db()
    await qdrant_store.initialize_collection()
    
    from app.cache.semantic_cache import semantic_cache
    await semantic_cache.initialize_collection()
    
    from app.services.graph_service import graph_service
    await graph_service.initialize_schema()
    
    # Model Warmups to eliminate cold-start inference latency & timeouts
    embedding_service.warmup()
    if settings.RERANKING_ENABLED:
        local_cross_encoder_reranker.warmup()
    
    yield
    
    logger.info("Shutting down RAGX API...")
    await postgres_client.close()
    await qdrant_client.close()
    await redis_client.close()
    await neo4j_client.close()

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION, lifespan=lifespan)
app.add_exception_handler(RAGXException, ragx_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

app.include_router(health_router, tags=["Health"])
app.include_router(documents_router, prefix="/api/v1/documents", tags=["Documents"])
app.include_router(query_router, prefix="/api/v1/query", tags=["Query"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=getattr(settings, "API_HOST", "0.0.0.0"), port=getattr(settings, "API_PORT", 8000), reload=getattr(settings, "DEBUG", False))
