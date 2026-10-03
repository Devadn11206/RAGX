import streamlit as st
import requests
import os
import time
import sqlite3
from app.telemetry.service import telemetry_service
from app.core.config import settings

API_URL = os.getenv("API_URL", "http://localhost:8000")

def render_overview():
    st.markdown("## RAGX")
    st.markdown("### Enterprise Intelligent Retrieval Platform")
    st.caption("Understand. Retrieve. Reason.")
    
    st.markdown("---")
    st.subheader("System Health & Service Dependencies")
    st.caption("Live Status Verified via Backend Health Probes")
    
    api_status = "OFFLINE"
    api_lat = 0
    services = {}
    
    try:
        start = time.time()
        res = requests.get(f"{API_URL}/health/detailed", timeout=3)
        api_lat = (time.time() - start) * 1000
        if res.status_code == 200:
            api_status = "ONLINE"
            services = res.json().get("services", {})
        elif res.status_code == 503:
            api_status = "DEGRADED"
            services = res.json().get("services", {})
        else:
            api_status = "OFFLINE"
    except Exception:
        api_status = "OFFLINE"
        
    # Check Telemetry DB
    telemetry_status = "OFFLINE"
    try:
        if os.path.exists("/tmp/telemetry.db"):
            with sqlite3.connect("/tmp/telemetry.db") as conn:
                conn.execute("SELECT 1")
            telemetry_status = "ONLINE"
    except Exception:
        telemetry_status = "OFFLINE"
        
    # Provider statuses
    gemini_status = "ONLINE" if settings.GEMINI_API_KEY else "OFFLINE"
    groq_status = "ONLINE" if settings.GROQ_API_KEY else "OFFLINE"
    
    # Overall badge
    if api_status == "ONLINE" and telemetry_status == "ONLINE":
        st.markdown("<div class='status-badge status-operational'>System Status: Operational</div>", unsafe_allow_html=True)
    elif api_status == "DEGRADED" or groq_status == "ONLINE":
        st.markdown("<div class='status-badge status-degraded'>System Status: Degraded (Failover Active)</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='status-badge status-degraded'>System Status: Critical / Offline</div>", unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Row 1 of Services
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("FastAPI Core", api_status, f"{api_lat:.0f} ms" if api_status != "OFFLINE" else "N/A")
    c2.metric("Telemetry DB (SQLite)", telemetry_status)
    c3.metric("PostgreSQL (Relational/Audit)", services.get("postgres", "OFFLINE").upper())
    c4.metric("Qdrant (Vector DB)", services.get("qdrant", "OFFLINE").upper())
    
    # Row 2 of Services
    st.markdown("<br>", unsafe_allow_html=True)
    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Neo4j (Knowledge Graph)", services.get("neo4j", "OFFLINE").upper())
    c6.metric("Gemini API (Primary LLM)", gemini_status)
    c7.metric("Groq API (Fallback LLM)", groq_status)
    c8.metric("Redis Cache Store", services.get("redis", "OFFLINE").upper())
    
    st.markdown("---")
    st.subheader("Live Telemetry Key Performance Indicators (REAL RUNTIME DATA)")
    
    try:
        metrics = telemetry_service.get_detailed_metrics()
        if metrics["total_queries"] > 0:
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Requests", f"{metrics['total_queries']:,}")
            m2.metric("Successful Requests", f"{metrics['successful_queries']:,}")
            m3.metric("Failed Requests", f"{metrics['failed_queries']:,}")
            m4.metric("Success Rate", f"{metrics['success_rate']:.1f}%")
            
            st.markdown("<br>", unsafe_allow_html=True)
            l1, l2, l3, l4 = st.columns(4)
            l1.metric("Average Latency", f"{metrics['avg_latency']:.0f} ms")
            l2.metric("p50 Latency", f"{metrics['p50_latency']:.0f} ms")
            l3.metric("p95 Latency", f"{metrics['p95_latency']:.0f} ms")
            l4.metric("Fallback Rate", f"{metrics['fallback_rate']:.1f}%")
        else:
            st.info("Insufficient runtime data recorded yet. Submit queries via the Chat page or run the test suite to populate real runtime telemetry.")
    except Exception as e:
        st.error(f"Error fetching runtime telemetry: {e}")
        
    st.markdown("---")
    st.subheader("Pipeline Architecture")
    
    # Mermaid representation of pipeline
    st.markdown("""
    ```mermaid
    graph TD
        User((User Query)) --> Auth[Authentication & Authorization]
        Auth --> Cache{Semantic Cache}
        Cache -- Hit --> Answer
        Cache -- Miss --> Hybrid[Hybrid Retrieval Engine]
        
        Hybrid --> Vec[Vector]
        Hybrid --> Lex[Lexical]
        Hybrid --> Graph[GraphRAG]
        
        Vec --> Fuse[Candidate Fusion]
        Lex --> Fuse
        Graph --> Fuse
        
        Fuse --> Rerank[Production Reranking]
        Rerank --> Route{Cost-Aware Router}
        
        Route -- Simple --> Small[Small Model]
        Route -- Complex --> Large[Large Model]
        Route -- Fallback --> Groq[Groq Fallback]
        
        Small --> Answer
        Large --> Answer
        Groq --> Answer
    ```
    """)
    
    st.info("Navigate through the sidebar to explore individual components of the RAGX pipeline in detail.")
