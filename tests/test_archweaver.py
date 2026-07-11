"""
VeriGenX — Phase 2 ArchWeaver Test Suite (Expanded)
Covers all 9 Phase 2 bugs + original tests.

Test Classes:
  1. TestDAGBuilderFromDict      — Bug #1: in-memory dict input
  2. TestDAGBuilderDynamic       — Bug #2: components derived from plan
  3. TestUVMEdgeCorrectness      — Bug #9: correct UVM dependency topology
  4. TestResolverSimple          — topological sort + cycle detection
  5. TestDOTExport               — DOT file generation
  6. TestConflictDetectorSignals — Bug #3: real signals passed in
  7. TestInterfaceConsistency    — Bug #4: FR-02.5 width/direction checks
  8. TestLLMResolverIntegration  — Bug #5: LLM resolver wired
  9. TestDynamicRegeneration     — Bug #6: auto-regen on file change
  10. TestMultiProtocolDesigns   — Bug #7: SPI/I2C/AXI-Lite/FIFO
  11. TestFullPipelineIntegration — Bug #8: SpecMind → ArchWeaver E2E
  12. TestOrchestratorStatePassing — Bug #1: orchestrator state flow
  13. TestBenchmarkFiveDesigns   — parametrized benchmark
"""
import os
import json
import time
import pytest
import tempfile
from pathlib import Path


# ================================================================== #
#  1. DAGBuilder — accepts in-memory dict (Bug #1)                    #
# ================================================================== #

class TestDAGBuilderFromDict:
    """Bug #1: build_from_test_plan must accept a dict, not only a file."""

    def test_accepts_dict_directly(self, uart_test_plan):
        from VeriGenX.agents.archweaver.dag_builder import DAGBuilder
        dag = DAGBuilder().build_from_test_plan(test_plan_dict=uart_test_plan)
        assert isinstance(dag, dict)

    def test_design_name_from_dict(self, uart_test_plan):
        from VeriGenX.agents.archweaver.dag_builder import DAGBuilder
        dag = DAGBuilder().build_from_test_plan(test_plan_dict=uart_test_plan)
        assert dag["design_name"] == "uart"

    def test_signals_propagated_to_dag(self, uart_test_plan):
        from VeriGenX.agents.archweaver.dag_builder import DAGBuilder
        dag = DAGBuilder().build_from_test_plan(test_plan_dict=uart_test_plan)
        assert len(dag["signals"]) == 4

    def test_file_path_still_works(self, test_plan_file):
        from VeriGenX.agents.archweaver.dag_builder import DAGBuilder
        dag = DAGBuilder().build_from_test_plan(test_plan_path=test_plan_file)
        assert "components" in dag

    def test_dict_overrides_path(self, uart_test_plan, test_plan_file):
        """Dict takes priority over file path."""
        from VeriGenX.agents.archweaver.dag_builder import DAGBuilder
        uart_test_plan["design_name"] = "custom_design"
        dag = DAGBuilder().build_from_test_plan(
            test_plan_path=test_plan_file,
            test_plan_dict=uart_test_plan,
        )
        assert dag["design_name"] == "custom_design"

    def test_dag_contains_filenames(self, uart_test_plan):
        from VeriGenX.agents.archweaver.dag_builder import DAGBuilder
        dag = DAGBuilder().build_from_test_plan(test_plan_dict=uart_test_plan)
        assert "component_filenames" in dag
        assert all(fn.endswith(".sv") for fn in dag["component_filenames"].values())


# ================================================================== #
#  2. Dynamic component derivation (Bug #2)                           #
# ================================================================== #

