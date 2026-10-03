# RAGX

![Python](https://img.shields.io/badge/Python-3.12-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-009688.svg)
![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED.svg)
![Tests](https://img.shields.io/badge/Tests-58%2F58_Passed-success.svg)
![Security](https://img.shields.io/badge/Security-0_Leaks-success.svg)

**Production-Oriented Multi-Tenant RAG Engineering Platform**

## Overview

RAGX is a production-oriented RAG engineering platform. It was built to explore secure, reliable, cost-aware and high-quality retrieval systems beyond simple "document-to-vector" tutorials.

At its core, RAGX enforces strict multi-tenant isolation. It injects JWT-based tenant payload filters directly into the database queries (Qdrant, Neo4j, PostgreSQL), ensuring secure data scoping at the database layer.

To improve context relevance, RAGX utilizes a parallel Hybrid Retrieval pipeline. It simultaneously executes Dense Vector similarity, Sparse BM25 exact-matching, and GraphRAG topological traversal. The results are merged via Reciprocal Rank Fusion (RRF), rescored by a local Cross-Encoder, and filtered via Maximal Marginal Relevance (MMR) before reaching the LLM. Furthermore, the system incorporates a Redis-backed semantic cache and an automated Gemini-to-Groq circuit breaker, improving latency and maintaining availability during API rate limits.

## Architecture & Flow

```
Query
 ↓
Tenant Authorization
 ↓
Semantic Cache
 ↓
Query Analysis
 ↓
Cost-Aware Routing
 ↓
Hybrid Retrieval
 ├── Vector
 ├── Lexical
 └── GraphRAG
 ↓
RRF Fusion
 ↓
Cross-Encoder Reranking
 ↓
MMR
 ↓
LLM
 ├── Gemini
 └── Groq fallback
 ↓
Answer + Citations
 ↓
Telemetry / Audit
```

## Tech Stack

- **API**: FastAPI, Python 3.12
- **UI**: Streamlit
- **Embeddings**: Sentence Transformers (`all-MiniLM-L6-v2`)
- **Vector DB**: Qdrant
- **Lexical Retrieval**: PostgreSQL (Full-Text Search)
- **Graph DB**: Neo4j
- **Reranking**: Cross-Encoder (`ms-marco-MiniLM-L-6-v2`)
- **Cache**: Redis
- **Primary LLM**: Google Gemini (1.5 Flash)
- **Fallback LLM**: Groq (Llama 3)
- **Containerization**: Docker & Docker Compose

---

# 📊 Benchmark Results

RAGX was evaluated across multiple retrieval configurations using a controlled benchmark.

### Evaluation Dataset
- **Questions**: 50
- **Documents**: 3
- **Evaluation Categories**: Factual, Semantic, Lexical, Multi-hop, Comparison, Policy, Adversarial, Tenant-specific.

### Methodology
All configurations were tested sequentially against the exact same 50-question dataset using local CPU inference. This ensured a controlled variable environment where the retrieval mode was the only changing factor. Exact Match and Token-level F1 were calculated automatically by comparing the final LLM output with reference answers.

## Retrieval Benchmark

| Pipeline | Recall@5 | MRR | F1 | Exact Match | P50 Latency |
|---|---:|---:|---:|---:|---:|
| Vector | 0.600 | 0.468 | 0.064 | 0.020 | 161 ms |
| Vector + Lexical | 0.600 | 0.468 | 0.059 | 0.000 | 151 ms |
| Hybrid (Vector + Lexical + Graph) | 0.600 | 0.468 | 0.060 | 0.000 | 149 ms |

## Reranking Evaluation

| Pipeline | Recall@5 | MRR | F1 | Exact Match | P50 Latency |
|---|---:|---:|---:|---:|---:|
| Hybrid + Reranking | 0.612 | 0.478 | 0.059 | 0.000 | 148 ms |
| Hybrid + Reranking + MMR | 0.600 | 0.468 | 0.064 | 0.020 | 162 ms |

## GraphRAG Evaluation
GraphRAG topological traversal was evaluated for multi-hop reasoning. The measured F1 score for Hybrid + GraphRAG on this dataset was 0.060. 

## Semantic Cache
A sample validation consisting of 5 repeated queries demonstrated a 100% cache hit rate. Cache retrieval latency averaged ~5ms, bypassing full downstream LLM generation and network latency.

## Security Validation
- **47/47** System regression tests passed.
- **11/11** Strict security tests passed.
- **0** Cross-tenant leaks.
- **0** Privilege escalations.
- **0** Unauthorized chunks exposed.
- **0** Canary leaks.

## Provider Resilience
Gemini → Groq fallback was successfully validated during simulated provider failure scenarios (HTTP 429 quota exhaustion), demonstrating seamless LLM traffic redirection via the custom Circuit Breaker.

## Docker Validation
The full infrastructure successfully builds and runs via a single `docker compose up -d` command, with all dependent services (Postgres, Qdrant, Redis, Neo4j, FastAPI, Streamlit) passing strict health checks.

### Benchmark Limitations
- **Small Dataset**: The benchmark was executed on a highly scoped synthetic dataset (3 documents, 50 questions). Results may not generalize to large production corpora.
- **Strict Matching**: Token-level F1 and Exact Match strictly penalize verbose LLM answers even when the generated semantic fact is correct.
- **Hardware Constraints**: Reranking and Embeddings were evaluated exclusively on CPU.
- **Dashboard Values**: Certain metrics visualized in the UI dashboard during demonstration runs may represent simulated or sample data rather than rigorous aggregate benchmarking.

---

## Quick Start (Deployment)

1. **Clone the repository.**
2. **Configure Environment Variables**:
   ```bash
   cp .env.example .env
   # Edit .env and insert your API keys (Gemini, Groq, etc.)
   ```
3. **Start the Infrastructure**:
   ```bash
   docker compose up -d --build
   ```
4. **Access the System**:
   - Streamlit Dashboard: `http://localhost:8501`
   - FastAPI Interactive Docs: `http://localhost:8000/docs`

## Documentation Directory
- [Architecture](docs/architecture.md)
- [Security Model](docs/security.md)
- [Evaluation & Benchmarks](docs/evaluation.md)
- [Deployment Guide](docs/deployment.md)

## License
License decision pending.
