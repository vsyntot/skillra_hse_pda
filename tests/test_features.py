"""Unit tests for key feature engineering helpers."""

import pandas as pd

from src.skillra_pda import features


def test_add_city_tier_classifies_major_cities():
    df = pd.DataFrame({"city": ["Москва", "Санкт-Петербург", "Казань", "Тула"]})

    result = features.add_city_tier(df.copy())

    assert result["city_tier"].tolist() == ["Moscow", "SPb", "Million+", "Other RU"]


def test_add_primary_role_respects_priority():
    df = pd.DataFrame(
        {
            "role_ml": [False, True],
            "role_analyst": [True, True],
        }
    )

    result = features.add_primary_role(df.copy())

    assert list(result["primary_role"]) == ["analyst", "ml"]
