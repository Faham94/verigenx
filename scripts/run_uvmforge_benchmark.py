"""
UVMForge Benchmark Script.
Runs UVMForge on UART, SPI, and I2C, measuring compile success rate
and repair statistics.
"""
import os
import json
import shutil
import sys

# Ensure VeriGenX is in the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from VeriGenX.agents.uvmforge.generator import UVMForgeGenerator
from VeriGenX.agents.archweaver.dag_builder import DAGBuilder
from VeriGenX.agents.uvmforge.metrics import update_metrics


def run_benchmark():
    print("=" * 60)
    print("Running UVMForge Benchmark on UART, SPI, and I2C...")
    print("=" * 60)
    
    # Clean previous compile reports and attempt logs for a clean benchmark run
    report_path = "generated_uvm/compile_report.json"
    attempts_path = "output/repair_attempts.json"
    
    if os.path.exists(report_path):
        try:
            os.remove(report_path)
        except Exception:
            pass
            
    if os.path.exists(attempts_path):
        try:
            os.remove(attempts_path)
        except Exception:
            pass

    designs = ["uart", "spi", "i2c"]
    generator = UVMForgeGenerator()
    builder = DAGBuilder()
    
    results = {}
    
    for design in designs:
        print(f"\n[Benchmark] Processing design: {design}...")
        test_plan_path = f"test_plans/{design}_test_plan.json"
        
        if not os.path.exists(test_plan_path):
            print(f"[Error] Test plan path not found for {design}: {test_plan_path}")
            continue
            
        try:
            with open(test_plan_path, "r", encoding="utf-8") as f:
                test_plan = json.load(f)
                
            # Build DAG
            dag = builder.build_from_test_plan(test_plan_dict=test_plan)
            
            # Generate UVM testbench
            files = generator.generate_all(test_plan, dag)
            print(f"[Benchmark] Generated {len(files)} files for {design}.")
            results[design] = {
                "status": "success",
                "files_count": len(files)
            }
        except Exception as e:
            print(f"[Benchmark] Failed to process {design}: {e}")
            results[design] = {
                "status": "failed",
                "error": str(e)
            }

    # Retrieve metrics
    update_metrics()
    
    metrics_path = "output/uvmforge_metrics.json"
    benchmark_report_path = "output/uvmforge_benchmark_report.json"
    
    benchmark_report = {
        "benchmark_results": results,
        "metrics": {}
    }
    
    if os.path.exists(metrics_path):
        with open(metrics_path, "r", encoding="utf-8") as f:
            benchmark_report["metrics"] = json.load(f)
            
    os.makedirs("output", exist_ok=True)
    with open(benchmark_report_path, "w", encoding="utf-8") as f:
        json.dump(benchmark_report, f, indent=4)
        
    print("\n" + "=" * 60)
    print("Benchmark Report Summary:")
    print(f"Report saved to: {benchmark_report_path}")
    print("=" * 60)
    print(json.dumps(benchmark_report, indent=4))
    print("=" * 60)


if __name__ == "__main__":
    run_benchmark()
