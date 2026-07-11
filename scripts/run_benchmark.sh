#!/bin/bash
# VeriGenX Benchmark Run Script
set -e

echo "=== Running VeriGenX ArchWeaver Benchmark ==="
source venv/bin/activate || source venv/Scripts/activate

# Execute pytest specifically on the benchmark tests
python -m pytest tests/unit/test_archweaver.py -k TestBenchmarkFiveDesigns -v

echo "Benchmark execution completed successfully!"
