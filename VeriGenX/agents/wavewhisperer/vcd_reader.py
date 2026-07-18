import os
import re
import pandas as pd
from typing import Dict, Any, List

class VCDReader:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.id_to_sig: Dict[str, str] = {}
        self.id_to_base_sig: Dict[str, str] = {}
        self.sig_to_id: Dict[str, str] = {}
        self.timescale: str = "1ps"

    def parse(self) -> pd.DataFrame:
        """
        Parses a VCD file and returns a pandas DataFrame where:
        - The index is the integer simulation timestamp
        - Columns are the base signal names
        - Values are the signal values at each timestamp (forward-filled)
        """
        if not os.path.exists(self.filepath):
            raise FileNotFoundError(f"VCD file not found at: {self.filepath}")

        with open(self.filepath, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

        scopes: List[str] = []
        time_dict: Dict[int, Dict[str, Any]] = {}
        current_time = 0
        
        # Initialize time 0
        time_dict[0] = {}

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Scope tracking
            if line.startswith("$scope"):
                parts = line.split()
                if len(parts) >= 3:
                    scopes.append(parts[2])
                continue
            elif line.startswith("$upscope"):
                if scopes:
                    scopes.pop()
                continue

            # Timescale tracking
            elif line.startswith("$timescale"):
                self.timescale = line.replace("$timescale", "").replace("$end", "").strip()
                continue

            # Variable declarations
            elif line.startswith("$var"):
                parts = line.split()
                if len(parts) >= 6:
                    var_id = parts[3]
                    base_name = parts[4]
                    
                    full_name = ".".join(scopes + [base_name])
                    self.id_to_sig[var_id] = full_name
                    self.id_to_base_sig[var_id] = base_name
                    self.sig_to_id[full_name] = var_id
                continue

            # Time markers
            elif line.startswith("#"):
                try:
                    current_time = int(line[1:])
                except ValueError:
                    pass
                if current_time not in time_dict:
                    time_dict[current_time] = {}
                continue

            # Value changes
            # Vector value change: e.g. b00000000 $
            if line.startswith("b") or line.startswith("B"):
                parts = line.split()
                if len(parts) == 2:
                    val = parts[0][1:]  # strip 'b'
                    var_id = parts[1]
                    
                    # If it contains X or Z, keep as uppercase string
                    if any(c in val.lower() for c in ('x', 'z')):
                        val_parsed = val.upper()
                    else:
                        try:
                            val_parsed = int(val, 2)
                        except ValueError:
                            val_parsed = val
                    
                    base_sig = self.id_to_base_sig.get(var_id)
                    if base_sig:
                        time_dict[current_time][base_sig] = val_parsed
                continue

            # Single bit value change: e.g. 1# or 0# or x#
            if line[0] in ('0', '1', 'x', 'y', 'z', 'X', 'Y', 'Z'):
                val = line[0].upper()
                var_id = line[1:]
                
                if val == '0':
                    val_parsed = 0
                elif val == '1':
                    val_parsed = 1
                else:
                    val_parsed = val  # 'X' or 'Z'
                    
                base_sig = self.id_to_base_sig.get(var_id)
                if base_sig:
                    time_dict[current_time][base_sig] = val_parsed
                continue

        if not time_dict or (len(time_dict) == 1 and not time_dict[0]):
            return pd.DataFrame()

        df = pd.DataFrame.from_dict(time_dict, orient="index")
        df.index.name = "timestamp"
        df.sort_index(inplace=True)
        # Forward fill continuous signals
        df = df.ffill().fillna(0)
        return df
