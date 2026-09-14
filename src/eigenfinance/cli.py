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
    return parser


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
        "runtime": {"python": sys.version, "platform": platform.platform()},
    }
    _atomic_text(args.output / "manifest.json", _strict_json(manifest))
    verification = hashlib.sha256(_strict_json(manifest).encode()).hexdigest()
    print(
        _strict_json(
            {
                "status": "complete",
                "manifest_sha256": verification,
                "summary": result.summary,
            }
        ),
        end="",
    )


def main() -> None:
    run(_parser().parse_args())


if __name__ == "__main__":
    main()

