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
// Sovereign GPU — Streaming Multiprocessor
// Single SM with 32 registers, local memory, fetch/decode/execute
// ============================================================================

module sm #(
    parameter SM_ID = 0,
    parameter TILE_SZ = 64
)(
    input  logic        clk,
    input  logic        rst_n,
    input  logic        enable,

    output logic [31:0] pc,
    output logic [31:0] regs [31:0],
    output logic        halted,
    output logic        active,

    output logic [31:0] pmem_addr,
    input  logic [31:0] pmem_rdata,

    output logic [31:0] smem_addr,
    output logic [31:0] smem_wdata,
    input  logic [31:0] smem_rdata,
    output logic        smem_we,
    output logic        smem_re
);

    localparam HALT_ADDR = 32'hFFFFFFFF;

    // State
    typedef enum logic [1:0] {
        SM_IDLE,
        SM_FETCH,
        SM_DECODE,
        SM_EXECUTE
    } sm_state_t;

    sm_state_t sm_state;

    logic [31:0] pc_next;
    logic [31:0] regs_next [31:0];

    // Decode fields
    logic [6:0]  opcode;
    logic [4:0]  rd, rs1, rs2;
    logic [2:0]  funct3;
    logic [6:0]  funct7;
    logic [31:0] imm_i, imm_s, imm_b, imm_j;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            pc <= 32'b0;
            halted <= 1'b0;
            active <= 1'b0;
            sm_state <= SM_IDLE;
            for (int i = 0; i < 31; i++)
                regs[i] <= 32'b0;
            regs[31] <= 32'b0;
        end else if (enable && !halted) begin
            for (int i = 0; i < 32; i++)
                regs[i] <= regs_next[i];
            pc <= pc_next;
            sm_state <= sm_state;
        end
    end

    // Decode
    assign opcode = pmem_rdata[6:0];
    assign rd     = pmem_rdata[11:7];
    assign funct3 = pmem_rdata[14:12];
    assign rs1    = pmem_rdata[19:15];
    assign rs2    = pmem_rdata[24:20];
    assign funct7 = pmem_rdata[31:25];

    assign imm_i = {{20{pmem_rdata[31]}}, pmem_rdata[31:20]};
    assign imm_s = {{20{pmem_rdata[31]}}, pmem_rdata[31:25], pmem_rdata[11:7]};
    assign imm_b = {{19{pmem_rdata[31]}}, pmem_rdata[31], pmem_rdata[7],
                     pmem_rdata[30:25], pmem_rdata[11:8], 1'b0};
    assign imm_j = {{11{pmem_rdata[31]}}, pmem_rdata[31], pmem_rdata[19:12],
                     pmem_rdata[20], pmem_rdata[30:21], 1'b0};

    // Execute
    always_comb begin
        pc_next = pc + 4;
        halted = halted;
        active = active;

        for (int i = 0; i < 32; i++)
            regs_next[i] = regs[i];

        pmem_addr = pc;
        smem_we = 1'b0;
        smem_re = 1'b0;
        smem_addr = 32'b0;
        smem_wdata = 32'b0;

        case (opcode)
            7'h00: begin // ADD
                regs_next[rd] = regs[rs1] + regs[rs2];
            end
            7'h01: begin // SUB
                regs_next[rd] = regs[rs1] - regs[rs2];
            end
            7'h02: begin // MUL
                regs_next[rd] = regs[rs1] * regs[rs2];
            end
            7'h0C: begin // ADDI
                regs_next[rd] = regs[rs1] + imm_i;
            end
            7'h13: begin // LDI
                regs_next[rd] = imm_i;
            end
            7'h10: begin // LD
                smem_re = 1'b1;
                smem_addr = regs[rs1] + imm_i;
                regs_next[rd] = smem_rdata;
            end
            7'h11: begin // ST
                smem_we = 1'b1;
                smem_addr = regs[rs1] + imm_s;
                smem_wdata = regs[rs2];
            end
            7'h13: begin // JMP
                pc_next = imm_j;
            end
            7'h18: begin // CALL
                regs_next[31] = pc + 4;
                pc_next = imm_j;
            end
            7'h19: begin // RET
                pc_next = regs[31];
            end
            7'h1A: begin // HALT
                halted = 1'b1;
                active = 1'b0;
                pc_next = HALT_ADDR;
            end
            7'h25: begin // SMID
                regs_next[rd] = SM_ID[31:0];
            end
            default: begin
                // NOP
            end
        endcase
    end

endmodule
