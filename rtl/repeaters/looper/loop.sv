module loop #(
  parameter int width = 24
 ) (
  input logic clk,
  input logic rst,

  input logic signed [width-1:0] in_signal,
  output logic signed [width-1:0] out_signal, 

  input logic loop_en
);

  // when button pressed, "record" the input until button pressed again 
  // when button pressed again, output is the recorded signal layered over the input signal

  // meed a circualr ram for storing the recorded signal 
  // out = in + ram[ptr]

  // fsm: 
  // idle - button pressed -> record
  // record - button pressed -> playback 
  // playback - button pressed -> idle


  typedef enum logic [1:0] {
    IDLE,
    RECORD,
    PLAYBACK
  } state_t;

  state_t state, next_state;

  always_comb begin 
    next_state = state;

    case(state) 
      IDLE: begin 
        if(loop_en) begin 
          next_state = RECORD;
        end else begin 
          next_state = IDLE;
        end
      end
      RECORD: begin 
        // record signal into ram 



        if(loop_en) begin 
          next_state = PLAYBACK;
        end else begin
          next_state = RECORD;
        end
      end
      PLAYBACK: begin 
        // stop recording, layer ram signal over input to the output 
        // out_signal = in_signal + ram[ptr]
        

        if(loop_en) begin 
          next_state = IDLE;
          // clear signal from ram, stop layering

        end else begin 
          next_state = PLAYBACK;
        end
      end
      default: next_state = IDLE;
    endcase 
  end


  always_ff @(posedge clk) begin 
    if(rst) begin 
      state <= IDLE;
    end else begin 
      state <= next_state;
    end
  end

endmodule
