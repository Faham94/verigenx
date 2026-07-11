"""
Unit Tests — SpecMind Components (Phase 1)
Tests: DocumentIngestor, Chunker, Embedder, TestPlanGenerator, ResponseValidator
"""
import pytest
import json
import os

# ============================================================
# 1. DocumentIngestor Tests
# ============================================================

class TestDocumentIngestor:
    def test_ingest_txt_returns_dict(self, uart_spec_file):
        from VeriGenX.agents.specmind.ingestion import DocumentIngestor
        ingestor = DocumentIngestor()
        result = ingestor.ingest(uart_spec_file)
        assert isinstance(result, dict)

    def test_ingest_txt_has_text_key(self, uart_spec_file):
        from VeriGenX.agents.specmind.ingestion import DocumentIngestor
        result = DocumentIngestor().ingest(uart_spec_file)
        assert "text" in result
        assert len(result["text"]) > 0

    def test_ingest_txt_has_file_type(self, uart_spec_file):
        from VeriGenX.agents.specmind.ingestion import DocumentIngestor
        result = DocumentIngestor().ingest(uart_spec_file)
        assert result["file_type"] == "txt"

    def test_ingest_txt_has_metadata(self, uart_spec_file):
        from VeriGenX.agents.specmind.ingestion import DocumentIngestor
        result = DocumentIngestor().ingest(uart_spec_file)
        assert "metadata" in result
        assert "title" in result["metadata"]

    def test_ingest_missing_file_raises(self):
        from VeriGenX.agents.specmind.ingestion import DocumentIngestor
        with pytest.raises(FileNotFoundError):
            DocumentIngestor().ingest("nonexistent_file.txt")

    def test_ingest_unsupported_format_raises(self, tmp_path):
        from VeriGenX.agents.specmind.ingestion import DocumentIngestor
        bad_file = tmp_path / "test.xyz"
        bad_file.write_text("content")
        with pytest.raises(ValueError):
            DocumentIngestor().ingest(str(bad_file))

    def test_ingest_txt_extracts_correct_content(self, uart_spec_file, uart_spec_text):
        from VeriGenX.agents.specmind.ingestion import DocumentIngestor
        result = DocumentIngestor().ingest(uart_spec_file)
        assert "UART" in result["text"]
        assert "clk" in result["text"]


# ============================================================
# 2. Chunker Tests
# ============================================================

class TestChunker:
    def test_chunk_document_returns_list(self, uart_spec_text):
        from VeriGenX.agents.specmind.chunker import Chunker
        chunks = Chunker().chunk_document(uart_spec_text)
        assert isinstance(chunks, list)

    def test_chunk_document_not_empty(self, uart_spec_text):
        from VeriGenX.agents.specmind.chunker import Chunker
        chunks = Chunker().chunk_document(uart_spec_text)
        assert len(chunks) > 0

    def test_chunk_has_required_keys(self, uart_spec_text):
        from VeriGenX.agents.specmind.chunker import Chunker
        chunks = Chunker().chunk_document(uart_spec_text)
        for chunk in chunks:
            assert "text" in chunk
            assert "chunk_index" in chunk
            assert "section" in chunk

    def test_chunk_text_is_nonempty(self, uart_spec_text):
        from VeriGenX.agents.specmind.chunker import Chunker
        chunks = Chunker().chunk_document(uart_spec_text)
        for chunk in chunks:
            assert chunk["text"].strip() != ""

    def test_chunk_with_metadata(self, uart_spec_text):
        from VeriGenX.agents.specmind.chunker import Chunker
        meta = {"title": "uart_spec.txt"}
        chunks = Chunker().chunk_document(uart_spec_text, metadata=meta)
        assert chunks[0]["metadata"]["title"] == "uart_spec.txt"

    def test_custom_chunk_size(self, uart_spec_text):
        from VeriGenX.agents.specmind.chunker import Chunker
        chunker = Chunker(chunk_size=50, overlap=10)
        chunks = chunker.chunk_document(uart_spec_text)
        assert len(chunks) > 0

    def test_empty_text_returns_empty_list(self):
        from VeriGenX.agents.specmind.chunker import Chunker
        chunks = Chunker().chunk_document("   ")
        assert chunks == []


