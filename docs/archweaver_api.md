# ArchWeaver Agent API Reference

## Overview

ArchWeaver is Phase 2 of the VeriGenX pipeline. It consumes the structured JSON test plan produced by SpecMind and builds a directed acyclic graph (DAG) of all UVM components. It then resolves the correct generation order, detects conflicts, supports multi-agent testbenches, and provides LLM-assisted conflict resolution.

**Module path:** `VeriGenX/agents/archweaver/`

---

## Classes

### `DAGBuilder`
**File:** `dag_builder.py`

Parses a test plan JSON and builds a dependency graph of all 12 standard UVM components.

```python
from VeriGenX.agents.archweaver.dag_builder import DAGBuilder

builder = DAGBuilder()
dag = builder.build_from_test_plan("test_plans/uart_test_plan.json")
# dag: {"components": [...], "dependencies": {...}, "design_name": "uart"}
```

**Methods:**

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `build_from_test_plan(test_plan_path)` | `str \| None` | `dict` | Builds DAG; defaults to `uart_test_plan.json` |
| `get_dag()` | — | `dict` | Returns current components and dependencies |

**DAG Output Schema:**
```json
{
  "components":   ["interface", "sequence_item", "driver", ...],
  "dependencies": {"driver": ["sequence_item", "interface"], ...},
  "design_name":  "uart"
}
```

**Standard 12 UVM Components:**

| Component | Depends On |
|-----------|-----------|
| interface | — |
| sequence_item | interface |
| sequence | sequence_item, interface |
| driver | sequence_item, interface |
| monitor | interface |
| agent | driver, monitor, sequence |
| scoreboard | sequence_item, interface |
| coverage | sequence_item, interface |
| env | agent, scoreboard, coverage |
| test_base | env, sequence |
| test_directed | test_base |
| top | test_base, interface, env |

---

### `Resolver`
**File:** `resolver.py`

Applies Kahn's topological sort algorithm to produce a valid generation order. Detects circular dependencies.

```python
from VeriGenX.agents.archweaver.resolver import Resolver

resolver = Resolver()
order     = resolver.resolve(dag)           # ["interface", "sequence_item", ...]
gen_order = resolver.get_generation_order(dag)  # [{component, filename, order}, ...]
dot_file  = resolver.export_dot(dag, "dag.dot")
```

**Methods:**

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `resolve(dag)` | `dict` | `List[str]` | Kahn's topological sort; raises on cycle |
| `get_generation_order(dag)` | `dict` | `List[dict]` | Sorted list with filenames and order index |
| `export_dot(dag, filename)` | `dict, str` | `str` | Writes Graphviz DOT file |

**Raises:** `Exception("Circular dependency detected in UVM components!")` if a cycle is found.

**Generation Order Output:**
```json
[
  {"component": "interface", "filename": "interface.sv", "order": 1},
  {"component": "driver",    "filename": "driver.sv",    "order": 5}
]
```

**DOT Visualization:**
```bash
dot -Tpng dag.dot -o dag.png
```

---

### `ConflictDetector`
**File:** `conflict_detector.py`

Detects three categories of conflicts in the DAG and test plan.

```python
from VeriGenX.agents.archweaver.conflict_detector import ConflictDetector

detector  = ConflictDetector()
conflicts = detector.detect_conflicts(dag, test_plan)
detector.report_conflicts(conflicts)
```

**Methods:**

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `detect_conflicts(dag, test_plan)` | `dict, dict` | `List[dict]` | Returns list of conflict dicts |
| `report_conflicts(conflicts)` | `List[dict]` | `None` | Prints formatted conflict report |

**Conflict Types:**

| Type | Severity | Detection Logic |
|------|---------|----------------|
| `duplicate_signal` | error | Signal name appears more than once in test plan |
| `duplicate_component` | error | Component name appears more than once in DAG |
| `missing_dependency` | error | A dependency references a component not in the component list |

**Conflict Dict Schema:**
```json
{
  "type":        "duplicate_signal",
  "severity":    "error",
  "description": "Duplicate signal names found: ['clk']",
  "suggestion":  "Rename signals to avoid conflicts"
}
```

---

### `MultiAgentDAGBuilder`
**File:** `multi_agent_builder.py`

Builds dependency graphs for testbenches with multiple UVM agent instances (e.g., AXI master + slave, UART TX + RX).

```python
from VeriGenX.agents.archweaver.multi_agent_builder import MultiAgentDAGBuilder

builder = MultiAgentDAGBuilder()

# Two-agent AXI testbench
dag = builder.build_multi_agent(["master", "slave"], design_name="axi")
# Generates: master_driver, master_monitor, master_sequence, master_agent
#            slave_driver,  slave_monitor,  slave_sequence,  slave_agent
#            + shared: interface, sequence_item, scoreboard, coverage, env, top
```

**Methods:**

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `build_multi_agent(agent_names, design_name)` | `List[str], str` | `dict` | Builds multi-agent DAG |
| `build_from_test_plan(test_plan_path, agent_names)` | `str, List[str]` | `dict` | Reads test plan and builds multi-agent DAG |

**Shared vs. Per-Agent Components:**

| Category | Components |
|----------|-----------|
| Shared | interface, sequence_item, scoreboard, coverage, env, top |
| Per-Agent | `{name}_driver`, `{name}_monitor`, `{name}_sequence`, `{name}_agent` |

**Multi-Agent DAG Output:**
```json
{
  "components":   ["interface", "master_driver", "slave_driver", ...],
  "dependencies": {"env": ["master_agent", "slave_agent", "scoreboard", ...]},
  "design_name":  "axi",
  "agent_count":  2,
  "agent_names":  ["master", "slave"]
}
```

---

### `LLMConflictResolver`
**File:** `llm_conflict_resolver.py`

Uses the local Ollama LLM to generate specific resolution suggestions for detected conflicts. Falls back gracefully when Ollama is unavailable.

```python
from VeriGenX.agents.archweaver.llm_conflict_resolver import LLMConflictResolver

resolver  = LLMConflictResolver()
resolved  = resolver.resolve(conflicts, spec_context=spec_text)
resolver.report_with_resolutions(resolved)
```

**Methods:**

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `resolve(conflicts, spec_context)` | `List[dict], str` | `List[dict]` | Augments each conflict with `llm_resolution` key |
| `report_with_resolutions(resolved)` | `List[dict]` | `None` | Prints full report with LLM suggestions |

> **Requires Ollama running** at `http://localhost:11434`. Falls back to rule-based suggestion text if unavailable.

---

## Pipeline Flow

```
test_plans/uart_test_plan.json
        |
        v
  DAGBuilder.build_from_test_plan()
        |
        v
  ConflictDetector.detect_conflicts()  -->  LLMConflictResolver.resolve()
        |
        v
  Resolver.resolve()                    -->  topologically sorted list
        |
        v
  Resolver.get_generation_order()       -->  [{component, filename, order}]
        |
        v
  Resolver.export_dot()                 -->  dag.dot  (Graphviz)
```

---

## Running Phase 2

```bash
# Quick integration test
python test_phase2.py

# Full pytest suite (66 tests)
pytest tests/test_archweaver.py -v

# Combined Phase 1 + Phase 2 (107 tests)
pytest tests/ -v

# Full pipeline via orchestrator
python -m VeriGenX.orchestrator --spec input_designs/uart_spec.txt

# Visualize DAG (requires Graphviz)
dot -Tpng dag.dot -o dag.png
```
