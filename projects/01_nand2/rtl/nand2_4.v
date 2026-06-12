module nand2 (
    input  a,
    input  b,
    output y
);
    // Dataflow modeling of a NAND gate
    assign y = ~(a & b);
endmodule
