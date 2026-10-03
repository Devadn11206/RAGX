import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from app.telemetry.service import telemetry_service

def render_analytics():
    st.header("System Analytics & Telemetry")

    st.subheader("Global System Telemetry")

    # Safe default — overwritten if DB is accessible
    metrics = {
        "total_queries": 0, "success_rate": 0.0, "avg_latency": 0.0, "fallback_rate": 0.0,
        "gemini_count": 0, "groq_count": 0, "small_count": 0, "large_count": 0,
        "p50_latency": 0.0, "p95_latency": 0.0, "total_cost": 0.0,
        "successful_queries": 0, "failed_queries": 0, "fallback_count": 0,
    }

    try:
        metrics = telemetry_service.get_global_metrics()

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Platform Queries", f"{metrics['total_queries']:,}")
        c2.metric("Overall Success Rate", f"{metrics['success_rate']:.1f}%")
        c3.metric("Avg Provider Latency", f"{metrics['avg_latency']:.0f} ms")
        c4.metric("Fallback Rate", f"{metrics['fallback_rate']:.1f}%")

        c5, c6, c7, c8 = st.columns(4)
        c5.metric("p50 Latency", f"{metrics['p50_latency']:.0f} ms")
        c6.metric("p95 Latency", f"{metrics['p95_latency']:.0f} ms")
        c7.metric("Total LLM Cost", f"${metrics['total_cost']:.4f}")
        c8.metric("Failed Queries", metrics['failed_queries'])
    except Exception as e:
        st.warning("No production data available or database uninitialized.")
        st.error(str(e))

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("LLM Provider Distribution")
        if metrics['total_queries'] > 0:
            mix_llm = pd.DataFrame({
                "Provider": ["Gemini (Primary)", "Groq (Fallback)"],
                "Volume": [metrics['gemini_count'], metrics['groq_count']]
            })
            st.bar_chart(mix_llm.set_index("Provider"), use_container_width=True)
        else:
            st.info("No production data available. Run queries via the Chat page to populate analytics.")

    with col2:
        st.subheader("Model Tier Distribution")
        if metrics['total_queries'] > 0:
            mix_tier = pd.DataFrame({
                "Tier": ["Small (Flash/8B)", "Large (Pro/70B)"],
                "Volume": [metrics['small_count'], metrics['large_count']]
            })
            st.bar_chart(mix_tier.set_index("Tier"), use_container_width=True)
        else:
            st.info("No production data available.")

    st.markdown("---")
    st.subheader("Recent Request Traces")
    try:
        traces = telemetry_service.get_recent_traces(limit=20)
        if traces:
            df_traces = pd.DataFrame(traces)
            st.dataframe(df_traces, use_container_width=True)
        else:
            st.info("No recent traces found. Run queries via the Chat page.")
    except Exception as e:
        st.warning(f"Could not load traces: {e}")
