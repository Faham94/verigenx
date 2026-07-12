"""
Transaction Model Generator for UVMForge.
Parses signals and generates proper SystemVerilog types, enums, structs, and constraints.
"""
from typing import List, Dict, Any

class TransactionModelGenerator:
    def __init__(self, signals: List[Dict[str, Any]]):
        self.signals = signals

    def generate_types_and_fields(self) -> str:
        """Generates declarations of fields, enums, and structs."""
        lines = []
        # Exclude system clock and reset signals
        filtered_signals = [
            s for s in self.signals 
            if s["name"].lower() not in ["clk", "rst_n", "aclk", "aresetn"]
        ]
        
        # Check if we should declare an enum
        declared_enums = {}
        for s in filtered_signals:
            name = s["name"].lower()
            desc = s.get("description", "").lower()
            width = s.get("width", 1)
            
            if ("mode" in name or "cmd" in name or "state" in name or "op" in name) and width > 1:
                enum_name = f"{s['name']}_enum_t"
                # Define simple enum values
                enum_values = [f"{s['name'].upper()}_VAL_{i}" for i in range(min(2**width, 4))]
                enum_str = f"    typedef enum bit [{width-1}:0] {{\n"
                enum_str += ",\n".join(f"        {val} = {idx}" for idx, val in enumerate(enum_values))
                enum_str += f"\n    }} {enum_name};"
                lines.append(enum_str)
                declared_enums[s["name"]] = enum_name
        
        if lines:
            lines.append("") # empty line after enums
            
        # Check if we should declare any struct (packed struct support)
        has_struct = False
        for s in filtered_signals:
            desc = s.get("description", "").lower()
            if "struct" in desc or "packed" in desc:
                has_struct = True
                break
                
        if has_struct:
            lines.append("    typedef struct packed {")
            lines.append("        bit [7:0] payload;")
            lines.append("        bit       error;")
            lines.append("    } packet_struct_t;")
            lines.append("")

        # Now declare fields
        for s in filtered_signals:
            name = s["name"]
            width = s.get("width", 1)
            desc = s.get("description", "").lower()
            
            # Use declared enum if applicable
            if name in declared_enums:
                lines.append(f"    rand {declared_enums[name]} {name};")
            elif "struct" in desc or "packed" in desc:
                lines.append(f"    rand packet_struct_t {name};")
            else:
                if width > 1:
                    lines.append(f"    rand bit [{width-1}:0] {name};")
                else:
                    lines.append(f"    rand bit {name};")
                    
        return "\n".join(lines)

    def generate_constraints(self) -> str:
        """Generates randomization constraints for transaction fields."""
        lines = ["    // Randomization constraints"]
        filtered_signals = [
            s for s in self.signals 
            if s["name"].lower() not in ["clk", "rst_n", "aclk", "aresetn"]
        ]
        
        for s in filtered_signals:
            name = s["name"]
            width = s.get("width", 1)
            
            # Heuristically add constraints based on width
            if width > 1:
                max_val = (2**width) - 1
                if width <= 8:
                    lines.append(f"    constraint c_{name}_range {{ {name} <= {max_val}; }}")
                else:
                    # Larger width, constrain to reasonable test values
                    lines.append(f"    constraint c_{name}_val {{ {name} < {2**(width-2)}; }}")
            else:
                # 1-bit fields: distribute values
                if "valid" in name.lower() or "ready" in name.lower() or "enable" in name.lower():
                    lines.append(f"    constraint c_{name}_dist {{ {name} dist {{ 0 := 30, 1 := 70 }}; }}")
                    
        return "\n".join(lines)
