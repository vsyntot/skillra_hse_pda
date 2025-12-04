"""EDA helper functions."""
from __future__ import annotations

from typing import Iterable

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


def describe_salary_two_dim(
    df: pd.DataFrame,
    group_a: str,
    group_b: str,
    salary_col: str = "salary_mid_rub_capped",
    agg: str = "median",
) -> pd.DataFrame:
    """Pivot salary statistics across two categorical dimensions."""
    return df.pivot_table(values=salary_col, index=group_a, columns=group_b, aggfunc=agg)


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


def skill_frequency(df: pd.DataFrame, skill_cols: Iterable[str], top_n: int = 15) -> pd.Series:
    """Return aggregated frequencies for provided skill columns."""
    present = [col for col in skill_cols if col in df.columns]
    if not present:
        return pd.Series(dtype="float64")
    freq = df[present].mean().sort_values(ascending=False)
    return freq.head(top_n)


def junior_friendly_share(df: pd.DataFrame, flags: Iterable[str]) -> pd.Series:
    """Calculate mean availability of junior-friendly attributes if present."""
    usable = [flag for flag in flags if flag in df.columns]
    if not usable:
        return pd.Series(dtype="float64")
    return df[usable].mean().sort_values(ascending=False)
