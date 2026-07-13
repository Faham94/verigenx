import os
import shutil
import pytest
from unittest.mock import patch
from VeriGenX.agents.simrunner import SimRunner
from VeriGenX.agents.uvmforge.generator import UVMForgeGenerator
from VeriGenX.agents.archweaver.dag_builder import DAGBuilder

@pytest.mark.parametrize("design", ["uart", "spi", "i2c", "fifo"])
def test_simrunner_e2e(design, tmp_path):
    """
    Integration test executing SimRunner end-to-end:
    1. Generates real UVM testbench files using Phase 3 generator.
    2. Invokes SimRunner compilation on the topologically sorted files + mock library.
    3. Runs base & directed tests, capturing execution reports and verification coverage.
    """
    # Create mock plan for the design
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    spec_path = os.path.join(base_dir, "tests", "fixtures", design, f"{design}_spec.txt")
    if not os.path.exists(spec_path):
        pytest.skip(f"Spec fixture not found for {design}")

    # Generate plan and DAG
    from VeriGenX.agents.specmind.test_plan import TestPlanGenerator
    from VeriGenX.agents.specmind.ingestion import DocumentIngestor
    
    text = DocumentIngestor().ingest(spec_path)["text"]
    test_plan = TestPlanGenerator().generate(text)
    
    dag = DAGBuilder().build_from_test_plan(test_plan_dict=test_plan)

    # Compile files in a temporary dir
    generated_dir = tmp_path / "generated_uvm"
    os.makedirs(generated_dir, exist_ok=True)

    # Mock generator save path
    with patch("VeriGenX.agents.uvmforge.generator.GENERATED_UVM_DIR", str(generated_dir)):
        generator = UVMForgeGenerator()
        uvm_files = generator.generate_all(test_plan, dag)

    # Verify we got 12 files
    assert len(uvm_files) == 12

    # Instantiate SimRunner and execute
    runner = SimRunner()
    if not runner.compiler.is_verilator_available():
        pytest.skip("Verilator is not installed/available on this system.")

    run_dir = tmp_path / "sim_run"
    results = runner.run_simulations(design, test_plan, uvm_files, base_run_dir=str(run_dir))

    # Verify compilation succeeded
    assert results["compiled"] is True
    assert results["status"] == "passed"
    
    # Check that both tests ran and passed
    assert len(results["tests"]) == 2
    for tname, tres in results["tests"].items():
        assert tres["success"] is True
        assert tres["status"] == "passed"
        assert os.path.exists(tres["vcd_path"])
        # Coverage file should be recorded
        assert "line_coverage" in tres["coverage"]
        assert "functional_coverage" in tres["coverage"]
