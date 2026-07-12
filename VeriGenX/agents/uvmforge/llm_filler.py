"""
UVMForge: LLM Filler
Fills design-specific placeholders in UVM SystemVerilog templates.
"""
import re
import json
from typing import Dict, Any, List

from VeriGenX.llm.ollama_client import get_ollama_client
from VeriGenX.llm.prompt_library import get_prompt
from VeriGenX.config import UVM_CODEGEN_MODEL
from VeriGenX.agents.uvmforge.logger import get_logger

logger = get_logger("llm_calls")


class LLMFiller:

    def __init__(self):
        self.client = get_ollama_client()

    def fill_placeholders(
        self,
        component_name: str,
        content: str,
        test_plan: Dict[str, Any]
    ) -> str:
        """
        Parses content for // {% llm_fill "<block_name>" %} ... // {% endllm_fill %}
        and replaces it using the LLM or heuristic fallbacks.
        """
        pattern = r"(//\s*\{%\s*llm_fill\s+[\"']([^\"']+)[\"']\s*%\})(.*?)(?://\s*\{%\s*endllm_fill\s*%\})"
        
        def replace_match(match) -> str:
            start_tag = match.group(1)
            block_name = match.group(2)
            default_body = match.group(3)
            
            # Request fill from LLM or heuristic fallback
            filled_code = self._get_fill(component_name, block_name, content, test_plan)
            return start_tag + "\n" + filled_code + "\n// {% endllm_fill %}"

        return re.sub(pattern, replace_match, content, flags=re.DOTALL)

    def _clean_response(self, response: str) -> str:
        """Helper to remove markdown fences from LLM responses."""
        if not response:
            return ""
        clean_response = response.strip()
        if clean_response.startswith("```"):
            lines = clean_response.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            clean_response = "\n".join(lines).strip()
        return clean_response

    # ------------------------------------------------------------------ #
    #  Dedicated Named Public Methods                                     #
    # ------------------------------------------------------------------ #

    def fill_sequence_item(self, signals: List[Dict[str, Any]], block_type: str = "fields") -> str:
        """Generates sequence item fields, constraints, types."""
        if self.client.is_available():
            try:
                prompt_tmpl = get_prompt("uvmforge_fill_sequence_item")
                prompt = prompt_tmpl.format(
                    signals=json.dumps(signals, indent=2),
                    block_type=block_type
                )
                logger.debug(f"Querying LLM for sequence item: {block_type}")
                response = self.client.generate(prompt, model=UVM_CODEGEN_MODEL)
                if response and response.strip():
                    return self._clean_response(response)
            except Exception as e:
                logger.warning(f"LLM fill failed for sequence item {block_type}: {e}")

        # Fallback to TransactionModelGenerator
        from VeriGenX.agents.uvmforge.transaction_model import TransactionModelGenerator
        gen = TransactionModelGenerator(signals)
        if block_type == "fields":
            return gen.generate_types_and_fields()
        elif block_type == "constraints":
            return gen.generate_constraints()
        elif block_type == "macros":
            macros = []
            for s in signals:
                if s["name"].lower() not in ["clk", "rst_n", "aclk", "aresetn"]:
                    macros.append(f"    `uvm_field_int({s['name']}, UVM_ALL_ON)")
            return "\n".join(macros)
        return ""

    def fill_driver_behavior(self, protocol: List[str], signals: List[Dict[str, Any]]) -> str:
        """Generates driver pin-level behavior from protocol rules."""
        if self.client.is_available():
            try:
                prompt_tmpl = get_prompt("uvmforge_fill_driver_behavior")
                prompt = prompt_tmpl.format(
                    signals=json.dumps(signals, indent=2),
                    protocol=json.dumps(protocol, indent=2)
                )
                logger.debug("Querying LLM for driver behavior")
                response = self.client.generate(prompt, model=UVM_CODEGEN_MODEL)
                if response and response.strip():
                    return self._clean_response(response)
            except Exception as e:
                logger.warning(f"LLM fill failed for driver behavior: {e}")

        # Fallback to Heuristics
        drive_stmts = []
        for s in signals:
            name_lower = s["name"].lower()
            is_clk_rst = any(k in name_lower for k in ["clk", "clock", "rst", "reset"])
            if s["direction"] == "input" and not is_clk_rst:
                drive_stmts.append(f"            vif.cb.{s['name']} <= req.{s['name']};")
        drive_code = "\n".join(drive_stmts)
        
        # Find clock name
        clk_name = "clk"
        for s in signals:
            if s["name"].lower() in ["clk", "clock", "aclk"]:
                clk_name = s["name"]
                break
                
        return f"""        @(posedge vif.{clk_name});
{drive_code}
        #10;"""

    def fill_monitor_behavior(self, protocol: List[str], signals: List[Dict[str, Any]]) -> str:
        """Generates monitor sampling logic."""
        if self.client.is_available():
            try:
                prompt_tmpl = get_prompt("uvmforge_fill_monitor_behavior")
                prompt = prompt_tmpl.format(
                    signals=json.dumps(signals, indent=2),
                    protocol=json.dumps(protocol, indent=2)
                )
                logger.debug("Querying LLM for monitor behavior")
                response = self.client.generate(prompt, model=UVM_CODEGEN_MODEL)
                if response and response.strip():
                    return self._clean_response(response)
            except Exception as e:
                logger.warning(f"LLM fill failed for monitor behavior: {e}")

        # Fallback to Heuristics
        mon_stmts = []
        for s in signals:
            name_lower = s["name"].lower()
            is_clk_rst = any(k in name_lower for k in ["clk", "clock", "rst", "reset"])
            if not is_clk_rst:
                mon_stmts.append(f"            tx.{s['name']} = vif.{s['name']};")
        mon_code = "\n".join(mon_stmts)
        
        # Find clock name
        clk_name = "clk"
        for s in signals:
            if s["name"].lower() in ["clk", "clock", "aclk"]:
                clk_name = s["name"]
                break
                
        # Find design name (will be replaced by caller or uses generic)
        return f"""        type_id_t tx;
        forever begin
            @(posedge vif.{clk_name});
            tx = type_id_t::type_id::create("tx"); // type_id_t replaced dynamically in caller
{mon_code}
            ap.write(tx);
        end"""

    def fill_scoreboard(self, dut_info: Dict[str, Any], functional_points: List[Dict[str, Any]]) -> str:
        """Generates scoreboard comparison logic with reference model."""
        dut_name = dut_info.get("design_name", "design")
        if self.client.is_available():
            try:
                prompt_tmpl = get_prompt("uvmforge_fill_scoreboard")
                prompt = prompt_tmpl.format(
                    dut_name=dut_name,
                    functional_points=json.dumps(functional_points, indent=2)
                )
                logger.debug("Querying LLM for scoreboard comparison")
                response = self.client.generate(prompt, model=UVM_CODEGEN_MODEL)
                if response and response.strip():
                    return self._clean_response(response)
            except Exception as e:
                logger.warning(f"LLM fill failed for scoreboard check: {e}")

        # Fallback to Heuristics
        return f"""        {dut_name}_seq_item expected;
        ref_model.predict(item, expected);
        if (!item.compare(expected)) begin
            `uvm_error("SB_MISMATCH", $sformatf("Transaction mismatch! Actual: %s, Expected: %s", item.convert2string(), expected.convert2string()))
        end else begin
            `uvm_info("SB_MATCH", $sformatf("Transaction match: %s", item.convert2string()), UVM_MEDIUM)
        end"""

    def fill_coverage(self, signals: List[Dict[str, Any]], functional_points: List[Dict[str, Any]], block_name: str) -> str:
        """Generates coverpoints, cross coverage, and edge bins."""
        if self.client.is_available():
            try:
                prompt_tmpl = get_prompt("uvmforge_fill_coverage")
                prompt = prompt_tmpl.format(
                    signals=json.dumps(signals, indent=2),
                    functional_points=json.dumps(functional_points, indent=2)
                )
                logger.debug(f"Querying LLM for coverage: {block_name}")
                response = self.client.generate(prompt, model=UVM_CODEGEN_MODEL)
                if response and response.strip():
                    return self._clean_response(response)
            except Exception as e:
                logger.warning(f"LLM fill failed for coverage: {e}")

        # Fallback to Heuristics
        if block_name == "coverage_sample":
            return "" # returns sampling statement wrapper handled outside or just sample call
            
        # Fallback to cycling / matching keywords
        desc = ""
        for fp in functional_points:
            if fp.get("id") == block_name:
                desc = fp.get("description", "").lower()
                break
        
        chosen_sig = None
        if desc:
            for s in signals:
                sname = s["name"].lower()
                if sname not in ["clk", "rst_n", "aclk", "aresetn"] and sname in desc:
                    chosen_sig = s["name"]
                    break
                    
        if not chosen_sig:
            filtered_sigs = [s["name"] for s in signals if s["name"].lower() not in ["clk", "rst_n", "aclk", "aresetn"]]
            if filtered_sigs:
                try:
                    fp_num = int(block_name.split("_")[-1])
                except Exception:
                    fp_num = 0
                chosen_sig = filtered_sigs[fp_num % len(filtered_sigs)]
            else:
                chosen_sig = "clk"
                
        return f"        cp_{block_name}: coverpoint t.{chosen_sig};"

    def generate_reference_model(self, dut_behavior: Dict[str, Any]) -> str:
        """Generates reference model prediction logic using uvm_report_error on mismatch/invalid input."""
        dut_name = dut_behavior.get("design_name", "design")
        if self.client.is_available():
            try:
                prompt_tmpl = get_prompt("uvmforge_generate_reference_model")
                prompt = prompt_tmpl.format(
                    dut_behavior=json.dumps(dut_behavior, indent=2)
                )
                logger.debug("Querying LLM for reference model logic")
                response = self.client.generate(prompt, model=UVM_CODEGEN_MODEL)
                if response and response.strip():
                    return self._clean_response(response)
            except Exception as e:
                logger.warning(f"LLM fill failed for reference model behavior: {e}")

        # Fallback to Heuristics
        return f"""    virtual function void predict({dut_name}_seq_item item, ref {dut_name}_seq_item expected);
        expected = {dut_name}_seq_item::type_id::create("expected");
        // Predict next expected outputs based on inputs.
        // Heuristically copy input fields to output fields.
        expected.copy(item);
    endfunction"""

    # ------------------------------------------------------------------ #
    #  Placeholder Fill Pipeline Router                                   #
    # ------------------------------------------------------------------ #

    def _get_fill(
        self,
        component_name: str,
        block_name: str,
        full_code: str,
        test_plan: Dict[str, Any]
    ) -> str:
        dut_name = test_plan.get("design_name", "design")
        signals = test_plan.get("signals", [])
        protocol = test_plan.get("protocol_handshake_rules", [])
        functional_points = test_plan.get("functional_points", [])

        # Routing to dedicated methods
        if block_name == "transaction_fields":
            return self.fill_sequence_item(signals, block_type="fields")
        elif block_name == "constraints":
            return self.fill_sequence_item(signals, block_type="constraints")
        elif block_name == "field_macros":
            return self.fill_sequence_item(signals, block_type="macros")
            
        elif block_name == "driver_drive_item":
            return self.fill_driver_behavior(protocol, signals)
            
        elif block_name == "monitor_run":
            # Call named monitor method and replace type_id_t dynamically
            mon_code = self.fill_monitor_behavior(protocol, signals)
            return mon_code.replace("type_id_t", f"{dut_name}_seq_item")
            
        elif block_name == "scoreboard_write":
            dut_info = {"design_name": dut_name, "signals": signals}
            return self.fill_scoreboard(dut_info, functional_points)
            
        elif block_name == "ref_model_predict":
            dut_behavior = {
                "design_name": dut_name,
                "signals": signals,
                "protocol_handshake_rules": protocol
            }
            return self.generate_reference_model(dut_behavior)
            
        elif block_name == "coverage_sample":
            # Coverage sample method fallback wrapper
            return f"        {dut_name}_cg.sample();"
            
        elif block_name.startswith("FP_"):
            return self.fill_coverage(signals, functional_points, block_name)

        # Standard system boilerplate blocks
        elif block_name == "interface_assertions":
            return "    // TODO: Add SystemVerilog assertions for protocol compliance checking"
            
        elif block_name == "sequence_body":
            return f"""        req = {dut_name}_seq_item::type_id::create("req");
        start_item(req);
        if (!req.randomize()) begin
            `uvm_fatal("SEQ", "Randomization failed")
        end
        finish_item(req);"""
        
        elif block_name == "driver_reset":
            rst_name = "rst_n"
            for s in signals:
                if "rst" in s["name"].lower() or "reset" in s["name"].lower():
                    rst_name = s["name"]
                    break
            return f"""        vif.{rst_name} <= 0;
        #100;
        vif.{rst_name} <= 1;"""

        return "    // Heuristic fill fallback"

    def _get_heuristic_fill(
        self,
        dut_name: str,
        component_name: str,
        block_name: str,
        test_plan: Dict[str, Any]
    ) -> str:
        """Compatibility method for older unit tests and generic fallbacks."""
        signals = test_plan.get("signals", [])
        protocol = test_plan.get("protocol_handshake_rules", [])
        functional_points = test_plan.get("functional_points", [])

        if block_name == "transaction_fields":
            from VeriGenX.agents.uvmforge.transaction_model import TransactionModelGenerator
            return TransactionModelGenerator(signals).generate_types_and_fields()
        elif block_name == "constraints":
            from VeriGenX.agents.uvmforge.transaction_model import TransactionModelGenerator
            return TransactionModelGenerator(signals).generate_constraints()
        elif block_name == "field_macros":
            macros = []
            for s in signals:
                if s["name"].lower() not in ["clk", "rst_n", "aclk", "aresetn"]:
                    macros.append(f"    `uvm_field_int({s['name']}, UVM_ALL_ON)")
            return "\n".join(macros)
        elif block_name == "driver_drive_item":
            drive_stmts = []
            for s in signals:
                name_lower = s["name"].lower()
                is_clk_rst = any(k in name_lower for k in ["clk", "clock", "rst", "reset"])
                if s["direction"] == "input" and not is_clk_rst:
                    drive_stmts.append(f"            vif.cb.{s['name']} <= req.{s['name']};")
            drive_code = "\n".join(drive_stmts)
            clk_name = "clk"
            for s in signals:
                if s["name"].lower() in ["clk", "clock", "aclk"]:
                    clk_name = s["name"]
                    break
            return f"""        @(posedge vif.{clk_name});
{drive_code}
        #10;"""
        elif block_name == "monitor_run":
            mon_stmts = []
            for s in signals:
                name_lower = s["name"].lower()
                is_clk_rst = any(k in name_lower for k in ["clk", "clock", "rst", "reset"])
                if not is_clk_rst:
                    mon_stmts.append(f"            tx.{s['name']} = vif.{s['name']};")
            mon_code = "\n".join(mon_stmts)
            clk_name = "clk"
            for s in signals:
                if s["name"].lower() in ["clk", "clock", "aclk"]:
                    clk_name = s["name"]
                    break
            return f"""        {dut_name}_seq_item tx;
        forever begin
            @(posedge vif.{clk_name});
            tx = {dut_name}_seq_item::type_id::create("tx");
{mon_code}
            ap.write(tx);
        end"""
        elif block_name == "scoreboard_write":
            return f"""        {dut_name}_seq_item expected;
        ref_model.predict(item, expected);
        if (!item.compare(expected)) begin
            `uvm_error("SB_MISMATCH", $sformatf("Transaction mismatch! Actual: %s, Expected: %s", item.convert2string(), expected.convert2string()))
        end else begin
            `uvm_info("SB_MATCH", $sformatf("Transaction match: %s", item.convert2string()), UVM_MEDIUM)
        end"""
        elif block_name == "ref_model_predict":
            return f"""    virtual function void predict({dut_name}_seq_item item, ref {dut_name}_seq_item expected);
        expected = {dut_name}_seq_item::type_id::create("expected");
        // Predict next expected outputs based on inputs.
        // Heuristically copy input fields to output fields.
        expected.copy(item);
    endfunction"""
        elif block_name == "coverage_sample":
            return f"        {dut_name}_cg.sample();"
        elif block_name.startswith("FP_"):
            desc = ""
            for fp in functional_points:
                if fp.get("id") == block_name:
                    desc = fp.get("description", "").lower()
                    break
            chosen_sig = None
            if desc:
                for s in signals:
                    sname = s["name"].lower()
                    if sname not in ["clk", "rst_n", "aclk", "aresetn"] and sname in desc:
                        chosen_sig = s["name"]
                        break
            if not chosen_sig:
                filtered_sigs = [s["name"] for s in signals if s["name"].lower() not in ["clk", "rst_n", "aclk", "aresetn"]]
                if filtered_sigs:
                    try:
                        fp_num = int(block_name.split("_")[-1])
                    except Exception:
                        fp_num = 0
                    chosen_sig = filtered_sigs[fp_num % len(filtered_sigs)]
                else:
                    chosen_sig = "clk"
            return f"        cp_{block_name}: coverpoint t.{chosen_sig};"
            
        elif block_name == "interface_assertions":
            return "    // TODO: Add SystemVerilog assertions for protocol compliance checking"
        elif block_name == "sequence_body":
            return f"""        req = {dut_name}_seq_item::type_id::create("req");
        start_item(req);
        if (!req.randomize()) begin
            `uvm_fatal("SEQ", "Randomization failed")
        end
        finish_item(req);"""

        return "    // Heuristic fill fallback"
