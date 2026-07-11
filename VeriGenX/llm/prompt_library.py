"""
Prompt Library for VeriGenX
Centralized store for all LLM prompts.
Expanded to include timing constraints and confidence scoring.
"""
from typing import Dict

_PROMPTS: Dict[str, str] = {

    # ------------------------------------------------------------------ #
    #  SpecMind extraction prompts                                         #
    # ------------------------------------------------------------------ #

    "specmind_signal_extraction": (
        "You are an expert RTL verification engineer.\n"
        "Extract ALL interface signals from the specification below.\n"
        "Return a JSON array. Each element must have:\n"
        "  name (string), width (integer), direction (input|output|inout), "
        "description (string, optional)\n\n"
        "Specification:\n{context}\n\n"
        "Return ONLY a valid JSON array. No explanation, no markdown fences."
    ),

    "specmind_fsm_extraction": (
        "You are an expert RTL verification engineer.\n"
        "Extract ALL FSM state names from the specification below.\n"
        "Return a JSON array of strings only.\n\n"
        "Specification:\n{context}\n\n"
        "Return ONLY a valid JSON array of state name strings. No explanation."
    ),

    "specmind_register_extraction": (
        "You are an expert RTL verification engineer.\n"
        "Extract ALL registers from the specification below.\n"
        "Return a JSON array. Each element must have:\n"
        "  address (hex string), name (string), width (integer), "
        "access (RW|RO|WO|RC, optional), reset_value (hex string, optional)\n\n"
        "Specification:\n{context}\n\n"
        "Return ONLY a valid JSON array. No explanation, no markdown fences."
    ),

    # Bug #11 fix: comprehensive timing constraints prompt
    "specmind_timing_extraction": (
        "You are an expert RTL verification engineer.\n"
        "Extract ALL timing constraints from the specification below.\n"
        "Return a JSON object with any of these fields that are present:\n"
        "  clock_period_ns (number), setup_time_ns (number), hold_time_ns (number),\n"
        "  max_frequency_mhz (number), baud_rate (number or string),\n"
        "  propagation_delay_ns (number), output_delay_ns (number),\n"
        "  input_delay_ns (number), reset_duration_cycles (integer)\n\n"
        "Specification:\n{context}\n\n"
        "Return ONLY a valid JSON object. If a field is not mentioned, omit it.\n"
        "No explanation, no markdown fences."
    ),

    "specmind_handshake_extraction": (
        "You are an expert RTL verification engineer.\n"
        "Extract ALL protocol handshake rules (e.g., request/acknowledge signals, valid/ready behaviors, status triggers) from the specification below.\n"
        "Return a JSON array of strings, where each string describes a specific handshake rule.\n\n"
        "Specification:\n{context}\n\n"
        "Return ONLY a valid JSON array. No explanation, no markdown fences."
    ),

    "specmind_firmware_extraction": (
        "You are an expert RTL verification engineer.\n"
        "Extract the firmware programming model obligations (e.g., initialization sequences, register configuration orders, status polling sequences) from the specification below.\n"
        "Return a JSON array of strings, where each string represents a step or obligation in the programming model.\n\n"
        "Specification:\n{context}\n\n"
        "Return ONLY a valid JSON array. No explanation, no markdown fences."
    ),

    "specmind_functional_points_extraction": (
        "You are an expert RTL verification engineer.\n"
        "Extract ALL functional coverage points from the specification below.\n"
        "Return a JSON array. Each element must have:\n"
        "  id (string like FP_001), description (string), "
        "priority (high|medium|low, optional)\n\n"
        "Specification:\n{context}\n\n"
        "Return ONLY a valid JSON array. No explanation, no markdown fences."
    ),

    # ------------------------------------------------------------------ #
    #  Confidence scoring prompt                                           #
    # ------------------------------------------------------------------ #

    "specmind_confidence_scoring": (
        "You are a QA engineer reviewing LLM extraction results.\n"
        "Given the original specification and extracted data, score the extraction quality.\n"
        "Return a JSON object with:\n"
        "  overall_confidence (0.0-1.0), signals_confidence (0.0-1.0),\n"
        "  fsm_confidence (0.0-1.0), registers_confidence (0.0-1.0),\n"
        "  timing_confidence (0.0-1.0), notes (string)\n\n"
        "Specification:\n{context}\n\n"
        "Extracted data:\n{extracted}\n\n"
        "Return ONLY a valid JSON object."
    ),

    # ------------------------------------------------------------------ #
    #  ArchWeaver conflict resolution                                      #
    # ------------------------------------------------------------------ #

    "archweaver_conflict_resolution": (
        "You are an expert UVM verification engineer.\n"
        "A conflict has been detected in the UVM testbench dependency graph.\n\n"
        "Conflict type: {conflict_type}\n"
        "Description: {description}\n\n"
        "Specification context:\n{spec_context}\n\n"
        "Provide a single, concrete resolution suggestion in one or two sentences.\n"
        "Be specific about what to rename or restructure."
    ),
}


def get_prompt(name: str) -> str:
    """Retrieve a prompt template by name."""
    if name not in _PROMPTS:
        raise KeyError(
            f"Prompt '{name}' not found. Available: {list(_PROMPTS.keys())}"
        )
    return _PROMPTS[name]


def get_all_prompts() -> Dict[str, str]:
    """Return a copy of all prompt templates."""
    return dict(_PROMPTS)
