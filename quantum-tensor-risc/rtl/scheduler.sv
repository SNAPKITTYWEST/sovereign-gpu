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
// Sovereign GPU — QRNG-Driven Scheduler
// Priority-based task scheduling with QRNG entropy
// ============================================================================

module scheduler #(
    parameter SM_COUNT = 4,
    parameter MAX_PRIO = 7
)(
    input  logic        clk,
    input  logic        rst_n,
    input  logic [SM_COUNT-1:0] sm_halted,
    input  logic [63:0] qrng_seed,
    output logic [$clog2(SM_COUNT)-1:0] sm_id,
    output logic        valid
);

    typedef enum logic [2:0] {
        ACT_RUN,
        ACT_SPAWN,
        ACT_JOIN,
        ACT_BARRIER,
        ACT_SYNC,
        ACT_NOOP
    } action_t;

    action_t action;
    logic [$clog2(SM_COUNT)-1:0] next_sm;

    // Pseudo-random selection from QRNG seed
    logic [63:0] lfsr;
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            lfsr <= qrng_seed;
        else
            lfsr <= {lfsr[62:0], lfsr[63] ^ lfsr[62]};
    end

    // Find first non-halted SM
    always_comb begin
        valid = 1'b0;
        next_sm = 0;
        action = ACT_NOOP;

        for (int i = 0; i < SM_COUNT; i++) begin
            if (!sm_halted[i]) begin
                valid = 1'b1;
                next_sm = i[$clog2(SM_COUNT)-1:0];
                action = ACT_RUN;
                break;
            end
        end

        // Apply QRNG for scheduling decision
        if (valid) begin
            case (lfsr[1:0])
                2'b00: action = ACT_RUN;
                2'b01: action = ACT_SPAWN;
                2'b10: action = ACT_SYNC;
                2'b11: action = ACT_NOOP;
            endcase
        end
    end

    assign sm_id = next_sm;

endmodule
