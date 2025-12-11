"""Product-oriented persona utilities for Skillra."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Mapping

import pandas as pd

from . import config


@dataclass
class Persona:
    """Persona definition for skill-gap and market analysis."""

    name: str
    description: str
    current_skills: List[str]
    target_role: str
    target_grade: str | None = None
    target_city_tier: str | None = None
    target_work_mode: str | None = None
    constraints: Dict[str, object] = field(default_factory=dict)
    goals: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)

    # Backward compatibility: expose target_filter as a property to avoid breaking old callers
    @property
    def target_filter(self) -> Dict[str, object]:  # pragma: no cover - legacy shim
        filt: Dict[str, object] = {}
        if self.target_role:
            filt["primary_role"] = self.target_role
        if self.target_grade:
            filt["grade"] = self.target_grade
        if self.target_city_tier:
            filt["city_tier"] = self.target_city_tier
        if self.target_work_mode:
            filt["work_mode"] = self.target_work_mode
        filt.update(self.constraints)
        return filt


__all__ = [
    "Persona",
    "build_skill_demand_profile",
    "skill_gap_for_persona",
    "analyze_persona",
    "plot_persona_skill_gap",
    "DATA_STUDENT",
    "SWITCHER_BI",
    "MID_DATA_ANALYST",
]


def _filter_by_target(df: pd.DataFrame, persona: Persona) -> pd.DataFrame:
    """Filter a dataframe by persona targets and constraints."""

    filtered = df.copy()
    mapping: Mapping[str, Any] = {
        "primary_role": persona.target_role,
        "grade": persona.target_grade,
        "city_tier": persona.target_city_tier,
        "work_mode": persona.target_work_mode,
    }
    for col, value in mapping.items():
        if value is None or col not in filtered.columns:
            continue
        if isinstance(value, (list, tuple, set)):
            filtered = filtered[filtered[col].isin(value)]
        else:
            filtered = filtered[filtered[col] == value]

    for key, value in persona.constraints.items():
        if key not in filtered.columns:
            continue
        if isinstance(value, (list, tuple, set)):
            filtered = filtered[filtered[key].isin(value)]
        else:
            filtered = filtered[filtered[key] == value]
    return filtered


def build_skill_demand_profile(
    df: pd.DataFrame,
    persona: Persona,
    skill_prefixes: tuple[str, ...] = ("has_", "skill_"),
    min_share: float = 0.05,
) -> pd.DataFrame:
    """Compute market demand for skills in the persona's target segment."""

    df_filtered = _filter_by_target(df, persona)
    if df_filtered.empty:
        return pd.DataFrame(columns=["skill_name", "market_share"])

    skill_cols = [c for c in df_filtered.columns if c.startswith(skill_prefixes)]
    rows: list[dict[str, object]] = []
    for col in skill_cols:
        series = df_filtered[col].fillna(False)
        try:
            share = series.astype(bool).mean()
        except Exception:
            continue
        if share < min_share:
            continue
        rows.append({"skill_name": col, "market_share": share})

    demand = pd.DataFrame(rows)
    if demand.empty:
        return demand
    return demand.sort_values(by="market_share", ascending=False).reset_index(drop=True)


def skill_gap_for_persona(
    df: pd.DataFrame,
    persona: Persona,
    skill_cols: List[str] | None = None,
    min_share: float = 0.1,
    top_n: int | None = 20,
) -> pd.DataFrame:
    """
    Calculate market share of skills for persona targets and mark gaps.

    Returns columns: skill_name, market_share, persona_has (bool), gap (bool).
    """

    demand = build_skill_demand_profile(
        df, persona, skill_prefixes=("has_", "skill_"), min_share=min_share
    )
    if skill_cols:
        demand = demand[demand["skill_name"].isin(skill_cols)]

    if demand.empty:
        return pd.DataFrame(columns=["skill_name", "market_share", "persona_has", "gap"])

    demand["persona_has"] = demand["skill_name"].isin(persona.current_skills)
    demand["gap"] = ~demand["persona_has"] & (demand["market_share"] >= min_share)
    demand_sorted = demand.sort_values(by="market_share", ascending=False)
    if top_n is not None:
        demand_sorted = demand_sorted.head(top_n)
    return demand_sorted.reset_index(drop=True)


