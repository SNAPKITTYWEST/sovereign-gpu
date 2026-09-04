"""
Exact Recursive Rank Decomposition (fraction-free QR).

Deterministic, sovereign-first, auditable rational tensor decomposition.
All arithmetic uses fractions.Fraction — no floating-point approximations.
"""
from __future__ import annotations
from fractions import Fraction
from typing import List, Tuple


P = 18446744069414584321  # SNARK prime


def _get_shape(tensor) -> List[int]:
    """Return the shape of a nested list tensor."""
    shape = []
    current = tensor
    while isinstance(current, list):
        shape.append(len(current))
        current = current[0] if current else None
    return shape


def _flatten(tensor) -> List[Fraction]:
    """Flatten nested list to 1-D list of Fractions."""
    result = []
    if isinstance(tensor, list):
        for item in tensor:
            result.extend(_flatten(item))
    else:
        result.append(Fraction(tensor))
    return result


def _dot(a: List[Fraction], b: List[Fraction]) -> Fraction:
    """Dot product of two equal-length vectors."""
    return sum(x * y for x, y in zip(a, b))


def _outer(a: List[Fraction], b: List[Fraction]) -> List[List[Fraction]]:
    """Outer product of two vectors."""
    return [[x * y for y in b] for x in a]


def _matmul(A: List[List[Fraction]], B: List[List[Fraction]]) -> List[List[Fraction]]:
    """Matrix multiply A @ B for nested lists of Fractions."""
    rows_A, cols_A = len(A), len(A[0])
    cols_B = len(B[0])
    result = [[Fraction(0) for _ in range(cols_B)] for _ in range(rows_A)]
    for i in range(rows_A):
        for j in range(cols_B):
            for k in range(cols_A):
                result[i][j] += A[i][k] * B[k][j]
    return result


def _subtract_outer(M: List[List[Fraction]], a: List[Fraction], b: List[Fraction]) -> List[List[Fraction]]:
    """M - a @ b^T"""
    n, m = len(M), len(M[0])
    return [[M[i][j] - a[i] * b[j] for j in range(m)] for i in range(n)]


def _scale_vector(v: List[Fraction], s: Fraction) -> List[Fraction]:
    return [x * s for x in v]


def _column(matrix: List[List[Fraction]], j: int) -> List[Fraction]:
    return [row[j] for row in matrix]


def exact_rrd(tensor, max_rank: int = None) -> List[Tuple[int, List[List[Fraction]]]]:
    """
    Exact Recursive Rank Decomposition.

    Decomposes a tensor into a sum of rank-1 terms using fraction-free
    Gaussian elimination. Each term is (base, vectors) where:
      - base: scalar coefficient (Fraction)
      - vectors: list of 1-D vectors (one per mode)

    Returns list of (base, vectors) in decomposition order.
    """
    shape = _get_shape(tensor)
    flat = _flatten(tensor)
    n_modes = len(shape)

    # Reshape flat to nested list matching shape
    def _reshape(flat_data: List[Fraction], dims: List[int]):
        if len(dims) == 1:
            return [flat_data[i] for i in range(dims[0])]
        stride = 1
        for d in dims[1:]:
            stride *= d
        result = []
        for i in range(dims[0]):
            sub = _reshape(flat_data[i * stride:(i + 1) * stride], dims[1:])
            result.append(sub)
        return result

    matrix = _reshape(flat, shape)

    terms = []
    remaining = [row[:] if isinstance(row, list) else [row] for row in matrix]
    rank = 0

    if max_rank is None:
        max_rank = min(shape[0], shape[1]) if n_modes >= 2 else shape[0]

    for _ in range(max_rank):
        # Find pivot (first non-zero)
        pivot = None
        for i in range(len(remaining)):
            for j in range(len(remaining[0])):
                if remaining[i][j] != 0:
                    pivot = (i, j)
                    break
            if pivot:
                break

        if pivot is None:
            break

        pi, pj = pivot
        pivot_val = remaining[pi][pj]

        # Extract outer-product vectors
        row_vec = _scale_vector(remaining[pi], Fraction(1))
        col_vec = _column(remaining, pj)

        # Compute outer product
        outer = _outer(row_vec, col_vec)

        # Subtract from remaining
        remaining = _subtract_outer(remaining, row_vec, col_vec)

        # Store term: base = pivot_val, vectors = [row_vec, col_vec]
        terms.append((pivot_val, [row_vec, col_vec]))
        rank += 1

    return terms


def vec_to_angles(v: List[Fraction]) -> List[int]:
    """
    Convert a vector of Fractions to integer field elements suitable
    for rz angle computation: angle = int(v * SCALE) mod P.
    """
    SCALE = 2 ** 64
    return [int(val * SCALE) % P for val in v]
