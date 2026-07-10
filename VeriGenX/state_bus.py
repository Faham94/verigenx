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
    
    def get_state(self) -> PipelineState:
        return self.state
    
    def update_state(self, **kwargs):
        self.history.append(self.state.__dict__.copy())
        for key, value in kwargs.items():
            if hasattr(self.state, key):
                setattr(self.state, key, value)
    
    def rollback(self):
        if self.history:
            previous = self.history.pop()
            for key, value in previous.items():
                if hasattr(self.state, key):
                    setattr(self.state, key, value)
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
