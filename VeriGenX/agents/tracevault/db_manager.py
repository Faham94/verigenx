import sqlite3
import os
from typing import Dict, List, Any, Optional

class TraceabilityDBManager:
    """
    Manages the SQLite database for spec-to-coverage traceability mapping (TraceVault).
    Supports transactional CRUD operations and bidirectional queries.
    """
    def __init__(self, db_path: str = "output/traceability.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Creates the relational database schema if it does not already exist."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            # 1. Spec Sections
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS spec_sections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    design_name TEXT,
                    section_name TEXT,
                    content TEXT,
                    UNIQUE(design_name, section_name)
                )
            """)

            # 2. Functional Points (FK to Spec Sections)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS functional_points (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    design_name TEXT,
                    fp_id TEXT,
                    description TEXT,
                    section_id INTEGER,
                    FOREIGN KEY(section_id) REFERENCES spec_sections(id) ON DELETE CASCADE,
                    UNIQUE(design_name, fp_id)
                )
            """)

            # 3. Test Cases
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS test_cases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    design_name TEXT,
                    test_name TEXT,
                    file_path TEXT,
                    UNIQUE(design_name, test_name)
                )
            """)

            # 4. Coverage Bins
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS coverage_bins (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    design_name TEXT,
                    bin_name TEXT,
                    target_coverage REAL DEFAULT 100.0,
                    achieved_coverage REAL DEFAULT 0.0,
                    UNIQUE(design_name, bin_name)
                )
            """)

            # 5. Simulation Results
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS simulation_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    design_name TEXT,
                    test_name TEXT,
                    status TEXT,
                    log_summary TEXT,
                    UNIQUE(design_name, test_name)
                )
            """)

            # 6. Junction Table: Functional Points <-> Test Cases
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS fp_test_links (
                    fp_id INTEGER,
                    test_id INTEGER,
                    PRIMARY KEY (fp_id, test_id),
                    FOREIGN KEY(fp_id) REFERENCES functional_points(id) ON DELETE CASCADE,
                    FOREIGN KEY(test_id) REFERENCES test_cases(id) ON DELETE CASCADE
                )
            """)

            # 7. Junction Table: Test Cases <-> Coverage Bins
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS test_bin_links (
                    test_id INTEGER,
                    bin_id INTEGER,
                    PRIMARY KEY (test_id, bin_id),
                    FOREIGN KEY(test_id) REFERENCES test_cases(id) ON DELETE CASCADE,
                    FOREIGN KEY(bin_id) REFERENCES coverage_bins(id) ON DELETE CASCADE
                )
            """)
            conn.commit()
        finally:
            conn.close()

    # ------------------------------------------------------------------ #
    #  CRUD Operations                                                   #
    # ------------------------------------------------------------------ #

    def insert_spec_section(self, design_name: str, section_name: str, content: str = "") -> int:
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO spec_sections (design_name, section_name, content)
                VALUES (?, ?, ?)
            """, (design_name, section_name, content))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def insert_functional_point(self, design_name: str, fp_id: str, description: str, section_id: int) -> int:
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO functional_points (design_name, fp_id, description, section_id)
                VALUES (?, ?, ?, ?)
            """, (design_name, fp_id, description, section_id))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def insert_test_case(self, design_name: str, test_name: str, file_path: str = "") -> int:
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO test_cases (design_name, test_name, file_path)
                VALUES (?, ?, ?)
            """, (design_name, test_name, file_path))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def insert_coverage_bin(self, design_name: str, bin_name: str, target: float = 100.0, achieved: float = 0.0) -> int:
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO coverage_bins (design_name, bin_name, target_coverage, achieved_coverage)
                VALUES (?, ?, ?, ?)
            """, (design_name, bin_name, target, achieved))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def insert_simulation_result(self, design_name: str, test_name: str, status: str, log_summary: str = "") -> int:
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO simulation_results (design_name, test_name, status, log_summary)
                VALUES (?, ?, ?, ?)
            """, (design_name, test_name, status, log_summary))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def link_fp_to_test(self, fp_id: int, test_id: int):
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO fp_test_links (fp_id, test_id)
                VALUES (?, ?)
            """, (fp_id, test_id))
            conn.commit()
        finally:
            conn.close()

    def link_test_to_bin(self, test_id: int, bin_id: int):
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO test_bin_links (test_id, bin_id)
                VALUES (?, ?)
            """, (test_id, bin_id))
            conn.commit()
        finally:
            conn.close()

    # ------------------------------------------------------------------ #
    #  Query Helpers                                                     #
    # ------------------------------------------------------------------ #

    def get_tests_by_section(self, design_name: str, section_name: str) -> List[Dict[str, Any]]:
        """Given a spec section -> return all test cases that trace to it."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT tc.test_name, tc.file_path, sr.status
                FROM test_cases tc
                JOIN fp_test_links ftl ON tc.id = ftl.test_id
                JOIN functional_points fp ON ftl.fp_id = fp.id
                JOIN spec_sections ss ON fp.section_id = ss.id
                LEFT JOIN simulation_results sr ON tc.test_name = sr.test_name AND tc.design_name = sr.design_name
                WHERE ss.design_name = ? AND ss.section_name = ?
            """, (design_name, section_name))
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_requirements_by_test(self, design_name: str, test_name: str) -> List[Dict[str, Any]]:
        """Given a test case -> return all spec requirements/functional points it satisfies."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT ss.section_name, fp.fp_id, fp.description
                FROM spec_sections ss
                JOIN functional_points fp ON ss.id = fp.section_id
                JOIN fp_test_links ftl ON fp.id = ftl.fp_id
                JOIN test_cases tc ON ftl.test_id = tc.id
                WHERE tc.design_name = ? AND tc.test_name = ?
            """, (design_name, test_name))
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_all_traceability_data(self, design_name: str) -> Dict[str, Any]:
        """Fetches all structured elements to construct matrix summaries."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            # Fetch sections
            cursor.execute("SELECT * FROM spec_sections WHERE design_name = ?", (design_name,))
            sections = [dict(row) for row in cursor.fetchall()]
            
            # Fetch FPs
            cursor.execute("SELECT * FROM functional_points WHERE design_name = ?", (design_name,))
            fps = [dict(row) for row in cursor.fetchall()]
            
            # Fetch tests
            cursor.execute("SELECT * FROM test_cases WHERE design_name = ?", (design_name,))
            tests = [dict(row) for row in cursor.fetchall()]
            
            # Fetch bins
            cursor.execute("SELECT * FROM coverage_bins WHERE design_name = ?", (design_name,))
            bins = [dict(row) for row in cursor.fetchall()]
            
            # Fetch results
            cursor.execute("SELECT * FROM simulation_results WHERE design_name = ?", (design_name,))
            results = {row["test_name"]: dict(row) for row in cursor.fetchall()}
            
            # Fetch links
            cursor.execute("""
                SELECT fp_id, test_id FROM fp_test_links
                WHERE fp_id IN (SELECT id FROM functional_points WHERE design_name = ?)
            """, (design_name,))
            fp_test_links = [dict(row) for row in cursor.fetchall()]
            
            cursor.execute("""
                SELECT test_id, bin_id FROM test_bin_links
                WHERE test_id IN (SELECT id FROM test_cases WHERE design_name = ?)
            """, (design_name,))
            test_bin_links = [dict(row) for row in cursor.fetchall()]

            return {
                "sections": sections,
                "functional_points": fps,
                "test_cases": tests,
                "coverage_bins": bins,
                "simulation_results": results,
                "fp_test_links": fp_test_links,
                "test_bin_links": test_bin_links
            }
        finally:
            conn.close()