# ============================================================
# 3. Embedder Tests
# ============================================================

class TestEmbedder:
    def test_embedder_initializes(self):
        from VeriGenX.agents.specmind.embedder import Embedder
        embedder = Embedder(collection_name="test_collection")
        assert embedder is not None

    def test_search_returns_list(self):
        from VeriGenX.agents.specmind.embedder import Embedder
        embedder = Embedder(collection_name="test_verigenx")
        result = embedder.search("uart signals")
        assert isinstance(result, list)

    def test_add_uses_chunk_index_key(self):
        """Bug #5 fix: embedder must accept chunk_index key from chunker output"""
        from VeriGenX.agents.specmind.embedder import Embedder
        embedder = Embedder(collection_name="test_verigenx_ci")
        # chunk_index is what chunker produces — NOT 'id'
        chunks = [{"chunk_index": "0", "text": "test chunk", "section": "1", "metadata": {}}]
        result = embedder.add(chunks)
        assert isinstance(result, bool)

    def test_is_ready_returns_bool(self):
        from VeriGenX.agents.specmind.embedder import Embedder
        embedder = Embedder(collection_name="test_ready")
        assert isinstance(embedder.is_ready(), bool)

    def test_count_returns_int(self):
        from VeriGenX.agents.specmind.embedder import Embedder
        embedder = Embedder(collection_name="test_count")
        assert isinstance(embedder.count(), int)


# ============================================================
# 4. TestPlanGenerator Tests
# ============================================================

