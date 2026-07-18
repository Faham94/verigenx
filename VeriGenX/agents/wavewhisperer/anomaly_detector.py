import re
import pandas as pd
from typing import Dict, Any, List

class AnomalyDetector:
    def __init__(self, design_name: str, test_plan: Dict[str, Any]):
        self.design_name = design_name.lower()
        self.test_plan = test_plan
        self.anomalies: List[Dict[str, Any]] = []

    def detect_anomalies(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        self.anomalies = []
        if df.empty:
            return self.anomalies

        # 1. Identify critical signals
        clk_col = self._find_signal(df, ["clk", "sclk", "scl"])
        rst_col = self._find_signal(df, ["rst_n", "reset", "rst"])
        state_col = self._find_signal(df, ["state", "current_state", "fsm_state", "state_reg"])

        # 2. Estimate Clock Period
        t_half = 5  # fallback
        if clk_col and len(df) > 1:
            clk_changes = df[df[clk_col] != df[clk_col].shift(1)].index.tolist()
            if clk_changes:
                clk_changes.pop(0)
            if len(clk_changes) > 1:
                diffs = [clk_changes[i] - clk_changes[i-1] for i in range(1, len(clk_changes))]
                t_half = min(diffs) if diffs else 5
        
        # 3. Scan for Undefined (X/Z) states
        self._check_xz_propagation(df)

        # 4. Check Reset behavior
        if rst_col:
            self._check_reset_issues(df, rst_col)

        # 5. Check Glitches
        self._check_glitches(df, clk_col, t_half)

        # 6. Check Setup/Hold Violations
        if clk_col:
            self._check_setup_hold(df, clk_col, t_half)

        # 7. Check FSM Transitions
        if state_col:
            self._check_fsm_transitions(df, state_col)

        # 8. Check Protocol Sequence Violations
        self._check_protocol_violations(df, clk_col)

        return self.anomalies

    def _find_signal(self, df: pd.DataFrame, search_names: List[str]) -> str:
        for name in search_names:
            for col in df.columns:
                if col.lower() == name.lower():
                    return col
        return ""

    def _check_xz_propagation(self, df: pd.DataFrame):
        for col in df.columns:
            # We don't care about UVM macro columns
            if any(x in col.upper() for x in ("UVM_", "ACTIVE", "PASSIVE")):
                continue
            
            # Find any row where the value is X or Z
            xz_mask = df[col].apply(lambda v: isinstance(v, str) and any(c in v.upper() for c in ('X', 'Z')))
            xz_times = df[xz_mask].index.tolist()
            for t in xz_times:
                val = df.loc[t, col]
                self.anomalies.append({
                    "type": "XZ_PROPAGATION",
                    "timestamp": int(t),
                    "signal": col,
                    "actual": f"Value went to '{val}'",
                    "expected": "Signal should hold a valid logic value (0 or 1)",
                    "severity": "CRITICAL"
                })

    def _check_reset_issues(self, df: pd.DataFrame, rst_col: str):
        # Reset is active low
        reset_active_mask = (df[rst_col] == 0)
        reset_times = df[reset_active_mask].index.tolist()
        
        for t in reset_times:
            # Check outputs during active reset
            for col in df.columns:
                if col in (rst_col, "clk", "sclk", "scl") or any(x in col.upper() for x in ("UVM_", "ACTIVE", "PASSIVE")):
                    continue
                
                val = df.loc[t, col]
                # Default expectation: signals should be 0 during reset
                # Exception: SPI cs_n should be 1 (inactive)
                expected_val = 1 if col.lower() == "cs_n" else 0
                
                # Normalize val for comparison if numeric float
                val_norm = int(val) if isinstance(val, (int, float)) else val
                
                if val_norm != expected_val and val not in ('X', 'Z'):
                    self.anomalies.append({
                        "type": "RESET_VIOLATION",
                        "timestamp": int(t),
                        "signal": col,
                        "actual": f"Signal value is {val} during reset",
                        "expected": f"Signal should assume reset value ({expected_val})",
                        "severity": "CRITICAL"
                    })

    def _check_glitches(self, df: pd.DataFrame, clk_col: str, t_half: int):
        glitch_threshold = max(2, t_half)
        
        for col in df.columns:
            if col == clk_col or any(x in col.upper() for x in ("UVM_", "ACTIVE", "PASSIVE")):
                continue
                
            changes = df[df[col] != df[col].shift(1)].index.tolist()
            if changes:
                changes.pop(0)
                
            for i in range(len(changes) - 1):
                pulse_width = changes[i+1] - changes[i]
                if pulse_width < glitch_threshold:
                    self.anomalies.append({
                        "type": "GLITCH_DETECTION",
                        "timestamp": int(changes[i]),
                        "signal": col,
                        "actual": f"Signal toggled back and forth within {pulse_width} units",
                        "expected": f"Signal must remain stable for at least {glitch_threshold} units",
                        "severity": "WARNING"
                    })

    def _check_setup_hold(self, df: pd.DataFrame, clk_col: str, t_half: int):
        # We define setup and hold windows as 20% of clock half-period or from timing constraints
        tc = self.test_plan.get("timing_constraints", {})
        setup_limit = int(tc.get("setup_time_ns", max(1, int(0.2 * t_half))))
        hold_limit = int(tc.get("hold_time_ns", max(1, int(0.2 * t_half))))

        # Detect positive clock edges
        clk_series = df[clk_col]
        pos_edges = df[(clk_series == 1) & (clk_series.shift(1) == 0)].index.tolist()

        for edge_time in pos_edges:
            # Check setup window
            for col in df.columns:
                if col == clk_col or any(x in col.upper() for x in ("UVM_", "ACTIVE", "PASSIVE", "RST_N")):
                    continue
                
                col_change = (df[col] != df[col].shift(1))
                changes_in_setup = df[col_change & (df.index >= edge_time - setup_limit) & (df.index < edge_time)].index.tolist()
                for t in changes_in_setup:
                    self.anomalies.append({
                        "type": "SETUP_VIOLATION",
                        "timestamp": int(t),
                        "signal": col,
                        "actual": f"Signal changed at {t} (too close to clock edge at {edge_time})",
                        "expected": f"Signal must be stable {setup_limit} units before clock edge",
                        "severity": "WARNING"
                    })

                # Check hold window
                changes_in_hold = df[col_change & (df.index > edge_time) & (df.index <= edge_time + hold_limit)].index.tolist()
                for t in changes_in_hold:
                    self.anomalies.append({
                        "type": "HOLD_VIOLATION",
                        "timestamp": int(t),
                        "signal": col,
                        "actual": f"Signal changed at {t} (too close to clock edge at {edge_time})",
                        "expected": f"Signal must be stable {hold_limit} units after clock edge",
                        "severity": "WARNING"
                    })

    def _resolve_state_name(self, val: Any, fsm_states: List[str]) -> str:
        # Check float/int
        if isinstance(val, (int, float)):
            try:
                idx = int(val)
                if 0 <= idx < len(fsm_states):
                    return fsm_states[idx]
            except (ValueError, TypeError):
                pass
        # Check string representation of number
        if isinstance(val, str):
            try:
                idx = int(val)
                if 0 <= idx < len(fsm_states):
                    return fsm_states[idx]
            except ValueError:
                pass
        return str(val)

    def _check_fsm_transitions(self, df: pd.DataFrame, state_col: str):
        fsm_states = self.test_plan.get("fsm_states", [])
        if not fsm_states:
            return

        state_changes = df[df[state_col] != df[state_col].shift(1)].index.tolist()
        if state_changes:
            state_changes.pop(0)
        
        # Mapping of valid transitions based on design name
        valid_transitions = {}
        if self.design_name == "uart":
            valid_transitions = {
                "IDLE": ["START", "IDLE"],
                "START": ["DATA"],
                "DATA": ["STOP", "DATA"],
                "STOP": ["IDLE"]
            }
        elif self.design_name == "spi":
            valid_transitions = {
                "IDLE": ["ACTIVE", "IDLE"],
                "ACTIVE": ["DONE", "ACTIVE"],
                "DONE": ["IDLE"]
            }
        elif self.design_name == "i2c":
            valid_transitions = {
                "IDLE": ["START", "IDLE"],
                "START": ["DATA"],
                "DATA": ["ACK", "DATA"],
                "ACK": ["STOP", "DATA"],
                "STOP": ["IDLE"]
            }

        for i in range(1, len(state_changes)):
            t_curr = state_changes[i]
            t_prev = state_changes[i-1]
            val_prev = df.loc[t_prev, state_col]
            val_curr = df.loc[t_curr, state_col]

            # Resolve name from index if numeric
            state_prev = self._resolve_state_name(val_prev, fsm_states)
            state_curr = self._resolve_state_name(val_curr, fsm_states)

            if valid_transitions and state_prev in valid_transitions:
                allowed = valid_transitions[state_prev]
                if state_curr not in allowed:
                    self.anomalies.append({
                        "type": "FSM_SEQUENCE_VIOLATION",
                        "timestamp": int(t_curr),
                        "signal": state_col,
                        "actual": f"State transition {state_prev} -> {state_curr}",
                        "expected": f"Only transition to {allowed} allowed from {state_prev}",
                        "severity": "CRITICAL"
                    })

    def _check_protocol_violations(self, df: pd.DataFrame, clk_col: str):
        if self.design_name == "uart":
            tx_col = self._find_signal(df, ["tx_data"])
            rx_col = self._find_signal(df, ["rx_data"])
            if tx_col and rx_col and clk_col:
                pass
        
        elif self.design_name == "spi":
            cs_col = self._find_signal(df, ["cs_n"])
            sclk_col = self._find_signal(df, ["sclk"])
            
            if cs_col and sclk_col:
                sclk_changes = df[df[sclk_col] != df[sclk_col].shift(1)].index.tolist()
                if sclk_changes:
                    sclk_changes.pop(0)
                for t in sclk_changes:
                    cs_val = df.loc[t, cs_col]
                    if cs_val == 1:
                        self.anomalies.append({
                            "type": "PROTOCOL_VIOLATION",
                            "timestamp": int(t),
                            "signal": sclk_col,
                            "actual": "SCLK toggling while CS_N is inactive (high)",
                            "expected": "SCLK must toggle only when CS_N is active (low)",
                            "severity": "CRITICAL"
                        })
                        
        elif self.design_name == "i2c":
            scl_col = self._find_signal(df, ["scl"])
            sda_col = self._find_signal(df, ["sda"])
            
            if scl_col and sda_col:
                sda_changes = df[df[sda_col] != df[sda_col].shift(1)].index.tolist()
                if sda_changes:
                    sda_changes.pop(0)
                for t in sda_changes:
                    scl_val = df.loc[t, scl_col]
                    if scl_val == 1:
                        prev_t_list = df.index[df.index < t].tolist()
                        if prev_t_list:
                            prev_t = prev_t_list[-1]
                            sda_prev = df.loc[prev_t, sda_col]
                            sda_curr = df.loc[t, sda_col]
                            
                            is_start = (sda_prev == 1 and sda_curr == 0)
                            is_stop = (sda_prev == 0 and sda_curr == 1)
                            
                            if not (is_start or is_stop):
                                self.anomalies.append({
                                    "type": "PROTOCOL_VIOLATION",
                                    "timestamp": int(t),
                                    "signal": sda_col,
                                    "actual": "SDA changed value while SCL is high (not a valid START/STOP condition)",
                                    "expected": "SDA must toggle only when SCL is low, or transition uniquely for START/STOP",
                                    "severity": "CRITICAL"
                                })
