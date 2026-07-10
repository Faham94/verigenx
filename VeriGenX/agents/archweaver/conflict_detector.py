"""
ArchWeaver: Conflict Detector
Detects interface signal mismatches and naming conflicts
"""
from collections import Counter

class ConflictDetector:
    def detect_conflicts(self, dag, test_plan):
        """
        Detect conflicts in the dependency graph
        Returns: List of conflict reports
        """
        conflicts = []
        
        # 1. Check for duplicate signal names
        signals = test_plan.get("signals", [])
        signal_names = [s.get("name") for s in signals if s.get("name")]
        
        duplicates = [name for name, count in Counter(signal_names).items() if count > 1]
        if duplicates:
            conflicts.append({
                "type": "duplicate_signal",
                "severity": "error",
                "description": f"Duplicate signal names found: {duplicates}",
                "suggestion": "Rename signals to avoid conflicts"
            })
        
        # 2. Check component naming conflicts
        components = dag.get("components", [])
        comp_duplicates = [name for name, count in Counter(components).items() if count > 1]
        if comp_duplicates:
            conflicts.append({
                "type": "duplicate_component",
                "severity": "error",
                "description": f"Duplicate component names found: {comp_duplicates}",
                "suggestion": "Rename components to avoid conflicts"
            })
        
        # 3. Check for missing dependencies
        dependencies = dag.get("dependencies", {})
        for comp, deps in dependencies.items():
            for dep in deps:
                if dep not in components:
                    conflicts.append({
                        "type": "missing_dependency",
                        "severity": "error",
                        "description": f"Component '{comp}' depends on '{dep}' which is not in the component list",
                        "suggestion": f"Add '{dep}' to components or remove dependency"
                    })
        
        return conflicts
    
    def report_conflicts(self, conflicts):
        """Print a formatted conflict report"""
        if not conflicts:
            print("No conflicts detected.")
            return
        
        print("\nConflict Report:")
        print("-" * 60)
        for i, conflict in enumerate(conflicts, 1):
            print(f"{i}. [{conflict['severity'].upper()}] {conflict['type']}")
            print(f"   Description: {conflict['description']}")
            print(f"   Suggestion: {conflict['suggestion']}")
            print("-" * 60)
