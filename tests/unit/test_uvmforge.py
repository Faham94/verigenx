"""
Unit Tests — UVMForge Components (Phase 3)
Tests: UVMForgeGenerator, LLMFiller, UVMForgeRepair
"""
import os
import pytest
from unittest.mock import MagicMock, patch

from VeriGenX.agents.uvmforge.generator import UVMForgeGenerator
from VeriGenX.agents.uvmforge.llm_filler import LLMFiller
from VeriGenX.agents.uvmforge.repair import UVMForgeRepair


# ============================================================
# 1. UVMForgeGenerator Tests
# ============================================================

class TestUVMForgeGenerator:

    def test_generator_initialization(self):
        generator = UVMForgeGenerator()
        assert generator.state_bus is not None
        assert generator.llm_filler is not None
        assert generator.repair_helper is not None

    def test_find_clk_rst_names_default(self):
        generator = UVMForgeGenerator()
        signals = [
            {"name": "clk", "width": 1, "direction": "input"},
            {"name": "rst_n", "width": 1, "direction": "input"},
            {"name": "tx", "width": 8, "direction": "output"}
        ]
        clk, rst = generator._find_clk_rst_names(signals)
        assert clk == "clk"
        assert rst == "rst_n"

    def test_find_clk_rst_names_custom(self):
        generator = UVMForgeGenerator()
        signals = [
            {"name": "aclk", "width": 1, "direction": "input"},
            {"name": "aresetn", "width": 1, "direction": "input"},
            {"name": "data", "width": 32, "direction": "input"}
        ]
        clk, rst = generator._find_clk_rst_names(signals)
        assert clk == "aclk"
        assert rst == "aresetn"

    def test_find_clk_rst_names_fallbacks(self):
        generator = UVMForgeGenerator()
        signals = [
            {"name": "sys_clock", "width": 1, "direction": "input"},
            {"name": "sys_reset", "width": 1, "direction": "input"}
        ]
        clk, rst = generator._find_clk_rst_names(signals)
        assert clk == "sys_clock"
        assert rst == "sys_reset"

    @patch("VeriGenX.agents.uvmforge.generator.UVMForgeRepair.is_verilator_available", return_value=False)
    @patch("VeriGenX.agents.uvmforge.generator.LLMFiller.fill_placeholders")
    def test_generate_all_writes_all_files(self, mock_fill, mock_verilator, tmp_path, uart_test_plan):
        mock_fill.return_value = "// Mock code"
        
        # Build a temporary DAG
        dag = {
            "components": [
                "interface", "sequence_item", "sequence", "driver", "monitor",
                "agent", "scoreboard", "coverage", "env", "test_base", "test_directed", "top"
            ],
            "dependencies": {
                "interface": [],
                "sequence_item": [],
                "sequence": ["sequence_item"],
                "driver": ["sequence_item", "interface"],
                "monitor": ["interface"],
                "agent": ["driver", "monitor", "sequence"],
                "scoreboard": ["sequence_item"],
                "coverage": ["sequence_item"],
                "env": ["agent", "scoreboard", "coverage"],
                "test_base": ["env", "sequence"],
                "test_directed": ["test_base"],
                "top": ["test_directed", "interface", "env"]
            },
            "design_name": "uart",
            "signals": uart_test_plan["signals"],
            "component_filenames": {
                c: f"uart_{c}.sv" for c in [
                    "interface", "sequence_item", "sequence", "driver", "monitor",
                    "agent", "scoreboard", "coverage", "env", "test_base", "test_directed", "top"
                ]
            }
        }
        
        with patch("VeriGenX.agents.uvmforge.generator.GENERATED_UVM_DIR", str(tmp_path)):
            generator = UVMForgeGenerator()
            filepaths = generator.generate_all(uart_test_plan, dag)
            
            assert len(filepaths) == 12
            for path in filepaths:
                assert os.path.exists(path)
                with open(path, "r") as f:
                    content = f.read()
                    assert content == "// Mock code"


