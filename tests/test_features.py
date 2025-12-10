"""Unit tests for key feature engineering helpers."""

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
from src.skillra_pda import features


def test_add_city_tier_assigns_expected_buckets_without_side_effects():
    df = pd.DataFrame(
        {
            "city": ["Москва", "Санкт-Петербург", "Казань", "Алматы"],
            "vacancy_id": [1, 2, 3, 4],
        }
    )

    result = features.add_city_tier(df.copy())

    assert set(result.columns) == set(df.columns) | {"city_tier"}
    assert result["vacancy_id"].tolist() == df["vacancy_id"].tolist()
    assert result["city_tier"].tolist() == ["Moscow", "SPb", "Million+", "KZ/Other"]


def test_add_primary_role_chooses_priority_role_and_keeps_other_columns():
    df = pd.DataFrame(
        {
            "role_ml": [False, True, False],
            "role_analyst": [True, True, False],
            "role_backend": [False, False, True],
            "city": ["Moscow", "SPb", "Kazan"],
        }
    )

    result = features.add_primary_role(df.copy())

    assert set(result.columns) == set(df.columns) | {"primary_role"}
    assert result["city"].tolist() == df["city"].tolist()
    assert list(result["primary_role"]) == ["analyst", "ml", "backend"]
