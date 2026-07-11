"""
ArchWeaver: LLM-Assisted Conflict Resolver
When ConflictDetector finds ambiguous conflicts, queries the Ollama LLM
with context from SpecMind to suggest a resolution.
"""
from typing import Dict, List, Optional
from VeriGenX.llm.ollama_client import get_ollama_client
from VeriGenX.llm.response_validator import ResponseValidator


class LLMConflictResolver:
    """
    Uses the local Ollama LLM to analyze DAG conflicts and suggest resolutions.
    Falls back gracefully when Ollama is unavailable.
    """

    RESOLUTION_PROMPT = (
        "You are an expert UVM (Universal Verification Methodology) verification engineer.\n"
        "A conflict has been detected in a UVM testbench dependency graph.\n\n"
        "Conflict details:\n"
        "  Type: {conflict_type}\n"
        "  Severity: {severity}\n"
        "  Description: {description}\n\n"
        "Specification context:\n{spec_context}\n\n"
        "Provide a concrete resolution suggestion in one or two sentences. "
        "Be specific about which component or signal to rename or restructure.\n"
        "Return ONLY your suggestion text, no JSON, no preamble."
    )

    def __init__(self):
        self.client = get_ollama_client()
        self.validator = ResponseValidator()

    def resolve(self, conflicts: List[Dict], spec_context: str = "") -> List[Dict]:
        """
        For each conflict, attempt LLM-assisted resolution.

        Args:
            conflicts: List of conflict dicts from ConflictDetector
            spec_context: Relevant specification text to give the LLM context

        Returns:
            Same conflict list, each augmented with 'llm_resolution' key
        """
        resolved = []
        for conflict in conflicts:
            enhanced = dict(conflict)
            if not self.client.is_available():
                enhanced["llm_resolution"] = (
                    "LLM unavailable — apply manual resolution: "
                    + conflict.get("suggestion", "")
                )
            else:
                prompt = self.RESOLUTION_PROMPT.format(
                    conflict_type=conflict.get("type", "unknown"),
                    severity=conflict.get("severity", "error"),
                    description=conflict.get("description", ""),
                    spec_context=spec_context[:1000] if spec_context else "No context provided."
                )
                response = self.client.generate(prompt, temperature=0.2, max_tokens=256)
                enhanced["llm_resolution"] = response.strip() if response else conflict.get("suggestion", "")
            resolved.append(enhanced)
        return resolved

    def report_with_resolutions(self, resolved_conflicts: List[Dict]) -> None:
        """Print a formatted report including LLM resolutions."""
        if not resolved_conflicts:
            print("No conflicts detected.")
            return

        print("\nConflict Resolution Report")
        print("=" * 60)
        for i, conflict in enumerate(resolved_conflicts, 1):
            print(f"\n{i}. [{conflict.get('severity', 'error').upper()}] {conflict.get('type', '')}")
            print(f"   Description : {conflict.get('description', '')}")
            print(f"   Suggestion  : {conflict.get('suggestion', '')}")
            print(f"   LLM Advice  : {conflict.get('llm_resolution', 'N/A')}")
        print("=" * 60)
