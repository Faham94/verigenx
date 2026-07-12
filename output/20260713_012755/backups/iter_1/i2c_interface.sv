interface i2c_if (
    input logic clk,
    input logic rst_n
);

    // Signals declaration
    
    
    
    
    
    
    logic  scl;
    
    
    
    logic  sda;
    
    

    // Clocking block for testbench synchronization
    clocking cb @(posedge clk);
        default input #1ns output #1ns;
        
        
        
        
        
        
        input scl;
        
        
        
        input sda;
        
        
    endclocking

    // TB modport
    modport tb (
        clocking cb,
        input clk,
        input rst_n
    );

    // {% llm_fill "interface_assertions" %}
    // TODO: Add SystemVerilog assertions for protocol compliance checking
// {% endllm_fill %}

endinterface