# EigenFinance

EigenFinance is a leakage-resistant walk-forward portfolio evaluation package. It implements three
fully executable long-only strategies—equal weight, inverse volatility, and shrinkage minimum
variance—and evaluates them on development folds plus an untouched final holdout after explicit
transaction costs.

The package is an evaluation system, not an investment recommendation. No real-market performance
claim is included in the repository. See `RESEARCH_TRUTH.md` for the falsifiable hypothesis and exact
claim boundary.

## Input contract

Prices use a rectangular long-form CSV:

```text
date,asset,adjusted_close
2024-01-02,AAA,101.25
2024-01-02,BBB,87.10
```

A JSON dataset manifest is mandatory:

```json
{
  "name": "dataset name and version",
  "source_url": "https://authoritative-source.example/dataset",
  "license": "dataset license identifier",
  "retrieved_at": "2026-09-14",
  "file_sha256": "sha256 of the CSV"
}
```

The loader rejects duplicates, missing asset/date cells, non-positive prices, malformed dates,
non-finite values, and hash mismatches.

## Install and verify

```bash
python -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python -m pytest -q
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src
```

## Run

```bash
.venv/bin/eigenfinance \
  --prices data/prices.csv \
  --dataset-manifest data/dataset.json \
  --output results/frozen-run \
  --train-periods 252 \
  --test-periods 21 \
  --step-periods 21 \
  --embargo-periods 1 \
  --final-holdout-periods 63 \
  --transaction-cost-bps 5 \
  --covariance-shrinkage 0.1 \
  --cost-sensitivity \
  --slippage-stress
```

Optional flags:

- `--cost-sensitivity` writes descriptive `cost_sensitivity.json` over 0/5/10/25/50 flat bps for all three strategies (not part of H1).
- `--slippage-stress` writes descriptive `slippage_stress.json` that adds 0/5/10/25 flat bps on top of `--transaction-cost-bps` (still not a market-impact model).

Multiplicity helpers (`eigenfinance.multiplicity.bonferroni` / `holm`) are available for multi-dataset scans after protocols are frozen.

The run atomically writes raw daily returns, per-fold portfolio weights, summary metrics, artifact
hashes, source hashes, the complete protocol, runtime metadata, and dataset provenance.
