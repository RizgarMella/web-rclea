"""Unit tests for each pathway function.

Tests check:
- Zero input -> zero dose
- Monotonicity: doubling soil concentration doubles the pathway dose
- Building shielding affects only the external dose
- Age sensitivity: infants receive higher soil-ingestion dose than adults per Bq/kg
"""
from __future__ import annotations

import pytest

from rclea_core import AssessmentInput, AgeGroup, Sex, load_dataset, run_assessment
from rclea_core.pathways import (
    dose_external,
    dose_inhalation_dust,
    dose_produce,
    dose_radon,
    dose_skin,
    dose_soil_ingestion,
)


def _input(**overrides) -> AssessmentInput:
    base = dict(
        soil_concentrations_Bq_per_kg={"Cs-137": 1000.0},
        scenario_id="Residential_with_Home_Grown_Produce",
        age=AgeGroup.ADULT,
        sex=Sex.MALE,
        building_id="Timber",
        fraction_land_contaminated=1.0,
    )
    base.update(overrides)
    return AssessmentInput(**base)


@pytest.fixture(scope="module")
def ds():
    return load_dataset()


def test_zero_soil_zero_dose(ds) -> None:
    inp = _input(soil_concentrations_Bq_per_kg={})
    for fn in (dose_external, dose_soil_ingestion, dose_inhalation_dust, dose_skin, dose_produce, dose_radon):
        result = fn(inp, ds)
        assert result.dose_mSv_per_year == 0.0


def test_linearity_in_concentration(ds) -> None:
    inp1 = _input(soil_concentrations_Bq_per_kg={"Cs-137": 1000.0})
    inp2 = _input(soil_concentrations_Bq_per_kg={"Cs-137": 2000.0})
    for fn in (dose_external, dose_soil_ingestion, dose_inhalation_dust, dose_skin, dose_produce):
        r1 = fn(inp1, ds).dose_mSv_per_year
        r2 = fn(inp2, ds).dose_mSv_per_year
        assert r2 == pytest.approx(2.0 * r1, rel=1e-9)


def test_fraction_land_scales_linearly(ds) -> None:
    inp_full = _input(fraction_land_contaminated=1.0)
    inp_half = _input(fraction_land_contaminated=0.5)
    e_full = dose_external(inp_full, ds).dose_mSv_per_year
    e_half = dose_external(inp_half, ds).dose_mSv_per_year
    assert e_half == pytest.approx(0.5 * e_full, rel=1e-9)


def test_building_shielding_reduces_external(ds) -> None:
    timber = dose_external(_input(building_id="Timber"), ds).dose_mSv_per_year
    brick = dose_external(_input(building_id="Concrete_Brick"), ds).dose_mSv_per_year
    assert brick < timber


def test_building_shielding_does_not_affect_soil_ingestion(ds) -> None:
    a = dose_soil_ingestion(_input(building_id="Timber"), ds).dose_mSv_per_year
    b = dose_soil_ingestion(_input(building_id="Concrete_Brick"), ds).dose_mSv_per_year
    assert a == b


def test_infant_higher_soil_ingestion_than_adult(ds) -> None:
    inf = dose_soil_ingestion(_input(age=AgeGroup.INFANT), ds).dose_mSv_per_year
    adult = dose_soil_ingestion(_input(age=AgeGroup.ADULT), ds).dose_mSv_per_year
    # Infants eat more soil per year AND have higher Cs-137 ingestion DCF
    assert inf > adult


def test_radon_zero_when_no_ra226(ds) -> None:
    inp = _input(soil_concentrations_Bq_per_kg={"Cs-137": 1000.0})
    r = dose_radon(inp, ds)
    assert r.dose_mSv_per_year == 0.0


def test_radon_scales_with_ra226(ds) -> None:
    inp1 = _input(soil_concentrations_Bq_per_kg={"Ra-226": 100.0})
    inp2 = _input(soil_concentrations_Bq_per_kg={"Ra-226": 500.0})
    r1 = dose_radon(inp1, ds).dose_mSv_per_year
    r2 = dose_radon(inp2, ds).dose_mSv_per_year
    assert r2 == pytest.approx(5.0 * r1, rel=1e-9)


def test_unknown_isotope_is_ignored_not_crashed() -> None:
    inp = _input(soil_concentrations_Bq_per_kg={"Xx-999": 1e6})
    result = run_assessment(inp)
    assert result.total_effective_dose_mSv_per_y == 0.0
    assert any("Xx-999" in n for n in result.notes)


def test_run_assessment_with_multiple_isotopes() -> None:
    inp = _input(
        soil_concentrations_Bq_per_kg={"Cs-137": 100.0, "Sr-90": 50.0, "Pu-239": 10.0}
    )
    r = run_assessment(inp)
    assert r.total_effective_dose_mSv_per_y > 0
    # All three should contribute to at least one pathway
    touched = set()
    for p in r.per_pathway:
        for iso, dose in p.contributing_isotopes.items():
            if dose > 0:
                touched.add(iso)
    assert {"Cs-137", "Sr-90", "Pu-239"}.issubset(touched)


def test_exceeds_criterion_flag() -> None:
    # Very large Cs-137 concentration should exceed 3 mSv/y
    inp = _input(soil_concentrations_Bq_per_kg={"Cs-137": 1_000_000.0})
    r = run_assessment(inp)
    assert r.exceeds_effective_criterion is True


def test_below_criterion_flag() -> None:
    inp = _input(soil_concentrations_Bq_per_kg={"Cs-137": 1.0})
    r = run_assessment(inp)
    assert r.exceeds_effective_criterion is False
