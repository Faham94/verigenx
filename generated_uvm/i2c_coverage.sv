class i2c_coverage extends uvm_subscriber #(i2c_seq_item);

    `uvm_component_utils(i2c_coverage)

    // Auto-derived covergroups from functional points
    covergroup i2c_cg;
        option.per_instance = 1;

        
        // FP_001: Reset and initialisation
        // {% llm_fill "FP_001" %}
        cp_FP_001: coverpoint t.clk;
// {% endllm_fill %}
        
        
        // FP_002: Acknowledge/no-acknowledge handling
        // {% llm_fill "FP_002" %}
        cp_FP_002: coverpoint t.clk;
// {% endllm_fill %}
        
        
    endgroup

    function new(string name = "i2c_coverage", uvm_component parent = null);
        super.new(name, parent);
        i2c_cg = new();
    endfunction

    virtual function void write(i2c_seq_item t);
        // {% llm_fill "coverage_sample" %}
        // Sample auto-derived covergroups
        // cgroup.sample();
// {% endllm_fill %}
    endfunction

endclass