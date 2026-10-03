# RAGX Deployment Guide

RAGX is fully containerized using Docker and orchestrated via Docker Compose.

## 1. Prerequisites
- **Docker** and **Docker Compose** installed.
- **Git** (if cloning).
- **API Keys**: Google Gemini and/or Groq API keys.

## 2. Environment Setup
Create a `.env` file from the example template:
```bash
cp .env.example .env
```
Edit the `.env` file and insert your API keys:
```env
GEMINI_API_KEY=your_gemini_key_here
GROQ_API_KEY=your_groq_key_here
JWT_SECRET=generate_a_secure_random_string_here
```
*Note: All database passwords default to `change_me` for local development. In a true production environment, replace these with secure passwords.*

## 3. Starting the System
Start all services in detached mode:
```bash
docker compose up -d --build
```
This single command spins up:
1. `ragx-postgres` (Port 5433 host / 5432 container)
2. `ragx-redis` (Port 6379)
3. `ragx-qdrant` (Port 6333)
4. `ragx-neo4j` (Port 7474 / 7687)
5. `ragx-api` (Port 8000)
6. `ragx-dashboard` (Port 8501)

## 4. Health Checks
Monitor the health of your services:
```bash
docker compose ps
```
Or check the API health endpoints directly:
- **Basic Health**: `http://localhost:8000/health`
- **Detailed Health**: `http://localhost:8000/health/detailed`

## 5. Endpoints
- **API Swagger Docs**: `http://localhost:8000/docs`
- **Streamlit Dashboard**: `http://localhost:8501`

## 6. Model Caching
RAGX downloads HuggingFace Embedding and Reranking models automatically on the first boot. These are persisted locally via the `hf_cache` Docker volume so they survive container restarts.

## 7. Shutdown
To cleanly stop the system without deleting your data:
```bash
docker compose down
```
To stop the system and completely wipe the database volumes:
```bash
docker compose down -v
```
