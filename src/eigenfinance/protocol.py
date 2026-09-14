from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class EvaluationProtocol:
    train_periods: int = 252
    test_periods: int = 21
    step_periods: int = 21
    embargo_periods: int = 1
    final_holdout_periods: int = 63
    annualization: int = 252
    transaction_cost_bps: float = 5.0
    covariance_shrinkage: float = 0.1

    def __post_init__(self) -> None:
        positive = {
            "train_periods": self.train_periods,
            "test_periods": self.test_periods,
            "step_periods": self.step_periods,
            "final_holdout_periods": self.final_holdout_periods,
            "annualization": self.annualization,
        }
        invalid = {key: value for key, value in positive.items() if value <= 0}
        if invalid:
            raise ValueError(f"protocol values must be positive: {invalid}")
        if self.embargo_periods < 0:
            raise ValueError("embargo_periods must be non-negative")
        if self.transaction_cost_bps < 0:
            raise ValueError("transaction_cost_bps must be non-negative")
        if not 0.0 <= self.covariance_shrinkage <= 1.0:
            raise ValueError("covariance_shrinkage must be in [0, 1]")

    def as_dict(self) -> dict[str, int | float]:
        return asdict(self)


@dataclass(frozen=True)
class Fold:
    fold_id: str
    train_start: int
    train_stop: int
    test_start: int
    test_stop: int
    final: bool


def build_folds(return_count: int, protocol: EvaluationProtocol) -> tuple[Fold, ...]:
    development_stop = return_count - protocol.final_holdout_periods
    minimum = protocol.train_periods + protocol.embargo_periods + protocol.test_periods
    if development_stop < minimum:
        raise ValueError(
            f"insufficient return observations: need at least "
            f"{minimum + protocol.final_holdout_periods}, got {return_count}"
        )
    folds: list[Fold] = []
    test_start = protocol.train_periods + protocol.embargo_periods
    index = 0
    while test_start + protocol.test_periods <= development_stop:
        folds.append(
            Fold(
                fold_id=f"development-{index:03d}",
                train_start=test_start - protocol.embargo_periods - protocol.train_periods,
                train_stop=test_start - protocol.embargo_periods,
                test_start=test_start,
                test_stop=test_start + protocol.test_periods,
                final=False,
            )
        )
        index += 1
        test_start += protocol.step_periods
    final_test_start = return_count - protocol.final_holdout_periods
    final_train_stop = final_test_start - protocol.embargo_periods
    folds.append(
        Fold(
            fold_id="final-holdout",
            train_start=max(0, final_train_stop - protocol.train_periods),
            train_stop=final_train_stop,
            test_start=final_test_start,
            test_stop=return_count,
            final=True,
        )
    )
    return tuple(folds)