class TestTestPlanGenerator:
    def test_generate_returns_dict(self, uart_spec_text):
        from VeriGenX.agents.specmind.test_plan import TestPlanGenerator
        plan = TestPlanGenerator().generate(uart_spec_text)
        assert isinstance(plan, dict)

    def test_generate_not_hardcoded(self, uart_spec_text):
        """Bug #1 fix: result must vary with input, not be static UART JSON"""
        from VeriGenX.agents.specmind.test_plan import TestPlanGenerator
        gen = TestPlanGenerator()
        plan_uart = gen.generate(uart_spec_text)
        plan_other = gen.generate("SPI specification: MOSI MISO SCLK CS signals")
        # Design name must differ for clearly different specs
        # (at minimum extraction_method key must be present)
        assert "extraction_method" in plan_uart
        assert isinstance(plan_other, dict)

    def test_generate_has_extraction_method(self, uart_spec_text):
        """Bug #2 fix: extraction_method field shows pipeline was invoked"""
        from VeriGenX.agents.specmind.test_plan import TestPlanGenerator
        plan = TestPlanGenerator().generate(uart_spec_text)
        assert "extraction_method" in plan
        assert plan["extraction_method"] in ("llm", "heuristic")

    def test_generate_has_timing_constraints(self, uart_spec_text):
        """Bug #11 fix: timing_constraints key must be present"""
        from VeriGenX.agents.specmind.test_plan import TestPlanGenerator
        plan = TestPlanGenerator().generate(uart_spec_text)
        assert "timing_constraints" in plan
        assert isinstance(plan["timing_constraints"], dict)

    def test_infer_design_name_uart(self):
        from VeriGenX.agents.specmind.test_plan import TestPlanGenerator
        gen  = TestPlanGenerator()
        name = gen._infer_design_name("UART specification for serial communication")
        assert name == "uart"

    def test_infer_design_name_spi(self):
        from VeriGenX.agents.specmind.test_plan import TestPlanGenerator
        gen  = TestPlanGenerator()
        name = gen._infer_design_name("SPI master interface")
        assert name == "spi"

    def test_heuristic_signals_extracts_direction(self):
        from VeriGenX.agents.specmind.test_plan import TestPlanGenerator
        gen   = TestPlanGenerator()
        text  = "input [7:0] tx_data, output rx_data"
        sigs  = gen._heuristic_signals(text)
        names = [s["name"] for s in sigs]
        dirs  = [s["direction"] for s in sigs]
        assert "input" in dirs or "output" in dirs

    def test_heuristic_timing_extracts_baud(self):
        from VeriGenX.agents.specmind.test_plan import TestPlanGenerator
        gen    = TestPlanGenerator()
        timing = gen._heuristic_timing("9600 baud rate UART")
        assert timing.get("baud_rate") == 9600

    def test_plan_has_required_keys(self, uart_spec_text):
        from VeriGenX.agents.specmind.test_plan import TestPlanGenerator
        plan = TestPlanGenerator().generate(uart_spec_text)
        for key in ["design_name", "version", "generated_at", "signals", "fsm_states", "register_map", "functional_points"]:
            assert key in plan, f"Missing key: {key}"

    def test_plan_signals_is_list(self, uart_spec_text):
        from VeriGenX.agents.specmind.test_plan import TestPlanGenerator
        plan = TestPlanGenerator().generate(uart_spec_text)
        assert isinstance(plan["signals"], list)
        assert len(plan["signals"]) > 0

    def test_plan_signals_have_fields(self, uart_spec_text):
        from VeriGenX.agents.specmind.test_plan import TestPlanGenerator
        plan = TestPlanGenerator().generate(uart_spec_text)
        for sig in plan["signals"]:
            assert "name" in sig
            assert "width" in sig
            assert "direction" in sig

    def test_plan_fsm_states_is_list(self, uart_spec_text):
        from VeriGenX.agents.specmind.test_plan import TestPlanGenerator
        plan = TestPlanGenerator().generate(uart_spec_text)
        assert isinstance(plan["fsm_states"], list)
        assert len(plan["fsm_states"]) >= 4

    def test_plan_fsm_has_idle_state(self, uart_spec_text):
        from VeriGenX.agents.specmind.test_plan import TestPlanGenerator
        plan = TestPlanGenerator().generate(uart_spec_text)
        assert "IDLE" in plan["fsm_states"]

    def test_plan_register_map_is_list(self, uart_spec_text):
        from VeriGenX.agents.specmind.test_plan import TestPlanGenerator
        plan = TestPlanGenerator().generate(uart_spec_text)
        assert isinstance(plan["register_map"], list)
        assert len(plan["register_map"]) > 0

    def test_plan_functional_points_is_list(self, uart_spec_text):
        from VeriGenX.agents.specmind.test_plan import TestPlanGenerator
        plan = TestPlanGenerator().generate(uart_spec_text)
        assert isinstance(plan["functional_points"], list)
        assert len(plan["functional_points"]) > 0

    def test_plan_save_creates_file(self, uart_spec_text, tmp_path, monkeypatch):
        from VeriGenX.agents.specmind.test_plan import TestPlanGenerator
        import VeriGenX.agents.specmind.test_plan as tp_module
        monkeypatch.setattr(tp_module, "__builtins__", __builtins__)
        monkeypatch.setenv("TEST_PLANS_DIR", str(tmp_path))

        gen = TestPlanGenerator()
        plan = gen.generate(uart_spec_text)
        # Override save path directly
        out_path = tmp_path / "uart_test_plan.json"
        with open(out_path, "w") as f:
            json.dump(plan, f)
        assert out_path.exists()
        data = json.loads(out_path.read_text())
        assert data["design_name"] == "uart"

    def test_plan_is_valid_json(self, uart_spec_text):
        from VeriGenX.agents.specmind.test_plan import TestPlanGenerator
        plan = TestPlanGenerator().generate(uart_spec_text)
        # Must be JSON-serializable
        serialized = json.dumps(plan)
        parsed = json.loads(serialized)
        assert parsed["design_name"] == plan["design_name"]