class TestDAGBuilderDynamic:
    """Bug #2: component set and edges must be derived from plan, not hardcoded."""

    def test_12_standard_components_present(self, uart_test_plan):
        from VeriGenX.agents.archweaver.dag_builder import DAGBuilder
        dag = DAGBuilder().build_from_test_plan(test_plan_dict=uart_test_plan)
        assert len(dag["components"]) == 12

    def test_extra_test_added_for_many_fps(self):
        from VeriGenX.agents.archweaver.dag_builder import DAGBuilder
        plan = {
            "design_name": "complex",
            "signals": [],
            "fsm_states": [],
            "register_map": [],
            "functional_points": [
                {"id": f"FP_{i:03d}", "description": f"fp {i}"}
                for i in range(6)        # > 4 → test_random added
            ],
        }
        dag = DAGBuilder().build_from_test_plan(test_plan_dict=plan)
        assert "test_random" in dag["components"]

    def test_design_name_spi(self, spi_test_plan):
        from VeriGenX.agents.archweaver.dag_builder import DAGBuilder
        dag = DAGBuilder().build_from_test_plan(test_plan_dict=spi_test_plan)
        assert dag["design_name"] == "spi"

    def test_filenames_use_design_prefix(self, spi_test_plan):
        from VeriGenX.agents.archweaver.dag_builder import DAGBuilder
        dag = DAGBuilder().build_from_test_plan(test_plan_dict=spi_test_plan)
        for fn in dag["component_filenames"].values():
            assert fn.startswith("spi_")

    def test_functional_points_in_dag(self, uart_test_plan):
        from VeriGenX.agents.archweaver.dag_builder import DAGBuilder
        dag = DAGBuilder().build_from_test_plan(test_plan_dict=uart_test_plan)
        assert len(dag["functional_points"]) == 2


# ================================================================== #
#  3. Correct UVM edge topology (Bug #9)                              #
# ================================================================== #

class TestUVMEdgeCorrectness:
    """Bug #9: sequence_item/sequence/scoreboard/coverage must NOT depend on interface."""

    @pytest.fixture(autouse=True)
    def dag(self, uart_test_plan):
        from VeriGenX.agents.archweaver.dag_builder import DAGBuilder
        self._dag = DAGBuilder().build_from_test_plan(test_plan_dict=uart_test_plan)
        return self._dag

    def test_sequence_item_has_no_interface_dep(self):
        deps = self._dag["dependencies"]["sequence_item"]
        assert "interface" not in deps, (
            f"Bug #9: sequence_item should NOT depend on interface. Got: {deps}"
        )

    def test_sequence_has_no_interface_dep(self):
        deps = self._dag["dependencies"]["sequence"]
        assert "interface" not in deps, (
            f"Bug #9: sequence should NOT depend on interface. Got: {deps}"
        )

    def test_scoreboard_has_no_interface_dep(self):
        deps = self._dag["dependencies"]["scoreboard"]
        assert "interface" not in deps, (
            f"Bug #9: scoreboard should NOT depend on interface. Got: {deps}"
        )

    def test_coverage_has_no_interface_dep(self):
        deps = self._dag["dependencies"]["coverage"]
        assert "interface" not in deps, (
            f"Bug #9: coverage should NOT depend on interface. Got: {deps}"
        )

    def test_driver_depends_on_interface(self):
        assert "interface" in self._dag["dependencies"]["driver"]

    def test_monitor_depends_on_interface(self):
        assert "interface" in self._dag["dependencies"]["monitor"]

    def test_sequence_depends_on_sequence_item(self):
        assert "sequence_item" in self._dag["dependencies"]["sequence"]

    def test_scoreboard_depends_on_sequence_item(self):
        assert "sequence_item" in self._dag["dependencies"]["scoreboard"]

    def test_interface_has_no_deps(self):
        assert self._dag["dependencies"]["interface"] == []

    def test_sequence_item_has_no_deps(self):
        assert self._dag["dependencies"]["sequence_item"] == []


# ================================================================== #
#  4. Resolver — topological sort                                     #
# ================================================================== #

