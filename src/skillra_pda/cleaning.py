"""Data cleaning helpers for the Skillra PDA project."""
from __future__ import annotations

from typing import Dict, Iterable, List, Tuple

import numpy as np
import pandas as pd

PREFIX_GROUPS = ["has_", "skill_", "benefit_", "soft_", "domain_", "role_"]
BOOL_NULL_MARKERS = {"unknown", "Unknown", "UNKNOWN", ""}


def _normalize_bool_like(value, null_lower: set) -> object:
    """Normalize a single value to True/False/pd.NA if it is boolean-like.

    Returns None when the value is not recognized as boolean-like.
    """

    if pd.isna(value):
        return pd.NA

    if isinstance(value, bool):
        return value

    if isinstance(value, (int, np.integer)):
        if value in (0, 1):
            return bool(value)
        return None

    if isinstance(value, str):
        stripped = value.strip()
        lowered = stripped.lower()
        if lowered in null_lower:
            return pd.NA
        if lowered in {"true", "1"}:
            return True
        if lowered in {"false", "0"}:
            return False

    return None


def coerce_bool_like_series(
    series: pd.Series,
    null_markers: Iterable[str] | None = None,
    force: bool = False,
) -> Tuple[pd.Series, bool]:
    """Convert boolean-like values to pandas nullable boolean dtype.

    Parameters
    ----------
    series : pd.Series
        Series to process.
    null_markers : Iterable[str] | None, optional
        Markers that should be treated as null/unknown before casting.
    force : bool, optional
        If True, unrecognized values are coerced to NA to allow casting. If
        False, the function returns (series, False) when encountering
        non-boolean-like values.
    """

    markers = set(null_markers) if null_markers is not None else BOOL_NULL_MARKERS
    null_lower = {m.strip().lower() for m in markers}

    uniques = series.dropna().unique()
    for val in uniques:
        normalized = _normalize_bool_like(val, null_lower)
        if normalized is None and not force:
            return series, False

    def _convert(val):
        normalized = _normalize_bool_like(val, null_lower)
        if normalized is None:
            return pd.NA if force else normalized
        return normalized

    coerced = series.map(_convert)
    if not force and coerced.isna().any() and len(series.dropna()) > 0:
        return series, False

    return coerced.astype("boolean"), True


def basic_profile(df: pd.DataFrame) -> Dict[str, object]:
    """Return a lightweight profile of the dataframe."""
    missing = df.isna().mean().sort_values(ascending=False).head(20)
    dtypes_summary = df.dtypes.astype(str).value_counts().to_dict()
    profile = {
        "shape": df.shape,
        "dtypes_summary": dtypes_summary,
        "missing_top20": missing,
    }
    return profile


def check_unique_id(df: pd.DataFrame, id_col: str = "vacancy_id") -> Tuple[bool, int]:
    """Check whether an identifier column is unique.

    Returns a tuple of (is_unique, duplicate_count).
    """
    duplicates = df.duplicated(subset=[id_col]).sum()
    return duplicates == 0, int(duplicates)


def detect_column_groups(df: pd.DataFrame) -> Dict[str, List[str]]:
    """Group columns by business prefixes."""
    groups: Dict[str, List[str]] = {prefix: [] for prefix in PREFIX_GROUPS}
    for col in df.columns:
        for prefix in PREFIX_GROUPS:
            if col.startswith(prefix):
                groups[prefix].append(col)
    return groups


def parse_dates(df: pd.DataFrame) -> pd.DataFrame:
    """Parse timestamp-like columns into datetimes."""
    date_cols = ["published_at_iso", "scraped_at_utc"]
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def handle_missingness(df: pd.DataFrame, drop_threshold: float = 0.95) -> pd.DataFrame:
    """Handle missing values with simple heuristics."""
    col_missing = df.isna().mean()
    to_drop = col_missing[col_missing >= drop_threshold].index
    if len(to_drop) > 0:
        df = df.drop(columns=list(to_drop))
        df.attrs["dropped_columns"] = list(to_drop)

    boolean_cols: List[str] = []
    for col in df.columns:
        coerced, did_cast = coerce_bool_like_series(df[col])
        if did_cast:
            df[col] = coerced
            boolean_cols.append(col)

    if "salary_gross" in df.columns and "salary_gross" not in boolean_cols:
        coerced, did_cast = coerce_bool_like_series(df["salary_gross"], force=True)
        if did_cast:
            df["salary_gross"] = coerced
            boolean_cols.append("salary_gross")

    categorical_cols = [
        col
        for col in df.columns
        if (df[col].dtype == "object" or str(df[col].dtype).startswith("category"))
        and col not in boolean_cols
    ]
    for col in categorical_cols:
        df[col] = df[col].fillna("unknown")

    text_cols = [col for col in categorical_cols if df[col].str.len().max() > 100]
    for col in text_cols:
        df[col] = df[col].replace("unknown", "").fillna("")

    numeric_cols = df.select_dtypes(include=["number"]).columns
    for col in numeric_cols:
        if df[col].isna().any():
            median = df[col].median()
            df[col] = df[col].fillna(median)

    return df


def salary_prepare(df: pd.DataFrame) -> pd.DataFrame:
    """Create salary helper columns and cap outliers for RUB."""
    if "salary_mid" in df.columns:
        df["salary_mid_rub"] = np.where(df.get("currency") == "RUB", df["salary_mid"], np.nan)
    else:
        df["salary_mid_rub"] = np.nan

    df["salary_known"] = df["salary_mid_rub"].notna()

    if df["salary_mid_rub"].notna().any():
        lower = df["salary_mid_rub"].quantile(0.01)
        upper = df["salary_mid_rub"].quantile(0.99)
        df["salary_mid_rub_capped"] = df["salary_mid_rub"].clip(lower=lower, upper=upper)
    else:
        df["salary_mid_rub_capped"] = df["salary_mid_rub"]

    non_rub_share = (
        df.get("currency").fillna("").ne("RUB").mean() if "currency" in df.columns else 0.0
    )
    df.attrs["non_rub_share"] = non_rub_share
    return df


def deduplicate(df: pd.DataFrame, id_col: str = "vacancy_id") -> pd.DataFrame:
    """Remove duplicate vacancies keeping the latest scrape."""
    if id_col not in df.columns:
        return df

    sort_col = "scraped_at_utc" if "scraped_at_utc" in df.columns else None
    if sort_col:
        df = df.sort_values(by=sort_col, ascending=False)
    before = len(df)
    df = df.drop_duplicates(subset=[id_col], keep="first")
    df.attrs["deduplicated_rows"] = before - len(df)
    return df
