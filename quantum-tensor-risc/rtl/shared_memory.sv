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
// Sovereign GPU — Shared Memory Controller
// 64KB shared memory with bank conflict avoidance
// ============================================================================

module shared_memory #(
    parameter DEPTH = 16384,
    parameter BANKS = 4
)(
    input  logic        clk,
    input  logic        rst_n,

    // Port A
    input  logic [31:0] addr_a,
    input  logic [31:0] wdata_a,
    output logic [31:0] rdata_a,
    input  logic        we_a,
    input  logic        re_a,

    // Port B
    input  logic [31:0] addr_b,
    input  logic [31:0] wdata_b,
    output logic [31:0] rdata_b,
    input  logic        we_b,
    input  logic        re_b
);

    logic [31:0] mem [0:DEPTH-1];

    // Bank assignment
    logic [1:0] bank_a, bank_b;
    assign bank_a = addr_a[1:0];
    assign bank_b = addr_b[1:0];

    always_ff @(posedge clk) begin
        if (we_a)
            mem[addr_a] <= wdata_a;
        if (we_b)
            mem[addr_b] <= wdata_b;
    end

    assign rdata_a = mem[addr_a];
    assign rdata_b = mem[addr_b];

endmodule
