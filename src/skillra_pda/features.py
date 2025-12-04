"""Feature engineering utilities."""
from __future__ import annotations

from typing import Dict, Iterable, List

import numpy as np
import pandas as pd

from .cleaning import PREFIX_GROUPS, detect_column_groups


def add_boolean_counts(df: pd.DataFrame, groups: Dict[str, List[str]] | None = None) -> pd.DataFrame:
    """Add aggregated counts for boolean prefix groups."""
    if groups is None:
        groups = detect_column_groups(df)

    for prefix, cols in groups.items():
        if cols:
            df[f"{prefix}count"] = df[cols].sum(axis=1)
    return df


def add_text_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add simple text-based proxy features."""
    text_cols = [col for col in df.columns if df[col].dtype == "object"]
    for col in text_cols:
        df[f"{col}_len"] = df[col].fillna("").str.len()
        df[f"{col}_words"] = df[col].fillna("").str.split().str.len()
    return df


def compute_skill_premium(
    df: pd.DataFrame,
    skill_cols: Iterable[str],
    salary_col: str = "salary_mid_rub_capped",
    min_count: int = 30,
) -> pd.DataFrame:
    """Estimate salary premium for skills vs salary column."""
    records = []
    for col in skill_cols:
        has_skill = df[col] == 1
        count_with_skill = int(has_skill.sum())
        if count_with_skill < min_count:
            continue
        median_with = df.loc[has_skill, salary_col].median()
        median_without = df.loc[~has_skill, salary_col].median()
        premium_abs = median_with - median_without
        premium_pct = premium_abs / median_without if median_without else np.nan
        records.append(
            {
                "skill": col,
                "median_with": median_with,
                "median_without": median_without,
                "premium_abs": premium_abs,
                "premium_pct": premium_pct,
                "count_with_skill": count_with_skill,
            }
        )
    return pd.DataFrame(records).sort_values(by="premium_pct", ascending=False)


def assemble_features(df: pd.DataFrame) -> pd.DataFrame:
    """Convenience pipeline for feature dataframe."""
    grouped = detect_column_groups(df)
    df = add_boolean_counts(df, groups=grouped)
    df = add_text_features(df)
    return df
