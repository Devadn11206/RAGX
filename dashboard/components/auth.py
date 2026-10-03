import streamlit as st
import jwt
from datetime import datetime, timedelta, timezone

JWT_SECRET_KEY = "super_secret_phase_3_key_change_in_prod"

users = {
    "Alice (ACME, Employee)": {"sub": "alice", "tenant_id": "tenant_acme", "roles": ["employee"]},
    "Bob (ACME, HR)": {"sub": "bob", "tenant_id": "tenant_acme", "roles": ["hr"]},
    "Charlie (Globex, Employee)": {"sub": "charlie", "tenant_id": "tenant_globex", "roles": ["employee"]},
    "Diana (Globex, Admin)": {"sub": "diana", "tenant_id": "tenant_globex", "roles": ["admin"]},
    "Eve (Initech, Manager)": {"sub": "eve", "tenant_id": "tenant_initech", "roles": ["manager"]}
}

def render_auth_sidebar():
    st.sidebar.markdown("### 🔐 Identity Simulation")
    selected_user_key = st.sidebar.selectbox("Active User Profile", list(users.keys()))
    user_data = users[selected_user_key]
    
    expire = datetime.now(timezone.utc) + timedelta(hours=1)
    token_payload = user_data.copy()
    token_payload.update({"exp": expire})
    token = jwt.encode(token_payload, JWT_SECRET_KEY, algorithm="HS256")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Store in session state for global access
    st.session_state["api_headers"] = headers
    st.session_state["current_user"] = user_data
    
    with st.sidebar.expander("Session Details", expanded=False):
        st.json(user_data)
        
    return headers, user_data
