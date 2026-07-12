class axi_lite_coverage extends uvm_subscriber #(axi_lite_seq_item);

    `uvm_component_utils(axi_lite_coverage)

    axi_lite_seq_item t;

    // Auto-derived covergroups from functional points
    covergroup axi_lite_cg;
        option.per_instance = 1;

        
        // FP_001: Reset and initialisation
        // {% llm_fill "FP_001" %}
        cp_FP_001: coverpoint t.awvalid;
// {% endllm_fill %}
        
        
    endgroup

    function new(string name = "axi_lite_coverage", uvm_component parent = null);
        super.new(name, parent);
        axi_lite_cg = new();
    endfunction

    virtual function void write(axi_lite_seq_item t);
        this.t = t;
        // {% llm_fill "coverage_sample" %}
        axi_lite_cg.sample();
// {% endllm_fill %}
    endfunction

endclass