"""Input/output helpers for the Skillra PDA project."""
from pathlib import Path
from typing import Union

import pandas as pd

from .cleaning import (
    BOOL_NULL_MARKERS,
    coerce_bool_like_series,
    ensure_salary_gross_boolean,
    is_boolean_like_series,
    normalize_boolean_columns,
)

PathLike = Union[str, Path]


def load_raw(path: PathLike) -> pd.DataFrame:
    """Load the raw CSV dataset with safe defaults.

    Parameters
    ----------
    path : PathLike
        Path to the raw CSV file.

    Returns
    -------
    pd.DataFrame
    """
    csv_path = Path(path)
    return pd.read_csv(csv_path, low_memory=False)


def _coerce_boollike_object_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Sanitize nearly-boolean object columns before persistence."""

    allowed = {
        True,
        False,
        1,
        0,
        "1",
        "0",
        "true",
        "false",
        "True",
        "False",
        "unknown",
        "Unknown",
        "UNKNOWN",
        "",
    }

    for col in df.columns:
        if str(df[col].dtype) != "object":
            continue

        uniques = set(df[col].dropna().unique().tolist())
        if not uniques:
            continue
        if not uniques.issubset(allowed):
            continue

        coerced, did_cast = coerce_bool_like_series(
            df[col], null_markers=BOOL_NULL_MARKERS, force=True
        )
        if did_cast:
            df[col] = coerced

    return df


def save_processed(df: pd.DataFrame, path: PathLike) -> None:
    """Save a processed dataframe to CSV or Parquet.

    The parent directory is created automatically. Format is inferred from the
    file suffix: `.parquet` → Parquet, otherwise CSV.
    """
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df_to_save = df.copy()

    df_to_save, _boolean_cols = normalize_boolean_columns(
        df_to_save, null_markers=BOOL_NULL_MARKERS, force_columns={"salary_gross"}
    )

    df_to_save = ensure_salary_gross_boolean(df_to_save)
    df_to_save = _coerce_boollike_object_columns(df_to_save)

    if output_path.suffix.lower() == ".parquet":
        df_to_save.to_parquet(output_path, index=False)
    else:
        df_to_save.to_csv(output_path, index=False)
