# Project status — EigenFinance (FinanceMeta Lab)

Last verified: 2026-09-18

## Objective

Provide a leakage-resistant, auditable walk-forward evaluation system for long-only
equal-weight, inverse-volatility, and shrinkage minimum-variance portfolios after
declared transaction costs — without asserting real-market alpha.

## Research question

See `research-question.md`. Primary endpoint: final-holdout volatility improvement
versus equal weight without worse max drawdown after costs.

## Lifecycle stage

**Engineering-complete / science-gated.** Implementation and tests are verified.
Real-market evaluation has **not** started pending a licensed prospective dataset.

## Result status

| Component | Classification |
|---|---|
| Package install + CLI evidence writer | **VERIFIED COMPLETE** |
| Walk-forward folds, embargo, final holdout | **VERIFIED COMPLETE** |
| Transaction-cost charging | **VERIFIED COMPLETE** |
| Experiment registry + commit provenance | **VERIFIED COMPLETE** (added this session) |
| Real-market H1 evaluation | **NOT STARTED** |
| Paper performance claims | **INVALID** if present; none retained |

## Work completed this session

- Verified 8→9 tests, Ruff, and strict Mypy.
- Added `registry.py`, CLI registry append, commit/seed/validity/limitations in manifests.
- Added `research-question.md`, `hypotheses.md`, `results.md`, `SECURITY_AUDIT.md`.
- Expanded finance-specific limitations in `RESEARCH_TRUTH.md`.
- Removed `FinanceMeta-Landing/.env.local` (`VERCEL_OIDC_TOKEN`); rotation may be required.

## Remaining blockers

1. Licensed, point-in-time (or explicitly risk-accepted adjusted) price panel + manifest.
2. Independent reproduction of any future non-engineering registry row.
3. Operator confirmation that the removed Vercel OIDC token was rotated if exposed.

## Files changed this session

- `src/eigenfinance/registry.py` (new)
- `src/eigenfinance/cli.py`
- `tests/test_eigenfinance.py`
- `RESEARCH_TRUTH.md`
- `research-question.md`, `hypotheses.md`, `results.md`, `SECURITY_AUDIT.md`, `PROJECT_STATUS.md`

## Validation commands

```bash
cd /Volumes/PRO-BLADE/GitHub-Every-Repo/EigenFinance
.venv/bin/python -m pytest -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src
```

Observed: **9 passed**; Ruff clean after autofix; Mypy clean.

## Next highest-value tasks

1. **P0** — Acquire/declare a licensed dataset; freeze protocol; run one holdout study; register it.
2. **P1** — Optional point-in-time adjustment mode or explicit `adjustment_policy` manifest field.
3. **P2** — Slippage stress grid as descriptive sensitivity (not primary H1).
4. **P3** — Multi-dataset multiplicity correction helper.
