import os
import re
from typing import Dict, Any

class SimCoverageParser:
    def __init__(self):
        pass

    def parse(self, coverage_dat_path: str, stdout_log: str, run_dir: str = None) -> Dict[str, Any]:
        """
        Parses Verilator coverage.dat file and stdout logs to extract coverage metrics.
        """
        metrics = {
            "line_coverage": 0.0,
            "branch_coverage": 0.0,
            "toggle_coverage": 0.0,
            "functional_coverage": 0.0,
            "total_points": 0,
            "covered_points": 0,
            "functional_points_detail": {}
        }

        # 1. Parse coverage.dat if it exists
        if os.path.exists(coverage_dat_path):
            total_line = 0
            covered_line = 0
            total_branch = 0
            covered_branch = 0
            total_toggle = 0
            covered_toggle = 0
            
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
                                
                                # Search for the 't' field value using Verilator's structured delimiters (\x01 and \x02)
                                cov_type = "unknown"
                                t_marker = "\x01t\x02"
                                match_idx = metadata.find(t_marker)
                                if match_idx != -1:
                                    start_val = match_idx + len(t_marker)
                                    next_x01 = metadata.find("\x01", start_val)
                                    if next_x01 != -1:
                                        cov_type = metadata[start_val:next_x01]
                                    else:
                                        cov_type = metadata[start_val:]
                                
                                if cov_type == "line":
                                    total_line += 1
                                    if hit_count > 0:
                                        covered_line += 1
                                elif cov_type == "branch":
                                    total_branch += 1
                                    if hit_count > 0:
                                        covered_branch += 1
                                elif cov_type == "toggle":
                                    total_toggle += 1
                                    if hit_count > 0:
                                        covered_toggle += 1
            except Exception as e:
                print(f"Error parsing coverage.dat: {e}")
                
            # Compute distinct metrics
            if total_line > 0:
                metrics["line_coverage"] = (covered_line / total_line) * 100.0
            if total_branch > 0:
                metrics["branch_coverage"] = (covered_branch / total_branch) * 100.0
            if total_toggle > 0:
                metrics["toggle_coverage"] = (covered_toggle / total_toggle) * 100.0
                
            metrics["total_points"] = total_line + total_branch + total_toggle
            metrics["covered_points"] = covered_line + covered_branch + covered_toggle

        # 2. Extract coverage from UVM report macros in stdout log
        log_match = re.search(r"Overall simulation coverage:\s*([\d\.]+)%", stdout_log)
        if log_match:
            try:
                val = float(log_match.group(1))
                metrics["functional_coverage"] = val
            except ValueError:
                pass

        # 3. Read functional coverage from JSON
        import json
        json_path = ""
        if run_dir:
            json_path = os.path.join(run_dir, "functional_coverage_report.json")
        elif coverage_dat_path:
            json_path = os.path.join(os.path.dirname(coverage_dat_path), "functional_coverage_report.json")

        if json_path and os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    fc_data = json.load(f)
                metrics["functional_coverage"] = fc_data.get("overall_functional_coverage", 0.0)
                metrics["functional_points_detail"] = fc_data.get("points", {})
            except Exception as e:
                print(f"Error reading functional coverage JSON from {json_path}: {e}")

        return metrics

