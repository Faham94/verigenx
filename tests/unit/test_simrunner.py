import os
import pytest
from unittest.mock import patch, MagicMock
from VeriGenX.agents.simrunner.compiler import SimCompiler
from VeriGenX.agents.simrunner.executor import SimExecutor
from VeriGenX.agents.simrunner.coverage_parser import SimCoverageParser
from VeriGenX.agents.simrunner.log_parser import SimLogParser

class TestSimLogParser:
    def test_log_parsing_uvm_severities(self):
        parser = SimLogParser()
        stdout = """
[UVM_INFO] @ 0 | TOP | Starting simulation
[UVM_WARNING] @ 100 | MON | Unknown packet received
[UVM_ERROR] @ 200 | SB_MISMATCH | Mismatch found!
[UVM_FATAL] @ 300 | DRV | Driver interface hung
"""
        stderr = "%Error: Some verilator syntax error"
        res = parser.parse(stdout, stderr)

        assert len(res["info"]) == 1
        assert len(res["warnings"]) == 1
        assert len(res["errors"]) == 2 # 1 UVM_ERROR + 1 %Error
        assert len(res["fatals"]) == 1
        assert res["summary"]["status"] == "failed"
        assert res["summary"]["total_errors"] == 3

    def test_log_parsing_clean_pass(self):
        parser = SimLogParser()
        stdout = """
[UVM_INFO] @ 0 | TOP | Starting simulation
[UVM_INFO] @ 10 | SB_MATCH | Transaction matched
[UVM_INFO] @ 100 | TOP | Simulation finished successfully
[UVM_INFO] Simulation PASSED.
"""
        res = parser.parse(stdout, "")
        assert res["summary"]["status"] == "passed"
        assert res["summary"]["total_errors"] == 0

class TestSimCoverageParser:
    def test_parse_coverage_dat(self, tmp_path):
        cov_file = tmp_path / "coverage.dat"
        cov_file.write_text("C '\x01f\x02uart_driver.sv\x01l\x0212\x01n\x025\x01t\x02line\x01page\x02v_line/uart_driver' 10\n"
                            "C '\x01f\x02uart_coverage.sv\x01l\x0214\x01n\x025\x01t\x02branch\x01page\x02v_branch/uart_coverage' 1\n"
                            "C '\x01f\x02uart_coverage.sv\x01l\x0220\x01n\x025\x01t\x02branch\x01page\x02v_branch/uart_coverage' 0\n"
                            "C '\x01f\x02uart_coverage.sv\x01l\x0222\x01n\x025\x01t\x02toggle\x01page\x02v_toggle/uart_coverage' 1\n")
        parser = SimCoverageParser()
        res = parser.parse(str(cov_file), "")

        assert res["total_points"] == 4
        assert res["covered_points"] == 3
        assert res["line_coverage"] == 100.0
        assert res["branch_coverage"] == 50.0
        assert res["toggle_coverage"] == 100.0

    def test_parse_stdout_coverage(self):
        parser = SimCoverageParser()
        stdout = "Overall simulation coverage: 92.5%"
        res = parser.parse("non_existent_file.dat", stdout)
        assert res["functional_coverage"] == 92.5

    def test_parse_missing_coverage_defaults_to_zero(self):
        parser = SimCoverageParser()
        res = parser.parse("non_existent_file.dat", "no coverage info in log")
        assert res["line_coverage"] == 0.0
        assert res["branch_coverage"] == 0.0
        assert res["functional_coverage"] == 0.0

class TestSimCompiler:
    def test_generate_sim_main(self, tmp_path):
        compiler = SimCompiler()
        cpp_file = tmp_path / "sim_main.cpp"
        compiler.generate_sim_main(str(cpp_file))
        assert cpp_file.exists()
        content = cpp_file.read_text()
        assert "int main" in content
        assert "Vtop.h" in content

    def test_generate_dut_wrapper(self, tmp_path):
        compiler = SimCompiler()
        wrapper_file = tmp_path / "uart_wrapper.sv"
        signals = [
            {"name": "clk", "width": 1, "direction": "input"},
            {"name": "tx_data", "width": 8, "direction": "input"},
            {"name": "rx_data", "width": 8, "direction": "output"}
        ]
        compiler.generate_dut_wrapper("uart", signals, str(wrapper_file))
        assert wrapper_file.exists()
        content = wrapper_file.read_text()
        assert "module uart" in content
        assert "uart_dut inst" in content
        assert "input logic  clk" in content

class TestSimExecutor:
    @patch("subprocess.run")
    def test_execute_success(self, mock_run, tmp_path):
        mock_run.return_value = MagicMock(returncode=0, stdout="[UVM_INFO] Simulation PASSED.", stderr="")
        bin_file = tmp_path / "Vuart_sim.exe"
        bin_file.touch()

        executor = SimExecutor()
        res = executor.execute(str(bin_file), "uart_test_directed", str(tmp_path))

        assert res["success"] is True
        assert res["returncode"] == 0
        assert "Simulation PASSED" in res["stdout"]
