"""Unit tests for cleaning helpers."""

import pandas as pd

from src.skillra_pda import cleaning


def test_ensure_salary_gross_boolean_normalizes_unknown():
    df = pd.DataFrame({"salary_gross": ["True", "False", "unknown"]})

    result = cleaning.ensure_salary_gross_boolean(df.copy())

    assert str(result["salary_gross"].dtype) == "boolean"
    assert bool(result.loc[0, "salary_gross"]) is True
    assert bool(result.loc[1, "salary_gross"]) is False
    assert pd.isna(result.loc[2, "salary_gross"])


def test_handle_missingness_drops_high_missing_columns():
    df = pd.DataFrame({"keep": [1, 2], "drop": [pd.NA, pd.NA]})

    cleaned = cleaning.handle_missingness(df, drop_threshold=0.9)

    assert "drop" not in cleaned.columns
    assert "drop" in cleaned.attrs.get("dropped_cols", [])
