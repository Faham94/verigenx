# Phase 7 Completion Report: TraceVault — Spec-to-Coverage Traceability Matrix

This report documents the design, implementation, and validation of **TraceVault** (Phase 7), the spec-to-coverage traceability matrix engine for VeriGenX.

---

## 1. Architectural Overview

TraceVault implements an auditable traceability database that aggregates spec definitions, test plan structures, SystemVerilog UVM testbenches, and dynamic simulation reports into a relational schema:

```
                                +---------------------------+
                                |  input_designs/*_spec.txt |
                                +---------------------------+
                                              |
                                              v
+-----------------------------+     +-------------------+     +---------------------------+
|  test_plans/*_test_plan.json| --> |   MatrixBuilder   | <-- |   generated_uvm/*.sv      |
+-----------------------------+     +-------------------+     +---------------------------+
                                              |
                                              v
                                +---------------------------+
                                |   SQLite Database         |
                                |   (traceability.db)       |
                                +---------------------------+
                                              |
                                              v
+-----------------------------+     +-------------------+     +---------------------------+
|  interactive HTML report    | <-- |   ReportExporter  | --> |   app.py                  |
|  (heatmap + anchor links)   |     +-------------------+     |   (Streamlit Dashboard)   |
+-----------------------------+                               +---------------------------+
```

---

## 2. Key Modules & Implementations

### A. SQLite Database Manager (`db_manager.py`)
* Establishes a relational SQLite database schema containing five primary tables (`spec_sections`, `functional_points`, `test_cases`, `coverage_bins`, `simulation_results`) and two junction tables (`fp_test_links`, `test_bin_links`).
* Exposes query APIs to fetch bidirectional mappings:
  * **Given a spec section** -> Return all test cases that trace to it (identifying their verification status).
  * **Given a test case** -> Return all spec requirements/functional points it satisfies.
* Implements robust connection cleanup using `try...finally` contexts to avoid file-lock errors on Windows.

### B. Matrix Builder (`matrix_builder.py`)
* Automatically parses sections and functional points from specification files and test plans.
* Scans `generated_uvm/` for all testbenches, including CoverHunter-added directed tests (e.g. `uart_test_directed_IDLE.sv`).
* Maps test hits, targeted gaps, and coverage parameters from CoverHunter and SimRunner logs.

### C. Report Exporter (`report_exporter.py`)
* Generates `CLIENT_REPORT_TRACEABILITY.html` containing:
  * **Traceability Heatmap:** A visual matrix linking spec sections and functional points to tests and coverage outcomes.
  * **Requirement Completion Table:** Computes the completion progress percentage of each section from real links (average coverage of its linked FPs), showing `0.0%` for sections with zero linked functional points.
  * **Bidirectional Cross-Reference Links:** Navigation links using internal HTML `#anchor` cross-references for seamless navigation.

---

## 3. Disclosures & Caveats

> [!WARNING]
> **Functional Coverage Proxy Discloser:**
> The functional coverage numbers represented in TraceVault trace back to a manual hit-counter proxy inside the mock UVM subscriber rather than native SystemVerilog covergroups. This proxy tracks code execution paths as an approximation.

> [!CAUTION]
> **Mock UVM Library Caveat:**
> Compilation and simulation checks are validated against `uvm_mock.svh` (a lightweight UVM-compatible library), not the full Accellera UVM package.

---

## 4. Database Query Verification Results

A query session run against the generated SQLite database (`output/traceability.db`) produced the following results:

```text
==========================================================
TRACELVAULT SQLITE DATABASE VERIFICATION
==========================================================

Spec Sections Count: 5
Sections found:
  - 1. Signals
  - 2. Protocol: 8-N-1
  - 3. FSM States
  - 4. Registers
  - 5. Timing Constraints

Functional Points Count: 3
  - FP_001: Data transmission functionality
  - FP_002: Baud rate configuration
  - FP_003: Reset and initialisation

Section-Wise Coverage and Completion Rates:
  - 1. Signals: 1 linked FPs | Completion: 100.00%
  - 2. Protocol: 8-N-1: 1 linked FPs | Completion: 100.00%
  - 3. FSM States: 1 linked FPs | Completion: 100.00%
  - 4. Registers: 0 linked FPs | Completion: 0.00%
  - 5. Timing Constraints: 0 linked FPs | Completion: 0.00%

Bidirectional Query: tests tracing to section '3. FSM States'
  - Test: uart_test_base | Status: passed | File: generated_uvm\uart_test_base.sv
  - Test: uart_test_directed | Status: passed | File: generated_uvm\uart_test_directed.sv
  - Test: uart_test_directed_IDLE | Status: passed | File: generated_uvm\uart_test_directed_IDLE.sv

Bidirectional Query: requirements satisfied by test 'uart_test_directed_IDLE'
  - Section: 3. FSM States | Requirement: FP_001 - Data transmission functionality
  - Section: 2. Protocol: 8-N-1 | Requirement: FP_002 - Baud rate configuration
  - Section: 1. Signals | Requirement: FP_003 - Reset and initialisation
```

---

## 5. Deliverables Generated on Disk
* Core Package: [VeriGenX/agents/tracevault/](file:///c:/Users/Dell/Desktop/PROJECT/VeriGenX/agents/tracevault/)
* SQLite Database: [output/traceability.db](file:///c:/Users/Dell/Desktop/PROJECT/output/traceability.db)
* Interactive Traceability Report: [CLIENT_REPORT_TRACEABILITY.html](file:///c:/Users/Dell/Desktop/PROJECT/CLIENT_REPORT_TRACEABILITY.html) (SPI and I2C reports are also compiled)
* Global Dashboard Updates: [index.html](file:///c:/Users/Dell/Desktop/PROJECT/index.html), [CLIENT_REPORT.html](file:///c:/Users/Dell/Desktop/PROJECT/CLIENT_REPORT.html), and [app.py](file:///c:/Users/Dell/Desktop/PROJECT/app.py)
