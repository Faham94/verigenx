import os
import re
import json
import sys
import shutil

# Ensure VeriGenX is in the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from VeriGenX.agents.coverhunter.closure_loop import ClosureLoop
from VeriGenX.state_bus import get_state_bus, PipelineState

def clean_previous_directed_tests(design_name: str):
    """Deletes directed tests from previous CoverHunter runs, leaving the base test and baseline directed test."""
    print(f"Cleaning previous CoverHunter-generated tests for {design_name}...")
    gen_dir = "generated_uvm"
    if not os.path.exists(gen_dir):
        return
    for filename in os.listdir(gen_dir):
        # Match design_test_directed_xyz.sv but NOT design_test_directed.sv
        if filename.startswith(f"{design_name}_test_directed_") and filename.endswith(".sv"):
            filepath = os.path.join(gen_dir, filename)
            try:
                os.remove(filepath)
                print(f"  Removed: {filename}")
            except Exception as e:
                print(f"  Error removing {filename}: {e}")

def run_design(design_name: str):
    print("\n" + "="*80)
    print(f"RUNNING COVERAGE CLOSURE LOOP FOR: {design_name.upper()}")
    print("="*80)
    
    # 1. Clean previous runs
    clean_previous_directed_tests(design_name)
    
    # 2. Reset state bus
    state_bus = get_state_bus()
    state_bus.state = PipelineState()
    
    # 3. Load test plan
    test_plan_path = f"test_plans/{design_name}_test_plan.json"
    if not os.path.exists(test_plan_path):
        print(f"Error: test plan not found at {test_plan_path}")
        return
    with open(test_plan_path, "r", encoding="utf-8") as f:
        test_plan = json.load(f)
        
    state_bus.update_state(test_plan=test_plan)
    
    # 4. Gather baseline UVM files
    base_files = [
        f"{design_name}_interface.sv",
        f"{design_name}_sequence_item.sv",
        f"{design_name}_sequence.sv",
        f"{design_name}_driver.sv",
        f"{design_name}_monitor.sv",
        f"{design_name}_agent.sv",
        f"{design_name}_scoreboard.sv",
        f"{design_name}_coverage.sv",
        f"{design_name}_env.sv",
        f"{design_name}_test_base.sv",
        f"{design_name}_test_directed.sv",
        f"{design_name}_top.sv"
    ]
    
    uvm_files = []
    for f in base_files:
        path = os.path.abspath(os.path.join("generated_uvm", f))
        if os.path.exists(path):
            uvm_files.append(path)
        else:
            print(f"Warning: expected file {path} not found")
            
    print(f"Gathered {len(uvm_files)} baseline files.")
    
    # 5. Run CoverHunter loop
    loop = ClosureLoop(max_iterations=5, convergence_threshold=0.1)
    results = loop.run_closure_loop(
        design_name=design_name,
        test_plan=test_plan,
        initial_uvm_files=uvm_files,
        base_run_dir="output"
    )
    
    # Read final coverage from report to confirm
    report_path = f"output/coverhunter_report_{design_name}.json"
    if os.path.exists(report_path):
        with open(report_path, "r", encoding="utf-8") as f:
            report_data = json.load(f)
        fc = report_data["final_coverage"]["functional_coverage"]
        print(f"SUCCESS: Finished {design_name}. Final functional coverage: {fc:.2f}%")
    else:
        print(f"Error: Report was not generated at {report_path}")

def main():
    designs = ["uart", "spi", "i2c"]
    for d in designs:
        run_design(d)

if __name__ == "__main__":
    main()
