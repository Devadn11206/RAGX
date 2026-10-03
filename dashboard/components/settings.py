import streamlit as st
import os

def render_settings():
    st.header("Platform Configuration")
    st.caption("Settings reflect the current environment and configuration files (`app/core/config.py`).")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Model Providers")
        
        st.markdown("**Primary LLM (Gemini)**")
        st.markdown("<span class='status-badge status-operational'>Configured via Environment</span>", unsafe_allow_html=True)
        st.text_input("Gemini API Key", value="****************************", disabled=True)
        
        st.markdown("**Fallback LLM (Groq)**")
        st.markdown("<span class='status-badge status-operational'>Configured via Environment</span>", unsafe_allow_html=True)
        st.text_input("Groq API Key", value="****************************", disabled=True)
        
        st.markdown("**Embedding Provider**")
        st.markdown("`sentence-transformers/all-MiniLM-L6-v2` (Local)")
        
        st.markdown("**Reranking Engine**")
        st.markdown("`cross-encoder/ms-marco-MiniLM-L-6-v2` (Local)")
        
    with col2:
        st.subheader("Retrieval & Reranking Limits")
        
        st.number_input("Vector Search Top-K", value=15, disabled=True)
        st.number_input("Lexical Search Top-K", value=15, disabled=True)
        st.number_input("Reranker Candidate K", value=30, disabled=True)
        st.number_input("Final Top-K Context", value=8, disabled=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("Semantic Cache")
        st.slider("Similarity Threshold", min_value=0.0, max_value=1.0, value=0.92, disabled=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("Cost-Aware Router")
        st.slider("Complexity Escalation Threshold", min_value=0.0, max_value=1.0, value=0.75, disabled=True)

    st.markdown("---")
    st.info("These settings are read-only in the UI. Modify `.env` or `app/core/config.py` to enact permanent infrastructure changes.")
