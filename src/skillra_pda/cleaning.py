"""Data cleaning helpers for the Skillra PDA project."""
from __future__ import annotations

from typing import Dict, Iterable, List, Tuple

import numpy as np
import pandas as pd

PREFIX_GROUPS = ["has_", "skill_", "benefit_", "soft_", "domain_", "role_"]
BOOL_NULL_MARKERS = {"unknown", "", "n/a", "nan"}
BOOL_TRUE_MARKERS = {True, 1, "1", "true", "yes"}
BOOL_FALSE_MARKERS = {False, 0, "0", "false", "no"}
BOOLEAN_MARKERS = BOOL_TRUE_MARKERS | BOOL_FALSE_MARKERS | BOOL_NULL_MARKERS


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
        if lowered in {"true", "1", "yes"}:
            return True
        if lowered in {"false", "0", "no"}:
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


def is_boolean_like_series(series: pd.Series, null_markers: Iterable[str] | None = None) -> bool:
    """Check whether a series only contains boolean-like values (plus null markers).

    Nulls are ignored for the check; any non-boolean-like value will return False.
    """

    markers = set(null_markers) if null_markers is not None else BOOL_NULL_MARKERS
    null_lower = {m.strip().lower() for m in markers}

    uniques = series.dropna().unique()
    for val in uniques:
        normalized = _normalize_bool_like(val, null_lower)
        if normalized is None:
            return False
    return True


def _drop_mostly_missing_columns(
    df: pd.DataFrame, threshold: float = 0.95
) -> Tuple[pd.DataFrame, List[str]]:
    """Drop columns whose missingness exceeds the threshold."""

    missing_share = df.isna().mean()
    to_drop = missing_share[missing_share >= threshold].index.tolist()
    if to_drop:
        df = df.drop(columns=to_drop)
    return df, to_drop


