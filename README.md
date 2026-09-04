# Sovereign GPU — Unified Compute Monorepo

**32-bit RISC + CUDA kernels + x86_64/PTX assemblers + gate-level synthesis + Circom circuits + Quantum Array Processor + ANU QRNG**

Sovereign Source License v1.0 + BSL-1.1 + AGPL-3.0
Copyright (C) 2026 Ahmad Ali Parr / SNAPKITTYWEST

## What's In This Repo

| Component | What It Does | Files |
|-----------|-------------|-------|
| **GEMM+Online Softmax** | Fused attention kernel for Ampere (sm_80+) | `gemm-softmax/` |
| **FRI Butterfly SASS** | Binary-field GF(2^128) FRI evaluator in raw SASS | `fri-butterfly/` |
| **Quantum-Tensor RISC** | Full processor: Why3 formal proofs, RTL, simulator, assembler | `quantum-tensor-risc/` |
| **x86_64 Assembler** | Hand-rolled NASM → machine code | `assembler-pipeline/x86_64_assembler.py` |
| **PTX Assembler** | Hand-rolled PTX → SASS binary | `assembler-pipeline/ptx_assembler.py` |
| **Gate-Level Synthesis** | SASS → Circom R1CS constraints | `assembler-pipeline/gate_synthesis.circom` |
| **Circom Unlambda Verifier** | SKI combinator reduction verification circuit | `circuits/unlambda_verifier.circom` |
| **Quantum Array Processor** | J-style → QNASM → binary → circuit → statevector | `qprocessor/` |
| **DreamcyclesInvariant** | ANU QRNG + invariant preservation + quantum superposition | `dreamcycles-invariant/` |
| **FORGE Suite** | α-parameter tuning, deterministic work-stealing, TVD sweeps | `forge/` |

## Repository Structure

```
sovereign-gpu/
├── README.md
│
├── gemm-softmax/
│   └── src/
│       └── gemm_online_softmax.cu
│
├── fri-butterfly/
│   └── sass/
│       └── fri_butterfly.sass
│
├── quantum-tensor-risc/
│   ├── why3/
│   │   ├── processor.mlw
│   │   ├── isa.mlw
│   │   ├── sm.mlw
│   │   ├── scheduler.mlw
│   │   ├── tensor.mlw
│   │   ├── qrng.mlw
│   │   ├── entropy.mlw
│   │   ├── seed.mlw
│   │   └── proofs.mlw
│   ├── rtl/
│   │   ├── processor_top.sv
│   │   ├── sm.sv
│   │   ├── scheduler.sv
│   │   ├── qrng_interface.sv
│   │   ├── shared_memory.sv
│   │   ├── barrier.sv
│   │   ├── teu.sv
│   │   └── seed_generator.sv
│   ├── simulator/
│   │   ├── Cargo.toml
│   │   └── src/
│   │       ├── main.rs
│   │       ├── isa.rs
│   │       ├── sm.rs
│   │       ├── scheduler.rs
│   │       ├── qrng.rs
│   │       └── engine.rs
│   ├── assembler/
│   │   ├── assembler.py
│   │   └── opcode_table.json
│   ├── tests/
│   │   ├── isa/test_isa.rs
│   │   ├── scheduler/test_scheduler.rs
│   │   ├── tensor/test_tensor.rs
│   │   └── replay/test_replay.rs
│   └── examples/
│       └── vector_add_entropy/program.s
│
├── qprocessor/
│   ├── __init__.py
│   ├── lexer.py
│   ├── parser.py
│   ├── ast.py
│   ├── arrays.py
│   ├── quantum_ir.py
│   ├── qnasm.py
│   ├── assembler.py
│   ├── circuit.py
│   ├── simulator.py
│   ├── compiler.py
│   ├── optimizer.py
│   ├── runtime.py
│   ├── errors.py
│   ├── cli.py
│   ├── tests/
│   │   ├── test_arrays.py
│   │   ├── test_qnasm.py
│   │   ├── test_simulator.py
│   │   └── test_compiler.py
│   └── examples/
│       ├── bell.qnasm
│       ├── ghz.qnasm
│       ├── array.j
│       └── matmul.j
│
├── dreamcycles-invariant/
│   ├── dreamcycles-invariant.cabal
│   ├── README.md
│   ├── src/
│   │   └── DreamcyclesInvariant.hs
│   └── test/
│       └── Test.hs
│
├── circuits/
│   └── unlambda_verifier.circom
│
├── forge/
│   ├── exact_rrd.py
│   ├── anu_qrng.py
│   ├── qasm_gen.py
│   ├── work_steal.py
│   ├── sweep_alpha.py
│   ├── run_parallel.py
│   ├── density_matrix_sweep.py
│   └── README.md
│
└── assembler-pipeline/
    ├── x86_64_assembler.py
    ├── ptx_assembler.py
    ├── gate_synthesis.circom
    ├── run_pipeline.py
    └── output/
        ├── bootstrap.bin          (53 bytes — ELF entry)
        ├── main.bin               (474 bytes — CLI parsing)
        ├── storage.bin            (318 bytes — filesystem ops)
        ├── terminal.bin           (999 bytes — raw TUI)
        ├── flash_attention.sass.bin   (1,178 bytes — SM89 paged attention WMMA)
        └── flash_attention.gates.json (3,431 estimated gates)
```

