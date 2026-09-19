# EigenFinance research truth

## Scope

EigenFinance is an auditable, long-only walk-forward evaluation package. It compares equal-weight,
inverse-volatility, and shrinkage minimum-variance allocations after transaction costs. It does not
claim investment profitability, trading alpha, or superiority of a learned model.

## Falsifiable hypothesis

On a prospectively declared dataset, the shrinkage minimum-variance strategy must reduce final-holdout
annualized volatility relative to equal weight without producing a worse maximum drawdown after the
declared transaction cost. Failure of either condition rejects the current risk-improvement hypothesis.

## Evidence boundary

The repository contains a complete implementation and synthetic tests, but no retained real-market
result. A scientific claim requires a licensed dataset manifest, an immutable protocol, the untouched
final-holdout output, multiplicity-aware analysis when multiple datasets are used, and independent
reproduction. Synthetic test fixtures are engineering evidence only.

## Leakage controls

- Training windows precede tests.
- A configurable embargo separates training and testing.
- The final holdout is excluded from development folds.
- Portfolio weights are computed only from each fold's training slice.
- Data hashes, fold boundaries, weights, daily returns, costs, runtime, and source hashes are retained.

## Limitations (finance-specific)

- **Survivorship bias:** the loader requires a rectangular panel, so delisted or
  intermittently missing assets are excluded before evaluation.
- **Look-ahead via adjustments:** `adjusted_close` series that were revised after
  the decision date can leak future corporate-action information unless the panel
  is point-in-time.
- **Costs vs execution:** `transaction_cost_bps` is a flat proportional cost.
  Slippage, bid-ask bounce, partial fills, and market impact are not modeled.
  Optional `--cost-sensitivity` and `--slippage-stress` grids only re-run the same
  flat-cost model at stressed bps levels; they are descriptive, not H1 endpoints.
- **Regime dependence and overfitting:** development folds may be inspected before
  the final holdout; multiplicity across datasets or protocols requires adjustment
  (see `eigenfinance.multiplicity` for Bonferroni/Holm helpers).
- **Benchmark weakness:** equal weight and inverse volatility are strong simple
  baselines for risk comparison, not exhaustive market benchmarks.

## Claim policy

Do not publish performance figures from synthetic fixtures. Do not claim alpha.
Preserve negative and inconclusive holdout outcomes in the registry.

