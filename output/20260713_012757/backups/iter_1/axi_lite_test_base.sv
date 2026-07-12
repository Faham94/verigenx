class axi_lite_test_base extends uvm_test;

    axi_lite_env env;

    `uvm_component_utils(axi_lite_test_base)

    function new(string name = "axi_lite_test_base", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    virtual function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        env = axi_lite_env::type_id::create("env", this);
    endfunction

    virtual task run_phase(uvm_phase phase);
        // {% llm_fill "test_base_run" %}
    // Heuristic fill fallback
// {% endllm_fill %}
    endtask

endclass