"""
VeriGenX Orchestrator
Main pipeline controller for all agents
"""
import argparse
import time
from typing import Optional
from VeriGenX.state_bus import get_state_bus
from VeriGenX.agents.specmind.ingestion import DocumentIngestor
from VeriGenX.agents.specmind.chunker import Chunker
from VeriGenX.agents.specmind.test_plan import TestPlanGenerator
from VeriGenX.agents.archweaver.dag_builder import DAGBuilder
from VeriGenX.agents.archweaver.resolver import Resolver
from VeriGenX.agents.archweaver.conflict_detector import ConflictDetector

class Orchestrator:
    def __init__(self):
        self.state = get_state_bus()
        self.start_time = None
    
    def run_pipeline(self, spec_path: str, output_dir: str = "output"):
        self.start_time = time.time()
        print("\n" + "="*60)
        print("VERIGENX PIPELINE STARTED")
        print("="*60)
        
        try:
            # Phase 1: SpecMind
            print("\n[Phase 1] SpecMind - Specification Intelligence")
            self._run_specmind(spec_path)
            
            # Phase 2: ArchWeaver
            print("\n[Phase 2] ArchWeaver - Dependency Graph Engine")
            self._run_archweaver()
            
            elapsed = time.time() - self.start_time
            print("\n" + "="*60)
            print(f"PIPELINE COMPLETE in {elapsed:.2f}s")
            print("="*60)
            
        except Exception as e:
            print(f"\nPipeline Error: {e}")
            self.state.update_state(errors=[str(e)])
    
    def _run_specmind(self, spec_path: str):
        print(f"  Ingesting: {spec_path}")
        ingestor = DocumentIngestor()
        result = ingestor.ingest(spec_path)
        print(f"  Extracted {len(result['text'])} chars")
        
        print("  Chunking document...")
        chunker = Chunker()
        chunks = chunker.chunk_document(result['text'], result.get('metadata', {}))
        print(f"  Created {len(chunks)} chunks")
        
        print("  Generating test plan...")
        generator = TestPlanGenerator()
        test_plan = generator.generate(result['text'])
        self.state.update_state(test_plan=test_plan)
        print("  Test plan generated successfully")
    
    def _run_archweaver(self):
        print("  Building dependency graph...")
        builder = DAGBuilder()
        dag = builder.build_from_test_plan()
        self.state.update_state(dependency_graph=dag)
        print(f"  Found {len(dag['components'])} UVM components")
        
        print("  Resolving dependencies...")
        resolver = Resolver()
        order = resolver.get_generation_order(dag)
        print(f"  Generation order established ({len(order)} components)")
        
        print("  Checking for conflicts...")
        conflict_detector = ConflictDetector()
        conflicts = conflict_detector.detect_conflicts(dag, {"signals": []})
        if not conflicts:
            print("  No conflicts detected")
        else:
            print(f"  Found {len(conflicts)} conflicts")
            conflict_detector.report_conflicts(conflicts)

def main():
    parser = argparse.ArgumentParser(description="VeriGenX Pipeline")
    parser.add_argument("--spec", required=True, help="Path to specification file")
    parser.add_argument("--output", default="output", help="Output directory")
    args = parser.parse_args()
    
    orchestrator = Orchestrator()
    orchestrator.run_pipeline(args.spec, args.output)

if __name__ == "__main__":
    main()
