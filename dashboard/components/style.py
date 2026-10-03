import streamlit as st

def apply_ragx_theme():
    st.markdown("""
    <style>
        /* RAGX Global Theme - Enterprise Dark Mode */
        
        /* Base Colors */
        :root {
            --ragx-bg: #0E1117;
            --ragx-card-bg: #161B22;
            --ragx-border: #30363D;
            --ragx-text: #E6EDF3;
            --ragx-text-muted: #8B949E;
            --ragx-accent: #2F81F7;
            --ragx-success: #238636;
            --ragx-warning: #D29922;
            --ragx-danger: #F85149;
        }

        /* typography */
        html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        }

        /* App Background */
        .stApp {
            background-color: var(--ragx-bg);
            color: var(--ragx-text);
        }

        /* Sidebar */
        [data-testid="stSidebar"] {
            background-color: #0d1117 !important;
            border-right: 1px solid var(--ragx-border);
        }
        
        /* Cards & Containers */
        div[data-testid="stMetricValue"] {
            font-size: 1.8rem !important;
            font-weight: 600 !important;
            color: var(--ragx-text) !important;
        }
        div[data-testid="stMetricLabel"] {
            font-size: 0.9rem !important;
            color: var(--ragx-text-muted) !important;
            font-weight: 500 !important;
        }
        
        /* Buttons */
        .stButton>button {
            border-radius: 6px;
            border: 1px solid var(--ragx-border);
            background-color: var(--ragx-card-bg);
            color: var(--ragx-text);
            font-weight: 500;
            transition: all 0.2s ease-in-out;
        }
        .stButton>button:hover {
            border-color: var(--ragx-accent);
            color: var(--ragx-accent);
        }
        .stButton>button[kind="primary"] {
            background-color: var(--ragx-success);
            border-color: var(--ragx-success);
            color: white;
        }
        
        /* Expander */
        .streamlit-expanderHeader {
            background-color: var(--ragx-card-bg) !important;
            border-radius: 6px;
            border: 1px solid var(--ragx-border);
        }
        
        /* Dataframes & Tables */
        [data-testid="stDataFrame"] {
            border: 1px solid var(--ragx-border);
            border-radius: 6px;
        }
        
        /* Source Cards Custom CSS */
        .source-card {
            background-color: var(--ragx-card-bg);
            border: 1px solid var(--ragx-border);
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 12px;
            transition: border-color 0.2s ease;
        }
        .source-card:hover {
            border-color: var(--ragx-accent);
        }
        .source-card h4 {
            margin-top: 0;
            margin-bottom: 8px;
            font-size: 1.1rem;
            color: var(--ragx-text);
        }
        .source-card-meta {
            font-size: 0.85rem;
            color: var(--ragx-text-muted);
            margin-bottom: 12px;
        }
        .source-card-score {
            display: inline-block;
            background-color: rgba(47, 129, 247, 0.15);
            color: var(--ragx-accent);
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
        }
        
        /* Status Badges */
        .status-badge {
            display: inline-flex;
            align-items: center;
            padding: 4px 10px;
            border-radius: 16px;
            font-size: 0.8rem;
            font-weight: 600;
        }
        .status-operational {
            background-color: rgba(35, 134, 54, 0.15);
            color: var(--ragx-success);
            border: 1px solid rgba(35, 134, 54, 0.3);
        }
        .status-degraded {
            background-color: rgba(210, 153, 34, 0.15);
            color: var(--ragx-warning);
            border: 1px solid rgba(210, 153, 34, 0.3);
        }
        .status-badge::before {
            content: '●';
            margin-right: 6px;
            font-size: 0.9em;
        }
        
        /* Chat Overrides */
        [data-testid="stChatMessage"] {
            background-color: transparent !important;
            border: none !important;
        }
        [data-testid="stChatMessage"][data-baseweb="user"] {
            background-color: var(--ragx-card-bg) !important;
            border: 1px solid var(--ragx-border) !important;
            border-radius: 8px;
        }
        
    </style>
    """, unsafe_allow_html=True)