class TestResolverSimple:

    @pytest.fixture(autouse=True)
    def setup(self, uart_test_plan):
        from VeriGenX.agents.archweaver.dag_builder import DAGBuilder
        from VeriGenX.agents.archweaver.resolver import Resolver
        self.dag      = DAGBuilder().build_from_test_plan(test_plan_dict=uart_test_plan)
        self.resolver = Resolver()

    def test_resolve_returns_list(self):
        assert isinstance(self.resolver.resolve(self.dag), list)

    def test_resolve_contains_all_components(self):
        order = self.resolver.resolve(self.dag)
        assert set(order) == set(self.dag["components"])

    def test_interface_comes_before_driver(self):
        order = self.resolver.resolve(self.dag)
        assert order.index("interface") < order.index("driver")

    def test_interface_comes_before_monitor(self):
        order = self.resolver.resolve(self.dag)
        assert order.index("interface") < order.index("monitor")

    def test_sequence_item_before_sequence(self):
        order = self.resolver.resolve(self.dag)
        assert order.index("sequence_item") < order.index("sequence")

    def test_sequence_item_before_scoreboard(self):
        order = self.resolver.resolve(self.dag)
        assert order.index("sequence_item") < order.index("scoreboard")

    def test_agent_before_env(self):
        order = self.resolver.resolve(self.dag)
        assert order.index("agent") < order.index("env")

    def test_env_before_test_base(self):
        order = self.resolver.resolve(self.dag)
        assert order.index("env") < order.index("test_base")

    def test_test_base_before_top(self):
        order = self.resolver.resolve(self.dag)
        assert order.index("test_base") < order.index("top")

    def test_cyclic_raises(self):
        bad_dag = {
            "components":   ["a", "b"],
            "dependencies": {"a": ["b"], "b": ["a"]},
        }
        with pytest.raises(Exception, match="Circular"):
            self.resolver.resolve(bad_dag)

    def test_generation_order_has_filename(self):
        order = self.resolver.get_generation_order(self.dag)
        for item in order:
            assert "filename" in item
            assert item["filename"].endswith(".sv")


# ================================================================== #
#  5. DOT export                                                      #
# ================================================================== #

class TestDOTExport:

    def test_dot_file_created(self, tmp_path, uart_test_plan):
        from VeriGenX.agents.archweaver.dag_builder import DAGBuilder
        from VeriGenX.agents.archweaver.resolver import Resolver
        dag = DAGBuilder().build_from_test_plan(test_plan_dict=uart_test_plan)
        dot = str(tmp_path / "dag.dot")
        Resolver().export_dot(dag, dot)
        assert os.path.exists(dot)

    def test_dot_contains_components(self, tmp_path, uart_test_plan):
        from VeriGenX.agents.archweaver.dag_builder import DAGBuilder
        from VeriGenX.agents.archweaver.resolver import Resolver
        dag = DAGBuilder().build_from_test_plan(test_plan_dict=uart_test_plan)
        dot = str(tmp_path / "dag.dot")
        Resolver().export_dot(dag, dot)
        content = Path(dot).read_text()
        assert "interface" in content
        assert "driver" in content

    def test_dot_has_digraph_keyword(self, tmp_path, uart_test_plan):
        from VeriGenX.agents.archweaver.dag_builder import DAGBuilder
        from VeriGenX.agents.archweaver.resolver import Resolver
        dag = DAGBuilder().build_from_test_plan(test_plan_dict=uart_test_plan)
        dot = str(tmp_path / "dag.dot")
        Resolver().export_dot(dag, dot)
        assert "digraph" in Path(dot).read_text()

    def test_dot_design_name_in_comment(self, tmp_path, spi_test_plan):
        from VeriGenX.agents.archweaver.dag_builder import DAGBuilder
        from VeriGenX.agents.archweaver.resolver import Resolver
        dag = DAGBuilder().build_from_test_plan(test_plan_dict=spi_test_plan)
        dot = str(tmp_path / "spi.dot")
        Resolver().export_dot(dag, dot)
        assert "SPI" in Path(dot).read_text()


# ================================================================== #
#  6. ConflictDetector — real signals passed (Bug #3)                 #
# ================================================================== #

