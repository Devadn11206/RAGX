# Project Audit

## Current Architecture
- **API**: FastAPI (`app.main:app`) running on Uvicorn.
- **Dashboard**: Streamlit (`dashboard/app.py`).
- **Core Infrastructure**:
  - PostgreSQL (Relational DB for metadata/users)
  - Qdrant (Vector DB)
  - Redis (Caching and rate limiting)
  - Neo4j (Knowledge Graph for GraphRAG)

## Runtime Dependencies
- Python >= 3.10 (3.12 recommended, used in Dockerfile)
- Core: `fastapi`, `uvicorn`, `pydantic`, `asyncpg`, `qdrant-client`, `redis`, `neo4j`, `streamlit`, `pymupdf`, `sentence-transformers`, `google-generativeai`, `python-multipart`
- Dev/Test: `pytest`, `pytest-asyncio`, `ruff`, `httpx`

## Environment Variables
- `APP_ENV`, `API_HOST`, `API_PORT`
- `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
- `QDRANT_HOST`, `QDRANT_PORT`, `QDRANT_URL`, `QDRANT_API_KEY`
- `REDIS_HOST`, `REDIS_PORT`, `REDIS_URL`
- `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`
- `GEMINI_API_KEY`, `GROQ_API_KEY`

## Test Commands
- Security Tests: `python -m scripts.security_test`
- GraphRAG Benchmark: `python scripts/graph_benchmark.py`
- Cache Benchmark: `python scripts/cache_benchmark.py`
- Provider Benchmark: `python scripts/provider_benchmark.py`
- Hybrid Retrieval: `python scripts/hybrid_benchmark.py`
- Reranking Benchmark: `python scripts/benchmark_reranking.py`
- Semantic Golden Test: `python -m scripts.semantic_golden_test`
- General regression/pytest: `pytest -q`
- Phase 12 validation (runs all benchmarks): `python scripts/run_phase12_validation.py`

## Identified Docker/CI Risks
- **Model downloading**: `sentence-transformers` models download at runtime which might cause slow start times or big Docker images, or timeouts in CI without caching.
- **Secrets in source**: A potential risk if `GEMINI_API_KEY` or `GROQ_API_KEY` are hardcoded in test scripts or `.env`. Needs to be excluded via `.gitignore` and `.dockerignore`.
- **Database initialization**: Need to ensure wait-for-it or proper health checks so FastAPI doesn't crash on start before databases are ready.
- **Data Persistence**: Named volumes must be properly mapped in docker-compose.
- **Environment config missing**: If the `.env` file is not properly mapped or CI secrets are not passed, API will fail to start.
