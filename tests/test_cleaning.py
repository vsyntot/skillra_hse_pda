"""Unit tests for cleaning helpers."""

import sys
import types

import pandas as pd

personas_stub = types.ModuleType("src.skillra_pda.personas")
for name in [
    "DATA_STUDENT",
    "MID_DATA_ANALYST",
    "Persona",
    "SWITCHER_BI",
    "analyze_persona",
    "build_skill_demand_profile",
    "skill_gap_for_persona",
]:
    setattr(personas_stub, name, None)
sys.modules.setdefault("src.skillra_pda.personas", personas_stub)
from src.skillra_pda import cleaning


def test_ensure_salary_gross_boolean_converts_and_preserves_columns():
    df = pd.DataFrame(
        {
            "salary_gross": ["True", "False", "unknown", "yes", "no"],
            "salary_from": [100000, 150000, None, 200000, 50000],
        }
    )

    result = cleaning.ensure_salary_gross_boolean(df.copy())

    assert set(result.columns) == set(df.columns)
    assert str(result["salary_gross"].dtype) == "boolean"
    pd.testing.assert_series_equal(result["salary_from"], df["salary_from"], check_names=False)
    assert list(result["salary_gross"].astype(object)) == [True, False, pd.NA, True, False]
