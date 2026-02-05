module overdrive #(
  parameter int width = 16
 ) (
  input logic clk,
  input logic rst,

  input logic signed [width-1:0] in_signal,
  output logic signed [width-1:0] out_signal

);

  logic signed [width-1:0] lut_out;

  softclip_lut lut (
    .in_signal(in_signal),
    .out_signal(lut_out)
  );

  always_ff @(posedge clk) begin 
    if (rst) begin 
      out_signal <= '0;
    end else begin 
      out_signal <= lut_out;
    end
  end


endmodule
