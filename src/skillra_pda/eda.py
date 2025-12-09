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


def salary_summary_by_grade_and_city(df: pd.DataFrame, salary_col: str = "salary_mid_rub_capped") -> pd.DataFrame:
    """Median and quartiles of salary by grade and city tier."""

    required = {"grade", "city_tier"}
    missing = required - set(df.columns)
    if missing:
        raise KeyError(f"Ожидал колонки {missing} для salary_summary_by_grade_and_city")

    summary = (
        df.groupby(["grade", "city_tier"])[salary_col]
        .agg(count="count", median="median", q1=lambda s: s.quantile(0.25), q3=lambda s: s.quantile(0.75))
        .reset_index()
    )
    return summary


def salary_summary_by_role_and_work_mode(df: pd.DataFrame, salary_col: str = "salary_mid_rub_capped") -> pd.DataFrame:
    """Median salary by primary role and work mode."""

    required = {"primary_role", "work_mode"}
    missing = required - set(df.columns)
    if missing:
        raise KeyError(f"Ожидал колонки {missing} для salary_summary_by_role_and_work_mode")

    return (
        df.groupby(["primary_role", "work_mode"])[salary_col]
        .median()
        .reset_index()
        .rename(columns={salary_col: "salary_median"})
    )


def remote_share_by_role(df: pd.DataFrame) -> pd.DataFrame:
    """Share of remote positions per primary role."""

    required = {"primary_role", "is_remote"}
    missing = required - set(df.columns)
    if missing:
        raise KeyError(f"Ожидал колонки {missing} для remote_share_by_role")

    pivot = df.groupby("primary_role")[["is_remote"]].mean().reset_index()
    pivot = pivot.rename(columns={"is_remote": "remote_share"})
    return pivot.sort_values(by="remote_share", ascending=False)


def junior_friendly_share_by_segment(df: pd.DataFrame) -> pd.DataFrame:
    """Share of junior-friendly flags by primary role and grade."""

    flags = ["is_for_juniors", "allows_students", "has_mentoring", "has_test_task"]
    missing_cols = [col for col in flags if col not in df.columns]
    if missing_cols:
        raise KeyError(
            f"Ожидал колонки {missing_cols} для junior_friendly_share_by_segment"
        )

    group_cols = [col for col in ["primary_role", "grade"] if col in df.columns]
    melted = df[group_cols + flags].melt(id_vars=group_cols, value_vars=flags, var_name="flag", value_name="value")
    result = (
        melted.groupby(group_cols + ["flag"])["value"].mean().reset_index().rename(columns={"value": "share"})
    )
    return result


__all__ = [
    "missing_share",
    "describe_salary_by_group",
    "describe_salary_two_dim",
    "correlation_matrix",
    "top_value_counts",
    "skill_frequency",
    "junior_friendly_share",
    "salary_summary_by_grade_and_city",
    "salary_summary_by_role_and_work_mode",
    "remote_share_by_role",
    "junior_friendly_share_by_segment",
]
