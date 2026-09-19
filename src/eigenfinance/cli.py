from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import platform
import sys
import tempfile
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .backtest import run_walk_forward
from .data import DatasetManifest, load_price_panel, sha256_file
from .protocol import EvaluationProtocol
from .registry import append_registry_row, git_commit, utc_timestamp
from .sensitivity import cost_sensitivity_grid, slippage_stress_grid


def _atomic_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


def _strict_json(payload: Any) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the EigenFinance walk-forward evaluation")
    parser.add_argument("--prices", type=Path, required=True)
    parser.add_argument("--dataset-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--train-periods", type=int, default=252)
    parser.add_argument("--test-periods", type=int, default=21)
    parser.add_argument("--step-periods", type=int, default=21)
    parser.add_argument("--embargo-periods", type=int, default=1)
    parser.add_argument("--final-holdout-periods", type=int, default=63)
    parser.add_argument("--transaction-cost-bps", type=float, default=5.0)
    parser.add_argument("--covariance-shrinkage", type=float, default=0.1)
    parser.add_argument(
        "--experiment-id",
        type=str,
        default="",
        help="Optional experiment id; defaults to output directory name",
    )
    parser.add_argument(
        "--registry",
        type=Path,
        default=None,
        help="Optional CSV registry path; defaults to <output>/../experiment_registry.csv",
    )
    parser.add_argument(
        "--hypothesis",
        type=str,
        default=(
            "shrinkage minimum-variance reduces final-holdout annualized volatility "
            "vs equal weight without worse max drawdown after declared costs"
        ),
    )
    parser.add_argument(
        "--cost-sensitivity",
        action="store_true",
        help=(
            "Also write descriptive cost_sensitivity.json over 0/5/10/25/50 bps "
            "for all strategies (not part of the primary H1 claim)"
        ),
    )
    parser.add_argument(
        "--slippage-stress",
        action="store_true",
        help=(
            "Also write descriptive slippage_stress.json adding 0/5/10/25 bps "
            "on top of --transaction-cost-bps (flat stress only; not market impact)"
        ),
    )
    return parser


def _evaluate_hypothesis(summary: dict[str, dict[str, float | int]]) -> str:
    """Classify the frozen holdout comparison without inventing market claims."""
    mv = summary["minimum_variance.final_holdout"]
    ew = summary["equal_weight.final_holdout"]
    mv_vol = float(mv["annual_volatility"])
    ew_vol = float(ew["annual_volatility"])
    mv_dd = float(mv["max_drawdown"])
    ew_dd = float(ew["max_drawdown"])
    if mv_vol < ew_vol and mv_dd >= ew_dd:
        return "hypothesis_supported_on_this_run"
    return "hypothesis_rejected_on_this_run"


