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
    axi_lite_if iface (
        .aclk(clk),
        .aresetn(rst_n)
    );

    // DUT instantiation
    axi_lite dut (
        .aclk(clk),
        .aresetn(rst_n)
        
        
        
        
        
        
        , .awaddr(iface.awaddr)
        
        
        
        , .awvalid(iface.awvalid)
        
        
        
        , .awready(iface.awready)
        
        
        
        , .wdata(iface.wdata)
        
        
        
        , .wvalid(iface.wvalid)
        
        
        
        , .wready(iface.wready)
        
        
        
        , .bresp(iface.bresp)
        
        
        
        , .bvalid(iface.bvalid)
        
        
        
        , .bready(iface.bready)
        
        
    );

    // Test run and interface configuration
    initial begin
        uvm_config_db#(virtual axi_lite_if)::set(null, "uvm_test_top*", "vif", iface);
        run_test();
    end

    // {% llm_fill "top_extra" %}
    // Heuristic fill fallback
// {% endllm_fill %}

endmodule