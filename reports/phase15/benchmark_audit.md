# RAGX Final Benchmark Audit Report

## 1. Executive Summary
This report traces every benchmark metric reported in the repository to its underlying source to ensure that all claims made in the RAGX portfolio presentation are scientifically honest, backed by verifiable data, and accurately categorized. Misleading, estimated, or sample-only metrics have been separated from rigorous measurements.

## 2. Metrics Audited

### Vector Baseline
- **Metric**: Recall@5
- **Value**: 0.600
- **Classification**: VERIFIED MEASURED
- **Source file**: `reports/phase14/final_benchmark_table.csv`
- **Verified?**: YES (Note: The Phase 14 report text erroneously listed 0.625 from an earlier run, but the final generated CSV confirms 0.600).

- **Metric**: MRR
- **Value**: 0.468
- **Classification**: VERIFIED MEASURED
- **Source file**: `reports/phase14/final_benchmark_table.csv`
- **Verified?**: YES

- **Metric**: F1
- **Value**: 0.064
- **Classification**: VERIFIED MEASURED
- **Source file**: `reports/phase14/final_benchmark_table.csv`
- **Verified?**: YES

- **Metric**: Exact Match
- **Value**: 0.020
- **Classification**: VERIFIED MEASURED
- **Source file**: `reports/phase14/final_benchmark_table.csv`
- **Verified?**: YES

- **Metric**: P50 Latency
- **Value**: 161 ms
- **Classification**: VERIFIED MEASURED
- **Source file**: `reports/phase14/final_benchmark_table.csv`
- **Verified?**: YES

### Vector + Lexical
- **Metric**: Recall@5
- **Value**: 0.600
- **Classification**: VERIFIED MEASURED
- **Source file**: `reports/phase14/final_benchmark_table.csv`
- **Verified?**: YES

- **Metric**: MRR
- **Value**: 0.468
- **Classification**: VERIFIED MEASURED
- **Source file**: `reports/phase14/final_benchmark_table.csv`
- **Verified?**: YES

- **Metric**: F1
- **Value**: 0.059
- **Classification**: VERIFIED MEASURED
- **Source file**: `reports/phase14/final_benchmark_table.csv`
- **Verified?**: YES

- **Metric**: Exact Match
- **Value**: 0.000
- **Classification**: VERIFIED MEASURED
- **Source file**: `reports/phase14/final_benchmark_table.csv`
- **Verified?**: YES

- **Metric**: P50 Latency
- **Value**: 151 ms
- **Classification**: VERIFIED MEASURED
- **Source file**: `reports/phase14/final_benchmark_table.csv`
- **Verified?**: YES

### Hybrid (Vector + Lexical + GraphRAG)
- **Metric**: Recall@5
- **Value**: 0.600
- **Classification**: VERIFIED MEASURED
- **Source file**: `reports/phase14/final_benchmark_table.csv` (Row: Hybrid + GraphRAG)
- **Verified?**: YES

- **Metric**: MRR
- **Value**: 0.468
- **Classification**: VERIFIED MEASURED
- **Source file**: `reports/phase14/final_benchmark_table.csv`
- **Verified?**: YES

- **Metric**: F1
- **Value**: 0.060
- **Classification**: VERIFIED MEASURED
- **Source file**: `reports/phase14/final_benchmark_table.csv`
- **Verified?**: YES

- **Metric**: P50 Latency
- **Value**: 149 ms
- **Classification**: VERIFIED MEASURED
- **Source file**: `reports/phase14/final_benchmark_table.csv`
- **Verified?**: YES

### Semantic Cache
- **Metric**: Cache Hit Rate / Latency
- **Value**: 100% hits, ~5ms latency on 5 repeated queries.
- **Classification**: VALIDATED SAMPLE
- **Source file**: `reports/phase14/PHASE14_FINAL_BENCHMARK_REPORT.md`
- **Verified?**: YES (Classified strictly as sample validation).

### Reranking + MMR
- **Metric**: Recall@5
- **Value**: 0.600
- **Classification**: VERIFIED MEASURED
- **Source file**: `reports/phase14/final_benchmark_table.csv` (Row: Hybrid + Reranking + MMR)
- **Verified?**: YES

### GraphRAG
- **Metric**: Exact Match = 71.5%, F1 = 74.8%
- **Value**: 71.5% / 74.8%
- **Classification**: UNSUPPORTED
- **Source file**: Not present in Phase 14 validation suite; these were theoretical or from an older different pipeline. 
- **Verified?**: NO. These claims have been purged. The actual measured F1 for Hybrid+GraphRAG is 0.060.

### Security
- **Metric**: 11/11 tests, 0 cross-tenant leaks.
- **Value**: 11
- **Classification**: VERIFIED MEASURED
- **Source file**: `reports/phase14/PHASE14_FINAL_BENCHMARK_REPORT.md` (and terminal output of Phase 15 runs).
- **Verified?**: YES

## 3. Verified Measurements
Only metrics sourced directly from `reports/phase14/final_benchmark_table.csv` will be included in the primary README tables.

## 4. Sample/Validation Results
Cache hit rates and provider fallback success are confirmed via sample execution and will be described contextually rather than as absolute production guarantees.

## 5. Estimated/Expected Results
No estimated results will be presented in the README.

## 6. Unsupported Claims Removed
- Removed any reference to GraphRAG achieving 71.5% Exact Match.
- Removed claims of "state-of-the-art" or "100% uptime".
- Removed Expected Recall@5 (~0.72) from Reranking/MMR discussions as it was not achieved in the final Phase 14.1 benchmark (actual achieved was 0.612 for Hybrid+Reranking).

## 7. README Changes
The README has been comprehensively updated to separate metrics into factual, isolated categories (Retrieval, GraphRAG, Cache, Security, Fallback) and clearly states the limitations of the dataset.

## 8. Dashboard Integrity
Dashboard metrics must be treated as "Demo / Simulated" if they do not derive directly from the DB. 

## 9. Dataset
- **Questions**: 50
- **Documents**: 3
- **Categories**: Factual, Semantic, Lexical, Multi-hop, Comparison, Policy, Adversarial, Tenant-specific.
- **Verified?**: YES, via `reports/phase14/PHASE14_FINAL_BENCHMARK_REPORT.md` Section 3.

## 10. Methodology
Documented in README: all configurations were tested sequentially against the exact same 50-question dataset using local CPU inference, ensuring a controlled variable environment. 

## 11. Limitations
Strictly acknowledged in README that token-level F1 is fundamentally flawed for verbose LLMs, testing was on a minimal 3-document corpus, and execution was purely CPU-bound.

## 12. Final Benchmark Integrity Status
**BENCHMARK CLAIMS — VERIFIED WITH LIMITATIONS**
