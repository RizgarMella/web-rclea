"""Top-level assessment orchestrator."""
from __future__ import annotations

from rclea_core.disclaimer import DISCLAIMER_FULL
from rclea_core.loader import load_dataset
from rclea_core.models import (
    AssessmentInput,
    AssessmentResult,
    PathwayResult,
    RadonMode,
)
from rclea_core.pathways import PATHWAY_FUNCTIONS


def _gather_notes(inp: AssessmentInput, ds, per_path: list[PathwayResult]) -> list[str]:
    notes: list[str] = []
    unknown = [i for i in inp.soil_concentrations_Bq_per_kg if i not in ds.isotopes]
    if unknown:
        notes.append(
            f"Ignored {len(unknown)} unknown isotope id(s): {', '.join(unknown)}. "
            "Add entries to data/isotopes.json to extend the catalogue."
        )
    scenario = ds.scenarios[inp.scenario_id]
    if "Ra-226" in inp.soil_concentrations_Bq_per_kg and not scenario.pathways.radon_indoor:
        notes.append(
            "Ra-226 is present but the selected scenario does not include the indoor radon pathway; "
            "the radon contribution has been suppressed."
        )
    if inp.age.value not in scenario.per_age:
        notes.append(
            f"Scenario '{scenario.label}' does not define parameters for age '{inp.age.value}'. "
            "Results use zero-filled defaults for this age; consider 'adult'."
        )
    if (
        inp.radon_mode == RadonMode.MEASURED
        and inp.measured_rn222_Bq_per_m3 is None
        and scenario.pathways.radon_indoor
    ):
        notes.append(
            "Radon mode is 'measured' but no measured_rn222_Bq_per_m3 was provided; "
            "the radon pathway has been set to zero. Supply a measurement or switch to 'default'/'site_specific'."
        )
    if inp.radon_mode == RadonMode.SITE_SPECIFIC and scenario.pathways.radon_indoor:
        notes.append(
            "Radon mode is 'site_specific': K computed from soil emanation/diffusion and building "
            "height/ventilation (Nazaroff/Porstendörfer 1-D exhalation model). Results sensitive to those parameters."
        )
    if inp.overrides:
        notes.append(
            f"{len(inp.overrides)} user override(s) applied: {', '.join(sorted(inp.overrides))}."
        )
    return notes


def run_assessment(inp: AssessmentInput) -> AssessmentResult:
    """Run every applicable pathway for the selected scenario and receptor."""
    ds = load_dataset()
    if inp.scenario_id not in ds.scenarios:
        raise ValueError(
            f"Unknown scenario_id: {inp.scenario_id!r}. Known: {list(ds.scenarios)}"
        )
    if inp.building_id not in ds.buildings:
        raise ValueError(
            f"Unknown building_id: {inp.building_id!r}. Known: {list(ds.buildings)}"
        )

    scenario = ds.scenarios[inp.scenario_id]
    flags = scenario.pathways
    per_path: list[PathwayResult] = []
    pathway_flag_map = {
        "external": flags.external,
        "soil_ingestion": flags.soil_ingestion,
        "inhalation_dust": flags.inhalation_dust,
        "skin": flags.skin,
        "produce": flags.produce,
        "radon_indoor": flags.radon_indoor,
    }
    for pid, fn in PATHWAY_FUNCTIONS.items():
        if not pathway_flag_map.get(pid, False):
            continue
        per_path.append(fn(inp, ds))

    # Effective dose excludes the skin equivalent dose (which has its own criterion).
    total_eff = sum(r.dose_mSv_per_year for r in per_path if r.pathway != "skin")
    total_skin = next(
        (r.dose_mSv_per_year for r in per_path if r.pathway == "skin"),
        0.0,
    )

    eff_crit = ds.constants.effective_dose_criterion_mSv_per_y
    skin_crit = ds.constants.equivalent_skin_dose_criterion_mSv_per_y

    safety_margin = (eff_crit / total_eff) if total_eff > 0 else None

    return AssessmentResult(
        total_effective_dose_mSv_per_y=total_eff,
        total_skin_equivalent_dose_mSv_per_y=total_skin,
        effective_dose_criterion_mSv_per_y=eff_crit,
        skin_dose_criterion_mSv_per_y=skin_crit,
        exceeds_effective_criterion=total_eff > eff_crit,
        exceeds_skin_criterion=total_skin > skin_crit,
        safety_margin=safety_margin,
        per_pathway=per_path,
        inputs_echo=inp,
        notes=_gather_notes(inp, ds, per_path),
        disclaimer=DISCLAIMER_FULL,
    )


__all__ = ["run_assessment"]
