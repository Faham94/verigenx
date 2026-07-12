interface axi_lite_if (
    input logic aclk,
    input logic aresetn
);

    // Signals declaration
    
    
    
    
    
    
    logic [31:0] awaddr;
    
    
    
    logic  awvalid;
    
    
    
    logic  awready;
    
    
    
    logic [31:0] wdata;
    
    
    
    logic  wvalid;
    
    
    
    logic  wready;
    
    
    
    logic [1:0] bresp;
    
    
    
    logic  bvalid;
    
    
    
    logic  bready;
    
    

    // Clocking block for testbench synchronization
    clocking cb @(posedge aclk);
        default input #1ns output #1ns;
        
        
        
        
        
        
        output awaddr;
        
        
        
        output awvalid;
        
        
        
        input awready;
        
        
        
        output wdata;
        
        
        
        output wvalid;
        
        
        
        input wready;
        
        
        
        input bresp;
        
        
        
        input bvalid;
        
        
        
        output bready;
        
        
    endclocking

    // TB modport
    modport tb (
        clocking cb,
        input aclk,
        input aresetn
    );

    // {% llm_fill "interface_assertions" %}
    // TODO: Add SystemVerilog assertions for protocol compliance checking
// {% endllm_fill %}

endinterface