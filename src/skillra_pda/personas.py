"""Product-oriented persona utilities."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

import pandas as pd


@dataclass
class Persona:
    """Persona definition for skill-gap analysis."""

    name: str
    description: str
    current_skills: List[str]
    target_filter: Dict[str, object] = field(default_factory=dict)


__all__ = ["Persona", "skill_gap_for_persona", "plot_persona_skill_gap"]


def _filter_by_target(df: pd.DataFrame, target_filter: Dict[str, object]) -> pd.DataFrame:
    filtered = df.copy()
    for key, value in target_filter.items():
        if key not in filtered.columns:
            continue
        if isinstance(value, (list, tuple, set)):
            filtered = filtered[filtered[key].isin(value)]
        else:
            filtered = filtered[filtered[key] == value]
    return filtered


def skill_gap_for_persona(
    df: pd.DataFrame, persona: Persona, skill_cols: List[str], min_share: float = 0.1
) -> pd.DataFrame:
    """
    Calculate market share of skills for persona targets and mark gaps.

    Returns columns: skill_name, market_share, persona_has (0/1), gap (bool).
    """

    df_filtered = _filter_by_target(df, persona.target_filter)
    present_skills = [col for col in skill_cols if col in df_filtered.columns]
    if not present_skills:
        return pd.DataFrame(columns=["skill_name", "market_share", "persona_has", "gap"])

    rows: list[dict[str, object]] = []
    for col in present_skills:
        share = df_filtered[col].fillna(False).astype(bool).mean()
        persona_has = 1 if col in persona.current_skills else 0
        rows.append(
            {
                "skill_name": col,
                "market_share": share,
                "persona_has": persona_has,
                "gap": persona_has == 0 and share >= min_share,
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
