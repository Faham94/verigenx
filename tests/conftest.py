# VeriGenX Tests — conftest.py
# Shared fixtures for Phase 1 and Phase 2 tests
import pytest
import os
import json


# ==================================================================== #
#  UART spec text and file                                              #
# ==================================================================== #

UART_SPEC_TEXT = """
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
- Baud rate: 9600 baud
"""


@pytest.fixture
def uart_spec_text():
    return UART_SPEC_TEXT


@pytest.fixture
def uart_spec_file(tmp_path):
    f = tmp_path / "uart_spec.txt"
    f.write_text(UART_SPEC_TEXT, encoding="utf-8")
    return str(f)


# ==================================================================== #
#  Reference design test plan fixtures (Bug #7 + #8 fix)               #
#  All 5 designs: UART, SPI, I2C, AXI-Lite, FIFO                       #
# ==================================================================== #

def _make_plan(design, signals, fsm, registers, fps):
    return {
        "design_name":         design,
        "version":             "1.0",
        "generated_at":        "2026-07-11T00:00:00",
        "extraction_method":   "heuristic",
        "signals":             signals,
        "fsm_states":          fsm,
        "register_map":        registers,
        "timing_constraints":  {},
        "functional_points":   fps,
    }


@pytest.fixture
def uart_test_plan():
    return _make_plan(
        design="uart",
        signals=[
            {"name": "clk",     "width": 1, "direction": "input"},
            {"name": "rst_n",   "width": 1, "direction": "input"},
            {"name": "tx_data", "width": 8, "direction": "input"},
            {"name": "rx_data", "width": 8, "direction": "output"},
        ],
        fsm=["IDLE", "START", "DATA", "STOP"],
        registers=[
            {"address": "0x00", "name": "baud_divisor", "width": 16},
            {"address": "0x04", "name": "control",      "width": 8},
        ],
        fps=[
            {"id": "FP_001", "description": "8-bit data transmission"},
            {"id": "FP_002", "description": "Baud rate configuration"},
        ],
    )


@pytest.fixture
def spi_test_plan():
    return _make_plan(
        design="spi",
        signals=[
            {"name": "clk",   "width": 1, "direction": "input"},
            {"name": "rst_n", "width": 1, "direction": "input"},
            {"name": "mosi",  "width": 1, "direction": "input"},
            {"name": "miso",  "width": 1, "direction": "output"},
            {"name": "sclk",  "width": 1, "direction": "output"},
            {"name": "cs_n",  "width": 1, "direction": "output"},
        ],
        fsm=["IDLE", "ACTIVE", "DONE"],
        registers=[
            {"address": "0x00", "name": "spi_ctrl",  "width": 8},
            {"address": "0x04", "name": "spi_status", "width": 8},
            {"address": "0x08", "name": "spi_data",   "width": 8},
        ],
        fps=[
            {"id": "FP_001", "description": "Full-duplex SPI transfer"},
            {"id": "FP_002", "description": "Chip select toggling"},
            {"id": "FP_003", "description": "CPOL/CPHA mode selection"},
        ],
    )


@pytest.fixture
def i2c_test_plan():
    return _make_plan(
        design="i2c",
        signals=[
            {"name": "clk",   "width": 1, "direction": "input"},
            {"name": "rst_n", "width": 1, "direction": "input"},
            {"name": "scl",   "width": 1, "direction": "inout"},
            {"name": "sda",   "width": 1, "direction": "inout"},
        ],
        fsm=["IDLE", "START", "ADDR", "DATA", "ACK", "STOP"],
        registers=[
            {"address": "0x00", "name": "i2c_addr",   "width": 7},
            {"address": "0x04", "name": "i2c_ctrl",   "width": 8},
            {"address": "0x08", "name": "i2c_status",  "width": 8},
        ],
        fps=[
            {"id": "FP_001", "description": "Master write transaction"},
            {"id": "FP_002", "description": "Master read transaction"},
            {"id": "FP_003", "description": "ACK/NACK handling"},
        ],
    )


