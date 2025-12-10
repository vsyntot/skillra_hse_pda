"""Visualization utilities for reports."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import pandas as pd

from .config import FIGURES_DIR, ensure_directories


ensure_directories()


def _save_fig(fig: plt.Figure, filename: str | Path) -> Path:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    filename_path = Path(filename)
    output = filename_path if filename_path.is_absolute() else FIGURES_DIR / filename_path
    fig.tight_layout()
    fig.savefig(output, dpi=200)
    plt.close(fig)
    return output


def _require_columns(df: pd.DataFrame, cols: Iterable[str], func_name: str) -> None:
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"{func_name}: expected columns {missing}, but they are missing")


def salary_by_grade_box(df: pd.DataFrame, salary_col: str = "salary_mid_rub_capped") -> Path:
    _require_columns(df, ["grade", salary_col], "salary_by_grade_box")
    fig, ax = plt.subplots(figsize=(8, 5))
    df.boxplot(column=salary_col, by="grade", ax=ax)
    ax.set_title("Salary by grade")
    ax.set_xlabel("Grade")
    ax.set_ylabel("Salary (RUB, capped)")
    fig.suptitle("")
    return _save_fig(fig, "fig_salary_by_grade_box.png")


def salary_by_role_box(df: pd.DataFrame, salary_col: str = "salary_mid_rub_capped", top_n: int = 8) -> Path:
    _require_columns(df, ["primary_role", salary_col], "salary_by_role_box")
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
    _require_columns(df, ["city_tier", "work_mode"], "work_mode_share_by_city")
    pivot = pd.crosstab(df["city_tier"], df["work_mode"], normalize="index")
    fig, ax = plt.subplots(figsize=(8, 5))
    pivot.plot(kind="bar", stacked=True, ax=ax)
    ax.set_ylabel("Share")
    ax.set_xlabel("City tier")
    ax.set_title("Work mode share by city tier")
    ax.legend(title="Work mode", bbox_to_anchor=(1.05, 1), loc="upper left")
    return _save_fig(fig, "fig_work_mode_share_by_city.png")


def top_skills_bar(df: pd.DataFrame, skill_cols: Iterable[str], role_filter: str = "data", top_n: int = 15) -> Path:
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
    return _save_fig(fig, "fig_top_skills_data_bar.png")


def skill_premium_bar(premium_df: pd.DataFrame, top_n: int = 10) -> Path:
    _require_columns(premium_df, ["skill", "premium_pct"], "skill_premium_bar")
    top = premium_df.sort_values(by="premium_pct", ascending=False).head(top_n)
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(top["skill"], top["premium_pct"])
    ax.set_ylabel("Premium (%)")
    ax.set_xlabel("Skill")
    ax.set_title("Top skill premium")
    plt.xticks(rotation=60, ha="right")
    return _save_fig(fig, "fig_skill_premium_bar.png")


def corr_heatmap(corr: pd.DataFrame) -> Path:
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
    return _save_fig(fig, "fig_corr_heatmap.png")


def skill_heatmap(
    df: pd.DataFrame,
    index_col: str,
    skill_cols: Iterable[str],
    title: str,
    filename: str,
    top_n: int = 20,
) -> Path:
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
    return _save_fig(fig, filename)


def salary_mean_and_count_bar(
    df: pd.DataFrame,
    category_col: str,
    salary_col: str = "salary_mid_rub_capped",
    top_n: int = 10,
    figsize: tuple[int, int] = (10, 6),
    output_path: Path | None = None,
) -> Path:
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
    return _save_fig(fig, filename)


def salary_by_city_mean_count_plot(
    df: pd.DataFrame,
    salary_col: str = "salary_mid_rub_capped",
    top_n: int = 10,
    figsize: tuple[int, int] = (10, 6),
) -> Path:
    """Wrapper for salary mean/count by city tier."""

    return salary_mean_and_count_bar(
        df,
        category_col="city_tier",
        salary_col=salary_col,
        top_n=top_n,
        figsize=figsize,
        output_path=FIGURES_DIR / "fig_salary_by_city_mean_count.png",
    )


def salary_by_grade_mean_count_plot(
    df: pd.DataFrame,
    salary_col: str = "salary_mid_rub_capped",
    top_n: int = 10,
    figsize: tuple[int, int] = (10, 6),
) -> Path:
    """Wrapper for salary mean/count by grade."""

    return salary_mean_and_count_bar(
        df,
        category_col="grade",
        salary_col=salary_col,
        top_n=top_n,
        figsize=figsize,
        output_path=FIGURES_DIR / "fig_salary_by_grade_mean_count.png",
    )


def salary_by_primary_role_mean_count_plot(
    df: pd.DataFrame,
    salary_col: str = "salary_mid_rub_capped",
    top_n: int = 10,
    figsize: tuple[int, int] = (10, 6),
) -> Path:
    """Wrapper for salary mean/count by primary role."""

    return salary_mean_and_count_bar(
        df,
        category_col="primary_role",
        salary_col=salary_col,
        top_n=top_n,
        figsize=figsize,
        output_path=FIGURES_DIR / "fig_salary_by_primary_role_mean_count.png",
    )


def salary_by_employer_rating_plot(
    df: pd.DataFrame,
    salary_col: str = "salary_mid_rub_capped",
    top_n: int = 10,
    figsize: tuple[int, int] = (10, 6),
) -> Path:
    """Wrapper for salary mean/count by employer rating buckets."""

    return salary_mean_and_count_bar(
        df,
        category_col="employer_rating",
        salary_col=salary_col,
        top_n=top_n,
        figsize=figsize,
        output_path=FIGURES_DIR / "fig_salary_by_employer_rating_mean_count.png",
    )


def salary_by_skills_bucket_plot(
    df: pd.DataFrame,
    salary_col: str = "salary_mid_rub_capped",
    top_n: int = 10,
    figsize: tuple[int, int] = (10, 6),
) -> Path:
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
    )


def salary_by_domain_plot(df: pd.DataFrame, top_n: int = 10, savepath: Path | None = None) -> Path:
    """Barplot of median salary by domain with vacancy counts on a twin axis."""

    from . import eda as eda_mod

    summary = eda_mod.describe_salary_by_domain(df)
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
    return _save_fig(fig, filename)


def salary_by_english_level_plot(
    df: pd.DataFrame, salary_col: str = "salary_mid_rub_capped", savepath: Path | None = None
) -> Path:
    """Plot median salary by normalized English level requirements."""

    from . import eda as eda_mod

    stats = eda_mod.english_requirement_stats(df, salary_col=salary_col)
    if stats.empty:
        raise ValueError("salary_by_english_level_plot: expected non-empty English stats")

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(stats["english_level"], stats["salary_median"], color="steelblue")
    ax.set_xlabel("English level")
    ax.set_ylabel("Median salary (RUB)")
    ax.set_title("Salary by English level requirement")
    plt.xticks(rotation=45, ha="right")

    filename = savepath or FIGURES_DIR / "fig_salary_by_english_level.png"
    return _save_fig(fig, filename)


def salary_by_education_level_plot(
    df: pd.DataFrame, salary_col: str = "salary_mid_rub_capped", savepath: Path | None = None
) -> Path:
    """Plot median salary by education requirement buckets."""

    from . import eda as eda_mod

    stats = eda_mod.education_requirement_stats(df, salary_col=salary_col)
    if stats.empty:
        raise ValueError("salary_by_education_level_plot: expected non-empty education stats")

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(stats["education_requirement"], stats["salary_median"], color="steelblue")
    ax.set_xlabel("Education requirement")
    ax.set_ylabel("Median salary (RUB)")
    ax.set_title("Salary by education requirement")
    plt.xticks(rotation=45, ha="right")

    filename = savepath or FIGURES_DIR / "fig_salary_by_education_level.png"
    return _save_fig(fig, filename)


def heatmap_skills_by_grade(
    skill_share: pd.DataFrame, figsize: tuple[int, int] = (10, 6), output_path: Path | None = None
) -> Path:
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
    return _save_fig(fig, filename)


def heatmap_benefits_by_company(
    benefits_df: pd.DataFrame, figsize: tuple[int, int] = (10, 6), output_path: Path | None = None
) -> Path:
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
    return _save_fig(fig, filename)


def heatmap_soft_skills_correlation(
    corr_df: pd.DataFrame, figsize: tuple[int, int] = (8, 6), output_path: Path | None = None
) -> Path:
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
    return _save_fig(fig, filename)


def benefits_employer_heatmap(
    df: pd.DataFrame, top_n: int = 10, savepath: Path | None = None
) -> Path:
    """Heatmap of benefit prevalence by employer for top companies."""

    from . import eda as eda_mod

    _require_columns(df, ["company"], "benefits_employer_heatmap")
    benefit_cols = [col for col in df.columns if col.startswith("benefit_")]
    if not benefit_cols:
        raise ValueError("benefits_employer_heatmap: expected benefit_ columns in dataframe")

    pivot = eda_mod.benefits_by_employer(df, top_n=top_n)
    if pivot.empty:
        raise ValueError("benefits_employer_heatmap: no data to plot")

    numeric = pivot.astype(float)
    fig, ax = plt.subplots(figsize=(10, 6))
    cax = ax.imshow(numeric.values, aspect="auto", cmap="Greens")
    ax.set_xticks(range(len(numeric.columns)))
    ax.set_xticklabels(numeric.columns, rotation=90)
    ax.set_yticks(range(len(numeric.index)))
    ax.set_yticklabels(numeric.index)
    fig.colorbar(cax, ax=ax, fraction=0.046, pad=0.04, label="Share")
    ax.set_title("Benefits share by employer")

    filename = savepath or FIGURES_DIR / "fig_benefits_by_employer_heatmap.png"
    return _save_fig(fig, filename)


def soft_skills_employer_heatmap(
    df: pd.DataFrame, top_n: int = 10, savepath: Path | None = None
) -> Path:
    """Heatmap of soft skill prevalence by employer for top companies."""

    from . import eda as eda_mod

    _require_columns(df, ["company"], "soft_skills_employer_heatmap")
    soft_cols = [col for col in df.columns if col.startswith("soft_")]
    if not soft_cols:
        raise ValueError("soft_skills_employer_heatmap: expected soft_ columns in dataframe")

    pivot = eda_mod.soft_skills_by_employer(df, top_n=top_n)
    if pivot.empty:
        raise ValueError("soft_skills_employer_heatmap: no data to plot")

    numeric = pivot.astype(float)
    fig, ax = plt.subplots(figsize=(10, 6))
    cax = ax.imshow(numeric.values, aspect="auto", cmap="Purples")
    ax.set_xticks(range(len(numeric.columns)))
    ax.set_xticklabels(numeric.columns, rotation=90)
    ax.set_yticks(range(len(numeric.index)))
    ax.set_yticklabels(numeric.index)
    fig.colorbar(cax, ax=ax, fraction=0.046, pad=0.04, label="Share")
    ax.set_title("Soft skills share by employer")

    filename = savepath or FIGURES_DIR / "fig_soft_skills_by_employer_heatmap.png"
    return _save_fig(fig, filename)


def distribution_with_boxplot(
    df: pd.DataFrame,
    column: str,
    bins: int = 30,
    figsize: tuple[int, int] = (10, 6),
    output_path: Path | None = None,
) -> Path:
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
    return _save_fig(fig, filename)
