# Project status — EigenFinance (FinanceMeta Lab)

Last verified: 2026-09-19 (agent pass) — **pytest 17/17 PASS**; working tree clean on `eng/registry-sensitivity-local` @ `89646eb`

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
| Experiment registry + commit provenance | **VERIFIED COMPLETE** |
| `adjustment_policy` on dataset manifest | **VERIFIED COMPLETE** (schema/code path) |
| Cost sensitivity grid (all strategies) | **VERIFIED** (fail-closed holdout keys) |
| Slippage stress grid (flat extra bps) | **VERIFIED** |
| Multiplicity helpers (Bonferroni/Holm) | **VERIFIED** (finite p-values required) |
| CLI epilog (engineering-only / no force-push) | **VERIFIED** |
| Licensed rectangular prices checked in | **BLOCKED** — no license held in this session; **no fake/synthetic “licensed” panel invented** |
| Real-market H1 evaluation | **NOT STARTED** |
| Paper performance claims | **INVALID** if asserted |

## Dataset license gap (explicit)

- There is **no** `data/` directory and **no** dataset manifest JSON in-repo.
- README / `RESEARCH_TRUTH.md` / `results.md` correctly require a licensed prospective panel + `adjustment_policy` before scientific claims.
- Agents must **not** fabricate vendor data, invent license strings, or check in placeholder prices labeled as licensed.
- Unblocking requires a human-provided licensed source (URL + license id + SHA-256) and a real rectangular adjusted-price panel.

## Git / remote

| Item | Truth |
|---|---|
| Local tip | `eng/registry-sensitivity-local` @ `89646eb` (clean; **synced** with `fm-candidate`) |
| Candidate GitHub | `https://github.com/Finance-Meta-Research/EigenFinance` (remote `fm-candidate`) |
| Remote eng branch | Pushed @ `89646eb` — registry/code **pushable and current** |
| Remote `main` | Placeholder history (`8c9f349` docs boundary) — **unrelated / diverged** from eng tip |
| Open PRs | None (only merged #1 placeholder boundary) |
| Push to `main` | **BLOCKED** without human decision (do not force-push placeholder main) |

## Verification

```bash
cd /Volumes/PRO-BLADE/GitHub-Every-Repo/EigenFinance
.venv/bin/python -m pytest -q   # expect 17 passed
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src
```

## Remaining blockers

1. Human: choose remote strategy (PR/replace placeholder `main` from eng history, or new repo) — histories are unrelated.
2. Licensed rectangular prices + manifest including `adjustment_policy` (human license; not agent-invented).
3. One frozen holdout run with honest `validity` (not `engineering_only` unless synthetic).
4. If prior FinanceMeta Vercel OIDC `.env.local` was exposed, confirm rotation.

## Next tasks

1. **P0** — Human remote strategy for `main` + licensed dataset intake.
2. Keep eng branch as the pushable engineering tip until strategy is chosen.
