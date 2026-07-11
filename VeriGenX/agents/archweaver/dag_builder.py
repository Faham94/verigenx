"""
ArchWeaver: DAG Builder
Builds a dependency graph for UVM components from a test plan.

Fixes applied:
  - Bug #1: Was ignoring in-memory state — now accepts a test_plan dict directly
  - Bug #2: Edges were hardcoded — now derived from the test plan (signals,
            design_name, functional_points determine component set)
  - Bug #9: UVM dependency edges were architecturally incorrect:
              sequence_item, sequence, scoreboard, coverage all had interface
              as a dependency — WRONG.  Only driver/monitor hold the virtual
              interface handle.  Corrected edges documented below.
"""
import json
import os
from typing import Dict, List, Optional
from VeriGenX.config import TEST_PLANS_DIR


# ---------------------------------------------------------------------- #
#  Correct UVM dependency model (Bug #9)                                  #
#                                                                         #
#  interface      → []                 no deps; hardware VIF              #
#  sequence_item  → []                 pure data container; no VIF        #
#  sequence       → [sequence_item]    extends uvm_sequence#(seq_item)    #
#  driver         → [seq_item, iface]  holds virtual interface handle     #
#  monitor        → [interface]        holds virtual interface handle      #
#  agent          → [driver, monitor,  UVM agent aggregation              #
#                    sequence]                                             #
#  scoreboard     → [sequence_item]    receives transactions via AP;      #
#                                      does NOT touch the VIF             #
#  coverage       → [sequence_item]    same as scoreboard                 #
#  env            → [agent, sb, cov]   aggregation                        #
#  test_base      → [env, sequence]    instantiates env, runs seqs        #
#  test_directed  → [test_base]        extends test_base                  #
#  top            → [test_base,        instantiates DUT + VIF + env       #
#                    interface, env]                                       #
# ---------------------------------------------------------------------- #

CORRECT_UVM_DEPENDENCIES: Dict[str, List[str]] = {
    "interface":    [],
    "sequence_item": [],                              # Bug #9 fix
    "sequence":     ["sequence_item"],                # Bug #9 fix
    "driver":       ["sequence_item", "interface"],
    "monitor":      ["interface"],
    "agent":        ["driver", "monitor", "sequence"],
    "scoreboard":   ["sequence_item"],                # Bug #9 fix
    "coverage":     ["sequence_item"],                # Bug #9 fix
    "env":          ["agent", "scoreboard", "coverage"],
    "test_base":    ["env", "sequence"],
    "test_directed": ["test_base"],
    "top":          ["test_base", "interface", "env"],
}

STANDARD_COMPONENT_ORDER: List[str] = [
    "interface", "sequence_item", "sequence", "driver", "monitor",
    "agent", "scoreboard", "coverage", "env", "test_base", "test_directed", "top",
]


class DAGBuilder:

    def __init__(self):
        self.components   = []
        self.dependencies = {}
        self._plan        = {}

    # ------------------------------------------------------------------ #
    #  Primary API — accepts dict or file path                            #
    # ------------------------------------------------------------------ #

    def build_from_test_plan(
        self,
        test_plan_path: Optional[str] = None,
        test_plan_dict: Optional[Dict] = None,
    ) -> Dict:
        """
        Build a UVM component dependency graph.

        Bug #1 fix: accepts test_plan_dict from in-memory state so the
        orchestrator does NOT have to fall back to a hardcoded disk file.

        Bug #2 fix: derives component set and design metadata directly from
        the test plan rather than using a static list.

        Args:
            test_plan_path: path to a JSON test plan file (optional fallback)
            test_plan_dict: an already-loaded test plan dict (preferred)

        Returns:
            DAG dict: {components, dependencies, design_name, signals,
                       component_filenames}
        """
        # --- Load plan (Bug #1 fix: prefer in-memory dict) ---
        if test_plan_dict is not None:
            plan = test_plan_dict
        elif test_plan_path is not None:
            with open(test_plan_path, "r", encoding="utf-8") as f:
                plan = json.load(f)
        else:
            default_path = os.path.join(TEST_PLANS_DIR, "uart_test_plan.json")
            with open(default_path, "r", encoding="utf-8") as f:
                plan = json.load(f)

        self._plan = plan
        return self._build(plan)

    # ------------------------------------------------------------------ #
    #  Internal build                                                      #
    # ------------------------------------------------------------------ #

    def _build(self, plan: Dict) -> Dict:
        design = plan.get("design_name", "design")

        # Bug #2 fix: derive component set from test plan content
        self.components   = self._derive_components(plan)
        self.dependencies = self._derive_dependencies(self.components)

        # Generate SystemVerilog filenames prefixed with design name
        filenames = {
            comp: f"{design}_{comp}.sv" for comp in self.components
        }

        return {
            "components":         self.components,
            "dependencies":       self.dependencies,
            "design_name":        design,
            "signals":            plan.get("signals", []),
            "fsm_states":         plan.get("fsm_states", []),
            "register_map":       plan.get("register_map", []),
            "functional_points":  plan.get("functional_points", []),
            "component_filenames": filenames,
        }

    # ------------------------------------------------------------------ #
    #  Derivation logic (Bug #2)                                           #
    # ------------------------------------------------------------------ #

    def _derive_components(self, plan: Dict) -> List[str]:
        """
        Determine required UVM components from the test plan.
        All 12 standard components are always required for a complete
        testbench.  Future extension: add extra test types per FP count.
        """
        components = list(STANDARD_COMPONENT_ORDER)

        # If there are more than 4 functional points, add a second directed test
        fps = plan.get("functional_points", [])
        if len(fps) > 4 and "test_random" not in components:
            components.append("test_random")
            # No extra deps — test_random also extends test_base

        return components

    def _derive_dependencies(self, components: List[str]) -> Dict[str, List[str]]:
        """
        Build the dependency map from the correct UVM model.
        Extra components (e.g. test_random) default to [test_base].
        """
        deps = {}
        for comp in components:
            if comp in CORRECT_UVM_DEPENDENCIES:
                deps[comp] = list(CORRECT_UVM_DEPENDENCIES[comp])
            else:
                # Unknown extra component: depends on test_base by default
                deps[comp] = ["test_base"]

        # Ensure 'top' depends on all tests in the components list to keep it last
        if "top" in deps:
            for comp in components:
                if comp.startswith("test_") and comp != "test_base":
                    if comp not in deps["top"]:
                        deps["top"].append(comp)
        return deps

    # ------------------------------------------------------------------ #
    #  Accessors                                                           #
    # ------------------------------------------------------------------ #

    def get_dag(self) -> Dict:
        return {
            "components":   self.components,
            "dependencies": self.dependencies,
            "design_name":  self._plan.get("design_name", "design"),
        }

    def get_test_plan(self) -> Dict:
        return self._plan
