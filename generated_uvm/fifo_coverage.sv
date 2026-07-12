class fifo_coverage extends uvm_subscriber #(fifo_seq_item);

    `uvm_component_utils(fifo_coverage)

    fifo_seq_item t;

    // Auto-derived covergroups from functional points
    covergroup fifo_cg;
        option.per_instance = 1;

        
        // FP_001: Reset and initialisation
        // {% llm_fill "FP_001" %}
        cp_FP_001: coverpoint t.rd_en;
// {% endllm_fill %}
        
        
        // FP_002: Full-condition boundary behavior
        // {% llm_fill "FP_002" %}
        cp_FP_002: coverpoint t.full;
// {% endllm_fill %}
        
        
        // FP_003: Empty-condition boundary behavior
        // {% llm_fill "FP_003" %}
        cp_FP_003: coverpoint t.empty;
// {% endllm_fill %}
        
        
    endgroup

    function new(string name = "fifo_coverage", uvm_component parent = null);
        super.new(name, parent);
        fifo_cg = new();
    endfunction

    virtual function void write(fifo_seq_item t);
        this.t = t;
        // {% llm_fill "coverage_sample" %}
        fifo_cg.sample();
// {% endllm_fill %}
    endfunction

endclass