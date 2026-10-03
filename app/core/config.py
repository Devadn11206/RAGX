from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "RAGX API"
    APP_VERSION: str = "0.1.0"
    LOG_LEVEL: str = "INFO"
    
    # Existing settings...
    POSTGRES_USER: str = "ragx"
    POSTGRES_PASSWORD: str = "change_me"
    POSTGRES_DB: str = "ragx"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5433

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_URL: str = "redis://localhost:6379/0"

    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "change_me"

    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION: str = "ragx_documents"
    
    # Phase 1 parameters
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.8-flash"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    RAG_CHUNK_SIZE: int = 500
    RAG_CHUNK_OVERLAP: int = 50
    RAG_TOP_K: int = 5
    MIN_RETRIEVAL_SCORE: float = 0.35
    
    # Phase 6 Router
    ROUTER_ENABLED: bool = True
    ROUTER_SMALL_MODEL: str = "gemini-3.8-flash"
    ROUTER_LARGE_MODEL: str = "gemini-3.8-flash"
    MAX_LLM_CALLS_PER_REQUEST: int = 2
    
    # Phase 7 Provider Fallback
    GROQ_API_KEY: str = ""
    GROQ_SMALL_MODEL: str = "qwen/qwen3.8-27b"
    GROQ_LARGE_MODEL: str = "openai/gpt-oss-120b"
    GEMINI_TIMEOUT_SECONDS: int = 10
    GROQ_TIMEOUT_SECONDS: int = 30
    GEMINI_MAX_RETRIES: int = 1
    GROQ_MAX_RETRIES: int = 2
    CIRCUIT_FAILURE_THRESHOLD: int = 5
    CIRCUIT_OPEN_SECONDS: int = 60
    CIRCUIT_HALF_OPEN_REQUESTS: int = 1
    
    # Phase 8 GraphRAG
    GRAPH_MAX_HOPS: int = 2
    GRAPH_MAX_ENTITIES: int = 20
    GRAPH_MAX_CHUNKS: int = 20
    
    # Phase 3 Auth
    JWT_SECRET_KEY: str = "super_secret_phase_3_key_change_in_prod"

    # Phase 9 Hybrid Retrieval
    HYBRID_RETRIEVAL_ENABLED: bool = True
    VECTOR_TOP_K: int = 10
    LEXICAL_TOP_K: int = 10
    GRAPH_TOP_K: int = 10
    HYBRID_FINAL_K: int = 8
    RRF_K: int = 60
    MAX_CONTEXT_CHUNKS: int = 8
    
    # Phase 10 Production Reranking
    RERANKING_ENABLED: bool = True
    RERANKER_PROVIDER: str = "local_cross_encoder"
    RERANKER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    RERANK_TOP_K: int = 8
    RERANK_CANDIDATE_K: int = 30
    RERANK_BATCH_SIZE: int = 16
    RERANK_TIMEOUT_MS: int = 5000
    RERANK_RETRIEVAL_WEIGHT: float = 0.20
    RERANK_MODEL_WEIGHT: float = 0.80
    RERANK_SELECTION: str = "score"  # "score" or "mmr"
    ADAPTIVE_RERANKING_ENABLED: bool = False
    MAX_CHUNKS_PER_DOCUMENT: int = 3

    model_config = {"env_file": ".env"}

settings = Settings()
