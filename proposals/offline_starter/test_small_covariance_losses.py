"""Independent rational oracles for small but distinguishable covariance errors."""
from fractions import Fraction
import unittest

from development_comparison import compare


class SmallCovarianceLossTests(unittest.TestCase):
    def record(self, assets=16, scale=1e-81, extra_fold=False):
        values = [[0.0] * assets, [scale] * assets, [0.0] * assets, [0.0] * assets]
        if extra_fold:
            values.extend([[0.0] * assets, [scale] * assets])
        return {'evaluation_mode': 'development', 'source': 'fictional numeric fixture',
                'assets': [str(i) for i in range(assets)], 'train_rows': 2, 'horizon_rows': 2,
                'rows': [{'date': f'2020-01-{i+1:02d}', 'returns': v} for i, v in enumerate(values)]}

    def test_subnormal_total_loss_survives_per_entry_squared_underflow(self):
        result = compare(self.record())
        fold = result['folds'][0]
        for name, matrix in fold['predicted_covariance'].items():
            target = fold['realized_covariance']
            expected = float(sum(((Fraction(a) - Fraction(b))**2
                                  for ra, rb in zip(matrix, target) for a, b in zip(ra, rb)), Fraction()))
            with self.subTest(method=name):
                self.assertGreater(expected, 0)
                self.assertEqual(fold['squared_frobenius_error'][name], expected)

    def test_fold_mean_does_not_discard_subnormal_contributions_before_sum(self):
        result = compare(self.record(extra_fold=True))
        for name, actual in result['mean_squared_frobenius_error'].items():
            expected = float(sum((Fraction(f['squared_frobenius_error'][name])
                                  for f in result['folds']), Fraction()) / len(result['folds']))
            with self.subTest(method=name):
                self.assertGreater(expected, 0)
                self.assertEqual(actual, expected)

    def test_unrepresentable_nonzero_loss_is_refused_not_reported_as_perfect(self):
        with self.assertRaisesRegex(ValueError, 'underflow'):
            compare(self.record(assets=2, scale=1e-90))

    def test_true_identical_covariances_keep_zero_error(self):
        result = compare(self.record(scale=0.0))
        self.assertEqual(set(result['mean_squared_frobenius_error'].values()), {0.0})


if __name__ == '__main__':
    unittest.main()
