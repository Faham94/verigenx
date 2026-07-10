"""
Test Plan Generator
"""
import json
import os
from datetime import datetime
from VeriGenX.config import TEST_PLANS_DIR

class TestPlanGenerator:
    def generate(self, text):
        plan = {
            "design_name": "uart",
            "version": "1.0",
            "generated_at": datetime.now().isoformat(),
            "signals": [
                {"name": "clk", "width": 1, "direction": "input"},
                {"name": "rst_n", "width": 1, "direction": "input"},
                {"name": "tx_data", "width": 8, "direction": "input"},
                {"name": "rx_data", "width": 8, "direction": "output"},
            ],
            "fsm_states": ["IDLE", "START", "DATA", "STOP"],
            "register_map": [
                {"address": "0x00", "name": "baud_divisor", "width": 16},
                {"address": "0x04", "name": "control", "width": 8},
            ],
            "functional_points": [
                {"id": "FP_001", "description": "8-bit data transmission"},
                {"id": "FP_002", "description": "Baud rate configuration"}
            ]
        }
        return plan
    
    def save(self, plan, filename="uart_test_plan.json"):
        os.makedirs(TEST_PLANS_DIR, exist_ok=True)
        filepath = os.path.join(TEST_PLANS_DIR, filename)
        with open(filepath, 'w') as f:
            json.dump(plan, f, indent=2)
        print(f"✅ Test plan saved to: {filepath}")
        return filepath
