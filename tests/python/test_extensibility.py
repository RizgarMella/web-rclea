"""The extensibility acceptance test.

Adding a new isotope to data/isotopes.json should make it visible to the engine
and usable in an assessment, with NO code change. This test mutates the in-memory
loaded Dataset to simulate that, exercising the end-to-end assumption.
"""
from __future__ import annotations

from rclea_core import AssessmentInput, AgeGroup, Sex, run_assessment
from rclea_core.loader import reload_dataset
from rclea_core.models import Isotope


def test_added_isotope_appears_in_assessment() -> None:
    # Ensure a fresh dataset load, then inject a fictitious isotope
    ds = reload_dataset()
    ds.isotopes["Xx-999"] = Isotope(
        id="Xx-999",
        name="Xxunobtainium-999",
        element="Xx",
        ingestion_Sv_per_Bq={"infant": 1e-7, "child": 5e-8, "adult": 2e-8},
        inhalation_Sv_per_Bq={"infant": 3e-7, "child": 1.5e-7, "adult": 6e-8},
        external_Sv_per_y_per_Bq_per_m3=1e-9,
        skin_beta_Sv_per_y_per_Bq_per_cm2=0.0,
        skin_gamma_Sv_per_y_per_Bq_per_cm2=0.0,
    )
    inp = AssessmentInput(
        soil_concentrations_Bq_per_kg={"Xx-999": 1000.0},
        scenario_id="Residential_with_Home_Grown_Produce",
        age=AgeGroup.ADULT,
        sex=Sex.MALE,
        building_id="Timber",
        fraction_land_contaminated=1.0,
    )
    r = run_assessment(inp)
    # Must be > 0 (external + soil ingestion + inhalation pathways contribute)
    assert r.total_effective_dose_mSv_per_y > 0
    # The isotope must appear by id in at least one pathway's breakdown
    seen = False
    for p in r.per_pathway:
        if "Xx-999" in p.contributing_isotopes:
            seen = True
            break
    assert seen, "Xx-999 did not appear in any pathway breakdown"

    # Clean up for subsequent tests
    reload_dataset()
