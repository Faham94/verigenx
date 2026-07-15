import os
import json
import pytest
from unittest.mock import patch, MagicMock

from VeriGenX.agents.coverhunter.gap_analyzer import GapAnalyzer
from VeriGenX.agents.coverhunter.test_generator import TestGenerator
from VeriGenX.agents.coverhunter.closure_loop import ClosureLoop

class TestGapAnalyzer:
    def test_analyze_gaps_line_and_branch(self, tmp_path):
        run_dir = tmp_path / "sim_run"
        run_dir.mkdir()
        
        # Write mock coverage.dat containing some uncovered lines and branches
        cov_file = run_dir / "coverage.dat"
        cov_file.write_text(
            "C '\x01f\x02uart_driver.sv\x01l\x0212\x01t\x02line' 0\n"
            "C '\x01f\x02uart_monitor.sv\x01l\x0214\x01t\x02branch' 0\n"
            "C '\x01f\x02uart_scoreboard.sv\x01l\x0220\x01t\x02line' 1\n"
        )

        test_plan = {"fsm_states": []}
        sim_results = {"tests": {}}

        analyzer = GapAnalyzer()
        gaps = analyzer.analyze_gaps(test_plan, sim_results, str(run_dir))

        assert len(gaps) == 2
        assert gaps[0]["type"] == "uncovered branch"
        assert gaps[0]["file"] == "uart_monitor.sv"
        assert gaps[1]["type"] == "uncovered line"
        assert gaps[1]["file"] == "uart_driver.sv"

    def test_analyze_gaps_functional(self, tmp_path):
        run_dir = tmp_path / "sim_run"
        run_dir.mkdir()

        # Write mock functional_coverage_report.json
        func_file = run_dir / "functional_coverage_report.json"
        func_data = {
            "overall_functional_coverage": 50.0,
            "points": {
                "FP_001": {"description": "Data transmission", "hit_count": 0},
                "FP_002": {"description": "Reset", "hit_count": 5}
            }
        }
        func_file.write_text(json.dumps(func_data))

        test_plan = {"fsm_states": []}
        sim_results = {"tests": {}}

        analyzer = GapAnalyzer()
        gaps = analyzer.analyze_gaps(test_plan, sim_results, str(run_dir))

        assert len(gaps) == 1
        assert gaps[0]["type"] == "uncovered functional bin"
        assert gaps[0]["name"] == "FP_001"

    def test_analyze_gaps_fsm(self, tmp_path):
        run_dir = tmp_path / "sim_run"
        run_dir.mkdir()

        test_plan = {"fsm_states": ["IDLE", "START", "DATA", "STOP"]}
        sim_results = {
            "tests": {
                "uart_test_base": {"stdout": "[UVM_INFO] IDLE state hit\n[UVM_INFO] START state hit"}
            }
        }

        analyzer = GapAnalyzer()
        gaps = analyzer.analyze_gaps(test_plan, sim_results, str(run_dir))

        # IDLE and START should be considered covered because they are in stdout
        # DATA and STOP should be uncovered FSM states
        uncovered_states = [g["name"] for g in gaps if g["type"] == "uncovered FSM state"]
        assert "DATA" in uncovered_states
        assert "STOP" in uncovered_states
        assert "IDLE" not in uncovered_states
        assert "START" not in uncovered_states


class TestTestGenerator:
    @patch("VeriGenX.agents.coverhunter.test_generator.get_ollama_client")
    def test_generate_targeted_test(self, mock_get_client, tmp_path):
        run_dir = tmp_path / "sim_run"
        run_dir.mkdir()

        # Mock OllamaClient response
        mock_client = MagicMock()
        mock_client.generate.return_value = """
```systemverilog
class uart_test_directed_FP_001 extends uart_test_base;
    // test body
endclass
```
"""
        mock_get_client.return_value = mock_client

        generator = TestGenerator()
        # Mock lint_check to bypass Verilator
        with patch.object(generator, "lint_check", return_value=True):
            test_plan = {"signals": [], "functional_points": []}
            gap = {"type": "uncovered functional bin", "name": "FP_001"}
            code = generator.generate_targeted_test("uart", test_plan, gap, [], str(run_dir))
            
            assert "class uart_test_directed_FP_001" in code
            assert "```" not in code


class TestClosureLoop:
    @patch("VeriGenX.agents.coverhunter.closure_loop.SimRunner")
    @patch("VeriGenX.agents.coverhunter.closure_loop.TestGenerator")
    def test_closure_loop_success(self, mock_test_gen_cls, mock_sim_runner_cls, tmp_path):
        base_dir = tmp_path / "run"
        base_dir.mkdir()

        # Mock SimRunner
        mock_runner = MagicMock()
        # First run has 60% coverage, second run has 90% coverage
        mock_runner.run_simulations.side_effect = [
            {
                "compiled": True,
                "status": "passed",
                "coverage": {
                    "line_coverage": 70.0,
                    "branch_coverage": 60.0,
                    "toggle_coverage": 50.0,
                    "functional_coverage": 60.0
                }
            },
            {
                "compiled": True,
                "status": "passed",
                "coverage": {
                    "line_coverage": 90.0,
                    "branch_coverage": 90.0,
                    "toggle_coverage": 90.0,
                    "functional_coverage": 90.0
                }
            }
        ]
        mock_sim_runner_cls.return_value = mock_runner

        # Mock TestGenerator
        mock_generator = MagicMock()
        mock_generator.generate_targeted_test.return_value = "class new_test extends uvm_test; endclass"
        mock_test_gen_cls.return_value = mock_generator

        # Mock GapAnalyzer to return one gap in first iteration
        with patch("VeriGenX.agents.coverhunter.closure_loop.GapAnalyzer") as mock_gap_analyzer_cls:
            mock_analyzer = MagicMock()
            mock_analyzer.analyze_gaps.side_effect = [
                [{"type": "uncovered functional bin", "name": "FP_001"}],
                []
            ]
            mock_gap_analyzer_cls.return_value = mock_analyzer

            loop = ClosureLoop(max_iterations=5, convergence_threshold=0.1)
            results = loop.run_closure_loop("uart", {}, [], str(base_dir))

            assert results["coverage"]["functional_coverage"] == 90.0
            assert mock_runner.run_simulations.call_count == 2

            # Check report was written and has correct values
            report_path = base_dir / "coverhunter_report.json"
            assert report_path.exists()
            with open(report_path, "r", encoding="utf-8") as f:
                report_data = json.load(f)
            assert report_data["design_name"] == "uart"
            assert "baseline_coverage" in report_data
            assert len(report_data["iterations"]) == 2
            assert report_data["iterations"][0]["iteration"] == 1
            assert report_data["iterations"][0]["targeted_gap"]["name"] == "FP_001"
            assert report_data["iterations"][1]["targeted_gap"] is None
            assert report_data["rollback_info"]["occurred"] is False
            assert report_data["final_coverage"]["functional_coverage"] == 90.0
