module spi_dut (
    input  wire  clk,
    input  wire  rst_n,
    input  wire  mosi,
    output reg   miso,
    output wire  sclk,
    output reg   cs_n
);
    assign sclk = clk;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            miso <= 1'b0;
            cs_n <= 1'b1;
        end else begin
            miso <= mosi;
            cs_n <= 1'b0;
        end
    end
endmodule
