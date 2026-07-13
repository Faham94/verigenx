import os
import subprocess
from typing import Dict, Any, Tuple

class SimExecutor:
    def __init__(self):
        pass

    def execute(self, binary_path: str, test_name: str, run_dir: str, timeout: int = 15) -> Dict[str, Any]:
        """
        Executes the compiled simulation binary with the given test name.
        """
        if not os.path.exists(binary_path):
            return {
                "success": False,
                "error": "Binary does not exist.",
                "stdout": "",
                "stderr": "",
                "returncode": -1
            }

        design_name = os.path.basename(binary_path).replace("V", "").replace("_sim.exe", "").replace("_sim", "")
        vcd_filename = f"{design_name}_{test_name}.vcd"
        vcd_path = os.path.join(run_dir, vcd_filename)
        coverage_path = os.path.join(run_dir, "coverage.dat")

        cmd = [
            binary_path,
            f"+UVM_TESTNAME={test_name}",
            f"+VCD_FILE={vcd_path}"
        ]

        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False,
                text=True,
                timeout=timeout,
                cwd=run_dir
            )
            
            # Check stdout for fatal errors
            stdout = result.stdout
            stderr = result.stderr
            
            success = (result.returncode == 0)
            if "[UVM_FATAL]" in stdout or "[UVM_ERROR]" in stdout or "%Error" in stderr:
                success = False

            return {
                "success": success,
                "returncode": result.returncode,
                "stdout": stdout,
                "stderr": stderr,
                "vcd_path": vcd_path if os.path.exists(vcd_path) else "",
                "coverage_dat_path": coverage_path if os.path.exists(coverage_path) else ""
            }

        except subprocess.TimeoutExpired as e:
            return {
                "success": False,
                "error": f"Simulation timed out after {timeout} seconds.",
                "stdout": e.stdout.decode("utf-8", errors="ignore") if e.stdout else "",
                "stderr": e.stderr.decode("utf-8", errors="ignore") if e.stderr else "",
                "returncode": -2
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "stdout": "",
                "stderr": "",
                "returncode": -3
            }
