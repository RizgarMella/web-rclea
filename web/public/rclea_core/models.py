"""Pydantic models for RCLEA inputs, lookups, and outputs."""
from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class AgeGroup(str, Enum):
    INFANT = "infant"
    CHILD = "child"
    ADULT = "adult"


class Sex(str, Enum):
    MALE = "male"
    FEMALE = "female"


class RadonMode(str, Enum):
    """How indoor Rn-222 concentration is determined.

    default:       C_Rn = 3 Bq/m^3 per Bq/kg Ra-226 (conservative generic)
    measured:      user supplies measured indoor C_Rn directly in Bq/m^3
    site_specific: C_Rn computed from soil emanation/diffusion + building height/ventilation
                   via the classical 1-D radon exhalation model:
                     K = (alpha * rho_B * sqrt(D_e * lambda_Rn)) / (h * (lambda_v + lambda_Rn))
                     C_Rn = K * C_Ra226
    """

    DEFAULT = "default"
    MEASURED = "measured"
    SITE_SPECIFIC = "site_specific"


class AssessmentMode(str, Enum):
    """Generic = find the worst receptor combo; site_specific = use the exact user-picked combo."""

    GENERIC = "generic"
    SITE_SPECIFIC = "site_specific"


# --- Lookup (library) models -------------------------------------------------


class Isotope(BaseModel):
    model_config = ConfigDict(frozen=False, extra="allow")

    id: str
    name: str
    element: str
    ingestion_Sv_per_Bq: dict[str, float]
    inhalation_Sv_per_Bq: dict[str, float]
    external_Sv_per_y_per_Bq_per_m3: float
    skin_beta_Sv_per_y_per_Bq_per_cm2: float = 0.0
    skin_gamma_Sv_per_y_per_Bq_per_cm2: float = 0.0


class Element(BaseModel):
    id: str
    kd_m3_per_kg: float
    plant_uptake_affinity: float
    soil_to_plant_cf_fw_per_dw: float


class ScenarioAgeParams(BaseModel):
    model_config = ConfigDict(extra="allow")

    soil_ingestion_kg_per_y: float = 0.0
    occupancy_indoor_fraction: float = 0.0
    occupancy_outdoor_fraction: float = 0.0
    skin_contact_fraction_indoor: float = 0.0
    active_fraction_indoor: float = 0.0
    passive_fraction_indoor: float = 0.0
    skin_contact_fraction_outdoor: float = 0.0
    active_fraction_outdoor: float = 0.0
    passive_fraction_outdoor: float = 0.0
    skin_soil_loading_indoor_mg_per_cm2: float = 0.0
    skin_exposed_fraction_indoor: float = 0.0
    skin_soil_loading_outdoor_mg_per_cm2: float = 0.0
    skin_exposed_fraction_outdoor: float = 0.0


class ScenarioPathwayFlags(BaseModel):
    external: bool = True
    soil_ingestion: bool = True
    skin: bool = True
    inhalation_dust: bool = True
    produce: bool = False
    radon_indoor: bool = False


class ScenarioDust(BaseModel):
    fraction_indoor_dust_from_local_soil: float = 0.75
    air_respirable_particles_kg_per_m3: float = 5e-8


class Scenario(BaseModel):
    id: str
    label: str
    area_hectares: float
    pathways: ScenarioPathwayFlags
    dust: ScenarioDust
    per_age: dict[str, ScenarioAgeParams]


class Building(BaseModel):
    id: str
    label: str | None = None
    shielding_factor: float
    rn222_height_m: float = 3.0
    rn222_ventilation_rate_per_s: float = 8.33e-5

    @property
    def name(self) -> str:
        return self.label or self.id


class CropMeta(BaseModel):
    home_fraction: float
    soil_loading_kg_dw_per_kg_fw: float


class Receptors(BaseModel):
    body_weight_kg: dict[str, dict[str, float]]  # sex -> age -> kg
    respiration_m3_per_h: dict[str, dict[str, dict[str, float]]]  # sex -> age -> {active, passive}
    uv_exposed_skin_fraction: float
    tissue_weighting_factor_uv_skin: float


class RadonParams(BaseModel):
    rn222_inhalation_Sv_per_h_per_Bq_per_m3: float
    rn222_equilibrium_factor: float
    rn222_decay_constant_per_s: float
    default_rn222_conversion_Bq_m3_per_Bq_kg: float


