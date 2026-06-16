module led_counter (
    input        CLOCK_50,
    input        KEY0,
    input        KEY1,
    output [7:0] LED
);
    wire key0_pressed;

    debounce u_deb (
        .clk         (CLOCK_50),
        .rst_n       (KEY1),
        .btn_raw     (KEY0),
        .btn_clean   (),
        .btn_pressed (key0_pressed)
    );

    reg [7:0] count;
    always @(posedge CLOCK_50 or negedge KEY1) begin
        if (!KEY1)          count <= 8'd0;
        else if (key0_pressed) count <= count + 8'd1;
    end

    assign LED = count;

endmodule
