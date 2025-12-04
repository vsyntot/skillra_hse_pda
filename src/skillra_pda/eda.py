"""EDA helper functions."""
from __future__ import annotations

from typing import Iterable, Tuple

import pandas as pd


def missing_share(df: pd.DataFrame, top_n: int = 20) -> pd.Series:
    """Return top missing shares."""
    return df.isna().mean().sort_values(ascending=False).head(top_n)


def describe_salary_by_group(
    df: pd.DataFrame, group_col: str, salary_col: str = "salary_mid_rub_capped", top_n: int | None = None
) -> pd.DataFrame:
    """Summaries of salary by categorical grouping."""
    grouped = (
        df.groupby(group_col)[salary_col]
        .agg(["count", "median", "mean", "min", "max"])
        .rename(columns={"count": "n"})
        .sort_values(by="median", ascending=False)
    )
    if top_n:
        grouped = grouped.head(top_n)
    return grouped.reset_index()


def correlation_matrix(df: pd.DataFrame, cols: Iterable[str] | None = None) -> pd.DataFrame:
    """Compute Pearson correlation matrix for numeric columns."""
    if cols is None:
        numeric_df = df.select_dtypes(include=["number"])
    else:
        numeric_df = df[list(cols)]
    return numeric_df.corr()


def top_value_counts(df: pd.DataFrame, col: str, top_n: int = 15) -> pd.Series:
    """Return top frequency counts for a categorical column."""
    return df[col].value_counts().head(top_n)
