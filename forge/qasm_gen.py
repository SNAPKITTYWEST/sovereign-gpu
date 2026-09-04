"""
OpenQASM 3 generator with α-scaled ANU vacuum-fluctuation rz layer.

Each call to rank1_to_qasm emits a gate definition in OpenQASM 3.
The α parameter scales ANU field elements before converting to rz angles.
Returns (gate_definition, gate_name, n_q, fluctuation_values) for audit logging.
"""
from __future__ import annotations
from fractions import Fraction
from typing import List, Tuple

from exact_rrd import exact_rrd, vec_to_angles

try:
    from anu_qrng import get_anu_field_elements
    _ANU_AVAILABLE = True
except Exception:
    _ANU_AVAILABLE = False

P = 18446744069414584321  # SNARK prime
SCALE = 2 ** 64           # fixed-point scaling
BASE_ERROR_RATE = 0.01    # 1% base chance of X-error per alpha unit


def rank1_to_qasm(
    base: int,
    vecs: List[List[Fraction]],
    alpha: int = 1,
    noise_mode: str = "rz",
) -> Tuple[str, str, int, list]:
    """
    Emit an OpenQASM 3 gate applying rz rotations on each qubit.

    noise_mode:
      'rz'  → alpha scales ANU field elements as rz angles (phase-only)
      'x'   → alpha scales a bit-flip probability threshold (transverse noise)

    Returns (gate_definition, gate_name, n_q, audit_data).
    audit_data is either List[int] (rz mode) or List[Tuple[int, bool]] (x mode).
    """
    gate_name = f"rank1_{base}"
    n_q = sum(len(v) for v in vecs)

    lines: List[str] = [f"gate {gate_name} q[0:{n_q-1}] {{"]
    offset = 0
    for v in vecs:
        angles = vec_to_angles(v)
        for j, ang in enumerate(angles):
            lines.append(f"  // Rz on q[{offset + j}] with field {ang}")
            lines.append(f"  rz(2 * pi() * {ang} / {SCALE}) q[{offset + j}];")
        offset += len(v)

    audit_data = []

    if _ANU_AVAILABLE:
        raw_flux = get_anu_field_elements(n_q)

        if noise_mode == "x":
            # Transverse noise: threshold-based X-gate injection
            threshold = alpha * BASE_ERROR_RATE
            for j, f in enumerate(raw_flux):
                prob = (f % P) / P
                triggered = prob < threshold
                audit_data.append((f, triggered))
                lines.append(
                    f"  // Transverse noise on q[{j}] "
                    f"(ANU={f}, prob={prob:.6f}, threshold={threshold:.4f})"
                )
                if triggered:
                    lines.append(f"  x q[{j}];")
                else:
                    lines.append(f"  // id q[{j}]; (no flip)")
        else:
            # Phase noise: alpha-scaled rz layer
            flux = [(f * alpha) % P for f in raw_flux]
            for j, f in enumerate(flux):
                lines.append(
                    f"  // Vacuum fluctuation on q[{j}] "
                    f"(ANU field={f}, alpha={alpha})"
                )
                lines.append(f"  rz(2 * pi() * {f} / {SCALE}) q[{j}];")
            audit_data = flux
    else:
        # Deterministic fallback
        for j in range(n_q):
            lines.append(f"  // Vacuum fluctuation disabled (fallback) q[{j}]")
            lines.append(f"  rz(0.0) q[{j}];")
        audit_data = [0] * n_q

    lines.append("}")
    gate_def = "\n".join(lines)
    return gate_def, gate_name, n_q, audit_data


def generate_openqasm(
    tensor: List,
    alpha: int = 1,
    noise_mode: str = "rz",
) -> Tuple[str, list]:
    """
    High-level API: decompose a nested rational tensor into rank-1 terms,
    generate the OpenQASM 3 gate definitions, and return the full program
    plus the audit data (fluctuation field elements).

    Returns (qasm_string, audit_data).
    """
    terms = exact_rrd(tensor)

    header = [
        "OPENQASM 3.0;",
        'include "stdgates.inc";',
    ]

    # Count total qubits needed
    total_q = 0
    gate_bodies = []
    all_audit = []
    for base, vecs in terms:
        gate_def, gate_name, n_q, audit = rank1_to_qasm(
            int(base), vecs, alpha=alpha, noise_mode=noise_mode
        )
        gate_bodies.append(gate_def)
        all_audit.extend(audit) if isinstance(audit, list) else all_audit.append(audit)
        total_q += n_q

    qubit_decl = f"qubit[{total_q}] q;"

    # Assemble full program
    program_lines = header + [qubit_decl, ""] + gate_bodies + [""]

    # Instantiate gates
    offset = 0
    for base, vecs in terms:
        n_q = sum(len(v) for v in vecs)
        gate_name = f"rank1_{int(base)}"
        if n_q == 1:
            program_lines.append(f"{gate_name} q[{offset}];")
        else:
            program_lines.append(f"{gate_name} q[{offset}:{offset + n_q - 1}];")
        offset += n_q

    # Measurements
    program_lines.append("")
    for i in range(total_q):
        program_lines.append(f"measure q[{i}] -> c[{i}];")

    qasm = "\n".join(program_lines)
    return qasm, all_audit
