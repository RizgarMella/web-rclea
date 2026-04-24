"""Tests for the per-parameter override mechanism on AssessmentInput.overrides."""
from __future__ import annotations

import pytest

from rclea_core import AgeGroup, AssessmentInput, Sex, run_assessment


def _cs137() -> dict[str, float]:
    return {"Cs-137": 1000.0}


def _pathway(result, pid: str) -> float:
    for p in result.per_pathway:
        if p.pathway == pid:
            return p.dose_mSv_per_year
    return 0.0


def _run(**overrides) -> float:
    """Return total effective dose for Cs-137 residential adult with the given overrides."""
    return run_assessment(
        AssessmentInput(
            soil_concentrations_Bq_per_kg=_cs137(),
            scenario_id="Residential_with_Home_Grown_Produce",
            age=AgeGroup.ADULT,
            sex=Sex.MALE,
            building_id="Timber",
            overrides=overrides,
        )
    ).total_effective_dose_mSv_per_y


def test_dust_loading_override_scales_inhalation_linearly() -> None:
    """Doubling dust loading doubles the inhalation pathway."""
    base = run_assessment(
        AssessmentInput(
            soil_concentrations_Bq_per_kg=_cs137(),
            scenario_id="Residential_with_Home_Grown_Produce",
            age=AgeGroup.ADULT,
        )
    )
    doubled = run_assessment(
        AssessmentInput(
            soil_concentrations_Bq_per_kg=_cs137(),
            scenario_id="Residential_with_Home_Grown_Produce",
            age=AgeGroup.ADULT,
            overrides={"dust_loading_kg_per_m3": 1e-7},  # 2x the default 5e-8
        )
    )
    assert _pathway(doubled, "inhalation_dust") == pytest.approx(
        2.0 * _pathway(base, "inhalation_dust"), rel=1e-9
    )


def test_soil_ingestion_override_is_per_age_keyed() -> None:
    """Override affecting adult should not affect infant."""
    base_adult = run_assessment(
        AssessmentInput(
            soil_concentrations_Bq_per_kg=_cs137(),
            scenario_id="Residential_with_Home_Grown_Produce",
            age=AgeGroup.ADULT,
        )
    )
    base_infant = run_assessment(
        AssessmentInput(
            soil_concentrations_Bq_per_kg=_cs137(),
            scenario_id="Residential_with_Home_Grown_Produce",
            age=AgeGroup.INFANT,
        )
    )
    # Override only the adult key
    overridden_adult = run_assessment(
        AssessmentInput(
            soil_concentrations_Bq_per_kg=_cs137(),
            scenario_id="Residential_with_Home_Grown_Produce",
            age=AgeGroup.ADULT,
            overrides={"soil_ingestion_kg_per_y.adult": 2 * 0.022},
        )
    )
    overridden_infant_with_adult_key = run_assessment(
        AssessmentInput(
            soil_concentrations_Bq_per_kg=_cs137(),
            scenario_id="Residential_with_Home_Grown_Produce",
            age=AgeGroup.INFANT,
            overrides={"soil_ingestion_kg_per_y.adult": 999.9},  # adult key ignored for infant
        )
    )
    # Adult soil ingestion doubled -> that pathway doubles
    assert _pathway(overridden_adult, "soil_ingestion") == pytest.approx(
        2.0 * _pathway(base_adult, "soil_ingestion"), rel=1e-9
    )
    # Infant is unaffected by the adult-keyed override
    assert _pathway(overridden_infant_with_adult_key, "soil_ingestion") == pytest.approx(
        _pathway(base_infant, "soil_ingestion"), rel=1e-9
    )


def test_shielding_factor_override_affects_external() -> None:
    base = run_assessment(
        AssessmentInput(
            soil_concentrations_Bq_per_kg=_cs137(),
            scenario_id="Residential_with_Home_Grown_Produce",
            age=AgeGroup.ADULT,
            building_id="Timber",  # shielding = 0
        )
    )
    heavy_shield = run_assessment(
        AssessmentInput(
            soil_concentrations_Bq_per_kg=_cs137(),
            scenario_id="Residential_with_Home_Grown_Produce",
            age=AgeGroup.ADULT,
            building_id="Timber",
            overrides={"shielding_factor": 0.5},
        )
    )
    assert _pathway(heavy_shield, "external") < _pathway(base, "external")


def test_notes_record_override_count() -> None:
    r = run_assessment(
        AssessmentInput(
            soil_concentrations_Bq_per_kg=_cs137(),
            scenario_id="Residential_with_Home_Grown_Produce",
            age=AgeGroup.ADULT,
            overrides={"dust_loading_kg_per_m3": 1e-7, "shielding_factor": 0.5},
        )
    )
    assert any("override" in n.lower() for n in r.notes)


def test_no_overrides_is_equivalent_to_library() -> None:
    base = _run()
    with_empty = _run()  # same call; sanity deterministic
    assert base == with_empty


def test_unknown_override_key_is_silently_ignored() -> None:
    """Unknown keys don't crash; they simply have no effect (safe-by-default)."""
    base = _run()
    weird = _run(**{"totally_made_up_key": 999.0})
    assert base == weird
