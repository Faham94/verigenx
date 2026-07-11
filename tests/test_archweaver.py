"""
Unit Tests — ArchWeaver Components (Phase 2)
Tests: DAGBuilder, Resolver, ConflictDetector, MultiAgentDAGBuilder, LLMConflictResolver
Scenarios: simple DAG, complex/cycle, multi-agent
"""
import pytest


# ============================================================
# FIXTURES
# ============================================================

@pytest.fixture
def simple_dag():
    """Minimal valid DAG with no cycles"""
    return {
        "design_name": "uart",
        "components": ["interface", "sequence_item", "driver", "monitor",
                       "sequence", "agent", "scoreboard", "coverage",
                       "env", "test_base", "test_directed", "top"],
        "dependencies": {
            "interface":    [],
            "sequence_item": ["interface"],
            "sequence":     ["sequence_item", "interface"],
            "driver":       ["sequence_item", "interface"],
            "monitor":      ["interface"],
            "agent":        ["driver", "monitor", "sequence"],
            "scoreboard":   ["sequence_item", "interface"],
            "coverage":     ["sequence_item", "interface"],
            "env":          ["agent", "scoreboard", "coverage"],
            "test_base":    ["env", "sequence"],
            "test_directed": ["test_base"],
            "top":          ["test_base", "interface", "env"],
        }
    }

@pytest.fixture
def cyclic_dag():
    """DAG with a deliberate circular dependency — should raise"""
    return {
        "design_name": "broken",
        "components": ["A", "B", "C"],
        "dependencies": {
            "A": ["C"],
            "B": ["A"],
            "C": ["B"],   # C -> B -> A -> C  = cycle
        }
    }

@pytest.fixture
def minimal_dag():
    """Smallest valid DAG — single component, no deps"""
    return {
        "design_name": "trivial",
        "components": ["top"],
        "dependencies": {"top": []}
    }

@pytest.fixture
def uart_test_plan():
    """Minimal UART test plan dict"""
    return {
        "design_name": "uart",
        "signals": [
            {"name": "clk",     "width": 1, "direction": "input"},
            {"name": "rst_n",   "width": 1, "direction": "input"},
            {"name": "tx_data", "width": 8, "direction": "input"},
            {"name": "rx_data", "width": 8, "direction": "output"},
        ],
        "fsm_states": ["IDLE", "START", "DATA", "STOP"],
        "register_map": [
            {"address": "0x00", "name": "baud_divisor", "width": 16},
            {"address": "0x04", "name": "control",      "width": 8},
        ],
        "functional_points": [
            {"id": "FP_001", "description": "8-bit data transmission"},
            {"id": "FP_002", "description": "Baud rate configuration"},
        ]
    }

@pytest.fixture
def test_plan_file(tmp_path, uart_test_plan):
    import json
    p = tmp_path / "uart_test_plan.json"
    p.write_text(json.dumps(uart_test_plan), encoding="utf-8")
    return str(p)


# ============================================================
# 1. DAGBuilder Tests
# ============================================================

