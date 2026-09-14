from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

from .protocol import EvaluationProtocol, Fold, build_folds
from .strategies import STRATEGIES

FloatArray = npt.NDArray[np.float64]


@dataclass(frozen=True)
class DailyRecord:
    fold_id: str
    strategy: str
    return_index: int
    net_return: float
    turnover: float
    final: bool


@dataclass(frozen=True)
class FoldRecord:
    fold: Fold
    strategy: str
    weights: tuple[float, ...]


@dataclass(frozen=True)
class BacktestResult:
    daily: tuple[DailyRecord, ...]
    folds: tuple[FoldRecord, ...]
    summary: dict[str, dict[str, float | int]]


def _simulate(
    test_returns: FloatArray,
    target: FloatArray,
    previous: FloatArray,
    cost: float,
) -> tuple[FloatArray, FloatArray, FloatArray]:
    weights = previous.copy()
    net: list[float] = []
    turnovers: list[float] = []
    for day, asset_returns in enumerate(test_returns):
        turnover = float(np.abs(target - weights).sum()) if day == 0 else 0.0
        weights = target.copy() if day == 0 else weights
        gross = float(weights @ asset_returns)
        net_return = gross - cost * turnover
        if net_return <= -1.0:
            raise ValueError("portfolio lost 100% or more in one period")
        grown = weights * (1.0 + asset_returns)
        denominator = float(grown.sum())
        if denominator <= 0 or not np.isfinite(denominator):
            raise ValueError("portfolio weights became invalid")
        weights = grown / denominator
        net.append(net_return)
        turnovers.append(turnover)
    return np.asarray(net), np.asarray(turnovers), weights


def _metrics(
    values: FloatArray, turnovers: FloatArray, annualization: int
) -> dict[str, float | int]:
    if values.size == 0 or not np.all(np.isfinite(values)):
        raise ValueError("metrics require finite non-empty returns")
    wealth = np.cumprod(1.0 + values)
    years = values.size / annualization
    annual_return = float(wealth[-1] ** (1.0 / years) - 1.0)
    annual_volatility = (
        float(np.std(values, ddof=1) * np.sqrt(annualization)) if values.size > 1 else 0.0
    )
    sharpe = annual_return / annual_volatility if annual_volatility > 0 else 0.0
    wealth_with_origin = np.concatenate(([1.0], wealth))
    running_max = np.maximum.accumulate(wealth_with_origin)
    drawdowns = wealth_with_origin / running_max - 1.0
    return {
        "observations": int(values.size),
        "total_return": float(wealth[-1] - 1.0),
        "annual_return": annual_return,
        "annual_volatility": annual_volatility,
        "sharpe_zero_rate": float(sharpe),
        "max_drawdown": float(drawdowns.min()),
        "total_turnover": float(turnovers.sum()),
    }


def run_walk_forward(returns: FloatArray, protocol: EvaluationProtocol) -> BacktestResult:
    if returns.ndim != 2 or not np.all(np.isfinite(returns)):
        raise ValueError("returns must be a finite [time, assets] matrix")
    folds = build_folds(returns.shape[0], protocol)
    cost = protocol.transaction_cost_bps / 10_000.0
    daily_records: list[DailyRecord] = []
    fold_records: list[FoldRecord] = []
    previous = {
        name: np.full(returns.shape[1], 1.0 / returns.shape[1]) for name in STRATEGIES
    }
    for fold in folds:
        train = returns[fold.train_start : fold.train_stop]
        test = returns[fold.test_start : fold.test_stop]
        if fold.train_stop + protocol.embargo_periods > fold.test_start:
            raise RuntimeError("fold violates embargo")
        for name, strategy in STRATEGIES.items():
            target = strategy(train, protocol.covariance_shrinkage)
            net, turnover, previous[name] = _simulate(test, target, previous[name], cost)
            fold_records.append(FoldRecord(fold, name, tuple(float(value) for value in target)))
            daily_records.extend(
                DailyRecord(
                    fold.fold_id,
                    name,
                    fold.test_start + index,
                    float(value),
                    float(turnover[index]),
                    fold.final,
                )
                for index, value in enumerate(net)
            )
    summary: dict[str, dict[str, float | int]] = {}
    for name in STRATEGIES:
        for final, label in ((False, "development"), (True, "final_holdout")):
            selected = [
                record
                for record in daily_records
                if record.strategy == name and record.final is final
            ]
            summary[f"{name}.{label}"] = _metrics(
                np.asarray([record.net_return for record in selected]),
                np.asarray([record.turnover for record in selected]),
                protocol.annualization,
            )
    return BacktestResult(tuple(daily_records), tuple(fold_records), summary)

