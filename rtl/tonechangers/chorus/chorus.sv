module chorus #(
  parameter int width = 24,
  // Delay in samples. At 48 kHz:
  //  5 ms = 240 samples
	// 10 ms = 480 samples
	// 20 ms = 960 samples
  parameter int delay = 480 // 10 ms at 48 kHz
) (
  input logic clk,
  input logic rst,

  input logic signed [width-1:0] in_signal,
  output logic signed [width-1:0] out_signal
);

  logic signed [width-1:0] wet_signal; 
  logic signed [width-1:0] wet_signal_delayed; 
  assign wet_signal = in_signal;
  logic signed [width-1:0] dry_signal;
  assign dry_signal = in_signal;

  delaybuffer delaymod #(
    .width_p(width),
    .delay_p(delay)
   ) (
    .clk_i(clk),
    .reset_i(rst),
    .data_i(wet_signal),
    .valid_i(1'b1),
    .ready_o(),
    .valid_o(),
    .data_o(wet_signal_delayed),
    .ready_i(1'b1)
  );
    

endmodule