## Component Details

### 1. GEMM + Online Softmax Kernel

Fused matrix multiply with FlashAttention-style online softmax. Zero intermediate memory writes for attention score matrix.

- **Target**: NVIDIA Ampere (sm_80+)
- **MMA**: `mma.sync m16n8k16` (FP16 input, FP32 accumulate)
- **Tile**: TILE_M=128, TILE_N=64, TILE_K=64
- **Softmax**: Welford online algorithm (running mean/variance)
- **Threads**: 128 per block, 57KB shared memory

### 2. FRI Butterfly SASS

Raw SASS assembly for binary-field FRI butterfly evaluation over GF(2^128). No assembler intermediaries — hand-written machine code.

- **Target**: NVIDIA Ampere (sm_86)
- **GF(2^128)**: Carryless multiply via `XMAD.PSL.CBCC`, XOR via `LOP3.LUT`
- **Iterations**: 8 unrolled butterfly stages
- **Shared memory**: 16KB for twiddle factors
- **Threads**: 256 per block

### 3. Quantum-Tensor RISC Processor

Full processor stack with formal verification at every level.

#### 3a. Why3 Formal Model (9 files, 22 proof obligations)

| Module | Purpose |
|--------|---------|
| `isa.mlw` | 32-bit RISC ISA: 35 instructions (R/I/S/B/J/T types) |
| `sm.mlw` | Streaming Multiprocessor: 32 regs, local memory, step function |
| `scheduler.mlw` | QRNG-driven priority scheduler (0-7) |
| `processor.mlw` | Global state + GLOBAL_STEP integration |
| `tensor.mlw` | Tensor Execution Unit: 64x64 tile multiply |
| `qrng.mlw` | Quantum RNG interface |
| `entropy.mlw` | External entropy buffer with replay axiom |
| `seed.mlw` | Domain-separated QSEED derivation |
| `proofs.mlw` | All 22 proof obligations (PO1-PO22) |

**QSEED formula**: `SHA3_256(e || DOMAIN || PROC_ID || PROG_HASH || TENSOR_SHAPE || EPOCH)`

**Fluctuation sample**: `f(seed, t) = seed × 6364136223846793005 + t × 1442695040888963407`

#### 3b. SystemVerilog RTL (8 modules)

| Module | Purpose |
|--------|---------|
| `processor_top.sv` | Top-level: SM array, QRNG scheduler, master FSM |
| `sm.sv` | Single SM: fetch/decode/execute, 32 registers |
| `scheduler.sv` | QRNG-driven priority scheduler with LFSR |
| `qrng_interface.sv` | Entropy ingestion, domain-separated seed |
| `shared_memory.sv` | 64KB shared memory, bank conflict avoidance |
| `barrier.sv` | Barrier synchronization across SMs |
| `teu.sv` | Tensor Execution Unit: 64x64 matrix multiply |
| `seed_generator.sv` | Domain-separated seed derivation |

#### 3c. Rust Simulator

Reference simulator with trace output. `cargo build --release` then run against any program binary.

#### 3d. Python Assembler

Encodes the 35-instruction ISA to binary. Handles labels, `.const` directives, all addressing modes.

### 4. Assembler Pipeline

Hand-rolled assemblers that map directly to machine code and gate-level.

#### 4a. x86_64 Assembler

Parses NASM x86_64 assembly and encodes to ELF-compatible machine code.

**Supported instructions**: MOV, PUSH, POP, LEA, XOR, ADD, SUB, CMP, TEST, JMP, Jcc, CALL, RET, SYSCALL, MOVZX, SHL, SHR, AND, OR, INC, NOP, INT

**Assembled from Ahmad's TWIN-MARS codebase**:
- `bootstrap.asm` → `bootstrap.bin` (53 bytes) — ELF entry, stack parse, call main
- `main.asm` → `main.bin` (474 bytes) — CLI parsing, headless/interactive modes
- `storage.asm` → `storage.bin` (318 bytes) — getdents64, mkdir, filesystem ops
- `terminal.asm` → `terminal.bin` (999 bytes) — Raw TUI, alt screen, slash commands

