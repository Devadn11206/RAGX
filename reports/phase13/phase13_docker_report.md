# Phase 13 Dockerization Report

## 1. Docker Architecture Overview
RAGX uses a full containerized microservices architecture with `docker-compose`. 

- **API Service** (`ragx-api`): FastAPI application running via Uvicorn.
- **Dashboard Service** (`ragx-dashboard`): Streamlit application.
- **Infrastructure Services**:
  - `ragx-postgres`: PostgreSQL 16 Alpine
  - `ragx-qdrant`: Qdrant Vector DB 1.8.2
  - `ragx-redis`: Redis 7 Alpine
  - `ragx-neo4j`: Neo4j 5.18 Community

## 2. Docker Image Details
- **Base Image**: `python:3.12-slim-bookworm` provides a lightweight, highly-stable base OS.
- **Size Optimization**: Eliminated caching layers in Pip (`--no-cache-dir`) and avoided installing system tools like `curl` inside the image to maintain minimum footprint.
- **Execution Privilege**: Both custom services execute as a newly created `appuser`, conforming to security best practices.

## 3. Persistent Storage
All stateful services mount Docker Named Volumes to guarantee data persistence:
- `postgres_data` -> `/var/lib/postgresql/data`
- `qdrant_data` -> `/qdrant/storage`
- `redis_data` -> `/data`
- `neo4j_data` -> `/data`

## 4. Health Checks and Lifecycles
- `ragx-api` heavily relies on `docker-compose`'s `depends_on: condition: service_healthy` to wait for all databases to become responsive before booting up.
- FastAPI's internal `HEALTHCHECK` makes a local network call via python's `urllib` to `/health/detailed`, verifying that backend DB connections are still active.
- `ragx-dashboard` waits for `ragx-api` to be started.

## 5. Local Reproduction
The complete setup can be reliably started from a fresh clone using:
```bash
cp .env.example .env
docker compose up --build
```
