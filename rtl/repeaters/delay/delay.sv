module delay #(
  parameter int width = 24,
  parameter int delay = 480 // 10 ms at 48 kHz
 ) (
  input logic clk,
  input logic rst,

  input logic signed [width-1:0] in_signal,
  output logic signed [width-1:0] out_signal

);

  


endmodule
