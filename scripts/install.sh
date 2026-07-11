#!/bin/bash
# VeriGenX Installation Script
set -e

echo "=== Installing VeriGenX ==="
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment and installing dependencies..."
source venv/bin/activate || source venv/Scripts/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "Installation complete. Run tests with: make test"
