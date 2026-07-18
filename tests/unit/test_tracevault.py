import os
import tempfile
import pytest
from VeriGenX.agents.tracevault.db_manager import TraceabilityDBManager

@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = TraceabilityDBManager(path)
    yield db
    try:
        os.remove(path)
    except Exception:
        pass

def test_db_schema_and_inserts(temp_db):
    db = temp_db
    
    # 1. Insert Spec Sections
    sec_id1 = db.insert_spec_section("uart", "1. Signals", "Signal details")
    sec_id2 = db.insert_spec_section("uart", "2. Protocol", "Protocol details")
    
    assert sec_id1 is not None
    assert sec_id2 is not None

    # 2. Insert Functional Points
    fp_id1 = db.insert_functional_point("uart", "FP_001", "Verify data transmission", sec_id1)
    fp_id2 = db.insert_functional_point("uart", "FP_002", "Verify baud configuration", sec_id2)
    
    assert fp_id1 is not None
    assert fp_id2 is not None

    # 3. Insert Test Cases
    t_id1 = db.insert_test_case("uart", "uart_test_base", "generated_uvm/uart_test_base.sv")
    t_id2 = db.insert_test_case("uart", "uart_test_directed", "generated_uvm/uart_test_directed.sv")
    
    assert t_id1 is not None
    assert t_id2 is not None

    # 4. Insert Coverage Bins
    bin_id1 = db.insert_coverage_bin("uart", "FP_001", achieved=100.0)
    bin_id2 = db.insert_coverage_bin("uart", "FP_002", achieved=50.0)
    
    assert bin_id1 is not None
    assert bin_id2 is not None

    # 5. Insert Simulation Results
    sr_id1 = db.insert_simulation_result("uart", "uart_test_base", "passed", "Sim passed successfully")
    sr_id2 = db.insert_simulation_result("uart", "uart_test_directed", "failed", "Baud check mismatch error")
    
    assert sr_id1 is not None
    assert sr_id2 is not None

    # 6. Link entities
    db.link_fp_to_test(fp_id1, t_id1)
    db.link_fp_to_test(fp_id2, t_id2)
    db.link_test_to_bin(t_id1, bin_id1)
    db.link_test_to_bin(t_id2, bin_id2)

    # 7. Query bidirectional links: section -> tests
    tests_sec1 = db.get_tests_by_section("uart", "1. Signals")
    assert len(tests_sec1) == 1
    assert tests_sec1[0]["test_name"] == "uart_test_base"
    assert tests_sec1[0]["status"] == "passed"

    # 8. Query bidirectional links: test -> sections/requirements
    reqs_test2 = db.get_requirements_by_test("uart", "uart_test_directed")
    assert len(reqs_test2) == 1
    assert reqs_test2[0]["section_name"] == "2. Protocol"
    assert reqs_test2[0]["fp_id"] == "FP_002"
