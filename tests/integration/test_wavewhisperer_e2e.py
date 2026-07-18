import os
import pytest
from VeriGenX.orchestrator import Orchestrator
from VeriGenX.state_bus import get_state_bus, PipelineState
from VeriGenX.agents.simrunner import SimRunner
from VeriGenX.agents.wavewhisperer import WaveWhisperer

FIXTURE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "fixtures"))

class TestWaveWhispererE2E:
    def test_wavewhisperer_analysis_e2e(self, tmp_path):
        """
        Runs the full e2e flow:
        1. Generates UVM files for UART.
        2. Executes a real simulation to dump a VCD trace.
        3. Invokes WaveWhisperer to parse the VCD and generate the HTML report.
        """
        spec_path = os.path.join(FIXTURE_DIR, "uart", "uart_spec.txt")
        if not os.path.exists(spec_path):
            pytest.fail(f"Required spec fixture missing at: {spec_path}")

        # 1. Run pipeline up to Phase 4
        orchestrator = Orchestrator()
        state_bus = get_state_bus()
        state_bus.state = PipelineState()

        # Generate files inside tmp_path
        orchestrator.run_pipeline(spec_path, output_dir=str(tmp_path))
        
        state = state_bus.get_state()
        assert state.test_plan is not None
        assert len(state.generated_files) > 0

        # We must use absolute path for base_run_dir so Verilator's +VCD_FILE opens successfully
        absolute_run_dir = os.path.abspath(os.path.join(tmp_path, "sim_run"))

        # 2. Run simulation using SimRunner
        runner = SimRunner()
        results = runner.run_simulations(
            design_name="uart",
            test_plan=state.test_plan,
            uvm_files=list(state.generated_files),
            base_run_dir=absolute_run_dir
        )

        assert results["compiled"] is True
        
        # Verify at least one test ran and dumped VCD
        test_base_res = results["tests"].get("uart_test_base")
        assert test_base_res is not None
        assert test_base_res["status"] == "passed"
        
        vcd_path = test_base_res.get("vcd_path")
        assert vcd_path != ""
        assert os.path.exists(vcd_path)

        # 3. Run WaveWhisperer Analyzer
        whisperer = WaveWhisperer("uart", state.test_plan)
        report_html_path = os.path.join(tmp_path, "WAVEFORM_ANALYSIS.html")
        
        anomalies = whisperer.analyze_vcd(vcd_path, report_html_path)
        
        # 4. Verify output report is generated
        assert os.path.exists(report_html_path)
        assert os.path.getsize(report_html_path) > 1000  # HTML contains Plotly header

        # Verify that we generated some explanations or summary
        with open(report_html_path, "r", encoding="utf-8") as f:
            html_text = f.read()
            assert "VeriGenX WaveWhisperer" in html_text
            assert "Plotly" in html_text