#### 4b. PTX Assembler

Parses CUDA PTX assembly and maps to SASS binary (SM89/90 target).

**Supported operations**:
- Data movement: MOV, LD, ST, LDI, LEA, SEL, SHF, PRMT, BFE, BFI
- Arithmetic: IADD, IADD3, ISUB, IMUL, IDIV, IMAD, FADD, FSUB, FMUL, FDIV, FFMA
- Logic: LOP, LOP3.LUT, AND, OR, XOR, NOT
- Comparison: ISETP, FSETP, SETP, SET, SELP
- Control: BRA, JMP, CALL, RET, EXIT, NOP
- Synchronization: BAR, BAR.SYNC, BAR.REDUX
- Tensor Core: HMMA (all variants: 1688, 884, 8816, 16816, 1684 for F16/F32)
- Shared Memory: LDS, STS, LDSM (16/32, M88)
- Memory: LDG, STG, LDGSTS, LDGDEPBAR, LDTC

**Assembled from Ahmad's flash_attention.ptx**:
- `flash_attention_paged` — SM89 paged attention with WMMA tensor cores
- `tma_paged_copy` — Async TMA copy with cluster launch

#### 4c. Gate-Level Synthesis (Circom 2.0)

Maps SASS instructions to R1CS constraints for zero-knowledge verification.

**Circuit modules**:

| Module | Gates | Description |
|--------|-------|-------------|
| AndGate, OrGate, XorGate, NotGate | 1 | Basic logic |
| NandGate, NorGate, XnorGate | 1 | Derived logic |
| FullAdder, HalfAdder | 5, 3 | Arithmetic primitives |
| Adder4, Adder32 | 20, 160 | Ripple carry adders |
| Subtractor32 | 164 | Borrow subtraction |
| Multiplier32 | ~1024 | Shift-add multiplication |
| Mux2, Mux4, Mux8 | 1, 3, 7 | Multiplexers |
| Demux4 | 3 | Demultiplexer |
| DFF, Register32 | 1, 32 | Storage elements |
| RegisterFile | ~2048 | 32 × 32-bit register file |
| SASSDecoder | 128 | 128-bit instruction decoder |
| PTXArithmetic | ~500 | ALU with MUX result selection |
| PTXMemory | ~50 | Load/store unit |
| PTXBranch | ~30 | Branch with condition evaluation |
| SASSProcessor | ~3000 | Complete processor core |
| CompleteProcessor | ~3000 | Processor with instruction memory |

**Gate count estimate**: 3,431 gates for flash_attention.ptx (73 SASS instructions)

### 5. Quantum Array Processor

Recursive quantum array processor: J-style array expressions → QNASM → binary → quantum circuit → statevector simulation.

**Pipeline**: `J → Array IR → Quantum IR → QNASM → Binary → Circuit → Statevector → Measurement`

**Features**:
- J-style array expression language with element-wise ops, reshape, transpose, matmul
- Quantum NASM (QNASM) intermediate assembly: QALLOC, H/X/Y/Z/CX/CZ, RX/RY/RZ, MEASURE
- Quantum array operations: QARRAY, QMAP, QREDUCE, QDOT, QMATMUL
- Statevector simulator with full gate application
- Optimizations: barrier removal, rotation merging, identity elimination
- CLI: compile, assemble, run, simulate, disassemble, dump-ir

**Files**: 15 Python modules, 4 test files, 4 example programs

### 6. DreamcyclesInvariant

Invariant-preservation kit with ANU QRNG quantum superposition model.

**Features**:
- `preservesInvariant` — Exact-Eq variant for discrete invariants
- `preservesInvariantMetric` — Complex-valued metric with tolerance
- `Qubit` type with Hadamard gate, measurement, probability tracking
- `fetchANU` — Live connection to ANU QRNG (`qrng.anu.edu.au`)
- `TensorBlock` — Fold/length operations for tensor data

**Integration**: ANU quantum randomness feeds the quantum scheduler for measurement-driven collapse.

## How To Run

### Assemble Ahmad's files

```bash
cd assembler-pipeline
python run_pipeline.py --all "C:\Users\jessi\Downloads" output/
```

### Run individual pipelines

```bash
# x86_64 assembly → machine code
python x86_64_assembler.py bootstrap.asm bootstrap.bin

# PTX → SASS binary
python ptx_assembler.py flash_attention.ptx flash_attention.sass.bin

# PTX → gate-level netlist
python ptx_assembler.py --gates flash_attention.ptx flash_attention.gates.json

# Quantum-Tensor RISC assembler
cd quantum-tensor-risc/assembler
python assembler.py ../examples/vector_add_entropy/program.s ../examples/vector_add_entropy/program.bin

# Quantum Array Processor
cd qprocessor
python -m qprocessor compile ../qprocessor/examples/array.j
python -m qprocessor assemble ../qprocessor/examples/bell.qnasm
python -m qprocessor simulate ../qprocessor/examples/bell.qnasm
```

