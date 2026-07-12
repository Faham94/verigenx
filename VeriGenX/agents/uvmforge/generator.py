"""
UVMForge: Generator Orchestrator
Loads templates, renders static structures, triggers LLM filler, and runs repair loops.
"""
import os
import json
from typing import Dict, Any, List, Tuple

from jinja2 import Environment, FileSystemLoader, nodes
from jinja2.ext import Extension

from VeriGenX.state_bus import get_state_bus
from VeriGenX.agents.archweaver.resolver import Resolver
from VeriGenX.agents.uvmforge.llm_filler import LLMFiller
from VeriGenX.agents.uvmforge.repair import UVMForgeRepair
from VeriGenX.config import GENERATED_UVM_DIR


class LlmFillExtension(Extension):
    tags = {"llm_fill"}

    def parse(self, parser):
        # Consume the tag name 'llm_fill'
        tag_token = next(parser.stream)
        lineno = tag_token.lineno
        args = []
        if parser.stream.current.type != 'block_end':
            args.append(parser.parse_expression())
        
        # Do not expect block_end here as parse_statements expects it
        body = parser.parse_statements(("name:endllm_fill",), drop_needle=True)
        
        return nodes.CallBlock(
            self.call_method("_fill_placeholder", args),
            [],
            [],
            body
        ).set_lineno(lineno)

    def _fill_placeholder(self, block_name, caller):
        default_content = caller()
        return f"{{% llm_fill \"{block_name}\" %}}\n{default_content}\n{{% endllm_fill %}}"


