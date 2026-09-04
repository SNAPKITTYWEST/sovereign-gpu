# DreamcyclesInvariant

Invariant-preservation kit with ANU QRNG quantum superposition model.

## Features

- **Invariant-preservation verification**: Exact-Eq and complex-valued metric variants
- **Quantum superposition model**: Pure-functional Complex amplitude representation
- **ANU QRNG connection**: Live quantum vacuum entropy from `qrng.anu.edu.au`
- **TensorBlock operations**: Fold, length, and structural transforms

## Usage

```haskell
import DreamcyclesInvariant

-- Verify invariant preservation
let result = preservesInvariant id transform after input
case result of
  Verified v proof -> -- invariant holds
  Refuted v msg    -> -- invariant violated
  Unverified msg   -> -- proof deferred

-- Quantum superposition
let q0 = mkQubit [(1.0 :+ 0.0, False)]
let qH = hadamard q0
(outcome, qCollapsed) <- measureWith <$> fetchRandom <*> pure qH

-- ANU QRNG
result <- fetchANU 10  -- 10 random uint16 values
```

## Integration with sovereign-gpu

The ANU QRNG feeds true quantum randomness into the quantum scheduler,
enabling measurement-driven collapse that cannot be predicted by classical means.