# ============================================================
# 2. LLMFiller Tests
# ============================================================

class TestLLMFiller:

    def test_filler_initialization(self):
        filler = LLMFiller()
        assert filler.client is not None

    def test_fill_placeholders_heuristic_fallback(self):
        filler = LLMFiller()
        # Mock client unavailable
        filler.client.is_available = MagicMock(return_value=False)
        
        template = """
// {% llm_fill "interface_assertions" %}
// {% endllm_fill %}
        """
        test_plan = {"design_name": "uart", "signals": []}
        result = filler.fill_placeholders("interface", template, test_plan)
        assert "TODO: Add SystemVerilog assertions" in result

    def test_get_heuristic_fill_transaction_fields(self):
        filler = LLMFiller()
        test_plan = {
            "design_name": "uart",
            "signals": [
                {"name": "clk", "width": 1, "direction": "input"},
                {"name": "tx_data", "width": 8, "direction": "input"},
                {"name": "rx_data", "width": 8, "direction": "output"}
            ]
        }
        fill = filler._get_heuristic_fill("uart", "seq_item", "transaction_fields", test_plan)
        assert "tx_data" in fill
        assert "rx_data" in fill
        assert "[7:0]" in fill
        assert "clk" not in fill

    def test_get_heuristic_fill_field_macros(self):
        filler = LLMFiller()
        test_plan = {
            "design_name": "uart",
            "signals": [
                {"name": "tx_data", "width": 8, "direction": "input"}
            ]
        }
        fill = filler._get_heuristic_fill("uart", "seq_item", "field_macros", test_plan)
        assert "`uvm_field_int(tx_data, UVM_ALL_ON)" in fill

    def test_get_heuristic_fill_sequence_body(self):
        filler = LLMFiller()
        fill = filler._get_heuristic_fill("uart", "sequence", "sequence_body", {})
        assert "randomize()" in fill
        assert "start_item" in fill
        assert "finish_item" in fill


# ============================================================
# 3. UVMForgeRepair Tests
# ============================================================

class TestUVMForgeRepair:

    def test_classify_error_syntax_error(self):
        repair = UVMForgeRepair()
        err = "%Error: uart_driver.sv:12:34: syntax error, unexpected IDENTIFIER, expecting SEMICOLON"
        assert repair.classify_error(err) == "syntax_error"

    def test_classify_error_undeclared_identifier(self):
        repair = UVMForgeRepair()
        err = "%Error: uart_monitor.sv:45:12: Member not found: 'ap' in 'uart_monitor'"
        assert repair.classify_error(err) == "undeclared_identifier"

    def test_classify_error_type_mismatch(self):
        repair = UVMForgeRepair()
        err = "%Error: uart_scoreboard.sv:56:8: type mismatch: cannot assign bit[7:0] to string"
        assert repair.classify_error(err) == "type_mismatch"

    def test_classify_error_port_mismatch(self):
        repair = UVMForgeRepair()
        err = "%Error: top.sv:89:12: width mismatch on port connection 'tx_data'"
        assert repair.classify_error(err) == "port_mismatch"

    def test_classify_error_other(self):
        repair = UVMForgeRepair()
        assert repair.classify_error("some unknown warning message") == "other"
        assert repair.classify_error("") == "unknown"

    @patch("VeriGenX.agents.uvmforge.repair.UVMForgeRepair.is_verilator_available", return_value=False)
    def test_repair_file_when_verilator_not_available(self, mock_verilator, tmp_path):
        repair = UVMForgeRepair()
        filepath = tmp_path / "test.sv"
        filepath.write_text("module top; endmodule")
        
        # When verilator is not available, it should compile cleanly immediately and return True without modifying the file.
        success = repair.repair_file(str(filepath), "top", {})
        assert success is True
        assert filepath.read_text() == "module top; endmodule"
