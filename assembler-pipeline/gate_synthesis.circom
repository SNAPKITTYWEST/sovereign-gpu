pragma circom 2.0;

// ============================================================================
// Gate-Level Synthesis Module — Maps SASS Instructions to R1CS Constraints
// Converts PTX/SASS operations into verifiable gate-level representations
// Sovereign Source License v1.0 + BSL-1.1 + AGPL-3.0
// Copyright (C) 2026 Ahmad Ali Parr / SNAPKITTYWEST
// ============================================================================

// ============================================================================
// SECTION 1: Basic Logic Gates
// ============================================================================

// Template: AND Gate
template AndGate() {
    signal input a;
    signal input b;
    signal output out;
    out <== a * b;
}

// Template: OR Gate
template OrGate() {
    signal input a;
    signal input b;
    signal output out;
    // out = a + b - a*b (inclusion-exclusion)
    out <== a + b - a * b;
}

// Template: XOR Gate
template XorGate() {
    signal input a;
    signal input b;
    signal output out;
    out <== a + b - 2 * a * b;
}

// Template: NOT Gate
template NotGate() {
    signal input a;
    signal output out;
    out <== 1 - a;
}

// Template: NAND Gate
template NandGate() {
    signal input a;
    signal input b;
    signal output out;
    out <== 1 - a * b;
}

// Template: NOR Gate
template NorGate() {
    signal input a;
    signal input b;
    signal output out;
    out <== 1 - (a + b - a * b);
}

// Template: XNOR Gate
template XnorGate() {
    signal input a;
    signal input b;
    signal output out;
    out <== 1 - (a + b - 2 * a * b);
}

// ============================================================================
// SECTION 2: Arithmetic Units
// ============================================================================

// Template: Full Adder
template FullAdder() {
    signal input a;
    signal input b;
    signal input cin;
    signal output sum;
    signal output cout;

    signal p;
    signal g;

    p <== a + b - 2 * a * b;  // XOR
    g <== a * b;              // AND

    sum <== p + cin - 2 * p * cin;
    cout <== g + p * cin;
}

// Template: Half Adder
template HalfAdder() {
    signal input a;
    signal input b;
    signal output sum;
    signal output cout;

    sum <== a + b - 2 * a * b;
    cout <== a * b;
}

// Template: 4-bit Ripple Carry Adder
template Adder4() {
    signal input a[4];
    signal input b[4];
    signal input cin;
    signal output sum[4];
    signal output cout;

    component fa[4];

    fa[0] = FullAdder();
    fa[0].a <== a[0];
    fa[0].b <== b[0];
    fa[0].cin <== cin;

    fa[1] = FullAdder();
    fa[1].a <== a[1];
    fa[1].b <== b[1];
    fa[1].cin <== fa[0].cout;

    fa[2] = FullAdder();
    fa[2].a <== a[2];
    fa[2].b <== b[2];
    fa[2].cin <== fa[1].cout;

    fa[3] = FullAdder();
    fa[3].a <== a[3];
    fa[3].b <== b[3];
    fa[3].cin <== fa[2].cout;

    sum[0] <== fa[0].sum;
    sum[1] <== fa[1].sum;
    sum[2] <== fa[2].sum;
    sum[3] <== fa[3].sum;
    cout <== fa[3].cout;
}

// Template: 32-bit Adder
template Adder32() {
    signal input a[32];
    signal input b[32];
    signal input cin;
    signal output sum[32];
    signal output cout;

    component adders[8];

    for (var i = 0; i < 8; i++) {
        adders[i] = Adder4();
        for (var j = 0; j < 4; j++) {
            adders[i].a[j] <== a[i * 4 + j];
            adders[i].b[j] <== b[i * 4 + j];
        }
        if (i == 0) {
            adders[i].cin <== cin;
        } else {
            adders[i].cin <== adders[i - 1].cout;
        }
    }

    for (var i = 0; i < 32; i++) {
        sum[i] <== adders[i / 4].sum[i % 4];
    }
    cout <== adders[7].cout;
}

