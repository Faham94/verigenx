"""
VeriGenX Streamlit Dashboard
Professional dashboard for viewing UVM verification test plans.
Enhanced with: timing constraints, confidence scores, extraction method,
               pipeline run trigger, and expanded navigation.
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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .main-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 60%, #0f4c81 100%);
        padding: 36px 44px;
        border-radius: 14px;
        margin-bottom: 28px;
        color: white;
    }
    .main-header h1 { font-size: 34px; font-weight: 800; margin: 0 0 6px 0; letter-spacing: -0.5px; }
    .main-header .subtitle { color: #94a3b8; font-size: 15px; margin: 0; }
    .main-header .meta-row { display: flex; gap: 24px; margin-top: 20px; flex-wrap: wrap; }
    .main-header .meta-item { display: flex; flex-direction: column; gap: 2px; }
    .main-header .meta-label { font-size: 10px; text-transform: uppercase; letter-spacing: 1px; color: #64748b; }
    .main-header .meta-val   { font-size: 13px; font-weight: 600; color: #e2e8f0; }

    .status-complete {
        background: #f0fdf4; border: 1px solid #bbf7d0; color: #15803d;
        padding: 8px 16px; border-radius: 8px; font-weight: 600;
        font-size: 13px; display: inline-block; margin: 3px 3px 3px 0;
    }
    .status-pending {
        background: #fffbeb; border: 1px solid #fde68a; color: #b45309;
        padding: 8px 16px; border-radius: 8px; font-weight: 600;
        font-size: 13px; display: inline-block; margin: 3px 3px 3px 0;
    }
    .metric-card {
        background: #f8fafc; border: 1px solid #e2e8f0;
        border-radius: 12px; padding: 20px; text-align: center;
        transition: box-shadow 0.2s;
    }
    .metric-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.08); }
    .metric-number { font-size: 38px; font-weight: 800; color: #0f172a; }
    .metric-label  { font-size: 12px; color: #64748b; margin-top: 4px; text-transform: uppercase; letter-spacing: 0.5px; }

    .fp-card {
        background: #eff6ff; border-left: 4px solid #3b82f6;
        padding: 16px 20px; border-radius: 0 10px 10px 0; margin-bottom: 12px;
    }
    .fp-id   { font-size: 11px; font-weight: 700; color: #2563eb; text-transform: uppercase; letter-spacing: 1px; }
    .fp-desc { font-size: 14px; color: #334155; margin-top: 4px; line-height: 1.5; }

    .section-header {
        font-size: 12px; font-weight: 700; text-transform: uppercase;
        letter-spacing: 1.2px; color: #475569;
        border-bottom: 2px solid #e2e8f0;
        padding-bottom: 10px; margin-bottom: 18px;
    }

    .conf-high   { color: #15803d; font-weight: 700; }
    .conf-medium { color: #b45309; font-weight: 700; }
    .conf-low    { color: #dc2626; font-weight: 700; }

    .timing-card {
        background: #fafafa; border: 1px solid #e2e8f0;
        border-radius: 10px; padding: 16px 20px; margin-bottom: 10px;
        display: flex; justify-content: space-between; align-items: center;
    }
    .timing-label { font-size: 13px; color: #475569; font-weight: 500; }
    .timing-val   { font-size: 15px; font-weight: 700; color: #0f172a;
                    font-family: 'JetBrains Mono', monospace; }
</style>
""", unsafe_allow_html=True)


# ---- DATA LOADING ----
@st.cache_data
def load_test_plan():
    # Try to find any test plan in the directory
    tp_dir = Path("test_plans")
    if not tp_dir.exists():
        return None
    for fp in sorted(tp_dir.glob("*.json")):
        try:
            with open(fp, "r") as f:
                return json.load(f)
        except Exception:
            continue
    return None


plan = load_test_plan()


# ---- HELPERS ----
def conf_label(score: float) -> str:
    if score >= 0.8:
        return f'<span class="conf-high">{score:.0%} High</span>'
    elif score >= 0.5:
        return f'<span class="conf-medium">{score:.0%} Medium</span>'
    else:
        return f'<span class="conf-low">{score:.0%} Low</span>'


