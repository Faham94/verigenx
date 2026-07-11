module uart_dut (
    input  wire       clk,
    input  wire       rst_n,
    input  wire [7:0] tx_data,
    output reg  [7:0] rx_data
);
    // UART Transmitter / Receiver model
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            rx_data <= 8'h00;
        end else begin
            rx_data <= tx_data;
        end
    end
endmodule