class UVMForgeGenerator:

    def __init__(self):
        self.state_bus = get_state_bus()
        self.llm_filler = LLMFiller()
        self.repair_helper = UVMForgeRepair()
        self.templates_dir = os.path.join(os.path.dirname(__file__), "templates")
        self.jinja_env = Environment(
            loader=FileSystemLoader(self.templates_dir),
            extensions=[LlmFillExtension]
        )

    def _find_clk_rst_names(self, signals: List[Dict[str, Any]]) -> Tuple[str, str]:
        """Heuristically find system clock and reset names from signals list."""
        clk_name = "clk"
        rst_name = "rst_n"
        
        # Primary search for exact standard names
        for s in signals:
            name = s["name"].lower()
            if name in ["clk", "aclk", "clock"]:
                clk_name = s["name"]
            if name in ["rst_n", "aresetn", "rst", "reset_n"]:
                rst_name = s["name"]

        # Secondary search if standard names not found
        if clk_name == "clk":
            for s in signals:
                name = s["name"].lower()
                if "clk" in name or "clock" in name:
                    clk_name = s["name"]
                    break
        if rst_name == "rst_n":
            for s in signals:
                name = s["name"].lower()
                if "rst" in name or "reset" in name:
                    rst_name = s["name"]
                    break
                    
        return clk_name, rst_name

    def generate_all(self, test_plan: Dict[str, Any], dag: Dict[str, Any]) -> List[str]:
        """
        Orchestrates UVM code generation for all components topologically.
        """
        resolver = Resolver()
        generation_order = resolver.get_generation_order(dag)
        
        dut_name = test_plan.get("design_name", "design")
        signals = test_plan.get("signals", [])
        clk_name, rst_name = self._find_clk_rst_names(signals)
        protocol_rules = test_plan.get("protocol_handshake_rules", [])
        functional_points = test_plan.get("functional_points", [])

        os.makedirs(GENERATED_UVM_DIR, exist_ok=True)
        generated_filepaths = []
        
        # Keep track of compile metrics
        total_compiled = 0
        first_attempt_clean = 0
        compile_results = {}
        
        # Mapping from DAG component names to template files
        comp_to_template = {
            "interface": "interface.sv.j2",
            "sequence_item": "seq_item.sv.j2",
            "sequence": "sequence.sv.j2",
            "driver": "driver.sv.j2",
            "monitor": "monitor.sv.j2",
            "agent": "agent.sv.j2",
            "scoreboard": "scoreboard.sv.j2",
            "coverage": "coverage.sv.j2",
            "env": "env.sv.j2",
            "test_base": "test_base.sv.j2",
            "test_directed": "test_directed.sv.j2",
            "test_random": "test_directed.sv.j2", # Falls back to directed structure but gets specialized name
            "top": "top.sv.j2",
        }

        print(f"\n[UVMForge] Starting testbench generation for design: {dut_name}")
        
        for item in generation_order:
            comp = item["component"]
            filename = item["filename"]
            
            tmpl_name = comp_to_template.get(comp)
            if not tmpl_name:
                print(f"  [Warning] No template found for component: {comp}. Skipping.")
                continue

            print(f"  [{item['order']}/{len(generation_order)}] Generating {comp} -> {filename}...")
            
            try:
                template = self.jinja_env.get_template(tmpl_name)
            except Exception as e:
                print(f"  [Error] Failed to load template {tmpl_name}: {e}")
                continue

            # Render template
            rendered = template.render(
                dut_name=dut_name,
                signals=signals,
                clk_name=clk_name,
                rst_name=rst_name,
                protocol_rules=protocol_rules,
                functional_points=functional_points
            )

            # Specialize names if component is a variant (e.g. test_random)
            if comp == "test_random":
                rendered = rendered.replace(f"{dut_name}_test_directed", f"{dut_name}_test_random")
                rendered = rendered.replace(f"{dut_name}_sequence", f"{dut_name}_random_sequence")

            # Fill LLM designated placeholders
            final_code = self.llm_filler.fill_placeholders(comp, rendered, test_plan)

            # Write file
            filepath = os.path.join(GENERATED_UVM_DIR, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(final_code)
                
            generated_filepaths.append(filepath)

            # Run compile checks and repair loop
            if self.repair_helper.is_verilator_available():
                total_compiled += 1
                clean, err_msg = self.repair_helper.compile_file(filepath)
                first_attempt = clean
                if clean:
                    first_attempt_clean += 1
                    status = "passed"
                    errors = ""
                else:
                    status = "failed"
                    errors = err_msg
                    # Run repair loop if compile failed
                    self.repair_helper.repair_file(filepath, comp, test_plan)
                    # Check if compile is fixed after repair
                    repaired_clean, repaired_err = self.repair_helper.compile_file(filepath)
                    if repaired_clean:
                        status = "passed"
                        errors = ""
                    else:
                        errors = repaired_err
                
                compile_results[filename] = {
                    "status": status,
                    "first_attempt": first_attempt,
                    "errors": errors
                }
            else:
                compile_results[filename] = {
                    "status": "not-tested",
                    "first_attempt": False,
                    "errors": ""
                }

        # Log compile metrics if compiling was active
        if total_compiled > 0:
            rate = (first_attempt_clean / total_compiled) * 100
            print(f"\n[UVMForge] Compile Success Rate on first attempt: {rate:.1f}% ({first_attempt_clean}/{total_compiled})")
        else:
            rate = 0.0
            print("\n[UVMForge] Verilator not available. Compilation checks were skipped.")

        # Save compile report JSON
        report_path = os.path.join(GENERATED_UVM_DIR, "compile_report.json")
        existing_report = {}
        if os.path.exists(report_path):
            try:
                with open(report_path, "r", encoding="utf-8") as f:
                    existing_report = json.load(f)
            except Exception:
                pass
        
        verilator_avail = self.repair_helper.is_verilator_available()
        existing_report[dut_name] = {
            "verilator_available": verilator_avail,
            "first_attempt_success_rate": rate,
            "files": compile_results
        }
        
        try:
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(existing_report, f, indent=4)
        except Exception as e:
            print(f"  [Warning] Failed to write compile report: {e}")

        # Update State Bus
        self.state_bus.update_state(generated_files=generated_filepaths)
        return generated_filepaths
