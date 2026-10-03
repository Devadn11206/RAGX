# RAGX Portfolio Summary

## 100-Word Summary
RAGX is a production-ready, multi-tenant Retrieval-Augmented Generation (RAG) platform designed to solve enterprise engineering challenges. Moving beyond simple vector search, it implements a hybrid retrieval engine combining Dense Vector, BM25 Lexical, and GraphRAG methodologies, fused via RRF and optimized with Cross-Encoder reranking. RAGX strictly enforces JWT-based data isolation at the database level, ensuring zero cross-tenant data leakage. Built with FastAPI and Docker, the system minimizes LLM API costs through Redis semantic caching and guarantees high availability via automated Gemini-to-Groq fallback circuit breakers, fully validated by an automated test and benchmarking suite.

## 250-Word Summary
RAGX is a comprehensive AI engineering platform built to bridge the gap between basic RAG tutorials and enterprise-grade deployment realities. It tackles the fundamental challenges of deploying LLMs in production: security, latency, retrieval accuracy, and cost management. 

At its core, RAGX enforces strict multi-tenancy. Using JWT-based RBAC, it injects payload filters directly into Qdrant, Neo4j, and PostgreSQL queries, making unauthorized cross-tenant data leakage mathematically impossible at the database level. 

To maximize context relevance, the system Abandons naive vector search in favor of a parallel Hybrid Retrieval pipeline. It executes Dense Vector similarity, Sparse BM25 exact-matching, and GraphRAG topological traversal simultaneously. Results are normalized via Reciprocal Rank Fusion (RRF), rescored for absolute relevance using a Cross-Encoder, and filtered through Maximal Marginal Relevance (MMR) to maximize context diversity. 

Performance and reliability are heavily optimized. A Redis-backed semantic cache intercepts repeated queries to bypass costly LLM generation, reducing latency from seconds to milliseconds. A robust Circuit Breaker monitors the primary LLM (Gemini 1.5); upon detecting rate limits (`429`) or failures, it instantly fails over to a secondary provider (Groq Llama-3) ensuring zero downtime. The entire system is containerized via Docker Compose, instrumented with a Streamlit observability dashboard, and validated by a rigorous programmatic benchmarking suite proving its security and retrieval gains.

## Technical Summary
- **Backend**: Python 3.12, FastAPI
- **Retrieval Engine**: Sentence-Transformers, Qdrant (Dense), PostgreSQL (Sparse), Neo4j (Graph), Cross-Encoder (Reranking).
- **Orchestration**: Custom Circuit Breaker, Redis Semantic Cache, Cost-Aware Router.
- **LLM**: Google Gemini 1.5 Flash (Primary), Groq Llama-3 (Fallback).
- **Infrastructure**: Docker, Docker Compose, Pytest.

## Key Achievements
- Engineered strict database-level payload filtering achieving a verified **100% pass rate across 11 security tests** (0 cross-tenant leaks).
- Improved Retrieval MRR and nDCG compared to naive vector search by implementing RRF fusion and Cross-Encoder reranking, validated via automated benchmarking.
- Designed automated LLM failover resulting in seamless handling of API quota exhaustion during load testing.

## Limitations
- Generative evaluation currently relies on strict Exact Match/F1 scores, which penalizes correctly rephrased LLM answers.
- Synchronous LLM API calls currently block the HTTP response; migrating to streaming SSE would improve perceived user latency.