class TestDAGBuilder:
    def test_build_returns_dict(self, test_plan_file):
        from VeriGenX.agents.archweaver.dag_builder import DAGBuilder
        dag = DAGBuilder().build_from_test_plan(test_plan_file)
        assert isinstance(dag, dict)

    def test_build_has_components(self, test_plan_file):
        from VeriGenX.agents.archweaver.dag_builder import DAGBuilder
        dag = DAGBuilder().build_from_test_plan(test_plan_file)
        assert "components" in dag
        assert len(dag["components"]) > 0

    def test_build_has_dependencies(self, test_plan_file):
        from VeriGenX.agents.archweaver.dag_builder import DAGBuilder
        dag = DAGBuilder().build_from_test_plan(test_plan_file)
        assert "dependencies" in dag
        assert isinstance(dag["dependencies"], dict)

    def test_build_has_design_name(self, test_plan_file):
        from VeriGenX.agents.archweaver.dag_builder import DAGBuilder
        dag = DAGBuilder().build_from_test_plan(test_plan_file)
        assert dag["design_name"] == "uart"

    def test_build_has_12_components(self, test_plan_file):
        from VeriGenX.agents.archweaver.dag_builder import DAGBuilder
        dag = DAGBuilder().build_from_test_plan(test_plan_file)
        assert len(dag["components"]) == 12

    def test_build_contains_expected_components(self, test_plan_file):
        from VeriGenX.agents.archweaver.dag_builder import DAGBuilder
        dag = DAGBuilder().build_from_test_plan(test_plan_file)
        for comp in ["interface", "driver", "monitor", "agent", "env", "top"]:
            assert comp in dag["components"]

    def test_top_depends_on_env(self, test_plan_file):
        from VeriGenX.agents.archweaver.dag_builder import DAGBuilder
        dag = DAGBuilder().build_from_test_plan(test_plan_file)
        assert "env" in dag["dependencies"]["top"]

    def test_all_deps_reference_valid_components(self, test_plan_file):
        from VeriGenX.agents.archweaver.dag_builder import DAGBuilder
        dag = DAGBuilder().build_from_test_plan(test_plan_file)
        comps = set(dag["components"])
        for comp, deps in dag["dependencies"].items():
            for dep in deps:
                assert dep in comps, f"Dep '{dep}' for '{comp}' not in component list"


# ============================================================
# 2. Resolver Tests — Simple DAG
# ============================================================

class TestResolverSimple:
    def test_resolve_returns_list(self, simple_dag):
        from VeriGenX.agents.archweaver.resolver import Resolver
        order = Resolver().resolve(simple_dag)
        assert isinstance(order, list)

    def test_resolve_returns_all_components(self, simple_dag):
        from VeriGenX.agents.archweaver.resolver import Resolver
        order = Resolver().resolve(simple_dag)
        assert set(order) == set(simple_dag["components"])

    def test_resolve_correct_count(self, simple_dag):
        from VeriGenX.agents.archweaver.resolver import Resolver
        order = Resolver().resolve(simple_dag)
        assert len(order) == len(simple_dag["components"])

    def test_interface_before_driver(self, simple_dag):
        from VeriGenX.agents.archweaver.resolver import Resolver
        order = Resolver().resolve(simple_dag)
        assert order.index("interface") < order.index("driver")

    def test_interface_before_monitor(self, simple_dag):
        from VeriGenX.agents.archweaver.resolver import Resolver
        order = Resolver().resolve(simple_dag)
        assert order.index("interface") < order.index("monitor")

    def test_agent_after_driver_and_monitor(self, simple_dag):
        from VeriGenX.agents.archweaver.resolver import Resolver
        order = Resolver().resolve(simple_dag)
        assert order.index("driver")  < order.index("agent")
        assert order.index("monitor") < order.index("agent")

    def test_env_after_agent(self, simple_dag):
        from VeriGenX.agents.archweaver.resolver import Resolver
        order = Resolver().resolve(simple_dag)
        assert order.index("agent") < order.index("env")

    def test_top_is_last_or_after_env(self, simple_dag):
        from VeriGenX.agents.archweaver.resolver import Resolver
        order = Resolver().resolve(simple_dag)
        assert order.index("env") < order.index("top")

    def test_minimal_dag_resolves(self, minimal_dag):
        from VeriGenX.agents.archweaver.resolver import Resolver
        order = Resolver().resolve(minimal_dag)
        assert order == ["top"]

    def test_get_generation_order_returns_list_of_dicts(self, simple_dag):
        from VeriGenX.agents.archweaver.resolver import Resolver
        gen = Resolver().get_generation_order(simple_dag)
        assert isinstance(gen, list)
        for item in gen:
            assert "component" in item
            assert "filename"  in item
            assert "order"     in item

    def test_get_generation_order_filenames_end_in_sv(self, simple_dag):
        from VeriGenX.agents.archweaver.resolver import Resolver
        gen = Resolver().get_generation_order(simple_dag)
        for item in gen:
            assert item["filename"].endswith(".sv")


