import streamlit as st
import os
import json
import asyncio
import pandas as pd
from app.security.models import User
from app.retrieval.hybrid_retriever import hybrid_retriever

def render_retrieval():
    st.header("Hybrid Retrieval Engine (Phase 9)")
    st.caption("Multi-strategy candidate generation: Dense Vector + BM25 Lexical + GraphRAG with Reciprocal Rank Fusion.")
    
    hybrid_bench_path = "reports/hybrid/benchmark_results.json"
    if os.path.exists(hybrid_bench_path):
        with open(hybrid_bench_path, "r", encoding="utf-8") as f:
            hb = json.load(f)
            
        st.subheader("Retrieval Funnel & Strategy (BENCHMARK DATA)")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Vector Queries", f"{hb.get('vector_usage', 0):.1f}%")
        c2.metric("Lexical Queries", f"{hb.get('lexical_usage', 0):.1f}%")
        c3.metric("Graph Queries", f"{hb.get('graph_usage', 0):.1f}%")
        c4.metric("Cross-Encoder Reranks", f"{hb.get('reranker_usage', 0):.1f}%")
        
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2 = st.columns([2, 1])
        with col1:
            st.subheader("Performance vs Single Retrievers")
            comp_df = pd.DataFrame([
                {"Strategy": "Vector Only", "Recall@K": hb.get("vector_recall", 0), "MRR": hb.get("vector_mrr", 0), "F1": hb.get("vector_f1", 0), "Latency": hb.get("vector_latency", 0)},
                {"Strategy": "Vector + Lexical", "Recall@K": hb.get("vector_lexical_recall", 0), "MRR": hb.get("vector_lexical_mrr", 0), "F1": hb.get("vector_lexical_f1", 0), "Latency": hb.get("vector_lexical_latency", 0)},
                {"Strategy": "Full Hybrid (No Rerank)", "Recall@K": hb.get("hybrid_recall", 0), "MRR": hb.get("hybrid_mrr", 0), "F1": hb.get("hybrid_f1", 0), "Latency": hb.get("hybrid_latency", 0)},
                {"Strategy": "Full Hybrid + Reranker", "Recall@K": hb.get("reranked_recall", 0), "MRR": hb.get("reranked_mrr", 0), "F1": hb.get("reranked_f1", 0), "Latency": hb.get("reranked_latency", 0)}
            ])
            st.dataframe(comp_df, use_container_width=True)
            
        with col2:
            st.subheader("Average Retrieval Pipeline")
            st.metric("Avg Raw Candidates", hb.get('avg_raw_candidates', 0))
            st.metric("Avg Unique Candidates", hb.get('avg_unique_candidates', 0))
            st.metric("Avg Final Context Chunks", hb.get('avg_final_context', 0))
            st.metric("Avg Total Latency", f"{hb.get('total_latency_ms', 0):.0f} ms")
        
    else:
        st.info("No Hybrid Retrieval benchmark results available. Run `python scripts/hybrid_benchmark.py` to generate Phase 9 metrics.")
        
    st.markdown("---")
    st.subheader("🔍 Interactive Live Retrieval Explorer (REAL RUNTIME DATA)")
    st.markdown("Execute a query through the live multi-strategy retrieval engine to observe candidate generation, RRF score aggregation, and reranking across the active tenant.")
    
    current_user_data = st.session_state.get("current_user", {"sub": "alice", "tenant_id": "tenant_a", "roles": ["employee", "admin"]})
    active_tenant = current_user_data.get("tenant_id", "tenant_a")
    st.caption(f"Authenticated Tenant: `{active_tenant}` | Active User: `{current_user_data.get('sub', 'alice')}`")
    
    query = st.text_input("Enter a query to inspect candidate generation:", value="What are the standard working hours?", key="ret_explorer_query")
    
    if st.button("Execute Live Retrieval", type="primary"):
        with st.spinner("Executing real multi-retriever search and RRF fusion..."):
            user = User(
                user_id=current_user_data.get("sub", "user_1"),
                tenant_id=active_tenant,
                roles=current_user_data.get("roles", ["employee"]),
                active=True
            )
            try:
                res = asyncio.run(hybrid_retriever.retrieve_detailed_breakdown(query, user))
                
                v_cands = res.get("vector_candidates", [])
                l_cands = res.get("lexical_candidates", [])
                g_cands = res.get("graph_candidates", [])
                f_cands = res.get("fused_candidates", [])
                r_cands = res.get("reranked_candidates", [])
                
                st.markdown("### 1. Raw Candidate Streams")
                c1, c2, c3 = st.columns(3)
                
                with c1:
                    st.markdown(f"#### 🔵 Vector Dense ({len(v_cands)})")
                    if v_cands:
                        for idx, c in enumerate(v_cands, 1):
                            st.markdown(f"**Rank {idx}** (Score: `{c.get('score', 0):.4f}`)\n- `ID`: {c.get('chunk_id')[:12]}...\n- `File`: {c.get('filename')}\n- `Tenant`: {active_tenant}")
                    else:
                        st.info("No vector matches.")
                        
                with c2:
                    st.markdown(f"#### 🟢 Lexical BM25 ({len(l_cands)})")
                    if l_cands:
                        for idx, c in enumerate(l_cands, 1):
                            st.markdown(f"**Rank {idx}** (Score: `{c.get('score', 0):.4f}`)\n- `ID`: {c.get('chunk_id')[:12]}...\n- `File`: {c.get('filename')}\n- `Tenant`: {active_tenant}")
                    else:
                        st.info("No lexical matches.")
                        
                with c3:
                    st.markdown(f"#### 🟣 GraphRAG Multi-Hop ({len(g_cands)})")
                    if g_cands:
                        for idx, c in enumerate(g_cands, 1):
                            st.markdown(f"**Rank {idx}** (Score: `{c.get('score', 0):.4f}`)\n- `ID`: {c.get('chunk_id')[:12]}...\n- `File`: {c.get('filename')}\n- `Tenant`: {active_tenant}")
                    else:
                        st.info("No graph matches.")
                        
                st.markdown("---")
                st.markdown("### 2. Reciprocal Rank Fusion (RRF) & Final Reranked Context")
                
                col_fused, col_reranked = st.columns(2)
                with col_fused:
                    st.markdown(f"#### 🔗 RRF Fused Candidates ({len(f_cands)})")
                    if f_cands:
                        f_df = pd.DataFrame([
                            {
                                "Rank": idx,
                                "Chunk ID": c.get("chunk_id")[:12] + "...",
                                "File": c.get("filename"),
                                "Method": c.get("retrieval_method"),
                                "RRF Score": f"{c.get('score', 0):.5f}"
                            }
                            for idx, c in enumerate(f_cands, 1)
                        ])
                        st.dataframe(f_df, use_container_width=True)
                    else:
                        st.info("No candidates fused.")
                        
                with col_reranked:
                    st.markdown(f"#### 🏆 Final Reranked Candidates ({len(r_cands)})")
                    if r_cands:
                        r_df = pd.DataFrame([
                            {
                                "Rank": idx,
                                "Chunk ID": c.get("chunk_id")[:12] + "...",
                                "File": c.get("filename"),
                                "Method": c.get("retrieval_method"),
                                "Reranker Score": f"{c.get('score', 0):.4f}"
                            }
                            for idx, c in enumerate(r_cands, 1)
                        ])
                        st.dataframe(r_df, use_container_width=True)
                    else:
                        st.info("No reranked candidates.")
                        
            except Exception as e:
                st.error(f"Retrieval execution failed: {e}")
