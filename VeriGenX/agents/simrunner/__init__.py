import os
import json
from datetime import datetime
from typing import List, Dict, Any

from VeriGenX.agents.simrunner.compiler import SimCompiler
from VeriGenX.agents.simrunner.executor import SimExecutor
from VeriGenX.agents.simrunner.coverage_parser import SimCoverageParser
from VeriGenX.agents.simrunner.log_parser import SimLogParser

class SimRunner:
    def __init__(self):
        self.compiler = SimCompiler()
        self.executor = SimExecutor()
        self.coverage_parser = SimCoverageParser()
        self.log_parser = SimLogParser()
        self.run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    def run_simulations(self, design_name: str, test_plan: Dict[str, Any], uvm_files: List[str], base_run_dir: str = "output") -> Dict[str, Any]:
        """
        Coordinates the full simulation lifecycle:
        Compile -> Execute tests -> Parse Logs -> Parse Coverage -> Aggregate Results.
        """
        # Define isolated run output directory to never overwrite previous run artifacts
        run_dir = os.path.join(base_run_dir, f"sim_{self.run_id}")
        os.makedirs(run_dir, exist_ok=True)

        results = {
            "design_name": design_name,
            "run_id": self.run_id,
            "compiled": False,
            "compile_log": "",
            "tests": {},
            "coverage": {},
            "status": "failed"
        }

        # 1. Compile
        print(f"  Compiling simulation for {design_name}...")
        success, compile_log, binary_path = self.compiler.compile(design_name, test_plan, uvm_files, run_dir)
        results["compiled"] = success
        results["compile_log"] = compile_log

        if not success:
            print(f"  [Error] Compilation failed:\n{compile_log}")
            return results

        # 2. Run test classes
        # List of tests to run (from plan / default template conventions)
        tests_to_run = [f"{design_name}_test_base", f"{design_name}_test_directed"]
        passed_tests = 0

        # Create output directory for coverage
        for test_name in tests_to_run:
            print(f"  Running test: {test_name}...")
            exec_res = self.executor.execute(binary_path, test_name, run_dir, timeout=15)
            
            # Parse logs and severity
            log_metrics = self.log_parser.parse(exec_res.get("stdout", ""), exec_res.get("stderr", ""))
            
            # Parse coverage
            cov_metrics = self.coverage_parser.parse(exec_res.get("coverage_dat_path", ""), exec_res.get("stdout", ""))

            test_status = log_metrics["summary"]["status"]
            if exec_res.get("returncode") != 0:
                test_status = "failed"
            
            if test_status == "passed":
                passed_tests += 1

            results["tests"][test_name] = {
                "success": (test_status == "passed"),
                "status": test_status,
                "stdout": exec_res.get("stdout", ""),
                "stderr": exec_res.get("stderr", ""),
                "vcd_path": exec_res.get("vcd_path", ""),
                "log_summary": log_metrics,
                "coverage": cov_metrics
            }

        # 3. Aggregate overall results
        all_passed = (passed_tests == len(tests_to_run))
        results["status"] = "passed" if all_passed else "failed"

        # Aggregate coverage from the last run or take max/average
        # (directed test typically runs more sequences and achieves more coverage)
        agg_cov = {
            "line_coverage": 100.0,
            "branch_coverage": 100.0,
            "functional_coverage": 100.0
        }
        for test_name in tests_to_run:
            if test_name in results["tests"]:
                test_cov = results["tests"][test_name]["coverage"]
                agg_cov["line_coverage"] = min(agg_cov["line_coverage"], test_cov.get("line_coverage", 100.0))
                agg_cov["branch_coverage"] = min(agg_cov["branch_coverage"], test_cov.get("branch_coverage", 100.0))
                agg_cov["functional_coverage"] = min(agg_cov["functional_coverage"], test_cov.get("functional_coverage", 100.0))
        
        results["coverage"] = agg_cov

        # Save run report to output directory
        run_report_path = os.path.join(run_dir, "simulation_run_report.json")
        try:
            with open(run_report_path, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=4)
            
            # Save global simulation report
            with open("output/validation_report.json", "w", encoding="utf-8") as f:
                json.dump(results, f, indent=4)
        except Exception as e:
            print(f"Error saving simulation report: {e}")

        return results