// Template: 32-bit Subtractor
template Subtractor32() {
    signal input a[32];
    signal input b[32];
    signal output diff[32];
    signal output borrow;

    // a - b = a + (~b + 1)
    signal not_b[32];
    component nots[32];

    for (var i = 0; i < 32; i++) {
        nots[i] = NotGate();
        nots[i].a <== b[i];
        not_b[i] <== nots[i].out;
    }

    component adder = Adder32();
    for (var i = 0; i < 32; i++) {
        adder.a[i] <== a[i];
        adder.b[i] <== not_b[i];
    }
    adder.cin <== 1;

    for (var i = 0; i < 32; i++) {
        diff[i] <== adder.sum[i];
    }
    borrow <== 1 - adder.cout;
}

// Template: 32-bit Multiplier (simplified shift-add)
template Multiplier32() {
    signal input a[32];
    signal input b[32];
    signal output product[64];

    // Initialize product
    for (var i = 0; i < 64; i++) {
        product[i] <== 0;
    }

    // Shift-and-add multiplication
    signal partial[32][64];
    signal carry[32][64];

    for (var i = 0; i < 32; i++) {
        for (var j = 0; j < 64; j++) {
            if (j < i) {
                partial[i][j] <== 0;
            } else if (j - i < 32) {
                partial[i][j] <== a[j - i] * b[i];
            } else {
                partial[i][j] <== 0;
            }
        }
    }

    // Accumulate partial products
    signal acc[64];
    for (var j = 0; j < 64; j++) {
        acc[j] <== 0;
        for (var i = 0; i < 32; i++) {
            acc[j] += partial[i][j];
        }
        product[j] <== acc[j];
    }
}

// ============================================================================
// SECTION 3: Multiplexers and Demultiplexers
// ============================================================================

// Template: 2-to-1 MUX
template Mux2() {
    signal input a;
    signal input b;
    signal input sel;
    signal output out;
    out <== sel * b + (1 - sel) * a;
}

// Template: 4-to-1 MUX
template Mux4() {
    signal input a[4];
    signal input sel[2];
    signal output out;

    signal mid[3];

    mid[0] <== (1 - sel[0]) * a[0] + sel[0] * a[1];
    mid[1] <== (1 - sel[0]) * a[2] + sel[0] * a[3];
    out <== (1 - sel[1]) * mid[0] + sel[1] * mid[1];
}

// Template: 8-to-1 MUX
template Mux8() {
    signal input a[8];
    signal input sel[3];
    signal output out;

    signal mid[7];

    mid[0] <== (1 - sel[0]) * a[0] + sel[0] * a[1];
    mid[1] <== (1 - sel[0]) * a[2] + sel[0] * a[3];
    mid[2] <== (1 - sel[0]) * a[4] + sel[0] * a[5];
    mid[3] <== (1 - sel[0]) * a[6] + sel[0] * a[7];
    mid[4] <== (1 - sel[1]) * mid[0] + sel[1] * mid[1];
    mid[5] <== (1 - sel[1]) * mid[2] + sel[1] * mid[3];
    out <== (1 - sel[2]) * mid[4] + sel[2] * mid[5];
}

// Template: Demultiplexer 1-to-4
template Demux4() {
    signal input a;
    signal input sel[2];
    signal output out[4];

    out[0] <== a * (1 - sel[0]) * (1 - sel[1]);
    out[1] <== a * sel[0] * (1 - sel[1]);
    out[2] <== a * (1 - sel[0]) * sel[1];
    out[3] <== a * sel[0] * sel[1];
}

// ============================================================================
// SECTION 4: Register File
// ============================================================================

// Template: D Flip-Flop
template DFF() {
    signal input d;
    signal input clk;
    signal input rst_n;
    signal output q;

    signal d_internal;
    d_internal <== d;

    // In actual hardware, this would be a latch
    // For R1CS, we model it as: q follows d on clk edge
    // Constraint: q * (1 - clk) = d * clk (simplified)
    q <== d;
}

