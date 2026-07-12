class uart_coverage extends uvm_subscriber #(uart_seq_item);

    `uvm_component_utils(uart_coverage)

    uart_seq_item t;

    // Auto-derived covergroups from functional points
    covergroup uart_cg;
        option.per_instance = 1;

        
        // FP_001: Data transmission functionality
        // {% llm_fill "FP_001" %}
        cp_FP_001: coverpoint t.rx_data;
// {% endllm_fill %}
        
        
        // FP_002: Baud rate configuration
        // {% llm_fill "FP_002" %}
        cp_FP_002: coverpoint t.tx_data;
// {% endllm_fill %}
        
        
        // FP_003: Reset and initialisation
        // {% llm_fill "FP_003" %}
        cp_FP_003: coverpoint t.rx_data;
// {% endllm_fill %}
        
        
    endgroup

    function new(string name = "uart_coverage", uvm_component parent = null);
        super.new(name, parent);
        uart_cg = new();
    endfunction

    virtual function void write(uart_seq_item t);
        this.t = t;
        // {% llm_fill "coverage_sample" %}
        uart_cg.sample();
// {% endllm_fill %}
    endfunction

endclass