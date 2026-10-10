"""Development-only covariance comparison on explicitly supplied return observations."""
import argparse
import datetime as dt
import json
import math
import hashlib
from pathlib import Path
from fractions import Fraction
import numpy as np


def canonical_sha256(value):
    try:
        encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise ValueError("input and provenance must be finite JSON") from error
    return hashlib.sha256(encoded).hexdigest()


def squared_frobenius(prediction, realized):
    with np.errstate(over="ignore", invalid="ignore", under="ignore"):
        residual = prediction - realized
        value = float(np.sum(residual**2))
    if not np.isfinite(residual).all() or not math.isfinite(value):
        raise ValueError("covariance/loss overflow; no comparison receipt")
    if value < float.fromhex('0x1p-1022') and np.any(residual != 0):
        # Individual squared entries can round to zero even when their sum is
        # representable. Round the exact binary-input sum once in this regime.
        exact = sum((Fraction(float(x))**2 for x in residual.flat), Fraction())
        value = float(exact)
        if value == 0:
            raise ValueError("squared Frobenius loss underflow; rescale inputs explicitly")
    return value


def mean_losses(values):
    try:
        total = math.fsum(values)
    except OverflowError:
        total = sum((Fraction(value) for value in values), Fraction())
    mean = float(total / len(values))
    if mean == 0 and total != 0:
        raise ValueError("mean loss underflow; rescale inputs explicitly")
    return mean


def _covariance(rows):
    with np.errstate(over="ignore", invalid="ignore"):
        covariance = np.atleast_2d(np.cov(rows, rowvar=False, ddof=1))
    if not np.isfinite(covariance).all():
        # np.cov may overflow its mean reduction even for a large constant
        # column whose covariance is exactly zero. Only the failing arithmetic
        # path uses shifted/normalized centering; normal-scale results retain
        # their existing calculation and the declared squared-Frobenius metric.
        with np.errstate(over="ignore", invalid="ignore", under="ignore"):
            shifted = rows - rows[0]
            finite_shift = np.isfinite(shifted).all(axis=0)
            # Each asset needs its own scale. A large unrelated column must
            # not push a small column's normalized variance into subnormals.
            scale = np.where(finite_shift, np.max(np.abs(shifted), axis=0),
                             np.max(np.abs(rows), axis=0))
            numerator = np.where(finite_shift, shifted, rows)
            normalized = np.divide(numerator, scale, out=np.zeros_like(rows, dtype=np.float64),
                                   where=scale != 0)
            centered = normalized - normalized.mean(axis=0, keepdims=True)
            normalized_covariance = centered.T @ centered / (len(rows) - 1)
            # Restore both column units in one exponent operation. Either
            # ordinary multiplication order can overflow/underflow before a
            # representable cross-covariance has been formed.
            covariance_fraction, covariance_exponent = np.frexp(normalized_covariance)
            scale_fraction, scale_exponent = np.frexp(scale)
            covariance = np.ldexp(
                covariance_fraction * scale_fraction[:, None] * scale_fraction[None, :],
                covariance_exponent + scale_exponent[:, None] + scale_exponent[None, :],
            )
        if np.any((normalized_covariance != 0) & (covariance == 0)):
            raise ValueError("covariance underflow; no comparison receipt")
    if not np.isfinite(covariance).all():
        raise ValueError("covariance/loss overflow; no comparison receipt")
    # A genuinely nonconstant supplied column has positive sample variance.
    # Underflow must not turn that dispersion into an exact zero covariance.
    nonconstant = np.any(rows != rows[0], axis=0)
    if np.any(nonconstant & (np.diag(covariance) == 0)):
        raise ValueError("covariance underflow; no comparison receipt")
    return covariance


