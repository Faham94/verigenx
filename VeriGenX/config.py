"""
VeriGenX Configuration
"""
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

INPUT_DESIGNS_DIR  = os.path.join(BASE_DIR, "input_designs")
GENERATED_UVM_DIR  = os.path.join(BASE_DIR, "generated_uvm")
TEST_PLANS_DIR     = os.path.join(BASE_DIR, "test_plans")
LOGS_DIR           = os.path.join(BASE_DIR, "logs")
CACHE_DIR          = os.path.join(BASE_DIR, ".cache")  # Incremental update cache

OLLAMA_BASE_URL    = "http://localhost:11434"
DEEPSEEK_MODEL     = "deepseek-coder-v2:16b"
EMBEDDING_MODEL    = "nomic-embed-text"
CHROMADB_PATH      = os.path.join(BASE_DIR, "chromadb_store")

UVM_CODEGEN_MODEL  = "deepseek-coder-v2:16b"
REPAIR_MODEL       = "qwen2.5-coder:7b"

# LLM generation settings
LLM_TEMPERATURE    = 0.3
LLM_MAX_TOKENS     = 4096
LLM_TIMEOUT        = 120

# Confidence thresholds
CONFIDENCE_HIGH    = 0.8
CONFIDENCE_MEDIUM  = 0.5
CONFIDENCE_LOW     = 0.0

# Coverage targets
LINE_COVERAGE      = 100
BRANCH_COVERAGE    = 100
FSM_COVERAGE       = 100
