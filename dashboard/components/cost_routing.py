import streamlit as st
import os
import json
import time
import pandas as pd
from app.telemetry.service import telemetry_service
from app.llm.orchestrator import llm_orchestrator
from app.llm.circuit_breaker import gemini_circuit_breaker
from app.core.config import settings

def render_cost_routing():
    st.header("Cost Intelligence & Provider Resilience (Phases 6 & 7)")
    st.caption("Intelligent cost-aware routing with automatic circuit-breaker protected failover from Gemini to Groq.")
    
    st.markdown("---")
    st.subheader("1. Live Provider Telemetry (REAL RUNTIME DATA)")
    
    try:
        metrics = telemetry_service.get_detailed_metrics()
        total_q = metrics.get("total_queries", 0)
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total LLM Calls", f"{total_q:,}")
        c2.metric("Primary (Gemini) Calls", metrics.get("gemini_count", 0))
        c3.metric("Fallback (Groq) Calls", metrics.get("groq_count", 0))
        c4.metric("Fallback Rate", f"{metrics.get('fallback_rate', 0):.1f}%")
        
        st.markdown("<br>", unsafe_allow_html=True)
        c5, c6, c7, c8 = st.columns(4)
        c5.metric("Small Tier Usage", metrics.get("small_count", 0))
        c6.metric("Large Tier Usage", metrics.get("large_count", 0))
        c7.metric("Cumulative LLM Cost", f"${metrics.get('total_cost', 0.0):.5f}")
        cb_state = gemini_circuit_breaker.state
        c8.markdown(f"**Circuit Breaker:** <span class='status-badge {'status-operational' if cb_state == 'CLOSED' else 'status-degraded'}'>{cb_state}</span>", unsafe_allow_html=True)
        
        if total_q > 0:
            st.markdown("<br>", unsafe_allow_html=True)
            col_chart1, col_chart2 = st.columns(2)
            with col_chart1:
                st.markdown("##### Provider Share (Live)")
                p_df = pd.DataFrame({
                    "Provider": ["Gemini (Primary)", "Groq (Fallback)"],
                    "Invocations": [metrics.get("gemini_count", 0), metrics.get("groq_count", 0)]
                })
                st.bar_chart(p_df.set_index("Provider"), use_container_width=True)
                
            with col_chart2:
                st.markdown("##### Model Tier Distribution (Live)")
                t_df = pd.DataFrame({
                    "Tier": ["Small (Flash / 27B)", "Large (Pro / 120B)"],
                    "Invocations": [metrics.get("small_count", 0), metrics.get("large_count", 0)]
                })
                st.bar_chart(t_df.set_index("Tier"), use_container_width=True)
        else:
            st.info("Insufficient runtime data. Run live queries or the failover test below to generate live provider telemetry.")
            
    except Exception as e:
        st.error(f"Failed to fetch telemetry metrics: {e}")

    st.markdown("---")
    st.subheader("2. Controlled Provider Failover Test (LIVE EXECUTION)")
    st.markdown("Test the automated resilience pipeline: Primary Gemini Call → 10s Timeout / 503 Overload Detection → Circuit Breaker → Instant Groq Fallback.")
    
    if st.button("⚡ Run Live Provider Failover Test", type="primary"):
        test_prompt = "Explain in one sentence why automated failover is essential for enterprise AI pipelines."
        with st.spinner("Executing live failover probe (Gemini → Circuit Breaker → Groq)..."):
            t_start = time.time()
            res = llm_orchestrator.generate(test_prompt, model_name=settings.ROUTER_SMALL_MODEL, is_test_run=True)
            t_total = (time.time() - t_start) * 1000
            
            st.markdown("##### Test Results")
            r1, r2, r3, r4 = st.columns(4)
            r1.metric("Responding Provider", res.provider.upper())
            r2.metric("Active Model", res.model)
            r3.metric("Fallback Activated", "YES" if res.fallback_used else "NO")
            r4.metric("Total Probe Latency", f"{t_total:.0f} ms")
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.success(f"**Generated Answer:** {res.content}")
            st.caption(f"Circuit Breaker State: `{gemini_circuit_breaker.state}` | Fallback Reason: `{res.fallback_reason or 'None (Primary Succeeded)'}`")

    st.markdown("---")
    st.subheader("3. Historical Routing & Resilience Benchmarks (BENCHMARK DATA)")
    
    col_bench1, col_bench2 = st.columns(2)
    with col_bench1:
        st.markdown("##### Cost-Aware Routing Benchmark")
        router_bench_path = "reports/router/benchmark_results.json"
        if os.path.exists(router_bench_path):
            with open(router_bench_path, "r", encoding="utf-8") as f:
                rb = json.load(f)
            b1, b2 = st.columns(2)
            b1.metric("Cost Reduction vs Always-Large", f"{rb.get('cost_reduction', 0):.1f}%")
            b2.metric("Routing Accuracy", f"{rb.get('router_quality', 0):.2f}")
        else:
            st.info("No router benchmark file found.")
            
    with col_bench2:
        st.markdown("##### Provider Fallback Benchmark")
        prov_bench_path = "reports/provider/benchmark_results.json"
        if os.path.exists(prov_bench_path):
            with open(prov_bench_path, "r", encoding="utf-8") as f:
                pb = json.load(f)
            p1, p2 = st.columns(2)
            p1.metric("Simulated Gemini Availability", f"{pb.get('gemini_success_rate', 0):.1f}%")
            p2.metric("Final Pipeline Success Rate", f"{pb.get('final_success_rate', 0):.1f}%")
        else:
            st.info("No provider benchmark file found.")
