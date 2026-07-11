# VeriGenX Makefile for easy workflow orchestration

.PHONY: install test run-dashboard clean build-graph benchmark

install:
	python -m venv venv
	./venv/Scripts/pip install --upgrade pip
	./venv/Scripts/pip install -r requirements.txt

test:
	./venv/Scripts/python -m pytest tests/ -v --tb=short

run-dashboard:
	./venv/Scripts/streamlit run app.py

build-graph:
	./venv/Scripts/python -m VeriGenX.orchestrator --spec input_designs/uart_spec.txt

benchmark:
	./venv/Scripts/python -m pytest tests/unit/test_archweaver.py -k TestBenchmarkFiveDesigns -v

clean:
	rm -rf .pytest_cache .cache htmlcov .coverage
	find . -type d -name "__pycache__" -exec rm -rf {} +
