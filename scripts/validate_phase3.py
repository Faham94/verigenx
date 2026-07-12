"""
UVMForge Validation Script for Phase 3.
Validates all 8 reference designs, clearly flagging/skipping missing ones.
Measures first-pass success rate, repair statistics, and outputs JSON + Markdown reports.
"""
import os
import json
import sys

# Ensure VeriGenX is in the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from VeriGenX.agents.uvmforge.generator import UVMForgeGenerator
from VeriGenX.agents.archweaver.dag_builder import DAGBuilder
from VeriGenX.agents.uvmforge.metrics import update_metrics


def run_validation():
    print("=" * 60)
    print("Running UVMForge Validation on 8 Reference Designs...")
    print("=" * 60)

    all_designs = ["uart", "spi", "i2c", "axi_lite", "fifo", "axi", "counter", "riscv"]
    generator = UVMForgeGenerator()
    builder = DAGBuilder()
    
    validation_results = {}
    skipped_designs = []
    processed_designs = []
    
    # Reset previous run data
    attempts_path = "output/repair_attempts.json"
    if os.path.exists(attempts_path):
        try:
            os.remove(attempts_path)
        except Exception:
            pass

    for design in all_designs:
        # Check standard file naming or custom
        test_plan_path = f"test_plans/{design}_test_plan.json"
        
        if not os.path.exists(test_plan_path):
            print(f"[Validation] Design '{design.upper()}' is missing test plan fixture -> SKIP")
            skipped_designs.append(design)
            validation_results[design] = {
                "status": "skipped",
                "reason": "Test plan JSON file not found in test_plans/"
            }
            continue
            
        print(f"[Validation] Processing design '{design.upper()}'...")
        processed_designs.append(design)
        
        try:
            with open(test_plan_path, "r", encoding="utf-8") as f:
                test_plan = json.load(f)
                
            dag = builder.build_from_test_plan(test_plan_dict=test_plan)
            files = generator.generate_all(test_plan, dag)
            
            validation_results[design] = {
                "status": "passed",
                "files_count": len(files)
            }
        except Exception as e:
            print(f"[Validation] Error processing design '{design.upper()}': {e}")
            validation_results[design] = {
                "status": "failed",
                "error": str(e)
            }

    # Aggregate compile report statistics
    update_metrics()
    
    metrics_path = "output/uvmforge_metrics.json"
    validation_report_json_path = "output/validation_report.json"
    validation_report_md_path = "output/validation_report.md"
    
    metrics_data = {}
    if os.path.exists(metrics_path):
        with open(metrics_path, "r", encoding="utf-8") as f:
            metrics_data = json.load(f)

    # Save JSON report
    report_json = {
        "processed_designs": processed_designs,
        "skipped_designs": skipped_designs,
        "metrics": metrics_data,
        "details": validation_results
    }
    
    os.makedirs("output", exist_ok=True)
    with open(validation_report_json_path, "w", encoding="utf-8") as f:
        json.dump(report_json, f, indent=4)
        
    # Generate Markdown report
    md_lines = [
        "# Phase 3: UVMForge Validation Report",
        "",
        "## Summary Metrics",
        f"- **First-Pass Success Rate**: {metrics_data.get('first_pass_rate', 0.0)}%",
        f"- **Overall Success Rate**: {metrics_data.get('overall_success_rate', 0.0)}%",
        f"- **Average Repair Iterations**: {metrics_data.get('avg_repair_iterations', 0.0)}",
        f"- **First-Pass Successes (Files)**: {metrics_data.get('first_pass_success', 0)}",
        f"- **Repair Successes (Files)**: {metrics_data.get('repair_success', 0)}",
        f"- **Failures (Files)**: {metrics_data.get('failures', 0)}",
        "",
        "## Design Checklist",
        "| Design | Status | Details |",
        "| :--- | :--- | :--- |"
    ]
    
    for design, res in validation_results.items():
        status = res["status"].upper()
        if status == "PASSED":
            badge = "🟢 PASSED"
            details = f"{res.get('files_count')} testbench files generated and validated"
        elif status == "SKIPPED":
            badge = "🟡 SKIPPED"
            details = res.get("reason")
        else:
            badge = "🔴 FAILED"
            details = res.get("error")
        md_lines.append(f"| **{design.upper()}** | {badge} | {details} |")
        
    md_lines.extend([
        "",
        "## Skipped Reference Designs",
        "The following designs do not currently have specification plans or JSON fixtures:",
        ", ".join(f"`{d}`" for d in skipped_designs)
    ])
    
    with open(validation_report_md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))
        
    print("\n" + "=" * 60)
    print("Validation Completed!")
    print(f"JSON report written to: {validation_report_json_path}")
    print(f"Markdown report written to: {validation_report_md_path}")
    print("=" * 60)


if __name__ == "__main__":
    run_validation()
