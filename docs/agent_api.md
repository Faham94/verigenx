# SpecMind Agent API Reference

## Overview

SpecMind is Phase 1 of the VeriGenX pipeline. It ingests RTL specification documents, chunks them semantically, embeds them into ChromaDB, uses an LLM to extract structured data, and outputs a structured JSON test plan.

**Module path:** `VeriGenX/agents/specmind/`

---

## Classes

### `DocumentIngestor`
**File:** `ingestion.py`

Parses specification documents in TXT, PDF, and DOCX formats.

```python
from VeriGenX.agents.specmind.ingestion import DocumentIngestor

ingestor = DocumentIngestor()
result = ingestor.ingest("input_designs/uart_spec.txt")
# result: {"text": str, "file_type": str, "metadata": dict}
```

**Methods:**

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `ingest(file_path)` | `file_path: str` | `dict` | Auto-detects format and dispatches |
| `_ingest_txt(file_path)` | `file_path: str` | `dict` | Plain text reader (UTF-8) |
| `_ingest_pdf(file_path)` | `file_path: str` | `dict` | PDF reader via PyMuPDF |
| `_ingest_docx(file_path)` | `file_path: str` | `dict` | DOCX reader via python-docx |

**Return schema:**
```json
{
  "text": "<extracted text>",
  "file_type": "txt | pdf | docx",
  "metadata": {
    "title": "<filename>",
    "pages": "<int, PDF only>"
  }
}
```

---

### `Chunker`
**File:** `chunker.py`

Splits specification text into semantically coherent, overlapping chunks.

```python
from VeriGenX.agents.specmind.chunker import Chunker

chunker = Chunker(chunk_size=500, overlap=100)
chunks = chunker.chunk_document(text, metadata={})
```

**Constructor Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `chunk_size` | `int` | `500` | Maximum words per chunk |
| `overlap` | `int` | `100` | Word overlap between adjacent chunks |

**Methods:**

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `chunk_document(text, metadata)` | `str, dict` | `List[dict]` | Section-aware chunking |
| `_split_long_section(text)` | `str` | `List[str]` | Word-level chunking for long sections |

**Chunk schema:**
```json
{
  "text": "<chunk text>",
  "chunk_index": "0 | 0_1",
  "section": "Section 1",
  "metadata": {}
}
```

---

### `Embedder`
**File:** `embedder.py`

Manages ChromaDB collections for persistent semantic search.

```python
from VeriGenX.agents.specmind.embedder import Embedder

embedder = Embedder(collection_name="verigenx_specs")
embedder.add(chunks)
results = embedder.search("baud rate configuration", n_results=5)
```

**Methods:**

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `add(chunks)` | `List[dict]` | `bool` | Adds chunks to ChromaDB |
| `search(query, n_results)` | `str, int` | `List[str]` | Semantic similarity search |
| `delete_collection()` | — | `None` | Deletes the ChromaDB collection |

> **Note:** If ChromaDB is unavailable, `Embedder` gracefully falls back without crashing the pipeline.

---

### `Extractor`
**File:** `extractor.py`

Uses Ollama LLM + RAG to extract structured data from specification text.

```python
from VeriGenX.agents.specmind.extractor import Extractor

extractor = Extractor()
signals   = extractor.extract_signals(context)
states    = extractor.extract_fsm_states(context)
registers = extractor.extract_registers(context)
timing    = extractor.extract_timing(context)
all_data  = extractor.extract_all(context)
```

**Methods:**

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `extract_signals(context)` | `str` | `List[dict]` | Extracts interface signals |
| `extract_fsm_states(context)` | `str` | `List[str]` | Extracts FSM state names |
| `extract_registers(context)` | `str` | `List[dict]` | Extracts register map entries |
| `extract_timing(context)` | `str` | `dict` | Extracts timing constraints |
| `extract_all(context)` | `str` | `dict` | Runs all extractions |

> **Requires Ollama running** at `http://localhost:11434`. Degrades gracefully if unavailable.

---

### `TestPlanGenerator`
**File:** `test_plan.py`

Converts extracted knowledge into a structured JSON test plan.

```python
from VeriGenX.agents.specmind.test_plan import TestPlanGenerator

generator = TestPlanGenerator()
plan = generator.generate(text)
path = generator.save(plan, filename="uart_test_plan.json")
```

**Methods:**

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `generate(text)` | `str` | `dict` | Builds test plan dict |
| `save(plan, filename)` | `dict, str` | `str` | Saves JSON to `test_plans/` |

**Output follows:** `docs/test_plan_schema.json`

---

## LLM Utilities

### `OllamaClient`
**File:** `VeriGenX/llm/ollama_client.py`

| Method | Description |
|--------|-------------|
| `generate(prompt, model, temperature, max_tokens)` | Text completion |
| `embed(text)` | Embedding vector via `nomic-embed-text` |
| `is_available()` | Returns `True` if Ollama is reachable |

### `ResponseValidator`
**File:** `VeriGenX/llm/response_validator.py`

| Method | Description |
|--------|-------------|
| `validate_json(response)` | Extracts and parses JSON object |
| `validate_json_array(response)` | Extracts and parses JSON array |
| `extract_signals(response)` | Parses signal list from LLM output |
| `extract_fsm_states(response)` | Parses FSM state list |
| `extract_registers(response)` | Parses register list |
| `extract_timing(response)` | Parses timing constraints object |

### `prompt_library`
**File:** `VeriGenX/llm/prompt_library.py`

| Key | Purpose |
|-----|---------|
| `specmind_signal_extraction` | Extract interface signals |
| `specmind_fsm_extraction` | Extract FSM states |
| `specmind_register_extraction` | Extract register map |
| `specmind_timing_extraction` | Extract timing constraints |

```python
from VeriGenX.llm.prompt_library import get_prompt, get_all_prompts
prompt = get_prompt("specmind_signal_extraction")
```

---

## Pipeline Flow

```
Specification File (TXT / PDF / DOCX)
        |
        v
  DocumentIngestor.ingest()
        |
        v
  Chunker.chunk_document()
        |
        v
  Embedder.add()  ------>  ChromaDB (persistent)
        |
        v
  Extractor.extract_all()  <--  Embedder.search() [RAG]
        |                         |
        |                    OllamaClient.generate()
        v
  TestPlanGenerator.generate()
        |
        v
  test_plans/uart_test_plan.json
```

---

## Running Phase 1

```bash
# Quick test
python test_phase1.py

# Full pipeline via orchestrator
python -m VeriGenX.orchestrator --spec input_designs/uart_spec.txt

# Run unit tests
pytest tests/test_specmind.py -v
```
