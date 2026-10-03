# RAGX Resume Descriptions

## VERSION A — ONE LINE
**AI Engineer / RAGX**: Engineered a secure, multi-tenant RAG platform using FastAPI and Docker, featuring hybrid retrieval (Vector, BM25, Graph), semantic caching, and LLM circuit breakers to guarantee robust, isolated query resolution.

## VERSION B — 2 BULLETS
**AI Software Engineer - RAGX**
- Architected a containerized, multi-tenant RAG pipeline leveraging Qdrant, Neo4j, and PostgreSQL, strictly enforcing JWT-based tenant data isolation at the database query layer (0 cross-tenant leaks in automated security tests).
- Engineered a scalable retrieval engine implementing parallel dense/sparse/graph search with RRF fusion and Cross-Encoder reranking, significantly boosting nDCG while minimizing LLM API costs via Redis semantic caching and automated provider fallbacks (Gemini to Groq).

## VERSION C — 4 BULLETS
**AI Backend Engineer - RAGX Project**
- Built a production-grade, multi-tenant hybrid Retrieval-Augmented Generation (RAG) platform with FastAPI, Streamlit, and Docker.
- Implemented robust security controls by enforcing JWT-based RBAC and deep tenant payload filtering in Qdrant and Neo4j, achieving a 100% pass rate across 11 targeted cross-tenant leakage and privilege escalation tests.
- Designed an advanced retrieval architecture using parallel vector search, PostgreSQL full-text search, and GraphRAG, fused via Reciprocal Rank Fusion (RRF) and optimized with Cross-Encoder reranking to maximize context relevance (MRR).
- Reduced external API overhead and increased reliability by deploying a Redis-backed semantic cache and a Circuit Breaker pattern to handle Gemini `429` rate limits with zero-downtime automated fallbacks to Groq Llama-3.
