"""
UVMForge: LLM Filler
Fills design-specific placeholders in UVM SystemVerilog templates.
"""
import re
import json
from typing import Dict, Any

from VeriGenX.llm.ollama_client import get_ollama_client
from VeriGenX.llm.prompt_library import get_prompt
from VeriGenX.config import UVM_CODEGEN_MODEL


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
            # Retain the comments so that it's clear what was filled (and for possible parsing/repair later)
            return start_tag + "\n" + filled_code + "\n// {% endllm_fill %}"

        # We execute the regex substitution
        return re.sub(pattern, replace_match, content, flags=re.DOTALL)

    def _get_fill(
        self,
        component_name: str,
        block_name: str,
        full_code: str,
        test_plan: Dict[str, Any]
    ) -> str:
        dut_name = test_plan.get("design_name", "design")
        
        # Build test plan context string
        tp_context = {
            "signals": test_plan.get("signals", []),
            "fsm_states": test_plan.get("fsm_states", []),
            "register_map": test_plan.get("register_map", []),
            "functional_points": test_plan.get("functional_points", []),
            "protocol_handshake_rules": test_plan.get("protocol_handshake_rules", []),
            "firmware_programming_model": test_plan.get("firmware_programming_model", []),
        }
        test_plan_context_str = json.dumps(tp_context, indent=2)

        # Truncate full code in prompt if too large
        code_context = full_code if len(full_code) < 2000 else full_code[:2000] + "\n... [truncated] ..."

        # Attempt to run LLM
        if self.client.is_available():
            try:
                prompt_tmpl = get_prompt("uvmforge_placeholder_fill")
                prompt = prompt_tmpl.format(
                    dut_name=dut_name,
                    test_plan_context=test_plan_context_str,
                    block_name=block_name,
                    component_name=component_name,
                    code_context=code_context
                )
                response = self.client.generate(prompt, model=UVM_CODEGEN_MODEL)
                if response and response.strip():
                    # Clean markdown codeblocks from response if any
                    clean_response = response.strip()
                    if clean_response.startswith("```"):
                        lines = clean_response.splitlines()
                        if lines[0].startswith("```"):
                            lines = lines[1:]
                        if lines and lines[-1].startswith("```"):
                            lines = lines[:-1]
                        clean_response = "\n".join(lines).strip()
                    return clean_response
            except Exception as e:
                print(f"  [Warning] LLM fill failed for {block_name}: {e}")

        # Fallback to heuristics if LLM is offline or fails
        return self._get_heuristic_fill(dut_name, component_name, block_name, test_plan)

    def _get_heuristic_fill(
        self,
        dut_name: str,
        component_name: str,
        block_name: str,
        test_plan: Dict[str, Any]
    ) -> str:
        """
        Detailed heuristic fallback generators when Ollama is unavailable.
        """
        signals = test_plan.get("signals", [])
        
        # Find clock name
        clk_name = "clk"
        for s in signals:
            if s["name"].lower() in ["clk", "clock", "aclk"]:
                clk_name = s["name"]
                break
        
        if block_name == "interface_assertions":
            return "    // TODO: Add SystemVerilog assertions for protocol compliance checking"
            
        elif block_name == "transaction_fields":
            fields = []
            for s in signals:
                if s["name"] not in ["clk", "rst_n", "aclk", "aresetn"]:
                    width_decl = f"[{s['width']-1}:0]" if s["width"] > 1 else ""
                    fields.append(f"    rand bit {width_decl} {s['name']};")
            return "\n".join(fields) if fields else "    // rand bit fields;"
            
        elif block_name == "field_macros":
            macros = []
            for s in signals:
                if s["name"] not in ["clk", "rst_n", "aclk", "aresetn"]:
                    macros.append(f"    `uvm_field_int({s['name']}, UVM_ALL_ON)")
            return "\n".join(macros) if macros else "    // `uvm_field_int"
            
        elif block_name == "constraints":
            return "    // Constraint blocks for transaction randomization\n    // e.g., constraint c_valid { ... }"
            
        elif block_name == "sequence_body":
            return f"""        req = {dut_name}_seq_item::type_id::create("req");
        start_item(req);
        if (!req.randomize()) begin
            `uvm_fatal("SEQ", "Randomization failed")
        end
        finish_item(req);"""
        
        elif block_name == "driver_reset":
            # Find active-low reset name
            rst_name = "rst_n"
            for s in signals:
                if "rst" in s["name"].lower() or "reset" in s["name"].lower():
                    rst_name = s["name"]
                    break
            return f"""        vif.{rst_name} <= 0;
        #100;
        vif.{rst_name} <= 1;"""

        elif block_name == "driver_drive_item":
            # Generate code to drive inputs
            drive_stmts = []
            for s in signals:
                if s["direction"] == "input" and s["name"] not in ["clk", "rst_n", "aclk", "aresetn"]:
                    drive_stmts.append(f"            vif.cb.{s['name']} <= req.{s['name']};")
            drive_code = "\n".join(drive_stmts)
            return f"""        @(posedge vif.{clk_name});
{drive_code}
        #10;"""

        elif block_name == "monitor_run":
            # Collect outputs into transaction
            mon_stmts = []
            for s in signals:
                if s["name"] not in ["clk", "rst_n", "aclk", "aresetn"]:
                    mon_stmts.append(f"            tx.{s['name']} = vif.{s['name']};")
            mon_code = "\n".join(mon_stmts)
            return f"""        {dut_name}_seq_item tx;
        forever begin
            @(posedge vif.{clk_name});
            tx = {dut_name}_seq_item::type_id::create("tx");
{mon_code}
            ap.write(tx);
        end"""

        elif block_name == "ref_model_predict":
            return f"""    virtual function void predict({dut_name}_seq_item item, ref {dut_name}_seq_item expected);
        expected = {dut_name}_seq_item::type_id::create("expected");
        // Predict next expected outputs based on inputs
    endfunction"""

        elif block_name == "scoreboard_write":
            return f"""        {dut_name}_seq_item expected;
        ref_model.predict(item, expected);
        if (!item.compare(expected)) begin
            `uvm_error("SB_MISMATCH", $sformatf("Transaction mismatch! Actual: %s, Expected: %s", item.convert2string(), expected.convert2string()))
        end else begin
            `uvm_info("SB_MATCH", $sformatf("Transaction match: %s", item.convert2string()), UVM_MEDIUM)
        end"""

        elif block_name == "coverage_sample":
            return f"        {dut_name}_cg.sample();"

        elif block_name.startswith("FP_"):
            # Try to match keywords in description to find relevant signal
            desc = ""
            for fp in test_plan.get("functional_points", []):
                if fp.get("id") == block_name:
                    desc = fp.get("description", "").lower()
                    break
            
            chosen_sig = None
            if desc:
                # Rank signals based on keyword overlap
                for s in signals:
                    sname = s["name"].lower()
                    if sname not in ["clk", "rst_n", "aclk", "aresetn"] and sname in desc:
                        chosen_sig = s["name"]
                        break
            
            # Fallback 1: match keywords/synonyms
            if not chosen_sig and desc:
                term_map = {
                    "transmit": ["tx", "mosi", "sda"],
                    "receive": ["rx", "miso", "sda"],
                    "data": ["data", "sda", "mosi", "miso", "wdata", "rdata"],
                    "address": ["addr", "awaddr", "araddr"],
                    "valid": ["valid", "ready"],
                    "ready": ["ready", "valid"],
                    "select": ["cs", "cs_n", "sel"],
                    "enable": ["en", "wr_en", "rd_en"],
                    "full": ["full"],
                    "empty": ["empty"],
                    "reset": ["rst", "reset"],
                }
                for term, synonyms in term_map.items():
                    if term in desc:
                        for syn in synonyms:
                            for s in signals:
                                if syn in s["name"].lower() and s["name"].lower() not in ["clk", "rst_n", "aclk", "aresetn"]:
                                    chosen_sig = s["name"]
                                    break
                            if chosen_sig:
                                break
                    if chosen_sig:
                        break
            
            # Fallback 2: cycle through signals
            if not chosen_sig:
                filtered_sigs = [s["name"] for s in signals if s["name"].lower() not in ["clk", "rst_n", "aclk", "aresetn"]]
                if not filtered_sigs:
                    filtered_sigs = [s["name"] for s in signals]
                
                if filtered_sigs:
                    try:
                        fp_num = int(block_name.split("_")[-1])
                    except Exception:
                        fp_num = 0
                    chosen_sig = filtered_sigs[fp_num % len(filtered_sigs)]
                else:
                    chosen_sig = "clk"

            return f"        cp_{block_name}: coverpoint t.{chosen_sig};"

        return "    // Heuristic fill fallback"
