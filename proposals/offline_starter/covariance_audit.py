"""Offline diagnostics for a supplied covariance matrix; no market-data access."""
import argparse
import json
import numpy as np


def audit(matrix):
    if not isinstance(matrix, list) or any(not isinstance(row, list) for row in matrix):
        raise ValueError("matrix must be a JSON array of arrays")
    if any(isinstance(v, bool) for row in matrix for v in row):
        raise ValueError("boolean covariance entry")
    raw = np.asarray(matrix)
    if raw.dtype.kind not in "iuf" or raw.ndim != 2 or raw.shape[0] != raw.shape[1] or raw.shape[0] == 0:
        raise ValueError("nonempty square numeric matrix required")
    a = raw.astype(float)
    if not np.isfinite(a).all():
        raise ValueError("nonfinite covariance entry")
    scale = float(np.max(np.abs(a)))
    tolerance = 1e-10 * scale
    if not np.allclose(a, a.T, rtol=0, atol=tolerance):
        raise ValueError("matrix is not symmetric within declared tolerance")
    a = (a / 2) + (a.T / 2)
    eigenvalues = np.linalg.eigvalsh(a)
    if not np.isfinite(eigenvalues).all():
        raise ValueError("eigendecomposition overflow")
    psd = bool(eigenvalues[0] >= -tolerance)
    positive_definite = bool(eigenvalues[0] > tolerance)
    condition = float(eigenvalues[-1] / eigenvalues[0]) if positive_definite else None
    if condition is not None and not np.isfinite(condition):
        condition = None
    return {"assets": len(a), "symmetric": True, "positive_semidefinite": psd,
            "positive_definite": positive_definite, "eigenvalues": eigenvalues.tolist(),
            "spectral_condition_number": condition, "absolute_tolerance": tolerance,
            "source_verified": False, "forecast_skill_established": False,
            "scope": "supplied-matrix numerical diagnostics only"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="JSON square covariance matrix")
    args = parser.parse_args()
    try:
        with open(args.input, encoding="utf-8") as f:
            print(json.dumps(audit(json.load(f)), indent=2, allow_nan=False))
    except (ValueError, OSError, OverflowError, np.linalg.LinAlgError) as exc:
        parser.exit(2, f"Invalid input: {exc}\n")
