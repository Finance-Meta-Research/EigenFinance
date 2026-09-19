from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pytest

from eigenfinance.backtest import run_walk_forward
from eigenfinance.data import DatasetManifest, load_price_panel
from eigenfinance.protocol import EvaluationProtocol, build_folds
from eigenfinance.strategies import STRATEGIES, minimum_variance


def write_prices(path: Path, periods: int = 90) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["date", "asset", "adjusted_close"])
        for index in range(periods):
            current = date(2020, 1, 1) + timedelta(days=index)
            writer.writerow([current.isoformat(), "AAA", 100.0 * (1.001**index)])
            writer.writerow(
                [
                    current.isoformat(),
                    "BBB",
                    80.0 * (1.0005**index) * (1 + 0.002 * np.sin(index)),
                ]
            )
            writer.writerow(
                [
                    current.isoformat(),
                    "CCC",
                    60.0 * (1.0008**index) * (1 + 0.001 * np.cos(index)),
                ]
            )


def test_loader_is_sorted_and_computes_returns(tmp_path: Path) -> None:
    path = tmp_path / "prices.csv"
    write_prices(path)
    panel = load_price_panel(path)
    assert panel.assets == ("AAA", "BBB", "CCC")
    assert panel.adjusted_close.shape == (90, 3)
    assert panel.returns.shape == (89, 3)
    assert np.all(np.isfinite(panel.returns))


