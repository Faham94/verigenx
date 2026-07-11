"""
Test Plan Generator
Converts extracted knowledge into a structured JSON test plan.

Fixes applied:
  - Bug #2: Extractor now called.
  - Bug #3: Support protocol handshake rules and firmware obligations.
  - Bug #4: Dynamic protocol-specific fallbacks (UART, SPI, I2C, AXI, FIFO)
            to prevent UART defaults leaking into other designs.
  - Heuristics: Enhanced register map extraction to get width, access, and reset_value.
"""
import json
import os
import re
from datetime import datetime
from typing import Dict, List, Optional

from VeriGenX.config import TEST_PLANS_DIR


# ==================================================================== #
#  Design-Specific Defaults (Bug #4)                                   #
# ==================================================================== #

DESIGN_DEFAULTS: Dict[str, Dict] = {
    "uart": {
        "signals": [
            {"name": "clk",     "width": 1, "direction": "input"},
            {"name": "rst_n",   "width": 1, "direction": "input"},
            {"name": "tx_data", "width": 8, "direction": "input"},
            {"name": "rx_data", "width": 8, "direction": "output"},
        ],
        "fsm_states": ["IDLE", "START", "DATA", "STOP"],
        "register_map": [
            {"address": "0x00", "name": "baud_divisor", "width": 16, "access": "RW", "reset_value": "0x0001"},
            {"address": "0x04", "name": "control",      "width": 8,  "access": "RW", "reset_value": "0x00"},
        ],
        "functional_points": [
            {"id": "FP_001", "description": "8-bit data transmission"},
            {"id": "FP_002", "description": "Baud rate configuration"},
        ],
        "protocol_handshake_rules": [
            "Start bit (low) initiates transmission",
            "Stop bit (high) finalizes transmission",
        ],
        "firmware_programming_model": [
            "Write the baud rate divisor to baud_divisor register",
            "Configure character length, parity, and stop bits in control register",
        ],
    },
    "spi": {
        "signals": [
            {"name": "clk",   "width": 1, "direction": "input"},
            {"name": "rst_n", "width": 1, "direction": "input"},
            {"name": "mosi",  "width": 1, "direction": "input"},
            {"name": "miso",  "width": 1, "direction": "output"},
            {"name": "sclk",  "width": 1, "direction": "output"},
            {"name": "cs_n",  "width": 1, "direction": "output"},
        ],
        "fsm_states": ["IDLE", "ACTIVE", "DONE"],
        "register_map": [
            {"address": "0x00", "name": "spi_ctrl",   "width": 8, "access": "RW", "reset_value": "0x00"},
            {"address": "0x04", "name": "spi_status", "width": 8, "access": "RO", "reset_value": "0x02"},
            {"address": "0x08", "name": "spi_data",   "width": 8, "access": "RW", "reset_value": "0x00"},
        ],
        "functional_points": [
            {"id": "FP_001", "description": "Full-duplex SPI transfer"},
            {"id": "FP_002", "description": "Chip select toggling"},
        ],
        "protocol_handshake_rules": [
            "CS_N asserted low initiates clock and data transfer",
            "SCLK toggles on active edges determined by CPOL/CPHA",
        ],
        "firmware_programming_model": [
            "Write configuration options to spi_ctrl",
            "Write transmit byte to spi_data",
            "Poll spi_status until transfer is complete",
        ],
    },
    "i2c": {
        "signals": [
            {"name": "clk",   "width": 1, "direction": "input"},
            {"name": "rst_n", "width": 1, "direction": "input"},
            {"name": "scl",   "width": 1, "direction": "inout"},
            {"name": "sda",   "width": 1, "direction": "inout"},
        ],
        "fsm_states": ["IDLE", "START", "ADDR", "DATA", "ACK", "STOP"],
        "register_map": [
            {"address": "0x00", "name": "i2c_addr",   "width": 7, "access": "RW", "reset_value": "0x00"},
            {"address": "0x04", "name": "i2c_ctrl",   "width": 8, "access": "RW", "reset_value": "0x00"},
            {"address": "0x08", "name": "i2c_status", "width": 8, "access": "RO", "reset_value": "0x00"},
        ],
        "functional_points": [
            {"id": "FP_001", "description": "Start and Stop condition generation"},
            {"id": "FP_002", "description": "ACK/NACK verification"},
        ],
        "protocol_handshake_rules": [
            "Start condition: SDA falling while SCLK is high",
            "Stop condition: SDA rising while SCLK is high",
            "ACK check: receiver pulls SDA low on 9th clock",
        ],
        "firmware_programming_model": [
            "Set target address in i2c_addr",
            "Configure command in i2c_ctrl and initiate START",
            "Poll i2c_status for transfer complete or arbitration loss",
        ],
    },
    "axi": {
        "signals": [
            {"name": "aclk",    "width": 1,  "direction": "input"},
            {"name": "aresetn", "width": 1,  "direction": "input"},
            {"name": "awaddr",  "width": 32, "direction": "input"},
            {"name": "awvalid", "width": 1,  "direction": "input"},
            {"name": "awready", "width": 1,  "direction": "output"},
            {"name": "wdata",   "width": 32, "direction": "input"},
            {"name": "wvalid",  "width": 1,  "direction": "input"},
            {"name": "wready",  "width": 1,  "direction": "output"},
            {"name": "bresp",   "width": 2,  "direction": "output"},
            {"name": "bvalid",  "width": 1,  "direction": "output"},
            {"name": "bready",  "width": 1,  "direction": "input"},
        ],
        "fsm_states": ["IDLE", "AW_PHASE", "W_PHASE", "B_PHASE"],
        "register_map": [
            {"address": "0x000", "name": "ctrl_reg",   "width": 32, "access": "RW", "reset_value": "0x00000000"},
            {"address": "0x004", "name": "status_reg", "width": 32, "access": "RO", "reset_value": "0x00000002"},
        ],
        "functional_points": [
            {"id": "FP_001", "description": "Write address channel handshake"},
            {"id": "FP_002", "description": "Write data channel handshake"},
        ],
        "protocol_handshake_rules": [
            "Valid/Ready handshake: transfer occurs only when both VALID and READY are asserted",
            "Write response: BVALID must be held until master asserts BREADY",
        ],
        "firmware_programming_model": [
            "Issue AXI write request to target base address",
            "Read status_reg to verify completion",
        ],
    },
    "fifo": {
        "signals": [
            {"name": "clk",      "width": 1,  "direction": "input"},
            {"name": "rst_n",    "width": 1,  "direction": "input"},
            {"name": "wr_en",    "width": 1,  "direction": "input"},
            {"name": "rd_en",    "width": 1,  "direction": "input"},
            {"name": "wr_data",  "width": 8,  "direction": "input"},
            {"name": "rd_data",  "width": 8,  "direction": "output"},
            {"name": "full",     "width": 1,  "direction": "output"},
            {"name": "empty",    "width": 1,  "direction": "output"},
        ],
        "fsm_states": ["EMPTY", "PARTIAL", "FULL"],
        "register_map": [],
        "functional_points": [
            {"id": "FP_001", "description": "Write when not full"},
            {"id": "FP_002", "description": "Read when not empty"},
        ],
        "protocol_handshake_rules": [
            "Full assertion prevents write acknowledgment",
            "Empty assertion prevents read data propagation",
        ],
        "firmware_programming_model": [
            "Assert rst_n to clear internal buffers",
            "Check empty flag before reading rd_data",
        ],
    }
}


