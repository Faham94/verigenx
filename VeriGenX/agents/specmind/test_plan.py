"""
Test Plan Generator
Converts extracted knowledge into a structured JSON test plan.

Fixes applied:
  - Bug #1: Was returning hardcoded UART JSON regardless of input.
            Now calls Extractor on the actual spec text.
  - Bug #2: Extractor now invoked properly — LLM used when available,
            regex heuristics used as fallback.
"""
import json
import os
import re
from datetime import datetime
from typing import Dict, List, Optional

from VeriGenX.config import TEST_PLANS_DIR


class TestPlanGenerator:

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    def generate(self, text: str, design_name: Optional[str] = None) -> Dict:
        """
        Generate a structured JSON test plan from spec text.

        Bug #1 + #2 fix:
          1. Try LLM-based extraction via Extractor (when Ollama available).
          2. Fall back to regex heuristics when LLM unavailable.
          3. Fill any missing fields from UART defaults as last resort.
        """
        # Infer design name from content if not provided
        inferred_name = design_name or self._infer_design_name(text)

        # --- Attempt LLM extraction (Bug #2 fix: actually call Extractor) ---
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

        # --- Regex heuristic fallback for missing fields ---
        signals   = extracted.get("signals")     or self._heuristic_signals(text)
        fsm       = extracted.get("fsm_states")  or self._heuristic_fsm(text)
        registers = extracted.get("register_map") or self._heuristic_registers(text)
        timing    = extracted.get("timing_constraints") or self._heuristic_timing(text)
        func_pts  = extracted.get("functional_points") or self._heuristic_functional_points(text)

        # --- Apply UART defaults only for completely empty fields ---
        signals   = signals   or self._uart_default_signals()
        fsm       = fsm       or self._uart_default_fsm()
        registers = registers or self._uart_default_registers()
        func_pts  = func_pts  or self._uart_default_functional_points()

        plan = {
            "design_name":          inferred_name,
            "version":              "1.0",
            "generated_at":         datetime.now().isoformat(),
            "extraction_method":    "llm" if llm_available else "heuristic",
            "signals":              signals,
            "fsm_states":           fsm,
            "register_map":         registers,
            "timing_constraints":   timing,
            "functional_points":    func_pts,
        }

        # Include confidence if LLM was used
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
        for name in ["uart", "spi", "i2c", "axi", "fifo", "apb", "ahb",
                     "pcie", "usb", "ethernet", "can"]:
            if name in text_lower:
                return name
        return "design"

    # ------------------------------------------------------------------ #
    #  Regex heuristic extractors                                          #
    # ------------------------------------------------------------------ #

    def _heuristic_signals(self, text: str) -> List[Dict]:
        """Extract signal names via regex patterns common in RTL specs."""
        signals = []
        # Match patterns like "clk: 1-bit input" or "input [7:0] tx_data"
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
        """Extract FSM state names (UPPERCASE words near 'state' or 'FSM')."""
        states = []
        # Common state pattern: uppercase word near fsm/state context
        for m in re.finditer(r"\b([A-Z][A-Z0-9_]{1,})\b", text):
            word = m.group(1)
            if word not in states and len(word) >= 2:
                states.append(word)
        # Filter to plausible FSM states
        fsm_keywords = {"IDLE", "START", "STOP", "DATA", "WAIT", "SEND",
                        "RECEIVE", "ACK", "NACK", "RESET", "INIT", "DONE",
                        "TX", "RX", "ACTIVE", "PAUSE", "ERROR", "SETUP"}
        filtered = [s for s in states if s in fsm_keywords]
        return filtered if filtered else states[:6]

    def _heuristic_registers(self, text: str) -> List[Dict]:
        """Extract register map entries via hex address patterns."""
        registers = []
        seen = set()
        for m in re.finditer(
            r"(0x[0-9A-Fa-f]{2,8})\s*[:=]?\s*(\w+)\s*[,;]?\s*(?:\((\d+)[\s-]*bit\))?",
            text, re.IGNORECASE
        ):
            addr, name, width = m.group(1), m.group(2), m.group(3)
            if name.lower() in seen:
                continue
            seen.add(name.lower())
            registers.append({
                "address": addr.upper(),
                "name":    name,
                "width":   int(width) if width else 8,
            })
        return registers

    def _heuristic_timing(self, text: str) -> Dict:
        """Extract timing values via numeric pattern matching."""
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
        """Generate functional points from signal and register context."""
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

    # ------------------------------------------------------------------ #
    #  UART defaults (last resort only)                                    #
    # ------------------------------------------------------------------ #

    def _uart_default_signals(self):
        return [
            {"name": "clk",     "width": 1, "direction": "input"},
            {"name": "rst_n",   "width": 1, "direction": "input"},
            {"name": "tx_data", "width": 8, "direction": "input"},
            {"name": "rx_data", "width": 8, "direction": "output"},
        ]

    def _uart_default_fsm(self):
        return ["IDLE", "START", "DATA", "STOP"]

    def _uart_default_registers(self):
        return [
            {"address": "0x00", "name": "baud_divisor", "width": 16},
            {"address": "0x04", "name": "control",      "width": 8},
        ]

    def _uart_default_functional_points(self):
        return [
            {"id": "FP_001", "description": "8-bit data transmission"},
            {"id": "FP_002", "description": "Baud rate configuration"},
        ]
