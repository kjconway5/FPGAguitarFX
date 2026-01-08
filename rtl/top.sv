// Top-level design file for the icebreaker FPGA board
//
// Wi23, Lab 1
module top
  (input [0:0] clk_12mhz_i
  ,input [0:0] reset_n_async_unsafe_i
   // n: Negative Polarity (0 when pressed, 1 otherwise)
   // async: Not synchronized to clock
   // unsafe: Not De-Bounced
  ,input [3:1] button_async_unsafe_i
   // async: Not synchronized to clock
   // unsafe: Not De-Bounced
  ,output [5:1] led_o);

  // For this lab, instantiate your and2 gate. Using two wires from
  // btn_async_unsafe_i, drive an output wire in led_o.
  //
  // Your code goes here:
  and2 u1 (
    .a_i(button_async_unsafe_i[1]),
    .b_i(button_async_unsafe_i[2]),
    .c_o(led_o[1])
  );

endmodule
