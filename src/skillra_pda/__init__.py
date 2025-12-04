"""Skillra HSE Python for Data Analysis utilities."""

# Re-export commonly used modules and helpers to simplify notebook imports.
from . import cleaning, config, eda, features, io, personas, viz  # noqa: F401
from .cleaning import ensure_salary_gross_boolean  # noqa: F401
from .eda import junior_friendly_share  # noqa: F401
from .features import ensure_expected_feature_columns  # noqa: F401

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
    "ensure_expected_feature_columns",
]
