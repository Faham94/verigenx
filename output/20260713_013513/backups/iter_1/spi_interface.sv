interface spi_if (
    input logic clk,
    input logic rst_n
);

    // Signals declaration
    
    
    
    
    
    
    logic  mosi;
    
    
    
    logic  miso;
    
    
    
    logic  sclk;
    
    
    
    logic  cs_n;
    
    

    // Clocking block for testbench synchronization
    clocking cb @(posedge clk);
        default input #1ns output #1ns;
        
        
        
        
        
        
        output mosi;
        
        
        
        input miso;
        
        
        
        input sclk;
        
        
        
        input cs_n;
        
        
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