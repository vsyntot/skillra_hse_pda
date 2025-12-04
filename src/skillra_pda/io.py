"""Input/output helpers for the Skillra PDA project."""
from pathlib import Path
from typing import Union

import pandas as pd

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

    if output_path.suffix.lower() == ".parquet":
        df.to_parquet(output_path, index=False)
    else:
        df.to_csv(output_path, index=False)
