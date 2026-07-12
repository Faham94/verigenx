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
    axi_if iface (
        .clock(clk),
        .rst_n(rst_n)
    );

    // DUT instantiation
    axi dut (
        .clock(clk),
        .rst_n(rst_n)
        
        
        , .aclk(iface.aclk)
        
        
        
        , .awaddr(iface.awaddr)
        
        
        
        , .awvalid(iface.awvalid)
        
        
        
        , .awready(iface.awready)
        
        
        
        , .wdata(iface.wdata)
        
        
        
        , .wvalid(iface.wvalid)
        
        
        
        , .wready(iface.wready)
        
        
        
        , .bresp(iface.bresp)
        
        
        
        , .bvalid(iface.bvalid)
        
        
        
        , .bready(iface.bready)
        
        
        
        
        
        , .write(iface.write)
        
        
    );

    // Test run and interface configuration
    initial begin
        uvm_config_db#(virtual axi_if)::set(null, "uvm_test_top*", "vif", iface);
        run_test();
    end

    // {% llm_fill "top_extra" %}
    // Heuristic fill fallback
// {% endllm_fill %}

endmodule