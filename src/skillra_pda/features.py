"""Feature engineering utilities aligned with the project plan."""
from __future__ import annotations

from typing import Dict, Iterable, List

import numpy as np
import pandas as pd

from .cleaning import detect_column_groups


CITY_MILLION_PLUS = {
    "novosibirsk",
    "yekaterinburg",
    "nizhny novgorod",
    "kazan",
    "chelyabinsk",
    "samara",
    "omsk",
    "rostov-on-don",
    "rostov-na-donu",
    "ufa",
    "krasnoyarsk",
    "perm",
    "voronezh",
    "volgograd",
}

PRIMARY_ROLE_PRIORITY = [
    "role_ml",
    "role_data",
    "role_devops",
    "role_backend",
    "role_frontend",
    "role_fullstack",
    "role_mobile",
    "role_qa",
    "role_product",
    "role_manager",
    "role_analyst",
]


def add_time_features(df: pd.DataFrame, date_col: str = "published_at_iso") -> pd.DataFrame:
    """Add weekday/month/is_weekend flags from the publication date."""
    if date_col in df.columns:
        dt = pd.to_datetime(df[date_col], errors="coerce")
        df["published_weekday"] = dt.dt.weekday
        df["published_month"] = dt.dt.month
        df["is_weekend_post"] = dt.dt.weekday.isin([5, 6])
    else:
        # Keep downstream expectations stable even if the source column was dropped upstream.
        df["published_weekday"] = pd.NA
        df["published_month"] = pd.NA
        df["is_weekend_post"] = pd.NA
    return df


def _city_to_tier(city: str | float) -> str:
    if not isinstance(city, str):
        return "unknown"
    city_norm = city.lower()
    if "moscow" in city_norm or "моск" in city_norm:
        return "Moscow"
    if "spb" in city_norm or "петербург" in city_norm or "санкт" in city_norm:
        return "SPb"
    if city_norm in CITY_MILLION_PLUS:
        return "Million+"
    if any(country in city_norm for country in ["kazakhstan", "kazakh", "kz", "алматы", "нур-султан", "астана"]):
        return "KZ/Other"
    return "Other RU"


def add_city_tier(df: pd.DataFrame, city_col: str = "city") -> pd.DataFrame:
    """Map raw cities into simplified buckets for analysis."""
    if city_col in df.columns:
        df["city_tier"] = df[city_col].apply(_city_to_tier)
    else:
        df["city_tier"] = "unknown"
    return df


def add_work_mode(df: pd.DataFrame) -> pd.DataFrame:
    """Create normalized work mode based on remote/hybrid flags."""
    remote = df.get("is_remote")
    hybrid = df.get("is_hybrid")
    work_format = df.get("work_format")

    def decide(row):
        if bool(row.get("is_remote")):
            return "remote"
        if bool(row.get("is_hybrid")):
            return "hybrid"
        if row.get("work_format") == "office":
            return "office"
        return "unknown"

    df = df.copy()
    df["work_mode"] = [
        decide({
            "is_remote": remote.iloc[i] if remote is not None else None,
            "is_hybrid": hybrid.iloc[i] if hybrid is not None else None,
            "work_format": work_format.iloc[i] if work_format is not None else None,
        })
        for i in range(len(df))
    ]
    return df


def add_boolean_counts(df: pd.DataFrame, groups: Dict[str, List[str]] | None = None) -> pd.DataFrame:
    """Aggregate boolean prefix groups into compact counters."""
    if groups is None:
        groups = detect_column_groups(df)

    mapping = {
        "benefit_": "benefits_count",
        "soft_": "soft_skills_count",
        "has_": "hard_stack_count",
        "skill_": "skills_count",
        "role_": "role_count",
    }

    for prefix, target_col in mapping.items():
        cols = groups.get(prefix, [])
        if cols:
            df[target_col] = df[cols].sum(axis=1)
    return df


def add_primary_role(df: pd.DataFrame, role_prefix: str = "role_") -> pd.DataFrame:
    """Collapse multiple role flags into a single prioritized primary role."""
    role_cols = [col for col in df.columns if col.startswith(role_prefix)]
    df = df.copy()
    primary_role = []
    for _, row in df[role_cols].iterrows():
        chosen = "other"
        for col in PRIMARY_ROLE_PRIORITY:
            if col in row and row[col]:
                chosen = col.replace(role_prefix, "")
                break
        primary_role.append(chosen)
    df["primary_role"] = pd.Categorical(primary_role)
    return df


def add_salary_bucket(
    df: pd.DataFrame, salary_col: str = "salary_mid_rub_capped", labels: List[str] | None = None
) -> pd.DataFrame:
    """Create quantile-based salary buckets for downstream analysis."""
    if labels is None:
        labels = ["low", "mid", "high"]

    df = df.copy()
    if salary_col not in df.columns:
        df[salary_col] = np.nan

    valid = df[salary_col].dropna()
    if len(valid) >= len(labels):
        df.loc[valid.index, "salary_bucket"] = pd.qcut(valid, q=len(labels), labels=labels, duplicates="drop")
    else:
        df["salary_bucket"] = np.nan
    return df


def add_text_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add simple text-based proxy features."""
    text_cols = [col for col in df.columns if df[col].dtype == "object"]
    for col in text_cols:
        cleaned = df[col].fillna("")
        df[f"{col}_len"] = cleaned.str.len()
        df[f"{col}_words"] = cleaned.str.split().str.len()
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
        if col not in df.columns:
            continue
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
    df = add_time_features(df)
    df = add_city_tier(df)
    df = add_work_mode(df)
    df = add_boolean_counts(df, groups=grouped)
    df = add_primary_role(df)
    df = add_salary_bucket(df)
    df = add_text_features(df)
    return df