def _coerce_boolean_like_columns(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """Coerce boolean-like columns (including salary_gross and prefixed bools)."""

    bool_like_cols: List[str] = []
    allowed_values = BOOLEAN_MARKERS | {True, False, 0, 1}
    replace_map = {
        "true": True,
        "1": True,
        "yes": True,
        "false": False,
        "0": False,
        "no": False,
        "unknown": pd.NA,
        "": pd.NA,
        "n/a": pd.NA,
        "nan": pd.NA,
    }

    for col in df.columns:
        series = df[col]
        dtype_str = str(series.dtype)
        prefix_candidate = any(col.startswith(prefix) for prefix in PREFIX_GROUPS)
        force = prefix_candidate or col == "salary_gross" or dtype_str in {"bool", "boolean"}

        uniques = series.dropna().unique()
        normalized_uniques = set()
        for val in uniques:
            if isinstance(val, str):
                normalized_uniques.add(val.strip().lower())
            else:
                normalized_uniques.add(val)

        subset_bool_like = all(u in allowed_values for u in normalized_uniques) or not normalized_uniques
        if not (subset_bool_like or force):
            continue

        def _convert(val: object) -> object:
            if pd.isna(val):
                return pd.NA
            if isinstance(val, bool):
                return val
            if isinstance(val, (int, np.integer)) and val in (0, 1):
                return bool(val)
            if isinstance(val, str):
                lowered = val.strip().lower()
                if lowered in replace_map:
                    return replace_map[lowered]
            return pd.NA if force else None

        coerced = series.map(_convert)
        if coerced.isna().any() and not force and not subset_bool_like:
            continue

        df[col] = coerced.astype("boolean")
        bool_like_cols.append(col)

    return df, bool_like_cols


def _fill_categorical_missing(
    df: pd.DataFrame, exclude: Iterable[str] | None = None
) -> Tuple[pd.DataFrame, List[str]]:
    """Fill missing values in categorical/object columns with 'unknown'."""

    exclude_set = set(exclude or [])
    filled_cols: List[str] = []

    for col in df.columns:
        if col in exclude_set:
            continue
        dtype_str = str(df[col].dtype)
        if dtype_str != "object" and not dtype_str.startswith("category"):
            continue
        df[col] = df[col].fillna("unknown")
        if dtype_str == "object" and df[col].str.len().max() > 100:
            df[col] = df[col].replace("unknown", "").fillna("")
        filled_cols.append(col)

    return df, filled_cols


def _fill_numeric_missing(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """Fill missing numeric columns with median values."""

    filled_cols: List[str] = []
    numeric_cols = df.select_dtypes(include=["number"]).columns
    for col in numeric_cols:
        if df[col].isna().any():
            df[col] = df[col].fillna(df[col].median())
            filled_cols.append(col)
    return df, filled_cols


def normalize_boolean_columns(
    df: pd.DataFrame,
    null_markers: Iterable[str] | None = None,
    force_columns: Iterable[str] | None = None,
) -> Tuple[pd.DataFrame, List[str]]:
    """Coerce boolean-like columns to pandas nullable booleans.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe. It is modified in place.
    null_markers : Iterable[str] | None
        Markers that should be treated as unknown/NA before coercion.
    force_columns : Iterable[str] | None
        Columns that must be coerced regardless of boolean-likeness checks.
    """

    markers = set(null_markers) if null_markers is not None else BOOL_NULL_MARKERS
    forced = set(force_columns) if force_columns is not None else set()
    boolean_cols: List[str] = []

    for col in df.columns:
        series = df[col]
        dtype_str = str(series.dtype)

        if dtype_str == "boolean":
            boolean_cols.append(col)
            continue

        should_force = col in forced
        should_try = should_force or dtype_str == "bool" or dtype_str.startswith("bool")
        should_try = should_try or is_boolean_like_series(series, null_markers=markers)

        if not should_try:
            continue

        coerced, did_cast = coerce_bool_like_series(series, null_markers=markers, force=True)
        if should_force or did_cast:
            df[col] = coerced
            boolean_cols.append(col)

    return df, boolean_cols


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
    if "published_at_iso" in df.columns and "scraped_at_utc" in df.columns:
        df["vacancy_age_days"] = (df["scraped_at_utc"] - df["published_at_iso"]).dt.days
    return df


def handle_missingness(df: pd.DataFrame, drop_threshold: float = 0.95) -> pd.DataFrame:
    """Handle missing values using declarative sub-steps."""

    df = df.copy()

    df, dropped_cols = _drop_mostly_missing_columns(df, threshold=drop_threshold)
    df, bool_like_cols = _coerce_boolean_like_columns(df)
    df, filled_categorical_cols = _fill_categorical_missing(df, exclude=bool_like_cols)
    df, filled_numeric_cols = _fill_numeric_missing(df)

    df.attrs["dropped_cols"] = dropped_cols
    df.attrs["bool_like_cols"] = bool_like_cols
    df.attrs["filled_categorical_cols"] = filled_categorical_cols
    df.attrs["filled_numeric_cols"] = filled_numeric_cols

    return df


def ensure_salary_gross_boolean(df: pd.DataFrame) -> pd.DataFrame:
    """Guarantee salary_gross is a nullable boolean without stray string markers."""

    if "salary_gross" not in df.columns:
        return df

    replacement_map = {
        "unknown": pd.NA,
        "Unknown": pd.NA,
        "UNKNOWN": pd.NA,
        "": pd.NA,
        "n/a": pd.NA,
        "nan": pd.NA,
        "true": True,
        "false": False,
        "yes": True,
        "no": False,
        "True": True,
        "False": False,
        "1": True,
        "0": False,
    }

    series = df["salary_gross"].copy()
    if series.dtype == "object":
        series = series.replace(replacement_map)

    coerced, _ = coerce_bool_like_series(
        series, null_markers=BOOL_NULL_MARKERS, force=True
    )
    df["salary_gross"] = coerced.astype("boolean")
    return df


def salary_prepare(df: pd.DataFrame) -> pd.DataFrame:
    """Create salary helper columns and cap outliers for RUB."""
    if "salary_mid" in df.columns:
        currency_series = df.get("currency")
        mask = currency_series == "RUB" if currency_series is not None else False
        if isinstance(mask, pd.Series):
            mask = mask.fillna(False)
        df["salary_mid_rub"] = np.where(mask, df["salary_mid"], np.nan)
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
