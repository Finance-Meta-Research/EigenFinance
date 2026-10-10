import copy
import unittest
from development_comparison import compare


class DevelopmentComparisonTests(unittest.TestCase):
    def record(self):
        return {"evaluation_mode": "development", "source": "fictional arithmetic fixture",
                "assets": ["a", "b"], "train_rows": 2, "horizon_rows": 2,
                "rows": [{"date": f"2020-01-{i+1:02d}", "returns": v}
                         for i, v in enumerate([[0, 0], [2, 2], [0, 0], [2, -2], [1, 1]])]}

    def test_independent_known_covariance_errors(self):
        r = compare(self.record())
        self.assertEqual(r["mean_squared_frobenius_error"]["sample"], 32)
        self.assertEqual(r["mean_squared_frobenius_error"]["diagonal"], 8)
        self.assertAlmostEqual(r["mean_squared_frobenius_error"]["fixed_shrinkage_0_2"], 25.92)
        self.assertEqual(r["unused_tail_rows"], 1)

    def test_future_does_not_change_context_predictions(self):
        r = self.record()
        r["rows"][2]["returns"] = [0, 0]
        r["rows"][3]["returns"] = [0, 0]
        result = compare(r)
        self.assertEqual(result["mean_squared_frobenius_error"]["sample"], 16)
        self.assertEqual(result["folds"][0]["context_end"], "2020-01-02")
        self.assertEqual(result["folds"][0]["evaluation_start"], "2020-01-03")

    def test_protected_mode_refused(self):
        r = self.record()
        r["evaluation_mode"] = "protected"
        with self.assertRaises(ValueError):
            compare(r)

    def test_invalid_contracts(self):
        base = self.record()
        variants = []
        for key, value in [("train_rows", True), ("horizon_rows", 1), ("assets", ["a", " A "]), ("source", "")]:
            r = copy.deepcopy(base)
            r[key] = value
            variants.append(r)
        r = copy.deepcopy(base)
        r["rows"][1]["date"] = r["rows"][0]["date"]
        variants.append(r)
        r = copy.deepcopy(base)
        r["rows"][0]["returns"] = [True, 0]
        variants.append(r)
        for r in variants:
            with self.subTest(record=r), self.assertRaises(ValueError):
                compare(r)

    def test_no_authorization_or_source_certification(self):
        result = compare(self.record())
        self.assertFalse(result["protected_run_authorized"])
        self.assertFalse(result["source_verified"])

    def test_nonconstant_covariance_cannot_underflow_to_zero(self):
        r = self.record()
        for row in r["rows"]:
            row["returns"] = [v * 1e-200 for v in row["returns"]]
        with self.assertRaisesRegex(ValueError, "covariance underflow"):
            compare(r)

    def test_unequal_covariances_cannot_report_exact_zero_error(self):
        r = self.record()
        for row in r["rows"]:
            row["returns"] = [v * 1e-100 for v in row["returns"]]
        with self.assertRaisesRegex(ValueError, "nonzero covariance error underflowed"):
            compare(r)

    def test_small_representable_nonzero_error_is_preserved(self):
        r = self.record()
        for row in r["rows"]:
            row["returns"] = [v * 1e-75 for v in row["returns"]]
        error = compare(r)["mean_squared_frobenius_error"]["sample"]
        self.assertGreater(error, 0)
        self.assertAlmostEqual(error / 3.2e-299, 1.0)

    def test_genuine_zero_error_and_constant_observations_remain_valid(self):
        equal_covariance = self.record()
        equal_covariance["rows"][3]["returns"] = [2, 2]
        self.assertEqual(compare(equal_covariance)["mean_squared_frobenius_error"]["sample"], 0)
        constant = self.record()
        for row in constant["rows"]:
            row["returns"] = [1e-200, 2e-200]
        self.assertTrue(all(error == 0 for error in compare(constant)["mean_squared_frobenius_error"].values()))


if __name__ == "__main__":
    unittest.main()
