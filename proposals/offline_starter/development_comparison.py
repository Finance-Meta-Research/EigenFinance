"""Development-only covariance comparison on explicitly supplied return observations."""
import argparse
import datetime as dt
import json
import math
import numpy as np


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
            if np.isfinite(shifted).all():
                scale = float(np.max(np.abs(shifted)))
                normalized = shifted / scale if scale else shifted
            else:
                scale = float(np.max(np.abs(rows)))
                normalized = rows / scale
            centered = normalized - normalized.mean(axis=0, keepdims=True)
            covariance = ((centered.T @ centered / (len(rows) - 1)) * scale) * scale
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
            losses = {}
            for name, prediction in [("sample", sample), ("diagonal", diagonal), ("fixed_shrinkage_0_2", shrunk)]:
                difference = prediction - realized
                loss = float(np.sum(difference**2))
                if loss == 0 and np.any(difference != 0):
                    raise ValueError("nonzero covariance error underflowed; no comparison receipt")
                losses[name] = loss
        if not np.isfinite(sample).all() or not np.isfinite(realized).all() or any(not math.isfinite(v) for v in losses.values()):
            raise ValueError("covariance/loss overflow; no comparison receipt")
        folds.append({"context_start": dates[start-train], "context_end": dates[start-1],
                      "evaluation_start": dates[start], "evaluation_end": dates[start+horizon-1],
                      "squared_frobenius_error": losses})
    return {"evaluation_mode": "development", "source": source.strip(), "assets": assets,
            "train_rows": train, "horizon_rows": horizon, "folds": folds,
            "unused_tail_rows": (len(rows)-train) % horizon,
            "mean_squared_frobenius_error": {name: math.fsum(f["squared_frobenius_error"][name]/len(folds) for f in folds)
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
