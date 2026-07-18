import os
from typing import Dict, List, Any
from VeriGenX.agents.tracevault.db_manager import TraceabilityDBManager

class ReportExporter:
    """
    Generates a premium, self-contained HTML traceability report (TraceVault).
    Features interactive heatmaps, navigable cross-references, requirement completion rates,
    and verified status indicators.
    """
    def __init__(self, db_path: str = "output/traceability.db"):
        self.db = TraceabilityDBManager(db_path)

    def export_html(self, design_name: str, output_path: str = "CLIENT_REPORT_TRACEABILITY.html"):
        """Compiles traceability records and exports them to a premium styled HTML file."""
        data = self.db.get_all_traceability_data(design_name)
        
        # 1. Compute Section Metrics
        sections_metrics = self._compute_section_metrics(data)
        
        # 2. Render HTML Content
        html = self._generate_html_content(design_name, data, sections_metrics)
        
        # 3. Write to Disk
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"  [ReportExporter] Exported traceability dashboard: {output_path}")

    def _compute_section_metrics(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Calculates completion rates for each spec section based on linked FP coverage."""
        sections = data["sections"]
        fps = data["functional_points"]
        bins = {b["bin_name"]: b["achieved_coverage"] for b in data["coverage_bins"]}
        
        metrics = []
        for sec in sections:
            sec_id = sec["id"]
            sec_name = sec["section_name"]
            
            # Find linked functional points
            linked_fps = [f for f in fps if f["section_id"] == sec_id]
            
            if not linked_fps:
                completion = 0.0
            else:
                total_cov = 0.0
                for fp in linked_fps:
                    fp_code = fp["fp_id"]
                    total_cov += bins.get(fp_code, 0.0)
                completion = total_cov / len(linked_fps)
                
            metrics.append({
                "id": sec_id,
                "name": sec_name,
                "fps_count": len(linked_fps),
                "completion_percentage": completion,
                "fps": linked_fps
            })
        return metrics

    def _generate_html_content(self, design_name: str, data: Dict[str, Any], sections_metrics: List[Dict[str, Any]]) -> str:
        # Build mappings
        results = data["simulation_results"]
        bins_map = {b["bin_name"]: b["achieved_coverage"] for b in data["coverage_bins"]}
        
        # Map tests linked to each FP
        fp_to_tests = {}
        for link in data["fp_test_links"]:
            fp_id = link["fp_id"]
            test_id = link["test_id"]
            if fp_id not in fp_to_tests:
                fp_to_tests[fp_id] = []
            fp_to_tests[fp_id].append(test_id)
            
        tests_map = {t["id"]: t for t in data["test_cases"]}
        fps_map = {f["id"]: f for f in data["functional_points"]}
        
        # Heatmap grid generation
        heatmap_rows = ""
        for sec in sections_metrics:
            sec_name = sec["name"]
            completion = sec["completion_percentage"]
            
            # Heatmap color scale based on completion
            if completion >= 100.0:
                bg_color = "rgba(16, 185, 129, 0.15)"
                border_color = "var(--green)"
            elif completion > 0.0:
                bg_color = "rgba(245, 158, 11, 0.15)"
                border_color = "var(--warning)"
            else:
                bg_color = "rgba(239, 68, 68, 0.15)"
                border_color = "var(--red)"

            heatmap_rows += f"""
            <div class="heatmap-card" style="background: {bg_color}; border-left: 4px solid {border_color};" id="card-sec-{sec['id']}">
                <div class="heatmap-header">
                    <span class="heatmap-sec-name"><a href="#sec-{sec['id']}">{sec_name}</a></span>
                    <span class="heatmap-badge" style="background: {border_color}22; color: {border_color};">{completion:.1f}%</span>
                </div>
                <div class="heatmap-body">
            """
            if not sec["fps"]:
                heatmap_rows += '<div class="heatmap-no-fp">No functional points linked</div>'
            else:
                for fp in sec["fps"]:
                    fp_code = fp["fp_id"]
                    fp_cov = bins_map.get(fp_code, 0.0)
                    cov_color = "var(--green)" if fp_cov >= 100.0 else ("var(--warning)" if fp_cov > 0.0 else "var(--muted)")
                    
                    # Get tests mapped to this fp
                    linked_t_ids = fp_to_tests.get(fp["id"], [])
                    t_names_str = ", ".join([f'<a href="#test-{tid}">{tests_map[tid]["test_name"]}</a>' for tid in linked_t_ids]) or "None"
                    
                    heatmap_rows += f"""
                    <div class="heatmap-fp-row">
                        <span class="heatmap-fp-id"><a href="#fp-{fp['id']}">{fp_code}</a></span>
                        <span class="heatmap-fp-desc">{fp['description']}</span>
                        <span class="heatmap-fp-cov" style="color: {cov_color};">{fp_cov:.1f}%</span>
                        <span class="heatmap-fp-tests">Linked Tests: {t_names_str}</span>
                    </div>
                    """
            heatmap_rows += "</div></div>"

        # Requirement completion table
        req_rows = ""
        for sec in sections_metrics:
            comp_val = sec["completion_percentage"]
            progress_bar_color = "var(--green)" if comp_val >= 100.0 else ("var(--warning)" if comp_val > 0.0 else "var(--red)")
            req_rows += f"""
            <tr id="sec-{sec['id']}">
                <td><strong>{sec['name']}</strong></td>
                <td>{sec['fps_count']}</td>
                <td>
                    <div class="progress-container">
                        <div class="progress-bar" style="width: {comp_val}%; background-color: {progress_bar_color};"></div>
                    </div>
                    <span class="progress-text">{comp_val:.1f}%</span>
                </td>
                <td>
                    <a href="#card-sec-{sec['id']}" class="btn-micro">Go to Heatmap</a>
                </td>
            </tr>
            """

        # Detailed Mapping Table (FPs vs Tests)
        mapping_rows = ""
        for fp in data["functional_points"]:
            fp_code = fp["fp_id"]
            sec_name = next((s["section_name"] for s in data["sections"] if s["id"] == fp["section_id"]), "Unknown")
            cov_val = bins_map.get(fp_code, 0.0)
            status_badge = f'<span class="badge badge-pass" style="color:var(--green); border-color:var(--green)44;">{cov_val:.1f}% Covered</span>' if cov_val >= 100.0 else f'<span class="badge badge-warn">{cov_val:.1f}% Covered</span>'
            
            linked_t_ids = fp_to_tests.get(fp["id"], [])
            t_links = [f'<a href="#test-{tid}">{tests_map[tid]["test_name"]}</a>' for tid in linked_t_ids]
            t_str = ", ".join(t_links) if t_links else '<span style="color:var(--red);">No Test Linked</span>'

            mapping_rows += f"""
            <tr id="fp-{fp['id']}">
                <td><strong class="mono">{fp_code}</strong></td>
                <td>{fp['description']}</td>
                <td><a href="#sec-{fp['section_id']}">{sec_name}</a></td>
                <td>{status_badge}</td>
                <td>{t_str}</td>
            </tr>
            """

        # Test Satisfying Spec Mapping
        test_rows = ""
        for t in data["test_cases"]:
            t_id = t["id"]
            t_name = t["test_name"]
            t_res = results.get(t_name, {})
            t_status = t_res.get("status", "pending")
            
            if t_status == "passed":
                status_badge = '<span class="badge badge-pass">PASSED</span>'
            elif t_status == "failed":
                status_badge = '<span class="badge badge-fail">FAILED</span>'
            else:
                status_badge = '<span class="badge badge-pending">PENDING</span>'
                
            # Find FPs satisfied by this test
            satisfied_fps = []
            for fp_id_key, linked_t_ids in fp_to_tests.items():
                if t_id in linked_t_ids:
                    satisfied_fps.append(fps_map[fp_id_key]["fp_id"])
                    
            sat_str = ", ".join([f'<a href="#fp-{next(f["id"] for f in data["functional_points"] if f["fp_id"] == fcode)}">{fcode}</a>' for fcode in satisfied_fps]) or "None"

            test_rows += f"""
            <tr id="test-{t_id}">
                <td><strong class="mono">{t_name}</strong></td>
                <td>{status_badge}</td>
                <td>{sat_str}</td>
                <td><code style="font-size:11px; opacity:0.8;">{t['file_path']}</code></td>
            </tr>
            """

        # Template compilation
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>VeriGenX Traceability Matrix — {design_name.upper()}</title>
  <style>
    :root {{
      --bg: #030712;
      --surface: #0b0f19;
      --surface2: #1e293b;
      --border: #1e293b;
      --text: #f8fafc;
      --muted: #94a3b8;
      --accent: #06b6d4;
      --accent2: #3b82f6;
      --green: #10b981;
      --warning: #f59e0b;
      --red: #ef4444;
      --font-mono: 'JetBrains Mono', 'Fira Code', monospace;
    }}
    body {{
      background-color: var(--bg);
      color: var(--text);
      font-family: 'Inter', -apple-system, sans-serif;
      margin: 0;
      padding: 0;
      line-height: 1.6;
    }}
    .header {{
      background: linear-gradient(135deg, #1e1b4b 0%, #030712 100%);
      border-bottom: 1px solid var(--border);
      padding: 48px 2rem;
      text-align: center;
    }}
    .header h1 {{
      font-size: 36px;
      font-weight: 800;
      margin: 0 0 8px 0;
      letter-spacing: -1px;
    }}
    .header h1 span {{ color: var(--accent); }}
    .header p {{ color: var(--muted); max-width: 700px; margin: 0 auto; font-size: 15px; }}
    
    .container {{
      max-width: 1200px;
      margin: 0 auto;
      padding: 48px 2rem 80px;
    }}
    
    /* Alerts */
    .caveat-box {{
      background: rgba(99, 102, 241, 0.1);
      border: 1px solid rgba(99, 102, 241, 0.2);
      border-left: 4px solid var(--accent2);
      padding: 16px 24px;
      border-radius: 12px;
      margin-bottom: 40px;
      font-size: 13px;
      color: #cbd5e1;
    }}
    .caveat-box strong {{ color: var(--text); }}
    
    .section-title {{
      font-size: 14px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 1.5px;
      color: var(--accent);
      margin-bottom: 24px;
      padding-bottom: 12px;
      border-bottom: 1px solid var(--border);
    }}
    
    /* Tables */
    .table-wrap {{
      background: var(--surface);
      border-radius: 16px;
      overflow: hidden;
      border: 1px solid var(--border);
      margin-bottom: 48px;
    }}
    table {{ width: 100%; border-collapse: collapse; }}
    thead tr {{ background: var(--surface2); }}
    thead th {{
      padding: 16px 24px;
      text-align: left;
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 1.5px;
      color: var(--muted);
      border-bottom: 1px solid var(--border);
    }}
    tbody tr {{ border-bottom: 1px solid var(--border); transition: background 0.15s; }}
    tbody tr:last-child {{ border-bottom: none; }}
    tbody tr:hover {{ background: rgba(255,255,255,0.015); }}
    tbody td {{ padding: 16px 24px; font-size: 14px; color: #cbd5e1; }}
    
    a {{ color: var(--accent); text-decoration: none; font-weight: 500; }}
    a:hover {{ text-decoration: underline; }}
    .mono {{ font-family: var(--font-mono); font-size: 13px; }}
    
    /* Progress Bars */
    .progress-container {{
      width: 140px;
      height: 8px;
      background: #1e293b;
      border-radius: 10px;
      display: inline-block;
      vertical-align: middle;
      overflow: hidden;
    }}
    .progress-bar {{ height: 100%; border-radius: 10px; }}
    .progress-text {{
      display: inline-block;
      vertical-align: middle;
      margin-left: 10px;
      font-weight: 700;
      font-size: 13px;
    }}
    
    /* Heatmap Grid */
    .heatmap-grid {{
      display: grid;
      grid-template-columns: 1fr;
      gap: 20px;
      margin-bottom: 48px;
    }}
    .heatmap-card {{
      border-radius: 16px;
      padding: 24px;
      border: 1px solid var(--border);
    }}
    .heatmap-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
    }}
    .heatmap-sec-name {{ font-size: 16px; font-weight: 700; }}
    .heatmap-sec-name a {{ color: var(--text); }}
    .heatmap-sec-name a:hover {{ color: var(--accent); }}
    .heatmap-badge {{
      padding: 4px 12px;
      border-radius: 20px;
      font-size: 12px;
      font-weight: 700;
    }}
    .heatmap-body {{ display: flex; flex-direction: column; gap: 10px; }}
    .heatmap-fp-row {{
      display: grid;
      grid-template-columns: 100px 1fr 80px 220px;
      font-size: 13px;
      padding: 8px 12px;
      background: rgba(255,255,255,0.02);
      border-radius: 8px;
      border: 1px solid var(--border);
      align-items: center;
    }}
    .heatmap-fp-id {{ font-family: var(--font-mono); font-weight: 700; }}
    .heatmap-fp-desc {{ color: #cbd5e1; }}
    .heatmap-fp-cov {{ font-weight: 700; text-align: right; }}
    .heatmap-fp-tests {{ font-size: 11px; text-align: right; color: var(--muted); }}
    .heatmap-no-fp {{ font-size: 13px; color: var(--muted); font-style: italic; }}
    
    /* Badges */
    .badge {{
      display: inline-block;
      padding: 4px 12px;
      border-radius: 20px;
      font-size: 11px;
      font-weight: 700;
      border: 1px solid transparent;
    }}
    .badge-pass {{ background: rgba(16, 185, 129, 0.12); color: var(--green); border-color: rgba(16, 185, 129, 0.2); }}
    .badge-fail {{ background: rgba(239, 68, 68, 0.12); color: var(--red); border-color: rgba(239, 68, 68, 0.2); }}
    .badge-warn {{ background: rgba(245, 158, 11, 0.12); color: var(--warning); border-color: rgba(245, 158, 11, 0.2); }}
    .badge-pending {{ background: rgba(148, 163, 184, 0.12); color: var(--muted); border-color: rgba(148, 163, 184, 0.2); }}
    
    .btn-micro {{
      display: inline-block;
      padding: 4px 10px;
      border-radius: 6px;
      font-size: 11px;
      background: var(--surface2);
      color: var(--text);
      border: 1px solid var(--border);
    }}
    .btn-micro:hover {{ background: var(--accent-glow); border-color: var(--accent); }}
    
    .footer {{
      background: #02050b;
      border-top: 1px solid var(--border);
      color: var(--muted);
      text-align: center;
      padding: 32px;
      font-size: 13px;
    }}
  </style>
</head>
<body>

  <!-- HEADER -->
  <div class="header">
    <p style="text-transform: uppercase; letter-spacing: 2px; font-size:10px; font-weight:700; margin-bottom:8px; color:var(--accent);">Phase 7 — TraceVault</p>
    <h1>Traceability Matrix — <span>{design_name.upper()}</span></h1>
    <p>Verification trail mapping spec sections to functional requirements, generated test cases, and simulation coverage bins.</p>
  </div>

  <div class="container">
  
    <!-- CAVEATS -->
    <div class="caveat-box">
      <strong>Verification Trail & Database Disclosures:</strong>
      <p style="margin: 6px 0 0 0;">
        * Functional coverage numbers logged in this database trace back to the <strong>proxy hit-counter approximation</strong> inside the mock subscriber class, not real hardware covergroups.
        <br>
        * Simulation outcomes and testbench compilation checks were validated against <strong>uvm_mock.svh</strong>, not the full Accellera UVM package.
      </p>
    </div>

    <!-- HEATMAP -->
    <div class="section-title">Traceability Heatmap Grid</div>
    <div class="heatmap-grid">
      {heatmap_rows}
    </div>

    <!-- SECTION RATE -->
    <div class="section-title">Requirement Completion Rate</div>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Specification Section</th>
            <th>Functional Points</th>
            <th>Completion Progress</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {req_rows}
        </tbody>
      </table>
    </div>

    <!-- DETAILED MAPPING -->
    <div class="section-title">Functional Point to Test Mapping</div>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>FP ID</th>
            <th>Requirement Description</th>
            <th>Linked Spec Section</th>
            <th>Status / Coverage</th>
            <th>Satisfying Test Cases</th>
          </tr>
        </thead>
        <tbody>
          {mapping_rows}
        </tbody>
      </table>
    </div>

    <!-- TEST COMPLIANCE -->
    <div class="section-title">Test Case Compliance Ledger</div>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Test Name</th>
            <th>Sim Outcome</th>
            <th>Satisfied Requirements</th>
            <th>File Path</th>
          </tr>
        </thead>
        <tbody>
          {test_rows}
        </tbody>
      </table>
    </div>

  </div>

  <div class="footer">
    <strong>VeriGenX</strong> Autonomous Verification Platform — TraceVault Trail.
  </div>

</body>
</html>
"""
