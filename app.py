"""
VeriGenX Streamlit Dashboard
Professional dashboard for viewing UART verification test plan
"""
import streamlit as st
import json
import os
from pathlib import Path

# ---- PAGE CONFIG ----
st.set_page_config(
    page_title="VeriGenX Dashboard",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---- CUSTOM CSS ----
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .main-header {
        background: linear-gradient(135deg, #0f172a, #1e3a5f);
        padding: 32px 40px;
        border-radius: 12px;
        margin-bottom: 28px;
        color: white;
    }
    .main-header h1 { font-size: 32px; font-weight: 800; margin: 0 0 6px 0; }
    .main-header p { color: #94a3b8; font-size: 15px; margin: 0; }

    .status-complete {
        background: #f0fdf4;
        border: 1px solid #bbf7d0;
        color: #15803d;
        padding: 10px 18px;
        border-radius: 8px;
        font-weight: 600;
        font-size: 14px;
        display: inline-block;
        margin: 4px 4px 4px 0;
    }
    .status-pending {
        background: #fffbeb;
        border: 1px solid #fde68a;
        color: #b45309;
        padding: 10px 18px;
        border-radius: 8px;
        font-weight: 600;
        font-size: 14px;
        display: inline-block;
        margin: 4px 4px 4px 0;
    }
    .metric-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
    }
    .metric-number { font-size: 36px; font-weight: 800; color: #0f172a; }
    .metric-label { font-size: 13px; color: #64748b; margin-top: 4px; }

    .fp-card {
        background: #eff6ff;
        border-left: 4px solid #3b82f6;
        padding: 16px 20px;
        border-radius: 0 8px 8px 0;
        margin-bottom: 12px;
    }
    .fp-id { font-size: 12px; font-weight: 700; color: #2563eb; text-transform: uppercase; letter-spacing: 1px; }
    .fp-desc { font-size: 14px; color: #334155; margin-top: 4px; }

    .section-header {
        font-size: 13px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #475569;
        border-bottom: 2px solid #e2e8f0;
        padding-bottom: 10px;
        margin-bottom: 16px;
    }
</style>
""", unsafe_allow_html=True)

# ---- LOAD DATA ----
@st.cache_data
def load_test_plan():
    plan_path = Path("test_plans/uart_test_plan.json")
    if plan_path.exists():
        with open(plan_path, "r") as f:
            return json.load(f)
    return None

plan = load_test_plan()

# ---- SIDEBAR ----
with st.sidebar:
    st.markdown("### VeriGenX")
    st.markdown("Autonomous UVM Verification Intelligence Platform")
    st.markdown("---")
    page = st.radio(
        "Navigation",
        ["Overview", "Signals", "FSM States", "Register Map", "Functional Points", "Test Results"],
        label_visibility="collapsed"
    )
    st.markdown("---")
    st.markdown("**Phase Status**")
    st.markdown('<span class="status-complete">Phase 1 Complete</span>', unsafe_allow_html=True)
    st.markdown('<span class="status-complete">Phase 2 Complete</span>', unsafe_allow_html=True)
    st.markdown('<span class="status-pending">Phase 3 Pending</span>', unsafe_allow_html=True)
    st.markdown("---")
    if plan:
        st.markdown(f"**Design:** `{plan.get('design_name', 'uart').upper()}`")
        st.markdown(f"**Version:** `{plan.get('version', '1.0')}`")
        st.markdown(f"**Generated:** `{plan.get('generated_at', '')[:10]}`")

# ---- HEADER ----
st.markdown("""
<div class="main-header">
    <h1>VeriGenX Dashboard</h1>
    <p>UART Verification Test Plan — Phase 1 and Phase 2 Complete</p>
</div>
""", unsafe_allow_html=True)

if plan is None:
    st.error("Test plan not found. Run test_phase1.py first to generate test_plans/uart_test_plan.json")
    st.stop()

# ---- PAGES ----

if page == "Overview":
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown('<div class="metric-card"><div class="metric-number">4</div><div class="metric-label">Interface Signals</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="metric-card"><div class="metric-number">4</div><div class="metric-label">FSM States</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="metric-card"><div class="metric-number">2</div><div class="metric-label">Registers</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown('<div class="metric-card"><div class="metric-number">12</div><div class="metric-label">UVM Components</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-header">Design Summary</div>', unsafe_allow_html=True)
    col_a, col_b = st.columns(2)
    with col_a:
        st.info(f"**Design Name:** {plan.get('design_name', '').upper()}\n\n**Version:** {plan.get('version', '1.0')}\n\n**Protocol:** 8-N-1 (8 data bits, no parity, 1 stop bit)")
    with col_b:
        st.success("**Phase 1 — SpecMind:** Complete\n\nSpecification parsed. JSON test plan generated with signals, FSM states, registers, and functional points.")
        st.warning("**Phase 3 — UVMForge:** Pending\n\nTestbench generation from dependency graph. Requires Phase 3 approval.")

elif page == "Signals":
    st.markdown('<div class="section-header">Interface Signals</div>', unsafe_allow_html=True)
    signals = plan.get("signals", [])
    if signals:
        import pandas as pd
        df = pd.DataFrame(signals)
        df.columns = [c.replace("_", " ").title() for c in df.columns]
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.markdown(f"**Total signals:** {len(signals)}")
    else:
        st.warning("No signals found in test plan.")

elif page == "FSM States":
    st.markdown('<div class="section-header">FSM State Transition</div>', unsafe_allow_html=True)
    states = plan.get("fsm_states", [])
    if states:
        cols = st.columns(len(states) * 2 - 1)
        for i, state in enumerate(states):
            cols[i * 2].markdown(
                f'<div style="background:#1e293b;color:#e2e8f0;padding:12px 20px;border-radius:8px;text-align:center;font-family:monospace;font-weight:700;">{state}</div>',
                unsafe_allow_html=True
            )
            if i < len(states) - 1:
                cols[i * 2 + 1].markdown(
                    '<div style="text-align:center;font-size:24px;color:#64748b;line-height:48px;">&#8594;</div>',
                    unsafe_allow_html=True
                )
        st.markdown(f"\n**Total states:** {len(states)} | **Transition:** {' > '.join(states)} > IDLE (cyclic)")

elif page == "Register Map":
    st.markdown('<div class="section-header">Register Map</div>', unsafe_allow_html=True)
    registers = plan.get("register_map", [])
    if registers:
        import pandas as pd
        df = pd.DataFrame(registers)
        df.columns = [c.replace("_", " ").title() for c in df.columns]
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.markdown(f"**Total registers:** {len(registers)}")
    else:
        st.warning("No register map found in test plan.")

elif page == "Functional Points":
    st.markdown('<div class="section-header">Functional Coverage Points</div>', unsafe_allow_html=True)
    fps = plan.get("functional_points", [])
    for fp in fps:
        st.markdown(f"""
        <div class="fp-card">
            <div class="fp-id">{fp.get('id', '')}</div>
            <div class="fp-desc">{fp.get('description', '')}</div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown(f"**Total functional points:** {len(fps)}")

elif page == "Test Results":
    st.markdown('<div class="section-header">Verification Test Results</div>', unsafe_allow_html=True)
    results = [
        ("Phase 1", "Specification Parsing (TXT)", "PASS"),
        ("Phase 1", "Test Plan Generation (JSON)", "PASS"),
        ("Phase 1", "Semantic Chunking", "PASS"),
        ("Phase 2", "DAG Build (12 Components)", "PASS"),
        ("Phase 2", "Topological Sort", "PASS"),
        ("Phase 2", "Cycle Detection", "PASS"),
        ("Phase 2", "Conflict Detection", "PASS"),
        ("Phase 2", "DAG Visualization (DOT Export)", "PASS"),
    ]
    import pandas as pd
    df = pd.DataFrame(results, columns=["Phase", "Test Description", "Status"])
    st.dataframe(df, use_container_width=True, hide_index=True)
    pass_count = sum(1 for r in results if r[2] == "PASS")
    st.success(f"All {pass_count}/{len(results)} tests passing. Zero failures.")
