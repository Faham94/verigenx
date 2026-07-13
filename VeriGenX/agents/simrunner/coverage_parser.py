import os
import re
from typing import Dict, Any

class SimCoverageParser:
    def __init__(self):
        pass

    def parse(self, coverage_dat_path: str, stdout_log: str) -> Dict[str, Any]:
        """
        Parses Verilator coverage.dat file and stdout logs to extract coverage metrics.
        """
        metrics = {
            "line_coverage": 0.0,
            "branch_coverage": 0.0,
            "functional_coverage": 0.0,
            "total_points": 0,
            "covered_points": 0,
            "functional_points_detail": {}
        }

        # 1. Parse coverage.dat if it exists
        if os.path.exists(coverage_dat_path):
            total_points = 0
            covered_points = 0
            func_total = 0
            func_covered = 0
            
            try:
                with open(coverage_dat_path, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        # Verilator coverage line pattern:
                        # C 'filename' line col hit_count name
                        parts = line.strip().split(maxsplit=5)
                        if len(parts) >= 5 and parts[0] == 'C':
                            try:
                                hit_count = int(parts[4])
                                name = parts[5] if len(parts) > 5 else ""
                                
                                total_points += 1
                                if hit_count > 0:
                                    covered_points += 1
                                    
                                # Check if it is a functional coverpoint (contains 'cp_FP_')
                                if "cp_FP_" in name:
                                    func_total += 1
                                    is_hit = (hit_count > 0)
                                    if is_hit:
                                        func_covered += 1
                                    
                                    # Extract FP_xxx name
                                    fp_match = re.search(r"cp_(FP_\d+)", name)
                                    if fp_match:
                                        fp_id = fp_match.group(1)
                                        metrics["functional_points_detail"][fp_id] = "covered" if is_hit else "uncovered"
                            except ValueError:
                                pass
                
                if total_points > 0:
                    metrics["total_points"] = total_points
                    metrics["covered_points"] = covered_points
                    cov_pct = (covered_points / total_points) * 100.0
                    metrics["line_coverage"] = cov_pct
                    metrics["branch_coverage"] = cov_pct # fallback to same
                
                if func_total > 0:
                    metrics["functional_coverage"] = (func_covered / func_total) * 100.0
            except Exception as e:
                print(f"Error parsing coverage.dat: {e}")

        # 2. Extract coverage from UVM report macros in stdout log
        # Look for e.g. "Overall simulation coverage: 100.0%" or similar pattern
        log_match = re.search(r"Overall simulation coverage:\s*([\d\.]+)%", stdout_log)
        if log_match:
            try:
                val = float(log_match.group(1))
                metrics["functional_coverage"] = val
            except ValueError:
                pass

        return metrics
