class fifo_test_directed extends fifo_test_base;

    `uvm_component_utils(fifo_test_directed)

    function new(string name = "fifo_test_directed", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    virtual task run_phase(uvm_phase phase);
        fifo_sequence seq;
        phase.raise_objection(this);
        
        seq = fifo_sequence::type_id::create("seq");
        
        // {% llm_fill "test_directed_run" %}
    // Heuristic fill fallback
// {% endllm_fill %}
        
        phase.drop_objection(this);
    endtask

endclass