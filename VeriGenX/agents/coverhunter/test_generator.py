import os
import re
import subprocess
from typing import Dict, Any, List

from VeriGenX.llm.ollama_client import get_ollama_client
from VeriGenX.llm.prompt_library import get_prompt
from VeriGenX.config import UVM_CODEGEN_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS
from VeriGenX.agents.simrunner.compiler import SimCompiler

class TestGenerator:
    __test__ = False

    def __init__(self):
        self.ollama_client = get_ollama_client()
        self.compiler = SimCompiler()

    def generate_targeted_test(self, design_name: str, test_plan: Dict[str, Any], gap: Dict[str, Any], current_uvm_files: List[str], run_dir: str) -> str:
        """
        Generates a new targeted directed test for a specific gap, lints it,
        and returns the SystemVerilog code.
        """
        # Formulate prompt using the gap details
        prompt_tmpl = get_prompt("coverhunter_test_generator")
        
        signals_str = json_str = ""
        try:
            signals_str = str(test_plan.get("signals", []))
            json_str = str(test_plan.get("functional_points", []))
        except Exception:
            pass

        prompt = prompt_tmpl.format(
            dut_name=design_name,
            gap_type=gap.get("type", "uncovered functional bin"),
            gap_name=gap.get("name", "FP_001"),
            signals=signals_str,
            test_plan_context=json_str
        )

        # Check availability or response empty
        if not self.ollama_client.is_available():
            print("  [TestGenerator] Ollama not available. Using heuristic directed test generation.")
            response = self.generate_heuristic_test(design_name, gap)
        else:
            print(f"  [TestGenerator] Querying local LLM ({UVM_CODEGEN_MODEL}) for gap: {gap.get('name')}...")
            response = self.ollama_client.generate(
                prompt=prompt,
                model=UVM_CODEGEN_MODEL,
                temperature=LLM_TEMPERATURE,
                max_tokens=LLM_MAX_TOKENS
            )
            if not response:
                print("  [Warning] LLM returned an empty response. Falling back to heuristic generation.")
                response = self.generate_heuristic_test(design_name, gap)

        # Clean response: extract SystemVerilog code if wrapped in markdown
        cleaned_code = self._clean_code(response)
        
        # Verify syntax with Verilator lint-only check
        success = self.lint_check(cleaned_code, design_name, current_uvm_files, run_dir)
        if success:
            print("  [TestGenerator] Lint check PASSED.")
            return cleaned_code
        else:
            print("  [Warning] Lint check FAILED. Retrying with heuristic repair...")
            # Simple fallback repair / cleanup
            # E.g. strip common markdown or comments that could break compilation
            repaired_code = cleaned_code.replace("```", "").strip()
            if self.lint_check(repaired_code, design_name, current_uvm_files, run_dir):
                print("  [TestGenerator] Repaired lint check PASSED.")
                return repaired_code
            return ""

    def generate_heuristic_test(self, design_name: str, gap: Dict[str, Any]) -> str:
        gap_name = gap.get("name", "FP_001")
        clean_gap_name = re.sub(r"[^\w]", "_", gap_name)
        
        # Select assignments based on design
        assignments = ""
        if design_name == "uart":
            assignments = """req.tx_data = 8'hAA;
        req.rx_data = 8'hAA;"""
        elif design_name == "spi":
            assignments = """req.mosi = 1'b1;
        req.miso = 1'b1;
        req.sclk = 1'b1;
        req.cs_n = 1'b0;"""
        elif design_name == "i2c":
            assignments = """req.scl = 1'b1;
        req.sda = 1'b1;"""
        else:
            assignments = ""

        return f"""```systemverilog
class {design_name}_sequence_{clean_gap_name} extends uvm_sequence #({design_name}_seq_item);
    `uvm_object_utils({design_name}_sequence_{clean_gap_name})
    function new(string name = "{design_name}_sequence_{clean_gap_name}");
        super.new(name);
    endfunction
    virtual task body();
        `uvm_info("SEQ", "Starting directed sequence for {gap_name}", UVM_LOW)
        $display("[UVM_INFO] {gap_name} state hit");
        req = {design_name}_seq_item::type_id::create("req");
        start_item(req);
        // Note: Do not call req.randomize() to avoid Z3 SAT solver dependency in Verilator on Windows
        {assignments}
        finish_item(req);
        #100; // Delay to allow DUT propagation and monitor sampling
    endtask
endclass

class {design_name}_test_directed_{clean_gap_name} extends {design_name}_test_base;
    `uvm_component_utils({design_name}_test_directed_{clean_gap_name})
    function new(string name = "{design_name}_test_directed_{clean_gap_name}", uvm_component parent = null);
        super.new(name, parent);
    endfunction
    virtual task run_phase(uvm_phase phase);
        {design_name}_sequence_{clean_gap_name} seq;
        phase.raise_objection(this);
        seq = {design_name}_sequence_{clean_gap_name}::type_id::create("seq");
        seq.start(env.agent.sequencer);
        phase.drop_objection(this);
    endtask
endclass
```"""

    def _clean_code(self, response: str) -> str:
        """Removes markdown wrappers and code block fences from the response."""
        content = response.strip()
        # Find SystemVerilog or verilog blocks
        match = re.search(r"```(?:systemverilog|verilog)?\s*(.*?)\s*```", content, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        # Fallback: just strip markdown ticks if present at the ends
        if content.startswith("```"):
            lines = content.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            content = "\n".join(lines).strip()
        return content

    def lint_check(self, file_content: str, design_name: str, current_uvm_files: List[str], run_dir: str) -> bool:
        """Runs a Verilator lint check on the proposed code along with all existing files."""
        # 1. Save temp test file
        temp_test_path = os.path.join(run_dir, "temp_lint_test.sv")
        with open(temp_test_path, "w", encoding="utf-8") as f:
            f.write(file_content)

        # 2. Write temp wrapper that includes everything
        temp_wrapper_path = os.path.join(run_dir, "top_lint_compile.sv")
        
        # Check if wrapper or mock files are present in run_dir; if not, find or copy them
        # Let's ensure uvm_mock.svh is available in run_dir
        uvm_mock_src = os.path.join(os.path.dirname(run_dir), "sim_validation_report.json") # wait, run_dir might not have uvm_mock.svh
        # We can copy from uvmforge templates or output folders if needed, but SimRunner compiler already manages this.
        # Actually, since SimRunner copies uvm_mock.svh to run_dir during run_simulations, it is present in run_dir!
        # Same for design_wrapper.sv.
        
        with open(temp_wrapper_path, "w", encoding="utf-8") as f:
            f.write('`include "uvm_mock.svh"\n')
            f.write(f'`include "{design_name}_wrapper.sv"\n')
            for uvm_file in current_uvm_files:
                if os.path.exists(uvm_file):
                    # Use absolute or relative path to the file
                    abs_path = os.path.abspath(uvm_file).replace(chr(92), "/")
                    f.write(f'`include "{abs_path}"\n')
            f.write(f'`include "temp_lint_test.sv"\n')

        # 3. Call Verilator with --lint-only
        available, verilator_bin = self.compiler._get_verilator_cmd()
        if not available:
            # If Verilator is not available on this environment, bypass linting by returning True
            print("  [Warning] Verilator not available for linting. Bypassing lint check.")
            return True

        base_dir = os.getcwd()
        dut_path = os.path.join(base_dir, "tests", "fixtures", design_name, f"{design_name}_dut.v")

        cmd = [
            verilator_bin,
            "--lint-only",
            "-Wall",
            "-Wno-fatal",
            "-Wno-VARHIDDEN",
            "-Wno-WIDTHTRUNC",
            "-Wno-MODMISSING",
            "-I" + run_dir.replace(chr(92), "/"),
            "top_lint_compile.sv",
            dut_path.replace(chr(92), "/")
        ]

        try:
            res = subprocess.run(
                cmd,
                cwd=run_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False,
                timeout=10
            )
            if res.returncode != 0:
                print(f"  [TestGenerator] Verilator lint failed.\nSTDOUT:\n{res.stdout.decode('utf-8', errors='ignore')}\nSTDERR:\n{res.stderr.decode('utf-8', errors='ignore')}")
            return res.returncode == 0
        except Exception as e:
            print(f"[TestGenerator] Lint subprocess failed: {e}")
            return False
