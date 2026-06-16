module debounce (
    input  clk,
    input  rst_n,
    input  btn_raw,
    output btn_clean,
    output btn_pressed
);
    // --- 1ms tick ---
    reg [15:0] tick_cnt;
    reg        tick;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin tick_cnt <= 0; tick <= 0; end
        else if (tick_cnt == 16'd49_999) begin tick_cnt <= 0; tick <= 1; end
        else begin tick_cnt <= tick_cnt + 1; tick <= 0; end
    end

    // --- 16-sample shift register ---
    reg [15:0] shift_reg;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) shift_reg <= 16'hFFFF;
        else if (tick) shift_reg <= {shift_reg[14:0], btn_raw};
    end

    // --- Output: stable when all 16 agree ---
    wire stable = &shift_reg;
    assign btn_clean = stable;

    // --- Edge detect: one pulse on press ---
    reg prev;
    always @(posedge clk) prev <= stable;
    assign btn_pressed = ~stable & prev;

endmodule	