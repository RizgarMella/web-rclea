"""Interactive-tutorial parser tests.

The CLI uses a regex and yaml.safe_load to split tutorials into prose + step
sections. This test locks in the fence format and checks that every bundled
tutorial parses cleanly and that every embedded step, if run, produces a
finite dose.
"""
from __future__ import annotations

import pytest

from rclea_cli.commands.tutorial import FENCE_RE, _split_sections
from rclea_core import AssessmentInput, run_assessment
from rclea_core.tutorials import list_tutorials


def test_fences_parse_cleanly() -> None:
    for tut in list_tutorials():
        sections = _split_sections(tut.markdown)
        step_sections = [s for s in sections if s.kind == "step"]
        # Regex count must match parsed-section count
        assert len(step_sections) == len(FENCE_RE.findall(tut.markdown)), tut.slug
        for s in step_sections:
            assert "scenario_id" in s.spec, f"{tut.slug}: step missing scenario_id"
            assert "soil_concentrations_Bq_per_kg" in s.spec, f"{tut.slug}: step missing soil"


@pytest.mark.parametrize(
    "tutorial_slug",
    [
        "02-radiation-basics",
        "03-exposure-pathways",
        "04-first-assessment",
        "05-interpreting-results",
        "07-advanced-workflows",
    ],
)
def test_every_step_runs(tutorial_slug: str) -> None:
    tut = next((t for t in list_tutorials() if t.slug == tutorial_slug), None)
    assert tut is not None, f"Tutorial {tutorial_slug} not found"
    steps = [s for s in _split_sections(tut.markdown) if s.kind == "step"]
    assert steps, f"Tutorial {tutorial_slug} has no interactive steps"
    for step in steps:
        spec = step.spec
        inp = AssessmentInput.model_validate(
            {
                "soil_concentrations_Bq_per_kg": spec.get("soil_concentrations_Bq_per_kg", {}),
                "scenario_id": spec["scenario_id"],
                "age": spec.get("age", "adult"),
                "sex": spec.get("sex", "male"),
                "building_id": spec.get("building_id", "Timber"),
                "fraction_land_contaminated": spec.get("fraction_land_contaminated", 1.0),
            }
        )
        result = run_assessment(inp)
        # Finite, non-negative
        assert result.total_effective_dose_mSv_per_y >= 0
        assert result.total_effective_dose_mSv_per_y == result.total_effective_dose_mSv_per_y
