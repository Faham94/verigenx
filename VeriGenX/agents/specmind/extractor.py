"""
SpecMind: LLM-based Extractor
Uses Ollama to extract structured data from specification text via RAG.

Fixes applied:
  - Bug #9:  No confidence scoring — now scores each extraction with a
             heuristic confidence value based on response quality
  - Bug #11: Timing constraints now fully extracted
  - Bug #2:  Was never called — now properly integrated via TestPlanGenerator
"""
import re
from typing import Dict, List, Any

from VeriGenX.llm.ollama_client import get_ollama_client
from VeriGenX.llm.prompt_library import get_prompt
from VeriGenX.llm.response_validator import ResponseValidator


class Extractor:

    def __init__(self):
        self.client    = get_ollama_client()
        self.validator = ResponseValidator()

    # ------------------------------------------------------------------ #
    #  Individual extraction methods                                        #
    # ------------------------------------------------------------------ #

    def extract_signals(self, context: str) -> List[Dict]:
        prompt   = get_prompt("specmind_signal_extraction").format(context=context)
        response = self.client.generate(prompt)
        return self.validator.extract_signals(response)

    def extract_fsm_states(self, context: str) -> List[str]:
        prompt   = get_prompt("specmind_fsm_extraction").format(context=context)
        response = self.client.generate(prompt)
        return self.validator.extract_fsm_states(response)

    def extract_registers(self, context: str) -> List[Dict]:
        prompt   = get_prompt("specmind_register_extraction").format(context=context)
        response = self.client.generate(prompt)
        return self.validator.extract_registers(response)

    def extract_timing(self, context: str) -> Dict:
        """Bug #11 fix: timing constraints fully extracted via dedicated prompt."""
        prompt   = get_prompt("specmind_timing_extraction").format(context=context)
        response = self.client.generate(prompt)
        return self.validator.extract_timing(response)

    def extract_functional_points(self, context: str) -> List[Dict]:
        prompt   = get_prompt("specmind_functional_points_extraction").format(context=context)
        response = self.client.generate(prompt)
        return self.validator.extract_signals(response)  # same list-of-dicts extraction

    # ------------------------------------------------------------------ #
    #  Confidence scoring (Bug #9 fix)                                     #
    # ------------------------------------------------------------------ #

    def _score_confidence(self, items: Any, expected_min: int = 1) -> float:
        """
        Heuristic confidence scoring.
        Returns 0.0–1.0 based on whether meaningful data was extracted.
        """
        if items is None:
            return 0.0
        if isinstance(items, list):
            if len(items) == 0:
                return 0.0
            if len(items) < expected_min:
                return 0.4
            return min(1.0, 0.5 + 0.1 * len(items))
        if isinstance(items, dict):
            if len(items) == 0:
                return 0.0
            return min(1.0, 0.5 + 0.1 * len(items))
        return 0.5

    # ------------------------------------------------------------------ #
    #  Combined extraction with confidence scores                          #
    # ------------------------------------------------------------------ #

    def extract_all(self, context: str) -> Dict:
        """
        Run all extractions and return results with confidence scores.
        Bug #9 fix: each extraction result is annotated with a confidence value.
        """
        signals    = self.extract_signals(context)
        fsm_states = self.extract_fsm_states(context)
        registers  = self.extract_registers(context)
        timing     = self.extract_timing(context)
        func_pts   = self.extract_functional_points(context)

        # Confidence scoring — Bug #9 fix
        confidence = {
            "signals":    self._score_confidence(signals, expected_min=2),
            "fsm_states": self._score_confidence(fsm_states, expected_min=2),
            "registers":  self._score_confidence(registers, expected_min=1),
            "timing":     self._score_confidence(timing, expected_min=1),
            "func_pts":   self._score_confidence(func_pts, expected_min=1),
        }
        confidence["overall"] = round(
            sum(confidence.values()) / len(confidence), 3
        )

        return {
            "signals":              signals,
            "fsm_states":           fsm_states,
            "register_map":         registers,
            "timing_constraints":   timing,
            "functional_points":    func_pts,
            "confidence":           confidence,
            "llm_available":        self.client.is_available(),
        }

    # ------------------------------------------------------------------ #
    #  RAG-aware extraction (search ChromaDB then extract)                 #
    # ------------------------------------------------------------------ #

    def extract_with_rag(self, query: str, embedder) -> Dict:
        """
        Use the embedder to retrieve relevant context chunks, then run
        extraction against that focused context.
        """
        chunks = embedder.search(query, n_results=5)
        if not chunks:
            return self.extract_all(query)
        context = "\n\n".join(chunks)
        return self.extract_all(context)
