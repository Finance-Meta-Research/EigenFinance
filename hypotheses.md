# Hypotheses

## H1 — risk improvement (primary)

On a prospectively selected dataset with a locked protocol, the shrinkage
minimum-variance strategy's final-holdout annualized volatility is strictly lower
than equal weight, and its maximum drawdown is not worse (max drawdown closer to
zero or equal), after the declared `transaction_cost_bps`.

- **Accept only if** both conditions hold on the untouched final holdout.
- **Reject if** either condition fails.
- **Not eligible** on synthetic fixtures (`validity=engineering_only`).

## H0 — null

No joint risk improvement versus equal weight under the locked protocol and costs.

## Secondary comparisons (descriptive only)

Inverse-volatility versus equal weight is reported for context. It is not part of
the primary decision rule and must not be used for cherry-picked claims.
