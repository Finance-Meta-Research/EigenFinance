# Security audit — EigenFinance / FinanceMeta Lab surface

Audit date: 2026-09-18. Secrets are not printed in this document.

| Issue | Severity | Evidence | Affected files | Remediation | Verification |
|---|---|---|---|---|---|
| Vercel OIDC token material on shared volume | **High** | `FinanceMeta-Landing/.env.local` contained `VERCEL_OIDC_TOKEN` (values not logged). Directory has no git metadata; `.gitignore` already ignores `.env*`. | `GitHub-Every-Repo/FinanceMeta-Landing/.env.local` | Remove local secret file; obtain tokens via `vercel env pull` / environment only; **rotate** the OIDC credential if it may have been shared. | File removed this session; confirm no copies remain and rotate in Vercel. |
| Untrusted CSV/JSON inputs | Medium (mitigated) | CLI reads user-supplied price CSV and manifest. | `src/eigenfinance/data.py`, `cli.py` | Loader rejects duplicates, non-rectangular panels, non-positive/non-finite prices, empty manifest fields, and SHA-256 mismatch. | Covered by fail-closed unit tests. |
| Output path overwrite | Low | `--output` writes evidence artifacts. | `cli.py` | Atomic temp+replace writes; operators should use fresh output directories per run. | CLI evidence test verifies hashes. |
| Subprocess git probe | Low | Registry records `git rev-parse HEAD` with timeout. | `registry.py` | Fixed argv list, `cwd` bounded, 5s timeout, no shell. | Unit/CLI tests. |
| Dependency surface | Low | Runtime depends only on `numpy`. | `pyproject.toml` | Keep runtime deps minimal; pin in lockfiles when publishing. | `uv.lock` / CI when publishing. |
| No authn/authz endpoints | Info | Package is a local CLI, not a network service. | n/a | Keep it offline; do not embed API keys in manifests. | N/A |

## Actions taken this session

1. Removed `FinanceMeta-Landing/.env.local` after recording key names only.
2. Documented rotation requirement above.
3. EigenFinance registry/manifest now records commit and validity without embedding secrets.
