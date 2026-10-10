"""Constructed cross-feature regressions for the existing two draft branches."""

import datetime as dt
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

import development_comparison as comparison


def record(values):
    return {
        "evaluation_mode": "development",
        "source": "ARTIFICIAL integration arithmetic; no market observations",
        "assets": [f"fictional-{i}" for i in range(len(values[0]))],
        "train_rows": 2,
        "horizon_rows": 2,
        "rows": [{"date": (dt.date(2020, 1, 1) + dt.timedelta(days=i)).isoformat(), "returns": value}
                 for i, value in enumerate(values)],
    }


def test_recovered_covariance_has_recomputable_receipt_matrices_and_source_binding():
    supplied = record([[1e308, 0.], [1e308, 2.], [1e308, 0.], [1e308, 4.]])
    result = comparison.compare(supplied)
    assert result["schema"] == "eigenfinance.development-covariance.v2"
    assert result["source_sha256"] == hashlib.sha256(Path(comparison.__file__).read_bytes()).hexdigest()
    fold = result["folds"][0]
    expected_sample = np.diag([0., 2.])
    expected_realized = np.diag([0., 8.])
    np.testing.assert_array_equal(fold["realized_covariance"], expected_realized)
    for method, prediction in fold["predicted_covariance"].items():
        np.testing.assert_array_equal(prediction, expected_sample)
        error = float(np.sum((np.asarray(prediction) - expected_realized) ** 2))
        assert error == 36.
        assert fold["squared_frobenius_error"][method] == error
        assert fold["paired_error_difference_vs_sample"][method] == 0.
    assert result["source_verified"] is False
    assert result["availability_verified"] is False
    assert result["protected_run_authorized"] is False


def test_cli_underflow_refuses_to_publish_a_success_receipt(tmp_path):
    supplied = record([[0.], [1e-100], [0.], [2e-100]])
    input_path = tmp_path / "artificial.json"
    input_path.write_text(json.dumps(supplied))
    completed = subprocess.run([sys.executable, comparison.__file__, str(input_path)],
                               text=True, capture_output=True, timeout=10)
    assert completed.returncode == 2
    assert completed.stdout == ""
    assert "underflow" in completed.stderr
    with pytest.raises(ValueError, match="underflow"):
        comparison.compare(supplied)
