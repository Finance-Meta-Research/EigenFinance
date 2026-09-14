from __future__ import annotations

from collections.abc import Callable
from typing import cast

import numpy as np
import numpy.typing as npt

FloatArray = npt.NDArray[np.float64]
Strategy = Callable[[FloatArray, float], FloatArray]


def _validate_returns(returns: FloatArray) -> None:
    if returns.ndim != 2 or returns.shape[0] < 2 or returns.shape[1] < 2:
        raise ValueError("training returns must have shape [time>=2, assets>=2]")
    if not np.all(np.isfinite(returns)):
        raise ValueError("training returns contain non-finite values")


def equal_weight(returns: FloatArray, shrinkage: float = 0.0) -> FloatArray:
    _validate_returns(returns)
    del shrinkage
    return np.full(returns.shape[1], 1.0 / returns.shape[1], dtype=np.float64)


def inverse_volatility(returns: FloatArray, shrinkage: float = 0.0) -> FloatArray:
    _validate_returns(returns)
    del shrinkage
    volatility = np.std(returns, axis=0, ddof=1)
    floor = max(float(np.median(volatility)) * 1e-6, 1e-12)
    inverse = 1.0 / np.maximum(volatility, floor)
    return inverse / inverse.sum()


def _project_simplex(vector: FloatArray) -> FloatArray:
    ordered = np.sort(vector)[::-1]
    cumulative = np.cumsum(ordered) - 1.0
    indices = np.arange(1, vector.size + 1)
    valid = ordered - cumulative / indices > 0
    if not np.any(valid):
        raise RuntimeError("simplex projection failed")
    rho = int(indices[valid][-1])
    threshold = cumulative[rho - 1] / rho
    return cast(FloatArray, np.maximum(vector - threshold, 0.0))


def minimum_variance(returns: FloatArray, shrinkage: float = 0.1) -> FloatArray:
    _validate_returns(returns)
    if not 0.0 <= shrinkage <= 1.0:
        raise ValueError("shrinkage must be in [0, 1]")
    covariance = np.cov(returns, rowvar=False, ddof=1)
    diagonal = np.diag(np.diag(covariance))
    covariance = (1.0 - shrinkage) * covariance + shrinkage * diagonal
    covariance += np.eye(covariance.shape[0]) * 1e-12
    maximum_eigenvalue = float(np.linalg.eigvalsh(covariance)[-1])
    step = 1.0 / max(2.0 * maximum_eigenvalue, 1e-12)
    weights = np.full(returns.shape[1], 1.0 / returns.shape[1], dtype=np.float64)
    for _ in range(10_000):
        updated = _project_simplex(weights - step * 2.0 * covariance @ weights)
        if np.linalg.norm(updated - weights, ord=1) < 1e-12:
            weights = updated
            break
        weights = updated
    if not np.all(np.isfinite(weights)) or abs(float(weights.sum()) - 1.0) > 1e-10:
        raise RuntimeError("minimum-variance optimization produced invalid weights")
    return weights


STRATEGIES: dict[str, Strategy] = {
    "equal_weight": equal_weight,
    "inverse_volatility": inverse_volatility,
    "minimum_variance": minimum_variance,
}
