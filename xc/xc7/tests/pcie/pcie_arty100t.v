module top(
  input  wire clk,

  input  wire [7:0] sw,
  output wire [7:0] led
);
    assign led[7:1] = sw[7:1];
    
    wire drp_rdy, sys_rst_n;
    assign sys_rst_n = sw[0];
    assign led[0] = drp_rdy;
    
    PCIE_2_1 #(
        .LINK_CAP_MAX_LINK_WIDTH(8)
    ) PCIE_INST (
        .DRPRDY(drp_rdy),
        .SYSRSTN(sys_rst_n)
    );

endmodule