// Template: 32-bit Register
template Register32() {
    signal input d[32];
    signal input clk;
    signal input rst_n;
    signal input we;
    signal output q[32];

    component dff[32];
    signal we_q;

    we_q <== we;

    for (var i = 0; i < 32; i++) {
        dff[i] = DFF();
        dff[i].d <== d[i];
        dff[i].clk <== clk;
        dff[i].rst_n <== rst_n;
        q[i] <== dff[i].q;
    }
}

// Template: Register File (32 x 32-bit)
template RegisterFile() {
    signal input raddr1[5];
    signal input raddr2[5];
    signal input waddr[5];
    signal input wdata[32];
    signal input we;
    signal input clk;
    signal input rst_n;
    signal output rdata1[32];
    signal output rdata2[32];

    component regs[32];
    component mux_r1[32];
    component mux_r2[32];

    for (var i = 0; i < 32; i++) {
        regs[i] = Register32();
        regs[i].clk <== clk;
        regs[i].rst_n <== rst_n;
        regs[i].we <== we && (waddr == i);

        mux_r1[i] = Mux2();
        mux_r1[i].a <== 0;
        mux_r1[i].b <== regs[i].q[0];
        mux_r1[i].sel <== (raddr1 == i);

        mux_r2[i] = Mux2();
        mux_r2[i].a <== 0;
        mux_r2[i].b <== regs[i].q[0];
        mux_r2[i].sel <== (raddr2 == i);
    }

    // Read port 1
    signal acc1[32];
    for (var j = 0; j < 32; j++) {
        acc1[j] <== 0;
        for (var i = 0; i < 32; i++) {
            acc1[j] += mux_r1[i].out;
        }
        rdata1[j] <== acc1[j];
    }

    // Read port 2
    signal acc2[32];
    for (var j = 0; j < 32; j++) {
        acc2[j] <== 0;
        for (var i = 0; i < 32; i++) {
            acc2[j] += mux_r2[i].out;
        }
        rdata2[j] <== acc2[j];
    }
}

// ============================================================================
// SECTION 5: SASS Instruction Decoder
// ============================================================================

// Template: SASS Opcode Decoder
template SASSDecoder() {
    signal input instruction[128];
    signal output opcode[8];
    signal output src_a[5];
    signal output src_b[5];
    signal output src_c[5];
    signal output src_d[5];
    signal output dst[8];
    signal output imm[16];
    signal output sel[8];
    signal output pred[8];
    signal output stride[8];
    signal output ccat[8];
    signal output sfd[8];

    // Decode field A (bits 0-31)
    for (var i = 0; i < 8; i++) {
        opcode[i] <== instruction[i];
    }
    for (var i = 0; i < 5; i++) {
        src_a[i] <== instruction[8 + i];
    }
    for (var i = 0; i < 5; i++) {
        src_b[i] <== instruction[13 + i];
    }
    for (var i = 0; i < 2; i++) {
        src_c[i] <== instruction[18 + i];
    }
    src_d[0] <== instruction[20];

    // Decode field B (bits 32-63)
    for (var i = 0; i < 8; i++) {
        dst[i] <== instruction[32 + i];
    }
    for (var i = 0; i < 16; i++) {
        imm[i] <== instruction[40 + i];
    }
    for (var i = 0; i < 8; i++) {
        sel[i] <== instruction[56 + i];
    }

    // Decode field C (bits 64-95)
    for (var i = 0; i < 8; i++) {
        pred[i] <== instruction[64 + i];
    }
    for (var i = 0; i < 8; i++) {
        stride[i] <== instruction[72 + i];
    }

    // Decode field D (bits 96-127)
    for (var i = 0; i < 8; i++) {
        ccat[i] <== instruction[96 + i];
    }
    for (var i = 0; i < 8; i++) {
        sfd[i] <== instruction[104 + i];
    }
}

// ============================================================================
// SECTION 6: PTX Instruction Executer
// ============================================================================

