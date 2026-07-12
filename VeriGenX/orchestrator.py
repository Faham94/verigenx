"""
VeriGenX Orchestrator
Main pipeline controller for all agents.

Fixes applied (Phase 2):
  - Bug #1: ArchWeaver now receives in-memory test plan dict directly,
            not a hardcoded disk path fallback
  - Bug #3: ConflictDetector now receives actual signals from the test plan
  - Bug #5: LLMConflictResolver is now integrated after ConflictDetector —
            every detected conflict is passed through the LLM for resolution
"""
import argparse
import time
import os
from typing import Optional

from VeriGenX.state_bus import get_state_bus
from VeriGenX.agents.specmind.ingestion import DocumentIngestor
from VeriGenX.agents.specmind.chunker import Chunker
from VeriGenX.agents.specmind.embedder import Embedder
from VeriGenX.agents.specmind.test_plan import TestPlanGenerator
from VeriGenX.agents.archweaver.dag_builder import DAGBuilder
from VeriGenX.agents.archweaver.resolver import Resolver
from VeriGenX.agents.archweaver.conflict_detector import ConflictDetector
from VeriGenX.agents.archweaver.llm_conflict_resolver import LLMConflictResolver
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
            print("\n[Phase 1] SpecMind — Specification Intelligence")
            self._run_specmind(spec_path)

            print("\n[Phase 2] ArchWeaver — Dependency Graph Engine")
            self._run_archweaver()

            print("\n[Phase 3] UVMForge — UVM Code Generator")
            self._run_uvmforge()

            elapsed = time.time() - self.start_time
            print("\n" + "=" * 60)
            print(f"PIPELINE COMPLETE in {elapsed:.2f}s")
            print("=" * 60)

        except Exception as e:
            print(f"\nPipeline Error: {e}")
            self.state.update_state(errors=[str(e)])
            raise

    # ------------------------------------------------------------------ #
    #  Phase 1 — SpecMind                                                  #
    # ------------------------------------------------------------------ #

    def _run_specmind(self, spec_path: str) -> None:
        print(f"  Ingesting: {spec_path}")
        ingestor = DocumentIngestor()
        result   = ingestor.ingest(spec_path)
        text     = result["text"]
        meta     = result.get("metadata", {})
        print(f"  Extracted {len(text)} chars [{result['file_type']}]")

        print("  Chunking document...")
        chunker = Chunker()
        chunks  = chunker.chunk_document(text, meta)
        print(f"  Created {len(chunks)} chunks")

        print("  Embedding chunks into ChromaDB...")
        embedder = Embedder()
        if embedder.is_ready():
            embedder.add(chunks)
            print(f"  Embedded {embedder.count()} chunks in ChromaDB")
        else:
            print("  [Warning] ChromaDB not available — skipping embedding")

        print("  Generating test plan (LLM + heuristic extraction)...")
        generator = TestPlanGenerator()
        test_plan = generator.generate(text)
        test_plan["source_file"]     = os.path.basename(spec_path)
        test_plan["embedded_chunks"] = embedder.count()

        design   = test_plan.get("design_name", "design")
        filename = f"{design}_test_plan.json"
        generator.save(test_plan, filename=filename)

        # Store in-memory state — Phase 2 reads this directly (Bug #1 fix)
        self.state.update_state(test_plan=test_plan)
        method = test_plan.get("extraction_method", "unknown")
        print(f"  Test plan generated [{method} extraction, design={design}]")

    # ------------------------------------------------------------------ #
    #  Phase 2 — ArchWeaver                                                #
    # ------------------------------------------------------------------ #

    def _run_archweaver(self) -> None:
        # Bug #1 fix: consume in-memory test plan — no hardcoded file path
        state_plan = self.state.get_state().test_plan

        print("  Building dependency graph from in-memory test plan...")
        builder = DAGBuilder()

        if state_plan:
            # Primary path: use in-memory dict directly (Bug #1 fix)
            dag = builder.build_from_test_plan(test_plan_dict=state_plan)
        else:
            # Fallback: try saved file (should not normally happen)
            print("  [Warning] No in-memory test plan — falling back to disk")
            default_path = os.path.join(TEST_PLANS_DIR, "uart_test_plan.json")
            dag = builder.build_from_test_plan(test_plan_path=default_path)
            state_plan = builder.get_test_plan()

        self.state.update_state(dependency_graph=dag)
        print(f"  Design: {dag['design_name']} | Components: {len(dag['components'])}")

        print("  Resolving dependencies (topological sort)...")
        resolver = Resolver()
        order    = resolver.get_generation_order(dag)
        print(f"  Generation order established: {len(order)} components")

        # Bug #3 fix: pass actual signals from state plan, not empty dict
        print("  Checking for conflicts (FR-02.5 interface consistency)...")
        detector  = ConflictDetector()
        conflicts = detector.detect_conflicts(dag, state_plan)   # real signals!

        if not conflicts:
            print("  No conflicts detected")
        else:
            print(f"  Found {len(conflicts)} conflict(s)")
            detector.report_conflicts(conflicts)

            # Bug #5 fix: integrate LLM resolver for all detected conflicts
            print("  Resolving conflicts with LLM assistance...")
            llm_resolver = LLMConflictResolver()
            spec_context = state_plan.get("source_file", "") + " specification"
            resolved     = llm_resolver.resolve(conflicts, spec_context)
            llm_resolver.report_with_resolutions(resolved)

        print("  Exporting DAG to DOT format...")
        dot_file = resolver.export_dot(dag, "dag.dot")

        print(f"  ArchWeaver complete — DAG saved to {dot_file}")

    # ------------------------------------------------------------------ #
    #  Phase 3 — UVMForge                                                  #
    # ------------------------------------------------------------------ #

    def _run_uvmforge(self) -> None:
        state_plan = self.state.get_state().test_plan
        state_dag  = self.state.get_state().dependency_graph

        if not state_plan or not state_dag:
            print("  [Warning] Missing test plan or dependency graph in state. Cannot run UVMForge.")
            return

        print("  Generating UVM testbench components topologically...")
        from VeriGenX.agents.uvmforge.generator import UVMForgeGenerator
        generator = UVMForgeGenerator()
        generated_files = generator.generate_all(state_plan, state_dag)
        print(f"  UVMForge complete — Generated {len(generated_files)} SystemVerilog files")

    # ------------------------------------------------------------------ #
    #  ArchWeaver-only entry (for testing / standalone use)               #
    # ------------------------------------------------------------------ #

    def run_archweaver_from_plan(self, test_plan: dict) -> dict:
        """
        Run ArchWeaver directly from a provided test plan dict.
        Used by integration tests and the Streamlit 'Run Pipeline' page.
        """
        self.state.update_state(test_plan=test_plan)
        self._run_archweaver()
        return self.state.get_state().dependency_graph


# ------------------------------------------------------------------ #
#  CLI entry point                                                     #
# ------------------------------------------------------------------ #

def main() -> None:
    parser = argparse.ArgumentParser(description="VeriGenX Verification Pipeline")
    parser.add_argument("--spec",   required=True,    help="Spec file (.txt/.pdf/.docx/.xml/.rdl)")
    parser.add_argument("--output", default="output", help="Output directory")
    args = parser.parse_args()
    Orchestrator().run_pipeline(args.spec, args.output)


if __name__ == "__main__":
    main()
