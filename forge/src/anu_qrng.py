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
ANU QRNG wrapper with deterministic fallback and JSON audit logging.

Fetches true quantum vacuum entropy from https://qrng.anu.edu.au
Falls back to deterministic zero-fluctuation when offline.
Every field element is logged before any gate is emitted.
"""
from __future__ import annotations
import json
import time
from typing import List, Optional

P = 18446744069414584321  # SNARK prime

_ANU_URL = "https://qrng.anu.edu.au/API/jsonI.php"
_ANU_TIMEOUT = 25


def get_anu_field_elements(n: int) -> List[int]:
    """
    Fetch n quantum-random uint16 values from ANU and map to field elements.
    Returns list of ints in [0, P).
    Falls back to deterministic zeros if ANU is unreachable.
    """
    try:
        import requests
        resp = requests.get(
            _ANU_URL,
            params={"length": n, "type": "uint16", "size": 1024},
            timeout=_ANU_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        raw = data.get("data", [])
        # Map uint16 to field elements
        return [int(x) % P for x in raw[:n]]
    except Exception:
        # Deterministic fallback: zeros (valid QASM, no fluctuation)
        return [0] * n


def log_fluctuation_to_json(flux: List[int], path: str) -> None:
    """
    Write a JSON audit record containing the fluctuation field elements.
    Each record includes timestamp, values, and count for traceability.
    """
    record = {
        "timestamp": time.time(),
        "count": len(flux),
        "values": flux,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2)
