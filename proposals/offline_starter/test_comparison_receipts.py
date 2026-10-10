import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from development_comparison import compare


class ComparisonReceiptTests(unittest.TestCase):
    def record(self):
        return {"evaluation_mode": "development", "source": "fictional receipt fixture",
                "assets": ["a", "b"], "train_rows": 2, "horizon_rows": 2,
                "rows": [{"date": f"2020-01-{i+1:02d}", "returns": values}
                         for i, values in enumerate([[0, 0], [2, 2], [0, 0], [2, -2], [1, 1]])]}

    def digest(self, value):
        return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()

    def test_retains_independently_known_matrices_and_recomputable_errors(self):
        result = compare(self.record())
        fold = result["folds"][0]
        self.assertEqual(fold["predicted_covariance"]["sample"], [[2, 2], [2, 2]])
        self.assertEqual(fold["predicted_covariance"]["diagonal"], [[2, 0], [0, 2]])
        self.assertEqual(fold["predicted_covariance"]["fixed_shrinkage_0_2"], [[2, 1.6], [1.6, 2]])
        self.assertEqual(fold["realized_covariance"], [[2, -2], [-2, 2]])
        for name, prediction in fold["predicted_covariance"].items():
            independent = sum((prediction[i][j] - fold["realized_covariance"][i][j])**2 for i in range(2) for j in range(2))
            self.assertAlmostEqual(fold["squared_frobenius_error"][name], independent)
            self.assertAlmostEqual(fold["paired_error_difference_vs_sample"][name], independent - 32)
        self.assertEqual(fold["paired_error_difference_vs_sample"]["diagonal"], -24)

    def test_future_shock_preserves_actual_predictions_and_context_identity(self):
        original = self.record()
        before = compare(original)["folds"][0]
        shocked = copy.deepcopy(original)
        shocked["rows"][2]["returns"] = [10, 20]
        shocked["rows"][3]["returns"] = [30, -10]
        after = compare(shocked)["folds"][0]
        self.assertEqual(before["predicted_covariance"], after["predicted_covariance"])
        self.assertEqual(before["context_sha256"], after["context_sha256"])
        self.assertNotEqual(before["realized_covariance"], after["realized_covariance"])
        self.assertNotEqual(before["evaluation_sha256"], after["evaluation_sha256"])

    def test_context_shock_changes_predictions_but_not_realized_target(self):
        original = self.record()
        before = compare(original)["folds"][0]
        original["rows"][1]["returns"] = [4, 8]
        after = compare(original)["folds"][0]
        self.assertNotEqual(before["predicted_covariance"], after["predicted_covariance"])
        self.assertNotEqual(before["context_sha256"], after["context_sha256"])
        self.assertEqual(before["realized_covariance"], after["realized_covariance"])
        self.assertEqual(before["evaluation_sha256"], after["evaluation_sha256"])

    def test_input_source_and_fold_identities_are_bound(self):
        record = self.record()
        result = compare(record)
        self.assertEqual(result["input_sha256"], self.digest(record))
        self.assertEqual(result["folds"][0]["context_sha256"], self.digest(record["rows"][:2]))
        self.assertEqual(result["folds"][0]["evaluation_sha256"], self.digest(record["rows"][2:4]))
        self.assertEqual(result["source_sha256"], hashlib.sha256(Path(__file__).with_name("development_comparison.py").read_bytes()).hexdigest())
        reordered = {key: record[key] for key in reversed(list(record))}
        self.assertEqual(result["input_sha256"], compare(reordered)["input_sha256"])
        changed = copy.deepcopy(record)
        changed["rows"][-1]["returns"] = [99, 99]
        self.assertEqual(result["folds"], compare(changed)["folds"])
        self.assertNotEqual(result["input_sha256"], compare(changed)["input_sha256"])

    def test_one_asset_matrices_keep_two_dimensions(self):
        record = self.record()
        record["assets"] = ["a"]
        for row in record["rows"]:
            row["returns"] = [row["returns"][0]]
        fold = compare(record)["folds"][0]
        self.assertEqual(fold["realized_covariance"], [[2]])
        self.assertEqual(fold["predicted_covariance"]["sample"], [[2]])

    def test_nonfinite_provenance_is_rejected(self):
        record = self.record()
        record["metadata"] = float("nan")
        with self.assertRaises(ValueError):
            compare(record)

    def test_real_cli_emits_strict_recomputable_development_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "development.json"
            path.write_text(json.dumps(self.record()))
            script = Path(__file__).with_name("development_comparison.py")
            run = subprocess.run([sys.executable, str(script), str(path)], capture_output=True, text=True, timeout=30)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            result = json.loads(run.stdout)
            self.assertEqual(result, compare(self.record()))
            self.assertEqual(result["estimator_configuration"]["shrinkage_weight"], 0.2)
            self.assertFalse(result["source_verified"])
            self.assertFalse(result["availability_verified"])
            self.assertFalse(result["protected_run_authorized"])


if __name__ == "__main__":
    unittest.main()
