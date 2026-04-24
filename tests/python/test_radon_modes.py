"""Tests for the three Rn-222 modes and per-building radon parameters."""
from __future__ import annotations

import math

import pytest

from rclea_core import (
    AgeGroup,
    AssessmentInput,
    RadonMode,
    Sex,
    load_dataset,
    run_assessment,
)


def _base(radon_mode: RadonMode = RadonMode.DEFAULT, **kw) -> AssessmentInput:
    defaults = dict(
        soil_concentrations_Bq_per_kg={"Ra-226": 1000.0},
        scenario_id="Residential_with_Home_Grown_Produce",
        age=AgeGroup.ADULT,
        sex=Sex.MALE,
        building_id="Timber",
        radon_mode=radon_mode,
    )
    defaults.update(kw)
    return AssessmentInput(**defaults)


def _radon(result) -> float:
    for p in result.per_pathway:
        if p.pathway == "radon_indoor":
            return p.dose_mSv_per_year
    return 0.0


def test_default_mode_reproduces_baseline() -> None:
    """Dose with radon_mode=default matches the 3*C_Ra226 hand-calc."""
    r = run_assessment(_base(radon_mode=RadonMode.DEFAULT))
    ds = load_dataset()
    rn = ds.radon
    scenario = ds.scenarios["Residential_with_Home_Grown_Produce"]
    ap = scenario.per_age["adult"]
    hours_indoor = ap.occupancy_indoor_fraction * ds.constants.hours_per_year
    expected_sv = (
        1000.0
        * rn.default_rn222_conversion_Bq_m3_per_Bq_kg
        * rn.rn222_equilibrium_factor
        * rn.rn222_inhalation_Sv_per_h_per_Bq_per_m3
        * hours_indoor
    )
    assert _radon(r) == pytest.approx(expected_sv * 1000.0, rel=1e-9)


def test_measured_mode_bypasses_K() -> None:
    """radon_mode=measured uses the measured concentration directly; C_Ra226 is irrelevant."""
    r100 = run_assessment(
        _base(
            radon_mode=RadonMode.MEASURED,
            measured_rn222_Bq_per_m3=100.0,
            soil_concentrations_Bq_per_kg={"Ra-226": 100.0},  # different Ra, should not matter
        )
    )
    r100_other_ra = run_assessment(
        _base(
            radon_mode=RadonMode.MEASURED,
            measured_rn222_Bq_per_m3=100.0,
            soil_concentrations_Bq_per_kg={"Ra-226": 99999.0},
        )
    )
    assert _radon(r100) == pytest.approx(_radon(r100_other_ra), rel=1e-12)


def test_measured_mode_scales_linearly_with_measured_value() -> None:
    r1 = run_assessment(_base(radon_mode=RadonMode.MEASURED, measured_rn222_Bq_per_m3=50.0))
    r2 = run_assessment(_base(radon_mode=RadonMode.MEASURED, measured_rn222_Bq_per_m3=500.0))
    assert _radon(r2) == pytest.approx(10.0 * _radon(r1), rel=1e-9)


def test_measured_mode_missing_value_yields_zero_and_note() -> None:
    r = run_assessment(_base(radon_mode=RadonMode.MEASURED))
    assert _radon(r) == 0.0
    assert any("measured" in n.lower() for n in r.notes)


def test_site_specific_K_matches_workbook_to_under_one_percent() -> None:
    """Reverse-engineered K = 2.239 Bq/m^3 per Bq/kg; workbook reports 2.2398. Within 0.1 %."""
    from rclea_core.pathways import _site_specific_K

    ds = load_dataset()
    inp = _base(radon_mode=RadonMode.SITE_SPECIFIC, building_id="Timber")
    K = _site_specific_K(inp, ds)
    workbook_value = 2.2398
    assert K == pytest.approx(workbook_value, rel=0.01), f"K={K}, expected ~{workbook_value}"


def test_site_specific_vs_default_ratio() -> None:
    """Site-specific dose / default dose ≈ 2.239 / 3.0 = 0.7463."""
    r_def = run_assessment(_base(radon_mode=RadonMode.DEFAULT))
    r_site = run_assessment(_base(radon_mode=RadonMode.SITE_SPECIFIC))
    ratio = _radon(r_site) / _radon(r_def)
    assert ratio == pytest.approx(2.2398 / 3.0, rel=0.01)


def test_site_specific_respects_building_overrides() -> None:
    """A building with better ventilation → lower K → lower radon dose.

    Doubling the ventilation rate should roughly halve K (since lambda_v >> lambda_Rn).
    """
    r_std = run_assessment(_base(radon_mode=RadonMode.SITE_SPECIFIC))
    r_vent = run_assessment(
        _base(
            radon_mode=RadonMode.SITE_SPECIFIC,
            overrides={"building_rn222_ventilation_rate_per_s": 2 * 8.33e-5},
        )
    )
    # Ratio should be close to 1/2 but slightly above because lambda_Rn is non-zero
    ratio = _radon(r_vent) / _radon(r_std)
    assert 0.49 <= ratio <= 0.51


def test_site_specific_zero_ra226_returns_zero() -> None:
    inp = AssessmentInput(
        soil_concentrations_Bq_per_kg={"Cs-137": 1000.0},
        scenario_id="Residential_with_Home_Grown_Produce",
        radon_mode=RadonMode.SITE_SPECIFIC,
    )
    r = run_assessment(inp)
    assert _radon(r) == 0.0


def test_measured_mode_works_when_scenario_excludes_radon_pathway() -> None:
    """If the scenario doesn't have radon_indoor enabled, measured mode still produces zero (the pathway is not run)."""
    r = run_assessment(
        AssessmentInput(
            soil_concentrations_Bq_per_kg={"Ra-226": 1000.0},
            scenario_id="Allotments",  # no radon pathway
            age=AgeGroup.ADULT,
            radon_mode=RadonMode.MEASURED,
            measured_rn222_Bq_per_m3=100.0,
        )
    )
    assert _radon(r) == 0.0