# ============================================================
# 3. Resolver Tests — Cycle Detection
# ============================================================

class TestResolverCycleDetection:
    def test_cyclic_dag_raises_exception(self, cyclic_dag):
        from VeriGenX.agents.archweaver.resolver import Resolver
        with pytest.raises(Exception, match="Circular dependency"):
            Resolver().resolve(cyclic_dag)

    def test_self_reference_raises(self):
        from VeriGenX.agents.archweaver.resolver import Resolver
        dag = {
            "components": ["A"],
            "dependencies": {"A": ["A"]}  # self-loop
        }
        with pytest.raises(Exception):
            Resolver().resolve(dag)


# ============================================================
# 4. DOT Export Tests
# ============================================================

class TestDOTExport:
    def test_export_dot_creates_file(self, simple_dag, tmp_path):
        from VeriGenX.agents.archweaver.resolver import Resolver
        out = tmp_path / "test.dot"
        Resolver().export_dot(simple_dag, str(out))
        assert out.exists()

    def test_export_dot_contains_digraph(self, simple_dag, tmp_path):
        from VeriGenX.agents.archweaver.resolver import Resolver
        out = tmp_path / "test.dot"
        Resolver().export_dot(simple_dag, str(out))
        content = out.read_text()
        assert "digraph" in content

    def test_export_dot_contains_components(self, simple_dag, tmp_path):
        from VeriGenX.agents.archweaver.resolver import Resolver
        out = tmp_path / "test.dot"
        Resolver().export_dot(simple_dag, str(out))
        content = out.read_text()
        assert "interface" in content
        assert "driver" in content

    def test_export_dot_contains_edges(self, simple_dag, tmp_path):
        from VeriGenX.agents.archweaver.resolver import Resolver
        out = tmp_path / "test.dot"
        Resolver().export_dot(simple_dag, str(out))
        content = out.read_text()
        assert "->" in content


# ============================================================
# 5. ConflictDetector Tests
# ============================================================

class TestConflictDetector:
    def test_no_conflicts_clean_dag(self, simple_dag, uart_test_plan):
        from VeriGenX.agents.archweaver.conflict_detector import ConflictDetector
        conflicts = ConflictDetector().detect_conflicts(simple_dag, uart_test_plan)
        assert conflicts == []

    def test_duplicate_signal_detected(self, simple_dag):
        from VeriGenX.agents.archweaver.conflict_detector import ConflictDetector
        plan = {"signals": [
            {"name": "clk", "width": 1, "direction": "input"},
            {"name": "clk", "width": 1, "direction": "input"},  # duplicate
        ]}
        conflicts = ConflictDetector().detect_conflicts(simple_dag, plan)
        types = [c["type"] for c in conflicts]
        assert "duplicate_signal" in types

    def test_duplicate_component_detected(self):
        from VeriGenX.agents.archweaver.conflict_detector import ConflictDetector
        dag = {
            "components": ["interface", "interface"],  # duplicate
            "dependencies": {"interface": []}
        }
        conflicts = ConflictDetector().detect_conflicts(dag, {"signals": []})
        types = [c["type"] for c in conflicts]
        assert "duplicate_component" in types

    def test_missing_dependency_detected(self):
        from VeriGenX.agents.archweaver.conflict_detector import ConflictDetector
        dag = {
            "components": ["driver"],
            "dependencies": {"driver": ["interface"]}  # interface not in components
        }
        conflicts = ConflictDetector().detect_conflicts(dag, {"signals": []})
        types = [c["type"] for c in conflicts]
        assert "missing_dependency" in types

    def test_conflict_has_required_fields(self, simple_dag):
        from VeriGenX.agents.archweaver.conflict_detector import ConflictDetector
        plan = {"signals": [
            {"name": "clk", "width": 1, "direction": "input"},
            {"name": "clk", "width": 1, "direction": "input"},
        ]}
        conflicts = ConflictDetector().detect_conflicts(simple_dag, plan)
        for c in conflicts:
            assert "type" in c
            assert "severity" in c
            assert "description" in c
            assert "suggestion" in c

    def test_report_conflicts_no_crash_on_empty(self):
        from VeriGenX.agents.archweaver.conflict_detector import ConflictDetector
        # Should not raise
        ConflictDetector().report_conflicts([])


