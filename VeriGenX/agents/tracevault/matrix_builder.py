import json
import os
import re
from typing import Dict, List, Any, Optional
from VeriGenX.agents.tracevault.db_manager import TraceabilityDBManager

class MatrixBuilder:
    """
    Builds the traceability matrix by aggregating specifications, test plan definitions,
    UVM codebase, SimRunner outcomes, and CoverHunter coverage reports into the Traceability Database.
    """
    def __init__(self, db_path: str = "output/traceability.db"):
        self.db = TraceabilityDBManager(db_path)

    def build_matrix(self, design_name: str) -> Dict[str, Any]:
        """
        Runs the full traceability assembly pipeline for a design:
        1. Loads the test plan and extracts spec sections.
        2. Inserts spec sections and functional points.
        3. Identifies and inserts test cases.
        4. Identifies and inserts coverage bins.
        5. Imports simulation results.
        6. Interlinks requirements, tests, and coverage bins.
        """
        print(f"  [MatrixBuilder] Starting traceability mapping for '{design_name}'...")
        
        # 1. Load Test Plan
        test_plan = self._load_test_plan(design_name)
        
        # 2. Extract Spec Sections
        sections = self._extract_spec_sections(design_name, test_plan)
        section_ids = {}
        for sec in sections:
            sec_id = self.db.insert_spec_section(design_name, sec, f"Content for section: {sec}")
            section_ids[sec] = sec_id
            
        # 3. Insert Functional Points
        fp_ids = {}
        fp_list = test_plan.get("functional_points", [])
        for fp in fp_list:
            fp_id = fp.get("id")
            desc = fp.get("description", "")
            mapped_sec = self._map_fp_to_section(fp_id, desc, sections)
            sec_db_id = section_ids[mapped_sec]
            db_fp_id = self.db.insert_functional_point(design_name, fp_id, desc, sec_db_id)
            fp_ids[fp_id] = db_fp_id

        # 4. Parse Simulation Reports and Populated Test Cases & Coverage Bins
        sim_report = self._load_sim_report(design_name)
        coverhunter_report = self._load_coverhunter_report(design_name)
        
        test_ids = {}
        bin_ids = {}

        # First, insert FPs as coverage bins
        for fp in fp_list:
            fp_id = fp.get("id")
            bin_db_id = self.db.insert_coverage_bin(design_name, fp_id, target=100.0, achieved=0.0)
            bin_ids[fp_id] = bin_db_id

        # Insert FSM states as coverage bins
        fsm_states = test_plan.get("fsm_states", [])
        for state in fsm_states:
            bin_db_id = self.db.insert_coverage_bin(design_name, state, target=100.0, achieved=0.0)
            bin_ids[state] = bin_db_id

        # Identify tests in generated_uvm/
        test_files = self._scan_generated_test_files(design_name)
        
        # Link tests, bins, and simulation results
        tests_data = sim_report.get("tests", {})
        
        for t_file_name, file_path in test_files.items():
            t_name = t_file_name.replace(".sv", "")
            db_test_id = self.db.insert_test_case(design_name, t_name, file_path)
            test_ids[t_name] = db_test_id
            
            # Get sim results if run
            t_sim = tests_data.get(t_name, {})
            if t_sim:
                status = t_sim.get("status", "unknown")
                stdout = t_sim.get("stdout", "")
                self.db.insert_simulation_result(design_name, t_name, status, stdout)
                
                # Fetch achieved FP coverage from sim report
                cov_detail = t_sim.get("coverage", {}).get("functional_points_detail", {})
                for fp_code, fp_cov in cov_detail.items():
                    achieved = fp_cov.get("coverage_percentage", 0.0)
                    # Link test case to FP
                    if fp_code in fp_ids:
                        self.db.link_fp_to_test(fp_ids[fp_code], db_test_id)
                        # Link test case to coverage bin
                        if fp_code in bin_ids:
                            self.db.link_test_to_bin(db_test_id, bin_ids[fp_code])
                            # Update achieved coverage in database (use max)
                            self._update_coverage_bin_achieved(design_name, fp_code, achieved)
                
                # Link CoverHunter directed test to its targeted FSM/gap bin
                for state in fsm_states:
                    if fsm_state_targeted_by_test(t_name, state):
                        if state in bin_ids:
                            self.db.link_test_to_bin(db_test_id, bin_ids[state])
                            # If test passed, FSM state is hit
                            if status == "passed":
                                self._update_coverage_bin_achieved(design_name, state, 100.0)
                                
                            # Also link to appropriate Spec section FPs (if FSM states belong to FSM States section)
                            for fp in fp_list:
                                if "fsm" in fp.get("description", "").lower() or "state" in fp.get("description", "").lower():
                                    fp_code = fp.get("id")
                                    if fp_code in fp_ids:
                                        self.db.link_fp_to_test(fp_ids[fp_code], db_test_id)
            else:
                # Test not simulated yet
                self.db.insert_simulation_result(design_name, t_name, "pending", "No simulation result on disk.")
                
            # Default links for base and baseline directed test if simulation details were missing
            if t_name == f"{design_name}_test_base" or t_name == f"{design_name}_test_directed":
                for fp in fp_list:
                    fp_code = fp.get("id")
                    if fp_code in fp_ids:
                        self.db.link_fp_to_test(fp_ids[fp_code], db_test_id)
                    if fp_code in bin_ids:
                        self.db.link_test_to_bin(db_test_id, bin_ids[fp_code])

        # Walk through CoverHunter iterations to populate bins and links
        iterations = coverhunter_report.get("iterations", []) or []
        for it in iterations:
            gap = it.get("targeted_gap")
            if gap:
                gap_name = gap.get("name")
                gap_type = gap.get("type", "")
                
                # Generate corresponding directed test name
                t_name = f"{design_name}_test_directed_{gap_name}"
                
                # Insert bin if new
                if gap_name not in bin_ids:
                    bin_db_id = self.db.insert_coverage_bin(design_name, gap_name, target=100.0, achieved=0.0)
                    bin_ids[gap_name] = bin_db_id
                    
                # Link test to targeted gap bin if both exist
                if t_name in test_ids and gap_name in bin_ids:
                    self.db.link_test_to_bin(test_ids[t_name], bin_ids[gap_name])
                    
                    # Update gap completion from final coverage results
                    t_sim = tests_data.get(t_name, {})
                    if t_sim and t_sim.get("status") == "passed":
                        self._update_coverage_bin_achieved(design_name, gap_name, 100.0)

        print(f"  [MatrixBuilder] Traceability mapping built for '{design_name}'.")
        return self.db.get_all_traceability_data(design_name)

    # ------------------------------------------------------------------ #
    #  Internal Helpers                                                  #
    # ------------------------------------------------------------------ #

    def _load_test_plan(self, design_name: str) -> Dict[str, Any]:
        path = f"test_plans/{design_name}_test_plan.json"
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"  [Warning] Failed to read test plan: {e}")
        return {}

    def _load_sim_report(self, design_name: str) -> Dict[str, Any]:
        # Try design-specific validation report first
        path_spec = f"output/sim_validation_report_{design_name}.json"
        if os.path.exists(path_spec):
            try:
                with open(path_spec, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data.get("design_name") == design_name:
                        return data
            except Exception as e:
                print(f"  [Warning] Failed to read design-specific sim report: {e}")

        path = "output/sim_validation_report.json"
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data.get("design_name") == design_name:
                        return data
            except Exception as e:
                print(f"  [Warning] Failed to read sim report: {e}")
        return {}

    def _load_coverhunter_report(self, design_name: str) -> Dict[str, Any]:
        path = f"output/coverhunter_report_{design_name}.json"
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"  [Warning] Failed to read coverhunter report: {e}")
        return {}

    def _extract_spec_sections(self, design_name: str, test_plan: Dict[str, Any]) -> List[str]:
        source_file = test_plan.get("source_file", f"{design_name}_spec.txt")
        spec_path = os.path.join("input_designs", source_file)
        sections = []
        if os.path.exists(spec_path):
            try:
                with open(spec_path, "r", encoding="utf-8") as f:
                    content = f.read()
                lines = content.split("\n")
                for line in lines:
                    line = line.strip()
                    m = re.match(r"^(\d+\.\s*[A-Za-z0-9_\-\s:]+)", line)
                    if m:
                        sections.append(m.group(1).strip())
                    elif line.startswith("#"):
                        header = line.lstrip("#").strip()
                        if re.match(r"^\d+\.", header):
                            sections.append(header)
            except Exception as e:
                print(f"  [Warning] Spec parsing error: {e}")
                
        if not sections:
            # Fallback sections based on standard spec structure
            sections = ["1. Signals", "2. Protocol", "3. FSM States", "4. Registers"]
            
        # Ensure we always add timing section if constraints exist
        if test_plan.get("timing_constraints") and "5. Timing Constraints" not in sections:
            sections.append("5. Timing Constraints")
            
        return sections

    def _map_fp_to_section(self, fp_id: str, description: str, sections: List[str]) -> str:
        desc = (fp_id + " " + description).lower()
        if any(w in desc for w in ["signal", "clk", "rst", "reset", "clock"]):
            for s in sections:
                if "signal" in s.lower() or "reset" in s.lower():
                    return s
        if any(w in desc for w in ["fsm", "state", "idle", "start", "stop", "data"]):
            for s in sections:
                if "state" in s.lower() or "fsm" in s.lower():
                    return s
        if any(w in desc for w in ["register", "addr", "control", "divisor"]):
            for s in sections:
                if "register" in s.lower():
                    return s
        if any(w in desc for w in ["protocol", "baud", "transfer", "parity"]):
            for s in sections:
                if "protocol" in s.lower() or "baud" in s.lower() or "timing" in s.lower():
                    return s
        return sections[0]

    def _scan_generated_test_files(self, design_name: str) -> Dict[str, str]:
        gen_dir = "generated_uvm"
        test_files = {}
        if os.path.exists(gen_dir):
            for file in os.listdir(gen_dir):
                if file.startswith(f"{design_name}_test_") and file.endswith(".sv"):
                    test_files[file] = os.path.join(gen_dir, file)
        return test_files

    def _update_coverage_bin_achieved(self, design_name: str, bin_name: str, achieved: float):
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT achieved_coverage FROM coverage_bins
                WHERE design_name = ? AND bin_name = ?
            """, (design_name, bin_name))
            row = cursor.fetchone()
            existing = row[0] if row else 0.0
            
            new_achieved = max(existing, achieved)
            cursor.execute("""
                INSERT OR REPLACE INTO coverage_bins (design_name, bin_name, target_coverage, achieved_coverage)
                VALUES (?, ?, 100.0, ?)
            """, (design_name, bin_name, new_achieved))
            conn.commit()
        finally:
            conn.close()

def fsm_state_targeted_by_test(test_name: str, state_name: str) -> bool:
    """Helper to detect if a test targets a specific state by naming convention."""
    return test_name.endswith(f"_{state_name}")
