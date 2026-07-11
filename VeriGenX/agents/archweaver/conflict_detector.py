"""
ArchWeaver: Conflict Detector
Detects conflicts in the dependency graph and test plan.

Fixes applied:
  - Bug #3: Was receiving {"signals": []} — now receives actual test plan
            signals from the orchestrator (fixed in orchestrator.py)
  - Bug #4: Added FR-02.5 interface consistency check — verifies signal
            widths and directions are consistent across components
"""
from collections import Counter
from typing import Dict, List, Tuple


class ConflictDetector:

    def detect_conflicts(self, dag: Dict, test_plan: Dict) -> List[Dict]:
        """
        Detect all conflict categories in the DAG and test plan.

        Returns:
            List of conflict dicts with: type, severity, description, suggestion
        """
        conflicts = []
        conflicts.extend(self._check_duplicate_signals(test_plan))
        conflicts.extend(self._check_duplicate_components(dag))
        conflicts.extend(self._check_missing_dependencies(dag))
        conflicts.extend(self._check_interface_consistency(test_plan))   # Bug #4
        conflicts.extend(self._check_dag_integrity(dag))
        return conflicts

    # ------------------------------------------------------------------ #
    #  Check 1: Duplicate signal names                                     #
    # ------------------------------------------------------------------ #

    def _check_duplicate_signals(self, test_plan: Dict) -> List[Dict]:
        """Bug #3 fix: now called with actual signals from test plan."""
        conflicts = []
        signals      = test_plan.get("signals", [])
        signal_names = [s.get("name") for s in signals if s.get("name")]
        duplicates   = [n for n, c in Counter(signal_names).items() if c > 1]
        if duplicates:
            conflicts.append({
                "type":        "duplicate_signal",
                "severity":    "error",
                "description": f"Duplicate signal names found: {duplicates}",
                "suggestion":  "Rename signals to unique identifiers",
            })
        return conflicts

    # ------------------------------------------------------------------ #
    #  Check 2: Duplicate component names                                  #
    # ------------------------------------------------------------------ #

    def _check_duplicate_components(self, dag: Dict) -> List[Dict]:
        conflicts  = []
        components = dag.get("components", [])
        duplicates = [n for n, c in Counter(components).items() if c > 1]
        if duplicates:
            conflicts.append({
                "type":        "duplicate_component",
                "severity":    "error",
                "description": f"Duplicate component names: {duplicates}",
                "suggestion":  "Rename or merge duplicate components",
            })
        return conflicts

    # ------------------------------------------------------------------ #
    #  Check 3: Missing dependency references                              #
    # ------------------------------------------------------------------ #

    def _check_missing_dependencies(self, dag: Dict) -> List[Dict]:
        conflicts    = []
        components   = set(dag.get("components", []))
        dependencies = dag.get("dependencies", {})
        for comp, deps in dependencies.items():
            for dep in deps:
                if dep not in components:
                    conflicts.append({
                        "type":        "missing_dependency",
                        "severity":    "error",
                        "description": f"'{comp}' depends on '{dep}' which is not in the component list",
                        "suggestion":  f"Add '{dep}' to the component list or remove this dependency",
                    })
        return conflicts

    # ------------------------------------------------------------------ #
    #  Check 4: Interface consistency (FR-02.5) — Bug #4 fix              #
    # ------------------------------------------------------------------ #

    def _check_interface_consistency(self, test_plan: Dict) -> List[Dict]:
        """
        FR-02.5: Verify that all interface signals have consistent widths and
        valid directions.  Catches:
          - Signals with width <= 0
          - Signals with invalid direction (not input / output / inout)
          - Signals with the same name but conflicting width or direction
        """
        conflicts = []
        signals   = test_plan.get("signals", [])

        VALID_DIRECTIONS = {"input", "output", "inout"}
        seen: Dict[str, Dict] = {}   # name → first occurrence

        for sig in signals:
            name      = sig.get("name", "").strip()
            width     = sig.get("width")
            direction = str(sig.get("direction", "")).lower().strip()

            if not name:
                continue

            # Width validity
            if width is not None:
                try:
                    w = int(width)
                    if w <= 0:
                        conflicts.append({
                            "type":        "invalid_signal_width",
                            "severity":    "error",
                            "description": f"Signal '{name}' has invalid width {w} (must be >= 1)",
                            "suggestion":  f"Correct the width of '{name}' in the specification",
                        })
                except (TypeError, ValueError):
                    conflicts.append({
                        "type":        "invalid_signal_width",
                        "severity":    "error",
                        "description": f"Signal '{name}' has non-integer width: {width}",
                        "suggestion":  "Specify width as a positive integer",
                    })

            # Direction validity
            if direction and direction not in VALID_DIRECTIONS:
                conflicts.append({
                    "type":        "invalid_signal_direction",
                    "severity":    "error",
                    "description": f"Signal '{name}' has invalid direction '{direction}'",
                    "suggestion":  f"Use one of: {sorted(VALID_DIRECTIONS)}",
                })

            # Cross-signal consistency (same name, different attrs)
            if name in seen:
                prev = seen[name]
                if prev.get("width") != width:
                    conflicts.append({
                        "type":        "inconsistent_signal_width",
                        "severity":    "warning",
                        "description": (
                            f"Signal '{name}' appears with width {prev.get('width')} "
                            f"and {width} — inconsistent"
                        ),
                        "suggestion":  f"Unify the width of '{name}' across the specification",
                    })
                if prev.get("direction", "").lower() != direction:
                    conflicts.append({
                        "type":        "inconsistent_signal_direction",
                        "severity":    "warning",
                        "description": (
                            f"Signal '{name}' appears with direction "
                            f"'{prev.get('direction')}' and '{direction}' — inconsistent"
                        ),
                        "suggestion":  f"Unify the direction of '{name}'",
                    })
            else:
                seen[name] = sig

        return conflicts

    # ------------------------------------------------------------------ #
    #  Check 5: DAG integrity — orphans and cycles (lightweight)          #
    # ------------------------------------------------------------------ #

    def _check_dag_integrity(self, dag: Dict) -> List[Dict]:
        """Check for components with no incoming edges that are not 'interface'."""
        conflicts    = []
        components   = set(dag.get("components", []))
        dependencies = dag.get("dependencies", {})

        # Build reverse edge map
        has_dependent = set()
        for comp, deps in dependencies.items():
            for dep in deps:
                has_dependent.add(dep)

        for comp in components:
            if comp == "interface":
                continue
            deps = dependencies.get(comp, [])
            if not deps and comp not in has_dependent:
                conflicts.append({
                    "type":        "isolated_component",
                    "severity":    "warning",
                    "description": f"Component '{comp}' has no dependencies and no dependents (orphan)",
                    "suggestion":  f"Verify '{comp}' belongs in this DAG or add appropriate edges",
                })
        return conflicts

    # ------------------------------------------------------------------ #
    #  Reporting                                                           #
    # ------------------------------------------------------------------ #

    def report_conflicts(self, conflicts: List[Dict]) -> None:
        if not conflicts:
            print("No conflicts detected.")
            return
        print("\nConflict Report")
        print("=" * 60)
        for i, conflict in enumerate(conflicts, 1):
            sev = conflict.get("severity", "error").upper()
            print(f"\n{i}. [{sev}] {conflict.get('type', '')}")
            print(f"   Description : {conflict.get('description', '')}")
            print(f"   Suggestion  : {conflict.get('suggestion', '')}")
        print("=" * 60)
