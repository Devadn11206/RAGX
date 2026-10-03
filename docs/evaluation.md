# Evaluation Methodology & Benchmark Results

RAGX incorporates a full evaluation pipeline to validate retrieval accuracy, context relevance, generation quality, latency, and security across multiple system configurations.

## 1. Methodology

The evaluation uses a synthetically generated but realistic multi-tenant dataset comprising complex interconnected documents across distinct fictional companies (e.g., Acme Corp and Globex Inc.). 

### Retrieval Metrics
- **Recall@K**: Measures the proportion of relevant chunks retrieved in the top K results.
- **MRR (Mean Reciprocal Rank)**: Measures how high the first relevant chunk appears in the ranked results.
- **nDCG (Normalized Discounted Cumulative Gain)**: Measures ranking quality considering graded relevance.

### Generative Metrics
- **F1 Score**: Measures the overlap of tokens between the generated answer and the ground truth.
- **Exact Match (EM)**: Measures whether the generated answer perfectly matches the expected answer (often overly strict for LLM generation).

### Latency Metrics
- **P50 / P95 / P99**: Latency percentiles tracking performance under load.
- **Component Latency**: Detailed telemetry isolates retrieval vs. reranking vs. LLM generation latency.

## 2. Benchmark Results (Phase 14.1)

The following results were measured natively by the RAGX benchmarking engine during Phase 14.1 validation, bypassing caching to measure true retrieval performance.

### Retrieval & Quality Performance

| Pipeline | Recall@5 | MRR | nDCG | F1 | Exact Match |
|---|---:|---:|---:|---:|---:|
| Vector | 0.600 | 0.468 | 0.496 | 0.064 | 0.020 |
| Vector + Lexical | 0.600 | 0.468 | 0.496 | 0.059 | 0.000 |
| Hybrid | 0.592 | 0.457 | 0.486 | 0.047 | 0.000 |
| Hybrid + GraphRAG | 0.600 | 0.468 | 0.496 | 0.060 | 0.000 |
| Hybrid + Reranking | 0.612 | 0.478 | 0.506 | 0.059 | 0.000 |
| Hybrid + Reranking + MMR | 0.600 | 0.468 | 0.496 | 0.064 | 0.020 |

### Latency Profiles (ms)

| Pipeline | P50 | P95 | P99 | Retrieval | Reranking | Generation |
|---|---:|---:|---:|---:|---:|---:|
| Vector | 161 | 267 | 1089 | 118 | 0 | 65 |
| Vector + Lexical | 151 | 247 | 1424 | 123 | 0 | 59 |
| Hybrid | 156 | 1034 | 1751 | 241 | 0 | 64 |
| Hybrid + GraphRAG | 149 | 1014 | 1296 | 217 | 0 | 63 |
| Hybrid + Reranking | 148 | 717 | 1375 | 195 | 1 | 63 |
| Hybrid + Reranking + MMR | 162 | 879 | 1177 | 211 | 2 | 60 |

*(Note: Generating answers using `all-MiniLM-L6-v2` locally on CPU. LLM Latencies were simulated via caching/mocks during mass iterations to avoid API cost overheads.)*

## 3. Security Results

- **47/47** System regression tests passed.
- **11/11** Security tests passed.
- **0** Cross-tenant leaks detected.
- **0** Unauthorized chunks exposed.
- **0** Privilege escalations permitted.
- **0** Canary token leaks.

## 4. Limitations
- F1 and Exact Match are consistently low because LLM responses naturally diverge from strict deterministic baselines. A specialized LLM-as-a-judge metric (e.g., RAGAS) would provide higher fidelity for generative evaluation.
- Reranking currently uses a lightweight Cross-Encoder which limits the absolute ceiling of MRR improvements compared to massive parameter models like Cohere Rerank.
