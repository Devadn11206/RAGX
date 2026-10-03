# RAGX Technical Interview Guide

## 1. What is RAGX?
RAGX is a production-oriented, multi-tenant hybrid Retrieval-Augmented Generation (RAG) platform. It goes beyond simple document embedding to implement secure tenant isolation, advanced retrieval pipelines (Vector, BM25, Graph), and resilient LLM orchestration with automated fallbacks and semantic caching.

## 2. Why did you build it?
Most open-source RAG tutorials focus purely on the happy path (embedding text and querying OpenAI). I built RAGX to solve real-world engineering problems: what happens when users try to view other clients' data? What happens when an LLM API rate-limits you? How do you reduce latency and token costs for repeated queries?

## 3. Why not just vector search?
Dense vector embeddings are great for semantic similarity (e.g., "how do I reset my password") but terrible for exact matches (e.g., searching for a specific product ID like `AX-9942`). Vector search alone also misses complex structural relationships. 

## 4. Why hybrid retrieval?
By executing Dense Vector (Qdrant), Sparse Lexical (PostgreSQL full-text), and Graph (Neo4j) searches in parallel and fusing the results using Reciprocal Rank Fusion (RRF), RAGX covers both semantic meaning and exact keyword hits, providing a much higher Recall@K.

## 5. Why GraphRAG?
Graph databases explicitly model relationships (e.g., `[CEO] -> LEADS -> [Company]`). When a query asks complex multi-hop questions ("Who is the manager of the person leading Project X?"), standard vector chunks fail. Graph traversal retrieves the exact topological connection.

## 6. Why reranking?
Initial retrievers (like HNSW in Qdrant) prioritize speed over absolute accuracy, returning a wide net of documents. A Cross-Encoder reranker compares the query and document together through a transformer, calculating a highly accurate relevance score to bring the best documents to the top before they hit the LLM.

## 7. Why MMR?
Maximal Marginal Relevance (MMR) balances relevance with diversity. If the top 5 chunks all say the exact same thing, providing them to the LLM wastes tokens. MMR penalizes redundant chunks, ensuring the LLM sees a wider variety of relevant information.

## 8. Why semantic caching?
LLM generation is slow and expensive. A semantic cache (using Redis) calculates the embedding of the incoming user query. If the cosine similarity matches a recent query >0.95, RAGX bypasses the LLM and returns the cached answer instantly, cutting latency from seconds to milliseconds.

## 9. How does tenant isolation work?
Identity is verified via JWTs. The `tenant_id` is extracted and forcefully appended to all database queries. For Qdrant, it uses Payload filtering; for Postgres, `WHERE tenant_id = X`. This means it is mathematically impossible for the vector search algorithm to return another tenant's chunk, enforcing security at the data layer, not just the application layer.

## 10. How do you prevent cache leakage?
The semantic cache keys are namespaced by the user's `tenant_id`. A query from Tenant A looking for "Q3 Goals" will generate a different cache hash than the exact same query from Tenant B.

## 11. How does Gemini → Groq fallback work?
RAGX uses a Circuit Breaker pattern wrapped around the LLM orchestrator. If the primary provider (Gemini) times out or throws an error, the system automatically redirects the generated prompt to Groq (running Llama-3) to ensure the user gets an answer. 

## 12. Why use a circuit breaker?
If an external API goes down, you shouldn't sit there waiting for timeouts on every single user request. A circuit breaker tracks failures. Once the failure threshold is hit (e.g., 5 failures), it "opens" the circuit and instantly routes to the fallback provider without even trying the broken primary API, allowing the primary API time to recover.

## 13. What happens when Gemini returns 429?
A 429 RESOURCE_EXHAUSTED means quota is breached. The system detects this specific error code, immediately opens the circuit breaker, and routes the query to Groq to fulfill the request. This was heavily tested during Phase 14 validation.

## 14. How did you evaluate retrieval quality?
I built a programmatic benchmarking suite (Phase 14). I generated a ground-truth dataset mapping complex questions to expected document chunks. The script ran queries against different RAGX pipeline configurations and automatically calculated standard information retrieval metrics.

## 15. What are Recall@K, MRR and nDCG?
- **Recall@K**: Did the relevant document appear anywhere in the top K results?
- **MRR (Mean Reciprocal Rank)**: How far down the list was the first relevant document? (1/rank).
- **nDCG (Normalized Discounted Cumulative Gain)**: Evaluates the entire ranked list, giving higher scores when the most highly relevant documents appear at the very top.

## 16. What are the biggest latency bottlenecks?
1. External LLM generation time (Time-To-First-Token).
2. The Cross-Encoder reranking step (since it requires a heavy inference pass for every retrieved document). RAGX mitigates this by restricting reranking to only the top-K initial candidates.

## 17. What are the limitations?
The evaluation metrics for Generation (F1 / Exact Match) are flawed for LLMs, as LLMs naturally rephrase answers. A true LLM-as-a-judge (RAGAS) would be better. Also, the current lightweight cross-encoder caps out relatively quickly; a commercial reranker (like Cohere) would boost MRR further.

## 18. Why Docker?
Docker ensures the environment is reproducible. RAGX relies on PostgreSQL, Redis, Qdrant, and Neo4j. By defining them all in a `docker-compose.yml`, a new developer can spin up the entire complex architecture with a single `docker compose up` command, avoiding "it works on my machine" issues.

## 19. How does the CI/CD pipeline work?
While a full GitHub Action YAML exists to demonstrate intent, local `pytest` scripts heavily enforce system stability. Any PR must pass 47 regression tests, verify zero security leaks, and ensure Docker containers build cleanly before merging.

## 20. If you had more time, what would you improve?
I would implement streaming responses via WebSockets/Server-Sent Events (SSE) to reduce perceived latency, implement an asynchronous task queue (like Celery) for background document ingestion, and add a dedicated LLM-as-a-judge evaluation pipeline.
