"""
State Bus for VeriGenX
Shared state manager for all agents
"""
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

@dataclass
class PipelineState:
    current_phase: str = ""
    test_plan: Optional[Dict] = None
    dependency_graph: Optional[Dict] = None
    generated_files: list = field(default_factory=list)
    simulation_results: Optional[Dict] = None
    coverage_data: Optional[Dict] = None
    anomalies: list = field(default_factory=list)
    traceability_matrix: Optional[Dict] = None
    errors: list = field(default_factory=list)
    rollback_point: Optional[Dict] = None

class StateBus:
    def __init__(self):
        self.state = PipelineState()
        self.history = []
        self.load_from_disk()
    
    def get_state(self) -> PipelineState:
        return self.state
    
    def serialize(self) -> Dict[str, Any]:
        return {
            "current_phase": self.state.current_phase,
            "test_plan": self.state.test_plan,
            "dependency_graph": self.state.dependency_graph,
            "generated_files": self.state.generated_files,
            "simulation_results": self.state.simulation_results,
            "coverage_data": self.state.coverage_data,
            "anomalies": self.state.anomalies,
            "traceability_matrix": self.state.traceability_matrix,
            "errors": self.state.errors,
        }

    def deserialize(self, data: Dict[str, Any]):
        self.state.current_phase = data.get("current_phase", "")
        self.state.test_plan = data.get("test_plan")
        self.state.dependency_graph = data.get("dependency_graph")
        self.state.generated_files = data.get("generated_files", [])
        self.state.simulation_results = data.get("simulation_results")
        self.state.coverage_data = data.get("coverage_data")
        self.state.anomalies = data.get("anomalies", [])
        self.state.traceability_matrix = data.get("traceability_matrix")
        self.state.errors = data.get("errors", [])

    def save_to_disk(self, filepath: str = "output/pipeline_state.json"):
        import os
        import json
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(self.serialize(), f, indent=4)
        except Exception as e:
            print(f"Error saving StateBus: {e}")

    def load_from_disk(self, filepath: str = "output/pipeline_state.json"):
        import os
        import json
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.deserialize(data)
            except Exception as e:
                print(f"Error loading StateBus: {e}")
    
    def update_state(self, **kwargs):
        self.history.append(self.state.__dict__.copy())
        for key, value in kwargs.items():
            if hasattr(self.state, key):
                setattr(self.state, key, value)
        self.save_to_disk()
    
    def rollback(self):
        if self.history:
            previous = self.history.pop()
            for key, value in previous.items():
                if hasattr(self.state, key):
                    setattr(self.state, key, value)
            self.save_to_disk()
            return True
        return False
    
    def get_phase_status(self, phase: str) -> str:
        status_map = {
            "specmind": "completed" if self.state.test_plan else "pending",
            "archweaver": "completed" if self.state.dependency_graph else "pending",
            "uvmforge": "completed" if self.state.generated_files else "pending",
            "simrunner": "completed" if self.state.simulation_results else "pending",
            "coverhunter": "completed" if self.state.coverage_data else "pending",
            "wavewhisperer": "completed" if self.state.anomalies else "pending",
            "tracevault": "completed" if self.state.traceability_matrix else "pending"
        }
        return status_map.get(phase, "unknown")

_state_bus = None

def get_state_bus() -> StateBus:
    global _state_bus
    if _state_bus is None:
        _state_bus = StateBus()
    return _state_bus
