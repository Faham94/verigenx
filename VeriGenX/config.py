"""
VeriGenX Configuration
"""
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

INPUT_DESIGNS_DIR = os.path.join(BASE_DIR, "input_designs")
GENERATED_UVM_DIR = os.path.join(BASE_DIR, "generated_uvm")
TEST_PLANS_DIR = os.path.join(BASE_DIR, "test_plans")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

OLLAMA_BASE_URL = "http://localhost:11434"
DEEPSEEK_MODEL = "deepseek-coder-v2:16b"
EMBEDDING_MODEL = "nomic-embed-text"
CHROMADB_PATH = os.path.join(BASE_DIR, "chromadb_store")
