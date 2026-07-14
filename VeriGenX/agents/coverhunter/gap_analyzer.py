import os
import re
import json
from typing import List, Dict, Any

class GapAnalyzer:
    def __init__(self):
        pass

    def analyze_gaps(self, test_plan: Dict[str, Any], sim_results: Dict[str, Any], run_dir: str) -> List[Dict[str, Any]]:
        """
        Classifies coverage gaps into:
        - uncovered line
        - uncovered branch
        - uncovered functional bin
        - uncovered FSM state

        Prioritizes gaps by estimated test complexity and coverage impact.
        Returns a sorted list of gaps (highest priority first).
        """
        gaps: List[Dict[str, Any]] = []

        # 1. Extract Line and Branch gaps from Verilator's coverage.dat
        coverage_dat_path = os.path.join(run_dir, "coverage.dat")
        if os.path.exists(coverage_dat_path):
            try:
                with open(coverage_dat_path, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        line_str = line.strip()
                        if line_str.startswith("C '"):
                            last_quote_idx = line_str.rfind("'")
                            if last_quote_idx != -1:
                                metadata = line_str[3:last_quote_idx]
                                hit_count_str = line_str[last_quote_idx+1:].strip()
                                try:
                                    hit_count = int(hit_count_str)
                                except ValueError:
                                    continue

                                if hit_count == 0:
                                    # Extract coverage type
                                    cov_type = "line"
                                    t_marker = "\x01t\x02"
                                    t_idx = metadata.find(t_marker)
                                    if t_idx != -1:
                                        start_val = t_idx + len(t_marker)
                                        next_x01 = metadata.find("\x01", start_val)
                                        cov_type = metadata[start_val:next_x01] if next_x01 != -1 else metadata[start_val:]

                                    if cov_type not in ["line", "branch"]:
                                        continue

                                    # Extract file name
                                    filename = "unknown"
                                    f_marker = "\x01f\x02"
                                    f_idx = metadata.find(f_marker)
                                    if f_idx != -1:
                                        start_val = f_idx + len(f_marker)
                                        next_x01 = metadata.find("\x01", start_val)
                                        filename = metadata[start_val:next_x01] if next_x01 != -1 else metadata[start_val:]

                                    # Extract line number
                                    line_num = 0
                                    l_marker = "\x01l\x02"
                                    l_idx = metadata.find(l_marker)
                                    if l_idx != -1:
                                        start_val = l_idx + len(l_marker)
                                        next_x01 = metadata.find("\x01", start_val)
                                        try:
                                            line_num = int(metadata[start_val:next_x01] if next_x01 != -1 else metadata[start_val:])
                                        except ValueError:
                                            pass

                                    # Compute score and complexity
                                    priority_score = 30
                                    complexity = "medium"
                                    if "driver" in filename or "monitor" in filename:
                                        priority_score = 60
                                        complexity = "medium"
                                    elif "interface" in filename:
                                        priority_score = 50
                                        complexity = "low"
                                    elif "scoreboard" in filename:
                                        priority_score = 40
                                        complexity = "high"

                                    if cov_type == "branch":
                                        priority_score += 5

                                    gaps.append({
                                        "type": f"uncovered {cov_type}",
                                        "name": f"{filename}:{line_num}",
                                        "file": filename,
                                        "line": line_num,
                                        "priority_score": priority_score,
                                        "estimated_complexity": complexity
                                    })
            except Exception as e:
                print(f"[GapAnalyzer] Error parsing coverage.dat: {e}")

        # 2. Extract Functional Coverage gaps from functional_coverage_report.json
        func_report_path = os.path.join(run_dir, "functional_coverage_report.json")
        if os.path.exists(func_report_path):
            try:
                with open(func_report_path, "r", encoding="utf-8") as f:
                    fc_data = json.load(f)
                points = fc_data.get("points", {})
                for fp_id, details in points.items():
                    hit_count = details.get("hit_count", 0)
                    if hit_count == 0:
                        priority_score = 80
                        desc = details.get("description", "")
                        # Prioritize initialization or standard transfer
                        if "reset" in desc.lower() or "init" in desc.lower() or "transmit" in desc.lower():
                            priority_score = 90

                        gaps.append({
                            "type": "uncovered functional bin",
                            "name": fp_id,
                            "id": fp_id,
                            "description": desc,
                            "priority_score": priority_score,
                            "estimated_complexity": "low"
                        })
            except Exception as e:
                print(f"[GapAnalyzer] Error parsing functional_coverage_report.json: {e}")

        # 3. Extract FSM state gaps from test_plan fsm_states
        fsm_states = test_plan.get("fsm_states", [])
        if fsm_states:
            # Check if FSM states are mentioned in stdout of any of the simulations
            for state in fsm_states:
                state_covered = False
                for test_name, test_res in sim_results.get("tests", {}).items():
                    log_content = test_res.get("stdout", "").upper()
                    # A state is considered covered if it's explicitly hit/referenced in logs
                    if state.upper() in log_content:
                        state_covered = True
                        break

                if not state_covered:
                    priority_score = 100
                    if state.upper() in ["IDLE", "RESET", "START"]:
                        priority_score = 120 # easy to reach, high priority

                    gaps.append({
                        "type": "uncovered FSM state",
                        "name": state,
                        "priority_score": priority_score,
                        "estimated_complexity": "medium"
                    })

        # Sort gaps descending by priority_score
        gaps.sort(key=lambda x: x["priority_score"], reverse=True)
        return gaps
