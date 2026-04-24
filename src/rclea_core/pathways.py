"""Pathway-specific dose equations.

Every function is pure: takes explicit inputs (no file I/O, no globals), returns
a `PathwayResult` with the per-isotope breakdown so the UI can "explain this
number".

Units are annotated in variable names and comments. All intermediate doses are
in Sv; we convert to mSv at the very end. Concentration is Bq/kg dry soil.

The model follows the methodology published in CRCE-RAD-003-2020 and CLR-13.
Minor numeric differences from the legacy Excel tool are expected; this is an
educational implementation, not a bit-exact port.

Every pathway consults `AssessmentInput.overrides` via `_param()` before falling
back to library defaults. Override keys are hierarchical dotted names, e.g.
    "dust_loading_kg_per_m3"
    "soil_ingestion_kg_per_y.infant"
    "occupancy_indoor_fraction.adult"
    "fraction_indoor_dust_from_local_soil"
"""
from __future__ import annotations

import math
from typing import TypeVar

from rclea_core.models import (
    AssessmentInput,
    Dataset,
    Isotope,
    PathwayResult,
    RadonMode,
    Scenario,
    ScenarioAgeParams,
)

T = TypeVar("T")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _param(inp: AssessmentInput, key: str, fallback: float) -> float:
    """Return the user's override for `key` if present, otherwise the library `fallback`."""
    return inp.overrides.get(key, fallback)


def _isotope_concentrations(
    soil: dict[str, float], dataset: Dataset
) -> dict[str, tuple[Isotope, float]]:
    """Filter user-supplied concentrations to known isotopes only."""
    out: dict[str, tuple[Isotope, float]] = {}
    for iso_id, conc in soil.items():
        if conc <= 0:
            continue
        if iso_id not in dataset.isotopes:
            continue
        out[iso_id] = (dataset.isotopes[iso_id], conc)
    return out


def _age_params(scenario: Scenario, age: str) -> ScenarioAgeParams:
    return scenario.per_age.get(age, ScenarioAgeParams())


def _mSv(sv: float) -> float:
    return sv * 1000.0


# ---------------------------------------------------------------------------
# 1. External whole-body gamma dose
# ---------------------------------------------------------------------------


def dose_external(inp: AssessmentInput, ds: Dataset) -> PathwayResult:
    """External dose = sum_i C_i * rho_B * DCF_ext,i * [O_in*(1-SF) + O_out] * f_contam."""
    scenario = ds.scenarios[inp.scenario_id]
    ap = _age_params(scenario, inp.age.value)
    age = inp.age.value
    rho_B = _param(inp, "rho_B_soil_bulk_density_kg_per_m3", ds.constants.rho_B_soil_bulk_density_kg_per_m3)
    sf = _param(inp, "shielding_factor", ds.buildings[inp.building_id].shielding_factor)
    o_in = _param(inp, f"occupancy_indoor_fraction.{age}", ap.occupancy_indoor_fraction)
    o_out = _param(inp, f"occupancy_outdoor_fraction.{age}", ap.occupancy_outdoor_fraction)
    effective_occupancy = o_in * (1.0 - sf) + o_out
    contrib: dict[str, float] = {}
    for iso_id, (iso, conc_Bq_kg) in _isotope_concentrations(
        inp.soil_concentrations_Bq_per_kg, ds
    ).items():
        conc_Bq_m3 = conc_Bq_kg * rho_B
        dose_Sv = conc_Bq_m3 * iso.external_Sv_per_y_per_Bq_per_m3 * effective_occupancy
        dose_Sv *= inp.fraction_land_contaminated
        contrib[iso_id] = _mSv(dose_Sv)
    return PathwayResult(
        pathway="external",
        label=ds.pathways["external"].label,
        dose_mSv_per_year=sum(contrib.values()),
        contributing_isotopes=contrib,
    )


# ---------------------------------------------------------------------------
# 2. Soil ingestion
# ---------------------------------------------------------------------------


