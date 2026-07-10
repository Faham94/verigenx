"""
Prompt Library for VeriGenX
Centralized store for all LLM prompts
"""
from typing import Dict

_PROMPTS: Dict[str, str] = {
    "specmind_signal_extraction": (
        "You are an expert RTL verification engineer.\n"
        "Extract all interface signals from the following specification.\n"
        "Return a JSON array of objects with fields: name, width, direction.\n\n"
        "Specification:\n{context}\n\n"
        "Return ONLY a valid JSON array, no explanation."
    ),
    "specmind_fsm_extraction": (
        "You are an expert RTL verification engineer.\n"
        "Extract all FSM states from the following specification.\n"
        "Return a JSON array of state name strings.\n\n"
        "Specification:\n{context}\n\n"
        "Return ONLY a valid JSON array, no explanation."
    ),
    "specmind_register_extraction": (
        "You are an expert RTL verification engineer.\n"
        "Extract all registers from the following specification.\n"
        "Return a JSON array of objects with fields: address, name, width.\n\n"
        "Specification:\n{context}\n\n"
        "Return ONLY a valid JSON array, no explanation."
    ),
    "specmind_timing_extraction": (
        "You are an expert RTL verification engineer.\n"
        "Extract timing constraints from the following specification.\n"
        "Return a JSON object with timing details.\n\n"
        "Specification:\n{context}\n\n"
        "Return ONLY a valid JSON object, no explanation."
    ),
}

def get_prompt(name: str) -> str:
    """Retrieve a prompt by name"""
    if name not in _PROMPTS:
        raise KeyError(f"Prompt '{name}' not found. Available: {list(_PROMPTS.keys())}")
    return _PROMPTS[name]

def get_all_prompts() -> Dict[str, str]:
    """Return all prompts"""
    return dict(_PROMPTS)
