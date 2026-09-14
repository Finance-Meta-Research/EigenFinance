# Contributing

Changes must preserve temporal ordering, the training/test embargo, the untouched final holdout, strict
input rejection, transaction-cost accounting, and artifact provenance. Before review, run:

```bash
uv sync --extra dev
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src
.venv/bin/python -m pytest -q
.venv/bin/python -m build --no-isolation
```

Tests may use synthetic fixtures, but scientific documentation must never promote those fixtures to
market evidence. Retain negative results and failed runs.

