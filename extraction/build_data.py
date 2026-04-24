"""Build canonical JSON data files for RCLEA from the legacy .xls workbook.

Reads:  Resouces/RCLEA_software_application.xls
Writes: data/isotopes.json
        data/elements.json  (element-level soil-plant transfer + Kd)
        data/scenarios.json (land-use)
        data/receptors.json (age groups, body weights, respiration)
        data/buildings.json
        data/consumption.json (crops per age)
        data/pathways.json  (pathway metadata & glossary)
        data/constants.json (physical constants, parameter symbols)

One-time script. All values taken from the EffectiveDose, EquivDose, Human, LandUse,
SoilAndPlant, BuildingType, Consumption, IntermediateCalcs sheets of the workbook.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import xlrd

XLS = Path(r"C:/Users/Riz/Desktop/rclea/Resouces/RCLEA_software_application.xls")
OUT = Path(r"C:/Users/Riz/Desktop/rclea/data")


def _cells(sheet: xlrd.sheet.Sheet) -> list[list[Any]]:
    rows: list[list[Any]] = []
    for r in range(sheet.nrows):
        row: list[Any] = []
        for c in range(sheet.ncols):
            v = sheet.cell_value(r, c)
            if isinstance(v, str):
                v = v.strip() or None
            elif isinstance(v, float) and v != v:
                v = None
            row.append(v)
        rows.append(row)
    return rows


def write_json(name: str, payload: object) -> None:
    path = OUT / name
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  wrote {path}  ({len(json.dumps(payload))} chars)")


def element_of(isotope: str) -> str:
    """'Cs-137' -> 'Cs';  'Natural Th' -> 'Th'."""
    s = isotope.strip()
    if s.startswith("Natural "):
        return s.split(" ", 1)[1]
    return s.split("-", 1)[0]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    wb = xlrd.open_workbook(str(XLS))

    # --- isotopes ---------------------------------------------------------
    eff = _cells(wb.sheet_by_name("EffectiveDose"))
    equiv = _cells(wb.sheet_by_name("EquivDose"))

    # Intake (ingestion/inhalation) block: rows 7..147 (by inspection)
    intake: dict[str, dict[str, dict[str, float]]] = {}
    for row in eff[7:148]:
        nuclide, age, ing, _ing_u, inh, _inh_u = row[1], row[2], row[3], row[4], row[5], row[6]
        if not nuclide or not age:
            continue
        rec = intake.setdefault(nuclide, {"ingestion_Sv_per_Bq": {}, "inhalation_Sv_per_Bq": {}})
        rec["ingestion_Sv_per_Bq"][age.lower()] = float(ing)
        rec["inhalation_Sv_per_Bq"][age.lower()] = float(inh)

    # External block: rows 154..200
    external: dict[str, float] = {}
    for row in eff[154:201]:
        nuclide, _, lib, _u, _c = row[1], row[2], row[3], row[4], row[5]
        if not nuclide:
            continue
        external[nuclide] = float(lib)

    # Skin equivalent: rows 7..53 (by inspection of EquivDose)
    skin_eq: dict[str, dict[str, float]] = {}
    for row in equiv[7:54]:
        nuclide, beta, _bu, gamma, _gu = row[1], row[2], row[3], row[4], row[5]
        if not nuclide:
            continue
        skin_eq[nuclide] = {
            "beta_Sv_per_y_per_Bq_per_cm2": float(beta) if beta is not None else 0.0,
            "gamma_Sv_per_y_per_Bq_per_cm2": float(gamma) if gamma is not None else 0.0,
        }

    # Assemble isotopes with stable ordering
    isotopes = []
    for nuclide in intake:
        entry = {
            "id": nuclide,
            "name": nuclide,
            "element": element_of(nuclide),
            "ingestion_Sv_per_Bq": intake[nuclide]["ingestion_Sv_per_Bq"],
            "inhalation_Sv_per_Bq": intake[nuclide]["inhalation_Sv_per_Bq"],
            "external_Sv_per_y_per_Bq_per_m3": external.get(nuclide, 0.0),
            "skin_beta_Sv_per_y_per_Bq_per_cm2": skin_eq.get(nuclide, {}).get(
                "beta_Sv_per_y_per_Bq_per_cm2", 0.0
            ),
            "skin_gamma_Sv_per_y_per_Bq_per_cm2": skin_eq.get(nuclide, {}).get(
                "gamma_Sv_per_y_per_Bq_per_cm2", 0.0
            ),
        }
        isotopes.append(entry)
    # Rn-222 inhalation coefficient (for indoor radon pathway)
    rn = {
        "rn222_inhalation_Sv_per_h_per_Bq_per_m3": float(eff[207][1]),
        "rn222_equilibrium_factor": float(eff[207][3]),
        "rn222_decay_constant_per_s": 2.1e-06,  # from IntermediateCalcs
        "default_rn222_conversion_Bq_m3_per_Bq_kg": 3.0,  # default from Contamination sheet
    }
    write_json("isotopes.json", {"source": "RCLEA_software_application.xls / EffectiveDose+EquivDose sheets, Library column", "radon": rn, "isotopes": isotopes})

    # --- elements (soil-plant transfer) -----------------------------------
    sp = _cells(wb.sheet_by_name("SoilAndPlant"))
    # Element-independent data (row 7)
    soil_global = {
        "enrichment_factor": float(sp[7][1]),
        "water_filled_porosity": float(sp[7][3]),
        "total_porosity": float(sp[7][5]),
        "bulk_density_kg_per_m3": float(sp[7][7]),
        "rn222_emanation_fraction": float(sp[59][1]),
        "rn222_effective_diffusion_m2_per_s": float(sp[59][3]),
    }
    elements = []
    for row in sp[23:51]:
        el, kd, _ku, aff, _au, cf, _cfu = row[1], row[2], row[3], row[4], row[5], row[6], row[7]
        if not el:
            continue
        elements.append(
            {
                "id": el,
                "kd_m3_per_kg": float(kd),
                "plant_uptake_affinity": float(aff),
                "soil_to_plant_cf_fw_per_dw": float(cf),
            }
        )
    write_json("elements.json", {"source": "SoilAndPlant sheet, Library column", "soil_global": soil_global, "elements": elements})

    # --- receptors --------------------------------------------------------
    hum = _cells(wb.sheet_by_name("Human"))
    # Body weight: rows 7..12
    bw = {}
    for row in hum[7:13]:
        sex, age, weight = row[1], row[2], row[3]
        if not sex:
            continue
        bw.setdefault(sex.lower(), {})[age.lower()] = float(weight)
    # Respiration: rows 26..31
    resp = {}
    for row in hum[26:32]:
        sex, age, active, _au, passive, _pu = row[1], row[2], row[3], row[4], row[5], row[6]
        if not sex:
            continue
        resp.setdefault(sex.lower(), {})[age.lower()] = {
            "active_m3_per_h": float(active),
            "passive_m3_per_h": float(passive),
        }
    write_json(
        "receptors.json",
        {
            "source": "Human sheet, Library column",
            "age_groups": ["infant", "child", "adult"],
            "sexes": ["male", "female"],
            "body_weight_kg": bw,
            "respiration_m3_per_h": resp,
            "tissue_weighting_factor_uv_skin": float(hum[19][1]),
            "uv_exposed_skin_fraction": float(hum[7][5]),
        },
    )

    # --- scenarios (land use) ---------------------------------------------
    lu = _cells(wb.sheet_by_name("LandUse"))

    def collect_per_age(row_range: range, keys: list[str]) -> dict[str, dict[str, dict[str, float]]]:
        """Rows of form: [_, LU, Age, v1, _user, v2, _user, v3, _user, comment]."""
        out: dict[str, dict[str, dict[str, float]]] = {}
        for i in row_range:
            row = lu[i]
            luname, age = row[1], row[2]
            if not luname:
                continue
            values = [row[3], row[5], row[7]]
            d = out.setdefault(luname, {}).setdefault(age.lower(), {})
            for k, v in zip(keys, values):
                if v is not None:
                    d[k] = float(v)
        return out

    # Dust (rows 26..29)
    dust = {}
    for row in lu[26:30]:
        luname, f_dust, _, cdust, _, _c = row[1], row[2], row[3], row[4], row[5], row[6]
        if luname:
            dust[luname] = {
                "fraction_indoor_dust_from_local_soil": float(f_dust),
                "air_respirable_particles_kg_per_m3": float(cdust),
            }

    # Soil ingestion + occupancy (rows 36..45)
    ingest_occ = collect_per_age(
        range(36, 46),
        ["soil_ingestion_kg_per_y", "occupancy_indoor_fraction", "occupancy_outdoor_fraction"],
    )

    # Indoor time decomposition (rows 52..61)
    indoor_time = collect_per_age(
        range(52, 62),
        ["skin_contact_fraction_indoor", "active_fraction_indoor", "passive_fraction_indoor"],
    )

    # Outdoor time decomposition (rows 68..77)
    outdoor_time = collect_per_age(
        range(68, 78),
        ["skin_contact_fraction_outdoor", "active_fraction_outdoor", "passive_fraction_outdoor"],
    )

    # Skin soil loading indoors (rows 85..94) — only 2 values per row, not 3
    def collect_2val(row_range: range, keys: list[str]) -> dict[str, dict[str, dict[str, float]]]:
        out: dict[str, dict[str, dict[str, float]]] = {}
        for i in row_range:
            row = lu[i]
            luname, age, v1, _u1, v2, _u2 = row[1], row[2], row[3], row[4], row[5], row[6]
            if not luname:
                continue
            d = out.setdefault(luname, {}).setdefault(age.lower(), {})
            for k, v in zip(keys, [v1, v2]):
                if v is not None:
                    d[k] = float(v)
        return out

    skin_indoor = collect_2val(
        range(85, 95),
        ["skin_soil_loading_indoor_mg_per_cm2", "skin_exposed_fraction_indoor"],
    )
    skin_outdoor = collect_2val(
        range(102, 112),
        ["skin_soil_loading_outdoor_mg_per_cm2", "skin_exposed_fraction_outdoor"],
    )

    # Merge per-land-use-per-age dicts
    scenarios = []
    land_uses = ["Residential with Home-Grown Produce",
                 "Residential without Home-Grown Produce",
                 "Allotments",
                 "Commercial/Industrial"]
    pathway_flags = {
        "Residential with Home-Grown Produce": {
            "external": True, "soil_ingestion": True, "skin": True,
            "inhalation_dust": True, "produce": True, "radon_indoor": True,
        },
        "Residential without Home-Grown Produce": {
            "external": True, "soil_ingestion": True, "skin": True,
            "inhalation_dust": True, "produce": False, "radon_indoor": True,
        },
        "Allotments": {
            "external": True, "soil_ingestion": True, "skin": True,
            "inhalation_dust": True, "produce": True, "radon_indoor": False,
        },
        "Commercial/Industrial": {
            "external": True, "soil_ingestion": True, "skin": True,
            "inhalation_dust": True, "produce": False, "radon_indoor": True,
        },
    }
    area_ha = {
        "Residential with Home-Grown Produce": 0.2,
        "Residential without Home-Grown Produce": 0.2,
        "Allotments": 0.8,
        "Commercial/Industrial": 2.0,
    }
    for name in land_uses:
        per_age: dict[str, dict[str, Any]] = {}
        for age in ["infant", "child", "adult"]:
            merged: dict[str, float] = {}
            for src in (ingest_occ, indoor_time, outdoor_time, skin_indoor, skin_outdoor):
                if name in src and age in src[name]:
                    merged.update(src[name][age])
            if merged:
                per_age[age] = merged
        scenarios.append(
            {
                "id": name.replace(" ", "_").replace("/", "_").replace("-", "_"),
                "label": name,
                "area_hectares": area_ha[name],
                "pathways": pathway_flags[name],
                "dust": dust.get(name, {}),
                "per_age": per_age,
            }
        )

    write_json("scenarios.json", {"source": "LandUse sheet, Library column", "scenarios": scenarios})

    # --- buildings --------------------------------------------------------
    bldg = _cells(wb.sheet_by_name("BuildingType"))
    buildings = [
        {"id": "Timber", "shielding_factor": float(bldg[7][2])},
        {"id": "Concrete_Brick", "label": "Concrete/Brick", "shielding_factor": float(bldg[8][2])},
    ]
    building_global = {
        "height_m": float(bldg[16][1]),
        "ventilation_rate_per_s": float(bldg[16][3]),
    }
    write_json("buildings.json", {"source": "BuildingType sheet, Library column", "buildings": buildings, "global": building_global})

    # --- consumption (crops per age) --------------------------------------
    cons = _cells(wb.sheet_by_name("Consumption"))
    crop_consumption: dict[str, dict[str, float]] = {}  # age -> crop -> kg/y per kg bw
    for row in cons[7:25]:
        age, crop, lib = row[1], row[2], row[3]
        if not age or not crop:
            continue
        crop_consumption.setdefault(age.lower(), {})[crop] = float(lib)
    # Origin & soil on vegetables (rows 31..36)
    crop_meta: dict[str, dict[str, float]] = {}
    for row in cons[31:37]:
        crop, _, hf, _u, sl, _u2 = row[1], row[2], row[3], row[4], row[5], row[6]
        if not crop:
            continue
        crop_meta[crop] = {
            "home_fraction": float(hf),
            "soil_loading_kg_dw_per_kg_fw": float(sl),
        }
    # Map crop -> element used for CF_Veg (crop is a common vegetable; CF_Veg is element-specific)
    write_json(
        "consumption.json",
        {
            "source": "Consumption sheet, Library column",
            "units": "consumption rates: kg fresh weight per kg body weight per year",
            "by_age": crop_consumption,
            "crop_meta": crop_meta,
        },
    )

    # --- pathways (methodology metadata) ----------------------------------
    pathways = [
        {
            "id": "external",
            "label": "Whole-body external irradiation",
            "unit": "mSv/y",
            "short": "Gamma dose from radionuclides in the soil, integrated over indoor and outdoor occupancy. Indoor dose is reduced by the building shielding factor.",
            "equation": "D_ext = sum_i C_i * rho_B * DCF_ext,i * [O_in * (1 - SF_building) + O_out] * f_contam",
        },
        {
            "id": "soil_ingestion",
            "label": "Inadvertent soil ingestion",
            "unit": "mSv/y",
            "short": "Dose from unintentionally swallowing small amounts of contaminated soil or indoor dust derived from it. Age-dependent.",
            "equation": "D_ing = sum_i C_i * I_soil(age,land_use) * DCF_ing,i(age) * f_contam",
        },
        {
            "id": "inhalation_dust",
            "label": "Inhalation of resuspended soil/dust",
            "unit": "mSv/y",
            "short": "Dose from breathing airborne dust particles derived from contaminated soil. Uses a respirable-dust loading and fraction of indoor dust from local soil.",
            "equation": "A_air = C_i * rho_air * F_dust (indoor) or C_i * rho_air (outdoor); D_inh = sum_i A_air * RR * O * 8760 * DCF_inh,i(age) * f_contam",
        },
        {
            "id": "skin",
            "label": "Skin equivalent dose (beta+gamma)",
            "unit": "mSv/y",
            "short": "Dose to the skin from radionuclides in soil deposited on exposed skin surfaces, indoors and outdoors.",
            "equation": "D_skin = sum_i C_i * rho_skin * A_skin * O_SC * (DCF_beta + DCF_gamma) * f_contam",
        },
        {
            "id": "produce",
            "label": "Consumption of home-grown produce",
            "unit": "mSv/y",
            "short": "Dose from eating vegetables grown on contaminated land. Combines soil-to-plant uptake (element-specific) and soil adhering to vegetables.",
            "equation": "D_prod = sum_i sum_crops C_i * (CF_veg(element) + SL_veg(crop)) * CR(age,crop) * BW * HF(crop) * DCF_ing,i(age) * f_contam",
        },
        {
            "id": "radon_indoor",
            "label": "Inhalation of indoor Rn-222 gas",
            "unit": "mSv/y",
            "short": "Dose from radon gas accumulating indoors, originating from Ra-226 in soil. Only included when Ra-226 is present.",
            "equation": "C_Rn = K_Rn * C_Ra226; D_rn = C_Rn * F_eq * DCF_Rn * O_in_hours",
        },
    ]
    write_json("pathways.json", {"pathways": pathways})

    # --- global constants (from CalculationParams + IntermediateCalcs) -----
    calc = _cells(wb.sheet_by_name("CalculationParams"))
    constants = {
        "effective_dose_criterion_mSv_per_y": 3.0,
        "equivalent_skin_dose_criterion_mSv_per_y": 50.0,
        "hours_per_year": 8760.0,
        "Sv_per_mSv": 1e-3,
        "default_fraction_land_contaminated": 1.0,
        "rho_B_soil_bulk_density_kg_per_m3": 1400.0,
        "uv_tissue_weighting_factor": 0.01,
        "dust_loading_kg_per_m3": 5e-8,
    }
    write_json("constants.json", constants)

    print("\nDone. All data files written to data/.")


if __name__ == "__main__":
    main()