# ============================================================
# 6. Multi-Agent DAGBuilder Tests
# ============================================================

class TestMultiAgentDAGBuilder:
    def test_single_agent_build(self):
        from VeriGenX.agents.archweaver.multi_agent_builder import MultiAgentDAGBuilder
        dag = MultiAgentDAGBuilder().build_multi_agent(["default"], "uart")
        assert "default_driver" in dag["components"]
        assert "default_agent"  in dag["components"]

    def test_two_agent_build(self):
        from VeriGenX.agents.archweaver.multi_agent_builder import MultiAgentDAGBuilder
        dag = MultiAgentDAGBuilder().build_multi_agent(["master", "slave"], "axi")
        assert "master_driver" in dag["components"]
        assert "slave_driver"  in dag["components"]
        assert "master_agent"  in dag["components"]
        assert "slave_agent"   in dag["components"]

    def test_agent_count_stored(self):
        from VeriGenX.agents.archweaver.multi_agent_builder import MultiAgentDAGBuilder
        dag = MultiAgentDAGBuilder().build_multi_agent(["master", "slave"], "axi")
        assert dag["agent_count"] == 2

    def test_agent_names_stored(self):
        from VeriGenX.agents.archweaver.multi_agent_builder import MultiAgentDAGBuilder
        dag = MultiAgentDAGBuilder().build_multi_agent(["tx", "rx"], "uart")
        assert dag["agent_names"] == ["tx", "rx"]

    def test_multi_agent_dag_is_acyclic(self):
        from VeriGenX.agents.archweaver.multi_agent_builder import MultiAgentDAGBuilder
        from VeriGenX.agents.archweaver.resolver import Resolver
        dag = MultiAgentDAGBuilder().build_multi_agent(["master", "slave"], "axi")
        # Should resolve without raising
        order = Resolver().resolve(dag)
        assert len(order) == len(dag["components"])

    def test_multi_agent_env_depends_on_all_agents(self):
        from VeriGenX.agents.archweaver.multi_agent_builder import MultiAgentDAGBuilder
        dag = MultiAgentDAGBuilder().build_multi_agent(["master", "slave"], "axi")
        env_deps = dag["dependencies"]["env"]
        assert "master_agent" in env_deps
        assert "slave_agent"  in env_deps

    def test_multi_agent_shared_components_present(self):
        from VeriGenX.agents.archweaver.multi_agent_builder import MultiAgentDAGBuilder
        dag = MultiAgentDAGBuilder().build_multi_agent(["master", "slave"], "axi")
        for comp in ["interface", "sequence_item", "scoreboard", "env", "top"]:
            assert comp in dag["components"]

    def test_multi_agent_from_test_plan(self, test_plan_file):
        from VeriGenX.agents.archweaver.multi_agent_builder import MultiAgentDAGBuilder
        dag = MultiAgentDAGBuilder().build_from_test_plan(
            test_plan_file, agent_names=["tx", "rx"])
        assert dag["design_name"] == "uart"
        assert "tx_driver" in dag["components"]
        assert "rx_driver" in dag["components"]


# ============================================================
# 7. Integration Test: SpecMind -> ArchWeaver
# ============================================================

