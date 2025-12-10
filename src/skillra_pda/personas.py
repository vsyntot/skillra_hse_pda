"""Product-oriented persona utilities."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

from .eda import build_skill_demand_profile as _base_skill_profile


@dataclass
class Persona:
    """Persona definition for skill-gap analysis."""

    name: str
    current_skills: list[str]
    target_role: str
    target_grade: str
    constraints: dict[str, Any] = field(default_factory=dict)


def _filter_by_target(
    df: pd.DataFrame,
    persona: Persona,
    role_col: str = "primary_role",
    grade_col: str = "grade",
) -> pd.DataFrame:
    """Filter dataframe by persona target role/grade and constraint columns."""

    filtered = df.copy()

    if persona.target_role and role_col in filtered.columns:
        filtered = filtered[
            filtered[role_col].fillna("").str.lower()
            == persona.target_role.strip().lower()
        ]

    if persona.target_grade and grade_col in filtered.columns:
        filtered = filtered[
            filtered[grade_col].fillna("").str.lower()
            == persona.target_grade.strip().lower()
        ]

    for key, value in persona.constraints.items():
        if key not in filtered.columns or value is None:
            continue
        if isinstance(value, (list, tuple, set)):
            filtered = filtered[filtered[key].isin(value)]
        else:
            filtered = filtered[filtered[key] == value]

    return filtered


def build_skill_demand_profile(
    df_features: pd.DataFrame,
    role: str | None,
    grade: str | None,
    role_col: str = "primary_role",
    grade_col: str = "grade",
    skill_cols: list[str] | None = None,
    skill_prefixes: tuple[str, ...] = ("skill_", "has_", "soft_"),
) -> pd.DataFrame:
    """Compute per-skill market share for the specified segment."""

    filtered = df_features.copy()
    if role and role_col in filtered.columns:
        filtered = filtered[
            filtered[role_col].fillna("").str.lower() == role.strip().lower()
        ]
    if grade and grade_col in filtered.columns:
        filtered = filtered[
            filtered[grade_col].fillna("").str.lower() == grade.strip().lower()
        ]

    if skill_cols is None:
        skill_cols = [col for col in filtered.columns if col.startswith(skill_prefixes)]
    else:
        skill_cols = [col for col in skill_cols if col in filtered.columns]

    if filtered.empty or not skill_cols:
        return pd.DataFrame(columns=["skill", "market_share", "count"])

    skills_bool = filtered[skill_cols].fillna(False).astype(bool)
    share = skills_bool.mean()
    count = skills_bool.sum()

    profile = (
        pd.DataFrame(
            {
                "skill": share.index,
                "market_share": share.values,
                "count": count.values,
            }
        )
        .sort_values(by=["market_share", "count"], ascending=False)
        .reset_index(drop=True)
    )

    if profile.empty and (role or grade):
        # Fallback to the base implementation in case columns were missing upstream
        return _base_skill_profile(
            df_features,
            role=role,
            grade=grade,
            role_col=role_col,
            grade_col=grade_col,
            skill_cols=skill_cols,
        )

    return profile


def skill_gap_for_persona(
    df_features: pd.DataFrame,
    persona: Persona,
    top_k: int = 15,
    min_share: float = 0.05,
    role_col: str = "primary_role",
    grade_col: str = "grade",
    skill_cols: list[str] | None = None,
) -> pd.DataFrame:
    """
    Calculate market share of skills for persona targets and mark gaps.

    The function filters the feature dataframe by persona attributes (role, grade,
    custom constraints), builds a demand profile for the requested skills, and then
    flags which of them are missing for the persona.

    Returns columns: skill_name, market_share, persona_has (0/1), gap (bool).
    """

    df_filtered = _filter_by_target(
        df_features, persona, role_col=role_col, grade_col=grade_col
    )
    if df_filtered.empty:
        return pd.DataFrame(columns=["skill_name", "market_share", "persona_has", "gap"])

    demand_profile = build_skill_demand_profile(
        df_filtered,
        role=persona.target_role,
        grade=persona.target_grade,
        role_col=role_col,
        grade_col=grade_col,
        skill_cols=skill_cols,
    )

    if demand_profile.empty:
        return pd.DataFrame(columns=["skill_name", "market_share", "persona_has", "gap"])

    demand_profile = demand_profile[demand_profile["market_share"] >= min_share]
    if top_k:
        demand_profile = demand_profile.head(top_k)

    result = demand_profile.copy()
    result["skill_name"] = result["skill"]
    result["persona_has"] = result["skill_name"].apply(
        lambda skill: 1 if skill in persona.current_skills else 0
    )
    result["gap"] = result["persona_has"] == 0

    return result[["skill_name", "market_share", "persona_has", "gap"]]


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
    current_skills=["has_python", "skill_sql", "skill_excel", "skill_tableau"],
    target_role="data analyst",
    target_grade="junior",
    constraints={"work_mode": ["remote", "hybrid"], "city_tier": ["Moscow", "SPb"]},
)

CAREER_SWITCHER_BI_ANALYST = Persona(
    name="Career switcher → BI/Product analyst",
    current_skills=["skill_powerbi", "skill_sql", "skill_excel", "skill_tableau"],
    target_role="product analyst",
    target_grade="middle",
    constraints={"work_mode": ["hybrid", "office"], "city_tier": ["Moscow", "Million+"], "remote_only": False},
)

MID_DATA_ANALYST = Persona(
    name="Mid data analyst leveling up",
    current_skills=["skill_sql", "has_python", "skill_powerbi", "skill_excel", "skill_tableau"],
    target_role="data analyst",
    target_grade="middle",
    constraints={"work_mode": ["remote", "hybrid", "office"], "city_tier": ["Moscow", "SPb", "Million+", "Other RU"]},
)

REGIONAL_REMOTE_DA = Persona(
    name="Regional analyst → remote data role",
    current_skills=["skill_sql", "skill_excel", "has_python"],
    target_role="data analyst",
    target_grade="junior",
    constraints={"work_mode": ["remote"], "city_tier": ["Other RU", "Million+"], "remote_only": True},
)

PRODUCT_ANALYST_GROWTH = Persona(
    name="Product analyst aiming for growth",
    current_skills=["skill_sql", "skill_excel", "skill_powerbi", "has_python"],
    target_role="product analyst",
    target_grade="middle",
    constraints={"work_mode": ["hybrid", "office"], "city_tier": ["Moscow", "SPb"]},
)

PERSONAS = [
    DATA_STUDENT_JUNIOR_DA_DS,
    CAREER_SWITCHER_BI_ANALYST,
    MID_DATA_ANALYST,
    REGIONAL_REMOTE_DA,
    PRODUCT_ANALYST_GROWTH,
]

__all__ = [
    "Persona",
    "build_skill_demand_profile",
    "skill_gap_for_persona",
    "plot_persona_skill_gap",
    "DATA_STUDENT_JUNIOR_DA_DS",
    "CAREER_SWITCHER_BI_ANALYST",
    "MID_DATA_ANALYST",
    "REGIONAL_REMOTE_DA",
    "PRODUCT_ANALYST_GROWTH",
    "PERSONAS",
]
