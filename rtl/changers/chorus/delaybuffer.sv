module delaybuffer
  #(parameter [31:0] width_p = 8
   ,parameter [31:0] delay_p = 8
   )
  (input [0:0] clk_i
  ,input [0:0] reset_i

  ,input [width_p - 1:0] data_i
  ,input logic [0:0] valid_i
  ,output [0:0] ready_o

  ,output logic [0:0] valid_o
  ,output [width_p - 1:0] data_o
  ,input [0:0] ready_i
  );
    

    localparam delay_log2_p = $clog2(delay_p + 1);

    logic [delay_log2_p - 1 : 0] addr_n, addr_r;

    assign ready_o = ~valid_o | ready_i;

    always_ff @(posedge clk_i) begin
        if (reset_i) begin
            valid_o <= 1'b0;
            addr_r <= '0;
        end else begin
            if (ready_o)
                valid_o <= valid_i & ready_o;
            addr_r <= addr_n;
        end    
    end

    /* verilator lint_off WIDTHEXPAND */
    always_comb begin
        addr_n = addr_r;
        if (valid_i & ready_o)
            if (addr_r == delay_p - 1)
                addr_n = '0;
            else
                addr_n = addr_r + 1;
    end
    /* verilator lint_off WIDTHEXPAND */

    ram_1r1w_sync
        #(.width_p(width_p)
         ,.depth_p(delay_p))
    ram_inst
        (.clk_i(clk_i)
        ,.reset_i(reset_i)
        ,.wr_valid_i(valid_i & ready_o)
        ,.wr_data_i(data_i)
        ,.wr_addr_i(addr_r)
        ,.rd_valid_i(valid_i & ready_o)
        ,.rd_addr_i(addr_r)
        ,.rd_data_o(data_o));

endmodule
