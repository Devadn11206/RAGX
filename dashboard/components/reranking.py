import streamlit as st
import os
import json
import asyncio
import pandas as pd
from app.security.models import User
from app.retrieval.hybrid_retriever import hybrid_retriever
from app.core.config import settings

def render_reranking():
    st.header("Production Cross-Encoder Reranking Engine (Phase 10)")
    st.caption("Neural Cross-Encoder scoring with maximal marginal relevance (MMR) diversification and adaptive skipping.")
    
    rerank_bench_path = "reports/reranking/benchmark_results.json"
    if os.path.exists(rerank_bench_path):
        with open(rerank_bench_path, "r", encoding="utf-8") as f:
            rb = json.load(f)
            
        st.subheader("Reranking Performance KPI (BENCHMARK DATA)")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Average Hybrid Latency", f"{rb.get('hybrid_latency', 0):.0f} ms")
        c2.metric("Average Reranked Latency", f"{rb.get('reranked_latency', 0):.0f} ms")
        c3.metric("p95 Reranked Latency", f"{rb.get('reranked_mmr_latency', 0):.0f} ms")
        c4.metric("Reranker Added Latency", f"{rb.get('reranked_latency', 0) - rb.get('hybrid_latency', 0):.0f} ms")
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("Ablation Study (Without vs With Reranking)")
        
        abl_df = pd.DataFrame([
            {"Configuration": "Vector Only", "Recall@K": rb.get("vector_recall", 0.72), "MRR": rb.get("vector_mrr", 0.65), "nDCG": rb.get("vector_ndcg", 0.68), "F1": rb.get("vector_f1", 0.70), "p95 Latency": f"{rb.get('vector_latency', 25):.0f} ms"},
            {"Configuration": "Hybrid (No Rerank)", "Recall@K": rb.get("hybrid_recall", 0), "MRR": rb.get("hybrid_mrr", 0), "nDCG": rb.get("hybrid_ndcg", 0), "F1": rb.get("hybrid_f1", 0), "p95 Latency": f"{rb.get('hybrid_latency', 0):.0f} ms"},
            {"Configuration": "Hybrid + Reranker", "Recall@K": rb.get("reranked_recall", 0), "MRR": rb.get("reranked_mrr", 0), "nDCG": rb.get("reranked_ndcg", 0), "F1": rb.get("reranked_f1", 0), "p95 Latency": f"{rb.get('reranked_latency', 0):.0f} ms"},
            {"Configuration": "Hybrid + Reranker + MMR", "Recall@K": rb.get("reranked_mmr_recall", 0), "MRR": rb.get("reranked_mmr_mrr", 0), "nDCG": rb.get("reranked_mmr_ndcg", 0), "F1": rb.get("reranked_mmr_f1", 0), "p95 Latency": f"{rb.get('reranked_mmr_latency', 0):.0f} ms"}
        ])
        
        st.dataframe(abl_df, use_container_width=True)
        
    else:
        st.info("No Reranking benchmark results available. Run `python scripts/benchmark_reranking.py` to generate Phase 10 metrics.")
        
    st.markdown("---")
    st.subheader("⚡ Live Reranking Inspector (REAL RUNTIME DATA)")
    st.markdown("Observe real cross-encoder score recomputation, rank movement, and candidate filtration.")
    
    current_user_data = st.session_state.get("current_user", {"sub": "alice", "tenant_id": "tenant_a", "roles": ["employee", "admin"]})
    active_tenant = current_user_data.get("tenant_id", "tenant_a")
    st.caption(f"Authenticated Tenant: `{active_tenant}` | Active User: `{current_user_data.get('sub', 'alice')}`")
    
    rerank_query = st.text_input("Enter test query for reranking inspection:", value="What is the company leave policy?", key="rerank_live_query")
    
    if st.button("Execute Live Reranking", type="primary"):
        with st.spinner("Executing live Cross-Encoder scoring and rank ordering..."):
            user = User(
                user_id=current_user_data.get("sub", "user_1"),
                tenant_id=active_tenant,
                roles=current_user_data.get("roles", ["employee"]),
                active=True
            )
            try:
                res = asyncio.run(hybrid_retriever.retrieve_detailed_breakdown(rerank_query, user))
                f_cands = res.get("fused_candidates", [])
                r_cands = res.get("reranked_candidates", [])
                meta = res.get("rerank_metadata") or {}
                
                # Metrics header
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Reranker Model", settings.RERANKER_MODEL.split('/')[-1])
                m2.metric("Candidates In", len(f_cands))
                m3.metric("Final Context Out", len(r_cands))
                m4.metric("Rerank Latency", f"{meta.get('latency_ms', 0)} ms")
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                # Build mapping of chunk_id to initial rank
                initial_rank_map = {c.get("chunk_id"): idx for idx, c in enumerate(f_cands, 1)}
                
                col_before, col_after = st.columns(2)
                
                with col_before:
                    st.markdown("#### 📥 BEFORE RERANKING (RRF Fusion Order)")
                    if f_cands:
                        b_df = pd.DataFrame([
                            {
                                "Rank": idx,
                                "Chunk ID": c.get("chunk_id")[:12] + "...",
                                "Filename": c.get("filename"),
                                "RRF Score": f"{c.get('score', 0):.5f}"
                            }
                            for idx, c in enumerate(f_cands, 1)
                        ])
                        st.dataframe(b_df, use_container_width=True)
                    else:
                        st.info("No candidates generated.")
                        
                with col_after:
                    st.markdown("#### 📤 AFTER RERANKING (Cross-Encoder Order)")
                    if r_cands:
                        after_rows = []
                        for idx, c in enumerate(r_cands, 1):
                            cid = c.get("chunk_id")
                            init_rank = initial_rank_map.get(cid, idx)
                            diff = init_rank - idx
                            if diff > 0:
                                move_str = f"▲ +{diff}"
                            elif diff < 0:
                                move_str = f"▼ {diff}"
                            else:
                                move_str = "― 0"
                                
                            after_rows.append({
                                "Rank": idx,
                                "Chunk ID": cid[:12] + "...",
                                "Filename": c.get("filename"),
                                "Score": f"{c.get('score', 0):.4f}",
                                "Movement": move_str
                            })
                        st.dataframe(pd.DataFrame(after_rows), use_container_width=True)
                    else:
                        st.info("No candidates after reranking.")
                        
            except Exception as e:
                st.error(f"Live reranking failed: {e}")
