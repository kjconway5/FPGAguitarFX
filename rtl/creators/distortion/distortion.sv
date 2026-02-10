module distortion #(
  parameter int width = 24
 ) (
  input logic clk,
  input logic rst,

  input logic signed [width-1:0] in_signal,
  output logic signed [width-1:0] out_signal, 

  input logic signed [width-1:0] threshold
);

  always_ff @(posedge clk) begin 
    if (rst) begin 
      out_signal <= '0;
    end else begin 
      if (in_signal > threshold) begin 
        out_signal <= threshold;
      end else if (in_signal < -threshold) begin 
        out_signal <= -threshold;
      end else begin 
        out_signal <= in_signal;
      end
    end
  end


endmodule
