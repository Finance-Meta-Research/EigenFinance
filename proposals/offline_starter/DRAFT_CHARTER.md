# EigenFinance proposed research tooling scope

Status: proposed scope and offline prototype for review. The reserved project has not been activated by this draft. This scope is a new proposal, not recovered founder intent.

## Objective

Build auditable covariance diagnostics for FinanceMeta researchers. Start with supplied-matrix validation before adding a separately frozen covariance forecasting comparison. Keep the toolkit separate from Eigen-JEPA's closed synthetic study and its optional classical-baseline successor.

The implemented prototype reports eigenvalues, positive-semidefinite status, positive-definite status and spectral condition number. It rejects nonsquare, nonnumeric, nonfinite and asymmetric inputs. Singular matrices produce no finite condition number. Symmetry and positivity tolerance is 1e-10 times the largest absolute entry; near-zero decisions are numerical diagnostics, not proofs about population covariance.

## Proposed first study

Question: does a fixed shrinkage estimator lower next-window covariance prediction error relative to sample covariance and a diagonal control on the same chronological development windows?

Before outcomes: select a licensed point-in-time return source and fixed asset universe; freeze adjustment/missingness rules, decision timestamps, rolling window length, forecast horizon, purged folds, training-only parameter selection and all estimator configurations. Proposed primary metric is Frobenius error against a common future-window realized covariance; report each fold and paired differences. Realized covariance is noisy and is not a known population target. No trading claim follows from this metric.

No dataset, seed list, study threshold, outcome access or experiment authorization is frozen here. Stop if provenance or timestamps are unverifiable, or if a comparator uses unequal information. Preserve null and adverse differences. The implementation phase is complete when exact configuration, source hashes, per-fold predictions, metrics and a reproducible command are retained.

## Run the prototype

Requires Python 3.10+ and NumPy. From `proposals/offline_starter`:

```bash
python -m unittest discover -v
python covariance_audit.py matrix.json
```

`matrix.json` is a square JSON numeric array. For an explicitly fictional arithmetic fixture `[[1,0],[0,4]]`, eigenvalues are 1 and 4 and condition number is 4. No supplied examples represent market observations. The prototype neither reads protected data nor estimates forecast skill.

Accountable scientific owner and reviewer remain to be named before study activation. No dataset or learned model is included; no alpha, risk-reduction or real-market effectiveness claim is supported.

## Executable development comparison

`development_comparison.py` now compares rolling sample covariance, its diagonal, and a fixed 20% shrinkage toward that diagonal. This shrinkage choice is an illustrative development comparator, not a selected optimum. All predictors consume the same past context; evaluation windows do not overlap. Each result retains context/evaluation dates, squared Frobenius errors, mean errors and unused tail count. A future sample covariance is a noisy target. Asset counts affect the scale of this unnormalized metric.

Run `python development_comparison.py development.json`. The JSON object requires `evaluation_mode: "development"`, a nonempty `source`, unique `assets`, integer `train_rows` and `horizon_rows` of at least two, and `rows` containing strictly increasing completed ISO calendar `date` values and numeric decimal `returns` in asset order. Every complete horizon is evaluated; trailing incomplete rows are counted and excluded. Missing values and duplicate dates are rejected rather than imputed. Protected mode is refused.

This harness checks supplied dates, not provider release times, licensing, delistings or revision vintages. Source and availability verification remain false. Use only permitted development data after the study scope is agreed; no real dataset has been processed here. Fourteen fixture tests passed, including independent known covariance errors, context/evaluation separation, invalid contracts, protected-mode refusal and extreme-scale matrix diagnostics.
