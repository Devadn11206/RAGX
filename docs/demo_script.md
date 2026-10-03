# RAGX Portfolio Demo Script

This script provides a 3-5 minute coherent engineering story to demonstrate RAGX to a technical recruiter or engineering interviewer.

## 1. Introduction (0:00 - 0:30)
* **Goal**: Establish that RAGX is an engineering platform, not a simple wrapper.
* **Action**: Open the GitHub `README.md` or the Dashboard Overview page.
* **Talking Points**: "This is RAGX, a multi-tenant, hybrid-retrieval RAG platform. Unlike standard tutorials that just dump text into a vector database, I built this to handle production complexities: strict tenant isolation, performance optimization via semantic caching, and resilience via API circuit breakers."

## 2. Multi-Tenant Chat & Hybrid Retrieval (0:30 - 1:30)
* **Goal**: Show accurate retrieval and citations.
* **Action**: Open the Streamlit Dashboard **Chat** view. Log in as "Acme Employee" and ask: *"What are our Q3 financial goals?"*
* **Talking Points**: "Notice how fast it responded. Under the hood, this isn't just vector search. It executed Dense Vector search, BM25 Lexical search, and Graph traversal in parallel, fused the results with RRF, and reranked them. Look at the citations—it securely pulled only Acme documents."

## 3. Semantic Caching & Latency (1:30 - 2:30)
* **Goal**: Demonstrate performance optimizations.
* **Action**: Ask the exact same question again. Open the **System Analytics / Pipeline Trace**.
* **Talking Points**: "This time it was nearly instant. The telemetry shows a cache hit. Instead of paying the cost of the LLM generation and network latency, the Redis semantic cache recognized the semantic intent and returned the prior response. This drastically cuts cloud API costs at scale."

## 4. Resilience & Fallback (2:30 - 3:30)
* **Goal**: Highlight robust backend engineering.
* **Action**: (If possible) Trigger or simulate a Gemini 429 Rate Limit, or simply show the logs from Phase 14 validation.
* **Talking Points**: "Production LLMs fail or rate-limit you. I implemented a Circuit Breaker pattern. If Gemini hits a 429 Quota Exhausted error, the orchestrator immediately opens the circuit and falls back to Groq Llama-3. The user never sees an error, just a slightly different citation indicating the fallback provider."

## 5. Security & Evaluation Validation (3:30 - 4:30)
* **Goal**: Prove the claims with data.
* **Action**: Show the GitHub Actions output or the terminal output of the test suites. Show the Benchmark Table.
* **Talking Points**: "Finally, I didn't just guess that it works. The system has 47 regression tests and 11 strict security tests. It actively attempts cross-tenant data leaks and privilege escalations, and blocks them 100% of the time. The hybrid retrieval pipeline improved MRR and nDCG significantly over a baseline vector-only approach, which I proved through programmatic benchmarking."
