# Sovereign GPU — Unified Compute Monorepo

**32-bit fixed-width RISC with QRNG scheduler + Tensor Execution Units**

Sovereign Source License v1.0 + BSL-1.1 + AGPL-3.0  
Copyright (C) 2026 Ahmad Ali Parr / SNAPKITTYWEST

## Repository Structure

```
sovereign-gpu/
├── gemm-softmax/
│   └── src/
│       └── gemm_online_softmax.cu      # Fused GEMM + Online Softmax (sm_80+)
├── fri-butterfly/
│   └── sass/
│       └── fri_butterfly.sass           # Binary-field FRI butterfly (sm_86, GF(2^128))
├── quantum-tensor-risc/
│   ├── why3/                            # Why3 formal model
│   │   ├── processor.mlw                # Global state + GLOBAL_STEP
│   │   ├── isa.mlw                      # 32-bit RISC ISA (35 instructions)
│   │   ├── sm.mlw                       # Streaming Multiprocessor
│   │   ├── scheduler.mlw                # QRNG-driven priority scheduler
│   │   ├── tensor.mlw                   # Tensor Execution Unit
│   │   ├── qrng.mlw                     # Quantum RNG interface
│   │   ├── entropy.mlw                  # External entropy buffer
│   │   ├── seed.mlw                     # Domain-separated QSEED derivation
│   │   └── proofs.mlw                   # All proof obligations (PO1-PO22)
│   ├── rtl/                             # SystemVerilog RTL
│   │   ├── processor_top.sv             # Top-level module
│   │   ├── sm.sv                        # Streaming Multiprocessor
│   │   ├── scheduler.sv                 # QRNG-driven scheduler
│   │   ├── qrng_interface.sv            # QRNG entropy interface
│   │   ├── shared_memory.sv             # Shared memory controller
│   │   ├── barrier.sv                   # Barrier synchronization
│   │   ├── teu.sv                       # Tensor Execution Unit
│   │   └── seed_generator.sv            # Domain-separated seed derivation
│   ├── simulator/                       # Reference simulator (Rust)
│   │   ├── Cargo.toml
│   │   └── src/
│   │       ├── main.rs                  # CLI entry point
│   │       ├── isa.rs                   # Instruction decode + execute
│   │       ├── sm.rs                    # SM state
│   │       ├── scheduler.rs             # Scheduler logic
│   │       ├── qrng.rs                  # QRNG state + domain separation
│   │       └── engine.rs                # Engine orchestration
│   ├── assembler/                       # Python macro assembler
│   │   ├── assembler.py
│   │   └── opcode_table.json
│   ├── tests/                           # Unit tests
│   │   ├── isa/test_isa.rs
│   │   ├── scheduler/test_scheduler.rs
│   │   ├── tensor/test_tensor.rs
│   │   └── replay/test_replay.rs
│   └── examples/
│       └── vector_add_entropy/program.s
└── README.md
```

## Architecture

### Processor (32-bit RISC)
- **32 general-purpose registers** (x0-x31), x31 = return address
- **35 instructions**: R-type, I-type, S-type, B-type, J-type
- **Tensor instructions**: TMOV, TLOAD, TSTORE, TZERO, TSYNC, TILEID, TILESZ, TREDUCE
- **Parallel instructions**: SPAWN, JOIN, SYNC, BARRIER
- **Atomic instructions**: ATOM_ADD, ATOM_SUB, ATOM_AND, ATOM_OR, ATOM_XOR, ATOM_CAS
- **QRNG instructions**: QRNG_READ, QRNG_SEED

### QRNG-Driven Scheduler
- Domain-separated seed: `QSEED(e) = SHA3_256(e || DOMAIN || PROC_ID || PROG_HASH || TENSOR_SHAPE || EPOCH)`
- Priority-based task scheduling (0-7)
- Deterministic replay from same seed
- Fluctuation sample: `f(seed, t) = seed * 6364136223846793005 + t * 1442695040888963407`

### Tensor Fabric
- 256×256 matrix multiply with 64×64 tile decomposition
- Tensor Execution Unit (TEU) per SM
- Online softmax accumulation (no intermediate writes)

## Building

### Simulator (Rust)
```bash
cd quantum-tensor-risc/simulator
cargo build --release
cargo run -- --program ../examples/vector_add_entropy/program.bin --sms 4 --trace trace.json
```

### Assembler (Python)
```bash
cd quantum-tensor-risc/assembler
python assembler.py ../examples/vector_add_entropy/program.s ../examples/vector_add_entropy/program.bin
```

### Formal Verification (Why3)
```bash
cd quantum-tensor-risc/why3
why3 prove processor.mlw
```

### CUDA Kernel (GEMM + Online Softmax)
```bash
cd gemm-softmax
nvcc -arch=sm_80 -o gemm_softmax src/gemm_online_softmax.cu
```

## Formal Proofs (Why3)

All 22 proof obligations are PROVEN in Why3:

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

| Constant | Value |
|----------|-------|
| DOMAIN | 0x5A5A5A5A |
| PROC_ID | 0x01 |
| PROG_HASH | 0xDEADBEEF |
| TENSOR_M | 256 |
| TENSOR_K | 256 |
| TENSOR_N | 256 |
| MAX_PRIO | 7 |
| SM_COUNT | 4-128 |
| HALT_ADDR | 0xFFFFFFFF |

## License

Tri-license: Sovereign Source License v1.0 + BSL-1.1 + AGPL-3.0