def dose_soil_ingestion(inp: AssessmentInput, ds: Dataset) -> PathwayResult:
    """D_ing = sum_i C_i * I_soil(age, land_use) * DCF_ing,i(age) * f_contam."""
    scenario = ds.scenarios[inp.scenario_id]
    ap = _age_params(scenario, inp.age.value)
    age = inp.age.value
    i_soil = _param(inp, f"soil_ingestion_kg_per_y.{age}", ap.soil_ingestion_kg_per_y)
    contrib: dict[str, float] = {}
    for iso_id, (iso, conc) in _isotope_concentrations(
        inp.soil_concentrations_Bq_per_kg, ds
    ).items():
        dcf = iso.ingestion_Sv_per_Bq.get(age, 0.0)
        dose_Sv = conc * i_soil * dcf * inp.fraction_land_contaminated
        contrib[iso_id] = _mSv(dose_Sv)
    return PathwayResult(
        pathway="soil_ingestion",
        label=ds.pathways["soil_ingestion"].label,
        dose_mSv_per_year=sum(contrib.values()),
        contributing_isotopes=contrib,
    )


# ---------------------------------------------------------------------------
# 3. Inhalation of resuspended dust
# ---------------------------------------------------------------------------


def dose_inhalation_dust(inp: AssessmentInput, ds: Dataset) -> PathwayResult:
    scenario = ds.scenarios[inp.scenario_id]
    ap = _age_params(scenario, inp.age.value)
    age = inp.age.value
    sex = inp.sex.value
    rr = ds.receptors.respiration_m3_per_h[sex][age]
    rr_active = _param(inp, f"respiration_active_m3_per_h.{age}", rr["active_m3_per_h"])
    rr_passive = _param(inp, f"respiration_passive_m3_per_h.{age}", rr["passive_m3_per_h"])
    hours_per_year = ds.constants.hours_per_year

    a_in = _param(inp, f"active_fraction_indoor.{age}", ap.active_fraction_indoor)
    p_in = _param(inp, f"passive_fraction_indoor.{age}", ap.passive_fraction_indoor)
    a_out = _param(inp, f"active_fraction_outdoor.{age}", ap.active_fraction_outdoor)
    p_out = _param(inp, f"passive_fraction_outdoor.{age}", ap.passive_fraction_outdoor)

    vol_indoor = hours_per_year * (rr_active * a_in + rr_passive * p_in)
    vol_outdoor = hours_per_year * (rr_active * a_out + rr_passive * p_out)

    dust = _param(inp, "dust_loading_kg_per_m3", scenario.dust.air_respirable_particles_kg_per_m3)
    f_dust = _param(inp, "fraction_indoor_dust_from_local_soil", scenario.dust.fraction_indoor_dust_from_local_soil)

    contrib: dict[str, float] = {}
    for iso_id, (iso, conc) in _isotope_concentrations(
        inp.soil_concentrations_Bq_per_kg, ds
    ).items():
        dcf = iso.inhalation_Sv_per_Bq.get(age, 0.0)
        air_conc = conc * dust
        breathed_Bq = air_conc * (vol_indoor * f_dust + vol_outdoor)
        dose_Sv = breathed_Bq * dcf * inp.fraction_land_contaminated
        contrib[iso_id] = _mSv(dose_Sv)
    return PathwayResult(
        pathway="inhalation_dust",
        label=ds.pathways["inhalation_dust"].label,
        dose_mSv_per_year=sum(contrib.values()),
        contributing_isotopes=contrib,
    )


# ---------------------------------------------------------------------------
# 4. Skin equivalent dose (beta + gamma)
# ---------------------------------------------------------------------------


