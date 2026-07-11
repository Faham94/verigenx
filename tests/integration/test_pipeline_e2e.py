"""
VeriGenX — End-to-End Pipeline Integration Test
Executes the full SpecMind -> ArchWeaver workflow on real spec fixtures.
"""
import os
import json
import pytest
from VeriGenX.orchestrator import Orchestrator
from VeriGenX.state_bus import get_state_bus

FIXTURE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "fixtures"))


@pytest.mark.parametrize("design", ["uart", "spi", "i2c", "axi_lite", "fifo"])
def test_full_pipeline_e2e_for_design(design, tmp_path):
    """
    Run the full end-to-end pipeline:
    1. Ingest spec text from tests/fixtures/<design>/<design>_spec.txt
    2. Run SpecMind chunking, embedding, extraction (fallback heuristics)
    3. Verify generated test plan JSON matches requirements
    4. Run ArchWeaver component derivation and topological sort
    5. Verify final resolved UVM dependency order (interface first, top last)
    """
    spec_path = os.path.join(FIXTURE_DIR, design, f"{design}_spec.txt")
    if not os.path.exists(spec_path):
        pytest.fail(f"Required spec fixture missing at: {spec_path}")

    # Initialize orchestrator and run the pipeline
    from VeriGenX.state_bus import PipelineState
    orchestrator = Orchestrator()
    state_bus    = get_state_bus()
    state_bus.state = PipelineState()

    # We mock or bypass ChromaDB if it's not writable, orchestrator handles this
    orchestrator.run_pipeline(spec_path, output_dir=str(tmp_path))

    # Read output state
    state = state_bus.get_state()
    assert state.test_plan is not None
    assert state.dependency_graph is not None

    # Verify extracted test plan fields
    plan = state.test_plan
    assert plan["design_name"] == design
    assert "signals" in plan
    assert "fsm_states" in plan
    assert "register_map" in plan
    assert "timing_constraints" in plan
    assert "functional_points" in plan
    assert "protocol_handshake_rules" in plan
    assert "firmware_programming_model" in plan

    # Verify extracted items are not empty (due to heuristic fallback)
    assert len(plan["signals"]) > 0
    assert len(plan["fsm_states"]) > 0
    if design != "fifo":
        assert len(plan["register_map"]) > 0
        # Check that registers contain required access & reset_value fields (Bug #2 check)
        for reg in plan["register_map"]:
            assert "access" in reg
            assert "reset_value" in reg

    # Verify UVM dependencies and topological sort (Bug #9 check)
    dag = state.dependency_graph
    assert len(dag["components"]) >= 12
    assert "top" in dag["components"]

    # Verify interface has no dependencies
    assert dag["dependencies"]["interface"] == []
    # Verify sequence_item/scoreboard/coverage do not depend on interface
    assert "interface" not in dag["dependencies"]["sequence_item"]
    assert "interface" not in dag["dependencies"]["scoreboard"]
    assert "interface" not in dag["dependencies"]["coverage"]

    # Verify top is strictly last (or depends on all tests to stay last)
    from VeriGenX.agents.archweaver.resolver import Resolver
    order = Resolver().resolve(dag)
    assert order[0] == "interface"
    assert order[-1] == "top"
