"""rclea_core — RCLEA calculation engine (educational remake).

This package is intentionally UI-free: no terminal output, no web calls.
It is imported by both the CLI (`rclea_cli`) and the web app (via Pyodide).
"""
from rclea_core.analysis import compute_rsgvs, find_worst_case
from rclea_core.assessment import run_assessment
from rclea_core.disclaimer import DISCLAIMER_FULL, DISCLAIMER_SHORT
from rclea_core.loader import load_dataset
from rclea_core.models import (
    AgeGroup,
    AssessmentInput,
    AssessmentMode,
    AssessmentResult,
    Isotope,
    PathwayResult,
    RadonMode,
    RSGVReport,
    Scenario,
    Sex,
    WorstCaseEntry,
    WorstCaseReport,
)

__all__ = [
    "AgeGroup",
    "AssessmentInput",
    "AssessmentMode",
    "AssessmentResult",
    "DISCLAIMER_FULL",
    "DISCLAIMER_SHORT",
    "Isotope",
    "PathwayResult",
    "RadonMode",
    "RSGVReport",
    "Scenario",
    "Sex",
    "WorstCaseEntry",
    "WorstCaseReport",
    "compute_rsgvs",
    "find_worst_case",
    "load_dataset",
    "run_assessment",
]

__version__ = "0.1.0"
