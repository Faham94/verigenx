"""
ArchWeaver: DAG Builder
Builds dependency graph for UVM components from test plan
"""
import json
import os
from VeriGenX.config import TEST_PLANS_DIR

class DAGBuilder:
    def __init__(self):
        self.components = []
        self.dependencies = {}
    
    def build_from_test_plan(self, test_plan_path=None):
        """Build dependency graph from test plan JSON"""
        if test_plan_path is None:
            test_plan_path = os.path.join(TEST_PLANS_DIR, "uart_test_plan.json")
        
        # Read test plan
        with open(test_plan_path, 'r') as f:
            plan = json.load(f)
        
        # Define all UVM components needed for a complete testbench
        self.components = [
            "interface",
            "sequence_item",
            "sequence",
            "driver",
            "monitor",
            "agent",
            "scoreboard",
            "coverage",
            "env",
            "test_base",
            "test_directed",
            "top"
        ]
        
        # Define dependencies (component -> list of components it depends on)
        self.dependencies = {
            "interface": [],
            "sequence_item": ["interface"],
            "sequence": ["sequence_item", "interface"],
            "driver": ["sequence_item", "interface"],
            "monitor": ["interface"],
            "agent": ["driver", "monitor", "sequence"],
            "scoreboard": ["sequence_item", "interface"],
            "coverage": ["sequence_item", "interface"],
            "env": ["agent", "scoreboard", "coverage"],
            "test_base": ["env", "sequence"],
            "test_directed": ["test_base"],
            "top": ["test_base", "interface", "env"]
        }
        
        return {
            "components": self.components,
            "dependencies": self.dependencies,
            "design_name": plan.get("design_name", "uart")
        }
    
    def get_dag(self):
        """Return the dependency graph"""
        return {
            "components": self.components,
            "dependencies": self.dependencies
        }
