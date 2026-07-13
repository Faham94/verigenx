# Phase 4 Completion Report — SimRunner Orchestration

We have completed **Phase 4: SimRunner**, the SystemVerilog/UVM simulation and verification orchestrator for VeriGenX.

## Verification Metrics Summary (UART Design)

Based on the fresh end-to-end simulation run of the generated UVM testbench against the loopback DUT, the parsed verification metrics are:

- **Simulation Status**: **PASSED** (100% test completion)
- **Line Coverage**: **62.6%**
- **Branch Coverage**: **47.4%**
- **Toggle Coverage**: **33.9%**
- **Functional Coverage**: **Unmeasurable (due to Verilator limitations)**

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

### 4. Functional Coverage Unmeasurability Caveat
Verilator is a cycle-accurate RTL simulator and does not support compiling or evaluating SystemVerilog OOP covergroup/coverpoint objects at simulation runtime. Calling `.get_coverage()` on a covergroup is unsupported. Hence, functional coverage is unmeasurable under Verilator and defaults to `Unmeasurable` in the reports and UI.
