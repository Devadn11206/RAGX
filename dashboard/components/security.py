import streamlit as st
import os
import json
import pandas as pd

def render_security():
    st.header("Security Center & Audit Log (Phase 4)")
    st.caption("Test metrics sourced from `reports/security/security_report.json` (Automated Security Suite)")
    
    report_path = "reports/security/security_report.json"
    if os.path.exists(report_path):
        with open(report_path, "r", encoding="utf-8") as f:
            sec_report = json.load(f)
            
        total = sec_report.get("total_tests", 0)
        passed = sec_report.get("passed", 0)
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        st.subheader("Security Posture")
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Security Pass Rate", f"{pass_rate:.1f}%")
        c2.metric("Critical Failures", sec_report.get("critical_failures", 0))
        c3.metric("Errors / Warnings", sec_report.get("errors", 0))
        c4.metric("Total Automated Tests", total)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("Zero-Trust Architecture Status")
        v1, v2, v3, v4 = st.columns(4)
        v1.metric("Cross-Tenant Leaks", sec_report.get("cross_tenant_leaks", 0))
        v2.metric("Unauthorized Chunks", sec_report.get("unauthorized_chunks", 0))
        v3.metric("Canary Leaks", sec_report.get("canary_leaks", 0))
        v4.metric("Privilege Escalations", sec_report.get("privilege_escalations", 0))
        
        if sec_report.get("critical_failures", 0) == 0:
            st.markdown("<div class='status-badge status-operational' style='font-size: 1rem; padding: 10px 16px; margin-top: 10px;'>SECURITY STATUS: PASS — Zero unauthorized data leakage detected.</div>", unsafe_allow_html=True)
        else:
            st.error("❌ SECURITY STATUS: FAIL. Critical vulnerabilities detected.")
            
        st.markdown("---")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            st.subheader("Attack Category Analysis")
            if "details" in sec_report:
                cats = {}
                for test in sec_report["details"]:
                    cat = test.get("category", "General")
                    if cat not in cats:
                        cats[cat] = {"Passed": 0, "Failed": 0}
                    if test.get("status") == "PASS":
                        cats[cat]["Passed"] += 1
                    else:
                        cats[cat]["Failed"] += 1
                
                chart_data = pd.DataFrame(cats).T if cats else pd.DataFrame()
                if not chart_data.empty:
                    st.bar_chart(chart_data)
            else:
                st.info("No detailed breakdown available.")
            
        with col2:
            st.subheader("Test Execution Detail")
            if "details" in sec_report:
                df_details = pd.DataFrame(sec_report["details"])
                selected_test = st.selectbox("Inspect Vulnerability Test:", df_details["test_id"].tolist())
                if selected_test:
                    test_info = df_details[df_details["test_id"] == selected_test].iloc[0]
                    st.markdown(f"**Test ID:** `{test_info['test_id']}`")
                    st.markdown(f"**Status:** <span class='status-badge status-operational'>{test_info['status']}</span>", unsafe_allow_html=True)
                    st.markdown(f"**Execution Duration:** {test_info.get('duration_ms', 0)} ms")
    else:
        st.info("No security test results available. Run `python -m scripts.security_test` to generate Phase 4 metrics.")
        
    st.markdown("---")
    st.subheader("Enterprise Audit Log")
    try:
        import asyncpg
        import asyncio
        from app.core.config import settings
        
        async def fetch_audits():
            conn = await asyncpg.connect(
                user=settings.POSTGRES_USER, 
                password=settings.POSTGRES_PASSWORD, 
                database=settings.POSTGRES_DB, 
                host=settings.POSTGRES_HOST, 
                port=settings.POSTGRES_PORT
            )
            rows = await conn.fetch("SELECT timestamp, user_id, tenant_id, action, status FROM audit_events ORDER BY timestamp DESC LIMIT 20")
            await conn.close()
            return [dict(r) for r in rows]
            
        audits = asyncio.run(fetch_audits())
        if audits:
            df = pd.DataFrame(audits)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No audit events found in database.")
    except Exception as e:
        st.warning(f"Could not connect to PostgreSQL Audit Store: {str(e)}")