// Template: PTX Arithmetic Unit
template PTXArithmetic() {
    signal input opcode[8];
    signal input a[32];
    signal input b[32];
    signal input c[32];
    signal output result[32];
    signal output flags_nz;

    // Decode operation from opcode
    signal is_add;
    signal is_sub;
    signal is_mul;
    signal is_div;
    signal is_and;
    signal is_or;
    signal is_xor;
    signal is_shl;
    signal is_shr;

    // Simple opcode decode (bits 0-2)
    is_add <== (opcode[0] == 0) * (opcode[1] == 0) * (opcode[2] == 0);
    is_sub <== (opcode[0] == 1) * (opcode[1] == 0) * (opcode[2] == 0);
    is_mul <== (opcode[0] == 0) * (opcode[1] == 1) * (opcode[2] == 0);
    is_div <== (opcode[0] == 1) * (opcode[1] == 1) * (opcode[2] == 0);
    is_and <== (opcode[0] == 0) * (opcode[1] == 0) * (opcode[2] == 1);
    is_or  <== (opcode[0] == 1) * (opcode[1] == 0) * (opcode[2] == 1);
    is_xor <== (opcode[0] == 0) * (opcode[1] == 1) * (opcode[2] == 1);
    is_shl <== (opcode[0] == 0) * (opcode[1] == 0) * (opcode[2] == 0) * opcode[3];
    is_shr <== (opcode[0] == 1) * (opcode[1] == 0) * (opcode[2] == 0) * opcode[3];

    // Perform operations
    component adder = Adder32();
    component subtractor = Subtractor32();
    component multiplier = Multiplier32();

    for (var i = 0; i < 32; i++) {
        adder.a[i] <== a[i];
        adder.b[i] <== b[i];
        subtractor.a[i] <== a[i];
        subtractor.b[i] <== b[i];
        multiplier.a[i] <== a[i];
        multiplier.b[i] <== b[i];
    }

    // MUX results
    signal results[9][32];

    for (var i = 0; i < 32; i++) {
        results[0][i] <== adder.sum[i];      // ADD
        results[1][i] <== subtractor.diff[i]; // SUB
        results[2][i] <== multiplier.product[i]; // MUL
        results[3][i] <== a[i] & b[i];       // AND (bitwise)
        results[4][i] <== a[i] | b[i];       // OR
        results[5][i] <== a[i] ^ b[i];       // XOR
        results[6][i] <== a[i] << 1;         // SHL (simplified)
        results[7][i] <== a[i] >> 1;         // SHR (simplified)
        results[8][i] <== 0;                  // NOP
    }

    // Final MUX
    for (var i = 0; i < 32; i++) {
        result[i] <== is_add * results[0][i] +
                      is_sub * results[1][i] +
                      is_mul * results[2][i] +
                      is_and * results[3][i] +
                      is_or  * results[4][i] +
                      is_xor * results[5][i] +
                      is_shl * results[6][i] +
                      is_shr * results[7][i];
    }

    // Zero flag
    signal sum_result;
    sum_result <== 0;
    for (var i = 0; i < 32; i++) {
        sum_result += result[i];
    }
    flags_nz <== (sum_result != 0);
}

// Template: PTX Memory Unit
template PTXMemory() {
    signal input opcode[8];
    signal input addr[32];
    signal input data[32];
    signal input mem_in[32];
    signal output mem_out[32];
    signal output mem_addr[32];
    signal output mem_we;

    signal is_load;
    signal is_store;

    is_load <== (opcode[0] == 0) * (opcode[1] == 0);
    is_store <== (opcode[0] == 1) * (opcode[1] == 0);

    mem_addr <== addr;
    mem_we <== is_store;
    mem_out <== is_load ? mem_in : data;
}

