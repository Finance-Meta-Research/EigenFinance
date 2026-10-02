import unittest
from covariance_audit import audit


class CovarianceAuditTests(unittest.TestCase):
    def test_known_diagonal(self):
        r = audit([[1, 0], [0, 4]])
        self.assertEqual(r["eigenvalues"], [1, 4])
        self.assertEqual(r["spectral_condition_number"], 4)

    def test_singular_psd(self):
        r = audit([[1, 1], [1, 1]])
        self.assertTrue(r["positive_semidefinite"])
        self.assertFalse(r["positive_definite"])
        self.assertIsNone(r["spectral_condition_number"])

    def test_indefinite(self):
        self.assertFalse(audit([[1, 2], [2, 1]])["positive_semidefinite"])

    def test_zero_matrix(self):
        r = audit([[0, 0], [0, 0]])
        self.assertTrue(r["positive_semidefinite"])
        self.assertIsNone(r["spectral_condition_number"])

    def test_invalid_matrix(self):
        for matrix in [[], [[1, 2]], [[True]], [[True, 0], [0, 1]], [["1"]], [[float("nan")]], [[1, 1], [0, 1]]]:
            with self.subTest(matrix=matrix), self.assertRaises(ValueError):
                audit(matrix)

    def test_scale_invariance(self):
        r = audit([[1e-12, 0], [0, -1e-12]])
        self.assertFalse(r["positive_semidefinite"])

    def test_smallest_negative_float_does_not_disappear(self):
        self.assertFalse(audit([[-5e-324]])["positive_semidefinite"])

    def test_smallest_positive_float_remains_positive(self):
        r = audit([[5e-324]])
        self.assertTrue(r["positive_definite"])
        self.assertEqual(r["spectral_condition_number"], 1)

    def test_extreme_asymmetry_is_rejected(self):
        with self.assertRaises(ValueError):
            audit([[1e308, 1e308], [-1e308, 1e308]])


if __name__ == "__main__":
    unittest.main()
