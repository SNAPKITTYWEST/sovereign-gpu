# lean-formal

Sovereign Lean 4 Formal Verification Suite

**Zero sorrys.** Every proof is closed. No `sorry` anywhere.

## Theorems

| # | File | Theorem | Status |
|---|------|---------|--------|
| 1 | SubleqCore.lean | Memory Invariant | ✓ Closed |
| 2 | SubleqCore.lean | Branch Taken | ✓ Closed |
| 3 | SubleqCore.lean | Branch Not Taken | ✓ Closed |
| 4 | SubleqVM.lean | VM Termination (fuel) | ✓ Closed |
| 5 | AdditionCorrect.lean | Addition Correctness | ✓ Closed |
| 6 | MatrixAlgebra.lean | Left Identity (I * B = B) | ✓ Closed |
| 7 | MatrixAlgebra.lean | Right Identity (B * I = B) | ✓ Closed |
| 8 | MatrixAlgebra.lean | Associativity (AB)C = A(BC) | ✓ Closed |
| 9 | MatrixAlgebra.lean | Inverse Uniqueness | ✓ Closed |
| 10 | MatrixAlgebra.lean | Unitary → Invertible | ✓ Closed |
| 11 | ShorsAlgorithm.lean | Shor's Correctness (15 = 3×5) | ✓ Closed |

## Architecture

```
Memory = Nat → ZMod P_GOLD        -- total function, no bounds errors
SubleqState                       -- mem + pc + halted
subleq_step                       -- single-step transition
vm_run                            -- fuel-bounded recursive execution
```

## Field

P_GOLD = 18446744069414584321 (SNARK prime)

## License

Sovereign Source License v1.0 + BSL-1.1 + AGPL-3.0
SNAPKITTYWEST-PROPRIETARY-2026-001
