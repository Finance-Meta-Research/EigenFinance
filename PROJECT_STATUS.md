# Project status — EigenFinance (FinanceMeta Lab)

Last verified: 2026-09-19 (marathon) — **pytest 17/17 PASS**; working tree clean on `eng/registry-sensitivity-local` @ `6399a53`

## Objective

Leakage-resistant, auditable walk-forward evaluation for long-only equal-weight,
inverse-volatility, and shrinkage minimum-variance portfolios after declared
transaction costs — without asserting real-market alpha.

## Lifecycle

**Engineering-complete / science-gated.** Real-market H1 evaluation **NOT STARTED**.

## Result status

| Component | Classification |
|---|---|
| Package + CLI + walk-forward + costs | **VERIFIED COMPLETE** |
| Experiment registry + commit provenance | **VERIFIED COMPLETE** (`9dea855` base; local dirty sensitivity+stress) |
| `adjustment_policy` on dataset manifest | **VERIFIED COMPLETE** |
| Cost sensitivity grid (all strategies) | **VERIFIED** (fail-closed holdout keys) |
| Slippage stress grid (flat extra bps) | **VERIFIED** |
| Multiplicity helpers (Bonferroni/Holm) | **VERIFIED** (finite p-values required) |
| CLI epilog (engineering-only / no force-push) | **VERIFIED** |
| Real-market H1 evaluation | **NOT STARTED** |
| Paper performance claims | **INVALID** if asserted |

## Git / remote

| Item | Truth |
|---|---|
| Local tip | `eng/registry-sensitivity-local` @ `6399a53` (clean; ahead of `fm-candidate` by 1) |
| Candidate GitHub | `https://github.com/Finance-Meta-Research/EigenFinance` (fetched as `fm-candidate`) |
| Remote `main` | Placeholder history (`8c9f349` docs boundary) — **unrelated / diverged** from local eng tip |
| Push | **BLOCKED** without human decision (do not force-push placeholder main) |

## Verification (peer when Shell works)

```bash
cd /Volumes/PRO-BLADE/GitHub-Every-Repo/EigenFinance
.venv/bin/python -m pytest -q   # expect 17 passed
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src
```

## Remaining blockers

1. Human: choose remote strategy (replace placeholder main via PR from eng history, or new repo).
2. Licensed rectangular prices + manifest including `adjustment_policy`.
3. One frozen holdout run with honest `validity` (not `engineering_only` unless synthetic).
4. If prior FinanceMeta Vercel OIDC `.env.local` was exposed, confirm rotation.
5. Peer: run suite + commit when asked (see `/Volumes/PRO-BLADE/PEER_PUSH_NOTES.md`).

## Next tasks

1. **P0** — Remote strategy + licensed dataset.
2. **P2** — Slippage stress grid — **DONE locally (unverified by pytest this session)**.
3. **P3** — Multiplicity correction helper — **DONE locally (unverified by pytest this session)**.
