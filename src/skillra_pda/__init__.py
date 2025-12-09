"""Skillra HSE Python for Data Analysis utilities."""

# Re-export commonly used modules and helpers to simplify notebook imports.
from . import cleaning, config, eda, features, io, personas, viz  # noqa: F401
from .cleaning import ensure_salary_gross_boolean  # noqa: F401
from .eda import (  # noqa: F401
    junior_friendly_share,
    salary_by_city_tier,
    salary_by_experience_bucket,
    salary_by_grade,
    salary_by_primary_role,
    salary_by_stack_size,
)
from .features import ensure_expected_feature_columns  # noqa: F401
from .personas import Persona  # noqa: F401
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
    "salary_by_city_tier",
    "salary_by_experience_bucket",
    "salary_by_grade",
    "salary_by_primary_role",
    "salary_by_stack_size",
    "skill_heatmap",
    "ensure_expected_feature_columns",
    "Persona",
]
