"""
Integration Tests — UVMForge End-to-End Pipeline
Runs full pipeline on UART, SPI, and I2C spec fixtures.
Assures 12 SystemVerilog files are produced and non-empty.
"""
import os
import pytest

from VeriGenX.orchestrator import Orchestrator
from VeriGenX.state_bus import get_state_bus, PipelineState
from VeriGenX.config import GENERATED_UVM_DIR

FIXTURE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "fixtures"))


@pytest.mark.parametrize("design", ["uart", "spi", "i2c"])
def test_uvmforge_pipeline_e2e(design, tmp_path):
    """
    Run the full end-to-end pipeline:
    1. SpecMind extraction (heuristics)
    2. ArchWeaver DAG resolution
    3. UVMForge code generation
    4. Assert 12 UVM SystemVerilog files are written and non-empty
    """
    spec_path = os.path.join(FIXTURE_DIR, design, f"{design}_spec.txt")
    if not os.path.exists(spec_path):
        pytest.fail(f"Required spec fixture missing at: {spec_path}")

    # Initialize state
    state_bus = get_state_bus()
    state_bus.state = PipelineState()

    # We patch GENERATED_UVM_DIR to write to tmp_path to keep workspace clean during test
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("VeriGenX.agents.uvmforge.generator.GENERATED_UVM_DIR", str(tmp_path))
        
        orchestrator = Orchestrator()
        orchestrator.run_pipeline(spec_path)
        
        # Verify state bus contains generated files
        state = state_bus.get_state()
        assert state.generated_files is not None
        assert len(state.generated_files) >= 12
        
        # Assert each file exists and is non-empty
        for filepath in state.generated_files:
            assert os.path.exists(filepath)
            assert os.path.getsize(filepath) > 0
            
            # Review and print basic info about the file content
            filename = os.path.basename(filepath)
            print(f"Verified generated file: {filename} ({os.path.getsize(filepath)} bytes)")
