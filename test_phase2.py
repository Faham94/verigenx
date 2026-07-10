"""
Phase 2 Test: ArchWeaver
Tests dependency graph, topological sort, conflict detection, and DOT export
"""
import os
import sys
sys.path.insert(0, os.getcwd())

from VeriGenX.agents.archweaver.dag_builder import DAGBuilder
from VeriGenX.agents.archweaver.resolver import Resolver
from VeriGenX.agents.archweaver.conflict_detector import ConflictDetector

def test_phase2():
    print("\n" + "="*60)
    print("PHASE 2 TEST - ArchWeaver (Dependency Engine)")
    print("="*60)
    
    print("\n[1] Building dependency graph...")
    builder = DAGBuilder()
    dag = builder.build_from_test_plan()
    print(f"Found {len(dag['components'])} UVM components")
    print(f"Design: {dag['design_name']}")
    
    print("\n[2] Resolving dependencies (topological sort)...")
    resolver = Resolver()
    sorted_order = resolver.resolve(dag)
    print(f"Successfully resolved {len(sorted_order)} components")
    
    print("\n[3] Generation order:")
    generation_order = resolver.get_generation_order(dag)
    for item in generation_order:
        print(f"   {item['order']}. {item['component']} -> {item['filename']}")
    
    print("\n[4] Checking for conflicts...")
    conflict_detector = ConflictDetector()
    conflicts = conflict_detector.detect_conflicts(dag, {"signals": []})
    conflict_detector.report_conflicts(conflicts)
    
    print("\n[5] Exporting DAG to DOT format...")
    resolver.export_dot(dag, "dag.dot")
    
    print("\n" + "="*60)
    print("PHASE 2 TEST COMPLETE!")
    print("="*60)

if __name__ == "__main__":
    test_phase2()
