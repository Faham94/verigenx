module i2c_dut (
    input  wire  clk,
    input  wire  rst_n,
    inout  wire  scl,
    inout  wire  sda
);
    // Tri-state I2C bus model
    assign scl = 1'bz;
    assign sda = 1'bz;
endmodule
