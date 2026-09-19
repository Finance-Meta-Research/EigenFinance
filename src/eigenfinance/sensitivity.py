"""Descriptive transaction-cost and slippage stress helpers (not primary H1)."""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import numpy.typing as npt

from .backtest import run_walk_forward
from .protocol import EvaluationProtocol
from .strategies import STRATEGIES

FloatArray = npt.NDArray[np.float64]

# Final-holdout summary keys for every registered strategy (descriptive grids).
_HOLDING_KEYS = tuple(f"{name}.final_holdout" for name in STRATEGIES)


def _holdout_slice(
    summary: dict[str, dict[str, float | int]],
) -> dict[str, dict[str, float | int]]:
    return {key: summary[key] for key in _HOLDING_KEYS if key in summary}


def cost_sensitivity_grid(
    returns: FloatArray,
    protocol: EvaluationProtocol,
    cost_bps_grid: tuple[float, ...] = (0.0, 5.0, 10.0, 25.0, 50.0),
) -> dict[str, dict[str, dict[str, float | int]]]:
    """Re-run walk-forward at each flat cost level; results are descriptive only."""
    if not cost_bps_grid:
        raise ValueError("cost_bps_grid must be non-empty")
    if any(cost < 0 for cost in cost_bps_grid):
        raise ValueError("cost_bps_grid values must be non-negative")
    payload: dict[str, dict[str, dict[str, float | int]]] = {}
    for cost in cost_bps_grid:
        varied = replace(protocol, transaction_cost_bps=float(cost))
        result = run_walk_forward(returns, varied)
        payload[f"{cost:g}_bps"] = _holdout_slice(result.summary)
    return payload


def slippage_stress_grid(
    returns: FloatArray,
    protocol: EvaluationProtocol,
    extra_slippage_bps_grid: tuple[float, ...] = (0.0, 5.0, 10.0, 25.0),
) -> dict[str, dict[str, dict[str, float | int]]]:
    """Stress declared costs by adding flat extra slippage bps (descriptive only).

    This does **not** model bid-ask bounce, partial fills, or market impact.
    Extra bps are added to ``protocol.transaction_cost_bps`` and applied as the
    same proportional turnover charge already used by the backtest.
    """
    if not extra_slippage_bps_grid:
        raise ValueError("extra_slippage_bps_grid must be non-empty")
    if any(extra < 0 for extra in extra_slippage_bps_grid):
        raise ValueError("extra_slippage_bps_grid values must be non-negative")
    base = float(protocol.transaction_cost_bps)
    payload: dict[str, dict[str, dict[str, float | int]]] = {}
    for extra in extra_slippage_bps_grid:
        effective = base + float(extra)
        varied = replace(protocol, transaction_cost_bps=effective)
        result = run_walk_forward(returns, varied)
        payload[f"base_{base:g}_plus_{extra:g}_bps"] = _holdout_slice(result.summary)
    return payload
