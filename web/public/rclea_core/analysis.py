"""Multi-scenario analyses layered on top of `run_assessment`.

This module implements two tool-level workflows that existed in the original
Excel workbook but not (yet) in this remake:

  - `find_worst_case`  — enumerate every valid (scenario x building x age x sex)
    combination and report the combination that yields the highest total
    effective dose. Equivalent to the `AllDoses` sheet in the workbook.

  - `compute_rsgvs`    — "Radioactivity in Soil Guideline Values": for each
    radionuclide in the catalogue, compute the soil concentration (Bq/kg) that
    would alone produce the 3 mSv/y statutory criterion under the chosen
    scenario/receptor. Equivalent to the `GuidelineValues` sheet. Inverse
    problem: set C_i = 1 Bq/kg, compute dose D_i, RSGV_i = criterion / D_i.
"""
from __future__ import annotations

import math

from rclea_core.disclaimer import DISCLAIMER_FULL
from rclea_core.loader import load_dataset
from rclea_core.models import (
    AgeGroup,
    AssessmentInput,
    RadonMode,
    RSGVReport,
    Sex,
    WorstCaseEntry,
    WorstCaseReport,
)

# assessment import kept local to avoid circular import at module load
from rclea_core.assessment import run_assessment


def find_worst_case(
    soil_concentrations_Bq_per_kg: dict[str, float],
    *,
    fraction_land_contaminated: float = 1.0,
    radon_mode: RadonMode = RadonMode.DEFAULT,
    measured_rn222_Bq_per_m3: float | None = None,
    overrides: dict[str, float] | None = None,
) -> WorstCaseReport:
    """Enumerate every scenario x building x age x sex combination, return sorted + max.

    Combinations are only included if the scenario defines parameters for that age
    (e.g. `Commercial_Industrial` only defines `adult`, so infant/child rows are skipped).
    """
    ds = load_dataset()
    overrides = overrides or {}
    entries: list[WorstCaseEntry] = []
    for scenario_id, scenario in ds.scenarios.items():
        for building_id in ds.buildings:
            for age_key, _ in scenario.per_age.items():
                try:
                    age = AgeGroup(age_key)
                except ValueError:
                    continue
                for sex in Sex:
                    inp = AssessmentInput(
                        soil_concentrations_Bq_per_kg=dict(soil_concentrations_Bq_per_kg),
                        scenario_id=scenario_id,
                        age=age,
                        sex=sex,
                        building_id=building_id,
                        fraction_land_contaminated=fraction_land_contaminated,
                        radon_mode=radon_mode,
                        measured_rn222_Bq_per_m3=measured_rn222_Bq_per_m3,
                        overrides=overrides,
                    )
                    result = run_assessment(inp)
                    entries.append(
                        WorstCaseEntry(
                            scenario_id=scenario_id,
                            scenario_label=scenario.label,
                            building_id=building_id,
                            age=age,
                            sex=sex,
                            total_effective_dose_mSv_per_y=result.total_effective_dose_mSv_per_y,
                            exceeds_effective_criterion=result.exceeds_effective_criterion,
                        )
                    )

    if not entries:
        raise ValueError("No valid scenario/receptor combinations found.")

    entries.sort(key=lambda e: e.total_effective_dose_mSv_per_y, reverse=True)
    worst = entries[0]
    return WorstCaseReport(
        soil_concentrations_Bq_per_kg=dict(soil_concentrations_Bq_per_kg),
        fraction_land_contaminated=fraction_land_contaminated,
        radon_mode=radon_mode,
        measured_rn222_Bq_per_m3=measured_rn222_Bq_per_m3,
        effective_dose_criterion_mSv_per_y=ds.constants.effective_dose_criterion_mSv_per_y,
        entries=entries,
        worst=worst,
        disclaimer=DISCLAIMER_FULL,
    )


def compute_rsgvs(
    scenario_id: str,
    age: AgeGroup = AgeGroup.ADULT,
    sex: Sex = Sex.MALE,
    building_id: str = "Timber",
    *,
    radon_mode: RadonMode = RadonMode.DEFAULT,
    fraction_land_contaminated: float = 1.0,
    overrides: dict[str, float] | None = None,
    unit_concentration_Bq_per_kg: float = 1.0,
) -> RSGVReport:
    """For each isotope, compute the Bq/kg soil concentration that would alone produce
    the effective-dose criterion (default 3 mSv/y) under the chosen scenario.

    Method: set isotope concentration to a unit value, zero for everything else, run
    an assessment, compute RSGV = criterion / dose. If the isotope produces zero dose
    under this scenario (e.g. an alpha emitter in a scenario with no radon and no
    inhalation), the RSGV is +inf.
    """
    ds = load_dataset()
    overrides = overrides or {}

    if scenario_id not in ds.scenarios:
        raise ValueError(f"Unknown scenario_id: {scenario_id!r}")
    if building_id not in ds.buildings:
        raise ValueError(f"Unknown building_id: {building_id!r}")

    scenario = ds.scenarios[scenario_id]
    criterion = ds.constants.effective_dose_criterion_mSv_per_y

    rsgvs: dict[str, float] = {}
    for iso_id in ds.isotopes:
        inp = AssessmentInput(
            soil_concentrations_Bq_per_kg={iso_id: unit_concentration_Bq_per_kg},
            scenario_id=scenario_id,
            age=age,
            sex=sex,
            building_id=building_id,
            fraction_land_contaminated=fraction_land_contaminated,
            radon_mode=radon_mode,
            overrides=overrides,
        )
        r = run_assessment(inp)
        dose = r.total_effective_dose_mSv_per_y
        if dose <= 0:
            rsgvs[iso_id] = math.inf
        else:
            rsgvs[iso_id] = (criterion / dose) * unit_concentration_Bq_per_kg

    return RSGVReport(
        scenario_id=scenario_id,
        scenario_label=scenario.label,
        age=age,
        sex=sex,
        building_id=building_id,
        radon_mode=radon_mode,
        effective_dose_criterion_mSv_per_y=criterion,
        rsgvs_Bq_per_kg=rsgvs,
        disclaimer=DISCLAIMER_FULL,
    )


__all__ = ["find_worst_case", "compute_rsgvs"]
