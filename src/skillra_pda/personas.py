"""Product-oriented persona utilities."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

import pandas as pd


@dataclass
class Persona:
    name: str
    description: str
    current_skills: List[str]
    target_filter: Dict[str, object] = field(default_factory=dict)

    def __init__(self, name: str, current_skills: List[str], target_filter: Dict[str, object] | None = None, description: str = ""):
        # Explicit __init__ keeps compatibility with older notebook checkpoints that may still
        # instantiate Persona with or without a description keyword.
        self.name = name
        self.description = description
        self.current_skills = list(current_skills)
        self.target_filter = target_filter or {}


__all__ = ["Persona", "skill_gap_for_persona", "plot_persona_skill_gap"]


def skill_gap_for_persona(df: pd.DataFrame, persona: Persona, top_k: int = 10) -> pd.DataFrame:
    """Calculate skill gaps for a given persona with market prevalence."""

    df_filtered = df.copy()
    for key, value in persona.target_filter.items():
        if key not in df_filtered.columns:
            continue
        if isinstance(value, (list, tuple, set)):
            df_filtered = df_filtered[df_filtered[key].isin(value)]
        else:
            df_filtered = df_filtered[df_filtered[key] == value]

    skill_cols = [col for col in df_filtered.columns if col.startswith("skill_") or col.startswith("has_")]
    if not skill_cols:
        return pd.DataFrame(columns=["skill_name", "market_share", "persona_has", "gap"])

    freq = df_filtered[skill_cols].mean().sort_values(ascending=False).head(top_k)

    rows = []
    for skill, market_share in freq.items():
        persona_has = 1 if skill in persona.current_skills else 0
        rows.append(
            {
                "skill_name": skill,
                "market_share": market_share,
                "persona_has": persona_has,
                "gap": not bool(persona_has),
            }
        )
    return pd.DataFrame(rows)


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
