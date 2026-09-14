"""EigenFinance: auditable walk-forward portfolio evaluation."""

from .backtest import BacktestResult, run_walk_forward
from .data import DatasetManifest, PricePanel, load_price_panel
from .protocol import EvaluationProtocol

__all__ = [
    "BacktestResult",
    "DatasetManifest",
    "EvaluationProtocol",
    "PricePanel",
    "load_price_panel",
    "run_walk_forward",
]

