"""Visualization utilities for reports."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import pandas as pd

from .config import FIGURES_DIR, ensure_directories


ensure_directories()


def _save_fig(fig: plt.Figure, filename: str) -> Path:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    output = FIGURES_DIR / filename
    fig.tight_layout()
    fig.savefig(output, dpi=200)
    plt.close(fig)
    return output


def salary_by_grade_box(df: pd.DataFrame, salary_col: str = "salary_mid_rub_capped") -> Path:
    fig, ax = plt.subplots(figsize=(8, 5))
    df.boxplot(column=salary_col, by="grade", ax=ax)
    ax.set_title("Salary by grade")
    ax.set_xlabel("Grade")
    ax.set_ylabel("Salary (RUB, capped)")
    fig.suptitle("")
    return _save_fig(fig, "fig_salary_by_grade_box.png")


def salary_by_role_box(df: pd.DataFrame, salary_col: str = "salary_mid_rub_capped", top_n: int = 8) -> Path:
    top_roles = df["primary_role"].value_counts().head(top_n).index
    filtered = df[df["primary_role"].isin(top_roles)]
    fig, ax = plt.subplots(figsize=(10, 6))
    filtered.boxplot(column=salary_col, by="primary_role", ax=ax, rot=45)
    ax.set_title("Salary by primary role (top roles)")
    ax.set_xlabel("Primary role")
    ax.set_ylabel("Salary (RUB, capped)")
    fig.suptitle("")
    return _save_fig(fig, "fig_salary_by_role_box.png")


def work_mode_share_by_city(df: pd.DataFrame) -> Path:
    pivot = pd.crosstab(df["city_tier"], df["work_mode"], normalize="index")
    fig, ax = plt.subplots(figsize=(8, 5))
    pivot.plot(kind="bar", stacked=True, ax=ax)
    ax.set_ylabel("Share")
    ax.set_xlabel("City tier")
    ax.set_title("Work mode share by city tier")
    ax.legend(title="Work mode", bbox_to_anchor=(1.05, 1), loc="upper left")
    return _save_fig(fig, "fig_work_mode_share_by_city.png")


def top_skills_bar(df: pd.DataFrame, skill_cols: Iterable[str], role_filter: str = "data", top_n: int = 15) -> Path:
    role_mask = df["primary_role"].str.contains(role_filter, case=False, na=False)
    freq = df.loc[role_mask, skill_cols].sum().sort_values(ascending=False).head(top_n)
    fig, ax = plt.subplots(figsize=(8, 5))
    freq.plot(kind="bar", ax=ax)
    ax.set_ylabel("Count")
    ax.set_title(f"Top {top_n} skills for {role_filter} roles")
    return _save_fig(fig, "fig_top_skills_data_bar.png")


def skill_premium_bar(premium_df: pd.DataFrame, top_n: int = 10) -> Path:
    top = premium_df.sort_values(by="premium_pct", ascending=False).head(top_n)
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(top["skill"], top["premium_pct"])
    ax.set_ylabel("Premium (%)")
    ax.set_xlabel("Skill")
    ax.set_title("Top skill premium")
    plt.xticks(rotation=60, ha="right")
    return _save_fig(fig, "fig_skill_premium_bar.png")


def corr_heatmap(corr: pd.DataFrame) -> Path:
    fig, ax = plt.subplots(figsize=(8, 6))
    cax = ax.imshow(corr, cmap="coolwarm", vmin=-1, vmax=1)
    ax.set_xticks(range(len(corr.columns)))
    ax.set_xticklabels(corr.columns, rotation=90)
    ax.set_yticks(range(len(corr.index)))
    ax.set_yticklabels(corr.index)
    fig.colorbar(cax, ax=ax, fraction=0.046, pad=0.04)
    ax.set_title("Correlation heatmap")
    return _save_fig(fig, "fig_corr_heatmap.png")
