interface axi_if (
    input logic clock,
    input logic rst_n
);

    // Signals declaration
    
    
    logic  aclk;
    
    
    
    logic [31:0] awaddr;
    
    
    
    logic  awvalid;
    
    
    
    logic  awready;
    
    
    
    logic [31:0] wdata;
    
    
    
    logic  wvalid;
    
    
    
    logic  wready;
    
    
    
    logic [1:0] bresp;
    
    
    
    logic  bvalid;
    
    
    
    logic  bready;
    
    
    
    
    
    logic  write;
    
    

    // Clocking block for testbench synchronization
    clocking cb @(posedge clock);
        default input #1ns output #1ns;
        
        
        output aclk;
        
        
        
        output awaddr;
        
        
        
        output awvalid;
        
        
        
        input awready;
        
        
        
        output wdata;
        
        
        
        output wvalid;
        
        
        
        input wready;
        
        
        
        input bresp;
        
        
        
        input bvalid;
        
        
        
        output bready;
        
        
        
        
        
        output write;
        
        
    endclocking

    // TB modport
    modport tb (
        clocking cb,
        input clock,
        input rst_n
    );

    // {% llm_fill "interface_assertions" %}
    // TODO: Add SystemVerilog assertions for protocol compliance checking
// {% endllm_fill %}

endinterface