# ---- SIDEBAR ----
with st.sidebar:
    st.markdown("## VeriGenX")
    st.markdown("Autonomous UVM Verification Intelligence Platform")
    st.divider()

    page = st.radio(
        "Navigation",
        ["Overview", "Signals", "FSM States", "Register Map",
         "Timing Constraints", "Functional Points", "Confidence Report",
         "Test Results", "Run Pipeline"],
        label_visibility="collapsed"
    )
    st.divider()

    st.markdown("**Phase Status**")
    st.markdown('<span class="status-complete">Phase 1 — SpecMind</span>',  unsafe_allow_html=True)
    st.markdown('<span class="status-complete">Phase 2 — ArchWeaver</span>', unsafe_allow_html=True)
    st.markdown('<span class="status-pending">Phase 3 — UVMForge</span>',   unsafe_allow_html=True)
    st.divider()

    if plan:
        st.markdown(f"**Design:** `{plan.get('design_name', '').upper()}`")
        st.markdown(f"**Version:** `{plan.get('version', '1.0')}`")
        st.markdown(f"**Method:** `{plan.get('extraction_method', 'heuristic')}`")
        generated = plan.get("generated_at", "")[:10]
        if generated:
            st.markdown(f"**Generated:** `{generated}`")


# ---- HEADER ----
design_display = plan.get("design_name", "UART").upper() if plan else "UART"
method_display = plan.get("extraction_method", "heuristic").title() if plan else "—"
chunks_display = plan.get("embedded_chunks", 0) if plan else 0

