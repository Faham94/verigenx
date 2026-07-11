module fifo_dut (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       wr_en,
    input  wire       rd_en,
    input  wire [7:0] wr_data,
    output reg  [7:0] rd_data,
    output reg        full,
    output reg        empty
);
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            rd_data <= 8'h00;
            full    <= 1'b0;
            empty   <= 1'b1;
        end else begin
            if (wr_en && !full) begin
                rd_data <= wr_data;
                empty   <= 1'b0;
            end
        end
    end
endmodule
