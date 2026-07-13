import re
from typing import Dict, Any, List

class SimLogParser:
    def __init__(self):
        pass

    def parse(self, stdout: str, stderr: str) -> Dict[str, Any]:
        """
        Parses simulation output log to classify errors, warnings, and messages by severity.
        """
        fatals: List[str] = []
        errors: List[str] = []
        warnings: List[str] = []
        info: List[str] = []

        # Combine stdout and stderr for full scan
        log_content = stdout + "\n" + stderr
        lines = log_content.splitlines()

        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue

            # Check for UVM report severities
            if "[UVM_FATAL]" in line_str:
                fatals.append(line_str)
            elif "[UVM_ERROR]" in line_str:
                errors.append(line_str)
            elif "[UVM_WARNING]" in line_str:
                warnings.append(line_str)
            elif "[UVM_INFO]" in line_str:
                info.append(line_str)
            
            # Check for Verilator linter %Error or %Warning
            elif "%Error" in line_str:
                errors.append(line_str)
            elif "%Warning" in line_str:
                warnings.append(line_str)

        total_errors = len(errors) + len(fatals)
        total_warnings = len(warnings)
        
        status = "passed" if total_errors == 0 else "failed"
        if "Simulation timed out" in log_content:
            status = "failed"
            errors.append("Simulation execution timeout limit reached.")

        return {
            "fatals": fatals,
            "errors": errors,
            "warnings": warnings,
            "info": info,
            "summary": {
                "total_errors": total_errors,
                "total_warnings": total_warnings,
                "status": status
            }
        }
