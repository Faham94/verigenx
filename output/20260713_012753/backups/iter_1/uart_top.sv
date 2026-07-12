module top;

    // Clock and Reset Generation
    logic clk;
    logic rst_n;

    // Clock generation
    initial begin
        clk = 0;
        forever #5 clk = ~clk;
    end

    // Reset generation
    initial begin
        rst_n = 0;
        #20 rst_n = 1;
    end

    // Interface instantiation
    uart_if iface (
        .clk(clk),
        .rst_n(rst_n)
    );

    // DUT instantiation
    uart dut (
        .clk(clk),
        .rst_n(rst_n)
        
        
        
        
        
        
        , .tx_data(iface.tx_data)
        
        
        
        , .rx_data(iface.rx_data)
        
        
    );

    // Test run and interface configuration
    initial begin
        uvm_config_db#(virtual uart_if)::set(null, "uvm_test_top*", "vif", iface);
        run_test();
    end

    // {% llm_fill "top_extra" %}
    // Heuristic fill fallback
// {% endllm_fill %}

endmodule