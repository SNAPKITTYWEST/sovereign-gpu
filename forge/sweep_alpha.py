# Copyright © 2026 SnapKitty Collective and contributors.
#
# This file is part of a work licensed under the
# SnapKitty Strong Network Copyleft License Version 1.0 (SSNCL-1.0).
#
# You may use, study, modify, copy, and redistribute this work
# only under the terms of SSNCL-1.0.
#
# A copy of SSNCL-1.0 must accompany this work.

"""
Parameter sweep over α values.

Generates QASM with alpha-scaled vacuum-fluctuation rz layers,
simulates the kernel (feedback stripped), and computes the
total variation distance (TVD) from a uniform measurement distribution.
Writes alpha_sweep.csv for "Build in Public" artifacts.
"""
from __future__ import annotations
import csv
from fractions import Fraction
from typing import List, Tuple

from exact_rrd import exact_rrd
from qasm_gen import generate_openqasm

try:
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import Statevector
    _HAS_QISKIT = True
except Exception:
    _HAS_QISKIT = False

P = 18446744069414584321


def _strip_feedback(qasm: str) -> str:
    """Remove classical feedback blocks unsupported by Aer statevector sim."""
    lines = qasm.splitlines()
    out = []
    in_feedback = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("let b") and "= measure" in stripped:
            in_feedback = True
        if in_feedback:
            if stripped.startswith("}"):
                in_feedback = False
            continue
        out.append(line)
    return "\n".join(out)


def _simulate_qasm(qasm_str: str) -> dict[str, float]:
    """Simulate QASM and return probability distribution over bitstrings."""
    clean = _strip_feedback(qasm_str)
    qc = QuantumCircuit.from_qasm_str(clean)
    sv = Statevector.from_instruction(qc)
    return {
        format(i, f"0{sv.num_qubits}b"): p
        for i, p in enumerate(sv.probabilities())
    }


def _uniform_distance(probs: dict[str, float]) -> float:
    """TVD between empirical distribution and uniform over same support."""
    N = len(probs)
    if N == 0:
        return 0.0
    uniform = 1.0 / N
    return 0.5 * sum(abs(p - uniform) for p in probs.values())


def _evaluate_one_alpha(
    tensor: List[List[Fraction]], alpha: int
) -> Tuple[int, float, list]:
    """Generate QASM for given α, simulate, return (α, TVD, audit_data)."""
    qasm, audit = generate_openqasm(tensor, alpha=alpha)

    if not _HAS_QISKIT:
        return alpha, float("nan"), audit

    probs = _simulate_qasm(qasm)
    tvd = _uniform_distance(probs)
    return alpha, tvd, audit


def main():
    example_tensor = [
        [Fraction(1), Fraction(2)],
        [Fraction(2), Fraction(4)],
    ]

    alpha_values = [0, 1, 2, 4, 8, 16]
    results: List[Tuple[int, float, list]] = []

    print("Running α-sweep ...")
    for a in alpha_values:
        alpha, tvd, audit = _evaluate_one_alpha(example_tensor, a)
        results.append((alpha, tvd, audit))
        sample = audit[:2] if isinstance(audit, list) else audit
        print(f"α = {a:2d} → TVD = {tvd:.6f} (audit sample: {sample})")

    csv_path = "alpha_sweep.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["alpha", "total_variation_distance", "fluctuation_sample"])
        for a, tvd, audit in results:
            if isinstance(audit, list) and len(audit) >= 2:
                sample = f"{audit[0]},{audit[1]}"
            else:
                sample = str(audit)
            writer.writerow([a, f"{tvd:.6f}", sample])

    print(f"\nSweep finished. Results written to {csv_path}")


if __name__ == "__main__":
    main()
