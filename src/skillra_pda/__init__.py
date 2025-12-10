"""Skillra HSE Python for Data Analysis utilities."""

# Re-export commonly used modules and helpers to simplify notebook imports.
from . import cleaning, config, eda, features, io, personas, viz  # noqa: F401
from .cleaning import ensure_salary_gross_boolean  # noqa: F401
from .eda import (  # noqa: F401
    benefits_summary_by_company,
    benefits_summary_by_grade,
    correlation_matrix,
    junior_friendly_share,
    junior_friendly_share_by_segment,
    salary_by_city_tier,
    salary_by_english_level,
    salary_by_experience_bucket,
    salary_by_grade,
    salary_by_primary_role,
    salary_by_stack_size,
    salary_summary_by_category,
    salary_summary_by_grade_and_city,
    salary_summary_by_role_and_work_mode,
    skill_frequency,
    skill_share_by_grade,
    soft_skills_by_employer,
    soft_skills_correlation,
    soft_skills_overall_stats,
)
from .features import ensure_expected_feature_columns  # noqa: F401
from .personas import (  # noqa: F401
    CAREER_SWITCHER_BI_ANALYST,
    DATA_STUDENT_JUNIOR_DA_DS,
    MID_DATA_ANALYST,
    PERSONAS,
    Persona,
)
from .viz import skill_heatmap  # noqa: F401

__all__ = [
    "cleaning",
    "config",
    "eda",
    "features",
    "io",
    "personas",
    "viz",
    "ensure_salary_gross_boolean",
    "junior_friendly_share",
    "junior_friendly_share_by_segment",
    "salary_by_city_tier",
    "salary_by_experience_bucket",
    "salary_by_grade",
    "salary_by_primary_role",
    "salary_by_stack_size",
    "salary_by_english_level",
    "salary_summary_by_category",
    "salary_summary_by_grade_and_city",
    "salary_summary_by_role_and_work_mode",
    "benefits_summary_by_company",
    "benefits_summary_by_grade",
    "soft_skills_overall_stats",
    "soft_skills_by_employer",
    "soft_skills_correlation",
    "correlation_matrix",
    "skill_frequency",
    "skill_share_by_grade",
    "skill_heatmap",
    "ensure_expected_feature_columns",
    "Persona",
    "DATA_STUDENT_JUNIOR_DA_DS",
    "CAREER_SWITCHER_BI_ANALYST",
    "MID_DATA_ANALYST",
    "PERSONAS",
]
