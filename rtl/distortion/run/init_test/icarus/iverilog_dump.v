module iverilog_dump();
initial begin
    $dumpfile("distortion.fst");
    $dumpvars(0, distortion);
end
endmodule