class SoilGlobal(BaseModel):
    """Soil properties shared across all elements (from SoilAndPlant sheet, element-independent block)."""

    enrichment_factor: float = 3.0
    water_filled_porosity: float = 0.25
    total_porosity: float = 0.5
    bulk_density_kg_per_m3: float = 1400.0
    rn222_emanation_fraction: float = 0.2
    rn222_effective_diffusion_m2_per_s: float = 2e-6


class Pathway(BaseModel):
    id: str
    label: str
    unit: str
    short: str
    equation: str


class Constants(BaseModel):
    effective_dose_criterion_mSv_per_y: float
    equivalent_skin_dose_criterion_mSv_per_y: float
    hours_per_year: float
    Sv_per_mSv: float
    default_fraction_land_contaminated: float
    rho_B_soil_bulk_density_kg_per_m3: float
    uv_tissue_weighting_factor: float
    dust_loading_kg_per_m3: float


class Dataset(BaseModel):
    """Loaded and validated data/*.json files."""

    isotopes: dict[str, Isotope]
    radon: RadonParams
    elements: dict[str, Element]
    soil_global: SoilGlobal
    scenarios: dict[str, Scenario]
    receptors: Receptors
    buildings: dict[str, Building]
    consumption_by_age: dict[str, dict[str, float]]  # age -> crop -> kg/y per kg bw
    crop_meta: dict[str, CropMeta]
    pathways: dict[str, Pathway]
    constants: Constants


# --- Input model -------------------------------------------------------------


class AssessmentInput(BaseModel):
    """What the user supplies to run an assessment."""

    model_config = ConfigDict(str_strip_whitespace=True)

    soil_concentrations_Bq_per_kg: dict[str, float] = Field(
        description="Map of radionuclide id (e.g. 'Cs-137') to soil activity in Bq/kg dry weight.",
    )
    scenario_id: str = Field(description="id from data/scenarios.json")
    age: AgeGroup = AgeGroup.ADULT
    sex: Sex = Sex.MALE
    building_id: str = "Timber"
    fraction_land_contaminated: float = 1.0
    radon_mode: RadonMode = RadonMode.DEFAULT
    measured_rn222_Bq_per_m3: float | None = None
    overrides: dict[str, float] = Field(
        default_factory=dict,
        description=(
            "Optional per-parameter overrides keyed by hierarchical name, e.g. "
            "'dust_loading_kg_per_m3', 'soil_ingestion_kg_per_y.infant', "
            "'occupancy_indoor_fraction.adult'. Replaces the Library value for the current assessment only."
        ),
    )


# --- Result models -----------------------------------------------------------


class PathwayResult(BaseModel):
    pathway: str
    label: str
    dose_mSv_per_year: float
    contributing_isotopes: dict[str, float]  # isotope -> mSv/y contribution


class AssessmentResult(BaseModel):
    total_effective_dose_mSv_per_y: float
    total_skin_equivalent_dose_mSv_per_y: float
    effective_dose_criterion_mSv_per_y: float
    skin_dose_criterion_mSv_per_y: float
    exceeds_effective_criterion: bool
    exceeds_skin_criterion: bool
    safety_margin: float | None  # criterion / total_dose; None if total_dose == 0
    per_pathway: list[PathwayResult]
    inputs_echo: AssessmentInput
    notes: list[str] = Field(default_factory=list)
    disclaimer: str


class WorstCaseEntry(BaseModel):
    scenario_id: str
    scenario_label: str
    building_id: str
    age: AgeGroup
    sex: Sex
    total_effective_dose_mSv_per_y: float
    exceeds_effective_criterion: bool


class WorstCaseReport(BaseModel):
    soil_concentrations_Bq_per_kg: dict[str, float]
    fraction_land_contaminated: float
    radon_mode: RadonMode
    measured_rn222_Bq_per_m3: float | None
    effective_dose_criterion_mSv_per_y: float
    entries: list[WorstCaseEntry]  # sorted descending by dose
    worst: WorstCaseEntry
    disclaimer: str


class RSGVReport(BaseModel):
    scenario_id: str
    scenario_label: str
    age: AgeGroup
    sex: Sex
    building_id: str
    radon_mode: RadonMode
    effective_dose_criterion_mSv_per_y: float
    rsgvs_Bq_per_kg: dict[str, float]  # isotope_id -> Bq/kg; +inf if isotope yields zero dose
    disclaimer: str


# --- Verbose intermediate type for "explain this number" --------------------


class ExplainTerm(BaseModel):
    symbol: str
    value: float
    units: str
    source: Literal["input", "scenario", "receptor", "building", "isotope", "element", "constant"]
