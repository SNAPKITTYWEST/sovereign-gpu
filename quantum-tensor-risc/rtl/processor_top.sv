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
// Sovereign GPU — Processor Top-Level Module
// 32-bit fixed-width RISC with QRNG scheduler + Tensor Execution Units
// Sovereign Source License v1.0 + BSL-1.1 + AGPL-3.0
// Copyright (C) 2026 Ahmad Ali Parr / SNAPKITTYWEST
// ============================================================================

module processor_top #(
    parameter SM_COUNT = 4,
    parameter TILE_SZ = 64,
    parameter MATRIX_DIM = 256
)(
    input  logic        clk,
    input  logic        rst_n,
    input  logic        start,
    input  logic [63:0] entropy_in,
    input  logic        entropy_valid,
    output logic        entropy_ready,

    // Program memory
    output logic [31:0] pmem_addr,
    input  logic [31:0] pmem_rdata,

    // Shared memory
    output logic [31:0] smem_addr,
    output logic [31:0] smem_wdata,
    input  logic [31:0] smem_rdata,
    output logic        smem_we,
    output logic        smem_re,

    // Done
    output logic        done,
    output logic [$clog2(SM_COUNT)-1:0] active_sms
);

    logic [$clog2(SM_COUNT)-1:0] sm_idx;
    logic [SM_COUNT-1:0] sm_halted;
    logic [SM_COUNT-1:0] sm_active;

    // QRNG interface
    logic [63:0] qrng_seed;
    logic [63:0] qrng_word;
    logic        qrng_read;

    // Scheduler outputs
    logic [$clog2(SM_COUNT)-1:0] sched_sm_id;
    logic        sched_valid;
    logic [2:0]  sched_action;

    // SM state
    logic [31:0] sm_pc       [SM_COUNT-1:0];
    logic [31:0] sm_regs     [SM_COUNT-1:0][31:0];
    logic        sm_halted_i [SM_COUNT-1:0];
    logic        sm_active_i [SM_COUNT-1:0];

    // Master FSM
    typedef enum logic [2:0] {
        S_IDLE,
        S_FETCH_QRNG,
        S_SCHED,
        S_EXEC,
        S_BARRIER,
        S_DONE
    } state_t;

    state_t state, state_next;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            state <= S_IDLE;
        else
            state <= state_next;
    end

    always_comb begin
        state_next = state;
        done = 1'b0;
        sched_valid = 1'b0;
        qrng_read = 1'b0;

        case (state)
            S_IDLE: begin
                if (start)
                    state_next = S_FETCH_QRNG;
            end

            S_FETCH_QRNG: begin
                if (entropy_valid) begin
                    qrng_read = 1'b1;
                    state_next = S_SCHED;
                end
            end

            S_SCHED: begin
                sched_valid = 1'b1;
                if (sm_halted[sched_sm_id])
                    state_next = S_DONE;
                else
                    state_next = S_EXEC;
            end

            S_EXEC: begin
                if (sm_halted[sched_sm_id])
                    state_next = S_SCHED;
                else
                    state_next = S_EXEC;
            end

            S_DONE: begin
                done = 1'b1;
                if (sm_halted == {SM_COUNT{1'b1}})
                    state_next = S_IDLE;
            end

            default: state_next = S_IDLE;
        endcase
    end

    // Active SM count
    logic [$clog2(SM_COUNT)-1:0] active_count;
    always_comb begin
        active_count = 0;
        for (int i = 0; i < SM_COUNT; i++) begin
            if (sm_active_i[i] && !sm_halted_i[i])
                active_count = active_count + 1;
        end
    end
    assign active_sms = active_count;

    // SM instantiations
    generate
        for (genvar i = 0; i < SM_COUNT; i++) begin : gen_sm
            sm #(
                .SM_ID(i),
                .TILE_SZ(TILE_SZ)
            ) u_sm (
                .clk        (clk),
                .rst_n      (rst_n),
                .enable     (sched_valid && sched_sm_id == i[$clog2(SM_COUNT)-1:0]),
                .pc         (sm_pc[i]),
                .regs       (sm_regs[i]),
                .halted     (sm_halted_i[i]),
                .active     (sm_active_i[i]),
                .pmem_addr  (pmem_addr),
                .pmem_rdata (pmem_rdata),
                .smem_addr  (smem_addr),
                .smem_wdata (smem_wdata),
                .smem_rdata (smem_rdata),
                .smem_we    (smem_we),
                .smem_re    (smem_re)
            );
        end
    endgenerate

    assign sm_halted = sm_halted_i;
    assign sm_active = sm_active_i;

    // QRNG scheduler
    scheduler #(.SM_COUNT(SM_COUNT)) u_sched (
        .clk        (clk),
        .rst_n      (rst_n),
        .sm_halted  (sm_halted),
        .qrng_seed  (qrng_seed),
        .sm_id      (sched_sm_id),
        .valid      (sched_valid)
    );

    qrng_interface u_qrng (
        .clk        (clk),
        .rst_n      (rst_n),
        .entropy_in (entropy_in),
        .entropy_valid (entropy_valid),
        .entropy_ready (entropy_ready),
        .seed       (qrng_seed),
        .read       (qrng_read),
        .word       (qrng_word)
    );

endmodule
