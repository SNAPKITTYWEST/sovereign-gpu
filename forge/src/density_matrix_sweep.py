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
GPU-accelerated density matrix TVD sweep for transverse noise.

Simulates X-gate injections scaled by alpha using Qiskit Aer GPU,
computing the Total Variation Distance from the ideal uniform distribution.
Offloads density matrix evolution to RTX 3080 via cuQuantum.
"""
from __future__ import annotations
import csv
import time
from fractions import Fraction
from typing import List, Tuple

from .exact_rrd import exact_rrd, _get_shape, _flatten
from .anu_qrng import get_anu_field_elements

try:
    from qiskit import QuantumCircuit
    from qiskit_aer import AerSimulator
    _HAS_GPU_AER = True
except Exception:
    _HAS_GPU_AER = False

P = 18446744069414584321
SCALE = 2 ** 64
BASE_ERROR_RATE = 0.02


def vec_to_angles(v: list) -> list:
    """Convert vector of Fractions to integer field elements."""
    return [int(val * SCALE) % P for val in v]


def rank1_with_transverse_noise(
    vecs: List[List[Fraction]], alpha: int
) -> Tuple[str, List[Tuple[int, bool]]]:
    """
    Generate OpenQASM 3 kernel with X-gates injected based on
    ANU field elements scaled by alpha.
    """
    n_q = sum(len(v) for v in vecs)
    lines: List[str] = [
        "OPENQASM 3.0;",
        'include "stdgates.inc";',
        f"qubit[{n_q}] q;",
        f"gate custom_kernel q[0:{n_q-1}] {{",
    ]

    # Rz foundational phase layer
    offset = 0
    for v in vecs:
        angles = vec_to_angles(v)
        for j, ang in enumerate(angles):
            lines.append(f"  rz(2 * pi() * {ang} / {SCALE}) q[{offset + j}];")
        offset += len(v)

    # Transverse noise layer via ANU stream
    audit_data = []
    raw_flux = get_anu_field_elements(n_q)
    threshold = alpha * BASE_ERROR_RATE

    for j, f in enumerate(raw_flux):
        prob = (f % P) / P
        triggered = prob < threshold
        audit_data.append((f, triggered))

        if triggered:
            lines.append(f"  x q[{j}]; // Transverse error (ANU={f})")
        else:
            lines.append(f"  // id q[{j}]; (no error)")

    lines.append("}")
    lines.append("custom_kernel q;")
    return "\n".join(lines), audit_data


def _simulate_density_matrix(qasm_str: str) -> dict[str, float]:
    """Run QASM on GPU using density matrix simulation."""
    lines = [
        line for line in qasm_str.splitlines()
        if "let" not in line and "measure" not in line
    ]
    clean_qasm = "\n".join(lines)

    qc = QuantumCircuit.from_qasm_str(clean_qasm)
    qc.save_density_matrix()

    sim = AerSimulator(method="density_matrix", device="GPU")
    result = sim.run(qc).result()
    dm = result.get_density_matrix()

    probs = {
        format(i, f"0{qc.num_qubits}b"): float(dm.probabilities()[i].real)
        for i in range(2 ** qc.num_qubits)
    }
    return probs


def _uniform_distance(
    probs_ideal: dict[str, float], probs_noisy: dict[str, float]
) -> float:
    """TVD between ideal and noisy distributions."""
    states = set(probs_ideal.keys()) | set(probs_noisy.keys())
    return 0.5 * sum(
        abs(probs_ideal.get(s, 0.0) - probs_noisy.get(s, 0.0)) for s in states
    )


def main() -> None:
    if not _HAS_GPU_AER:
        print("qiskit-aer[gpu] required for density matrix simulation.")
        return

    print("=== Transverse Noise TVD Sweep (GPU Density Matrix) ===\n")

    example_tensor = [
        [Fraction(1, 2), Fraction(1, 2)],
        [Fraction(1, 2), Fraction(1, 2)],
    ]

    alpha_levels = [0, 1, 3, 5, 10, 20]
    results = []

    # Ideal baseline (alpha = 0)
    ideal_qasm, _ = rank1_with_transverse_noise(example_tensor, alpha=0)
    ideal_probs = _simulate_density_matrix(ideal_qasm)

    csv_path = "transverse_tvd_sweep.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["alpha", "total_variation_distance", "injected_flips"])

        for a in alpha_levels:
            start = time.perf_counter()
            qasm, audit = rank1_with_transverse_noise(example_tensor, alpha=a)
            noisy_probs = _simulate_density_matrix(qasm)
            elapsed = (time.perf_counter() - start) * 1000

            tvd = _uniform_distance(ideal_probs, noisy_probs)
            flips = sum(1 for _, triggered in audit if triggered)

            results.append((a, tvd, flips))
            print(
                f"α = {a:2d} | TVD = {tvd:.6f} | Flips: {flips:3d} | "
                f"Time: {elapsed:.1f}ms"
            )
            writer.writerow([a, f"{tvd:.6f}", flips])

    print(f"\nSweep complete. Results written to {csv_path}")


if __name__ == "__main__":
    main()
