import streamlit as st
import os
import json
import asyncio
import pandas as pd
from app.infrastructure.neo4j import neo4j_client

def render_graphrag():
    st.header("Knowledge Graph & Multi-Hop Reasoning (Phase 8)")
    st.caption("Entity-relationship extraction and multi-hop traversal with strict multi-tenant graph isolation.")
    
    graph_bench_path = "reports/graph/benchmark_results.json"
    if os.path.exists(graph_bench_path):
        with open(graph_bench_path, "r", encoding="utf-8") as f:
            gb = json.load(f)
            
        st.subheader("1. Hybrid GraphRAG KPI Dashboard (BENCHMARK DATA)")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Graph Queries Executed", gb.get("graph_queries", 0))
        c2.metric("Graph Usage Proportion", f"{gb.get('graph_usage_percent', 0):.1f}%")
        c3.metric("Average Traversal Hops", f"{gb.get('avg_graph_hops', 0):.1f}")
        c4.metric("Graph Retrieval Latency", f"{gb.get('graph_latency_ms', 0):.0f} ms")
        
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2 = st.columns([1, 1])
        with col1:
            st.subheader("Multi-Hop Evaluation (HotpotQA)")
            e1, e2 = st.columns(2)
            e1.metric("Vector-Only Exact Match", f"{gb.get('vector_exact_match', 0):.2f}%")
            e2.metric("Hybrid Graph Exact Match", f"{gb.get('graph_exact_match', 0):.2f}%", 
                     delta=f"{gb.get('graph_exact_match', 0) - gb.get('vector_exact_match', 0):.2f}%")
            st.metric("Multi-Hop Reasoning F1 Score", f"{gb.get('graph_f1', 0):.2f}%")
        
        with col2:
            st.subheader("Graph Economics")
            st.metric("Graph Extraction Cumulative Cost", f"${gb.get('extraction_cost', 0):.4f}")
            st.markdown("Knowledge graphs carry an upfront extraction cost during ingestion, but they dramatically improve fact recall for multi-hop questions.")
            
    else:
        st.info("No GraphRAG benchmark results available. Run `python scripts/graph_benchmark.py` to generate Phase 8 metrics.")
        
    st.markdown("---")
    st.subheader("2. Knowledge Graph Traversal Explorer (REAL RUNTIME DATA)")
    
    current_user_data = st.session_state.get("current_user", {"sub": "alice", "tenant_id": "tenant_a", "roles": ["employee", "admin"]})
    active_tenant = current_user_data.get("tenant_id", "tenant_a")
    st.caption(f"Authenticated Tenant Scope: `{active_tenant}` (Cross-tenant graph queries are strictly prohibited)")
    
    async def fetch_tenant_graph(tenant_id: str):
        if not neo4j_client.driver:
            await neo4j_client.connect()
        if not neo4j_client.driver:
            return []
        cypher = """
        MATCH (s:Entity {tenant_id: $tenant_id})-[r:RELATED_TO {tenant_id: $tenant_id}]->(t:Entity {tenant_id: $tenant_id})
        RETURN s.name AS source, s.type AS s_type, r.relation_type AS rel, t.name AS target, t.type AS t_type
        LIMIT 25
        """
        results = []
        try:
            async with neo4j_client.driver.session() as session:
                cursor = await session.run(cypher, tenant_id=tenant_id)
                async for row in cursor:
                    results.append({
                        "Source Entity": row["source"],
                        "Source Type": row["s_type"],
                        "Relationship": row["rel"],
                        "Target Entity": row["target"],
                        "Target Type": row["t_type"]
                    })
        except Exception:
            return []
        return results

    try:
        graph_data = asyncio.run(fetch_tenant_graph(active_tenant))
        if graph_data:
            st.markdown(f"##### Tenant `{active_tenant}` Knowledge Subgraph ({len(graph_data)} relations)")
            g_df = pd.DataFrame(graph_data)
            st.dataframe(g_df, use_container_width=True)
            
            # Render Mermaid diagram dynamically
            mermaid_lines = ["graph LR"]
            for row in graph_data[:10]:
                src = row["Source Entity"].replace(" ", "_").replace("-", "_")
                tgt = row["Target Entity"].replace(" ", "_").replace("-", "_")
                rel = row["Relationship"]
                mermaid_lines.append(f"    {src}[\"{row['Source Entity']} ({row['Source Type']})\"] -- \"{rel}\" --> {tgt}[\"{row['Target Entity']} ({row['Target Type']})\"]")
                
            mermaid_str = "\n".join(mermaid_lines)
            st.markdown("##### Topological Subgraph Visualization")
            st.markdown(f"```mermaid\n{mermaid_str}\n```")
        else:
            st.info(f"No graph relations found for tenant `{active_tenant}` yet. Index multi-entity documents (or run `python scripts/ingest_golden_dataset.py`) to build the knowledge graph.")
    except Exception as e:
        st.warning(f"Could not connect to Neo4j knowledge store: {e}")
