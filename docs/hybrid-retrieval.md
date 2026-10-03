# Hybrid Retrieval Engine (Phase 9)

## Architecture Overview
The Hybrid Retrieval Engine intelligently routes and merges multiple retrieval strategies to build the optimal context for generation.

```text
                         USER QUERY
                              │
                              ▼
                     Query Analyzer
                              │
                       Retrieval Router (Auto Mode)
                              │
              ┌───────────────┼───────────────┐
              │               │               │
              ▼               ▼               ▼
          VECTOR           LEXICAL          GRAPH
        RETRIEVER         RETRIEVER       RETRIEVER
        (Qdrant)         (Postgres FTS)   (Neo4j)
              │               │               │
              └───────────────┼───────────────┘
                              ▼
                       Candidate Fusion
                              │
                        RRF (Reciprocal Rank Fusion)
                              │
                         Deduplication (by Chunk ID)
                              │
                           Reranker (Cross-Encoder)
                              │
                       Context Selection (Budget: Max 8)
                              │
                     Cost-Aware Router
                              │
                       Gemini → Groq
                              │
                           Answer
```

## Retrieval Strategies
1. **Vector Retrieval**: Uses SentenceTransformers (`all-MiniLM-L6-v2`) and Qdrant to find semantically similar chunks. Great for conceptual queries.
2. **Lexical Retrieval**: Uses PostgreSQL Full-Text Search (`tsvector`) to perform exact keyword matching (BM25 equivalent). Essential for product IDs, error codes, and exact terminology.
3. **Graph Retrieval**: Uses Neo4j Knowledge Graph (Phase 8) to traverse relationships and answer multi-hop queries.

## Query Routing
The system supports specific query modes (`vector`, `lexical`, `graph`, `hybrid`).
In `auto` mode (default), the `QueryAnalyzer` uses an LLM to determine the complexity of the query and which retrieval modes to trigger. It extracts entities and decides if the query requires multi-hop traversal, falling back to Vector+Lexical if the LLM classification fails.

## Reciprocal Rank Fusion (RRF)
Raw scores from Vector, Lexical, and Graph retrieval are incompatible. We use RRF to fuse them:
`score = 1.0 / (RRF_K + rank + 1)`
Where `RRF_K` is 60.

## Reranking
Fused candidates are re-scored using a Cross-Encoder (`ms-marco-MiniLM-L-6-v2`), which significantly improves the MRR (Mean Reciprocal Rank) before passing them to the final LLM.

## Security (Phase 3 Integration)
- Every single retriever operates securely.
- Lexical Retriever pushes ACL validation onto the Qdrant payload exactly like the Vector Retriever.
- Graph Retriever pushes ACL verification on the resolved nodes.
- At no point does unauthorized context enter the reranker or candidate fusion layer.

## Limitations
- **Latency**: Reranking and Graph Extraction add significant latency to the retrieval pipeline (Total p95: ~1205ms).
- **Compute Cost**: Cross-Encoders require more CPU/GPU resources than bi-encoders.
- **Storage**: Lexical search requires storing `tsvector` indexed text in PostgreSQL alongside the Qdrant vectors.
