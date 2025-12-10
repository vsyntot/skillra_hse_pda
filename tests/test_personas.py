"""Unit tests for persona demand and gap analysis."""

import pandas as pd

from src.skillra_pda import personas


def test_build_skill_demand_profile_and_gap():
    df = pd.DataFrame(
        {
            "primary_role": ["data", "data"],
            "grade": ["junior", "junior"],
            "skill_sql": [True, True],
            "has_python": [True, False],
        }
    )

    persona = personas.Persona(
        name="student",
        description="",
        current_skills=["skill_sql"],
        target_role="data",
        target_grade="junior",
    )

    demand = personas.build_skill_demand_profile(df, persona, min_share=0.1)
    assert not demand.empty
    assert set(demand["skill_name"]).issuperset({"skill_sql", "has_python"})

    gap = personas.skill_gap_for_persona(df, persona, min_share=0.1)
    python_row = gap.loc[gap["skill_name"] == "has_python"].iloc[0]
    assert bool(python_row["gap"]) is True
    sql_row = gap.loc[gap["skill_name"] == "skill_sql"].iloc[0]
    assert bool(sql_row["gap"]) is False
