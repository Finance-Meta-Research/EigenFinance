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

