class axi_coverage extends uvm_subscriber #(axi_seq_item);

    `uvm_component_utils(axi_coverage)

    axi_seq_item t;

    // Auto-derived covergroups from functional points
    covergroup axi_cg;
        option.per_instance = 1;

        
        // FP_005: Reset and initialisation
        // {% llm_fill "FP_005" %}
        cp_FP_005: coverpoint t.wready;
// {% endllm_fill %}
        
        
    endgroup

    function new(string name = "axi_coverage", uvm_component parent = null);
        super.new(name, parent);
        axi_cg = new();
    endfunction

    virtual function void write(axi_seq_item t);
        this.t = t;
        // {% llm_fill "coverage_sample" %}
        axi_cg.sample();
// {% endllm_fill %}
    endfunction

endclass