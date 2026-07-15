import os
import re
import shutil
import json
from typing import List, Dict, Any

from VeriGenX.agents.simrunner import SimRunner
from VeriGenX.agents.coverhunter.gap_analyzer import GapAnalyzer
from VeriGenX.agents.coverhunter.test_generator import TestGenerator
from VeriGenX.state_bus import get_state_bus

class ClosureLoop:
    def __init__(self, max_iterations: int = 5, convergence_threshold: float = 0.1):
        self.max_iterations = max_iterations
        self.convergence_threshold = convergence_threshold
        self.gap_analyzer = GapAnalyzer()
        self.test_generator = TestGenerator()
        self.state_bus = get_state_bus()

    def run_closure_loop(self, design_name: str, test_plan: Dict[str, Any], initial_uvm_files: List[str], base_run_dir: str = "output") -> Dict[str, Any]:
        """
        Coordinates the main coverage closure feedback loop:
        1. Run SimRunner
        2. Identify and prioritize gaps
        3. Terminate if target coverage met, convergence detected, or max iterations reached
        4. Otherwise generate a targeted test, append to file list, and repeat
        5. Implements rollback logic if a new test causes regression/compilation failure
        """
        active_uvm_files = list(initial_uvm_files)
        
        # History to track test suites and overall metrics
        history: List[Dict[str, Any]] = []
        
        # Keep track of previous functional coverage and total coverage for comparison
        prev_functional_coverage = None
        prev_total_coverage = None

        # Track rollback events
        rollback_occurred = False
        rollback_reason = None
        rollback_iteration = None
        
        print("\n============================================================")
        print("  COVERHUNTER: STARTING COVERAGE CLOSURE LOOP")
        print("============================================================")

        for iteration in range(1, self.max_iterations + 1):
            print(f"\n--- Iteration {iteration} / {self.max_iterations} ---")
            
            # 1. Run SimRunner on current test suite
            # We instantiate a fresh SimRunner so it gets a unique run ID and output folder
            runner = SimRunner()
            results = runner.run_simulations(design_name, test_plan, active_uvm_files, base_run_dir)
            
            run_dir = os.path.join(base_run_dir, f"sim_{runner.run_id}")
            
            # If compilation failed, or overall status is not passed, treat coverage as 0.0
            if not results.get("compiled", False):
                print("  [ClosureLoop] Compilation failed in this iteration.")
                current_functional_coverage = 0.0
                current_total_coverage = 0.0
            else:
                cov = results.get("coverage", {})
                current_functional_coverage = cov.get("functional_coverage", 0.0)
                
                line = cov.get("line_coverage", 0.0)
                branch = cov.get("branch_coverage", 0.0)
                toggle = cov.get("toggle_coverage", 0.0)
                current_total_coverage = (line + branch + toggle + current_functional_coverage) / 4.0

            print(f"  [ClosureLoop] Functional Coverage: {current_functional_coverage:.2f}%")
            print(f"  [ClosureLoop] Total Staged Coverage: {current_total_coverage:.2f}%")

            # 2. Rollback Check (vs. previous iteration's metrics)
            if iteration > 1:
                # If compilation failed, simulation status is failed, or functional coverage decreased, we roll back!
                if not results.get("compiled", False) or results.get("status") != "passed" or current_functional_coverage < prev_functional_coverage:
                    rollback_reason = f"Compilation failed, simulation failed, or functional coverage decreased from {prev_functional_coverage:.2f}% to {current_functional_coverage:.2f}%"
                    print(f"  [WARNING] {rollback_reason}. Triggering ROLLBACK!")
                    rollback_occurred = True
                    rollback_iteration = iteration
                    
                    # Revert file list to the last known-good files list
                    last_good_suite = history[-1]["uvm_files"]
                    last_good_results = history[-1]["results"]
                    
                    # Delete the offending file added in the previous iteration
                    offending_file = active_uvm_files[-1]
                    if offending_file not in last_good_suite:
                        if os.path.exists(offending_file):
                            try:
                                os.remove(offending_file)
                                print(f"  [ClosureLoop] Rolled back and deleted file: {offending_file}")
                            except Exception as e:
                                print(f"  [ClosureLoop] Error deleting file: {e}")
                    
                    active_uvm_files = list(last_good_suite)
                    
                    # Re-run simulation on the last good suite to ensure correct system state
                    runner = SimRunner()
                    results = runner.run_simulations(design_name, test_plan, active_uvm_files, base_run_dir)
                    
                    # Restore previous stats
                    current_functional_coverage = prev_functional_coverage
                    current_total_coverage = prev_total_coverage
                    
                    # Update StateBus with final status
                    self.state_bus.update_state(
                        generated_files=active_uvm_files,
                        simulation_results=results,
                        coverage_data=results.get("coverage")
                    )
                    
                    print("  [ClosureLoop] Rollback complete. Terminating closure loop.")
                    break

            # Save iteration snapshot to history
            coverage_snapshot = {
                "functional_coverage": current_functional_coverage,
                "line_coverage": results.get("coverage", {}).get("line_coverage", 0.0) if results.get("compiled", False) else 0.0,
                "branch_coverage": results.get("coverage", {}).get("branch_coverage", 0.0) if results.get("compiled", False) else 0.0,
                "toggle_coverage": results.get("coverage", {}).get("toggle_coverage", 0.0) if results.get("compiled", False) else 0.0,
                "total_coverage": current_total_coverage
            }
            history.append({
                "iteration": iteration,
                "uvm_files": list(active_uvm_files),
                "coverage": coverage_snapshot,
                "targeted_gap": None,
                "results": results
            })

            # Update StateBus with current iteration progress
            self.state_bus.update_state(
                generated_files=active_uvm_files,
                simulation_results=results,
                coverage_data=results.get("coverage")
            )

            # 3. Termination Condition Checks
            if current_functional_coverage >= 85.0:
                print(f"  [ClosureLoop] Target functional coverage met: {current_functional_coverage:.2f}% >= 85%. Terminating.")
                break

            if prev_functional_coverage is not None:
                improvement = current_functional_coverage - prev_functional_coverage
                if improvement <= self.convergence_threshold:
                    print(f"  [ClosureLoop] Stagnation detected: improvement ({improvement:.2f}%) <= threshold ({self.convergence_threshold:.2f}%). Terminating.")
                    break

            # 4. Analyze Coverage Gaps
            gaps = self.gap_analyzer.analyze_gaps(test_plan, results, run_dir)
            if not gaps:
                print("  [ClosureLoop] No coverage gaps identified. Terminating.")
                break

            print(f"  [ClosureLoop] Identified {len(gaps)} coverage gaps. Top gap: {gaps[0]['type']} ({gaps[0]['name']})")
            
            # Save previous metrics before modifying the test suite
            prev_functional_coverage = current_functional_coverage
            prev_total_coverage = current_total_coverage

            # 5. Generate targeted test for the highest-priority gap
            selected_gap = gaps[0]
            clean_gap_name = re.sub(r"[^\w]", "_", selected_gap["name"])
            new_test_filename = f"{design_name}_test_directed_{clean_gap_name}.sv"
            new_test_path = os.path.abspath(os.path.join("generated_uvm", new_test_filename)).replace(chr(92), "/")

            # Update history with targeted gap details for this iteration
            history[-1]["targeted_gap"] = {
                "name": selected_gap.get("name"),
                "type": selected_gap.get("type"),
                "description": selected_gap.get("description", "")
            }

            test_code = self.test_generator.generate_targeted_test(
                design_name, test_plan, selected_gap, active_uvm_files, run_dir
            )

            if test_code:
                # Write file to generated_uvm/
                os.makedirs("generated_uvm", exist_ok=True)
                with open(new_test_path, "w", encoding="utf-8") as f:
                    f.write(test_code)
                print(f"  [ClosureLoop] Successfully generated targeted test: {new_test_path}")
                
                # Append to file list for next iteration
                active_uvm_files.append(new_test_path)
            else:
                print("  [ClosureLoop] LLM test generation failed for selected gap. Terminating.")
                break

        print("\n============================================================")
        print("  COVERHUNTER: CLOSURE LOOP COMPLETE")
        print("============================================================")

        # Build baseline coverage dict
        baseline_coverage = {}
        if len(history) > 0:
            baseline_coverage = history[0]["coverage"]

        # Build final coverage dict
        final_coverage = {
            "functional_coverage": current_functional_coverage,
            "line_coverage": results.get("coverage", {}).get("line_coverage", 0.0) if results.get("compiled", False) else 0.0,
            "branch_coverage": results.get("coverage", {}).get("branch_coverage", 0.0) if results.get("compiled", False) else 0.0,
            "toggle_coverage": results.get("coverage", {}).get("toggle_coverage", 0.0) if results.get("compiled", False) else 0.0,
            "total_coverage": current_total_coverage
        }

        # Build iterations summary
        iterations_data = []
        for h in history:
            iterations_data.append({
                "iteration": h["iteration"],
                "coverage": h["coverage"],
                "targeted_gap": h["targeted_gap"]
            })

        report_data = {
            "design_name": design_name,
            "baseline_coverage": baseline_coverage,
            "iterations": iterations_data,
            "rollback_info": {
                "occurred": rollback_occurred,
                "reason": rollback_reason,
                "iteration": rollback_iteration
            },
            "final_coverage": final_coverage
        }

        # Dump report to output/coverhunter_report.json
        os.makedirs(base_run_dir, exist_ok=True)
        report_path = os.path.join(base_run_dir, "coverhunter_report.json")
        try:
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(report_data, f, indent=2)
            print(f"  [ClosureLoop] Successfully wrote CoverHunter report to {report_path}")
        except Exception as e:
            print(f"  [ClosureLoop] Error writing CoverHunter report to {report_path}: {e}")
        
        return history[-1]["results"]