def compare(record):
    if not isinstance(record, dict) or record.get("evaluation_mode") != "development":
        raise ValueError("only explicit development mode is supported")
    source = record.get("source")
    if not isinstance(source, str) or not source.strip():
        raise ValueError("source reference required")
    input_sha256 = canonical_sha256(record)
    rows = record.get("rows")
    train = record.get("train_rows")
    horizon = record.get("horizon_rows")
    if any(isinstance(v, bool) or not isinstance(v, int) or v < 2 for v in [train, horizon]):
        raise ValueError("train_rows and horizon_rows must be integers >= 2")
    if not isinstance(rows, list) or len(rows) < train + horizon:
        raise ValueError("insufficient observations for one complete fold")
    observations, dates = [], []
    assets = record.get("assets")
    if not isinstance(assets, list) or not assets or any(not isinstance(a, str) or not a.strip() for a in assets):
        raise ValueError("nonempty asset names required")
    if len({a.strip().casefold() for a in assets}) != len(assets):
        raise ValueError("duplicate asset name")
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("row must be an object")
        date = row.get("date")
        if not isinstance(date, str):
            raise ValueError("ISO calendar date required")
        parsed = dt.date.fromisoformat(date)
        if parsed.isoformat() != date or parsed > dt.datetime.now(dt.timezone.utc).date():
            raise ValueError("canonical completed date required")
        if dates and date <= dates[-1]:
            raise ValueError("dates must be unique and strictly increasing")
        dates.append(date)
        values = row.get("returns")
        if not isinstance(values, list) or len(values) != len(assets):
            raise ValueError("returns must match declared assets")
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in values):
            raise ValueError("finite numeric decimal returns required")
        observations.append(values)
    values = np.asarray(observations, dtype=float)
    folds = []
    # Nonoverlapping evaluation windows; every prediction uses only earlier rows.
    for start in range(train, len(rows) - horizon + 1, horizon):
        context = values[start-train:start]
        future = values[start:start+horizon]
        with np.errstate(over="ignore", invalid="ignore"):
            sample = _covariance(context)
            realized = _covariance(future)
            diagonal = np.diag(np.diag(sample))
            # Fixed illustrative comparator, not tuned or advertised as optimal.
            shrunk = .8 * sample + .2 * diagonal
            predictions = {"sample": sample, "diagonal": diagonal, "fixed_shrinkage_0_2": shrunk}
            losses = {name: squared_frobenius(prediction, realized)
                      for name, prediction in predictions.items()}
        if not np.isfinite(sample).all() or not np.isfinite(realized).all() or any(not math.isfinite(v) for v in losses.values()):
            raise ValueError("covariance/loss overflow; no comparison receipt")
        folds.append({"context_start": dates[start-train], "context_end": dates[start-1],
                      "evaluation_start": dates[start], "evaluation_end": dates[start+horizon-1],
                      "context_sha256": canonical_sha256(rows[start-train:start]),
                      "evaluation_sha256": canonical_sha256(rows[start:start+horizon]),
                      "predicted_covariance": {name: value.tolist() for name, value in predictions.items()},
                      "realized_covariance": realized.tolist(),
                      "squared_frobenius_error": losses,
                      "paired_error_difference_vs_sample": {name: value - losses["sample"] for name, value in losses.items()}})
    return {"schema": "eigenfinance.development-covariance.v2",
            "input_sha256": input_sha256,
            "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "numpy_version": np.__version__,
            "estimator_configuration": {"covariance_ddof": 1, "shrinkage_weight": 0.2,
                                        "shrinkage_target": "diagonal of same-context sample covariance",
                                        "metric": "unnormalized squared Frobenius error against common future sample covariance",
                                        "paired_difference": "method error minus sample error; negative is lower error"},
            "evaluation_mode": "development", "source": source.strip(), "assets": assets,
            "train_rows": train, "horizon_rows": horizon, "folds": folds,
            "unused_tail_rows": (len(rows)-train) % horizon,
            "mean_squared_frobenius_error": {name: mean_losses([f["squared_frobenius_error"][name] for f in folds])
                                              for name in ["sample", "diagonal", "fixed_shrinkage_0_2"]},
            "source_verified": False, "availability_verified": False, "protected_run_authorized": False,
            "scope": "supplied development rows; noisy future covariance target; no trading or significance claim"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="development JSON record")
    args = parser.parse_args()
    try:
        with open(args.input, encoding="utf-8") as f:
            print(json.dumps(compare(json.load(f)), indent=2, allow_nan=False))
    except (ValueError, OSError, OverflowError, np.linalg.LinAlgError) as exc:
        parser.exit(2, f"Invalid input: {exc}\n")