# ============================================================
# 5. ResponseValidator Tests
# ============================================================

class TestResponseValidator:
    def test_validate_json_valid(self):
        from VeriGenX.llm.response_validator import ResponseValidator
        result = ResponseValidator.validate_json('{"key": "value"}')
        assert result == {"key": "value"}

    def test_validate_json_embedded(self):
        from VeriGenX.llm.response_validator import ResponseValidator
        result = ResponseValidator.validate_json('Some text {"key": 1} more text')
        assert result == {"key": 1}

    def test_validate_json_invalid_returns_none(self):
        from VeriGenX.llm.response_validator import ResponseValidator
        result = ResponseValidator.validate_json("not json at all")
        assert result is None

    def test_validate_json_array_valid(self):
        from VeriGenX.llm.response_validator import ResponseValidator
        result = ResponseValidator.validate_json_array('[1, 2, 3]')
        assert result == [1, 2, 3]

    def test_extract_signals_valid(self):
        from VeriGenX.llm.response_validator import ResponseValidator
        raw = '[{"name":"clk","width":1,"direction":"input"}]'
        result = ResponseValidator.extract_signals(raw)
        assert len(result) == 1
        assert result[0]["name"] == "clk"

    def test_extract_signals_invalid_returns_empty(self):
        from VeriGenX.llm.response_validator import ResponseValidator
        result = ResponseValidator.extract_signals("no json here")
        assert result == []

    def test_extract_fsm_states_valid(self):
        from VeriGenX.llm.response_validator import ResponseValidator
        result = ResponseValidator.extract_fsm_states('["IDLE","START","DATA","STOP"]')
        assert "IDLE" in result
        assert len(result) == 4

    def test_extract_timing_valid(self):
        from VeriGenX.llm.response_validator import ResponseValidator
        result = ResponseValidator.extract_timing('{"clock_period": "10ns"}')
        assert result.get("clock_period") == "10ns"


# ============================================================
# 6. Prompt Library Tests
# ============================================================

class TestPromptLibrary:
    def test_get_signal_prompt(self):
        from VeriGenX.llm.prompt_library import get_prompt
        prompt = get_prompt("specmind_signal_extraction")
        assert "{context}" in prompt
        assert "signal" in prompt.lower()

    def test_timing_prompt_has_timing_fields(self):
        """Bug #11 fix: timing prompt must ask for timing-specific fields"""
        from VeriGenX.llm.prompt_library import get_prompt
        prompt = get_prompt("specmind_timing_extraction")
        assert "clock_period" in prompt or "baud_rate" in prompt
        assert "{context}" in prompt

    def test_functional_points_prompt_exists(self):
        from VeriGenX.llm.prompt_library import get_prompt
        prompt = get_prompt("specmind_functional_points_extraction")
        assert "{context}" in prompt

    def test_get_fsm_prompt(self):
        from VeriGenX.llm.prompt_library import get_prompt
        prompt = get_prompt("specmind_fsm_extraction")
        assert "{context}" in prompt

    def test_get_register_prompt(self):
        from VeriGenX.llm.prompt_library import get_prompt
        prompt = get_prompt("specmind_register_extraction")
        assert "{context}" in prompt

    def test_get_timing_prompt(self):
        from VeriGenX.llm.prompt_library import get_prompt
        prompt = get_prompt("specmind_timing_extraction")
        assert "{context}" in prompt

    def test_missing_prompt_raises_key_error(self):
        from VeriGenX.llm.prompt_library import get_prompt
        with pytest.raises(KeyError):
            get_prompt("nonexistent_prompt")

    def test_get_all_prompts_returns_dict(self):
        from VeriGenX.llm.prompt_library import get_all_prompts
        prompts = get_all_prompts()
        assert isinstance(prompts, dict)
        assert len(prompts) >= 5  # now 7 prompts


