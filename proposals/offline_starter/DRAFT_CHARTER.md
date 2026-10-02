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
