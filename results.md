# Results

## Status of retained scientific results

| Result class | Status | Notes |
|---|---|---|
| Real-market walk-forward study | **NOT STARTED** | No licensed prospective panel is checked in |
| Synthetic CLI/fixture runs | **VALIDATED** (engineering only) | Prove tooling; do not support H1 |
| Paper-ready performance claim | **INVALID** if asserted | Explicitly disallowed by `RESEARCH_TRUTH.md` |

## Provenance rule

A scientific result is **VALIDATED** only when the experiment registry row links:

1. Git commit
2. Protocol JSON
3. Dataset name + SHA-256
4. Seed policy (`deterministic_no_rng` for this package)
5. Hypothesis text
6. Holdout metrics
7. Output directory with matching artifact hashes
8. `validity` other than `engineering_only`, plus independent review

Orphan summary files without a registry row are **INCONCLUSIVE**.

## Current registry

Runs append to `results/experiment_registry.csv` (or `--registry`). This repository
ships without a real-market registry row by design.