def analyze_persona(df: pd.DataFrame, persona: Persona, top_k: int = 10) -> dict:
    """Summarize market segment and skill gaps for a persona.

    Returns a dictionary with three core blocks:
    * ``market_summary`` — aggregated metrics for the target segment;
    * ``skill_gap`` — dataframe with market share, persona possession and gap flag;
    * ``recommended_skills`` — ordered list of missing skills to focus on.
    """

    df_filtered = _filter_by_target(df, persona)
    market_summary: dict[str, object] = {
        "vacancy_count": len(df_filtered),
    }
    salary_col = "salary_mid_rub_capped" if "salary_mid_rub_capped" in df_filtered.columns else None
    if salary_col:
        market_summary.update(
            {
                "salary_median": df_filtered[salary_col].median(),
                "salary_q25": df_filtered[salary_col].quantile(0.25),
                "salary_q75": df_filtered[salary_col].quantile(0.75),
            }
        )
    if "is_remote" in df_filtered.columns:
        market_summary["remote_share"] = df_filtered["is_remote"].fillna(False).astype(bool).mean()
    if "is_junior_friendly" in df_filtered.columns:
        market_summary["junior_friendly_share"] = (
            df_filtered["is_junior_friendly"].fillna(False).astype(bool).mean()
        )

    demand_df = build_skill_demand_profile(
        df_filtered, persona, skill_prefixes=("has_", "skill_"), min_share=0.05
    )
    top_demand = demand_df.head(top_k) if not demand_df.empty else pd.DataFrame()

    gap_df = skill_gap_for_persona(df_filtered, persona, min_share=0.05, top_n=top_k)
    recommended_skills: list[str] = gap_df.loc[gap_df["gap"], "skill_name"].head(top_k).tolist()

    return {
        "market_summary": market_summary,
        "skill_gap": gap_df,
        "recommended_skills": recommended_skills,
        "top_skill_demand": top_demand,
    }


def plot_persona_skill_gap(
    gap_df: pd.DataFrame,
    persona: Persona,
    output_dir: Path | None = None,
    return_fig: bool = False,
) -> Path | tuple[plt.Figure, Path]:
    """Plot top missing skills for a persona and optionally return a Figure."""

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

    output_dir = output_dir or config.FIGURES_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"fig_persona_{persona.name.lower().replace(' ', '_')}_skill_gap.png"
    fig.tight_layout()
    fig.savefig(output_path, dpi=200)
    if not return_fig:
        plt.close(fig)
        return output_path
    return fig, output_path


# Pre-defined personas for quick experimentation in the notebook/product layer.
DATA_STUDENT = Persona(
    name="data_student",
    description="Магистрант по данным, целится в Junior DA/DS",
    goals=[
        "Получить первую роль Junior DA/DS",
        "Подтянуть Python/SQL и продуктовую аналитику",
    ],
    limitations=["Неполная занятость из-за учёбы", "Ориентация на remote"],
    current_skills=["skill_sql", "skill_excel", "has_python"],
    target_role="analyst",
    target_grade="junior",
    target_city_tier="Moscow",
    target_work_mode="remote",
)

SWITCHER_BI = Persona(
    name="switcher_bi",
    description="Свитчер в продуктовую/BI-аналитику",
    goals=["Перейти из смежной сферы в BI/продуктовую аналитику"],
    limitations=["Нужно быстро выйти на работу", "Ставка на гибрид или офис"],
    current_skills=["skill_excel", "skill_powerbi"],
    target_role="product",
    target_grade="junior",
    target_city_tier=None,
    target_work_mode=None,
)

MID_DATA_ANALYST = Persona(
    name="mid_data_analyst",
    description="Middle аналитик, хочет усилить hard-стек",
    goals=["Выйти на позиции middle+", "Усилить ML/продвинутое моделирование"],
    limitations=["Рассматривает офис/гибрид", "Хочет рост зарплаты"],
    current_skills=["skill_sql", "skill_excel", "skill_powerbi"],
    target_role="analyst",
    target_grade="middle",
    target_city_tier=None,
    target_work_mode=None,
)
