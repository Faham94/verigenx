"""
UVMForge: Repair Loop
Runs compiler check, classifies errors, and queries LLM for fixes.
"""
import os
import re
import shutil
import json
import subprocess
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

from VeriGenX.llm.ollama_client import get_ollama_client
from VeriGenX.llm.prompt_library import get_prompt
from VeriGenX.config import REPAIR_MODEL
from VeriGenX.agents.uvmforge.logger import get_logger

logger = get_logger("repair")


class UVMForgeRepair:

    def __init__(self):
        self.client = get_ollama_client()
        # Unique run ID for backup iteration directories
        self.run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

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
        if any(p in lower_stderr for p in ["timeout", "race condition", "phase loop", "objection deadlock", "time limit", "join_any", "join_none"]):
            return "timing"
        if any(p in lower_stderr for p in ["syntax error", "unexpected", "expecting", "parse error"]):
            return "syntax_error"
        if any(p in lower_stderr for p in ["not declared", "unknown identifier", "could not find", "not found"]):
            return "undeclared_identifier"
        if any(p in lower_stderr for p in ["type mismatch", "incompatible types", "cannot assign"]):
            return "type_mismatch"
        if any(p in lower_stderr for p in ["port connection", "width mismatch", "pin connection", "port mismatch"]):
            return "port_mismatch"
            
        return "other"

    def _count_errors(self, stderr: str) -> int:
        """Counts occurrences of %Error in the compiler output."""
        if not stderr:
            return 0
        return len(re.findall(r"%Error", stderr))

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

    def _log_attempt(self, filepath: str, attempts: int, success: bool, error_types: list):
        """Saves a record of the repair attempt to output/repair_attempts.json."""
        attempts_path = "output/repair_attempts.json"
        os.makedirs("output", exist_ok=True)
        
        existing_attempts = []
        if os.path.exists(attempts_path):
            try:
                with open(attempts_path, "r", encoding="utf-8") as f:
                    existing_attempts = json.load(f)
            except Exception:
                pass
                
        existing_attempts.append({
            "filepath": filepath,
            "run_id": self.run_id,
            "attempts": attempts,
            "success": success,
            "error_types_encountered": error_types
        })
        
        try:
            with open(attempts_path, "w", encoding="utf-8") as f:
                json.dump(existing_attempts, f, indent=4)
        except Exception as e:
            logger.warning(f"Failed to save repair attempt log: {e}")

    def repair_file(
        self,
        filepath: str,
        component_name: str,
        test_plan: Dict[str, Any],
        max_retries: int = 5
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

        filename = os.path.basename(filepath)
        logger.warning(f"Compiler errors detected in {filename}. Starting repair loop...")
        
        error_types_encountered = []
        current_error_count = self._count_errors(output)
        success = False
        
        try:
            for attempt in range(1, max_retries + 1):
                error_type = self.classify_error(output)
                error_types_encountered.append(error_type)
                
                logger.info(f"Repair Attempt {attempt}/{max_retries} | Error Type: {error_type} | Count: {current_error_count}")
                
                # Backup iteration's starting version (iter_N represents attempt N)
                backup_dir = f"output/{self.run_id}/backups/iter_{attempt}"
                os.makedirs(backup_dir, exist_ok=True)
                backup_path = os.path.join(backup_dir, filename)
                shutil.copyfile(filepath, backup_path)
                
                # Retrieve current file content
                with open(filepath, "r", encoding="utf-8") as f:
                    file_content = f.read()

                # Attempt LLM repair
                if not self.client.is_available():
                    logger.warning("LLM unavailable for repair loop — aborting repair")
                    break

                try:
                    prompt_tmpl = get_prompt("uvmforge_repair_fix")
                    prompt = prompt_tmpl.format(
                        filename=filename,
                        component_name=component_name,
                        error_type=error_type,
                        compiler_output=output,
                        file_content=file_content
                    )
                    corrected_content = self.client.generate(prompt, model=REPAIR_MODEL)
                    
                    if corrected_content and corrected_content.strip():
                        # Clean markdown formatting from LLM response if present
                        clean_content = self._clean_response(corrected_content)
                            
                        # Save the repaired file
                        with open(filepath, "w", encoding="utf-8") as f:
                            f.write(clean_content)

                        # Re-compile
                        new_clean, new_output = self.compile_file(filepath)
                        new_error_count = self._count_errors(new_output)
                        
                        if new_clean:
                            logger.info(f"Repair successful on attempt {attempt}!")
                            success = True
                            self._log_attempt(filepath, attempt, True, error_types_encountered)
                            break
                        
                        # Rollback-if-worse logic
                        if new_error_count > current_error_count:
                            logger.warning(
                                f"Attempt {attempt} made errors worse! "
                                f"New count: {new_error_count} (vs {current_error_count}). "
                                "Rolling back to previous iteration's version."
                            )
                            # Restore from this attempt's starting backup
                            shutil.copyfile(backup_path, filepath)
                        else:
                            # It's better or equal, accept the new state
                            logger.info(
                                f"Attempt {attempt} accepted. "
                                f"Error count: {new_error_count} (vs {current_error_count} before)."
                            )
                            current_error_count = new_error_count
                            output = new_output
                            
                except Exception as e:
                    logger.error(f"Error during repair iteration {attempt}: {e}")
                    
            if not success:
                logger.error(f"Failed to repair {filename} after {max_retries} attempts.")
                # Log failed attempt
                self._log_attempt(filepath, max_retries, False, error_types_encountered)
                # Overwrite/restore the very first backup to avoid breaking things worse
                first_backup = f"output/{self.run_id}/backups/iter_1/{filename}"
                if os.path.exists(first_backup):
                    shutil.copyfile(first_backup, filepath)
                
        except Exception as e:
            logger.error(f"Exception in repair loop: {e}")

        return success

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