class TestSpecMindArchWeaverIntegration:
    def test_full_pipeline_uart(self, test_plan_file):
        """End-to-end: test plan file -> DAG -> topological sort -> no conflicts"""
        from VeriGenX.agents.archweaver.dag_builder import DAGBuilder
        from VeriGenX.agents.archweaver.resolver import Resolver
        from VeriGenX.agents.archweaver.conflict_detector import ConflictDetector
        import json

        # Build DAG from test plan
        dag = DAGBuilder().build_from_test_plan(test_plan_file)
        assert len(dag["components"]) == 12

        # Resolve topological order
        order = Resolver().resolve(dag)
        assert len(order) == 12

        # Dependency invariants
        assert order.index("interface") < order.index("driver")
        assert order.index("agent") < order.index("env")
        assert order.index("env") < order.index("top")

        # Conflict detection on actual test plan
        with open(test_plan_file) as f:
            plan = json.load(f)
        conflicts = ConflictDetector().detect_conflicts(dag, plan)
        assert conflicts == []

    def test_generation_order_has_all_sv_files(self, test_plan_file):
        from VeriGenX.agents.archweaver.dag_builder import DAGBuilder
        from VeriGenX.agents.archweaver.resolver import Resolver
        dag = DAGBuilder().build_from_test_plan(test_plan_file)
        gen = Resolver().get_generation_order(dag)
        sv_files = [item["filename"] for item in gen]
        for f in ["interface.sv", "driver.sv", "monitor.sv", "agent.sv",
                  "env.sv", "top.sv"]:
            assert f in sv_files


# ============================================================
# 8. Benchmark: 5 Reference Designs
# ============================================================

class TestBenchmarkFiveDesigns:
    """
    Verify correct generation order for 5 reference designs.
    All share the same 12-component UVM structure — what changes is the design_name.
    """

    DESIGNS = ["uart", "spi", "i2c", "axi_lite", "fifo"]

    def _build_dag(self, design_name):
        from VeriGenX.agents.archweaver.dag_builder import DAGBuilder
        builder = DAGBuilder()
        builder.components = [
            "interface", "sequence_item", "sequence", "driver",
            "monitor", "agent", "scoreboard", "coverage",
            "env", "test_base", "test_directed", "top"
        ]
        builder.dependencies = {
            "interface":    [],
            "sequence_item": ["interface"],
            "sequence":     ["sequence_item", "interface"],
            "driver":       ["sequence_item", "interface"],
            "monitor":      ["interface"],
            "agent":        ["driver", "monitor", "sequence"],
            "scoreboard":   ["sequence_item", "interface"],
            "coverage":     ["sequence_item", "interface"],
            "env":          ["agent", "scoreboard", "coverage"],
            "test_base":    ["env", "sequence"],
            "test_directed": ["test_base"],
            "top":          ["test_base", "interface", "env"],
        }
        return {
            "components":   builder.components,
            "dependencies": builder.dependencies,
            "design_name":  design_name,
        }

    @pytest.mark.parametrize("design", DESIGNS)
    def test_design_resolves_12_components(self, design):
        from VeriGenX.agents.archweaver.resolver import Resolver
        dag = self._build_dag(design)
        order = Resolver().resolve(dag)
        assert len(order) == 12, f"{design}: expected 12 components, got {len(order)}"

    @pytest.mark.parametrize("design", DESIGNS)
    def test_design_interface_is_first_leaf(self, design):
        from VeriGenX.agents.archweaver.resolver import Resolver
        dag = self._build_dag(design)
        order = Resolver().resolve(dag)
        # interface has no dependencies, must come before everything else
        assert order.index("interface") < order.index("driver")
        assert order.index("interface") < order.index("monitor")

    @pytest.mark.parametrize("design", DESIGNS)
    def test_design_top_after_env(self, design):
        from VeriGenX.agents.archweaver.resolver import Resolver
        dag = self._build_dag(design)
        order = Resolver().resolve(dag)
        assert order.index("env") < order.index("top"), \
            f"{design}: env must precede top"

    @pytest.mark.parametrize("design", DESIGNS)
    def test_design_no_conflicts(self, design):
        from VeriGenX.agents.archweaver.conflict_detector import ConflictDetector
        dag = self._build_dag(design)
        conflicts = ConflictDetector().detect_conflicts(dag, {"signals": []})
        assert conflicts == [], f"{design}: unexpected conflicts: {conflicts}"

    @pytest.mark.parametrize("design", DESIGNS)
    def test_design_is_acyclic(self, design):
        from VeriGenX.agents.archweaver.resolver import Resolver
        dag = self._build_dag(design)
        # No exception means acyclic
        Resolver().resolve(dag)