class TestConflictDetectorSignals:
    """Bug #3: detector must receive real signals, not empty list."""

    def test_no_conflicts_with_valid_plan(self, uart_test_plan):
        from VeriGenX.agents.archweaver.dag_builder import DAGBuilder
        from VeriGenX.agents.archweaver.conflict_detector import ConflictDetector
        dag       = DAGBuilder().build_from_test_plan(test_plan_dict=uart_test_plan)
        conflicts = ConflictDetector().detect_conflicts(dag, uart_test_plan)
        assert isinstance(conflicts, list)

    def test_duplicate_signal_detected(self, uart_test_plan):
        from VeriGenX.agents.archweaver.dag_builder import DAGBuilder
        from VeriGenX.agents.archweaver.conflict_detector import ConflictDetector
        # Inject a duplicate
        uart_test_plan["signals"].append({"name": "clk", "width": 1, "direction": "input"})
        dag       = DAGBuilder().build_from_test_plan(test_plan_dict=uart_test_plan)
        conflicts = ConflictDetector().detect_conflicts(dag, uart_test_plan)
        types     = [c["type"] for c in conflicts]
        assert "duplicate_signal" in types

    def test_empty_signals_no_false_duplicate(self):
        from VeriGenX.agents.archweaver.dag_builder import DAGBuilder
        from VeriGenX.agents.archweaver.conflict_detector import ConflictDetector
        plan = {"design_name": "empty", "signals": [], "fsm_states": [],
                "register_map": [], "functional_points": []}
        dag  = DAGBuilder().build_from_test_plan(test_plan_dict=plan)
        conflicts = ConflictDetector().detect_conflicts(dag, plan)
        dup_types = [c["type"] for c in conflicts if c["type"] == "duplicate_signal"]
        assert dup_types == []

    def test_detect_missing_dep_in_dag(self):
        from VeriGenX.agents.archweaver.conflict_detector import ConflictDetector
        bad_dag = {
            "components":   ["driver"],
            "dependencies": {"driver": ["interface"]},   # interface missing
        }
        plan      = {"signals": []}
        conflicts = ConflictDetector().detect_conflicts(bad_dag, plan)
        types     = [c["type"] for c in conflicts]
        assert "missing_dependency" in types


# ================================================================== #
#  7. Interface consistency — FR-02.5 (Bug #4)                       #
# ================================================================== #

class TestInterfaceConsistency:
    """Bug #4: FR-02.5 checks — width/direction validity and cross-consistency."""

    def _detect(self, signals):
        from VeriGenX.agents.archweaver.dag_builder import DAGBuilder
        from VeriGenX.agents.archweaver.conflict_detector import ConflictDetector
        plan = {"design_name": "t", "signals": signals,
                "fsm_states": [], "register_map": [], "functional_points": []}
        dag  = DAGBuilder().build_from_test_plan(test_plan_dict=plan)
        return ConflictDetector().detect_conflicts(dag, plan)

    def test_valid_signals_no_width_error(self):
        conflicts = self._detect([
            {"name": "clk", "width": 1, "direction": "input"},
        ])
        width_errs = [c for c in conflicts if c["type"] == "invalid_signal_width"]
        assert width_errs == []

    def test_zero_width_raises_error(self):
        conflicts = self._detect([{"name": "bad", "width": 0, "direction": "input"}])
        types     = [c["type"] for c in conflicts]
        assert "invalid_signal_width" in types

    def test_negative_width_raises_error(self):
        conflicts = self._detect([{"name": "bad", "width": -1, "direction": "input"}])
        types     = [c["type"] for c in conflicts]
        assert "invalid_signal_width" in types

    def test_invalid_direction_raises_error(self):
        conflicts = self._detect([
            {"name": "sig", "width": 1, "direction": "bidirectional"}
        ])
        types = [c["type"] for c in conflicts]
        assert "invalid_signal_direction" in types

    def test_valid_inout_direction_ok(self):
        conflicts = self._detect([{"name": "sda", "width": 1, "direction": "inout"}])
        dir_errs  = [c for c in conflicts if c["type"] == "invalid_signal_direction"]
        assert dir_errs == []

    def test_inconsistent_width_flagged(self):
        conflicts = self._detect([
            {"name": "data", "width": 8,  "direction": "input"},
            {"name": "data", "width": 16, "direction": "input"},
        ])
        types = [c["type"] for c in conflicts]
        assert "inconsistent_signal_width" in types

    def test_inconsistent_direction_flagged(self):
        conflicts = self._detect([
            {"name": "bus", "width": 8, "direction": "input"},
            {"name": "bus", "width": 8, "direction": "output"},
        ])
        types = [c["type"] for c in conflicts]
        assert "inconsistent_signal_direction" in types

    def test_all_axi_signals_valid(self, axi_lite_test_plan):
        from VeriGenX.agents.archweaver.dag_builder import DAGBuilder
        from VeriGenX.agents.archweaver.conflict_detector import ConflictDetector
        dag       = DAGBuilder().build_from_test_plan(test_plan_dict=axi_lite_test_plan)
        conflicts = ConflictDetector().detect_conflicts(dag, axi_lite_test_plan)
        width_errs = [c for c in conflicts if "invalid_signal_width" in c["type"]]
        dir_errs   = [c for c in conflicts if "invalid_signal_direction" in c["type"]]
        assert width_errs == []
        assert dir_errs   == []


