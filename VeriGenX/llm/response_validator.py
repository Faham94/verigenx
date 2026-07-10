"""
Response Validator for LLM outputs
Validates and parses LLM responses
"""
import json
import re
from typing import Any, Dict, List, Optional

class ResponseValidator:
    @staticmethod
    def validate_json(response: str) -> Optional[Dict]:
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return json.loads(response)
        except json.JSONDecodeError:
            return None
    
    @staticmethod
    def validate_json_array(response: str) -> Optional[List]:
        try:
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return json.loads(response)
        except json.JSONDecodeError:
            return None
    
    @staticmethod
    def extract_signals(response: str) -> List[Dict]:
        data = ResponseValidator.validate_json_array(response)
        if data and isinstance(data, list):
            return data
        return []
    
    @staticmethod
    def extract_fsm_states(response: str) -> List[str]:
        data = ResponseValidator.validate_json_array(response)
        if data and isinstance(data, list):
            return [str(item) for item in data]
        return []
    
    @staticmethod
    def extract_registers(response: str) -> List[Dict]:
        data = ResponseValidator.validate_json_array(response)
        if data and isinstance(data, list):
            return data
        return []
    
    @staticmethod
    def extract_timing(response: str) -> Dict:
        data = ResponseValidator.validate_json(response)
        if data and isinstance(data, dict):
            return data
        return {}