def dose_skin(inp: AssessmentInput, ds: Dataset) -> PathwayResult:
    scenario = ds.scenarios[inp.scenario_id]
    ap = _age_params(scenario, inp.age.value)
    age = inp.age.value
    mg_to_kg = 1e-6

    loading_in = _param(inp, f"skin_soil_loading_indoor_mg_per_cm2.{age}", ap.skin_soil_loading_indoor_mg_per_cm2)
    loading_out = _param(inp, f"skin_soil_loading_outdoor_mg_per_cm2.{age}", ap.skin_soil_loading_outdoor_mg_per_cm2)
    sc_in = _param(inp, f"skin_contact_fraction_indoor.{age}", ap.skin_contact_fraction_indoor)
    sc_out = _param(inp, f"skin_contact_fraction_outdoor.{age}", ap.skin_contact_fraction_outdoor)
    exp_in = _param(inp, f"skin_exposed_fraction_indoor.{age}", ap.skin_exposed_fraction_indoor)
    exp_out = _param(inp, f"skin_exposed_fraction_outdoor.{age}", ap.skin_exposed_fraction_outdoor)

    surf_indoor = loading_in * mg_to_kg
    surf_outdoor = loading_out * mg_to_kg
    indoor_factor = sc_in * exp_in
    outdoor_factor = sc_out * exp_out

    contrib: dict[str, float] = {}
    for iso_id, (iso, conc) in _isotope_concentrations(
        inp.soil_concentrations_Bq_per_kg, ds
    ).items():
        dcf = iso.skin_beta_Sv_per_y_per_Bq_per_cm2 + iso.skin_gamma_Sv_per_y_per_Bq_per_cm2
        dose_Sv = conc * dcf * (surf_indoor * indoor_factor + surf_outdoor * outdoor_factor)
        dose_Sv *= inp.fraction_land_contaminated
        contrib[iso_id] = _mSv(dose_Sv)
    return PathwayResult(
        pathway="skin",
        label=ds.pathways["skin"].label,
        dose_mSv_per_year=sum(contrib.values()),
        contributing_isotopes=contrib,
    )


# ---------------------------------------------------------------------------
# 5. Consumption of home-grown produce
# ---------------------------------------------------------------------------


def dose_produce(inp: AssessmentInput, ds: Dataset) -> PathwayResult:
    age = inp.age.value
    sex = inp.sex.value
    bw = _param(inp, f"body_weight_kg.{sex}.{age}", ds.receptors.body_weight_kg[sex][age])
    consumption = ds.consumption_by_age.get(age, {})

    contrib: dict[str, float] = {}
    for iso_id, (iso, conc) in _isotope_concentrations(
        inp.soil_concentrations_Bq_per_kg, ds
    ).items():
        dcf = iso.ingestion_Sv_per_Bq.get(age, 0.0)
        element = ds.elements.get(iso.element)
        if element is None:
            continue
        cf_veg = _param(inp, f"soil_to_plant_cf.{iso.element}", element.soil_to_plant_cf_fw_per_dw)

        total_bq = 0.0
        for crop, cr in consumption.items():
            meta = ds.crop_meta.get(crop)
            if meta is None:
                continue
            hf = _param(inp, f"home_fraction.{crop}", meta.home_fraction)
            sl = _param(inp, f"soil_loading_kg_dw_per_kg_fw.{crop}", meta.soil_loading_kg_dw_per_kg_fw)
            bq_per_kg_fw = conc * (cf_veg + sl)
            kg_eaten = cr * bw * hf
            total_bq += bq_per_kg_fw * kg_eaten

        dose_Sv = total_bq * dcf * inp.fraction_land_contaminated
        contrib[iso_id] = _mSv(dose_Sv)
    return PathwayResult(
        pathway="produce",
        label=ds.pathways["produce"].label,
        dose_mSv_per_year=sum(contrib.values()),
        contributing_isotopes=contrib,
    )


# ---------------------------------------------------------------------------
# 6. Indoor radon (Rn-222) — three modes
# ---------------------------------------------------------------------------


def _site_specific_K(inp: AssessmentInput, ds: Dataset) -> float:
    """Classical 1-D radon exhalation + indoor mass-balance model.

        K [Bq/m^3 per Bq/kg] = (alpha * rho_B * sqrt(D_e * lambda_Rn))
                             / (h * (lambda_v + lambda_Rn))

    Parameters are taken from soil_global and the selected building, with
    user-supplied overrides honoured via `_param()`.
    """
    sg = ds.soil_global
    b = ds.buildings[inp.building_id]
    rn = ds.radon

    alpha = _param(inp, "rn222_emanation_fraction", sg.rn222_emanation_fraction)
    rho_B = _param(inp, "rho_B_soil_bulk_density_kg_per_m3", sg.bulk_density_kg_per_m3)
    D_e = _param(inp, "rn222_effective_diffusion_m2_per_s", sg.rn222_effective_diffusion_m2_per_s)
    lam_Rn = _param(inp, "rn222_decay_constant_per_s", rn.rn222_decay_constant_per_s)
    h = _param(inp, "building_rn222_height_m", b.rn222_height_m)
    lam_v = _param(inp, "building_rn222_ventilation_rate_per_s", b.rn222_ventilation_rate_per_s)

    if h <= 0 or (lam_v + lam_Rn) <= 0:
        return rn.default_rn222_conversion_Bq_m3_per_Bq_kg
    numerator = alpha * rho_B * math.sqrt(D_e * lam_Rn)
    denominator = h * (lam_v + lam_Rn)
    return numerator / denominator


