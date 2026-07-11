"""
VeriGenX Orchestrator
Main pipeline controller for all agents.

Fixes applied:
  - Bug #3: Embedder was never called — now called after chunking
  - Bug #2: Extractor now called via TestPlanGenerator which invokes it internally
"""
import argparse
import time
import os
import json
from typing import Optional

from VeriGenX.state_bus import get_state_bus
from VeriGenX.agents.specmind.ingestion import DocumentIngestor
from VeriGenX.agents.specmind.chunker import Chunker
from VeriGenX.agents.specmind.embedder import Embedder
from VeriGenX.agents.specmind.test_plan import TestPlanGenerator
from VeriGenX.agents.archweaver.dag_builder import DAGBuilder
from VeriGenX.agents.archweaver.resolver import Resolver
from VeriGenX.agents.archweaver.conflict_detector import ConflictDetector
from VeriGenX.config import TEST_PLANS_DIR


class Orchestrator:

    def __init__(self):
        self.state      = get_state_bus()
        self.start_time = None

    def run_pipeline(self, spec_path: str, output_dir: str = "output") -> None:
        self.start_time = time.time()
        print("\n" + "=" * 60)
        print("VERIGENX PIPELINE STARTED")
        print("=" * 60)

        try:
            print("\n[Phase 1] SpecMind - Specification Intelligence")
            self._run_specmind(spec_path)

            print("\n[Phase 2] ArchWeaver - Dependency Graph Engine")
            self._run_archweaver()

            elapsed = time.time() - self.start_time
            print("\n" + "=" * 60)
            print(f"PIPELINE COMPLETE in {elapsed:.2f}s")
            print("=" * 60)

        except Exception as e:
            print(f"\nPipeline Error: {e}")
            self.state.update_state(errors=[str(e)])
            raise

    # ------------------------------------------------------------------ #
    #  Phase 1                                                             #
    # ------------------------------------------------------------------ #

    def _run_specmind(self, spec_path: str) -> None:
        # 1. Ingest (supports TXT/PDF/DOCX/XML/RDL + caching)
        print(f"  Ingesting: {spec_path}")
        ingestor = DocumentIngestor()
        result   = ingestor.ingest(spec_path)
        text     = result["text"]
        meta     = result.get("metadata", {})
        print(f"  Extracted {len(text)} chars [{result['file_type']}]")

        # 2. Chunk
        print("  Chunking document...")
        chunker = Chunker()
        chunks  = chunker.chunk_document(text, meta)
        print(f"  Created {len(chunks)} chunks")

        # 3. Embed — Bug #3 fix: Embedder now wired into the pipeline
        print("  Embedding chunks into ChromaDB...")
        embedder = Embedder()
        if embedder.is_ready():
            embedder.add(chunks)
            print(f"  Embedded {embedder.count()} chunks in ChromaDB")
        else:
            print("  [Warning] ChromaDB not available — skipping embedding")

        # 4. Generate test plan (calls Extractor internally — Bug #2 fix)
        print("  Generating test plan (LLM + heuristic extraction)...")
        generator = TestPlanGenerator()
        test_plan = generator.generate(text)
        test_plan["source_file"] = os.path.basename(spec_path)
        test_plan["embedded_chunks"] = embedder.count()

        # 5. Save test plan
        design   = test_plan.get("design_name", "design")
        filename = f"{design}_test_plan.json"
        generator.save(test_plan, filename=filename)

        self.state.update_state(test_plan=test_plan)
        method = test_plan.get("extraction_method", "unknown")
        print(f"  Test plan generated [{method} extraction]")

    # ------------------------------------------------------------------ #
    #  Phase 2                                                             #
    # ------------------------------------------------------------------ #

    def _run_archweaver(self) -> None:
        # Locate test plan
        plan    = self.state.get_state().test_plan
        design  = plan.get("design_name", "design") if plan else "uart"
        tp_path = os.path.join(TEST_PLANS_DIR, f"{design}_test_plan.json")
        if not os.path.exists(tp_path):
            tp_path = os.path.join(TEST_PLANS_DIR, "uart_test_plan.json")

        print("  Building dependency graph...")
        builder = DAGBuilder()
        dag     = builder.build_from_test_plan(tp_path)
        self.state.update_state(dependency_graph=dag)
        print(f"  Found {len(dag['components'])} UVM components")

        print("  Resolving dependencies (topological sort)...")
        resolver = Resolver()
        order    = resolver.get_generation_order(dag)
        print(f"  Generation order: {len(order)} components")

        print("  Checking for conflicts...")
        detector  = ConflictDetector()
        signals   = plan.get("signals", []) if plan else []
        conflicts = detector.detect_conflicts(dag, {"signals": signals})
        if not conflicts:
            print("  No conflicts detected")
        else:
            print(f"  Found {len(conflicts)} conflicts")
            detector.report_conflicts(conflicts)

        print("  Exporting DAG to DOT format...")
        resolver.export_dot(dag, "dag.dot")


# ------------------------------------------------------------------ #
#  CLI entry point                                                     #
# ------------------------------------------------------------------ #

def main() -> None:
    parser = argparse.ArgumentParser(description="VeriGenX Verification Pipeline")
    parser.add_argument("--spec",   required=True,         help="Path to spec file (.txt/.pdf/.docx/.xml/.rdl)")
    parser.add_argument("--output", default="output",      help="Output directory")
    parser.add_argument("--design", default=None,          help="Design name override")
    args = parser.parse_args()

    orchestrator = Orchestrator()
    orchestrator.run_pipeline(args.spec, args.output)


if __name__ == "__main__":
    main()
