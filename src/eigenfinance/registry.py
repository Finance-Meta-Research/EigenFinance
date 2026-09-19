"""Experiment registry helpers for EigenFinance runs."""

from __future__ import annotations

import csv
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REGISTRY_FIELDS = (
    "experiment_id",
    "commit",
    "config",
    "dataset_version",
    "seed",
    "hypothesis",
    "metrics",
    "output_path",
    "result",
    "validity",
    "timestamp",
)


def git_commit(repo: Path | None = None) -> str:
    """Return HEAD commit hex, or 'NO_GIT' when unavailable."""
    root = repo or Path.cwd()
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return "NO_GIT"
    commit = completed.stdout.strip()
    return commit if commit else "NO_GIT"


def append_registry_row(registry_path: Path, row: dict[str, Any]) -> None:
    """Append one registry row, creating the CSV with a header if needed."""
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    missing = [field for field in REGISTRY_FIELDS if field not in row]
    if missing:
        raise ValueError(f"registry row missing fields: {missing}")
    write_header = not registry_path.is_file()
    with registry_path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REGISTRY_FIELDS)
        if write_header:
            writer.writeheader()
        writer.writerow({field: row[field] for field in REGISTRY_FIELDS})


def utc_timestamp() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()
