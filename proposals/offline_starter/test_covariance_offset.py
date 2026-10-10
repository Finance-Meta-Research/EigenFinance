"""Fictional arithmetic cases for representable covariance after mean overflow."""

import unittest

import numpy as np

from development_comparison import _covariance, compare


class CovarianceOffsetTests(unittest.TestCase):
    def test_huge_constant_has_zero_covariance(self):
        np.testing.assert_array_equal(_covariance(np.full((4, 1), 1e308)), [[0.0]])

    def test_constant_asset_offset_preserves_other_asset_variance(self):
        values = np.array([[1e308, 1], [1e308, 3], [1e308, 5], [1e308, 7]])
        np.testing.assert_allclose(_covariance(values), [[0, 0], [0, 20/3]])

    def test_real_comparator_emits_finite_zero_error_on_constant_fixture(self):
        record = {"evaluation_mode": "development", "source": "fictional arithmetic fixture",
                  "assets": ["constant"], "train_rows": 2, "horizon_rows": 2,
                  "rows": [{"date": f"2020-01-0{i+1}", "returns": [1e308]} for i in range(4)]}
        result = compare(record)
        self.assertTrue(all(value == 0 for value in result["mean_squared_frobenius_error"].values()))
        self.assertFalse(result["source_verified"])
        self.assertFalse(result["protected_run_authorized"])

    def test_genuine_overflow_is_still_rejected(self):
        with self.assertRaisesRegex(ValueError, "overflow"):
            _covariance(np.array([[-1e308], [1e308]]))
