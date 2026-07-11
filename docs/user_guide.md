# VeriGenX User Guide

Welcome to the **VeriGenX** user guide. This document describes how to configure, run, and test the pipeline.

## Getting Started

### Prerequisites
- Python 3.11+
- Graphviz (for rendering `.dot` diagrams)
- Ollama (running locally with `deepseek-coder-v2` and `nomic-embed-text` models)

### Installation
1. Install Python packages:
   ```bash
   pip install -r requirements.txt
   ```
2. Start Ollama and download required models:
   ```bash
   ollama pull deepseek-coder-v2:16b-lite-instruct-q4_K_M
   ollama pull nomic-embed-text
   ```

## Running the Verification Pipeline

### Command Line Interface
Execute the orchestrator directly by passing a spec document:
```bash
python -m VeriGenX.orchestrator --spec input_designs/uart_spec.txt
```

### Dashboard (Streamlit)
To interact with the GUI dashboard and trigger the pipeline visually:
```bash
streamlit run app.py
```
Browse to `http://localhost:8501` to view overview metrics, register mappings, FSM status, and trigger pipeline executions.