def run(args: argparse.Namespace) -> None:
    protocol = EvaluationProtocol(
        train_periods=args.train_periods,
        test_periods=args.test_periods,
        step_periods=args.step_periods,
        embargo_periods=args.embargo_periods,
        final_holdout_periods=args.final_holdout_periods,
        transaction_cost_bps=args.transaction_cost_bps,
        covariance_shrinkage=args.covariance_shrinkage,
    )
    dataset = DatasetManifest.load(args.dataset_manifest, args.prices)
    panel = load_price_panel(args.prices)
    result = run_walk_forward(panel.returns, protocol)
    args.output.mkdir(parents=True, exist_ok=True)
    experiment_id = args.experiment_id.strip() or args.output.name
    commit = git_commit(Path(__file__).resolve().parents[2])
    hypothesis_result = _evaluate_hypothesis(result.summary)
    # Synthetic fixtures and unlicensed panels remain engineering-only.
    validity = (
        "engineering_only"
        if dataset.source_url.startswith("local://") or "synthetic" in dataset.name.lower()
        else "requires_independent_review"
    )

    rows = [asdict(record) for record in result.daily]
    header = list(rows[0])
    with tempfile.NamedTemporaryFile(
        "w",
        dir=args.output,
        prefix=".daily.",
        delete=False,
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)
        handle.flush()
        os.fsync(handle.fileno())
        temporary_daily = Path(handle.name)
    os.replace(temporary_daily, args.output / "daily_returns.csv")

    fold_payload = [
        {"fold": asdict(record.fold), "strategy": record.strategy, "weights": record.weights}
        for record in result.folds
    ]
    _atomic_text(args.output / "fold_weights.json", _strict_json(fold_payload))
    _atomic_text(args.output / "summary.json", _strict_json(result.summary))
    artifact_hashes = {
        name: sha256_file(args.output / name)
        for name in ("daily_returns.csv", "fold_weights.json", "summary.json")
    }
    source_files = sorted(Path(__file__).parent.glob("*.py"))
    manifest = {
        "format": "eigenfinance-evidence-v1",
        "experiment_id": experiment_id,
        "commit": commit,
        "seed": "deterministic_no_rng",
        "hypothesis": args.hypothesis,
        "hypothesis_result": hypothesis_result,
        "validity": validity,
        "dataset": asdict(dataset),
        "protocol": protocol.as_dict(),
        "assets": panel.assets,
        "first_date": panel.dates[0].isoformat(),
        "last_date": panel.dates[-1].isoformat(),
        "artifacts": artifact_hashes,
        "source": {
            str(path.relative_to(Path(__file__).parents[2])): sha256_file(path)
            for path in source_files
        },
        "runtime": {
            "python": sys.version,
            "platform": platform.platform(),
            "timestamp": utc_timestamp(),
        },
        "limitations": [
            "rectangular surviving-asset panels induce survivorship bias",
            "adjusted_close revisions can introduce look-ahead if not point-in-time",
            "transaction_cost_bps is a flat cost; slippage and market impact are not modeled",
            "within-fold buy-and-hold charges turnover only at rebalance boundaries",
        ],
    }
    _atomic_text(args.output / "manifest.json", _strict_json(manifest))
    if args.cost_sensitivity:
        sensitivity = {
            "format": "eigenfinance-cost-sensitivity-v1",
            "disclaimer": (
                "Descriptive only; not the primary hypothesis endpoint. "
                "Does not model slippage or market impact beyond flat bps."
            ),
            "grid": cost_sensitivity_grid(panel.returns, protocol),
        }
        _atomic_text(args.output / "cost_sensitivity.json", _strict_json(sensitivity))
    if args.slippage_stress:
        stress = {
            "format": "eigenfinance-slippage-stress-v1",
            "disclaimer": (
                "Descriptive flat extra-bps stress on top of declared transaction_cost_bps. "
                "Not a market-impact, bid-ask, or partial-fill model. Not part of H1."
            ),
            "base_transaction_cost_bps": protocol.transaction_cost_bps,
            "grid": slippage_stress_grid(panel.returns, protocol),
        }
        _atomic_text(args.output / "slippage_stress.json", _strict_json(stress))
    registry_path = args.registry or (args.output.parent / "experiment_registry.csv")
    append_registry_row(
        registry_path,
        {
            "experiment_id": experiment_id,
            "commit": commit,
            "config": _strict_json(protocol.as_dict()).strip(),
            "dataset_version": f"{dataset.name}|{dataset.file_sha256[:12]}",
            "seed": "deterministic_no_rng",
            "hypothesis": args.hypothesis,
            "metrics": _strict_json(
                {
                    key: result.summary[key]
                    for key in (
                        "equal_weight.final_holdout",
                        "inverse_volatility.final_holdout",
                        "minimum_variance.final_holdout",
                    )
                    if key in result.summary
                }
            ).strip(),
            "output_path": str(args.output.resolve()),
            "result": hypothesis_result,
            "validity": validity,
            "timestamp": utc_timestamp(),
        },
    )
    verification = hashlib.sha256(_strict_json(manifest).encode()).hexdigest()
    print(
        _strict_json(
            {
                "status": "complete",
                "experiment_id": experiment_id,
                "commit": commit,
                "validity": validity,
                "hypothesis_result": hypothesis_result,
                "manifest_sha256": verification,
                "registry": str(registry_path.resolve()),
                "summary": result.summary,
            }
        ),
        end="",
    )


def main() -> None:
    run(_parser().parse_args())


if __name__ == "__main__":
    main()

