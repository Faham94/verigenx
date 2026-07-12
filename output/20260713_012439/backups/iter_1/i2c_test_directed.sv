class i2c_test_directed extends i2c_test_base;

    `uvm_component_utils(i2c_test_directed)

    function new(string name = "i2c_test_directed", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    virtual task run_phase(uvm_phase phase);
        i2c_sequence seq;
        phase.raise_objection(this);
        
        seq = i2c_sequence::type_id::create("seq");
        
        // {% llm_fill "test_directed_run" %}
    // Heuristic fill fallback
// {% endllm_fill %}
        
        phase.drop_objection(this);
    endtask

endclass