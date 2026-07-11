"""
ArchWeaver: Multi-Agent DAG Builder
Extends DAGBuilder to support testbenches with multiple agents
(e.g., AXI master + slave, or UART TX + RX agents)
"""
import json
import os
from typing import Dict, List, Optional
from VeriGenX.config import TEST_PLANS_DIR


class MultiAgentDAGBuilder:
    """
    Builds a dependency graph for testbenches that require multiple UVM agents.
    Each agent instance gets its own driver, monitor, and sequencer components,
    all sharing a common interface and scoreboard.
    """

    # Standard UVM components that are shared across all agents
    SHARED_COMPONENTS = ["interface", "sequence_item", "scoreboard", "coverage", "env", "top"]

    # Per-agent UVM components (prefixed per agent instance)
    PER_AGENT_COMPONENTS = ["driver", "monitor", "sequence", "agent"]

    def __init__(self):
        self.components: List[str] = []
        self.dependencies: Dict[str, List[str]] = {}
        self.agent_names: List[str] = []

    def build_multi_agent(self, agent_names: List[str], design_name: str = "design") -> Dict:
        """
        Build a dependency graph for a multi-agent testbench.

        Args:
            agent_names: List of agent role names, e.g. ["master", "slave"]
            design_name: RTL design identifier

        Returns:
            DAG dict with components, dependencies, design_name, agent_count
        """
        self.agent_names = agent_names
        self.components = list(self.SHARED_COMPONENTS)  # start with shared
        self.dependencies = {
            "interface":    [],
            "sequence_item": ["interface"],
            "scoreboard":   ["sequence_item", "interface"],
            "coverage":     ["sequence_item", "interface"],
        }

        # Create per-agent components
        all_agents = []
        for name in agent_names:
            drv  = f"{name}_driver"
            mon  = f"{name}_monitor"
            seq  = f"{name}_sequence"
            agt  = f"{name}_agent"

            self.components.extend([drv, mon, seq, agt])
            all_agents.append(agt)

            self.dependencies[drv]  = ["sequence_item", "interface"]
            self.dependencies[mon]  = ["interface"]
            self.dependencies[seq]  = ["sequence_item", "interface"]
            self.dependencies[agt]  = [drv, mon, seq]

        # Env depends on all agent instances + scoreboard + coverage
        self.dependencies["env"] = all_agents + ["scoreboard", "coverage"]

        # Test hierarchy
        self.components.extend(["test_base", "test_directed"])
        self.dependencies["test_base"]    = ["env"] + [f"{n}_sequence" for n in agent_names]
        self.dependencies["test_directed"] = ["test_base"]
        self.dependencies["top"]           = ["test_base", "interface", "env"]

        return {
            "components":   self.components,
            "dependencies": self.dependencies,
            "design_name":  design_name,
            "agent_count":  len(agent_names),
            "agent_names":  agent_names,
        }

    def build_from_test_plan(self, test_plan_path: Optional[str] = None,
                              agent_names: Optional[List[str]] = None) -> Dict:
        """
        Build multi-agent DAG from an existing test plan JSON.
        Falls back to single-agent if no agent_names given.
        """
        if test_plan_path is None:
            test_plan_path = os.path.join(TEST_PLANS_DIR, "uart_test_plan.json")

        with open(test_plan_path, "r") as f:
            plan = json.load(f)

        design = plan.get("design_name", "design")
        agents = agent_names or ["default"]
        return self.build_multi_agent(agents, design_name=design)
