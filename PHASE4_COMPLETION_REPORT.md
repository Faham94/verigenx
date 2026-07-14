# Phase 4 Completion Report — SimRunner Orchestration

We have completed **Phase 4: SimRunner**, the SystemVerilog/UVM simulation and verification orchestrator for VeriGenX.

## Verification Metrics Summary (UART Design)

Based on the fresh end-to-end simulation run of the generated UVM testbench against the loopback DUT, the parsed verification metrics are:

- **Simulation Status**: **PASSED** (100% test completion)
- **Line Coverage**: **67.0%**
- **Branch Coverage**: **68.5%**
- **Toggle Coverage**: **45.5%**
- **Functional Coverage**: **33.3%**

## Architectural & Technical Gaps Resolved

### 1. Cross-Platform Compilation & Linking
SimRunner compiles topologically-sorted UVM files together with the mock library wrapper. We resolved compatibility bugs:
- **Separators**: Set the compiler setup to configure `PATH` and toolchain paths selectively when running on Windows (`os.name == 'nt'`), preventing path corruption on Linux/Docker.
- **Binary Suffix**: Dynamically configured binary output extension (using `.exe` on Windows and no extension on Linux/Unix).
- **Process exit on $finish**: SystemVerilog `$finish` halts C++ execution immediately by invoking `exit()`. We registered `std::atexit()` callbacks inside `sim_main.cpp` to correctly flush VCD traces and write `coverage.dat` files at simulation exit.

### 2. SOH/STX Delimited Coverage parsing
Verilator uses structured control characters (`\x01` and `\x02` ASCII delimiters) inside `coverage.dat`. By writing a direct delimiter parser, we extracted and isolated:
- **Statement/Line Coverage**: Counted points marked with type `line`.
- **Branch Coverage**: Counted points marked with type `branch` (instead of copying line metrics).
- **Toggle Coverage**: Counted points marked with type `toggle`.

### 3. Dynamic UVM Test Class Discovery
Instead of hardcoding or guessing test class names, SimRunner now scans the generated SystemVerilog source code files via regular expressions to find any classes that inherit from `uvm_test` (e.g. `uart_test_base`, `uart_test_directed`). This list is executed sequentially using `+UVM_TESTNAME=<test_name>`.

### 4. Mock UVM Functional Coverage Measurement
Since Verilator does not support runtime SystemVerilog covergroup/coverpoint evaluation, we extended the mock UVM framework to support functional coverage:
- **Manual Hit-Counters**: Declared per-functional-point hit counters (e.g., `hit_FP_xxx`) in the coverage subscriber class.
- **Condition Checking**: Incremented the counters inside the `write()` function based on sequence item fields.
- **JSON Dumping**: Overrode `report_phase()` to compute the overall functional coverage percentage and dump the hit counts to `functional_coverage_report.json` at simulation exit.
- **SimRunner Integration**: Updated the coverage parser to read this JSON file to report exact functional coverage metrics.
