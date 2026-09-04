"""
Parallel driver using the deterministic work-stealing pool.

Demonstrates end-to-end sovereign, auditable, deterministic execution
of multiple tensor-decomposition jobs in parallel.
"""
from __future__ import annotations
from fractions import Fraction
from typing import List, Tuple

from work_steal import deterministic_work_steal
from exact_rrd import _get_shape
from qasm_gen import generate_openqasm
from anu_qrng import log_fluctuation_to_json

import random


def rand_tensor(shape):
    """Generate a random rational tensor of given shape."""
    def gen():
        return Fraction(random.randint(-5, 5), random.randint(1, 5))
    if len(shape) == 1:
        return [gen() for _ in range(shape[0])]
    return [rand_tensor(shape[1:]) for _ in range(shape[0])]


ALPHA = 2


def process_one(tensor: List) -> Tuple[str, list]:
    """
    Process one tensor: generate QASM with α-scaled fluctuation.
    Returns (qasm_string, audit_data).
    """
    qasm, audit = generate_openqasm(tensor, alpha=ALPHA)
    return qasm, audit


def main():
    tensors = [
        rand_tensor((2, 2)),
        rand_tensor((3, 3)),
        rand_tensor((2, 2, 2)),
        rand_tensor((4, 4)),
    ]

    print(f"Processing {len(tensors)} tensors with α={ALPHA} ...")
    print(f"Workers: 4 (deterministic work-stealing)\n")

    results = deterministic_work_steal(
        tasks=tensors,
        fn=process_one,
        num_workers=4,
        audit_path="work_steal_audit.jsonl",
    )

    print("=== Completed tasks (original order) ===")
    for i, qasm in enumerate(results):
        shape = _get_shape(tensors[i])
        n_lines = len(qasm.splitlines()) if qasm else 0
        print(f"  Task {i}: shape {shape} → {n_lines} QASM lines")

    print(f"\nAudit log: work_steal_audit.jsonl")


if __name__ == "__main__":
    main()