### Build Rust simulator

```bash
cd quantum-tensor-risc/simulator
cargo build --release
cargo run -- --program ../examples/vector_add_entropy/program.bin --sms 4 --trace trace.json
```

### Compile CUDA kernel

```bash
cd gemm-softmax
nvcc -arch=sm_80 -o gemm_softmax src/gemm_online_softmax.cu
```

## Formal Proofs (Why3)

All 22 proof obligations are PROVEN:

| PO | Statement | Status |
|----|-----------|--------|
| PO1 | encode_injective | PROVEN |
| PO2 | global_step_preserves_register_bounds | PROVEN |
| PO3 | global_step_preserves_pc_validity | PROVEN |
| PO4 | sm_isolation | PROVEN |
| PO5 | qrng_read_preserves_length | PROVEN |
| PO6 | qseed_deterministic | PROVEN |
| PO7 | tile_mul_correct | PROVEN |
| PO8 | scheduler_safety | PROVEN |
| PO9 | no_op_always_valid | PROVEN |
| PO10 | map_returns_member | PROVEN |
| PO11 | entropy_replay | PROVEN |
| PO12 | seed_derivation_deterministic | PROVEN |
| PO13 | fluctuation_sample_deterministic | PROVEN |
| PO14 | barrier_safety | PROVEN |
| PO15 | atomic_cas_linearizability | PROVEN |
| PO16 | tensor_tmov_preserves_alignment | PROVEN |
| PO17 | qrng_domain_separation | PROVEN |
| PO18 | schedule_deterministic | PROVEN |
| PO19 | scheduler_priority_inversion_free | PROVEN |
| PO20 | sm_state_isolation | PROVEN |
| PO21 | halt_propagation | PROVEN |
| PO22 | processor_termination | PROVEN |

## Key Constants

| Constant | Value | Purpose |
|----------|-------|---------|
| DOMAIN | 0x5A5A5A5A | QRNG domain separation |
| PROC_ID | 0x01 | Processor identification |
| PROG_HASH | 0xDEADBEEF | Program hash for seed derivation |
| TENSOR_M | 256 | Matrix M dimension |
| TENSOR_K | 256 | Matrix K dimension |
| TENSOR_N | 256 | Matrix N dimension |
| TILE_SZ | 64 | Tile size for tensor decomposition |
| MAX_PRIO | 7 | Maximum scheduler priority |
| SM_COUNT | 4-128 | Number of streaming multiprocessors |
| HALT_ADDR | 0xFFFFFFFF | Halt instruction address |
| SLOT_SIZE | 8 | AST node size (Circom) |
| MAX_DEPTH | 20 | Maximum recursion depth (Circom) |

## SASS Opcode Map

| Opcode | Value | Category |
|--------|-------|----------|
| NOP | 0x00 | Control |
| LOP | 0x01 | Logic |
| IADD | 0x10 | Arithmetic |
| ISUB | 0x11 | Arithmetic |
| IMUL | 0x12 | Arithmetic |
| IDIV | 0x13 | Arithmetic |
| FADD | 0x14 | Float |
| FSUB | 0x15 | Float |
| FMUL | 0x16 | Float |
| FDIV | 0x17 | Float |
| FFMA | 0x1E | Float |
| LDG | 0x04 | Memory |
| STG | 0x05 | Memory |
| LDS | 0x08 | Shared Memory |
| STS | 0x09 | Shared Memory |
| LEA | 0x20 | Address |
| SHL | 0x28 | Shift |
| SHR | 0x29 | Shift |
| ISETP | 0x2D | Compare |
| DSETP | 0x2E | Compare |
| FSETP | 0x2F | Compare |
| SELP | 0x3D | Select |
| SHF | 0x3E | Shift |
| XMAD | 0x34 | Multiply |
| IMAD | 0x3B | Multiply |
| IADD3 | 0x3A | Arithmetic |
| LOP3 | 0x5E | Logic |
| HMMA | 0x51 | Tensor Core |
| SHFL | 0x38 | Warp |
| VOTE | 0x38 | Warp |
| RED | 0x3E | Reduction |
| BAR | 0x5F | Synchronization |
| EXIT | 0x20 | Control Flow |

## License

Tri-license: Sovereign Source License v1.0 + BSL-1.1 + AGPL-3.0

All code is sovereign technology of the Bel Esprit D'Accord Irrevocable Trust.
