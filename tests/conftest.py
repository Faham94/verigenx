# VeriGenX Tests — conftest.py (pytest fixtures)
import pytest
import os
import json

SPEC_TEXT = """
UART Specification v1.0

1. Overview
The UART module implements serial communication at configurable baud rates.

2. Interface Signals
- clk: 1-bit input clock
- rst_n: 1-bit active-low reset
- tx_data: 8-bit input transmit data
- rx_data: 8-bit output received data

3. FSM States
The UART controller uses a 4-state FSM: IDLE, START, DATA, STOP

4. Register Map
- 0x00: baud_divisor (16-bit) - Sets baud rate divisor
- 0x04: control (8-bit) - Control register

5. Timing
- Clock period: 10ns
- Baud rate: configurable via baud_divisor
"""

@pytest.fixture
def uart_spec_text():
    """Raw UART specification text"""
    return SPEC_TEXT

@pytest.fixture
def uart_spec_file(tmp_path):
    """Temporary UART spec TXT file"""
    spec_file = tmp_path / "uart_spec.txt"
    spec_file.write_text(SPEC_TEXT, encoding="utf-8")
    return str(spec_file)

@pytest.fixture
def sample_test_plan():
    """A valid sample test plan dict"""
    return {
        "design_name": "uart",
        "version": "1.0",
        "generated_at": "2026-07-10T00:00:00",
        "signals": [
            {"name": "clk",     "width": 1, "direction": "input"},
            {"name": "rst_n",   "width": 1, "direction": "input"},
            {"name": "tx_data", "width": 8, "direction": "input"},
            {"name": "rx_data", "width": 8, "direction": "output"},
        ],
        "fsm_states": ["IDLE", "START", "DATA", "STOP"],
        "register_map": [
            {"address": "0x00", "name": "baud_divisor", "width": 16},
            {"address": "0x04", "name": "control",      "width": 8},
        ],
        "functional_points": [
            {"id": "FP_001", "description": "8-bit data transmission"},
            {"id": "FP_002", "description": "Baud rate configuration"},
        ]
    }

@pytest.fixture
def test_plan_file(tmp_path, sample_test_plan):
    """Temporary test plan JSON file"""
    plan_file = tmp_path / "uart_test_plan.json"
    plan_file.write_text(json.dumps(sample_test_plan, indent=2), encoding="utf-8")
    return str(plan_file)
