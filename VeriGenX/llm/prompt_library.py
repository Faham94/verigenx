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

    "uvmforge_placeholder_fill": (
        "You are an expert RTL verification engineer specializing in UVM 1.2.\n"
        "We are generating UVM code for the DUT '{dut_name}' with the following design test plan details:\n"
        "{test_plan_context}\n\n"
        "You need to generate the SystemVerilog code for the placeholder block '{block_name}' in the component '{component_name}'.\n"
        "The surrounding code is:\n"
        "```systemverilog\n"
        "{code_context}\n"
        "```\n\n"
        "Guidelines:\n"
        "1. Write clean, synthesizable-by-Verilator SystemVerilog/UVM code.\n"
        "2. Do NOT write class shells, package imports, or factory macros. Only write the code to go inside the placeholder block.\n"
        "3. Respect protocol handshake rules and register mappings if applicable.\n"
        "4. Return ONLY the raw SystemVerilog code. No markdown fences, no explanation."
    ),

    "uvmforge_repair_fix": (
        "You are an expert RTL verification engineer.\n"
        "A compilation error was detected in the generated UVM file '{filename}' for component '{component_name}'.\n"
        "Error Type: {error_type}\n"
        "Compiler Output:\n"
        "```\n"
        "{compiler_output}\n"
        "```\n\n"
        "Current File Content:\n"
        "```systemverilog\n"
        "{file_content}\n"
        "```\n\n"
        "Generate the corrected, complete SystemVerilog code for this file. Ensure it is fully compliant with UVM 1.2 and compiles cleanly on Verilator 5.x.\n"
        "Return ONLY the complete raw SystemVerilog file content. No markdown fences, no explanations."
    ),
    "uvmforge_fill_sequence_item": (
        "You are an expert UVM verification engineer.\n"
        "Given the design signals:\n{signals}\n\n"
        "Generate the SystemVerilog code block for sequence item '{block_type}'.\n"
        "If block_type is 'fields', return rand bit declarations, enums, or structs.\n"
        "If block_type is 'constraints', return randomization constraint blocks.\n"
        "If block_type is 'macros', return UVM field macro registrations (`uvm_field_int, etc.).\n"
        "Return ONLY the raw code inside the block, no class wrapper, no markdown fences."
    ),
    "uvmforge_fill_driver_behavior": (
        "You are an expert UVM verification engineer.\n"
        "Generate SystemVerilog clocking block-based driver logic for these signals:\n{signals}\n\n"
        "Based on these protocol rules:\n{protocol}\n\n"
        "Return ONLY the raw driving logic, no function/task header/footer."
    ),
    "uvmforge_fill_monitor_behavior": (
        "You are an expert UVM verification engineer.\n"
        "Generate SystemVerilog monitor signal sampling logic for these signals:\n{signals}\n\n"
        "Based on these protocol rules:\n{protocol}\n\n"
        "The logic must sample signals and write transactions to the analysis port.\n"
        "Return ONLY the raw monitor loop logic."
    ),
    "uvmforge_fill_scoreboard": (
        "You are an expert UVM verification engineer.\n"
        "Generate SystemVerilog scoreboard check/compare logic for design: {dut_name}.\n"
        "Compare the actual monitored transaction against the expected transaction from reference model.\n"
        "Use functional points for reference:\n{functional_points}\n\n"
        "Return ONLY the compare and error reporting code."
    ),
    "uvmforge_fill_coverage": (
        "You are an expert UVM verification engineer.\n"
        "Generate SystemVerilog coverage bins/cross coverage for signals:\n{signals}\n\n"
        "And functional points:\n{functional_points}\n\n"
        "Return ONLY the coverpoint/cross declarations for the covergroup."
    ),
    "uvmforge_generate_reference_model": (
        "You are an expert verification engineer.\n"
        "Generate reference model prediction logic for DUT behavior:\n{dut_behavior}\n\n"
        "Produce code to compute expected transaction outputs from input transactions.\n"
        "If an invalid behavior is detected, use `uvm_report_error` or `uvm_error` to flag it.\n"
        "Return ONLY the prediction function body."
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
