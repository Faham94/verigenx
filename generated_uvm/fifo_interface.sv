interface fifo_if (
    input logic clk,
    input logic rst_n
);

    // Signals declaration
    
    
    
    
    
    
    logic  wr_en;
    
    
    
    logic  rd_en;
    
    
    
    logic [7:0] wr_data;
    
    
    
    logic [7:0] rd_data;
    
    
    
    logic  full;
    
    
    
    logic  empty;
    
    

    // Clocking block for testbench synchronization
    clocking cb @(posedge clk);
        default input #1ns output #1ns;
        
        
        
        
        
        
        output wr_en;
        
        
        
        output rd_en;
        
        
        
        output wr_data;
        
        
        
        input rd_data;
        
        
        
        input full;
        
        
        
        input empty;
        
        
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