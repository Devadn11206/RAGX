import streamlit as st
import os

# Import UI components
from dashboard.components.style import apply_ragx_theme
from dashboard.components.auth import render_auth_sidebar
from dashboard.components.overview import render_overview
from dashboard.components.chat import render_chat
from dashboard.components.retrieval import render_retrieval
from dashboard.components.graphrag import render_graphrag
from dashboard.components.semantic_cache import render_semantic_cache
from dashboard.components.reranking import render_reranking
from dashboard.components.cost_routing import render_cost_routing
from dashboard.components.security import render_security
from dashboard.components.evaluation import render_evaluation
from dashboard.components.analytics import render_analytics
from dashboard.components.settings import render_settings

# Setup Page Configuration
st.set_page_config(
    page_title="RAGX | Enterprise Retrieval", 
    page_icon="🧠", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply global dark-first premium theme
apply_ragx_theme()

# Left Sidebar Navigation
st.sidebar.title("🧠 RAGX")
st.sidebar.caption("Enterprise Intelligence Platform")
st.sidebar.markdown("---")

# Render Auth (Sets Headers & Session)
headers, user_data = render_auth_sidebar()
st.sidebar.markdown("---")

# App Shell Navigation
nav_options = {
    "◈ Overview": render_overview,
    "✦ Chat": render_chat,
    "⌘ Retrieval Explorer": render_retrieval,
    "◎ GraphRAG": render_graphrag,
    "⚡ Cache Analytics": render_semantic_cache,
    "◉ Production Reranking": render_reranking,
    "$ Cost & Routing": render_cost_routing,
    "◌ Evaluation": render_evaluation,
    "🛡 Security Center": render_security,
    "📊 System Analytics": render_analytics,
    "⚙ Settings": render_settings
}

selected_page = st.sidebar.radio("Navigation", list(nav_options.keys()), label_visibility="collapsed")

# Execute Selected Page
page_renderer = nav_options[selected_page]
page_renderer()

# Demo Mode Trigger at bottom of sidebar
st.sidebar.markdown("---")
if st.sidebar.button("▶ Run RAGX Demo", use_container_width=True):
    st.sidebar.info("Demo Mode: Navigating to Chat with prefilled pipeline context.")
    # In a full react app this would trigger an interactive tour, here we just show the message
    st.sidebar.markdown("Go to `✦ Chat` and ask: **'What is the company leave policy?'** to see the full pipeline in action.")
