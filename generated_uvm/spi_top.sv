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
    spi_if iface (
        .clk(clk),
        .rst_n(rst_n)
    );

    // DUT instantiation
    spi dut (
        .clk(clk),
        .rst_n(rst_n)
        
        
        
        
        
        
        , .mosi(iface.mosi)
        
        
        
        , .miso(iface.miso)
        
        
        
        , .sclk(iface.sclk)
        
        
        
        , .cs_n(iface.cs_n)
        
        
    );

    // Test run and interface configuration
    initial begin
        uvm_config_db#(virtual spi_if)::set(null, "uvm_test_top*", "vif", iface);
        run_test();
    end

    // {% llm_fill "top_extra" %}
    // Heuristic fill fallback
// {% endllm_fill %}

endmodule