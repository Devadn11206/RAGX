import streamlit as st
import requests
import os
import json

API_URL = os.getenv("API_URL", "http://localhost:8000")

def render_pipeline_trace(data: dict):
    """Renders the execution trace of the query with all Phase 11 required fields."""
    ret = data.get("retrieval", {})
    rerank = data.get("reranking", {})
    
    st.markdown("##### 🔍 Execution Trace & Telemetry")
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Request ID", f"{ret.get('request_id', 'N/A')[:8]}..." if ret.get('request_id') else "N/A", help=ret.get('request_id'))
    c2.metric("Total Latency", f"{ret.get('latency_ms', 0)} ms")
    c3.metric("Estimated Cost", f"${ret.get('estimated_cost', 0.0):.5f}")
    c4.metric("Provider", f"{ret.get('provider', 'N/A').title()}" if ret.get('provider') else "N/A")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Cache and Security
    cache_type = ret.get("cache_type", "MISS")
    if "HIT" in cache_type:
        st.markdown(f"**Semantic Cache:** <span class='status-badge status-operational'>HIT ({cache_type})</span>", unsafe_allow_html=True)
    elif "SECURITY" in cache_type:
        st.markdown(f"**Semantic Cache:** <span class='status-badge status-degraded'>REJECTED (Personalized / Security Scope)</span>", unsafe_allow_html=True)
    else:
        st.markdown(f"**Semantic Cache:** <span class='status-badge' style='background:rgba(255,255,255,0.1);color:#94a3b8;'>MISS</span>", unsafe_allow_html=True)
        
    # Retrieval Methods
    methods = []
    if ret.get("vector_used"): methods.append("Vector (Dense)")
    if ret.get("lexical_used"): methods.append("Lexical (BM25)")
    if ret.get("graph_used"): methods.append("GraphRAG (Multi-Hop)")
    st.markdown(f"**Retrieval Strategies Fused:** `{' + '.join(methods) if methods else 'Hybrid/Direct'}`")
    
    # Reranking Info
    if rerank and rerank.get("enabled"):
        if rerank.get("skipped"):
            st.markdown(f"**Reranking Engine:** Adaptive Skip Applied ({rerank.get('model')})")
        else:
            st.markdown(f"**Reranking Engine:** <span class='status-badge status-operational'>Applied</span> `{rerank.get('model')}` (Candidates: {rerank.get('candidate_count')} → Final: {rerank.get('final_count')} in {rerank.get('latency_ms')} ms)", unsafe_allow_html=True)
            
    # Model & Routing
    model_name = ret.get("model", "Default")
    router_tier = ret.get("router_tier", "Standard")
    st.markdown(f"**Model Routing Tier:** `{router_tier}` → Model: `{model_name}`")
    
    if ret.get("escalated"):
        st.warning("⚠️ Query complexity triggered escalation from Small to Large model.")
        
    if ret.get("fallback_used"):
        st.warning(f"⚠️ Primary provider failover triggered! Active Provider: Groq. (Reason: {ret.get('fallback_reason', 'Timeout/503')})")

def render_chat():
    st.markdown("## RAGX Assistant")
    st.caption("Ask questions about your knowledge base securely with end-to-end multi-tenant isolation.")
    
    # Session state for chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
        
    headers = st.session_state.get("api_headers", {})
    current_user = st.session_state.get("current_user", {})
    
    st.caption(f"Active Tenant: `{current_user.get('tenant_id', 'unknown')}` | User: `{current_user.get('sub', 'unknown')}` | Roles: `{', '.join(current_user.get('roles', []))}`")
    
    # Document indexing utility inside chat
    with st.expander("📄 Manage Knowledge Base", expanded=False):
        uploaded_file = st.file_uploader("Upload Document to Tenant", type=["pdf", "txt", "md"])
        if uploaded_file is not None and st.button("Index Document"):
            files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
            with st.spinner("Indexing document (Embedding + Graph Extractor + FTS)..."):
                try:
                    res = requests.post(f"{API_URL}/api/v1/documents/upload", files=files, headers=headers)
                    if res.status_code == 200:
                        st.success(f"Indexed successfully! {res.json().get('chunks_created', 0)} chunks created.")
                    elif res.status_code == 409:
                        st.warning("Document already indexed in this tenant.")
                    else:
                        st.error(f"Upload failed: HTTP {res.status_code} - {res.text}")
                except Exception as e:
                    st.error(f"Failed to connect to backend: {e}")
                    
        if st.button("Refresh Tenant Documents"):
            try:
                res_docs = requests.get(f"{API_URL}/api/v1/documents", headers=headers)
                if res_docs.status_code == 200:
                    docs = res_docs.json()
                    if not docs:
                        st.info("No documents found in your tenant.")
                    for d in docs:
                        c1, c2 = st.columns([4, 1])
                        c1.markdown(f"**{d['filename']}** ({d['file_type']}) - {d['chunk_count']} chunks | Status: `{d.get('status', 'indexed')}`")
                        if c2.button("Delete", key=f"del_{d['document_id']}"):
                            requests.delete(f"{API_URL}/api/v1/documents/{d['document_id']}", headers=headers)
                            st.rerun()
            except Exception as e:
                st.error(f"Could not fetch documents: {e}")

    st.markdown("---")

    # Display chat messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if "sources" in msg and msg["sources"]:
                st.markdown("#### Sources & Citations")
                for src in msg["sources"]:
                    st.markdown(f"<div class='source-card'><h4>📄 {src['filename']}</h4><div class='source-card-meta'>Doc ID: {src.get('document_id', 'N/A')} | Method: {src.get('retrieval_method', 'vector')}</div><div class='source-card-score'>Relevance Score: {src.get('score', 0):.4f}</div></div>", unsafe_allow_html=True)
            if "data" in msg and msg["data"]:
                with st.expander("Pipeline Trace & Telemetry", expanded=False):
                    render_pipeline_trace(msg["data"])

    # Chat input
    if prompt := st.chat_input("Ask RAGX anything..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.markdown("*(Processing through Semantic Cache → Hybrid Retrieval → Reranker → Cost Router → LLM...)*")
            
            try:
                res = requests.post(f"{API_URL}/api/v1/query", json={"query": prompt, "retrieval_mode": "hybrid"}, headers=headers, timeout=60)
                if res.status_code == 200:
                    data = res.json()
                    answer = data.get("answer", "No answer returned.")
                    sources = data.get("sources", [])
                    
                    message_placeholder.markdown(answer)
                    
                    if sources:
                        st.markdown("#### Sources & Citations")
                        for src in sources:
                            st.markdown(f"<div class='source-card'><h4>📄 {src['filename']}</h4><div class='source-card-meta'>Doc ID: {src.get('document_id', 'N/A')} | Method: {src.get('retrieval_method', 'vector')}</div><div class='source-card-score'>Relevance Score: {src.get('score', 0):.4f}</div></div>", unsafe_allow_html=True)
                            
                    with st.expander("Pipeline Trace & Telemetry", expanded=True):
                        render_pipeline_trace(data)
                        
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": answer,
                        "sources": sources,
                        "data": data
                    })
                else:
                    message_placeholder.error(f"Query execution failed. HTTP {res.status_code}: {res.text}")
            except Exception as e:
                message_placeholder.error(f"Could not connect to RAGX backend: {e}")
