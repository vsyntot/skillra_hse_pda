"""Input/output helpers for the Skillra PDA project."""
from pathlib import Path
from typing import Union

import pandas as pd

from .cleaning import BOOL_NULL_MARKERS, coerce_bool_like_series, is_boolean_like_series

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


def save_processed(df: pd.DataFrame, path: PathLike) -> None:
    """Save a processed dataframe to CSV or Parquet.

    The parent directory is created automatically. Format is inferred from the
    file suffix: `.parquet` → Parquet, otherwise CSV.
    """
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df_to_save = df.copy()

    for col in df_to_save.columns:
        dtype_str = str(df_to_save[col].dtype)
        if dtype_str in {"object", "string", "bool"} or dtype_str.startswith("category"):
            if is_boolean_like_series(df_to_save[col], null_markers=BOOL_NULL_MARKERS):
                coerced, did_cast = coerce_bool_like_series(
                    df_to_save[col], null_markers=BOOL_NULL_MARKERS, force=True
                )
                if did_cast:
                    df_to_save[col] = coerced

    if "salary_gross" in df_to_save.columns:
        df_to_save["salary_gross"] = coerce_bool_like_series(
            df_to_save["salary_gross"], null_markers=BOOL_NULL_MARKERS, force=True
        )[0]

    if output_path.suffix.lower() == ".parquet":
        df_to_save.to_parquet(output_path, index=False)
    else:
        df_to_save.to_csv(output_path, index=False)