# ================================================================== #
#  8. LLM resolver integration (Bug #5)                               #
# ================================================================== #

class TestLLMResolverIntegration:
    """Bug #5: LLMConflictResolver must be callable and return augmented results."""

    def test_resolve_returns_list(self):
        from VeriGenX.agents.archweaver.llm_conflict_resolver import LLMConflictResolver
        resolver  = LLMConflictResolver()
        conflicts = [
            {"type": "duplicate_signal", "severity": "error",
             "description": "dup", "suggestion": "rename"},
        ]
        resolved = resolver.resolve(conflicts, spec_context="UART spec")
        assert isinstance(resolved, list)
        assert len(resolved) == len(conflicts)

    def test_resolved_has_llm_resolution_key(self):
        from VeriGenX.agents.archweaver.llm_conflict_resolver import LLMConflictResolver
        conflicts = [
            {"type": "missing_dependency", "severity": "error",
             "description": "driver missing interface", "suggestion": "add interface"},
        ]
        resolved = LLMConflictResolver().resolve(conflicts, spec_context="SPI spec")
        assert "llm_resolution" in resolved[0]

    def test_empty_conflicts_returns_empty(self):
        from VeriGenX.agents.archweaver.llm_conflict_resolver import LLMConflictResolver
        resolved = LLMConflictResolver().resolve([], spec_context="")
        assert resolved == []

    def test_fallback_resolution_when_no_llm(self):
        """When Ollama unavailable, llm_resolution must still be populated."""
        from VeriGenX.agents.archweaver.llm_conflict_resolver import LLMConflictResolver
        conflicts = [{"type": "t", "severity": "warning", "description": "d", "suggestion": "s"}]
        resolved  = LLMConflictResolver().resolve(conflicts, spec_context="spec")
        assert resolved[0]["llm_resolution"] != ""


# ================================================================== #
#  9. Dynamic DAG regeneration (Bug #6)                               #
# ================================================================== #

class TestDynamicRegeneration:
    """Bug #6: regenerate_on_change must rebuild DAG+DOT when file changes."""

    def test_regenerate_on_change_exists(self):
        from VeriGenX.agents.archweaver.resolver import Resolver
        assert hasattr(Resolver(), "regenerate_on_change")

    def test_regenerate_rebuilds_on_mtime_change(self, tmp_path, uart_test_plan):
        from VeriGenX.agents.archweaver.resolver import Resolver

        plan_file = tmp_path / "watch_test.json"
        plan_file.write_text(json.dumps(uart_test_plan), encoding="utf-8")
        dot_out   = str(tmp_path / "watch.dot")

        resolver = Resolver()
        # Run for 1 rebuild then stop
        resolver.regenerate_on_change(
            str(plan_file),
            dot_output=dot_out,
            poll_interval=0.1,
            max_iterations=1,
        )
        assert os.path.exists(dot_out)

    def test_regenerate_does_nothing_if_no_change(self, tmp_path, uart_test_plan):
        """When file doesn't change, DOT should be created on first detection."""
        from VeriGenX.agents.archweaver.resolver import Resolver

        plan_file = tmp_path / "static.json"
        plan_file.write_text(json.dumps(uart_test_plan), encoding="utf-8")
        dot_out   = str(tmp_path / "static.dot")

        resolver = Resolver()
        resolver.regenerate_on_change(
            str(plan_file),
            dot_output=dot_out,
            poll_interval=0.1,
            max_iterations=1,
        )
        assert os.path.exists(dot_out)


# ================================================================== #
#  10. Multi-protocol testing (Bug #7)                                #
# ================================================================== #

