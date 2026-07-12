interface uart_if (
    input logic clk,
    input logic rst_n
);

    // Signals declaration
    
    
    
    
    
    
    logic [7:0] tx_data;
    
    
    
    logic [7:0] rx_data;
    
    

    // Clocking block for testbench synchronization
    clocking cb @(posedge clk);
        default input #1ns output #1ns;
        
        
        
        
        
        
        output tx_data;
        
        
        
        input rx_data;
        
        
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