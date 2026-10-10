"""Reviewer-supplied analytic cases for mixed-scale covariance fallback."""

import numpy as np
import pytest

from development_comparison import _covariance


@pytest.mark.parametrize("small_amplitude", [1e-7, 1e-154])
@pytest.mark.parametrize("small_sign", [1., -1.])
@pytest.mark.parametrize("reverse_columns", [False, True])
def test_fallback_preserves_independently_scaled_columns(small_amplitude, small_sign, reverse_columns):
    amplitude = np.array([1e154, small_sign * small_amplitude])
    if reverse_columns:
        amplitude = amplitude[::-1]
    values = np.stack([np.zeros(2), amplitude] * 4)
    # Four observations at zero and four at a: sample covariance is
    # 8*(a/2)(a/2)^T / 7 = (2/7) aa^T. Every entry is representable.
    expected = (2. / 7.) * np.outer(amplitude, amplitude)
    actual = _covariance(values)
    np.testing.assert_allclose(actual, expected, rtol=2e-14, atol=0.)