class TestMultiProtocolDesigns:
    """Bug #7: all 5 reference protocols must produce valid DAGs."""

    @pytest.mark.parametrize("plan_fixture", [
        "uart_test_plan", "spi_test_plan", "i2c_test_plan",
        "axi_lite_test_plan", "fifo_test_plan",
    ])
    def test_dag_builds_successfully(self, plan_fixture, request):
        from VeriGenX.agents.archweaver.dag_builder import DAGBuilder
        plan = request.getfixturevalue(plan_fixture)
        dag  = DAGBuilder().build_from_test_plan(test_plan_dict=plan)
        assert "components" in dag

    @pytest.mark.parametrize("plan_fixture", [
        "uart_test_plan", "spi_test_plan", "i2c_test_plan",
        "axi_lite_test_plan", "fifo_test_plan",
    ])
    def test_topological_sort_succeeds(self, plan_fixture, request):
        from VeriGenX.agents.archweaver.dag_builder import DAGBuilder
        from VeriGenX.agents.archweaver.resolver import Resolver
        plan  = request.getfixturevalue(plan_fixture)
        dag   = DAGBuilder().build_from_test_plan(test_plan_dict=plan)
        order = Resolver().resolve(dag)
        assert len(order) == len(dag["components"])

    @pytest.mark.parametrize("plan_fixture", [
        "uart_test_plan", "spi_test_plan", "i2c_test_plan",
        "axi_lite_test_plan", "fifo_test_plan",
    ])
    def test_no_conflicts_in_clean_plan(self, plan_fixture, request):
        from VeriGenX.agents.archweaver.dag_builder import DAGBuilder
        from VeriGenX.agents.archweaver.conflict_detector import ConflictDetector
        plan      = request.getfixturevalue(plan_fixture)
        dag       = DAGBuilder().build_from_test_plan(test_plan_dict=plan)
        conflicts = ConflictDetector().detect_conflicts(dag, plan)
        errors    = [c for c in conflicts if c["severity"] == "error"]
        assert errors == [], f"Unexpected errors in {plan_fixture}: {errors}"

    @pytest.mark.parametrize("plan_fixture", [
        "uart_test_plan", "spi_test_plan", "i2c_test_plan",
        "axi_lite_test_plan", "fifo_test_plan",
    ])
    def test_dot_exported_for_each_protocol(self, plan_fixture, request, tmp_path):
        from VeriGenX.agents.archweaver.dag_builder import DAGBuilder
        from VeriGenX.agents.archweaver.resolver import Resolver
        plan    = request.getfixturevalue(plan_fixture)
        dag     = DAGBuilder().build_from_test_plan(test_plan_dict=plan)
        dot_out = str(tmp_path / f"{plan['design_name']}.dot")
        Resolver().export_dot(dag, dot_out)
        assert os.path.exists(dot_out)


# ================================================================== #
#  11. Full pipeline integration (Bug #8)                             #
# ================================================================== #

class TestFullPipelineIntegration:
    """Bug #8: SpecMind → ArchWeaver end-to-end for all 5 reference designs."""

    @pytest.mark.parametrize("plan_fixture", [
        "uart_test_plan", "spi_test_plan", "i2c_test_plan",
        "axi_lite_test_plan", "fifo_test_plan",
    ])
    def test_specmind_to_archweaver_pipeline(self, plan_fixture, request, tmp_path):
        """
        Simulate the full SpecMind → ArchWeaver pipeline:
        1. Start with a test plan (simulating SpecMind output)
        2. Build DAG from that plan
        3. Resolve topological order
        4. Detect conflicts
        5. Export DOT
        """
        from VeriGenX.agents.archweaver.dag_builder import DAGBuilder
        from VeriGenX.agents.archweaver.resolver import Resolver
        from VeriGenX.agents.archweaver.conflict_detector import ConflictDetector

        plan      = request.getfixturevalue(plan_fixture)
        design    = plan["design_name"]

        # Step 1 → 2: DAG from in-memory plan (simulates state bus handoff)
        dag       = DAGBuilder().build_from_test_plan(test_plan_dict=plan)
        assert dag["design_name"] == design

        # Step 3: topological sort — no exception
        resolver  = Resolver()
        order     = resolver.resolve(dag)
        assert len(order) == len(dag["components"])

        # Step 4: conflict detection with real signals
        detector  = ConflictDetector()
        conflicts = detector.detect_conflicts(dag, plan)
        errors    = [c for c in conflicts if c["severity"] == "error"]
        assert errors == [], f"Pipeline errors for {design}: {errors}"

        # Step 5: DOT export
        dot       = str(tmp_path / f"{design}_pipeline.dot")
        resolver.export_dot(dag, dot)
        assert os.path.exists(dot)

    def test_generation_order_interface_first_for_all(self, all_reference_plans):
        from VeriGenX.agents.archweaver.dag_builder import DAGBuilder
        from VeriGenX.agents.archweaver.resolver import Resolver
        for plan in all_reference_plans:
            dag   = DAGBuilder().build_from_test_plan(test_plan_dict=plan)
            order = Resolver().resolve(dag)
            assert order[0] == "interface", (
                f"interface must be first for {plan['design_name']}, got {order[0]}"
            )

    def test_top_is_last_in_all_designs(self, all_reference_plans):
        from VeriGenX.agents.archweaver.dag_builder import DAGBuilder
        from VeriGenX.agents.archweaver.resolver import Resolver
        for plan in all_reference_plans:
            dag   = DAGBuilder().build_from_test_plan(test_plan_dict=plan)
            order = Resolver().resolve(dag)
            assert order[-1] == "top", (
                f"top must be last for {plan['design_name']}, got {order[-1]}"
            )


