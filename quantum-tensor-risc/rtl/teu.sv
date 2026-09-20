// Copyright © 2026 SnapKitty Collective and contributors.
//
// This file is part of a work licensed under the
// SnapKitty Strong Network Copyleft License Version 1.0 (SSNCL-1.0).
//
// You may use, study, modify, copy, and redistribute this work
// only under the terms of SSNCL-1.0.
//
// A copy of SSNCL-1.0 must accompany this work.

// ============================================================================
// Sovereign GPU — Tensor Execution Unit (TEU)
// Matrix multiply tile unit with accumulator
// ============================================================================

module teu #(
    parameter TILE_SZ = 64,
    parameter DATA_WIDTH = 32
)(
    input  logic        clk,
    input  logic        rst_n,
    input  logic        start,
    input  logic [DATA_WIDTH-1:0] tile_a [TILE_SZ-1:0][TILE_SZ-1:0],
    input  logic [DATA_WIDTH-1:0] tile_b [TILE_SZ-1:0][TILE_SZ-1:0],
    output logic [DATA_WIDTH-1:0] tile_c [TILE_SZ-1:0][TILE_SZ-1:0],
    output logic        done,
    output logic [$clog2(TILE_SZ):0] progress
);

    logic [$clog2(TILE_SZ):0] row_idx, col_idx;
    logic [DATA_WIDTH*2-1:0] accumulator;

    // State machine
    typedef enum logic [1:0] {
        TEU_IDLE,
        TEU_COMPUTE,
        TEU_DONE
    } teu_state_t;

    teu_state_t teu_state;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            teu_state <= TEU_IDLE;
            row_idx <= 0;
            col_idx <= 0;
            accumulator <= 0;
            done <= 1'b0;
            progress <= 0;
        end else begin
            case (teu_state)
                TEU_IDLE: begin
                    if (start) begin
                        teu_state <= TEU_COMPUTE;
                        row_idx <= 0;
                        col_idx <= 0;
                        done <= 1'b0;
                    end
                end

                TEU_COMPUTE: begin
                    accumulator <= accumulator + tile_a[row_idx][col_idx] * tile_b[col_idx][row_idx];
                    col_idx <= col_idx + 1;
                    if (col_idx == TILE_SZ - 1) begin
                        tile_c[row_idx][row_idx] <= accumulator[DATA_WIDTH-1:0];
                        accumulator <= 0;
                        col_idx <= 0;
                        row_idx <= row_idx + 1;
                        progress <= progress + 1;
                        if (row_idx == TILE_SZ - 1) begin
                            teu_state <= TEU_DONE;
                            done <= 1'b1;
                        end
                    end
                end

                TEU_DONE: begin
                    teu_state <= TEU_IDLE;
                    done <= 1'b0;
                    progress <= 0;
                end
            endcase
        end
    end

endmodule
