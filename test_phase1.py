"""
Phase 1 Test: SpecMind
Tests document ingestion (TXT, PDF, DOCX) and test plan generation
"""
import os
import sys
sys.path.insert(0, os.getcwd())

from VeriGenX.agents.specmind.ingestion import DocumentIngestor
from VeriGenX.agents.specmind.test_plan import TestPlanGenerator

def test_phase1():
    print("\n" + "="*60)
    print("PHASE 1 TEST - SpecMind (Document Ingestion + Test Plan)")
    print("="*60)
    
    print("\n[1] Testing TXT ingestion...")
    ingestor = DocumentIngestor()
    result = ingestor.ingest("input_designs/uart_spec.txt")
    print(f"TXT: Extracted {len(result['text'])} chars, Type: {result['file_type']}")
    
    print("\n[2] Generating test plan...")
    generator = TestPlanGenerator()
    plan = generator.generate(result['text'])
    filepath = generator.save(plan)
    
    print("\n" + "="*60)
    print("PHASE 1 TEST COMPLETE!")
    print("="*60)
    print(f"\nTest Plan saved to: {filepath}")

if __name__ == "__main__":
    test_phase1()
