class spi_coverage extends uvm_subscriber #(spi_seq_item);

    `uvm_component_utils(spi_coverage)

    spi_seq_item t;

    // Auto-derived covergroups from functional points
    covergroup spi_cg;
        option.per_instance = 1;

        
        // FP_001: Reset and initialisation
        // {% llm_fill "FP_001" %}
        cp_FP_001: coverpoint t.miso;
// {% endllm_fill %}
        
        
        // FP_002: Chip-select assertion and de-assertion
        // {% llm_fill "FP_002" %}
        cp_FP_002: coverpoint t.sclk;
// {% endllm_fill %}
        
        
    endgroup

    function new(string name = "spi_coverage", uvm_component parent = null);
        super.new(name, parent);
        spi_cg = new();
    endfunction

    virtual function void write(spi_seq_item t);
        this.t = t;
        // {% llm_fill "coverage_sample" %}
        spi_cg.sample();
// {% endllm_fill %}
    endfunction

endclass