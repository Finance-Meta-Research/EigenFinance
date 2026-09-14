from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import numpy as np
import numpy.typing as npt

FloatArray = npt.NDArray[np.float64]


@dataclass(frozen=True)
class DatasetManifest:
    name: str
    source_url: str
    license: str
    retrieved_at: str
    file_sha256: str

    @classmethod
    def load(cls, path: Path, data_path: Path) -> DatasetManifest:
        payload = json.loads(path.read_text(encoding="utf-8"))
        required = {"name", "source_url", "license", "retrieved_at", "file_sha256"}
        missing = sorted(required - payload.keys())
        if missing:
            raise ValueError(f"dataset manifest missing fields: {missing}")
        actual = sha256_file(data_path)
        if payload["file_sha256"] != actual:
            raise ValueError(
                f"dataset hash mismatch: manifest={payload['file_sha256']} actual={actual}"
            )
        for field in ("name", "source_url", "license", "retrieved_at"):
            if not str(payload[field]).strip():
                raise ValueError(f"dataset manifest field {field!r} must be non-empty")
        return cls(**{key: str(payload[key]) for key in required})


@dataclass(frozen=True)
class PricePanel:
    dates: tuple[date, ...]
    assets: tuple[str, ...]
    adjusted_close: FloatArray

    def __post_init__(self) -> None:
        expected = (len(self.dates), len(self.assets))
        if self.adjusted_close.shape != expected:
            raise ValueError(f"price shape {self.adjusted_close.shape} != {expected}")
        if len(self.dates) < 3 or len(self.assets) < 2:
            raise ValueError("at least three dates and two assets are required")
        if tuple(sorted(self.dates)) != self.dates or len(set(self.dates)) != len(self.dates):
            raise ValueError("dates must be unique and sorted")
        if len(set(self.assets)) != len(self.assets):
            raise ValueError("asset identifiers must be unique")
        if not np.all(np.isfinite(self.adjusted_close)) or np.any(self.adjusted_close <= 0):
            raise ValueError("adjusted prices must be finite and strictly positive")

    @property
    def returns(self) -> FloatArray:
        values = self.adjusted_close[1:] / self.adjusted_close[:-1] - 1.0
        if not np.all(np.isfinite(values)):
            raise ValueError("return calculation produced non-finite values")
        return values


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_price_panel(path: Path) -> PricePanel:
    if not path.is_file():
        raise FileNotFoundError(path)
    values: dict[tuple[date, str], float] = {}
    dates: set[date] = set()
    assets: set[str] = set()
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {"date", "asset", "adjusted_close"}
        if reader.fieldnames is None or not required.issubset(reader.fieldnames):
            raise ValueError(f"CSV must contain columns {sorted(required)}")
        for line_number, row in enumerate(reader, start=2):
            try:
                observation_date = date.fromisoformat(row["date"].strip())
                asset = row["asset"].strip()
                price = float(row["adjusted_close"])
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError(f"invalid row at line {line_number}") from exc
            if not asset or not np.isfinite(price) or price <= 0:
                raise ValueError(f"invalid asset or price at line {line_number}")
            key = (observation_date, asset)
            if key in values:
                raise ValueError(f"duplicate observation at line {line_number}: {key}")
            values[key] = price
            dates.add(observation_date)
            assets.add(asset)
    ordered_dates = tuple(sorted(dates))
    ordered_assets = tuple(sorted(assets))
    missing = [
        (observation_date.isoformat(), asset)
        for observation_date in ordered_dates
        for asset in ordered_assets
        if (observation_date, asset) not in values
    ]
    if missing:
        raise ValueError(
            f"price panel is not rectangular; missing {len(missing)} values: {missing[:5]}"
        )
    matrix = np.array(
        [
            [values[(observation_date, asset)] for asset in ordered_assets]
            for observation_date in ordered_dates
        ],
        dtype=np.float64,
    )
    return PricePanel(ordered_dates, ordered_assets, matrix)

