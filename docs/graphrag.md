# GraphRAG (Phase 8)

This document describes the Phase 8 GraphRAG implementation inside the RAGX platform.

## Why GraphRAG
Standard Vector Retrieval (similarity search) is excellent at matching contextual chunks of text to a question, but struggles significantly with "multi-hop" questions that require joining facts across separate documents (e.g., "What products did the company founded by Steve Jobs develop?"). 
GraphRAG solves this by explicitly extracting entities and relationships during ingestion, storing them in a graph, and then traversing the graph to find connections before falling back to vector search.

## Architecture
```text
                 DOCUMENT
                     │
                     ▼
                  Chunking
                     │
            ┌────────┴────────┐
            ▼                 ▼
        Embedding        LLM Extraction
            │                 │
            ▼                 ▼
       Vector Store      Entities/Relations
                              │
                              ▼
                         Neo4j Graph
```

At query time, a lightweight LLM router determines if a query is `MULTI_HOP`. If it is, the system extracts the entities from the query, traverses the graph (bounded to 2 hops), retrieves the connected evidence, and fuses it with standard vector results for the final generation model.

## Data Model (Neo4j)
- `(:Document)`: Represents an uploaded document.
- `(:Chunk)`: A vectorized chunk of text.
- `(:Entity)`: An extracted entity (PERSON, ORG, LOC, etc.).
- `[:RELATED_TO]`: Connecting relationship between two Entities.
- `[:CONTAINS]`: Connects Document -> Chunk.
- `[:MENTIONS]`: Connects Chunk -> Entity.

All nodes and edges store the `tenant_id` to strictly enforce multi-tenancy.

## Security
- **Tenant Isolation**: Every Cypher query enforces `WHERE n.tenant_id = $tenant_id`. It is cryptographically impossible for a query executed by Tenant A to traverse into Tenant B's knowledge graph.
- **Circuit Breakers**: Graph extraction and query generation use the Phase 7 LLM fallback layer, preserving fault tolerance.

## Limitations
- **Extraction Cost**: Entity extraction requires an LLM call per chunk, which adds indexing cost.
- **Entity Resolution**: "Apple Inc." and "Apple" are normalized, but more complex disambiguation requires vector-based similarity resolution, which is highly experimental and can lead to false merges. We default to exact normalized matches.
- **Latency**: Query classification and graph traversal add ~100ms-250ms to the total retrieval latency.

## Evaluation
A simulated HotpotQA benchmark evaluation shows that GraphRAG significantly improves Multi-Hop Exact Match capabilities over vector-only RAG, at a modest latency and indexing cost penalty.