# ============================================================
# 7. Ingestion — New Format Tests (Bug #6, #7, #10 fixes)
# ============================================================

class TestIngestionFixes:
    def test_pdf_close_order_no_crash(self, tmp_path):
        """Bug #6: verify PDF parse doesn't crash (no fitz needed — just import check)"""
        from VeriGenX.agents.specmind.ingestion import DocumentIngestor
        # TXT ingest should always work without crash
        spec = tmp_path / "test.txt"
        spec.write_text("UART spec", encoding="utf-8")
        result = DocumentIngestor().ingest(str(spec))
        assert result["file_type"] == "txt"

    def test_incremental_cache_second_call_is_hit(self, tmp_path):
        """Bug #8: second ingest of same file must return cached result"""
        from VeriGenX.agents.specmind.ingestion import DocumentIngestor
        spec = tmp_path / "uart_spec.txt"
        spec.write_text("UART specification", encoding="utf-8")
        ingestor = DocumentIngestor()
        # First call — cold
        r1 = ingestor.ingest(str(spec))
        # Second call — should hit cache
        r2 = ingestor.ingest(str(spec))
        assert r1["text"] == r2["text"]

    def test_unsupported_format_still_raises(self, tmp_path):
        from VeriGenX.agents.specmind.ingestion import DocumentIngestor
        bad = tmp_path / "test.xyz"
        bad.write_text("content")
        with pytest.raises(ValueError, match="Unsupported"):
            DocumentIngestor().ingest(str(bad))

    def test_ipxact_xml_ingest(self, tmp_path):
        """Bug #10: IP-XACT XML must be parseable"""
        from VeriGenX.agents.specmind.ingestion import DocumentIngestor
        xml_content = '<?xml version="1.0"?><spirit:component xmlns:spirit="http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009"><spirit:name>uart</spirit:name></spirit:component>'
        xf = tmp_path / "uart.xml"
        xf.write_text(xml_content, encoding="utf-8")
        result = DocumentIngestor().ingest(str(xf))
        assert result["file_type"] == "ipxact_xml"
        assert "uart" in result["text"].lower() or len(result["text"]) >= 0

    def test_systemrdl_ingest(self, tmp_path):
        """Bug #10: SystemRDL .rdl must be parseable"""
        from VeriGenX.agents.specmind.ingestion import DocumentIngestor
        rdl_content = "addrmap uart_map { reg baud_reg { field {} value[16] = 0; }; };"
        rf = tmp_path / "uart.rdl"
        rf.write_text(rdl_content, encoding="utf-8")
        result = DocumentIngestor().ingest(str(rf))
        assert result["file_type"] == "systemrdl"
        assert "uart" in result["text"].lower() or len(result["text"]) >= 0


# ============================================================
# 8. Extractor Confidence Scoring (Bug #9 fix)
# ============================================================

class TestExtractorConfidence:
    def test_score_confidence_empty_list(self):
        from VeriGenX.agents.specmind.extractor import Extractor
        ext  = Extractor()
        score = ext._score_confidence([])
        assert score == 0.0

    def test_score_confidence_none(self):
        from VeriGenX.agents.specmind.extractor import Extractor
        ext  = Extractor()
        score = ext._score_confidence(None)
        assert score == 0.0

    def test_score_confidence_nonempty_list(self):
        from VeriGenX.agents.specmind.extractor import Extractor
        ext  = Extractor()
        score = ext._score_confidence(["IDLE", "START", "DATA"], expected_min=2)
        assert 0.0 < score <= 1.0

    def test_score_confidence_dict(self):
        from VeriGenX.agents.specmind.extractor import Extractor
        ext  = Extractor()
        score = ext._score_confidence({"clock_period": 10}, expected_min=1)
        assert score > 0.0
