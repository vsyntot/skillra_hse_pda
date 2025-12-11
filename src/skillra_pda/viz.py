"""Visualization utilities for reports."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import pandas as pd

from .config import FIGURES_DIR, ensure_directories


ensure_directories()


def _save_fig(fig: plt.Figure, filename: str | Path, close: bool = True) -> Path:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    filename_path = Path(filename)
    output = filename_path if filename_path.is_absolute() else FIGURES_DIR / filename_path
    fig.tight_layout()
    fig.savefig(output, dpi=200)
    if close:
        plt.close(fig)
    return output


def _finalize_figure(fig: plt.Figure, filename: str | Path, return_fig: bool = False):
    path = _save_fig(fig, filename, close=not return_fig)
    if return_fig:
        return fig, path
    return path


def _require_columns(df: pd.DataFrame, cols: Iterable[str], func_name: str) -> None:
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"{func_name}: expected columns {missing}, but they are missing")


def salary_by_grade_box(
    df: pd.DataFrame, salary_col: str = "salary_mid_rub_capped", return_fig: bool = False
):
    _require_columns(df, ["grade", salary_col], "salary_by_grade_box")
    fig, ax = plt.subplots(figsize=(8, 5))
    df.boxplot(column=salary_col, by="grade", ax=ax)
    ax.set_title("Salary by grade")
    ax.set_xlabel("Grade")
    ax.set_ylabel("Salary (RUB, capped)")
    fig.suptitle("")
    return _finalize_figure(fig, "fig_salary_by_grade_box.png", return_fig)


def salary_by_role_box(
    df: pd.DataFrame,
    salary_col: str = "salary_mid_rub_capped",
    top_n: int = 8,
    return_fig: bool = False,
):
    _require_columns(df, ["primary_role", salary_col], "salary_by_role_box")
    top_roles = df["primary_role"].value_counts().head(top_n).index
    filtered = df[df["primary_role"].isin(top_roles)]
    fig, ax = plt.subplots(figsize=(10, 6))
    filtered.boxplot(column=salary_col, by="primary_role", ax=ax, rot=45)
    ax.set_title("Salary by primary role (top roles)")
    ax.set_xlabel("Primary role")
    ax.set_ylabel("Salary (RUB, capped)")
    fig.suptitle("")
    return _finalize_figure(fig, "fig_salary_by_role_box.png", return_fig)


def salary_by_grade_city_heatmap(
    summary_df: pd.DataFrame, value_col: str = "median", return_fig: bool = False
):
    """Heatmap of salary metric by grade (rows) and city tier (columns)."""

    _require_columns(summary_df, ["grade", "city_tier", value_col], "salary_by_grade_city_heatmap")
    pivot = summary_df.pivot(index="grade", columns="city_tier", values=value_col)
    if pivot.empty:
        raise ValueError("salary_by_grade_city_heatmap: got empty pivot table")

    numeric = pivot.astype(float)
    fig, ax = plt.subplots(figsize=(9, 6))
    cax = ax.imshow(numeric.values, aspect="auto", cmap="coolwarm")
    ax.set_xticks(range(len(numeric.columns)))
    ax.set_xticklabels(numeric.columns)
    ax.set_yticks(range(len(numeric.index)))
    ax.set_yticklabels(numeric.index)
    fig.colorbar(cax, ax=ax, fraction=0.046, pad=0.04, label=f"Salary {value_col}")
    ax.set_title("Salary by grade and city tier")
    return _finalize_figure(fig, "fig_salary_by_grade_city_heatmap.png", return_fig)


def work_mode_share_by_city(df: pd.DataFrame, return_fig: bool = False):
    _require_columns(df, ["city_tier", "work_mode"], "work_mode_share_by_city")
    pivot = pd.crosstab(df["city_tier"], df["work_mode"], normalize="index")
    fig, ax = plt.subplots(figsize=(8, 5))
    pivot.plot(kind="bar", stacked=True, ax=ax)
    ax.set_ylabel("Share")
    ax.set_xlabel("City tier")
    ax.set_title("Work mode share by city tier")
    ax.legend(title="Work mode", bbox_to_anchor=(1.05, 1), loc="upper left")
    return _finalize_figure(fig, "fig_work_mode_share_by_city.png", return_fig)


def salary_by_role_work_mode_heatmap(
    summary_df: pd.DataFrame, value_col: str = "salary_median", return_fig: bool = False
):
    """Heatmap of salary metric by role (rows) and work mode (columns)."""

    _require_columns(summary_df, ["primary_role", "work_mode", value_col], "salary_by_role_work_mode_heatmap")
    pivot = summary_df.pivot(index="primary_role", columns="work_mode", values=value_col)
    if pivot.empty:
        raise ValueError("salary_by_role_work_mode_heatmap: got empty pivot table")

    numeric = pivot.astype(float)
    fig, ax = plt.subplots(figsize=(10, 6))
    cax = ax.imshow(numeric.values, aspect="auto", cmap="OrRd")
    ax.set_xticks(range(len(numeric.columns)))
    ax.set_xticklabels(numeric.columns)
    ax.set_yticks(range(len(numeric.index)))
    ax.set_yticklabels(numeric.index)
    fig.colorbar(cax, ax=ax, fraction=0.046, pad=0.04, label=f"Salary {value_col}")
    ax.set_title("Salary by role and work mode")
    return _finalize_figure(fig, "fig_salary_by_role_work_mode_heatmap.png", return_fig)


def remote_share_by_role_bar(remote_df: pd.DataFrame, return_fig: bool = False):
    """Bar chart of remote vacancy share by primary role."""

    _require_columns(remote_df, ["primary_role", "remote_share"], "remote_share_by_role_bar")
    ordered = remote_df.sort_values(by="remote_share", ascending=False)
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(ordered["primary_role"], ordered["remote_share"], color="teal")
    ax.set_ylabel("Remote share")
    ax.set_xlabel("Primary role")
    ax.set_title("Remote vacancy share by role")
    ax.tick_params(axis="x", rotation=45)
    return _finalize_figure(fig, "fig_remote_share_by_role.png", return_fig)


def top_skills_bar(
    df: pd.DataFrame,
    skill_cols: Iterable[str],
    role_filter: str = "data",
    top_n: int = 15,
    return_fig: bool = False,
):
    _require_columns(df, ["primary_role"], "top_skills_bar")
    missing_skills = [c for c in skill_cols if c not in df.columns]
    if missing_skills:
        raise ValueError(f"top_skills_bar: expected skill columns {missing_skills} to be present")
    role_mask = df["primary_role"].str.contains(role_filter, case=False, na=False)
    freq = df.loc[role_mask, skill_cols].sum().sort_values(ascending=False).head(top_n)
    fig, ax = plt.subplots(figsize=(8, 5))
    freq.plot(kind="bar", ax=ax)
    ax.set_ylabel("Count")
    ax.set_title(f"Top {top_n} skills for {role_filter} roles")
    return _finalize_figure(fig, "fig_top_skills_data_bar.png", return_fig)


def skill_premium_bar(premium_df: pd.DataFrame, top_n: int = 10, return_fig: bool = False):
    _require_columns(premium_df, ["skill", "premium_pct"], "skill_premium_bar")
    top = premium_df.sort_values(by="premium_pct", ascending=False).head(top_n)
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(top["skill"], top["premium_pct"])
    ax.set_ylabel("Premium (%)")
    ax.set_xlabel("Skill")
    ax.set_title("Top skill premium")
    plt.xticks(rotation=60, ha="right")
    return _finalize_figure(fig, "fig_skill_premium_bar.png", return_fig)


def corr_heatmap(corr: pd.DataFrame, return_fig: bool = False):
    if corr.empty:
        raise ValueError("corr_heatmap: expected non-empty correlation matrix")
    fig, ax = plt.subplots(figsize=(8, 6))
    cax = ax.imshow(corr, cmap="coolwarm", vmin=-1, vmax=1)
    ax.set_xticks(range(len(corr.columns)))
    ax.set_xticklabels(corr.columns, rotation=90)
    ax.set_yticks(range(len(corr.index)))
    ax.set_yticklabels(corr.index)
    fig.colorbar(cax, ax=ax, fraction=0.046, pad=0.04)
    ax.set_title("Correlation heatmap")
    return _finalize_figure(fig, "fig_corr_heatmap.png", return_fig)


def skill_heatmap(
    df: pd.DataFrame,
    index_col: str,
    skill_cols: Iterable[str],
    title: str,
    filename: str,
    top_n: int = 20,
    return_fig: bool = False,
) -> Path | tuple[plt.Figure, Path]:
    """Plot heatmap of skill prevalence across a categorical segment."""

    _require_columns(df, [index_col], "skill_heatmap")
    present_skills = [col for col in skill_cols if col in df.columns]
    if not present_skills:
        raise ValueError("skill_heatmap: expected at least one skill column")

    numeric_skills = df[present_skills].apply(pd.to_numeric, errors="coerce")
    freq = numeric_skills.mean().sort_values(ascending=False)
    top_skills = freq.head(top_n).index

    grouped = (
        pd.concat([df[[index_col]], numeric_skills[top_skills]], axis=1)
        .groupby(index_col)
        .mean()
    )
    pivot = grouped.fillna(0.0).astype(float)
    if pivot.empty:
        raise ValueError("Нет данных для построения heatmap")

    fig, ax = plt.subplots(figsize=(10, 6))
    cax = ax.imshow(pivot.values.astype(float), aspect="auto", cmap="Blues")
    ax.set_xticks(range(len(top_skills)))
    ax.set_xticklabels(top_skills, rotation=90)
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index)
    fig.colorbar(cax, ax=ax, fraction=0.046, pad=0.04, label="Share")
    ax.set_title(title)
    return _finalize_figure(fig, filename, return_fig=return_fig)


def salary_mean_and_count_bar(
    df: pd.DataFrame,
    category_col: str,
    salary_col: str = "salary_mid_rub_capped",
    top_n: int = 10,
    figsize: tuple[int, int] = (10, 6),
    output_path: Path | None = None,
    return_fig: bool = False,
) -> Path | tuple[plt.Figure, Path]:
    """Bar of median salary with vacancy counts on a twin axis for a category."""

    _require_columns(df, [category_col, salary_col], "salary_mean_and_count_bar")
    agg = df.groupby(category_col)[salary_col].agg(median="median", mean="mean", count="count")
    top = agg.sort_values(by="count", ascending=False).head(top_n)
    if top.empty:
        raise ValueError("salary_mean_and_count_bar: no data after aggregation")

    fig, ax1 = plt.subplots(figsize=figsize)
    ax1.bar(top.index, top["median"], color="steelblue")
    ax1.set_ylabel("Median salary (RUB)")
    ax1.set_xlabel(category_col)
    ax1.tick_params(axis="x", rotation=45)

    ax2 = ax1.twinx()
    ax2.plot(top.index, top["count"], color="darkorange", marker="o")
    ax2.set_ylabel("Vacancy count")

    ax1.set_title(f"Salary and vacancy count by {category_col}")
    filename = output_path or FIGURES_DIR / f"fig_salary_{category_col}_mean_count.png"
    return _finalize_figure(fig, filename, return_fig=return_fig)


def salary_by_city_mean_count_plot(
    df: pd.DataFrame,
    salary_col: str = "salary_mid_rub_capped",
    top_n: int = 10,
    figsize: tuple[int, int] = (10, 6),
    return_fig: bool = False,
) -> Path | tuple[plt.Figure, Path]:
    """Wrapper for salary mean/count by city tier."""

    return salary_mean_and_count_bar(
        df,
        category_col="city_tier",
        salary_col=salary_col,
        top_n=top_n,
        figsize=figsize,
        output_path=FIGURES_DIR / "fig_salary_by_city_mean_count.png",
        return_fig=return_fig,
    )


def salary_by_grade_mean_count_plot(
    df: pd.DataFrame,
    salary_col: str = "salary_mid_rub_capped",
    top_n: int = 10,
    figsize: tuple[int, int] = (10, 6),
    return_fig: bool = False,
) -> Path | tuple[plt.Figure, Path]:
    """Wrapper for salary mean/count by grade."""

    return salary_mean_and_count_bar(
        df,
        category_col="grade",
        salary_col=salary_col,
        top_n=top_n,
        figsize=figsize,
        output_path=FIGURES_DIR / "fig_salary_by_grade_mean_count.png",
        return_fig=return_fig,
    )


def salary_by_primary_role_mean_count_plot(
    df: pd.DataFrame,
    salary_col: str = "salary_mid_rub_capped",
    top_n: int = 10,
    figsize: tuple[int, int] = (10, 6),
    return_fig: bool = False,
) -> Path | tuple[plt.Figure, Path]:
    """Wrapper for salary mean/count by primary role."""

    return salary_mean_and_count_bar(
        df,
        category_col="primary_role",
        salary_col=salary_col,
        top_n=top_n,
        figsize=figsize,
        output_path=FIGURES_DIR / "fig_salary_by_primary_role_mean_count.png",
        return_fig=return_fig,
    )


def salary_by_employer_rating_plot(
    df: pd.DataFrame,
    salary_col: str = "salary_mid_rub_capped",
    top_n: int = 10,
    figsize: tuple[int, int] = (10, 6),
    return_fig: bool = False,
) -> Path | tuple[plt.Figure, Path]:
    """Wrapper for salary mean/count by employer rating buckets."""

    return salary_mean_and_count_bar(
        df,
        category_col="employer_rating",
        salary_col=salary_col,
        top_n=top_n,
        figsize=figsize,
        output_path=FIGURES_DIR / "fig_salary_by_employer_rating_mean_count.png",
        return_fig=return_fig,
    )


def salary_by_skills_bucket_plot(
    df: pd.DataFrame,
    salary_col: str = "salary_mid_rub_capped",
    top_n: int = 10,
    figsize: tuple[int, int] = (10, 6),
    return_fig: bool = False,
) -> Path | tuple[plt.Figure, Path]:
    """Wrapper for salary mean/count by tech stack size buckets."""

    category_col = "tech_stack_size"
    _require_columns(df, [category_col], "salary_by_skills_bucket_plot")
    # Bin stack size for readability
    bins = [-1, 2, 5, 10, df[category_col].max()] if not df[category_col].isna().all() else [-1, 0, 1]
    labels = ["0-2", "3-5", "6-10", "10+"] if len(bins) == 4 else ["0-1", "1+"]
    df_local = df.copy()
    df_local["stack_bucket"] = pd.cut(df_local[category_col].fillna(0), bins=bins, labels=labels, include_lowest=True)
    return salary_mean_and_count_bar(
        df_local,
        category_col="stack_bucket",
        salary_col=salary_col,
        top_n=top_n,
        figsize=figsize,
        output_path=FIGURES_DIR / "fig_salary_by_skills_bucket_mean_count.png",
        return_fig=return_fig,
    )


def salary_by_domain_plot(
    df: pd.DataFrame,
    top_n: int = 10,
    savepath: Path | None = None,
    priorities: list[str] | None = None,
    return_fig: bool = False,
) -> Path | tuple[plt.Figure, Path]:
    """Barplot of median salary by domain with vacancy counts on a twin axis.

    Args:
        df: Feature dataset containing ``domain_*`` columns and salaries.
        top_n: Number of domains to display.
        savepath: Optional custom output path.
        priorities: Optional ordered list of domain names (without ``domain_``
            prefix) to use when multiple domain flags are set for a vacancy.
    """

    from . import eda as eda_mod

    summary = eda_mod.describe_salary_by_domain(df, priorities=priorities)
    if summary.empty:
        raise ValueError("salary_by_domain_plot: expected domain_* columns and salary data")

    top = summary.sort_values(by="vacancy_count", ascending=False).head(top_n)
    fig, ax1 = plt.subplots(figsize=(10, 6))
    ax1.bar(top["domain"], top["salary_median"], color="steelblue")
    ax1.set_ylabel("Median salary (RUB)")
    ax1.set_xlabel("Domain")
    ax1.tick_params(axis="x", rotation=45, labelrotation=45)

    ax2 = ax1.twinx()
    ax2.plot(top["domain"], top["vacancy_count"], color="darkorange", marker="o")
    ax2.set_ylabel("Vacancy count")

    ax1.set_title("Salary by domain")
    filename = savepath or FIGURES_DIR / "fig_salary_by_domain.png"
    return _finalize_figure(fig, filename, return_fig=return_fig)


def salary_by_english_level_plot(
    df: pd.DataFrame, savepath: Path | None = None, return_fig: bool = False
) -> Path | tuple[plt.Figure, Path]:
    """Barplot of median salary by English level."""

    from . import eda as eda_mod

    summary = eda_mod.english_requirement_stats(df)
    if summary.empty:
        raise ValueError("salary_by_english_level_plot: expected lang_* columns and salary data")

    ordered = summary.sort_values(by="salary_median", ascending=False)
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.bar(ordered["english_level"], ordered["salary_median"], color="steelblue")
    ax.set_ylabel("Median salary (RUB)")
    ax.set_xlabel("English level")
    ax.tick_params(axis="x", rotation=45, labelrotation=45)
    ax.set_title("Salary by English level")

    filename = savepath or FIGURES_DIR / "fig_salary_by_english_level.png"
    return _finalize_figure(fig, filename, return_fig=return_fig)


def salary_by_education_level_plot(
    df: pd.DataFrame, savepath: Path | None = None, return_fig: bool = False
) -> Path | tuple[plt.Figure, Path]:
    """Barplot of median salary by education requirement level."""

    from . import eda as eda_mod

    summary = eda_mod.education_requirement_stats(df)
    if summary.empty:
        raise ValueError("salary_by_education_level_plot: expected edu_* columns and salary data")

    ordered = summary.sort_values(by="salary_median", ascending=False)
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.bar(ordered["education_level"], ordered["salary_median"], color="seagreen")
    ax.set_ylabel("Median salary (RUB)")
    ax.set_xlabel("Education level")
    ax.tick_params(axis="x", rotation=45, labelrotation=45)
    ax.set_title("Salary by education requirement")

    filename = savepath or FIGURES_DIR / "fig_salary_by_education_level.png"
    return _finalize_figure(fig, filename, return_fig=return_fig)


def heatmap_skills_by_grade(
    skill_share: pd.DataFrame,
    figsize: tuple[int, int] = (10, 6),
    output_path: Path | None = None,
    return_fig: bool = False,
) -> Path | tuple[plt.Figure, Path]:
    """Plot heatmap for skill (index) x grade (columns) share matrix."""

    if skill_share.empty:
        raise ValueError("heatmap_skills_by_grade: expected non-empty skill share matrix")
    if skill_share.columns.empty or skill_share.index.empty:
        raise ValueError("heatmap_skills_by_grade: matrix must have both index and columns")

    numeric = skill_share.astype(float)
    fig, ax = plt.subplots(figsize=figsize)
    cax = ax.imshow(numeric.values, aspect="auto", cmap="Blues")
    ax.set_xticks(range(len(numeric.columns)))
    ax.set_xticklabels(numeric.columns, rotation=90)
    ax.set_yticks(range(len(numeric.index)))
    ax.set_yticklabels(numeric.index)
    fig.colorbar(cax, ax=ax, fraction=0.046, pad=0.04, label="Share")
    ax.set_title("Skill share by grade")
    filename = output_path or FIGURES_DIR / "fig_skill_vs_grade_heatmap.png"
    return _finalize_figure(fig, filename, return_fig=return_fig)


def heatmap_benefits_by_company(
    benefits_df: pd.DataFrame,
    figsize: tuple[int, int] = (10, 6),
    output_path: Path | None = None,
    return_fig: bool = False,
) -> Path | tuple[plt.Figure, Path]:
    """Plot heatmap for company x benefits matrix."""

    if benefits_df.empty:
        raise ValueError("heatmap_benefits_by_company: expected non-empty matrix")
    if benefits_df.columns.empty or benefits_df.index.empty:
        raise ValueError("heatmap_benefits_by_company: matrix must have both index and columns")

    numeric = benefits_df.astype(float)
    fig, ax = plt.subplots(figsize=figsize)
    cax = ax.imshow(numeric.values, aspect="auto", cmap="Greens")
    ax.set_xticks(range(len(numeric.columns)))
    ax.set_xticklabels(numeric.columns, rotation=90)
    ax.set_yticks(range(len(numeric.index)))
    ax.set_yticklabels(numeric.index)
    fig.colorbar(cax, ax=ax, fraction=0.046, pad=0.04, label="Share")
    ax.set_title("Benefits prevalence by company")
    filename = output_path or FIGURES_DIR / "fig_benefits_by_company_heatmap.png"
    return _finalize_figure(fig, filename, return_fig=return_fig)


def benefits_employer_heatmap(
    df: pd.DataFrame,
    top_n_employers: int = 10,
    top_n_benefits: int = 12,
    figsize: tuple[int, int] = (12, 6),
    output_path: Path | None = None,
    return_fig: bool = False,
) -> Path | tuple[plt.Figure, Path]:
    """Plot heatmap of benefit prevalence for top employers."""

    from . import eda as eda_mod

    summary = eda_mod.benefits_by_employer(df, top_n=top_n_employers)
    if summary.empty:
        raise ValueError("benefits_employer_heatmap: expected benefit_* columns and company data")

    benefit_cols = [col for col in summary.columns if col.startswith("benefit_")]
    if not benefit_cols:
        raise ValueError("benefits_employer_heatmap: no benefit columns found after aggregation")

    benefit_order = summary[benefit_cols].mean().sort_values(ascending=False)
    top_benefits = benefit_order.head(top_n_benefits).index if top_n_benefits else benefit_cols

    pivot = summary.set_index("company")[list(top_benefits)]
    fig, ax = plt.subplots(figsize=figsize)
    cax = ax.imshow(pivot.values.astype(float), aspect="auto", cmap="Greens")
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns, rotation=90)
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index)
    fig.colorbar(cax, ax=ax, fraction=0.046, pad=0.04, label="Share")
    ax.set_title("Benefits by employer")
    filename = output_path or FIGURES_DIR / "fig_benefits_employer_heatmap.png"
    return _finalize_figure(fig, filename, return_fig=return_fig)


def heatmap_soft_skills_correlation(
    corr_df: pd.DataFrame,
    figsize: tuple[int, int] = (8, 6),
    output_path: Path | None = None,
    return_fig: bool = False,
) -> Path | tuple[plt.Figure, Path]:
    """Plot correlation heatmap for soft skill columns."""

    if corr_df.empty:
        raise ValueError("heatmap_soft_skills_correlation: expected non-empty correlation matrix")
    if corr_df.shape[0] != corr_df.shape[1]:
        raise ValueError("heatmap_soft_skills_correlation: matrix must be square")

    fig, ax = plt.subplots(figsize=figsize)
    cax = ax.imshow(corr_df.values.astype(float), cmap="coolwarm", vmin=-1, vmax=1)
    ax.set_xticks(range(len(corr_df.columns)))
    ax.set_xticklabels(corr_df.columns, rotation=90)
    ax.set_yticks(range(len(corr_df.index)))
    ax.set_yticklabels(corr_df.index)
    fig.colorbar(cax, ax=ax, fraction=0.046, pad=0.04)
    ax.set_title("Soft skills correlation")
    filename = output_path or FIGURES_DIR / "fig_soft_skills_corr_heatmap.png"
    return _finalize_figure(fig, filename, return_fig=return_fig)


def soft_skills_employer_heatmap(
    df: pd.DataFrame,
    top_n_employers: int = 10,
    top_n_skills: int = 12,
    figsize: tuple[int, int] = (12, 6),
    output_path: Path | None = None,
    return_fig: bool = False,
) -> Path | tuple[plt.Figure, Path]:
    """Plot heatmap of soft skill prevalence for top employers."""

    from . import eda as eda_mod

    summary = eda_mod.soft_skills_by_employer(df, top_n=top_n_employers)
    if summary.empty:
        raise ValueError("soft_skills_employer_heatmap: expected soft_* columns and company data")

    skill_cols = [col for col in summary.columns if col.startswith("soft_")]
    if not skill_cols:
        raise ValueError("soft_skills_employer_heatmap: no soft skill columns found after aggregation")

    skill_order = summary[skill_cols].mean().sort_values(ascending=False)
    top_skills = skill_order.head(top_n_skills).index if top_n_skills else skill_cols

    pivot = summary.set_index("company")[list(top_skills)]
    fig, ax = plt.subplots(figsize=figsize)
    cax = ax.imshow(pivot.values.astype(float), aspect="auto", cmap="Blues")
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns, rotation=90)
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index)
    fig.colorbar(cax, ax=ax, fraction=0.046, pad=0.04, label="Share")
    ax.set_title("Soft skills by employer")
    filename = output_path or FIGURES_DIR / "fig_soft_skills_employer_heatmap.png"
    return _finalize_figure(fig, filename, return_fig=return_fig)


def distribution_with_boxplot(
    df: pd.DataFrame,
    column: str,
    bins: int = 30,
    figsize: tuple[int, int] = (10, 6),
    output_path: Path | None = None,
    return_fig: bool = False,
) -> Path | tuple[plt.Figure, Path]:
    """Histogram plus boxplot for a numeric column."""

    _require_columns(df, [column], "distribution_with_boxplot")
    series = pd.to_numeric(df[column], errors="coerce").dropna()
    if series.empty:
        raise ValueError("distribution_with_boxplot: no numeric data to plot")

    fig, (ax_hist, ax_box) = plt.subplots(
        2, 1, figsize=figsize, gridspec_kw={"height_ratios": [3, 1]}, sharex=True
    )
    ax_hist.hist(series, bins=bins, color="steelblue", edgecolor="white")
    ax_hist.set_ylabel("Count")
    ax_hist.set_title(f"Distribution of {column}")

    ax_box.boxplot(series, vert=False)
    ax_box.set_xlabel(column)

    filename = output_path or FIGURES_DIR / f"fig_dist_{column}.png"
    return _finalize_figure(fig, filename, return_fig=return_fig)
