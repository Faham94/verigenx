# VeriGenX — Autonomous UVM Verification Intelligence Platform

## Project Overview

VeriGenX is an open-source, AI-powered UVM verification platform that automates the entire verification flow:

- **Phase 1 (SpecMind):** Parses RTL specifications (TXT, PDF, DOCX), semantic chunking, ChromaDB embeddings, LLM-based extraction, and generates JSON test plans
- **Phase 2 (ArchWeaver):** Builds dependency graphs for UVM components with conflict detection and DAG visualization
- **Phase 3 (UVMForge):** Generates complete UVM testbenches (coming soon)

## Features Implemented

### Phase 1 — SpecMind
- [x] TXT/PDF/DOCX document parsing
- [x] Semantic chunking with configurable overlap
- [x] ChromaDB persistent embedding storage
- [x] LLM-based extraction (signals, FSM, registers, timing)
- [x] Test plan generation in JSON format
- [x] Centralized prompt library
- [x] Response validation and parsing
- [x] State management and pipeline orchestration
- [x] UART specification processed successfully

### Phase 2 — ArchWeaver
- [x] Dependency graph building (DAG)
- [x] Topological sorting (Kahn's algorithm)
- [x] Cycle detection
- [x] Conflict detection (duplicate signals, naming conflicts, missing dependencies)
- [x] DAG visualization (DOT export)

## Test Results

| Phase | Test | Result |
|-------|------|--------|
| Phase 1 | TXT parsing | Pass |
| Phase 1 | Test plan generation | Pass |
| Phase 1 | Semantic chunking | Pass |
| Phase 2 | DAG build (12 components) | Pass |
| Phase 2 | Topological sort | Pass |
| Phase 2 | Conflict detection | Pass |
| Phase 2 | DOT export | Pass |

## Quick Start

```bash
# Activate virtual environment
venv\Scripts\activate

# Run Phase 1 test
python test_phase1.py

# Run Phase 2 test
python test_phase2.py

# Run full pipeline
python -m VeriGenX.orchestrator --spec input_designs/uart_spec.txt
```
