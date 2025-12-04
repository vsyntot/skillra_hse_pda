"""Product-oriented persona utilities."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

import pandas as pd


@dataclass
class Persona:
    name: str
    current_skills: List[str]
    target_role: str
    target_grade: str | None = None
    constraints: Dict[str, object] = field(default_factory=dict)


def skill_gap_for_persona(df: pd.DataFrame, persona: Persona, top_k: int = 10) -> pd.DataFrame:
    """Calculate skill gaps for a given persona."""
    df_filtered = df.copy()
    if persona.target_role and "primary_role" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["primary_role"].str.contains(persona.target_role, case=False, na=False)]
    if persona.target_grade and "grade" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["grade"].str.contains(persona.target_grade, case=False, na=False)]

    for key, value in persona.constraints.items():
        if key in df_filtered.columns:
            if isinstance(value, (list, tuple, set)):
                df_filtered = df_filtered[df_filtered[key].isin(value)]
            else:
                df_filtered = df_filtered[df_filtered[key] == value]

    skill_cols = [col for col in df_filtered.columns if col.startswith("skill_") or col.startswith("has_")]
    freq = df_filtered[skill_cols].mean().sort_values(ascending=False).head(top_k)

    rows = []
    for skill, market_share in freq.items():
        persona_has = 1 if skill in persona.current_skills else 0
        rows.append(
            {
                "skill": skill,
                "market_share": market_share,
                "persona_has": persona_has,
                "gap": 1 - persona_has,
            }
        )
    return pd.DataFrame(rows)
