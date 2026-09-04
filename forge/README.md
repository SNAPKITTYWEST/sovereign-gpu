# FORGE — Parameter-Tuning Study & Deterministic Work-Stealing Executor

**SNAPKITTYWEST-PROPRIETARY-2026-001**
Ahmad Ali Parr, Bel Esprit D'Accord Irrevocable Trust · EIN 42-697643

Sovereign Source License v1.0 + BSL-1.1 + AGPL-3.0

## Components

| File | Purpose |
|------|---------|
| `exact_rrd.py` | Exact recursive rank decomposition (fraction-free QR, all Fraction arithmetic) |
| `anu_qrng.py` | ANU QRNG wrapper with deterministic fallback and JSON audit logging |
| `qasm_gen.py` | OpenQASM 3 generator with α-scaled vacuum-fluctuation rz/transverse-noise layer |
| `work_steal.py` | Deterministic work-stealing thread pool (round-robin steal, fully reproducible) |
| `sweep_alpha.py` | α-parameter sweep, TVD vs. uniform distribution, CSV output |
| `run_parallel.py` | Parallel driver using work-stealing pool |
| `density_matrix_sweep.py` | GPU-accelerated density matrix TVD sweep for transverse noise |

## Key Properties

- **Deterministic**: Given same inputs + α, produces identical audit files
- **Local-first**: No external quantum service required (ANU QRNG has fallback)
- **Auditable**: Every random field element is logged before gate emission
- **ZK-SNARK compatible**: All arithmetic over F_p, linear in field elements
- **GPU-accelerated**: density_matrix_sweep.py offloads to RTX 3080 via cuQuantum

## Quick Start

```bash
# Parameter sweep
python sweep_alpha.py

# Parallel work-stealing demo
python run_parallel.py

# GPU density matrix sweep
python density_matrix_sweep.py
```

## Audit Output

Each run produces:
- `work_steal_audit.jsonl` — one JSON line per task with audit_data
- `alpha_sweep.csv` — TVD vs α grid
- `transverse_tvd_sweep.csv` — transverse noise TVD results