@pytest.fixture
def axi_lite_test_plan():
    return _make_plan(
        design="axi_lite",
        signals=[
            {"name": "aclk",    "width": 1,  "direction": "input"},
            {"name": "aresetn", "width": 1,  "direction": "input"},
            {"name": "awaddr",  "width": 32, "direction": "input"},
            {"name": "awvalid", "width": 1,  "direction": "input"},
            {"name": "awready", "width": 1,  "direction": "output"},
            {"name": "wdata",   "width": 32, "direction": "input"},
            {"name": "wstrb",   "width": 4,  "direction": "input"},
            {"name": "wvalid",  "width": 1,  "direction": "input"},
            {"name": "wready",  "width": 1,  "direction": "output"},
            {"name": "bresp",   "width": 2,  "direction": "output"},
            {"name": "bvalid",  "width": 1,  "direction": "output"},
            {"name": "bready",  "width": 1,  "direction": "input"},
            {"name": "araddr",  "width": 32, "direction": "input"},
            {"name": "arvalid", "width": 1,  "direction": "input"},
            {"name": "arready", "width": 1,  "direction": "output"},
            {"name": "rdata",   "width": 32, "direction": "output"},
            {"name": "rresp",   "width": 2,  "direction": "output"},
            {"name": "rvalid",  "width": 1,  "direction": "output"},
            {"name": "rready",  "width": 1,  "direction": "input"},
        ],
        fsm=["IDLE", "AW_PHASE", "W_PHASE", "B_PHASE", "AR_PHASE", "R_PHASE"],
        registers=[
            {"address": "0x000", "name": "ctrl_reg",   "width": 32},
            {"address": "0x004", "name": "status_reg", "width": 32},
        ],
        fps=[
            {"id": "FP_001", "description": "Write address channel handshake"},
            {"id": "FP_002", "description": "Write data channel handshake"},
            {"id": "FP_003", "description": "Write response channel"},
            {"id": "FP_004", "description": "Read address channel handshake"},
            {"id": "FP_005", "description": "Read data channel handshake"},
        ],
    )


@pytest.fixture
def fifo_test_plan():
    return _make_plan(
        design="fifo",
        signals=[
            {"name": "clk",      "width": 1,  "direction": "input"},
            {"name": "rst_n",    "width": 1,  "direction": "input"},
            {"name": "wr_en",    "width": 1,  "direction": "input"},
            {"name": "rd_en",    "width": 1,  "direction": "input"},
            {"name": "wr_data",  "width": 8,  "direction": "input"},
            {"name": "rd_data",  "width": 8,  "direction": "output"},
            {"name": "full",     "width": 1,  "direction": "output"},
            {"name": "empty",    "width": 1,  "direction": "output"},
        ],
        fsm=["EMPTY", "PARTIAL", "FULL"],
        registers=[],
        fps=[
            {"id": "FP_001", "description": "Write when not full"},
            {"id": "FP_002", "description": "Read when not empty"},
            {"id": "FP_003", "description": "Full flag assertion"},
            {"id": "FP_004", "description": "Empty flag assertion"},
        ],
    )


# Generic alias used by Phase 1 tests
@pytest.fixture
def sample_test_plan(uart_test_plan):
    return uart_test_plan


@pytest.fixture
def test_plan_file(tmp_path, uart_test_plan):
    p = tmp_path / "uart_test_plan.json"
    p.write_text(json.dumps(uart_test_plan, indent=2), encoding="utf-8")
    return str(p)


@pytest.fixture
def all_reference_plans(uart_test_plan, spi_test_plan, i2c_test_plan,
                        axi_lite_test_plan, fifo_test_plan):
    """All 5 reference designs as a list."""
    return [uart_test_plan, spi_test_plan, i2c_test_plan,
            axi_lite_test_plan, fifo_test_plan]