class TestPlanGenerator:

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    def generate(self, text: str, design_name: Optional[str] = None) -> Dict:
        """
        Generate a structured JSON test plan from spec text.

        Features:
          1. Try LLM-based extraction via Extractor (including handshake & firmware).
          2. Fall back to regex heuristics when LLM is offline.
          3. Fill any missing fields from protocol-specific defaults (preventing UART leak).
        """
        # Infer design name
        inferred_name = design_name or self._infer_design_name(text)
        default_key   = "axi" if "axi" in inferred_name else inferred_name
        proto_defaults = DESIGN_DEFAULTS.get(default_key, DESIGN_DEFAULTS["uart"])

        # --- Attempt LLM extraction ---
        extracted = {}
        llm_available = False
        try:
            from VeriGenX.agents.specmind.extractor import Extractor
            extractor     = Extractor()
            llm_available = extractor.client.is_available()
            if llm_available:
                extracted = extractor.extract_all(text)
        except Exception as e:
            print(f"  [Warning] LLM extraction failed: {e}")

        # --- Fallback/Heuristics ---
        signals    = extracted.get("signals")     or self._heuristic_signals(text)
        fsm        = extracted.get("fsm_states")  or self._heuristic_fsm(text)
        registers  = extracted.get("register_map") or self._heuristic_registers(text)
        timing     = extracted.get("timing_constraints") or self._heuristic_timing(text)
        func_pts   = extracted.get("functional_points") or self._heuristic_functional_points(text)
        handshakes = extracted.get("protocol_handshake_rules") or self._heuristic_handshake_rules(text)
        firmware   = extracted.get("firmware_programming_model") or self._heuristic_firmware_model(text)

        # --- Design-Specific defaults as last resort (Bug #4 fix) ---
        signals    = signals    or proto_defaults["signals"]
        fsm        = fsm        or proto_defaults["fsm_states"]
        registers  = registers  or proto_defaults["register_map"]
        func_pts   = func_pts   or proto_defaults["functional_points"]
        handshakes = handshakes or proto_defaults["protocol_handshake_rules"]
        firmware   = firmware   or proto_defaults["firmware_programming_model"]

        plan = {
            "design_name":                inferred_name,
            "version":                    "1.0",
            "generated_at":               datetime.now().isoformat(),
            "extraction_method":          "llm" if llm_available else "heuristic",
            "signals":                    signals,
            "fsm_states":                 fsm,
            "register_map":               registers,
            "timing_constraints":         timing,
            "functional_points":          func_pts,
            "protocol_handshake_rules":   handshakes,
            "firmware_programming_model": firmware,
        }

        if llm_available and extracted.get("confidence"):
            plan["confidence"] = extracted["confidence"]

        return plan

    def save(self, plan: Dict, filename: str = "uart_test_plan.json") -> str:
        os.makedirs(TEST_PLANS_DIR, exist_ok=True)
        filepath = os.path.join(TEST_PLANS_DIR, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(plan, f, indent=2)
        print(f"  Test plan saved to: {filepath}")
        return filepath

    # ------------------------------------------------------------------ #
    #  Design name inference                                               #
    # ------------------------------------------------------------------ #

    def _infer_design_name(self, text: str) -> str:
        text_lower = text.lower()
        for name in ["uart", "spi", "i2c", "axi_lite", "axi-lite", "axi", "fifo", "apb", "ahb",
                     "pcie", "usb", "ethernet", "can"]:
            if name in text_lower:
                if "axi" in name and "lite" in name:
                    return "axi_lite"
                return name
        return "design"

    # ------------------------------------------------------------------ #
    #  Regex heuristic extractors                                          #
    # ------------------------------------------------------------------ #

    def _heuristic_signals(self, text: str) -> List[Dict]:
        signals = []
        patterns = [
            r"\b(\w+)\s*:\s*(\d+)[\s-]*bit\s*(input|output|inout)",
            r"\b(input|output|inout)\s+(?:\[(\d+):\d+\]\s+)?(\w+)",
            r"-\s+(\w+)\s*:\s*(\d+)[\s-]*bit\s*(input|output|inout)",
        ]
        seen = set()
        for pat in patterns:
            for m in re.finditer(pat, text, re.IGNORECASE):
                groups = m.groups()
                if len(groups) == 3 and groups[0].lower() in ("input", "output", "inout"):
                    direction, width_str, name = groups
                    width = int(width_str) + 1 if width_str else 1
                else:
                    name, width_str, direction = groups[0], groups[1], groups[2]
                    width = int(width_str) if width_str and width_str.isdigit() else 1

                name = name.strip()
                if name.lower() in seen or len(name) < 2:
                    continue
                seen.add(name.lower())
                signals.append({
                    "name":      name,
                    "width":     int(width),
                    "direction": direction.lower(),
                })
        return signals

    def _heuristic_fsm(self, text: str) -> List[str]:
        states = []
        for m in re.finditer(r"\b([A-Z][A-Z0-9_]{1,})\b", text):
            word = m.group(1)
            if word not in states and len(word) >= 2:
                states.append(word)
        fsm_keywords = {"IDLE", "START", "STOP", "DATA", "WAIT", "SEND",
                        "RECEIVE", "ACK", "NACK", "RESET", "INIT", "DONE",
                        "TX", "RX", "ACTIVE", "PAUSE", "ERROR", "SETUP"}
        filtered = [s for s in states if s in fsm_keywords]
        return filtered if filtered else states[:6]

    def _heuristic_registers(self, text: str) -> List[Dict]:
        """
        Extract registers via hex address patterns.
        Enhanced to capture width, access, and reset_value from context.
        """
        registers = []
        seen = set()
        lines = text.split('\n')
        for line in lines:
            m = re.search(r"(0x[0-9A-Fa-f]{2,8})\s*[:=]?\s*(\w+)", line)
            if m:
                addr, name = m.group(1), m.group(2)
                if name.lower() in seen or len(name) < 2:
                    continue
                seen.add(name.lower())

                # Check width
                width = 8
                w_match = re.search(r"\(?(\d+)[\s-]*bit\)?|\b(?:width|size)\b\s*[:=]?\s*(\d+)", line, re.I)
                if w_match:
                    width = int(w_match.group(1) or w_match.group(2))

                # Check access (RW, RO, WO, RC)
                access = "RW"
                acc_match = re.search(r"\b(RW|RO|WO|RC|R/W|R/O|W/O)\b", line, re.I)
                if acc_match:
                    access = acc_match.group(1).upper().replace("/", "")

                # Check reset_value
                reset_val = "0x00"
                rst_match = re.search(r"\breset\b\s*(?:value)?\s*[:=]?\s*(0x[0-9A-Fa-f]+|\d+)", line, re.I)
                if rst_match:
                    val = rst_match.group(1)
                    if val.startswith("0x"):
                        reset_val = val.upper()
                    else:
                        try:
                            reset_val = f"0x{int(val):02X}"
                        except ValueError:
                            pass

                registers.append({
                    "address":     addr.upper(),
                    "name":        name,
                    "width":       width,
                    "access":      access,
                    "reset_value": reset_val
                })
        return registers

    def _heuristic_timing(self, text: str) -> Dict:
        timing = {}
        ns_match  = re.search(r"(\d+(?:\.\d+)?)\s*ns\s+(?:clock|period|cycle)", text, re.I)
        mhz_match = re.search(r"(\d+(?:\.\d+)?)\s*[Mm][Hh][Zz]", text)
        baud_match = re.search(r"(\d+)\s*(?:baud|bps)", text, re.I)
        if ns_match:
            timing["clock_period_ns"] = float(ns_match.group(1))
        if mhz_match:
            timing["max_frequency_mhz"] = float(mhz_match.group(1))
        if baud_match:
            timing["baud_rate"] = int(baud_match.group(1))
        return timing

    def _heuristic_functional_points(self, text: str) -> List[Dict]:
        fps = []
        if re.search(r"\btx\b|\btransmit\b|\bsend\b", text, re.I):
            fps.append({"id": "FP_001", "description": "Data transmission functionality"})
        if re.search(r"\brx\b|\breceive\b|\brecv\b", text, re.I):
            fps.append({"id": "FP_002", "description": "Data reception functionality"})
        if re.search(r"\bbaud\b|\brate\b", text, re.I):
            fps.append({"id": "FP_003", "description": "Baud rate configuration"})
        if re.search(r"\bpariti\b|\bparity\b", text, re.I):
            fps.append({"id": "FP_004", "description": "Parity error detection"})
        if re.search(r"\breset\b|\brst\b", text, re.I):
            fps.append({"id": "FP_005", "description": "Reset and initialisation"})
        return fps

    def _heuristic_handshake_rules(self, text: str) -> List[str]:
        """Extract protocol handshake rules via keyword search."""
        rules = []
        lines = text.split('\n')
        for line in lines:
            if any(k in line.lower() for k in ["handshake", "request", "ack", "valid", "ready", "assert", "deassert"]):
                if len(line.strip()) > 10:
                    rules.append(line.strip())
        return rules[:5]

    def _heuristic_firmware_model(self, text: str) -> List[str]:
        """Extract firmware programming obligations via configuration/initialization patterns."""
        steps = []
        lines = text.split('\n')
        for line in lines:
            if any(k in line.lower() for k in ["program", "firmware", "initialize", "configure", "write to", "poll"]):
                if len(line.strip()) > 10:
                    steps.append(line.strip())
        return steps[:5]
