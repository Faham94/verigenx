import os
import pytest
from VeriGenX.agents.tracevault.matrix_builder import MatrixBuilder
from VeriGenX.agents.tracevault.report_exporter import ReportExporter
from VeriGenX.agents.tracevault.db_manager import TraceabilityDBManager

def test_tracevault_e2e_uart():
    db_path = "output/test_traceability_e2e.db"
    report_path = "output/test_traceability_e2e_report.html"
    
    # Cleanup previous runs
    if os.path.exists(db_path):
        os.remove(db_path)
    if os.path.exists(report_path):
        os.remove(report_path)

    # 1. Build traceability matrix
    builder = MatrixBuilder(db_path)
    data = builder.build_matrix("uart")
    
    # Assert database populated
    assert os.path.exists(db_path)
    assert len(data["sections"]) > 0
    assert len(data["functional_points"]) > 0
    assert len(data["test_cases"]) > 0
    assert len(data["coverage_bins"]) > 0
    
    # Confirm spec sections count matches test plan sections
    db = TraceabilityDBManager(db_path)
    all_sections = db.get_all_traceability_data("uart")["sections"]
    section_names = [s["section_name"] for s in all_sections]
    assert "1. Signals" in section_names
    assert "3. FSM States" in section_names
    
    # 2. Export report
    exporter = ReportExporter(db_path)
    exporter.export_html("uart", report_path)
    
    # Assert report file generated
    assert os.path.exists(report_path)
    assert os.path.getsize(report_path) > 0
    
    # Read generated HTML and verify caveats are printed
    with open(report_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    assert "proxy hit-counter approximation" in html_content
    assert "uvm_mock.svh" in html_content
    assert "Traceability Heatmap Grid" in html_content

    # Cleanup files
    if os.path.exists(db_path):
        os.remove(db_path)
    if os.path.exists(report_path):
        os.remove(report_path)
