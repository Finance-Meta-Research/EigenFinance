# Integrate numerical admission with auditable comparison receipts

This combines two existing draft changes without activating the proposed study:

- Receipt PR #3 at `04c151ee810d9cb1cc42de045d90b35246dd3f1c`.
- Its updated numerical-tool base, PR #2 at
  `83c43f5ad96269dde3f647b25e40a36502191ce5`.

PR #3 was created from the earlier base `b3150dfb0c02560e226b958348684eab012bfca0`.
The newer covariance fallback and loss-underflow checks overlapped the receipt
implementation, producing two actual merge conflicts in
`development_comparison.py`. Keeping either conflict side alone would lose
validity guards or auditable predictions.

## Resolved behavior

The integrated code retains both the exact input/source/slice identities and
per-fold prediction/target matrices from #3, and the covariance overflow recovery
and genuine covariance/error-underflow rejection from #2. The one prediction
mapping supplies both the guarded loss loop and the serialized matrices, keeping
the reported error tied to the exact reported prediction. Fixed 20% shrinkage,
sample covariance `ddof=1`, prior context, nonoverlapping future windows and the
squared Frobenius metric are unchanged.

Two cross-feature regressions failed against original #3 and pass after the
integration. An artificial constant `1e308` column paired with a finite varying
column now produces a complete receipt with known covariance diagonals `(0,2)`
and `(0,8)`, recomputable error 36, and the actual executed source hash. A real
CLI check verifies that a nonzero loss that underflows produces exit 2 with no
success receipt on stdout.

The combined existing suites and new tests passed **31 tests and 13 subtests**.
Exact test/source/log hashes and environment details are in
`research/verification/receipt_integration_20261010/receipt.json`. The original
failure output is retained. The integration preserves both parents in Git
history; it updates draft #3 and does not merge either PR into main.

This remains fictional arithmetic verification of a proposed tool. No market
dataset, protected outcomes, study activation, training, paper or paid compute
was used. Source/availability verification and protected-run authorization stay
false. The reserved main README and project activation gate are unchanged.

Next action: integrate the existing draft stack after the completed bounded
independent engineering review. Founder scope confirmation, accountable scientific roles,
verified data provenance and a separately frozen study remain required before
scientific outcome generation.


## Retained review failure and covariance correction

Independent review found a concrete defect in the originally integrated #2
fallback. Alternating `[0, 0]` and `[1e154, 1e-7]` in an eight-row fixture should
give the smaller sample variance `(2/7) * (1e-7)^2`. A global normalization
scale returned a finite value about 3.75% too large. With the smaller amplitude
`1e-154`, it refused a covariance whose entries are all representable. All eight
new cases, covering both small amplitudes, both correlation signs and reversed
asset order, failed before the correction; `review_regressions.log` retains
that output. The original global-scaling helper remains visible in parent #2
at `83c43f5ad96269dde3f647b25e40a36502191ce5`.

The nonfinite `np.cov` fallback now reference-centers and scales each column
independently. `frexp`/`ldexp` restores both column units in one exponent
operation, avoiding an intermediate overflow or underflow from either ordinary
multiplication order. Normal finite `np.cov` calculations are unchanged; true
nonrepresentable covariance still rejects a receipt. This is the same sample
covariance estimator and `ddof=1`, not a change to the study or comparator.

Independent review compared all eight alternating two-point fixtures against
800-digit Decimal arithmetic from the exact represented float inputs: all
passed at relative tolerance `3e-15` and absolute tolerance zero; maximum
observed relative error was `1.11e-16`. A ninth large-constant-column fixture
returned the independently known covariance `[[0, 0], [0, 6]]`.

## Current receipt parent and final combined verification

During this work, receipt PR #3 advanced to
`803321c27b5d354855d281ace7a16e56bafc478f`. The final integration preserves that
parent's exact binary-input squared Frobenius recovery for representable
subnormal losses, its finite fold-mean reducer, new rational-oracle tests,
workflow, and appended documentation. Their implementations are unchanged.
The reviewed covariance helper supplies both the context and future matrices
used by those exact loss calculations and the serialized receipt.

The original two cross-feature tests remain. Against current #3, the large
constant-column receipt case still failed and the CLI loss-underflow guard
already passed (**1 failed, 1 passed**, retained in
`latest_base_regressions.log`). Against original #3, both failed, as recorded
above. The four #2 numerical-admission tests are retained, with only one error
message regex aligned to #3's existing `squared Frobenius loss underflow` text.

The final full proposed-tool invocation passed **43 tests and 19 subtests in
1.42 s**. Its source and inherited test hashes matched before and after the
run. Earlier 31/13, 39/13 and partial-inheritance 39/19 invocations are also
retained with their distinct scopes; none substitutes for the final full run.
Final source SHA-256:
`04fd3848e75da10a397e93da690542f8b6bbe14bc05099d4ebe51123d82e8c9a`.

The final source received a further independent integration review. AST
comparison confirmed the approved covariance helper and current #3 exact loss
and mean helpers were unchanged. Fresh combined-module checks covered the
`1e154`/`1e-154` covariance against exact Fraction arithmetic, four `2**-538`
residuals accumulating into one minimum-subnormal squared loss, and the finite
mean of two `1e308` losses. No scoped blocker remained. No independent
scientific validation is claimed. The integration commit retains current #3
as its first parent and current #2 as its second parent. No PR is merged.
