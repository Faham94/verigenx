"""
VeriGenX — CoverHunter End-to-End Integration Test
Runs the closure feedback loop on a mock/loopback design.
"""
import os
import re
import pytest
from unittest.mock import patch, MagicMock
from VeriGenX.orchestrator import Orchestrator
from VeriGenX.state_bus import get_state_bus, PipelineState
from VeriGenX.agents.coverhunter.closure_loop import ClosureLoop

FIXTURE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "fixtures"))

class TestCoverHunterE2E:
    @patch("VeriGenX.agents.coverhunter.test_generator.get_ollama_client")
    def test_uart_coverage_closure_e2e(self, mock_get_client, tmp_path):
        """
        Runs the full CoverHunter loop on the UART design:
        1. Ingests spec and runs Phase 1-4 to generate baseline testbench.
        2. Starts CoverHunter closure loop.
        3. Mocks LLM response to generate targeted directed test classes dynamically.
        4. Verifies compilation, run execution, and coverage progress.
        """
        spec_path = os.path.join(FIXTURE_DIR, "uart", "uart_spec.txt")
        if not os.path.exists(spec_path):
            pytest.fail(f"Required spec fixture missing at: {spec_path}")

        # 1. Setup mock OllamaClient to return valid SystemVerilog directed test code
        mock_client = MagicMock()
        def mock_generate(prompt, model, temperature, max_tokens):
            # Extract gap name from prompt to generate matching class name
            match = re.search(r"(?:Target )?Gap Name/ID:\s*(\w+)", prompt)
            gap_name = match.group(1) if match else "FP_001"
            
            # Since the simulation reports hit counts on write(), we can even simulate hitting the point!
            # For example, if we want FP_001 (rx_data != 0) to get covered, our sequence item should randomize with tx_data != 0.
            # We can write a custom sequence block inside the generated test!
            return f"""
class uart_sequence_{gap_name} extends uvm_sequence #(uart_seq_item);
    `uvm_object_utils(uart_sequence_{gap_name})
    function new(string name = "uart_sequence_{gap_name}");
        super.new(name);
    endfunction
    virtual task body();
        req = uart_seq_item::type_id::create("req");
        start_item(req);
        if (!req.randomize()) begin
            `uvm_fatal("SEQ", "Randomization failed")
        end
        req.tx_data = 8'hAA;
        req.rx_data = 8'hAA;
        finish_item(req);
        #100;
    endtask
endclass

class uart_test_directed_{gap_name} extends uart_test_base;
    `uvm_component_utils(uart_test_directed_{gap_name})
    function new(string name = "uart_test_directed_{gap_name}", uvm_component parent = null);
        super.new(name, parent);
    endfunction
    virtual task run_phase(uvm_phase phase);
        uart_sequence_{gap_name} seq;
        phase.raise_objection(this);
        seq = uart_sequence_{gap_name}::type_id::create("seq");
        seq.start(env.agent.sequencer);
        phase.drop_objection(this);
    endtask
endclass
"""
        mock_client.generate.side_effect = mock_generate
        mock_get_client.return_value = mock_client

        # 2. Run the full Orchestrator pipeline up to Phase 4
        orchestrator = Orchestrator()
        state_bus = get_state_bus()
        state_bus.state = PipelineState()

        orchestrator.run_pipeline(spec_path, output_dir=str(tmp_path))

        # Check initial state after Phase 4
        state = state_bus.get_state()
        assert state.test_plan is not None
        assert state.simulation_results is not None
        
        initial_files = list(state.generated_files)
        initial_results = state.simulation_results
        
        # 3. Explicitly execute CoverHunter loop
        loop = ClosureLoop(max_iterations=3, convergence_threshold=0.1)
        final_results = loop.run_closure_loop(
            design_name="uart",
            test_plan=state.test_plan,
            initial_uvm_files=initial_files,
            base_run_dir=str(tmp_path)
        )

        # 4. Verify functional coverage increased or reached 100%
        final_coverage = final_results["coverage"]["functional_coverage"]
        assert final_coverage > 33.33  # Starts at 33.33% because only FP_003 is covered by baseline
        assert final_coverage >= 85.0 or final_coverage == 100.0