def dose_radon(inp: AssessmentInput, ds: Dataset) -> PathwayResult:
    """Dose from indoor Rn-222 accumulated from Ra-226 in soil.

    Three modes controlled by `inp.radon_mode`:
      - DEFAULT: K = default_rn222_conversion_Bq_m3_per_Bq_kg (3.0); C_Rn = K * C_Ra226
      - MEASURED: C_Rn = inp.measured_rn222_Bq_per_m3 (bypass K entirely)
      - SITE_SPECIFIC: K = f(soil + building properties); C_Rn = K * C_Ra226
    """
    scenario = ds.scenarios[inp.scenario_id]
    ap = _age_params(scenario, inp.age.value)
    rn = ds.radon
    age = inp.age.value

    if inp.radon_mode == RadonMode.MEASURED:
        if inp.measured_rn222_Bq_per_m3 is None:
            return PathwayResult(
                pathway="radon_indoor",
                label=ds.pathways["radon_indoor"].label,
                dose_mSv_per_year=0.0,
                contributing_isotopes={},
            )
        c_rn = inp.measured_rn222_Bq_per_m3
    else:
        ra226 = inp.soil_concentrations_Bq_per_kg.get("Ra-226", 0.0)
        if ra226 <= 0:
            return PathwayResult(
                pathway="radon_indoor",
                label=ds.pathways["radon_indoor"].label,
                dose_mSv_per_year=0.0,
                contributing_isotopes={},
            )
        if inp.radon_mode == RadonMode.SITE_SPECIFIC:
            K = _site_specific_K(inp, ds)
        else:
            K = _param(
                inp,
                "rn222_conversion_Bq_m3_per_Bq_kg",
                rn.default_rn222_conversion_Bq_m3_per_Bq_kg,
            )
        c_rn = ra226 * K

    o_in = _param(inp, f"occupancy_indoor_fraction.{age}", ap.occupancy_indoor_fraction)
    hours_indoor = o_in * ds.constants.hours_per_year
    eq_factor = _param(inp, "rn222_equilibrium_factor", rn.rn222_equilibrium_factor)
    dcf_Rn = _param(
        inp,
        "rn222_inhalation_Sv_per_h_per_Bq_per_m3",
        rn.rn222_inhalation_Sv_per_h_per_Bq_per_m3,
    )
    dose_Sv = (
        c_rn
        * eq_factor
        * dcf_Rn
        * hours_indoor
        * inp.fraction_land_contaminated
    )
    if inp.radon_mode == RadonMode.MEASURED:
        contrib = {"(measured Rn-222)": _mSv(dose_Sv)}
    else:
        contrib = {"Ra-226": _mSv(dose_Sv)}
    return PathwayResult(
        pathway="radon_indoor",
        label=ds.pathways["radon_indoor"].label,
        dose_mSv_per_year=_mSv(dose_Sv),
        contributing_isotopes=contrib,
    )


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------


PATHWAY_FUNCTIONS = {
    "external": dose_external,
    "soil_ingestion": dose_soil_ingestion,
    "inhalation_dust": dose_inhalation_dust,
    "skin": dose_skin,
    "produce": dose_produce,
    "radon_indoor": dose_radon,
}


__all__ = [
    "dose_external",
    "dose_soil_ingestion",
    "dose_inhalation_dust",
    "dose_skin",
    "dose_produce",
    "dose_radon",
    "PATHWAY_FUNCTIONS",
]