def test_loader_rejects_duplicate_and_incomplete_panels(tmp_path: Path) -> None:
    duplicate = tmp_path / "duplicate.csv"
    duplicate.write_text(
        "date,asset,adjusted_close\n2020-01-01,A,1\n2020-01-01,A,2\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="duplicate"):
        load_price_panel(duplicate)
    incomplete = tmp_path / "incomplete.csv"
    incomplete.write_text(
        "date,asset,adjusted_close\n2020-01-01,A,1\n2020-01-01,B,2\n2020-01-02,A,1\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="not rectangular"):
        load_price_panel(incomplete)


def test_manifest_is_fail_closed(tmp_path: Path) -> None:
    prices = tmp_path / "prices.csv"
    write_prices(prices)
    manifest = tmp_path / "dataset.json"
    manifest.write_text(
        json.dumps(
            {
                "name": "synthetic-test-only",
                "source_url": "local://generated-test-fixture",
                "license": "CC0-1.0",
                "retrieved_at": "2026-09-14",
                "file_sha256": hashlib.sha256(prices.read_bytes()).hexdigest(),
            }
        ),
        encoding="utf-8",
    )
    loaded = DatasetManifest.load(manifest, prices)
    assert loaded.name == "synthetic-test-only"
    assert loaded.adjustment_policy == "adjusted_close_risk_accepted"
    prices.write_text(prices.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="hash mismatch"):
        DatasetManifest.load(manifest, prices)


def test_manifest_rejects_unknown_adjustment_policy(tmp_path: Path) -> None:
    prices = tmp_path / "prices.csv"
    write_prices(prices)
    manifest = tmp_path / "dataset.json"
    manifest.write_text(
        json.dumps(
            {
                "name": "synthetic-test-only",
                "source_url": "local://generated-test-fixture",
                "license": "CC0-1.0",
                "retrieved_at": "2026-09-14",
                "file_sha256": hashlib.sha256(prices.read_bytes()).hexdigest(),
                "adjustment_policy": "look_ahead_ok",
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="adjustment_policy"):
        DatasetManifest.load(manifest, prices)


def test_manifest_accepts_point_in_time_policy(tmp_path: Path) -> None:
    prices = tmp_path / "prices.csv"
    write_prices(prices)
    manifest = tmp_path / "dataset.json"
    manifest.write_text(
        json.dumps(
            {
                "name": "synthetic-test-only",
                "source_url": "local://generated-test-fixture",
                "license": "CC0-1.0",
                "retrieved_at": "2026-09-14",
                "file_sha256": hashlib.sha256(prices.read_bytes()).hexdigest(),
                "adjustment_policy": "point_in_time",
            }
        ),
        encoding="utf-8",
    )
    loaded = DatasetManifest.load(manifest, prices)
    assert loaded.adjustment_policy == "point_in_time"


def test_folds_enforce_embargo_and_final_lock() -> None:
    protocol = EvaluationProtocol(
        train_periods=20,
        test_periods=5,
        step_periods=5,
        embargo_periods=2,
        final_holdout_periods=10,
    )
    folds = build_folds(89, protocol)
    assert folds[-1].final
    assert folds[-1].test_start == 79
    for fold in folds:
        assert fold.train_stop + 2 <= fold.test_start
    assert all(not fold.final for fold in folds[:-1])


def test_all_strategies_return_long_only_simplex_weights() -> None:
    rng = np.random.default_rng(17)
    returns = rng.normal(0.0002, 0.01, size=(100, 5))
    for strategy in STRATEGIES.values():
        weights = strategy(returns, 0.1)
        assert np.all(weights >= 0)
        assert weights.sum() == pytest.approx(1.0)


def test_minimum_variance_reduces_variance() -> None:
    rng = np.random.default_rng(4)
    returns = np.column_stack(
        [
            rng.normal(0, 0.005, 500),
            rng.normal(0, 0.02, 500),
            rng.normal(0, 0.03, 500),
        ]
    )
    weights = minimum_variance(returns, 0.1)
    equal = np.full(3, 1 / 3)
    covariance = np.cov(returns, rowvar=False)
    assert weights @ covariance @ weights < equal @ covariance @ equal


def test_walk_forward_is_deterministic_and_charges_costs() -> None:
    rng = np.random.default_rng(8)
    returns = rng.normal(0.0005, 0.01, size=(100, 4))
    free = EvaluationProtocol(20, 5, 5, 1, 10, transaction_cost_bps=0)
    costly = EvaluationProtocol(20, 5, 5, 1, 10, transaction_cost_bps=25)
    first = run_walk_forward(returns, free)
    second = run_walk_forward(returns, free)
    charged = run_walk_forward(returns, costly)
    assert first == second
    for strategy in STRATEGIES:
        costly_return = charged.summary[f"{strategy}.final_holdout"]["total_return"]
        free_return = first.summary[f"{strategy}.final_holdout"]["total_return"]
        assert isinstance(costly_return, float)
        assert isinstance(free_return, float)
        assert costly_return <= free_return


def test_cli_writes_verified_evidence(tmp_path: Path) -> None:
    prices = tmp_path / "prices.csv"
    write_prices(prices)
    dataset = tmp_path / "dataset.json"
    dataset.write_text(
        json.dumps(
            {
                "name": "synthetic-test-only",
                "source_url": "local://generated-test-fixture",
                "license": "CC0-1.0",
                "retrieved_at": "2026-09-14",
                "file_sha256": hashlib.sha256(prices.read_bytes()).hexdigest(),
            }
        ),
        encoding="utf-8",
    )
    output = tmp_path / "result"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "eigenfinance.cli",
            "--prices",
            str(prices),
            "--dataset-manifest",
            str(dataset),
            "--output",
            str(output),
            "--train-periods",
            "20",
            "--test-periods",
            "5",
            "--step-periods",
            "5",
            "--embargo-periods",
            "1",
            "--final-holdout-periods",
            "10",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(completed.stdout)["status"] == "complete"
    payload = json.loads(completed.stdout)
    assert payload["validity"] == "engineering_only"
    assert "hypothesis_result" in payload
    assert payload["commit"]
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    for name, expected in manifest["artifacts"].items():
        assert hashlib.sha256((output / name).read_bytes()).hexdigest() == expected
    assert manifest["experiment_id"] == "result"
    assert manifest["seed"] == "deterministic_no_rng"
    assert "survivorship" in " ".join(manifest["limitations"])
    registry = tmp_path / "experiment_registry.csv"
    assert registry.is_file()
    text = registry.read_text(encoding="utf-8")
    assert "experiment_id" in text
    assert "engineering_only" in text


def test_registry_append_is_stable(tmp_path: Path) -> None:
    from eigenfinance.registry import append_registry_row

    path = tmp_path / "experiment_registry.csv"
    row = {
        "experiment_id": "demo",
        "commit": "abc",
        "config": "{}",
        "dataset_version": "synthetic|deadbeef",
        "seed": "deterministic_no_rng",
        "hypothesis": "test",
        "metrics": "{}",
        "output_path": str(tmp_path),
        "result": "hypothesis_rejected_on_this_run",
        "validity": "engineering_only",
        "timestamp": "2026-09-18T00:00:00+00:00",
    }
    append_registry_row(path, row)
    append_registry_row(path, row)
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 3



def test_cost_sensitivity_grid_is_descriptive(tmp_path: Path) -> None:
    from eigenfinance.protocol import EvaluationProtocol
    from eigenfinance.sensitivity import cost_sensitivity_grid

    prices = tmp_path / "prices.csv"
    write_prices(prices, periods=120)
    panel = load_price_panel(prices)
    protocol = EvaluationProtocol(
        train_periods=40,
        test_periods=10,
        step_periods=10,
        embargo_periods=1,
        final_holdout_periods=20,
        transaction_cost_bps=5.0,
    )
    grid = cost_sensitivity_grid(panel.returns, protocol, (0.0, 5.0, 25.0))
    assert set(grid) == {"0_bps", "5_bps", "25_bps"}
    for strategy in STRATEGIES:
        assert f"{strategy}.final_holdout" in grid["5_bps"]
    with pytest.raises(ValueError, match="non-empty"):
        cost_sensitivity_grid(panel.returns, protocol, ())
    with pytest.raises(ValueError, match="non-negative"):
        cost_sensitivity_grid(panel.returns, protocol, (-1.0,))


def test_slippage_stress_grid_adds_flat_extra_bps(tmp_path: Path) -> None:
    from eigenfinance.protocol import EvaluationProtocol
    from eigenfinance.sensitivity import slippage_stress_grid

    prices = tmp_path / "prices.csv"
    write_prices(prices, periods=120)
    panel = load_price_panel(prices)
    protocol = EvaluationProtocol(
        train_periods=40,
        test_periods=10,
        step_periods=10,
        embargo_periods=1,
        final_holdout_periods=20,
        transaction_cost_bps=5.0,
    )
    grid = slippage_stress_grid(panel.returns, protocol, (0.0, 10.0))
    assert set(grid) == {"base_5_plus_0_bps", "base_5_plus_10_bps"}
    zero = grid["base_5_plus_0_bps"]["equal_weight.final_holdout"]["total_return"]
    stressed = grid["base_5_plus_10_bps"]["equal_weight.final_holdout"]["total_return"]
    assert isinstance(zero, float) and isinstance(stressed, float)
    assert stressed <= zero


def test_multiplicity_bonferroni_and_holm() -> None:
    from eigenfinance.multiplicity import bonferroni, holm

    raw = {"a": 0.01, "b": 0.04, "c": 0.20}
    bonf = {row.label: row.adjusted_p for row in bonferroni(raw)}
    assert bonf["a"] == pytest.approx(0.03)
    assert bonf["b"] == pytest.approx(0.12)
    assert bonf["c"] == pytest.approx(0.60)
    holm_rows = {row.label: row.adjusted_p for row in holm(raw)}
    assert holm_rows["a"] == pytest.approx(0.03)
    assert holm_rows["b"] == pytest.approx(0.08)
    assert holm_rows["c"] == pytest.approx(0.20)
    with pytest.raises(ValueError, match="non-empty"):
        bonferroni({})
    with pytest.raises(ValueError, match=r"\[0, 1\]"):
        holm({"bad": 1.5})


def test_cli_writes_sensitivity_artifacts(tmp_path: Path) -> None:
    prices = tmp_path / "prices.csv"
    write_prices(prices, periods=120)
    dataset = tmp_path / "dataset.json"
    dataset.write_text(
        json.dumps(
            {
                "name": "synthetic-test-only",
                "source_url": "local://generated-test-fixture",
                "license": "CC0-1.0",
                "retrieved_at": "2026-09-14",
                "file_sha256": hashlib.sha256(prices.read_bytes()).hexdigest(),
            }
        ),
        encoding="utf-8",
    )
    output = tmp_path / "result-stress"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "eigenfinance.cli",
            "--prices",
            str(prices),
            "--dataset-manifest",
            str(dataset),
            "--output",
            str(output),
            "--train-periods",
            "40",
            "--test-periods",
            "10",
            "--step-periods",
            "10",
            "--embargo-periods",
            "1",
            "--final-holdout-periods",
            "20",
            "--cost-sensitivity",
            "--slippage-stress",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(completed.stdout)["status"] == "complete"
    cost = json.loads((output / "cost_sensitivity.json").read_text(encoding="utf-8"))
    slip = json.loads((output / "slippage_stress.json").read_text(encoding="utf-8"))
    assert cost["format"] == "eigenfinance-cost-sensitivity-v1"
    assert slip["format"] == "eigenfinance-slippage-stress-v1"
    assert "inverse_volatility.final_holdout" in cost["grid"]["5_bps"]