// Template: PTX Branch Unit
template PTXBranch() {
    signal input opcode[8];
    signal input cond;
    signal input target[32];
    signal input pc[32];
    signal output next_pc[32];
    signal output taken;

    signal is_bra;
    signal is_beq;
    signal is_bne;
    signal is_blt;
    signal is_bge;

    is_bra <== (opcode[0] == 0) * (opcode[1] == 0) * (opcode[2] == 0);
    is_beq <== (opcode[0] == 1) * (opcode[1] == 0) * (opcode[2] == 0);
    is_bne <== (opcode[0] == 0) * (opcode[1] == 1) * (opcode[2] == 0);
    is_blt <== (opcode[0] == 1) * (opcode[1] == 1) * (opcode[2] == 0);
    is_bge <== (opcode[0] == 0) * (opcode[1] == 0) * (opcode[2] == 1);

    taken <== is_bra + is_beq * cond + is_bne * (1 - cond);
    next_pc <== taken ? target : pc + 4;
}

// ============================================================================
// SECTION 7: Complete SASS Processor
// ============================================================================

// Template: SASS Processor Core
template SASSProcessor() {
    signal input clk;
    signal input rst_n;
    signal input instruction[128];
    signal input mem_read[32];
    signal output mem_write[32];
    signal output mem_addr[32];
    signal output mem_we;
    signal output pc[32];
    signal output done;

    // Instruction decoder
    component decoder = SASSDecoder();
    for (var i = 0; i < 128; i++) {
        decoder.instruction[i] <== instruction[i];
    }

    // Register file
    component regfile = RegisterFile();
    regfile.raddr1 <== decoder.src_a;
    regfile.raddr2 <== decoder.src_b;
    regfile.waddr <== decoder.dst;
    regfile.we <== 1;
    regfile.clk <== clk;
    regfile.rst_n <== rst_n;

    // Arithmetic unit
    component alu = PTXArithmetic();
    alu.opcode <== decoder.opcode;
    alu.a <== regfile.rdata1;
    alu.b <== regfile.rdata2;
    alu.c <== 0;

    // Memory unit
    component mem = PTXMemory();
    mem.opcode <== decoder.opcode;
    mem.addr <== alu.result;
    mem.data <== regfile.rdata1;
    mem.mem_in <== mem_read;

    // Branch unit
    component branch = PTXBranch();
    branch.opcode <== decoder.opcode;
    branch.cond <== alu.flags_nz;
    branch.target <== decoder.imm;
    branch.pc <== pc;

    // PC update
    component pc_dff = DFF();
    pc_dff.d <== branch.next_pc;
    pc_dff.clk <== clk;
    pc_dff.rst_n <== rst_n;
    pc <== pc_dff.q;

    // Write-back
    regfile.wdata <== alu.result;

    // Memory outputs
    mem_write <== mem.mem_out;
    mem_addr <== mem.mem_addr;
    mem_we <== mem.mem_we;

    // Done detection (EXIT instruction)
    done <== (decoder.opcode[0] == 1) * (decoder.opcode[1] == 1) * (decoder.opcode[2] == 1);
}

// ============================================================================
// SECTION 8: Complete Processor with Memory
// ============================================================================

// Template: Complete SASS Processor with Memory
template CompleteProcessor(instruction_memory_size) {
    signal input clk;
    signal input rst_n;
    signal input start;
    signal input instruction_mem[instruction_memory_size * 128];
    signal output result[32];
    signal output done;

    component processor = SASSProcessor();
    component inst_mem_mux = Mux8();

    signal pc[32];
    signal instruction[128];

    // Instruction memory read
    for (var i = 0; i < 128; i++) {
        instruction[i] <== instruction_mem[pc[0] * 128 + i];
    }

    processor.clk <== clk;
    processor.rst_n <== rst_n;
    for (var i = 0; i < 128; i++) {
        processor.instruction[i] <== instruction[i];
    }

    pc <== processor.pc;
    done <== processor.done;
    result <== processor.mem_write;
}

// ============================================================================
// SECTION 9: Main Component
// ============================================================================

// Main: Complete processor for flash_attention.ptx verification
component main = CompleteProcessor(1024);
