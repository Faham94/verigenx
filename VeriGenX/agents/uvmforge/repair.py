"""
UVMForge: Repair Loop
Runs compiler check, classifies errors, and queries LLM for fixes.
"""
import os
import re
import shutil
import subprocess
from typing import Dict, Any, Optional, Tuple

from VeriGenX.llm.ollama_client import get_ollama_client
from VeriGenX.llm.prompt_library import get_prompt
from VeriGenX.config import REPAIR_MODEL


class UVMForgeRepair:

    def __init__(self):
        self.client = get_ollama_client()

    def _get_verilator_cmd(self) -> Tuple[bool, str]:
        """
        Locates the verilator executable.
        Returns (available, cmd_path)
        """
        # Option 1: check standard path
        try:
            subprocess.run(
                ["verilator", "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False,
                check=True
            )
            return True, "verilator"
        except Exception:
            pass

        # Option 2: check MSYS2 path
        msys_verilator = r"C:\msys64\mingw64\bin\verilator_bin.exe"
        if os.path.exists(msys_verilator):
            # Set VERILATOR_ROOT for MSYS2 Verilator to find its library files
            os.environ["VERILATOR_ROOT"] = r"C:\msys64\mingw64\share\verilator"
            return True, msys_verilator

        return False, ""

    def is_verilator_available(self) -> bool:
        """Checks if verilator command is available."""
        available, _ = self._get_verilator_cmd()
        return available

    def classify_error(self, stderr: str) -> str:
        """Classifies compiler errors based on patterns."""
        if not stderr:
            return "unknown"
        
        lower_stderr = stderr.lower()
        if any(p in lower_stderr for p in ["syntax error", "unexpected", "expecting", "parse error"]):
            return "syntax_error"
        if any(p in lower_stderr for p in ["not declared", "unknown identifier", "could not find", "not found"]):
            return "undeclared_identifier"
        if any(p in lower_stderr for p in ["type mismatch", "incompatible types", "cannot assign"]):
            return "type_mismatch"
        if any(p in lower_stderr for p in ["port connection", "width mismatch", "pin connection", "port mismatch"]):
            return "port_mismatch"
            
        return "other"

    def compile_file(self, filepath: str) -> Tuple[bool, str]:
        """
        Compiles the file with Verilator.
        If Verilator is not installed, it returns (True, "Verilator not installed")
        """
        available, cmd = self._get_verilator_cmd()
        if not available:
            return True, "Verilator not installed"

        try:
            uvm_mock_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "uvm_mock.svh"))
            
            # Find all generated files of the same design in the directory to compile together
            dir_name = os.path.dirname(filepath)
            base_name = os.path.basename(filepath)
            design_prefix = base_name.split("_")[0] + "_"
            
            design_files = []
            if os.path.exists(dir_name):
                for f in os.listdir(dir_name):
                    if f.startswith(design_prefix) and f.endswith(".sv"):
                        design_files.append(os.path.join(dir_name, f))
            
            # Sort files topologically to prevent forward declaration reference errors
            suffix_order = [
                "_interface.sv",
                "_sequence_item.sv",
                "_sequence.sv",
                "_random_sequence.sv",
                "_driver.sv",
                "_monitor.sv",
                "_agent.sv",
                "_scoreboard.sv",
                "_coverage.sv",
                "_env.sv",
                "_test_base.sv",
                "_test_directed.sv",
                "_test_random.sv",
                "_top.sv"
            ]
            def get_sort_key(fp):
                fn = os.path.basename(fp)
                for idx, suffix in enumerate(suffix_order):
                    if fn.endswith(suffix):
                        return idx
                return len(suffix_order)
            
            design_files.sort(key=get_sort_key)
            
            if not design_files:
                design_files = [filepath]

            # Run verilator linter check
            result = subprocess.run(
                [
                    cmd, "--lint-only", 
                    "-Wno-fatal", "-Wno-EOFNEWLINE", "-Wno-DECLFILENAME", 
                    "-Wno-VARHIDDEN", "-Wno-WIDTHTRUNC", "-Wno-MODMISSING",
                    uvm_mock_path
                ] + design_files,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False,
                text=True
            )
            if result.returncode == 0:
                return True, ""
            else:
                return False, result.stderr
        except Exception as e:
            return False, str(e)

    def repair_file(
        self,
        filepath: str,
        component_name: str,
        test_plan: Dict[str, Any],
        max_retries: int = 3
    ) -> bool:
        """
        Attempts to repair compilation issues on the file up to max_retries.
        Returns True if compiled cleanly (or Verilator not available),
        returns False and restores last known version if retries are exhausted.
        """
        # 1. Compile initially
        clean, output = self.compile_file(filepath)
        if clean:
            return True

        print(f"  [Repair] Compiler errors detected in {os.path.basename(filepath)}. Starting repair loop...")
        
        # Keep backup of the initial file version
        backup_path = filepath + ".bak"
        shutil.copyfile(filepath, backup_path)
        
        success = False
        try:
            for attempt in range(1, max_retries + 1):
                error_type = self.classify_error(output)
                print(f"  [Repair] Attempt {attempt}/{max_retries} | Error Type: {error_type}")
                
                # Retrieve current file content
                with open(filepath, "r", encoding="utf-8") as f:
                    file_content = f.read()

                # Attempt LLM repair
                if not self.client.is_available():
                    print("  [Repair] LLM unavailable for repair loop — aborting repair")
                    break

                try:
                    prompt_tmpl = get_prompt("uvmforge_repair_fix")
                    prompt = prompt_tmpl.format(
                        filename=os.path.basename(filepath),
                        component_name=component_name,
                        error_type=error_type,
                        compiler_output=output,
                        file_content=file_content
                    )
                    corrected_content = self.client.generate(prompt, model=REPAIR_MODEL)
                    
                    if corrected_content and corrected_content.strip():
                        # Clean markdown formatting from LLM response if present
                        clean_content = corrected_content.strip()
                        if clean_content.startswith("```"):
                            lines = clean_content.splitlines()
                            if lines[0].startswith("```"):
                                lines = lines[1:]
                            if lines and lines[-1].startswith("```"):
                                lines = lines[:-1]
                            clean_content = "\n".join(lines).strip()
                            
                        # Save the repaired file
                        with open(filepath, "w", encoding="utf-8") as f:
                            f.write(clean_content)

                        # Re-compile
                        clean, output = self.compile_file(filepath)
                        if clean:
                            print(f"  [Repair] Repair successful on attempt {attempt}!")
                            success = True
                            break
                except Exception as e:
                    print(f"  [Repair] Error during repair iteration {attempt}: {e}")
            
            if not success:
                print(f"  [Repair] Failed to repair {os.path.basename(filepath)} after {max_retries} attempts. Flagged for human review.")
                # Restore original backup
                shutil.copyfile(backup_path, filepath)
                
        finally:
            # Clean up backup file
            if os.path.exists(backup_path):
                os.remove(backup_path)

        return success
