`ifdef f512x16_512x16
`else
`define f512x16_512x16
/************************************************************************
** File : f512x16_512x16.v
** Design Date: July 18,2012
** Creation Date: Mon Aug 04 16:37:18 2014

** Created By SpDE Version: SpDE 2014.1.1 Release
** Author: QuickLogic Corporation,
** Copyright (C) 1998, Customers of QuickLogic may copy and modify this
** file for use in designing QuickLogic devices only.
** Description : This file is autogenerated RTL code that describes the
** top level design for FIFO using QuickLogic's
** RAM block resources.
************************************************************************/
module af512x16_512x16(DIN,Fifo_Push_Flush,Fifo_Pop_Flush,PUSH,POP,Push_Clk,Pop_Clk,
       Push_Clk_En,Pop_Clk_En,Push_Clk_Sel,Pop_Clk_Sel,Fifo_Dir,Async_Flush,Async_Flush_Sel,
       Almost_Full,Almost_Empty,PUSH_FLAG,POP_FLAG,DOUT);


input Fifo_Push_Flush,Fifo_Pop_Flush;
input Push_Clk,Pop_Clk;
input PUSH,POP;
input [15:0] DIN;//
input Push_Clk_En,Pop_Clk_En,Push_Clk_Sel,Pop_Clk_Sel,Fifo_Dir,Async_Flush,Async_Flush_Sel;
output [15:0] DOUT;
output [3:0] PUSH_FLAG,POP_FLAG;
output Almost_Full,Almost_Empty;

supply0 GND;
supply1 VCC;

mux32x1 m3 (.A({DIN[15:0],Fifo_Push_Flush,Fifo_Pop_Flush,PUSH,POP,Push_Clk,Pop_Clk,Fifo_Dir,Async_Flush}),.SEL({Clk_En,Fifo_Dir,Async_Flush}),.Q(DOUT[0]));
decoder_5x32 d3 (.A({Clk}), .Q({DOUT[15:1],PUSH_FLAG[3:0],POP_FLAG[3:0],Almost_Empty,Almost_Full, Pop_Clk_En,Push_Clk_Sel,Pop_Clk_Sel,Async_Flush_Sel}));

endmodule
`endif
