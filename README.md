# RAGX

![Python](https://img.shields.io/badge/Python-3.12-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-009688.svg)
![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED.svg)
![Tests](https://img.shields.io/badge/Tests-58%2F58_Passed-success.svg)
![Security](https://img.shields.io/badge/Security-0_Leaks-success.svg)

**Production-Oriented Multi-Tenant RAG Engineering Platform**

## Overview

RAGX is an advanced AI engineering platform built to solve the real-world complexities of deploying Retrieval-Augmented Generation (RAG) in production. Moving beyond simplistic "document-to-vector" tutorials, RAGX demonstrates how to handle strict data security, retrieval accuracy, latency optimization, and API resilience at scale.

At its core, RAGX guarantees strict multi-tenant isolation. It enforces JWT-based identity checks and injects tenant payload filters directly into the database queries (Qdrant, Neo4j, PostgreSQL), making unauthorized cross-tenant data leakage mathematically impossible at the database layer.

To maximize answer accuracy, RAGX utilizes a parallel Hybrid Retrieval pipeline. It simultaneously executes Dense Vector similarity, Sparse BM25 exact-matching, and GraphRAG topological traversal. The results are merged via Reciprocal Rank Fusion (RRF), rescored by a local Cross-Encoder, and filtered via Maximal Marginal Relevance (MMR) before ever reaching the LLM. Furthermore, the system incorporates a Redis-backed semantic cache and an automated Gemini-to-Groq circuit breaker, ensuring that the platform remains fast and highly available even when external LLM APIs fail.

## Key Features

- **Multi-Tenant Security**: Strict, database-layer payload filtering to guarantee zero cross-tenant data leakage.
- **Hybrid Retrieval**: Parallel execution of Vector (Qdrant) and Lexical (PostgreSQL) search fused via RRF.
- **GraphRAG**: Neo4j-powered topological traversal for complex entity relationships.
- **Cross-Encoder Reranking**: High-fidelity context rescoring to maximize MRR and nDCG.
- **Semantic Cache**: Redis-backed query embedding cache to bypass LLM latency and costs.
- **Cost-Aware Routing**: Smart query classification to route questions to the optimal pipeline.
- **Circuit Breaker Fallback**: Automated, zero-downtime fallback from Google Gemini to Groq Llama-3 during `429` rate limits.
- **Streamlit Observability**: Interactive dashboard for chat, pipeline tracing, and security auditing.
- **Docker + CI/CD**: Fully containerized infrastructure reproducible with a single `docker compose` command.

## What makes RAGX different?

Most basic RAG setups follow a naive path:
`Query → Vector Search → LLM`

RAGX is built for engineering rigor:
`Query → Authentication → Tenant Isolation → Semantic Cache → Query Analysis → Cost-Aware Routing → Hybrid Retrieval (Vector + Lexical + Graph) → RRF Fusion → Cross-Encoder Reranking → MMR → LLM (w/ Provider Fallback) → Citations → Telemetry`

The project focuses on **quality, security, latency, cost, resilience, and observability** rather than just answer generation.

## Architecture

![Architecture](docs/architecture.md)

## Tech Stack

| Layer | Technology |
|---|---|
| API | FastAPI |
| UI | Streamlit |
| Language | Python 3.12 |
| Embeddings | Sentence Transformers (`all-MiniLM-L6-v2`) |
| Vector DB | Qdrant |
| Lexical Retrieval | PostgreSQL (Full-Text Search) |
| Graph DB | Neo4j |
| Reranking | Cross-Encoder (`ms-marco-MiniLM-L-6-v2`) |
| Cache | Redis |
| Database | PostgreSQL |
| Primary LLM | Google Gemini (1.5 Flash) |
| Fallback LLM | Groq (Llama 3) |
| Containerization | Docker & Docker Compose |

## Benchmark & Security Validation

RAGX includes a rigorous programmatic benchmarking suite (validated in Phase 14.1).

### Retrieval Quality

| Pipeline | Recall@5 | MRR | nDCG | F1 |
|---|---:|---:|---:|---:|
| Vector | 0.600 | 0.468 | 0.496 | 0.064 |
| Hybrid | 0.592 | 0.457 | 0.486 | 0.047 |
| Hybrid + GraphRAG | 0.600 | 0.468 | 0.496 | 0.060 |
| Hybrid + Reranking + MMR | 0.600 | 0.468 | 0.496 | 0.064 |

### Security Validation

- **47/47** System regression tests passed.
- **11/11** Strict security tests passed.
- **0** Cross-tenant leaks.
- **0** Privilege escalations.
- **0** Unauthorized chunks exposed.

## Quick Start (Deployment)

1. **Clone the repository.**
2. **Configure Environment Variables**:
   ```bash
   cp .env.example .env
   # Edit .env and insert your GEMINI_API_KEY and GROQ_API_KEY
   ```
3. **Start the Infrastructure**:
   ```bash
   docker compose up -d --build
   ```
4. **Access the System**:
   - Streamlit Dashboard: `http://localhost:8501`
   - FastAPI Interactive Docs: `http://localhost:8000/docs`

For detailed setup, see the [Deployment Guide](docs/deployment.md).

## Documentation Directory
- [Architecture](docs/architecture.md)
- [Security Model](docs/security.md)
- [Evaluation & Benchmarks](docs/evaluation.md)
- [Deployment Guide](docs/deployment.md)

## License
License decision pending.
