"""
UVMForge Metrics Tracker.
Reads compile_report.json and repair_attempts.json, aggregates statistics,
and writes to output/uvmforge_metrics.json.
"""
import os
import json

def update_metrics():
    report_path = "generated_uvm/compile_report.json"
    attempts_path = "output/repair_attempts.json"
    metrics_path = "output/uvmforge_metrics.json"
    
    total_files = 0
    first_pass_success = 0
    repair_success = 0
    failures = 0
    
    # 1. Read compile report
    if os.path.exists(report_path):
        try:
            with open(report_path, "r", encoding="utf-8") as f:
                report_data = json.load(f)
            for design, data in report_data.items():
                for filename, file_info in data.get("files", {}).items():
                    total_files += 1
                    first_attempt = file_info.get("first_attempt", False)
                    status = file_info.get("status", "failed")
                    
                    if first_attempt and status == "passed":
                        first_pass_success += 1
                    elif not first_attempt and status == "passed":
                        repair_success += 1
                    else:
                        failures += 1
        except Exception as e:
            print(f"Error reading compile report for metrics: {e}")

    # 2. Read repair attempts logs
    total_attempts = 0
    repaired_files_count = 0
    if os.path.exists(attempts_path):
        try:
            with open(attempts_path, "r", encoding="utf-8") as f:
                attempts_data = json.load(f)
            for attempt_info in attempts_data:
                total_attempts += attempt_info.get("attempts", 0)
                repaired_files_count += 1
        except Exception as e:
            print(f"Error reading repair attempts for metrics: {e}")
            
    # Calculate rates
    first_pass_rate = (first_pass_success / total_files * 100) if total_files > 0 else 0.0
    overall_success_rate = ((first_pass_success + repair_success) / total_files * 100) if total_files > 0 else 0.0
    avg_repair_iterations = (total_attempts / repaired_files_count) if repaired_files_count > 0 else 0.0
    
    # Read existing total_runs if metrics file exists
    total_runs = 0
    if os.path.exists(metrics_path):
        try:
            with open(metrics_path, "r", encoding="utf-8") as f:
                existing_metrics = json.load(f)
                total_runs = existing_metrics.get("total_runs", 0)
        except Exception:
            pass
            
    total_runs += 1
    
    metrics = {
        "total_runs": total_runs,
        "first_pass_success": first_pass_success,
        "repair_success": repair_success,
        "failures": failures,
        "first_pass_rate": round(first_pass_rate, 2),
        "overall_success_rate": round(overall_success_rate, 2),
        "avg_repair_iterations": round(avg_repair_iterations, 2)
    }
    
    os.makedirs(os.path.dirname(os.path.abspath(metrics_path)), exist_ok=True)
    try:
        with open(metrics_path, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=4)
        print(f"\n[Metrics] Aggregate metrics saved to {metrics_path}")
    except Exception as e:
        print(f"Error saving metrics: {e}")
