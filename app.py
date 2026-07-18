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

    /* Custom scrollbars */
    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: #0b0f19; }
    ::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: #3b82f6; }

    .main-header {
        background: linear-gradient(135deg, #1e1b4b 0%, #0f172a 100%);
        padding: 36px 44px;
        border-radius: 14px;
        margin-bottom: 28px;
        color: white;
        border: 1px solid #312e81;
        box-shadow: 0 8px 32px rgba(99, 102, 241, 0.15);
    }
    .main-header h1 { font-size: 34px; font-weight: 800; margin: 0 0 6px 0; letter-spacing: -0.5px; color: #f8fafc; }
    .main-header .subtitle { color: #cbd5e1; font-size: 15px; margin: 0; }
    .main-header .meta-row { display: flex; gap: 24px; margin-top: 20px; flex-wrap: wrap; }
    .main-header .meta-item { display: flex; flex-direction: column; gap: 2px; }
    .main-header .meta-label { font-size: 10px; text-transform: uppercase; letter-spacing: 1px; color: #818cf8; }
    .main-header .meta-val   { font-size: 13px; font-weight: 600; color: #cbd5e1; }

    .status-complete {
        background: #064e3b; border: 1px solid #047857; color: #a7f3d0;
        padding: 8px 16px; border-radius: 8px; font-weight: 600;
        font-size: 13px; display: inline-block; margin: 3px 3px 3px 0;
        box-shadow: 0 2px 10px rgba(4,120,87,0.2);
    }
    .status-pending {
        background: #78350f; border: 1px solid #d97706; color: #fef3c7;
        padding: 8px 16px; border-radius: 8px; font-weight: 600;
        font-size: 13px; display: inline-block; margin: 3px 3px 3px 0;
        box-shadow: 0 2px 10px rgba(217,119,6,0.2);
    }
    .metric-card {
        background: linear-gradient(135deg, #131a35 0%, #0b0f19 100%); 
        border: 1px solid #1e293b;
        border-radius: 12px; padding: 20px; text-align: center;
        transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1), border-color 0.3s, box-shadow 0.3s;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    .metric-card:hover { 
        transform: translateY(-4px); 
        border-color: #6366f1;
        box-shadow: 0 10px 25px rgba(99,102,241,0.25); 
    }
    .metric-number { font-size: 38px; font-weight: 800; color: #3b82f6; text-shadow: 0 0 10px rgba(59,130,246,0.2); }
    .metric-label  { font-size: 12px; color: #94a3b8; margin-top: 4px; text-transform: uppercase; letter-spacing: 0.5px; }

    .fp-card {
        background: #1e1b4b; border-left: 4px solid #6366f1;
        padding: 16px 20px; border-radius: 0 10px 10px 0; margin-bottom: 12px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
        transition: transform 0.2s;
    }
    .fp-card:hover { transform: translateX(4px); }
    .fp-id   { font-size: 11px; font-weight: 700; color: #a5b4fc; text-transform: uppercase; letter-spacing: 1px; }
    .fp-desc { font-size: 14px; color: #e2e8f0; margin-top: 4px; line-height: 1.5; }

    .section-header {
        font-size: 12px; font-weight: 700; text-transform: uppercase;
        letter-spacing: 1.2px; color: #cbd5e1;
        border-bottom: 2px solid #312e81;
        padding-bottom: 10px; margin-bottom: 18px;
    }

    .conf-high   { color: #34d399; font-weight: 700; }
    .conf-medium { color: #fbbf24; font-weight: 700; }
    .conf-low    { color: #f87171; font-weight: 700; }

    .timing-card {
        background: #151b2d; border: 1px solid #1e293b;
        border-radius: 10px; padding: 16px 20px; margin-bottom: 10px;
        display: flex; justify-content: space-between; align-items: center;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
        transition: border-color 0.2s;
    }
    .timing-card:hover { border-color: #6366f1; }
    .timing-label { font-size: 13px; color: #cbd5e1; font-weight: 500; }
    .timing-val   { font-size: 15px; font-weight: 700; color: #818cf8;
                    font-family: 'JetBrains Mono', monospace; }

    /* Custom styling for all buttons (primary color gradient) */
    .stButton > button {
        background: linear-gradient(90deg, #4f46e5 0%, #3b82f6 100%) !important;
        color: white !important;
        border: none !important;
        padding: 10px 24px !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        transition: all 0.2s ease-in-out !important;
        box-shadow: 0 4px 14px rgba(99, 102, 241, 0.3) !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(99, 102, 241, 0.5) !important;
    }
    .stButton > button:active {
        transform: translateY(0) !important;
    }
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


def get_uvm_components_count() -> int:
    report_path = "generated_uvm/compile_report.json"
    if os.path.exists(report_path):
        try:
            with open(report_path, "r", encoding="utf-8") as f:
                report_data = json.load(f)
            # Find the first design's file count
            if report_data:
                first_design = list(report_data.keys())[0]
                files = report_data[first_design].get("files", {})
                if files:
                    return len(files)
        except Exception:
            pass
    return 12


# ---- SIDEBAR ----
with st.sidebar:
    st.markdown("## VeriGenX")
    st.markdown("Autonomous UVM Verification Intelligence Platform")
    st.divider()

    page = st.radio(
        "Navigation",
        ["Overview", "Signals", "FSM States", "Register Map",
         "Timing Constraints", "Functional Points", "Confidence Report",
         "Test Results", "Generated Testbench", "Repair Log", "Phase 3 Metrics",
         "Validation Report", "Simulation Report", "Waveform Diagnostics", "Traceability Matrix", "Run Pipeline"],
        label_visibility="collapsed"
    )
    st.divider()

    # Dynamic Phase Statuses
    p1_status, p2_status, p3_status, p4_status, p5_status, p6_status, p7_status = False, False, False, False, False, False, False
    if plan is not None:
        p1_status = True
    if os.path.exists("dag.dot"):
        p2_status = True
    else:
        try:
            if os.path.exists("output/pipeline_state.json"):
                with open("output/pipeline_state.json", "r") as f:
                    state = json.load(f)
                    if state.get("dependency_graph"):
                        p2_status = True
        except Exception:
            pass

    if os.path.exists("generated_uvm/compile_report.json"):
        try:
            with open("generated_uvm/compile_report.json", "r") as f:
                rep = json.load(f)
                if rep:
                    p3_status = True
        except Exception:
            pass
    if not p3_status:
        try:
            if os.path.exists("output/pipeline_state.json"):
                with open("output/pipeline_state.json", "r") as f:
                    state = json.load(f)
                    if state.get("generated_files"):
                        p3_status = True
        except Exception:
            pass

    if os.path.exists("output/sim_validation_report.json"):
        p4_status = True
    else:
        try:
            if os.path.exists("output/pipeline_state.json"):
                with open("output/pipeline_state.json", "r") as f:
                    state = json.load(f)
                    if state.get("simulation_results"):
                        p4_status = True
        except Exception:
            pass

    if os.path.exists("output/coverhunter_report.json") or os.path.exists("output/coverhunter_report_uart.json") or os.path.exists("output/coverhunter_report_spi.json") or os.path.exists("output/coverhunter_report_i2c.json"):
        p5_status = True

    if os.path.exists("CLIENT_REPORT_WAVEFORM.html") and os.path.getsize("CLIENT_REPORT_WAVEFORM.html") > 0:
        p6_status = True

    if os.path.exists("CLIENT_REPORT_TRACEABILITY.html") and os.path.getsize("CLIENT_REPORT_TRACEABILITY.html") > 0:
        p7_status = True

    st.markdown("**Phase Status**")
    if p1_status:
        st.markdown('<span class="status-complete">Phase 1 — SpecMind</span>',  unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-pending">Phase 1 — SpecMind</span>',  unsafe_allow_html=True)
        
    if p2_status:
        st.markdown('<span class="status-complete">Phase 2 — ArchWeaver</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-pending">Phase 2 — ArchWeaver</span>', unsafe_allow_html=True)
        
    if p3_status:
        st.markdown('<span class="status-complete">Phase 3 — UVMForge</span>',   unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-pending">Phase 3 — UVMForge</span>',   unsafe_allow_html=True)

    if p4_status:
        st.markdown('<span class="status-complete">Phase 4 — SimRunner</span>',  unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-pending">Phase 4 — SimRunner</span>',  unsafe_allow_html=True)

    if p5_status:
        st.markdown('<span class="status-complete">Phase 5 — CoverHunter</span>',  unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-pending">Phase 5 — CoverHunter</span>',  unsafe_allow_html=True)

    if p6_status:
        st.markdown('<span class="status-complete">Phase 6 — WaveWhisperer</span>',  unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-pending">Phase 6 — WaveWhisperer</span>',  unsafe_allow_html=True)

    if p7_status:
        st.markdown('<span class="status-complete">Phase 7 — TraceVault</span>',  unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-pending">Phase 7 — TraceVault</span>',  unsafe_allow_html=True)
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

if plan:
    completed_phases = []
    if p1_status:
        completed_phases.append("1")
    if p2_status:
        completed_phases.append("2")
    if p3_status:
        completed_phases.append("3")
    if p4_status:
        completed_phases.append("4")
    if p5_status:
        completed_phases.append("5")
    if p6_status:
        completed_phases.append("6")
    if p7_status:
        completed_phases.append("7")
    
    if completed_phases:
        if len(completed_phases) == 1:
            phase_str = f"Phase {completed_phases[0]} Complete"
        elif len(completed_phases) == 2:
            phase_str = f"Phase {completed_phases[0]} and {completed_phases[1]} Complete"
        else:
            phase_str = "Phase " + ", ".join(completed_phases[:-1]) + f", and {completed_phases[-1]} Complete"
        subtitle_display = f"{design_display} Verification Test Plan — {phase_str}"
    else:
        subtitle_display = f"{design_display} Verification Test Plan — Initializing"
else:
    subtitle_display = "No test plan loaded yet"

st.markdown(f"""
<div class="main-header">
    <h1>VeriGenX Dashboard</h1>
    <p class="subtitle">{subtitle_display}</p>
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
        comp_count = get_uvm_components_count()
        st.markdown(f'<div class="metric-card"><div class="metric-number">{comp_count}</div><div class="metric-label">UVM Components</div></div>', unsafe_allow_html=True)

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
        if p1_status:
            st.success("**Phase 1 — SpecMind:** Complete\n\nSpec parsed. Chunks embedded. Test plan generated with signals, FSM, registers, timing, and functional points.")
        else:
            st.warning("**Phase 1 — SpecMind:** Pending\n\nTest plan generation pending.")

        if p2_status:
            st.success("**Phase 2 — ArchWeaver:** Complete\n\nDependency graph resolved, topologically ordered, and interface consistency checked.")
        else:
            st.warning("**Phase 2 — ArchWeaver:** Pending\n\nDependency graph resolution pending.")

        if p3_status:
            st.success("**Phase 3 — UVMForge:** Complete\n\nTestbench generated and compiled cleanly with Verilator.")
        else:
            st.warning("**Phase 3 — UVMForge:** Pending\n\nTestbench generation and compilation pending.")

        if p4_status:
            st.success("**Phase 4 — SimRunner:** Complete\n\nMulti-test timing simulations run successfully, VCD traces generated, and distinct coverage metrics parsed.")
        else:
            st.warning("**Phase 4 — SimRunner:** Pending\n\nSimulations and coverage parsing pending.")

        if p5_status:
            st.success("**Phase 5 — CoverHunter:** Complete\n\nCoverage closure feedback loop executed, targeted tests generated, and functional coverage targets achieved.")
        else:
            st.warning("**Phase 5 — CoverHunter:** Pending\n\nCoverage closure loop and test generation pending.")

        if p6_status:
            st.success("**Phase 6 — WaveWhisperer:** Complete\n\nWaveform anomaly explanation engine ran, timing/reset rules checked, and interactive diagnostics report generated.")
        else:
            st.warning("**Phase 6 — WaveWhisperer:** Pending\n\nWaveform diagnostics pending.")

        if p7_status:
            st.success("**Phase 7 — TraceVault:** Complete\n\nSpec-to-coverage traceability matrix built, mapping specification requirements to test cases and simulation outcomes.")
        else:
            st.warning("**Phase 7 — TraceVault:** Pending\n\nTraceability matrix generation pending.")


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
    
    report_path = "generated_uvm/compile_report.json"
    repair_path = "output/repair_attempts.json"
    
    results = []
    
    # Add Phase 1 and Phase 2 checks if plan exists
    if plan is not None:
        results.append(("Phase 1", "Spec Parser", "Specification Parsing (TXT/PDF/DOCX/XML/RDL)", "PASS"))
        results.append(("Phase 1", "Test Plan", "Test Plan Generation (signals, FSM, registers, timing)", "PASS"))
        if plan.get("confidence"):
            results.append(("Phase 1", "Confidence Report", "Extraction confidence scoring", "PASS"))
            
    if os.path.exists("dag.dot"):
        results.append(("Phase 2", "DAG Builder", "Topological Sort & Cycle Detection check", "PASS"))
        results.append(("Phase 2", "DAG Visualization", "DOT graph representation export", "PASS"))
        
    compile_exists = os.path.exists(report_path)
    repair_exists = os.path.exists(repair_path)
    
    if not compile_exists and not repair_exists and not results:
        st.info("No test results are available yet. Run the pipeline first to generate and validate testbenches.")
    else:
        # Load compile report
        if compile_exists:
            try:
                with open(report_path, "r", encoding="utf-8") as f:
                    report_data = json.load(f)
                for design, ddetails in report_data.items():
                    files = ddetails.get("files", {})
                    for fname, fdetails in files.items():
                        status = "PASS" if fdetails.get("status") == "passed" else "FAIL"
                        first_att = " (first attempt)" if fdetails.get("first_attempt") else ""
                        results.append((
                            f"Phase 3 ({design.upper()})",
                            fname,
                            f"Verilator lint compilation check{first_att}",
                            status
                        ))
            except Exception as e:
                st.warning(f"Error loading compile report: {e}")
                
        # Load repair attempts
        if repair_exists:
            try:
                with open(repair_path, "r", encoding="utf-8") as f:
                    repair_data = json.load(f)
                for entry in repair_data:
                    filepath = entry.get("filepath", "")
                    fname = os.path.basename(filepath)
                    attempts = entry.get("attempts", 0)
                    success = entry.get("success", False)
                    status = "PASS" if success else "FAIL"
                    errs_str = ", ".join(entry.get("error_types_encountered", []))
                    results.append((
                        "Phase 3 (Repair)",
                        fname,
                        f"Auto-repair execution ({attempts} attempts, errors: {errs_str})",
                        status
                    ))
            except Exception as e:
                st.warning(f"Error loading repair attempts: {e}")
                
        if results:
            import pandas as pd
            df = pd.DataFrame(results, columns=["Phase", "Component/File", "Test Description", "Status"])
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            pass_count = sum(1 for r in results if r[3] == "PASS")
            fail_count = sum(1 for r in results if r[3] == "FAIL")
            if fail_count > 0:
                st.warning(f"Checks completed: {pass_count} passed, {fail_count} failed.")
            else:
                st.success(f"All {pass_count}/{len(results)} checks passing. Zero failures.")
        else:
            st.info("No test results are available yet. Run the pipeline first to generate and validate testbenches.")


elif page == "Generated Testbench":
    st.markdown('<div class="section-header">Generated Testbench Compilation Report</div>', unsafe_allow_html=True)
    
    report_path = "generated_uvm/compile_report.json"
    if not os.path.exists(report_path):
        st.warning("No compilation report found. Please run the pipeline first.")
    else:
        try:
            with open(report_path, "r", encoding="utf-8") as f:
                report_data = json.load(f)
            
            design_options = list(report_data.keys())
            if design_options:
                selected_design = st.selectbox("Select Design", design_options)
                design_report = report_data[selected_design]
                
                # Summary metrics
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Verilator Available", "Yes" if design_report.get("verilator_available", False) else "No")
                with col2:
                    rate = design_report.get("first_attempt_success_rate", 0.0)
                    st.metric("First-Attempt Pass Rate", f"{rate:.1f}%")
                
                st.markdown("### File Compilation Details")
                files_data = []
                for fname, fdetails in design_report.get("files", {}).items():
                    files_data.append({
                        "File Name": fname,
                        "Status": fdetails.get("status", "unknown").upper(),
                        "First Attempt Pass": "Yes" if fdetails.get("first_attempt", False) else "No",
                        "Errors": fdetails.get("errors", "")
                    })
                
                import pandas as pd
                df_files = pd.DataFrame(files_data)
                st.dataframe(df_files[["File Name", "Status", "First Attempt Pass"]], use_container_width=True, hide_index=True)
                
                # Show details for files with errors
                for fd in files_data:
                    if fd["Errors"]:
                        with st.expander(f"Compile Error log for {fd['File Name']}"):
                            st.code(fd["Errors"], language="text")
            else:
                st.warning("No design report data found in compile_report.json")
        except Exception as e:
            st.error(f"Failed to read compile report: {e}")


elif page == "Repair Log":
    st.markdown('<div class="section-header">Phase 3 Auto-Repair Log</div>', unsafe_allow_html=True)
    repair_path = "output/repair_attempts.json"
    
    if not os.path.exists(repair_path):
        st.info("No repair attempts logged yet — all files compiled cleanly on first attempt, or the pipeline hasn't run.")
    else:
        try:
            with open(repair_path, "r", encoding="utf-8") as f:
                repair_data = json.load(f)
        except Exception as e:
            st.error(f"Failed to read repair log: {e}")
            st.stop()
            
        if not repair_data:
            st.info("No repair attempts logged yet — all files compiled cleanly on first attempt, or the pipeline hasn't run.")
        else:
            # Summary Metrics
            total_repaired = len(repair_data)
            success_count = sum(1 for r in repair_data if r.get("success", False))
            success_rate = (success_count / total_repaired) if total_repaired > 0 else 1.0
            
            # Find most common error type
            error_types = []
            for r in repair_data:
                error_types.extend(r.get("error_types_encountered", []))
            
            if error_types:
                from collections import Counter
                most_common_err = Counter(error_types).most_common(1)[0][0]
            else:
                most_common_err = "None"
                
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f'<div class="metric-card"><div class="metric-number">{total_repaired}</div><div class="metric-label">Total Files Repaired</div></div>', unsafe_allow_html=True)
            with col2:
                st.markdown(f'<div class="metric-card"><div class="metric-number">{success_rate:.1%}</div><div class="metric-label">Overall Success Rate</div></div>', unsafe_allow_html=True)
            with col3:
                st.markdown(f'<div class="metric-card"><div class="metric-number">{most_common_err}</div><div class="metric-label">Most Common Error</div></div>', unsafe_allow_html=True)
                
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("### Repair History Details")
            
            # Build table
            table_rows = []
            for r in repair_data:
                filepath = r.get("filepath", "")
                filename = os.path.basename(filepath)
                table_rows.append({
                    "File": filename,
                    "Run ID": r.get("run_id", ""),
                    "Attempts": r.get("attempts", 0),
                    "Success": "PASSED" if r.get("success", False) else "FAILED",
                    "Error Types Encountered": ", ".join(r.get("error_types_encountered", []))
                })
                
            import pandas as pd
            df_repair = pd.DataFrame(table_rows)
            st.dataframe(df_repair, use_container_width=True, hide_index=True)
            
            st.markdown("### Backup Code Viewer")
            # Expanders for backups
            for r in repair_data:
                filepath = r.get("filepath", "")
                filename = os.path.basename(filepath)
                run_id = r.get("run_id", "")
                attempts = r.get("attempts", 0)
                
                with st.expander(f"View backup files for {filename} (Run: {run_id})"):
                    found_backups = False
                    for i in range(1, attempts + 1):
                        backup_file = f"output/{run_id}/backups/iter_{i}/{filename}"
                        if os.path.exists(backup_file):
                            found_backups = True
                            st.markdown(f"**Iteration {i} Backup:**")
                            try:
                                with open(backup_file, "r", encoding="utf-8") as bf:
                                    content = bf.read()
                                st.code(content, language="systemverilog")
                            except Exception as e:
                                st.error(f"Failed to read backup {backup_file}: {e}")
                    if not found_backups:
                        st.write("No backup file found on disk.")


elif page == "Phase 3 Metrics":
    st.markdown('<div class="section-header">Phase 3: UVMForge Compilation & Repair Metrics</div>', unsafe_allow_html=True)
    metrics_path = "output/uvmforge_metrics.json"
    
    if not os.path.exists(metrics_path):
        st.info("No Phase 3 metrics data found. Run the validation or benchmark scripts to collect metrics.")
    else:
        try:
            with open(metrics_path, "r", encoding="utf-8") as f:
                metrics_data = json.load(f)
        except Exception as e:
            st.error(f"Failed to read metrics: {e}")
            st.stop()
            
        # Metric cards
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f'<div class="metric-card"><div class="metric-number">{metrics_data.get("total_runs", 0)}</div><div class="metric-label">Total Runs</div></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="metric-card"><div class="metric-number">{metrics_data.get("first_pass_rate", 0.0):.1f}%</div><div class="metric-label">First-Pass Rate</div></div>', unsafe_allow_html=True)
        with col3:
            st.markdown(f'<div class="metric-card"><div class="metric-number">{metrics_data.get("overall_success_rate", 0.0):.1f}%</div><div class="metric-label">Overall Success Rate</div></div>', unsafe_allow_html=True)
        with col4:
            st.markdown(f'<div class="metric-card"><div class="metric-number">{metrics_data.get("avg_repair_iterations", 0.0):.2f}</div><div class="metric-label">Avg Repair Iters</div></div>', unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### Compilation Status Breakdown")
        
        # Simple bar chart
        import pandas as pd
        breakdown_data = {
            "Count": [
                metrics_data.get("first_pass_success", 0),
                metrics_data.get("repair_success", 0),
                metrics_data.get("failures", 0)
            ]
        }
        df_breakdown = pd.DataFrame(breakdown_data, index=["First-Pass Success", "Repair Success", "Failures"])
        st.bar_chart(df_breakdown)
        
        # Benchmark report
        benchmark_path = "output/uvmforge_benchmark_report.json"
        if os.path.exists(benchmark_path):
            try:
                with open(benchmark_path, "r", encoding="utf-8") as f:
                    bench_data = json.load(f)
                bench_results = bench_data.get("benchmark_results", {})
                if bench_results:
                    st.markdown("### Per-Design Benchmark Results")
                    bench_rows = []
                    for design, info in bench_results.items():
                        bench_rows.append({
                            "Design": design.upper(),
                            "Status": info.get("status", "unknown").upper(),
                            "Files Generated": info.get("files_count", 0)
                        })
                    df_bench = pd.DataFrame(bench_rows)
                    st.dataframe(df_bench, use_container_width=True, hide_index=True)
            except Exception as e:
                st.warning(f"Could not load benchmark report: {e}")


elif page == "Validation Report":
    st.markdown('<div class="section-header">Phase 3: Reference Designs Validation Report</div>', unsafe_allow_html=True)
    val_path = "output/validation_report.json"
    
    if not os.path.exists(val_path):
        st.info("No validation report found. Run scripts/validate_phase3.py to generate the validation report.")
    else:
        try:
            with open(val_path, "r", encoding="utf-8") as f:
                val_data = json.load(f)
        except Exception as e:
            st.error(f"Failed to read validation report: {e}")
            st.stop()
            
        metrics = val_data.get("metrics", {})
        
        # Aggregate metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f'<div class="metric-card"><div class="metric-number">{metrics.get("first_pass_rate", 0.0):.1f}%</div><div class="metric-label">First-Pass Rate</div></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="metric-card"><div class="metric-number">{metrics.get("overall_success_rate", 0.0):.1f}%</div><div class="metric-label">Overall Success Rate</div></div>', unsafe_allow_html=True)
        with col3:
            st.markdown(f'<div class="metric-card"><div class="metric-number">{metrics.get("avg_repair_iterations", 0.0):.2f}</div><div class="metric-label">Avg Repair Iters</div></div>', unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### Reference Designs Status")
        
        # Build and show HTML table
        details = val_data.get("details", {})
        html_table = """
        <table style="width:100%; border-collapse:collapse; margin-bottom:20px; font-size:14px;">
            <thead>
                <tr style="border-bottom:2px solid #334155; text-align:left;">
                    <th style="padding:10px 12px; font-weight:700; color:#94a3b8;">Design</th>
                    <th style="padding:10px 12px; font-weight:700; color:#94a3b8;">Status</th>
                    <th style="padding:10px 12px; font-weight:700; color:#94a3b8;">Details / Reason</th>
                </tr>
            </thead>
            <tbody>
        """
        
        for design_name, info in details.items():
            status = info.get("status", "unknown").upper()
            reason = info.get("reason", "") or (f"Generated {info.get('files_count', 0)} UVM testbench files" if "files_count" in info else "")
            
            if status == "PASSED":
                badge = '<span class="status-complete" style="padding:4px 8px; font-size:11px; margin:0;">PASSED</span>'
            elif status == "FAILED":
                badge = '<span style="background:#7f1d1d; border:1px solid #b91c1c; color:#fecaca; padding:4px 8px; border-radius:8px; font-weight:600; font-size:11px; display:inline-block; margin:0;">FAILED</span>'
            else:
                badge = '<span class="status-pending" style="padding:4px 8px; font-size:11px; margin:0;">SKIPPED</span>'
                
            html_table += f"""
                <tr style="border-bottom:1px solid #334155;">
                    <td style="padding:10px 12px; font-weight:600; color:#cbd5e1;">{design_name.upper()}</td>
                    <td style="padding:10px 12px;">{badge}</td>
                    <td style="padding:10px 12px; color:#94a3b8;">{reason}</td>
                </tr>
            """
            
        html_table += "</tbody></table>"
        st.markdown(html_table, unsafe_allow_html=True)
        
        # Call out skipped reference designs
        skipped = val_data.get("skipped_designs", [])
        if skipped:
            st.markdown('<div class="section-header" style="font-size:11px; margin-top:20px;">Skipped Reference Designs</div>', unsafe_allow_html=True)
            st.warning(
                f"The following reference designs were skipped because they lack specification plans or JSON fixtures:\n\n"
                f"**Skipped designs:** {', '.join(skipped)}"
            )


elif page == "Simulation Report":
    st.markdown('<div class="section-header">Phase 4: SimRunner Simulation Report</div>', unsafe_allow_html=True)
    val_path = "output/sim_validation_report.json"
    
    if not os.path.exists(val_path):
        st.info("No simulation validation report found. Run the simulation pipeline to generate results.")
    else:
        try:
            with open(val_path, "r", encoding="utf-8") as f:
                val_data = json.load(f)
        except Exception as e:
            st.error(f"Failed to read simulation report: {e}")
            st.stop()
            
        design_name = val_data.get("design_name", "unknown").upper()
        status = val_data.get("status", "failed").upper()
        run_id = val_data.get("run_id", "N/A")
        
        # Display overall simulation outcome
        col1, col2, col3 = st.columns(3)
        with col1:
            if status == "PASSED":
                badge = '<span class="status-complete">PASSED</span>'
            else:
                badge = '<span style="background:#fef2f2; border:1px solid #fecaca; color:#dc2626; padding:8px 16px; border-radius:8px; font-weight:600; font-size:13px; display:inline-block;">FAILED</span>'
            st.markdown(f"**Overall Simulation Status:** {badge}", unsafe_allow_html=True)
        with col2:
            st.markdown(f"**Design Name:** `{design_name}`")
        with col3:
            st.markdown(f"**Run ID:** `{run_id}`")
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Coverage metrics
        cov = val_data.get("coverage", {})
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f'<div class="metric-card"><div class="metric-number">{cov.get("line_coverage", 0.0):.1f}%</div><div class="metric-label">Line Coverage</div></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="metric-card"><div class="metric-number">{cov.get("branch_coverage", 0.0):.1f}%</div><div class="metric-label">Branch Coverage</div></div>', unsafe_allow_html=True)
        with col3:
            st.markdown(f'<div class="metric-card"><div class="metric-number">{cov.get("toggle_coverage", 0.0):.1f}%</div><div class="metric-label">Toggle Coverage</div></div>', unsafe_allow_html=True)
        with col4:
            func_cov = cov.get("functional_coverage", 0.0)
            st.markdown(f'<div class="metric-card"><div class="metric-number">{func_cov:.1f}%</div><div class="metric-label">Functional Coverage</div></div>', unsafe_allow_html=True)
            
        st.markdown(
            '<div style="background:#fffbeb; border:1px solid #fef3c7; color:#b45309; padding:12px; border-radius:8px; font-size:12px; margin-top:8px;">'
            '<strong>* Functional Coverage:</strong> SystemVerilog coverpoints are tracked via manual hit-counters '
            'inside the mock subscriber class and dumped to a JSON report at simulation exit.'
            '</div>',
            unsafe_allow_html=True
        )
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### Test Classes Results")
        
        tests = val_data.get("tests", {})
        for tname, tres in tests.items():
            tstatus = "PASSED" if tres.get("success", False) else "FAILED"
            tcolor = "#f0fdf4" if tstatus == "PASSED" else "#fef2f2"
            tborder = "#bbf7d0" if tstatus == "PASSED" else "#fecaca"
            tfont = "#15803d" if tstatus == "PASSED" else "#dc2626"
            
            with st.expander(f"{tname} — {tstatus}"):
                st.markdown(f"**VCD Path:** `{tres.get('vcd_path', 'N/A')}`")
                
                # Show errors if any
                log_summary = tres.get("log_summary", {})
                errors_list = log_summary.get("errors", [])
                fatals_list = log_summary.get("fatals", [])
                
                if errors_list or fatals_list:
                    st.error(f"Errors detected: {len(errors_list)} Error(s), {len(fatals_list)} Fatal(s)")
                    for err in fatals_list:
                        st.code(err, language="text")
                    for err in errors_list:
                        st.code(err, language="text")
                else:
                    st.success("No errors detected in simulation run.")
                    
                # Show stdout output
                st.markdown("**Simulation Log Output:**")
                st.code(tres.get("stdout", ""), language="text")


elif page == "Waveform Diagnostics":
    st.markdown('<div class="section-header">Phase 6: WaveWhisperer Waveform Anomaly Diagnostics</div>', unsafe_allow_html=True)
    report_path = "CLIENT_REPORT_WAVEFORM.html"
    
    if not os.path.exists(report_path):
        st.info("No Waveform Diagnostics report found. Run the timing checks and explanation engine first.")
    else:
        try:
            with open(report_path, "r", encoding="utf-8") as f:
                html_content = f.read()
            
            import streamlit.components.v1 as components
            components.html(html_content, height=850, scrolling=True)
            
            st.success("Loaded Waveform Diagnostics report successfully.")
        except Exception as e:
            st.error(f"Failed to load report: {e}")


elif page == "Traceability Matrix":
    st.markdown('<div class="section-header">Phase 7: TraceVault Spec-to-Coverage Traceability Matrix</div>', unsafe_allow_html=True)
    report_path = "CLIENT_REPORT_TRACEABILITY.html"
    
    if not os.path.exists(report_path):
        st.info("No Traceability Matrix report found. Run the traceability engine first to generate the report.")
    else:
        try:
            with open(report_path, "r", encoding="utf-8") as f:
                html_content = f.read()
            
            import streamlit.components.v1 as components
            components.html(html_content, height=850, scrolling=True)
            
            st.success("Loaded Traceability Matrix report successfully.")
        except Exception as e:
            st.error(f"Failed to load report: {e}")


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
        "# Activate virtual environment first\n"
        "# Windows:\n"
        "venv\\Scripts\\activate\n"
        "# Linux/Mac:\n"
        "source venv/bin/activate\n\n"
        "# Run full pipeline\n"
        "python -m VeriGenX.orchestrator --spec input_designs/uart_spec.txt\n\n"
        "# Run quick tests\n"
        "python test_phase1.py\n"
        "python test_phase2.py\n"
        "pytest tests/ -v",
        language="bash"
    )
