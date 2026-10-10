# Development covariance receipt completion — 2026-10-10

This patch extends the proposed offline covariance tools in draft PR #2.
EigenFinance main remains a reserved placeholder; the proposed charter and
scientific review/activation gates remain unchanged. No market dataset is
processed and no covariance-forecasting advantage is claimed.

## Missing audit functionality

The existing comparison calculated sample, diagonal, and fixed 20% shrinkage
predictions on common past windows, but retained only scalar errors. A reviewer
could not recompute those errors from a receipt, inspect the actual predictions,
or directly test that a future-data change left predictions unchanged. The
draft charter explicitly requires per-fold predictions and source/configuration
identities for a complete implementation.

Each fold now retains all three predicted covariance matrices, its common
future-window realized sample covariance, the existing squared Frobenius errors,
and method-minus-sample paired error differences. Negative paired differences
mean lower error than the sample comparator on that same target. This is a
descriptive comparison, not a significance statement; future sample covariance
remains a noisy target.

Receipts also bind canonical sorted-key JSON input, each context/evaluation row
slice, and the executed comparison source by SHA-256. They record NumPy version
and explicit estimator/metric conventions (sample covariance `ddof=1`, fixed
0.2 diagonal shrinkage, unnormalized squared Frobenius error). Input key order
does not affect identity. Even a changed unused tail changes full-input identity
while preserving unaffected fold calculations.

Estimator equations, common information sets, rolling windows, disjoint
evaluation windows, shrinkage strength, tail exclusion, and existing error
aggregations are unchanged. The matrix diagnostic implementation is unchanged.
The new schema is `eigenfinance.development-covariance.v2` because the receipt
contract has expanded. Hashes bind supplied records; they do not authenticate
availability, licensing, source, or study permission. Those flags remain false,
and protected mode remains refused.

## Execute and verify

From `proposals/offline_starter`, with NumPy installed:

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  python -m unittest discover -v
python development_comparison.py development.json
```

The full local suite passed **21 tests in 0.332 seconds**, including all fourteen
existing cases. Seven new tests retain independently known two-asset matrices,
recompute every error from receipt matrices, check signed paired differences,
directly compare predictions before/after future shocks, check context shocks,
verify source/input/fold identities, preserve one-asset matrix shape, reject
nonfinite provenance, and execute the real CLI. The fictional known case retains
sample/diagonal/shrinkage squared errors of 32, 8, and 25.92; it is an arithmetic
fixture and is not an observed market result.

A new exact-source bounded CI job runs this same proposed-tool suite with NumPy
and one numeric thread. It launches no study or training, reads no protected
data, and changes no retained research result or paper. The actual hosted result
is recorded in the PR after completion.

## Second pass: distinguish small covariance errors from zero

At reviewed head `04c151ee810d9cb1cc42de045d90b35246dd3f1c`, squaring each matrix
residual before summation rounded tiny entries to zero, even when the complete
squared Frobenius error was representable. A constructed 16-asset covariance
fixture reported zero for all methods instead of approximately 6.4e-323,
5e-324 and 4.4e-323. Averaging per-fold contributions after dividing each by the
fold count could discard additional subnormal information.

The ordinary matrix-loss path is retained. Subnormal totals are recomputed by
summing exact squared binary residuals and rounding once. A nonzero loss too
small for the output dtype is refused with an explicit rescaling error instead
of being labeled perfect. Mean losses accumulate before division, retaining an
exact-rational overflow fallback and nonzero-underflow refusal. The covariance
estimators, split windows, per-fold matrices, input identity, and false source /
availability / authorization flags are unchanged. This is still a proposed,
unactivated development-only tool with no market data or effectiveness claim.

Four new `Fraction`-oracle methods produced seven failing subcases on the
reviewed source; the exact-zero control passed. The full local proposed-tool
suite passed **25 tests in 0.409 seconds**. The existing exact-source bounded CI
runs these regressions. Stored losses remain rounded binary64 output values;
the implementation does not infer economic significance from representable
numerical differences or promise arbitrary-precision covariances.

### Verify the draft source independently of PR event eligibility

The Actions API returned no workflow for published source
`0a60a4959190d165df40d568ba097dcdb592ff96`, while PR metadata reported
`mergeable: false` / `dirty`. The commit comparison independently shows its
existing stacked base `b3150dfb0c02560e226b958348684eab012bfca0` is an ancestor
(two commits ahead, zero behind), so there is no source conflict to resolve.
The bounded workflow now also accepts pushes to this exact draft branch. Its
same exact-source checkout, five-minute limit, one numeric thread and fictional
unit tests are retained. This avoids depending solely on PR event eligibility
without retargeting or merging either proposal. A prior-head green check is not
treated as validation of a later revision; final run identity is in the PR.
