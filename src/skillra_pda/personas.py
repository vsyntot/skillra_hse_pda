"""Product-oriented persona utilities."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd


@dataclass
class Persona:
    """Persona definition for skill-gap analysis."""

    name: str
    current_skills: list[str]
    target_role: str
    target_grade: str
    constraints: dict[str, Any] = field(default_factory=dict)


def _filter_by_target(df: pd.DataFrame, persona: Persona) -> pd.DataFrame:
    filtered = df.copy()

    role_column = None
    if "primary_role" in filtered.columns:
        role_column = "primary_role"
    elif "target_role" in filtered.columns:
        role_column = "target_role"

    grade_column = "grade" if "grade" in filtered.columns else None

    if role_column and persona.target_role:
        filtered = filtered[
            filtered[role_column].fillna("").str.lower() == persona.target_role.lower()
        ]

    if grade_column and persona.target_grade:
        filtered = filtered[
            filtered[grade_column].fillna("").str.lower() == persona.target_grade.lower()
        ]

    for key, value in persona.constraints.items():
        if key not in filtered.columns:
            continue
        if isinstance(value, (list, tuple, set)):
            filtered = filtered[filtered[key].isin(value)]
        else:
            filtered = filtered[filtered[key] == value]

    return filtered


def skill_gap_for_persona(
    df: pd.DataFrame, persona: Persona, skill_cols: list[str], min_share: float = 0.1
) -> pd.DataFrame:
    """
    Calculate market share of skills for persona targets and mark gaps.

    The function first filters the feature dataframe by persona attributes
    (role, grade, custom constraints), builds a demand profile for the
    requested skills, and then flags which of them are missing for the persona.

    Returns columns: skill_name, market_share, persona_has (0/1), gap (bool).
    """

    df_filtered = _filter_by_target(df, persona)
    present_skills = [col for col in skill_cols if col in df_filtered.columns]
    if not present_skills or df_filtered.empty:
        return pd.DataFrame(columns=["skill_name", "market_share", "persona_has", "gap"])

    skill_types = {col: "boolean" for col in present_skills}
    skills_bool = df_filtered[present_skills].astype(skill_types)
    demand_profile = skills_bool.fillna(False).mean()

    rows: list[dict[str, object]] = []
    for skill_name, market_share in demand_profile.items():
        persona_has = 1 if skill_name in persona.current_skills else 0
        rows.append(
            {
                "skill_name": skill_name,
                "market_share": market_share,
                "persona_has": persona_has,
                "gap": persona_has == 0 and market_share >= min_share,
            }
        )

    result = pd.DataFrame(rows)
    return result.sort_values(by="market_share", ascending=False)


def plot_persona_skill_gap(gap_df: pd.DataFrame, persona: Persona, output_dir: Path | None = None) -> Path:
    """Plot top missing skills for a persona."""

    import matplotlib.pyplot as plt

    if gap_df.empty:
        raise ValueError("Gap dataframe is empty; cannot plot skill gaps.")

    missing = gap_df[gap_df["gap"]]
    if missing.empty:
        raise ValueError("Нет недостающих навыков для построения графика")

    top_missing = missing.sort_values(by="market_share", ascending=False)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(top_missing["skill_name"], top_missing["market_share"])
    ax.invert_yaxis()
    ax.set_xlabel("Доля вакансий с навыком")
    ax.set_title(f"Skill gap для персоны: {persona.name}")

    output_dir = output_dir or Path("reports/figures")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"fig_persona_{persona.name.lower().replace(' ', '_')}_skill_gap.png"
    fig.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)
    return output_path


# Predefined personas for quick exploration in notebooks
DATA_STUDENT_JUNIOR_DA_DS = Persona(
    name="Data student → Junior DA/DS",
    current_skills=["skill_sql", "skill_excel", "has_python", "skill_tableau"],
    target_role="data analyst",
    target_grade="junior",
    constraints={"work_mode": ["remote", "hybrid"], "city_tier": ["Moscow", "SPb"]},
)

CAREER_SWITCHER_BI_ANALYST = Persona(
    name="Career switcher → BI/Product analyst",
    current_skills=["skill_powerbi", "skill_sql", "skill_excel", "skill_tableau"],
    target_role="product analyst",
    target_grade="middle",
    constraints={"work_mode": ["hybrid", "office"], "city_tier": ["Moscow", "Million+"]},
)

MID_DATA_ANALYST = Persona(
    name="Mid data analyst leveling up",
    current_skills=["skill_sql", "has_python", "skill_powerbi", "skill_excel", "skill_tableau"],
    target_role="data analyst",
    target_grade="middle",
    constraints={"work_mode": ["remote", "hybrid", "office"], "city_tier": ["Moscow", "SPb", "Million+", "Other RU"]},
)

PERSONAS = [
    DATA_STUDENT_JUNIOR_DA_DS,
    CAREER_SWITCHER_BI_ANALYST,
    MID_DATA_ANALYST,
]

__all__ = [
    "Persona",
    "skill_gap_for_persona",
    "plot_persona_skill_gap",
    "DATA_STUDENT_JUNIOR_DA_DS",
    "CAREER_SWITCHER_BI_ANALYST",
    "MID_DATA_ANALYST",
    "PERSONAS",
]