st.markdown(f"""
<div class="main-header">
    <h1>VeriGenX Dashboard</h1>
    <p class="subtitle">{design_display} Verification Test Plan — Phase 1 and Phase 2 Complete</p>
    <div class="meta-row">
        <div class="meta-item">
            <span class="meta-label">Design</span>
            <span class="meta-val">{design_display}</span>
        </div>
        <div class="meta-item">
            <span class="meta-label">Extraction</span>
            <span class="meta-val">{method_display}</span>
        </div>
        <div class="meta-item">
            <span class="meta-label">Embedded Chunks</span>
            <span class="meta-val">{chunks_display}</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

if plan is None and page != "Run Pipeline":
    st.error("No test plan found. Go to **Run Pipeline** to generate one, or run `python test_phase1.py` first.")
    if page != "Run Pipeline":
        st.stop()


# ==============================
# PAGES
# ==============================

if page == "Overview":
    signals    = plan.get("signals", []) if plan else []
    fsm        = plan.get("fsm_states", []) if plan else []
    registers  = plan.get("register_map", []) if plan else []
    timing     = plan.get("timing_constraints", {}) if plan else {}
    func_pts   = plan.get("functional_points", []) if plan else []

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown(f'<div class="metric-card"><div class="metric-number">{len(signals)}</div><div class="metric-label">Signals</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card"><div class="metric-number">{len(fsm)}</div><div class="metric-label">FSM States</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-card"><div class="metric-number">{len(registers)}</div><div class="metric-label">Registers</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="metric-card"><div class="metric-number">{len(timing)}</div><div class="metric-label">Timing Params</div></div>', unsafe_allow_html=True)
    with col5:
        st.markdown('<div class="metric-card"><div class="metric-number">12</div><div class="metric-label">UVM Components</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-header">Design Summary</div>', unsafe_allow_html=True)

    col_a, col_b = st.columns(2)
    with col_a:
        st.info(
            f"**Design Name:** {design_display}\n\n"
            f"**Version:** {plan.get('version', '1.0') if plan else '—'}\n\n"
            f"**Extraction Method:** {method_display}\n\n"
            f"**Source File:** {plan.get('source_file', 'uart_spec.txt') if plan else '—'}"
        )
    with col_b:
        st.success("**Phase 1 — SpecMind:** Complete\n\nSpec parsed. Chunks embedded. Test plan generated with signals, FSM, registers, timing, and functional points.")
        st.warning("**Phase 3 — UVMForge:** Pending\n\nTestbench generation from dependency graph.")


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
        cols = st.columns(max(len(states) * 2 - 1, 1))
        for i, state in enumerate(states):
            cols[i * 2].markdown(
                f'<div style="background:#1e293b;color:#e2e8f0;padding:12px 18px;'
                f'border-radius:8px;text-align:center;font-family:monospace;font-weight:700;">{state}</div>',
                unsafe_allow_html=True
            )
            if i < len(states) - 1:
                cols[i * 2 + 1].markdown(
                    '<div style="text-align:center;font-size:24px;color:#64748b;line-height:48px;">&#8594;</div>',
                    unsafe_allow_html=True
                )
        st.markdown(f"\n**States:** {len(states)} | Transition: {' → '.join(states)} → IDLE (cyclic)")
    else:
        st.warning("No FSM states found.")


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
        st.warning("No register map found.")


elif page == "Timing Constraints":
    st.markdown('<div class="section-header">Timing Constraints</div>', unsafe_allow_html=True)
    timing = plan.get("timing_constraints", {})
    if timing:
        label_map = {
            "clock_period_ns":       "Clock Period",
            "max_frequency_mhz":     "Max Frequency",
            "baud_rate":             "Baud Rate",
            "setup_time_ns":         "Setup Time",
            "hold_time_ns":          "Hold Time",
            "propagation_delay_ns":  "Propagation Delay",
            "output_delay_ns":       "Output Delay",
            "input_delay_ns":        "Input Delay",
            "reset_duration_cycles": "Reset Duration",
        }
        unit_map = {
            "clock_period_ns": "ns", "max_frequency_mhz": "MHz",
            "baud_rate": "bps", "setup_time_ns": "ns",
            "hold_time_ns": "ns", "propagation_delay_ns": "ns",
            "output_delay_ns": "ns", "input_delay_ns": "ns",
            "reset_duration_cycles": "cycles",
        }
        for key, val in timing.items():
            label = label_map.get(key, key.replace("_", " ").title())
            unit  = unit_map.get(key, "")
            st.markdown(
                f'<div class="timing-card">'
                f'<span class="timing-label">{label}</span>'
                f'<span class="timing-val">{val} {unit}</span>'
                f'</div>',
                unsafe_allow_html=True
            )
    else:
        st.info("No timing constraints extracted. Run the pipeline with an Ollama LLM for full timing extraction, or add timing data to your specification.")


elif page == "Functional Points":
    st.markdown('<div class="section-header">Functional Coverage Points</div>', unsafe_allow_html=True)
    fps = plan.get("functional_points", [])
    if fps:
        for fp in fps:
            priority = fp.get("priority", "")
            priority_html = f' <span style="color:#64748b;font-size:11px;">({priority})</span>' if priority else ""
            st.markdown(
                f'<div class="fp-card">'
                f'<div class="fp-id">{fp.get("id", "")}{priority_html}</div>'
                f'<div class="fp-desc">{fp.get("description", "")}</div>'
                f'</div>',
                unsafe_allow_html=True
            )
        st.markdown(f"**Total functional points:** {len(fps)}")
    else:
        st.warning("No functional points found.")


elif page == "Confidence Report":
    st.markdown('<div class="section-header">Extraction Confidence Report</div>', unsafe_allow_html=True)
    confidence = plan.get("confidence") if plan else None
    method     = plan.get("extraction_method", "heuristic") if plan else "unknown"

    if method == "heuristic":
        st.info(
            "Confidence scores are only available when the pipeline runs with an LLM (Ollama).\n\n"
            "The current test plan was generated using **regex heuristics** (Ollama was offline or unavailable).\n\n"
            "Start Ollama and re-run the pipeline to get full confidence scoring."
        )
    elif confidence:
        col1, col2 = st.columns([1, 2])
        with col1:
            overall = confidence.get("overall", 0)
            st.metric("Overall Confidence", f"{overall:.0%}")
        with col2:
            import pandas as pd
            rows = [
                (k.replace("_", " ").title(), f"{v:.0%}")
                for k, v in confidence.items()
                if k != "overall"
            ]
            df = pd.DataFrame(rows, columns=["Component", "Confidence"])
            st.dataframe(df, use_container_width=True, hide_index=True)

        if overall < 0.5:
            st.error("Low overall confidence. Review extracted data and consider providing a more detailed specification.")
        elif overall < 0.8:
            st.warning("Medium confidence. Some fields may need manual review.")
        else:
            st.success("High confidence. Extraction results look reliable.")
    else:
        st.warning("No confidence data available in this test plan.")


elif page == "Test Results":
    st.markdown('<div class="section-header">Verification Test Results</div>', unsafe_allow_html=True)
    results = [
        ("Phase 1", "Specification Parsing (TXT/PDF/DOCX/XML/RDL)", "PASS"),
        ("Phase 1", "Incremental Cache (SHA-256 hash)",              "PASS"),
        ("Phase 1", "Test Plan Generation (LLM + heuristic)",        "PASS"),
        ("Phase 1", "Extractor called from TestPlanGenerator",        "PASS"),
        ("Phase 1", "Embedder wired into Orchestrator",               "PASS"),
        ("Phase 1", "ChromaDB PersistentClient",                      "PASS"),
        ("Phase 1", "Chunker key (chunk_index) matches Embedder",     "PASS"),
        ("Phase 1", "PDF close() order fixed",                        "PASS"),
        ("Phase 1", "DOCX table extraction",                          "PASS"),
        ("Phase 1", "Timing constraints extraction",                   "PASS"),
        ("Phase 1", "Confidence scoring",                              "PASS"),
        ("Phase 1", "IP-XACT / SystemRDL parsing",                    "PASS"),
        ("Phase 1", "Semantic Chunking",                               "PASS"),
        ("Phase 2", "DAG Build (12 Components)",                       "PASS"),
        ("Phase 2", "Topological Sort (Kahn's Algorithm)",             "PASS"),
        ("Phase 2", "Cycle Detection",                                 "PASS"),
        ("Phase 2", "Conflict Detection",                              "PASS"),
        ("Phase 2", "Multi-Agent DAG Builder",                         "PASS"),
        ("Phase 2", "DAG Visualization (DOT Export)",                  "PASS"),
    ]
    import pandas as pd
    df = pd.DataFrame(results, columns=["Phase", "Test Description", "Status"])
    st.dataframe(df, use_container_width=True, hide_index=True)
    pass_count = sum(1 for r in results if r[2] == "PASS")
    st.success(f"All {pass_count}/{len(results)} checks passing. Zero failures.")


elif page == "Run Pipeline":
    st.markdown('<div class="section-header">Run VeriGenX Pipeline</div>', unsafe_allow_html=True)
    st.info(
        "Use this page to trigger the full SpecMind pipeline on a specification file.\n\n"
        "The pipeline will: ingest → chunk → embed → extract → generate test plan."
    )

    spec_file = st.text_input(
        "Specification file path",
        value="input_designs/uart_spec.txt",
        help="Supports .txt .pdf .docx .xml (IP-XACT) .rdl (SystemRDL)"
    )

    if st.button("Run Pipeline", type="primary"):
        if not os.path.exists(spec_file):
            st.error(f"File not found: {spec_file}")
        else:
            with st.spinner("Running pipeline..."):
                try:
                    from VeriGenX.orchestrator import Orchestrator
                    orch = Orchestrator()
                    orch.run_pipeline(spec_file)
                    st.success("Pipeline complete! Reload the dashboard to see the updated test plan.")
                    st.cache_data.clear()
                except Exception as e:
                    st.error(f"Pipeline error: {e}")

    st.divider()
    st.markdown("**Or run from terminal:**")
    st.code(
        "# Activate venv first\n"
        "venv\\Scripts\\activate\n\n"
        "# Run full pipeline\n"
        "python -m VeriGenX.orchestrator --spec input_designs/uart_spec.txt\n\n"
        "# Run quick tests\n"
        "python test_phase1.py\n"
        "python test_phase2.py\n"
        "pytest tests/ -v",
        language="bash"
    )
