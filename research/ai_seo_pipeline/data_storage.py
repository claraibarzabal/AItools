"""CSV persistence helpers for pipeline artifacts."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def save_csv(df: pd.DataFrame, path: Path) -> None:
    ensure_parent(path)
    df.to_csv(path, index=False)


def load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def append_or_replace_rows(
    existing: pd.DataFrame,
    new_rows: pd.DataFrame,
    key_columns: list[str],
) -> pd.DataFrame:
    if existing.empty:
        return new_rows.copy()
    if new_rows.empty:
        return existing.copy()

    combined = pd.concat([existing, new_rows], ignore_index=True)
    return combined.drop_duplicates(subset=key_columns, keep="last").reset_index(drop=True)
