// ============================================================================
// Sovereign GPU — QRNG Interface
// Domain-separated quantum seed derivation
// ============================================================================

module qrng_interface (
    input  logic        clk,
    input  logic        rst_n,
    input  logic [63:0] entropy_in,
    input  logic        entropy_valid,
    output logic        entropy_ready,
    output logic [63:0] seed,
    input  logic        read,
    output logic [63:0] word
);

    localparam DOMAIN    = 64'h5A5A5A5A_5A5A5A5A;
    localparam PROC_ID   = 64'h01;
    localparam PROG_HASH = 64'hDEADBEEF_DEADBEEF;

    logic [63:0] entropy_buf;
    logic        buf_valid;

    // Domain-separated seed
    assign seed = entropy_buf + DOMAIN + PROC_ID + PROG_HASH;

    // Fluctuation sample (LCG)
    logic [63:0] lcg_state;
    logic [63:0] lcg_next;

    assign lcg_next = lcg_state * 64'd6364136223846793005 + 64'd1442695040888963407;
    assign word = lcg_state;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            entropy_buf <= 64'b0;
            buf_valid <= 1'b0;
            lcg_state <= 64'b0;
            entropy_ready <= 1'b1;
        end else begin
            if (entropy_valid && entropy_ready) begin
                entropy_buf <= entropy_in;
                buf_valid <= 1'b1;
                entropy_ready <= 1'b0;
            end

            if (read && buf_valid) begin
                lcg_state <= lcg_next;
                buf_valid <= 1'b0;
                entropy_ready <= 1'b1;
            end
        end
    end

endmodule
