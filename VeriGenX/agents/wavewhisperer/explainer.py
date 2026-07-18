import re
from typing import Dict, Any, List

from VeriGenX.llm.ollama_client import get_ollama_client
from VeriGenX.llm.prompt_library import get_prompt
from VeriGenX.config import UVM_CODEGEN_MODEL

class WaveExplainer:
    def __init__(self):
        self.ollama_client = get_ollama_client()

    def explain_anomalies(self, design_name: str, anomalies: List[Dict[str, Any]], test_plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Queries the LLM for each anomaly to generate detailed explanations.
        """
        explained_list = []
        is_available = self.ollama_client.is_available()

        for idx, anomaly in enumerate(anomalies):
            anomaly_type = anomaly.get("type", "UNKNOWN")
            timestamp = anomaly.get("timestamp", 0)
            signal = anomaly.get("signal", "")
            actual = anomaly.get("actual", "")
            expected = anomaly.get("expected", "")
            severity = anomaly.get("severity", "INFO")
            
            # Map type to default severity
            if anomaly_type in ("FSM_SEQUENCE_VIOLATION", "PROTOCOL_VIOLATION", "RESET_VIOLATION", "XZ_PROPAGATION"):
                severity = "CRITICAL"
            elif anomaly_type in ("SETUP_VIOLATION", "HOLD_VIOLATION", "GLITCH_DETECTION"):
                severity = "WARNING"

            # Find relevant spec context
            spec_reference = self._find_spec_reference(anomaly_type, test_plan)

            if not is_available:
                # LLM offline fallback
                what_happened = f"An anomaly of type '{anomaly_type}' was observed on signal '{signal}' at time step {timestamp}."
                why = f"The signal value was measured as '{actual}', which violated the design requirement: '{expected}'."
                suggested_fix = "Review the RTL driver logic and testbench constraint parameters for signal stability."
                
                explained_list.append({
                    "id": f"A_{idx+1:03d}",
                    "type": anomaly_type,
                    "timestamp": timestamp,
                    "signal": signal,
                    "what_happened": what_happened,
                    "why": why,
                    "suggested_fix": suggested_fix,
                    "spec_reference": spec_reference,
                    "severity": severity
                })
                continue

            # Query LLM
            prompt_tmpl = get_prompt("wavewhisperer_explanation")
            prompt = prompt_tmpl.format(
                design_name=design_name,
                anomaly_type=anomaly_type,
                timestamp=timestamp,
                signals_involved=signal,
                actual_values=actual,
                expected_values=expected,
                spec_reference=spec_reference
            )

            try:
                response = self.ollama_client.generate(
                    prompt=prompt,
                    model=UVM_CODEGEN_MODEL,
                    temperature=0.2,
                    max_tokens=500
                )
            except Exception:
                response = ""

            if response:
                what_happened, why, suggested_fix = self._parse_llm_response(response, anomaly_type, actual, expected)
            else:
                what_happened = f"An anomaly of type '{anomaly_type}' occurred."
                why = f"Actual value '{actual}' did not match expected '{expected}'."
                suggested_fix = "Check RTL logic."

            explained_list.append({
                "id": f"A_{idx+1:03d}",
                "type": anomaly_type,
                "timestamp": timestamp,
                "signal": signal,
                "what_happened": what_happened,
                "why": why,
                "suggested_fix": suggested_fix,
                "spec_reference": spec_reference,
                "severity": severity
            })

        return explained_list

    def _find_spec_reference(self, anomaly_type: str, test_plan: Dict[str, Any]) -> str:
        """Helper to link the check back to relevant test plan definitions."""
        if "RESET" in anomaly_type:
            # Try to pull from reset functional point
            for fp in test_plan.get("functional_points", []):
                if "reset" in fp.get("description", "").lower():
                    return f"Reset point: {fp.get('id')} - {fp.get('description')}"
            return "Reset & Initialisation requirements"
            
        elif "PROTOCOL" in anomaly_type:
            rules = test_plan.get("protocol_handshake_rules", [])
            return rules[0] if rules else "Protocol specification rules"
            
        elif "FSM" in anomaly_type:
            states = test_plan.get("fsm_states", [])
            return f"FSM state transitions: {', '.join(states)}" if states else "State machine definitions"
            
        elif "SETUP" in anomaly_type or "HOLD" in anomaly_type:
            tc = test_plan.get("timing_constraints", {})
            return f"Timing parameters: {tc}" if tc else "Timing constraints"
            
        return test_plan.get("source_file", "Design specification text")

    def _parse_llm_response(self, response: str, anomaly_type: str, actual: str, expected: str) -> tuple:
        """Parses the LLM's structured natural-language response."""
        what_happened = ""
        why = ""
        suggested_fix = ""

        # Use regex to find sections
        m_what = re.search(r"(?:what happened|1\.)\s*:\s*(.*?)(?=(?:why|2\.)|suggested fix|3\.|\Z)", response, re.DOTALL | re.IGNORECASE)
        m_why = re.search(r"(?:why|2\.)\s*:\s*(.*?)(?=suggested fix|3\.|\Z)", response, re.DOTALL | re.IGNORECASE)
        m_fix = re.search(r"(?:suggested fix|3\.)\s*:\s*(.*)", response, re.DOTALL | re.IGNORECASE)

        if m_what:
            what_happened = m_what.group(1).strip()
        if m_why:
            why = m_why.group(1).strip()
        if m_fix:
            suggested_fix = m_fix.group(1).strip()

        # Clean markdown formatting
        what_happened = re.sub(r"[*#`_\"]", "", what_happened)
        why = re.sub(r"[*#`_\"]", "", why)
        suggested_fix = re.sub(r"[*#`_\"]", "", suggested_fix)

        # Fallbacks
        if not what_happened:
            what_happened = f"Waveform anomaly of type '{anomaly_type}' detected."
        if not why:
            why = f"Measured event '{actual}' did not satisfy design criteria '{expected}'."
        if not suggested_fix:
            suggested_fix = "Examine design registers and driving timing relationships in the simulation log."

        return what_happened, why, suggested_fix
