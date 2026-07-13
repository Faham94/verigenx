import os
import subprocess
import shutil
from typing import Tuple, List, Dict, Any

class SimCompiler:
    def __init__(self):
        pass

    def _get_verilator_cmd(self) -> Tuple[bool, str]:
        """Locates the Verilator executable path."""
        # Option 1: check standard path
        try:
            subprocess.run(
                ["verilator", "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False,
                check=True
            )
            return True, "verilator"
        except Exception:
            pass

        # Option 2: check MSYS2 path
        msys_verilator = r"C:\msys64\mingw64\bin\verilator_bin.exe"
        if os.path.exists(msys_verilator):
            os.environ["VERILATOR_ROOT"] = r"C:\msys64\mingw64\share\verilator"
            return True, msys_verilator

        return False, ""

    def is_verilator_available(self) -> bool:
        return self._get_verilator_cmd()[0]

    def generate_sim_main(self, filepath: str):
        """Generates a main C++ wrapper for Verilator simulation."""
        content = """#include "Vtop.h"
#include "verilated.h"
#include "verilated_vcd_c.h"
#include <string>
#include <iostream>
#include <cstdlib>

double g_main_time = 0.0;
double sc_time_stamp() {
    return g_main_time;
}

#if VM_COVERAGE
void save_coverage() {
    Verilated::threadContextp()->coveragep()->write("coverage.dat");
}
#endif

VerilatedVcdC* g_tfp = nullptr;
void close_trace() {
    if (g_tfp) {
        g_tfp->close();
    }
}

int main(int argc, char** argv) {
    Verilated::commandArgs(argc, argv);
#if VM_COVERAGE
    std::atexit(save_coverage);
#endif
    Vtop* top = new Vtop;

    std::string vcd_file = "waveform.vcd";
    for (int i = 1; i < argc; i++) {
        std::string arg = argv[i];
        if (arg.find("+VCD_FILE=") == 0) {
            vcd_file = arg.substr(10);
        }
    }

    Verilated::traceEverOn(true);
    VerilatedVcdC* tfp = new VerilatedVcdC;
    g_tfp = tfp;
    std::atexit(close_trace);
    top->trace(tfp, 99);
    tfp->open(vcd_file.c_str());

    vluint64_t main_time = 0;
    while (!Verilated::gotFinish()) {
        top->eval();
        tfp->dump(main_time);
        main_time++;
        g_main_time = static_cast<double>(main_time);
        Verilated::timeInc(1);
    }

    top->final();
    tfp->close();

    delete top;
    return 0;
}
"""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

    def generate_dut_wrapper(self, design_name: str, signals: List[Dict[str, Any]], filepath: str):
        """Generates a SystemVerilog wrapper module to map design names to design_dut names."""
        ports = []
        inst_ports = []
        for sig in signals:
            direction = sig.get("direction", "input")
            # map input/output to input/output wire or logic
            width = sig.get("width", 1)
            width_str = f"[{width-1}:0]" if width > 1 else ""
            ports.append(f"    {direction} logic {width_str} {sig['name']}")
            inst_ports.append(f"        .{sig['name']}({sig['name']})")
        
        ports_str = ",\n".join(ports)
        inst_ports_str = ",\n".join(inst_ports)
        
        content = f"""module {design_name} (
{ports_str}
);
    {design_name}_dut inst (
{inst_ports_str}
    );
endmodule
"""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

    def compile(self, design_name: str, test_plan: Dict[str, Any], uvm_files: List[str], run_dir: str) -> Tuple[bool, str, str]:
        """
        Compiles the design and UVM files together.
        Returns (success, log_message, binary_path)
        """
        # Prepend MinGW-w64 paths first, then MSYS2 paths so make and gcc from MinGW-w64 are found (Windows only)
        if os.name == "nt":
            path = os.environ.get("PATH", "")
            mingw_bin = r"C:\msys64\mingw64\bin"
            msys_bin = r"C:\msys64\usr\bin"
            path_list = path.split(";")
            path_list = [p for p in path_list if p not in (mingw_bin, msys_bin, mingw_bin.lower(), msys_bin.lower())]
            os.environ["PATH"] = ";".join([mingw_bin, msys_bin] + path_list)
            os.environ["MSYSTEM"] = "MINGW64"


        os.makedirs(run_dir, exist_ok=True)
        
        available, verilator_path = self._get_verilator_cmd()
        if not available:
            return False, "Verilator is not installed on this system.", ""

        # Copy functional uvm_mock.svh to run_dir
        simrunner_dir = os.path.dirname(os.path.abspath(__file__))
        mock_source = os.path.join(simrunner_dir, "uvm_mock.svh")
        mock_dest = os.path.join(run_dir, "uvm_mock.svh")
        shutil.copy(mock_source, mock_dest)

        # Generate wrapper for module mismatch
        wrapper_path = os.path.join(run_dir, f"{design_name}_wrapper.sv")
        self.generate_dut_wrapper(design_name, test_plan.get("signals", []), wrapper_path)

        # Generate sim_main.cpp
        cpp_path = os.path.join(run_dir, "sim_main.cpp")
        self.generate_sim_main(cpp_path)

        # Find the DUT file in tests/fixtures/<design>/<design>_dut.v
        # Let's search standard path
        base_dir = os.getcwd()
        dut_path = os.path.join(base_dir, "tests", "fixtures", design_name, f"{design_name}_dut.v")
        if not os.path.exists(dut_path):
            return False, f"DUT file not found at {dut_path}", ""

        # Generate compilation wrapper file
        compile_wrapper_path = os.path.join(run_dir, "top_compile.sv")
        with open(compile_wrapper_path, "w", encoding="utf-8") as f:
            f.write('`include "uvm_mock.svh"\n')
            f.write(f'`include "{design_name}_wrapper.sv"\n')
            for uvm_file in uvm_files:
                f.write(f'`include "{uvm_file.replace(chr(92), "/")}"\n')

        # Command-line compilation list
        # Order: top_compile.sv wrapper, dut_path, cpp_path
        compilation_files = ["top_compile.sv", dut_path.replace("\\", "/"), "sim_main.cpp"]

        # Call verilator command
        cmd_args = [
            verilator_path,
            "--cc", "--exe", "--build",
            "--timing", "--coverage", "--trace",
            "--top-module", "top",
            "-CFLAGS", "-std=c++17",
            "-LDFLAGS", "-static -static-libgcc -static-libstdc++",
            "-Wall",
            "-Wno-fatal", "-Wno-EOFNEWLINE", "-Wno-DECLFILENAME",
            "-Wno-VARHIDDEN", "-Wno-WIDTHTRUNC", "-Wno-MODMISSING",
            "-I.",
            "-Mdir", "obj_dir",
            "-o", f"V{design_name}_sim"
        ] + compilation_files

        try:
            result = subprocess.run(
                cmd_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False,
                text=True,
                cwd=run_dir
            )
            binary_ext = ".exe" if os.name == "nt" else ""
            binary_path = os.path.join(run_dir, "obj_dir", f"V{design_name}_sim{binary_ext}")
            if result.returncode == 0 and os.path.exists(binary_path):
                return True, "Compilation successful.", binary_path
            else:
                log_msg = f"Stdout:\n{result.stdout}\nStderr:\n{result.stderr}"
                return False, log_msg, ""
        except Exception as e:
            return False, str(e), ""
