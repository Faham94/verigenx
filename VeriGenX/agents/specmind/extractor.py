"""
SpecMind: LLM-based Extractor
Uses Ollama to extract structured data from specification chunks
"""
from typing import Dict, List, Any
from VeriGenX.llm.ollama_client import get_ollama_client
from VeriGenX.llm.prompt_library import get_prompt
from VeriGenX.llm.response_validator import ResponseValidator

class Extractor:
    def __init__(self):
        self.client = get_ollama_client()
        self.validator = ResponseValidator()
    
    def extract_signals(self, context: str) -> List[Dict]:
        prompt = get_prompt("specmind_signal_extraction").format(context=context)
        response = self.client.generate(prompt)
        return self.validator.extract_signals(response)
    
    def extract_fsm_states(self, context: str) -> List[str]:
        prompt = get_prompt("specmind_fsm_extraction").format(context=context)
        response = self.client.generate(prompt)
        return self.validator.extract_fsm_states(response)
    
    def extract_registers(self, context: str) -> List[Dict]:
        prompt = get_prompt("specmind_register_extraction").format(context=context)
        response = self.client.generate(prompt)
        return self.validator.extract_registers(response)
    
    def extract_timing(self, context: str) -> Dict:
        prompt = get_prompt("specmind_timing_extraction").format(context=context)
        response = self.client.generate(prompt)
        return self.validator.extract_timing(response)
    
    def extract_all(self, context: str) -> Dict:
        return {
            "signals": self.extract_signals(context),
            "fsm_states": self.extract_fsm_states(context),
            "register_map": self.extract_registers(context),
            "timing_constraints": self.extract_timing(context)
        }
