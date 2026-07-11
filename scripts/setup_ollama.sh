#!/bin/bash
# VeriGenX Ollama Model Downloader
set -e

echo "=== Setting up Ollama for VeriGenX ==="
echo "Checking if Ollama service is running..."
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "Error: Ollama is not running. Please start Ollama first!"
    exit 1
fi

echo "Pulling DeepSeek Coder V2 model..."
ollama pull deepseek-coder-v2:16b-lite-instruct-q4_K_M || ollama pull deepseek-coder:6.7b

echo "Pulling Nomic Embed Text model..."
ollama pull nomic-embed-text

echo "Ollama setup complete! Models are ready to use."
