module axi_lite_dut (
    input  wire        aclk,
    input  wire        aresetn,
    input  wire [31:0] awaddr,
    input  wire        awvalid,
    output reg         awready,
    input  wire [31:0] wdata,
    input  wire        wvalid,
    output reg         wready,
    output reg  [1:0]  bresp,
    output reg         bvalid,
    input  wire        bready
);
    always @(posedge aclk or negedge aresetn) begin
        if (!aresetn) begin
            awready <= 1'b0;
            wready  <= 1'b0;
            bresp   <= 2'b00;
            bvalid  <= 1'b0;
        end else begin
            awready <= awvalid;
            wready  <= wvalid;
            bvalid  <= wvalid && awvalid;
        end
    end
endmodule