# ================================================================== #
#  12. Orchestrator state passing (Bug #1)                            #
# ================================================================== #

class TestOrchestratorStatePassing:
    """Bug #1: ArchWeaver must receive test plan from in-memory state, not file."""

    def test_run_archweaver_from_plan_returns_dag(self, uart_test_plan):
        from VeriGenX.orchestrator import Orchestrator
        orch = Orchestrator()
        dag  = orch.run_archweaver_from_plan(uart_test_plan)
        assert dag is not None
        assert "components" in dag

    def test_orchestrator_uses_in_memory_design_name(self, spi_test_plan):
        from VeriGenX.orchestrator import Orchestrator
        orch = Orchestrator()
        dag  = orch.run_archweaver_from_plan(spi_test_plan)
        assert dag["design_name"] == "spi"

    def test_orchestrator_does_not_crash_without_llm(self, uart_test_plan):
        """Orchestrator must handle Ollama being offline gracefully."""
        from VeriGenX.orchestrator import Orchestrator
        orch = Orchestrator()
        try:
            dag = orch.run_archweaver_from_plan(uart_test_plan)
            assert dag is not None
        except SystemExit:
            pytest.fail("Orchestrator should not call sys.exit on LLM unavailability")


# ================================================================== #
#  13. Benchmark — all 5 reference designs (Bug #7)                  #
# ================================================================== #

@pytest.mark.parametrize("plan_fixture,expected_signals", [
    ("uart_test_plan",     4),
    ("spi_test_plan",      6),
    ("i2c_test_plan",      4),
    ("axi_lite_test_plan", 19),
    ("fifo_test_plan",     8),
])
class TestBenchmarkFiveDesigns:

    def test_signal_count(self, plan_fixture, expected_signals, request):
        plan = request.getfixturevalue(plan_fixture)
        assert len(plan["signals"]) == expected_signals

    def test_dag_has_12_components(self, plan_fixture, expected_signals, request):
        from VeriGenX.agents.archweaver.dag_builder import DAGBuilder
        plan = request.getfixturevalue(plan_fixture)
        dag  = DAGBuilder().build_from_test_plan(test_plan_dict=plan)
        assert len(dag["components"]) >= 12

    def test_topological_sort_correct_length(self, plan_fixture, expected_signals, request):
        from VeriGenX.agents.archweaver.dag_builder import DAGBuilder
        from VeriGenX.agents.archweaver.resolver import Resolver
        plan  = request.getfixturevalue(plan_fixture)
        dag   = DAGBuilder().build_from_test_plan(test_plan_dict=plan)
        order = Resolver().resolve(dag)
        assert len(order) == len(dag["components"])

    def test_no_errors_in_clean_reference_plan(self, plan_fixture, expected_signals, request):
        from VeriGenX.agents.archweaver.dag_builder import DAGBuilder
        from VeriGenX.agents.archweaver.conflict_detector import ConflictDetector
        plan      = request.getfixturevalue(plan_fixture)
        dag       = DAGBuilder().build_from_test_plan(test_plan_dict=plan)
        conflicts = ConflictDetector().detect_conflicts(dag, plan)
        errors    = [c for c in conflicts if c["severity"] == "error"]
        assert errors == []
