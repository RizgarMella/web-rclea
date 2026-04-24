# RCLEA: an educational remake

A modern, extensible, open re-implementation of the UK **Radioactively Contaminated Land Exposure Assessment** (RCLEA) methodology, shipped as:

1. A **single-page web application** (branded `webRCLEA` in the UI) that runs entirely in the browser, no server, via Pyodide.
2. A **Python command-line application** (`rclea`).
3. A **7-module interactive tutorial curriculum** usable in both.

Both the web app and the CLI invoke the **same** Python calculation engine (`rclea_core`). The radionuclide catalogue, land-use scenarios, and reference parameters are plain JSON files — adding a new isotope or scenario needs **no code change**.

---

> ### Educational use only
>
> This software is a study tool. It is **not** a regulatory instrument, is **not** affiliated with or endorsed by the UK Environment Agency or UKHSA, and must **not** be used as the sole basis for decisions under Part 2A of the Environmental Protection Act 1990 or any equivalent regime. The author(s) accept **no liability** for any consequence of using this software or its outputs. See [`DISCLAIMER.md`](DISCLAIMER.md) for the full disclaimer. Conservative default assumptions may over- or under-estimate real risk; always cross-reference the primary guidance (CRCE-RAD-003-2020, CLR-13, the Part 2A Statutory Guidance) and consult a qualified radiological practitioner for real-world application.

---

## Contents

- [1. Overview](#1-overview)
- [2. Regulatory context](#2-regulatory-context)
- [3. The methodology](#3-the-methodology)
  - [3.1 Dose criteria and safety margin](#31-dose-criteria-and-safety-margin)
  - [3.2 Land-use scenarios](#32-land-use-scenarios)
  - [3.3 Receptor age groups and sex](#33-receptor-age-groups-and-sex)
  - [3.4 Building types](#34-building-types)
  - [3.5 The six exposure pathways](#35-the-six-exposure-pathways)
  - [3.6 The three radon modes](#36-the-three-radon-modes)
  - [3.7 Worst-case scenario finding (generic mode)](#37-worst-case-scenario-finding-generic-mode)
  - [3.8 Per-isotope RSGVs](#38-per-isotope-rsgvs)
  - [3.9 Per-parameter overrides](#39-per-parameter-overrides)
  - [3.10 Custom land-use scenarios](#310-custom-land-use-scenarios)
  - [3.11 Conservative defaults](#311-conservative-defaults)
- [4. The radionuclide catalogue](#4-the-radionuclide-catalogue)
- [5. Data reference](#5-data-reference)
- [6. The Python CLI (`rclea`)](#6-the-python-cli-rclea)
- [7. The web application (`webRCLEA`)](#7-the-web-application-webrclea)
- [8. Tutorials](#8-tutorials)
- [9. Extending the tool](#9-extending-the-tool)
- [10. Architecture](#10-architecture)
- [11. Development and testing](#11-development-and-testing)
- [12. Deployment](#12-deployment)
- [13. References](#13-references)
- [14. Licence](#14-licence)

---

## 1. Overview

RCLEA is the UK screening methodology for estimating the annual effective dose received by a representative person from radioactive contamination in soil. It sits under Part 2A of the Environmental Protection Act 1990 (as amended for radioactivity by the 2006 and 2018 regulations). Results are compared against the **3 mSv/y** effective-dose criterion that defines "significant harm" under the statutory guidance.

The official tool is an Excel 97–2003 workbook (`RCLEA_software_application.xls`) with VBA macros. It has reached end-of-life as a platform: the `.xls` format is obsolete, macros are blocked by modern IT policy, extending the catalogue requires cell editing, there is no test coverage, and the tool cannot run on mobile or in a browser.

This project rebuilds the tool from the published methodology (CRCE-RAD-003-2020, CLR-13, the Part 2A Statutory Guidance) **feature-complete with the original workbook** across 18 sheets:

- A **pure Python calculation engine** (`rclea_core`): ~900 lines, fully typed, zero UI concerns.
- **JSON data files**: the single source of truth for isotopes, elements, scenarios, receptors, building types, consumption rates, pathways, soil-global properties, and constants.
- A **Typer CLI** (`rclea_cli`): for power users, scripting, batch runs.
- A **React + Vite + Tailwind SPA** branded `webRCLEA` that loads the Python engine into the browser via Pyodide.
- A **7-module tutorial curriculum** shared between CLI and web, with embedded interactive assessment steps that run the real engine inline.

Features matched to the original workbook:

| Workbook sheet | Feature | Location in remake |
|---|---|---|
| `EffectiveDose` + `EquivDose` | Dose coefficients (ingestion, inhalation, external, skin) for 48 radionuclides | `data/isotopes.json` |
| `Contamination` | Soil concentrations input; three Rn-222 modes | Assess tab + `--radon-mode` flag |
| `LandUse` | Four reference scenarios with per-age exposure parameters | `data/scenarios.json` |
| `NewLandUse` | User-defined custom land-use scenarios | Custom tab + `scenarios template/register` |
| `BuildingType` | Two building types with shielding + radon height/ventilation | `data/buildings.json` |
| `Human` | Body weight and respiration by sex and age | `data/receptors.json` |
| `Consumption` | Six crops with age-specific consumption + home fraction | `data/consumption.json` |
| `SoilAndPlant` | Element-specific soil-plant transfer factors + soil global properties | `data/elements.json` |
| `Doses` | Per-pathway dose breakdown + total | Results panel + `rclea assess` |
| `AllDoses` | Dose matrix across (scenario × building × age × sex) | Generic mode + `rclea worst-case` |
| `GuidelineValues` | Per-isotope RSGVs + Safety Margin | Guidelines tab + `rclea rsgv` |
| `CalculationParams` | Every parameter overridable | "Advanced / Overrides" disclosure + `--override KEY=VALUE` |
| `IntermediateCalcs` | Radon K calculation details | `_site_specific_K()` in `pathways.py` |
| `Intro`, `Instructions`, `SideCalcs` | Splash, help, scratchpad | Replaced by this README + tutorials |
| `Main` | Control dashboard | Replaced by the web Assess tab |

Every feature is covered by a pytest test (48 tests passing, including the extensibility and round-trip tests) and an educational-use disclaimer that appears in the CLI banner, the web modal + sticky banner + footer, exported reports, and every tutorial introduction.

---

## 2. Regulatory context

| Instrument | Role |
|---|---|
| **Environmental Protection Act 1990, Part 2A** (as amended) | Defines "contaminated land" in England and the duty to identify and remediate it. |
| **Radioactive Contaminated Land (Enabling Powers) (England) Regulations 2005** (SI 2005/3467, amended 2010, 2018) | Extends Part 2A to radioactive contamination. |
| **Council Directive 2013/59/Euratom** (Basic Safety Standards Directive) | Sets dose limits for public exposure; implemented through the above. |
| **CRCE-RAD-003-2020** (UKHSA) | Technical principles underpinning RCLEA. |
| **CLR-13** (Environment Agency) | Practical user guide to the original workbook, with worked examples. |
| **Part 2A Statutory Guidance** (DEFRA/EA, 2018 consolidated) | Binding interpretation for local authorities. |

**Key legal terms:**

- **Contaminant linkage**: (source, pathway, receptor) triple that must all be present for Part 2A to apply.
- **Significant harm** (for radiation from contaminated land): effective dose above **3 mSv/y**, or equivalent dose above **15 mSv/y to the lens of the eye** or **50 mSv/y to skin**, excluding natural background.
- **SPOSH** ("significant possibility of significant harm"): the legal test. Requires both capacity to cause significant harm and a significant probability of that happening.

Scotland, Wales, and Northern Ireland have equivalent separately made regulations; the methodology is the same.

---

## 3. The methodology

### 3.1 Dose criteria and safety margin

| Criterion | Threshold | Location in results |
|---|---|---|
| Total effective dose | **3 mSv/year** | `AssessmentResult.exceeds_effective_criterion` |
| Skin equivalent dose | **50 mSv/year** | `AssessmentResult.exceeds_skin_criterion` |
| Safety margin | `criterion / total_dose` | `AssessmentResult.safety_margin` |

The **safety margin** is a single-number summary: ≥ 1 means the site is below the 3 mSv/y threshold (the bigger the better); < 1 means above (and 1 / margin tells you how far above). The CLI prints it colour-coded; the web app shows it on the Results panel.

Background radiation is **excluded**. RCLEA counts only the anthropogenic contamination.

### 3.2 Land-use scenarios

The reference scenarios determine which pathways are active, indoor/outdoor occupancy, soil ingestion rate, and — for residential and allotment scenarios — the produce pathway. The catalogue ships four scenarios plus any **custom scenarios** registered via the CLI or web (§3.10):

| `scenario_id` | Label | Area (ha) | Pathways included |
|---|---|---|---|
| `Residential_with_Home_Grown_Produce` | Residential with home-grown produce | 0.2 | external, soil ingestion, skin, inhalation (dust), produce, indoor radon |
| `Residential_without_Home_Grown_Produce` | Residential without home-grown produce | 0.2 | external, soil ingestion, skin, inhalation (dust), indoor radon |
| `Allotments` | Allotments | 0.8 | external, soil ingestion, skin, inhalation (dust), produce |
| `Commercial_Industrial` | Commercial / industrial | 2.0 | external, soil ingestion, skin, inhalation (dust), indoor radon (adult only) |

Each scenario has age-specific parameters: `soil_ingestion_kg_per_y`, fractional indoor and outdoor occupancy, active vs. passive breathing fractions, skin contact fractions, skin soil loading (indoor + outdoor). Defaults are taken from the LandUse and CalculationParams sheets of the reference workbook and cross-checked against CRCE-RAD-003-2020 Annex tables.

### 3.3 Receptor age groups and sex

Three ICRP-representative age groups × two sexes (`data/receptors.json`):

| Age | Body weight M/F (kg) | Active respiration M/F (m³/h) |
|---|---|---|
| Infant (1 yr) | 11.0 / 11.0 | 0.339 / 0.320 |
| Child (10 yr) | 37.0 / 37.0 | 1.103 / 1.100 |
| Adult (20 yr) | 81.0 / 68.0 | 1.456 / 1.234 |

Sex affects body weight (used in the produce pathway) and respiration rate (used in the inhalation pathway); it does not change published ICRP dose coefficients.

### 3.4 Building types

Two shipped building types plus per-building radon transport parameters:

| `building_id` | γ shielding factor | `rn222_height_m` | `rn222_ventilation_rate_per_s` |
|---|---|---|---|
| `Timber` | 0.0 | 3.0 | 8.33 × 10⁻⁵ |
| `Concrete_Brick` | 0.9 | 3.0 | 8.33 × 10⁻⁵ |

The shielding factor multiplies the indoor external dose; the radon parameters feed into the site-specific K calculation (§3.6).

### 3.5 The six exposure pathways

All pathway functions live in `src/rclea_core/pathways.py`. They are pure: `AssessmentInput + Dataset → PathwayResult`. Each respects user overrides via the `_param()` helper (§3.9).

**Notation.** `Cᵢ` — soil concentration Bq/kg; `ρ_B` — soil bulk density, 1400 kg/m³; `O_in`, `O_out` — indoor/outdoor fractional occupancy; `SF` — shielding factor; `f_contam` — fraction of land contaminated (user input, default 1.0); `I_soil` — annual soil ingestion rate (kg/y); `DCF_ing,i(age)`, `DCF_inh,i(age)` — ICRP ingestion/inhalation DCF, Sv/Bq; `DCF_ext,i` — external DCF, Sv/y per Bq/m³.

**1. External whole-body γ** (`dose_external`):

```
D_ext = Σᵢ Cᵢ × ρ_B × DCF_ext,i × [O_in × (1 − SF) + O_out] × f_contam
```

**2. Inadvertent soil ingestion** (`dose_soil_ingestion`):

```
D_ing = Σᵢ Cᵢ × I_soil(age, land_use) × DCF_ing,i(age) × f_contam
```

**3. Inhalation of resuspended dust** (`dose_inhalation_dust`):

```
breathed_volume (m³/y) =
    8760 × (RR_active × O_active_in + RR_passive × O_passive_in) × F_dust  (indoor)
  + 8760 × (RR_active × O_active_out + RR_passive × O_passive_out)         (outdoor)

D_inh = Σᵢ Cᵢ × dust_loading × breathed_volume × DCF_inh,i(age) × f_contam
```

**4. Skin equivalent dose β + γ** (`dose_skin`):

```
surface Bq/cm² = Cᵢ × skin_loading(mg/cm²) × 10⁻⁶ kg/mg
D_skin = Σᵢ Cᵢ × (DCF_β_i + DCF_γ_i) × ∑(loading × contact × exposed_fraction)  (indoor + outdoor) × f_contam
```

**5. Home-grown produce** (`dose_produce`):

```
bq_per_kg_fw = Cᵢ × (CF_veg(element) + SL_veg(crop))
kg_eaten     = CR(age, crop) × BW(sex, age) × HF(crop)
D_prod       = Σᵢ Σ_crops bq_per_kg_fw × kg_eaten × DCF_ing,i(age) × f_contam
```

**6. Indoor Rn-222** (`dose_radon`) — see §3.6.

### 3.6 The three radon modes

The original workbook's `Contamination` sheet offered three ways to determine the indoor Rn-222 concentration. The remake preserves all three (`AssessmentInput.radon_mode`):

#### 3.6.1 `default` — conservative generic

`C_Rn = K × C_Ra226`, with `K = 3.0 Bq/m³ per Bq/kg`. No site-specific information needed. This is what the workbook uses when no other data are provided.

#### 3.6.2 `measured` — a radon survey value

`C_Rn = measured_rn222_Bq_per_m3` (user input). Bypasses the K formula entirely. Use when you have an actual radon measurement at the site.

When `radon_mode = measured` and no value is supplied, the pathway produces zero dose and a warning appears in the result `notes`.

#### 3.6.3 `site_specific` — classical 1-D exhalation model

Derives K from soil emanation / diffusion and building ventilation / height. Formula:

```
K = (α × ρ_B × √(D_e × λ_Rn)) / (h × (λ_v + λ_Rn))
```

- `α` — Rn-222 emanation fraction (default 0.2)
- `ρ_B` — soil bulk density (1400 kg/m³)
- `D_e` — effective diffusion coefficient in soil (default 2 × 10⁻⁶ m²/s)
- `λ_Rn` — Rn-222 decay constant (2.1 × 10⁻⁶ s⁻¹)
- `h` — building height (per building; default 3 m)
- `λ_v` — building ventilation rate (per building; default 8.33 × 10⁻⁵ s⁻¹, i.e. ~0.3 air-changes/hour)

Under the default parameters this gives **K ≈ 2.239 Bq/m³ per Bq/kg** — matches the workbook's `K_calc = 2.2398` to within 0.04 %. Reducing the diffusion coefficient, reducing the emanation fraction, or increasing the ventilation rate all reduce K.

Once C_Rn is known by whichever mode:

```
D_rn = C_Rn × F_eq × DCF_Rn × (O_in × 8760 h/y) × f_contam
```

Where `F_eq = 0.4` is the radon-progeny equilibrium factor and `DCF_Rn = 9 × 10⁻⁹ Sv/h per Bq/m³` is the ICRP inhalation dose coefficient.

**Effect on total dose (Ra-226 = 2500 Bq/kg, residential infant, timber):**

| Mode | Radon dose (mSv/y) | Total (mSv/y) |
|---|---|---|
| `default` (K=3) | ~207 | ~214 |
| `site_specific` (K=2.24) | ~155 | ~161 |
| `measured` @ 50 Bq/m³ | ~1.4 | ~8.3 |

The default is intentionally conservative; a real site with a radon survey will typically show a substantially lower dose.

### 3.7 Worst-case scenario finding (generic mode)

The workbook's `AllDoses` sheet listed the effective dose for every combination of (land use × building × age × sex). The remake does the same via `find_worst_case()` in `src/rclea_core/analysis.py`, producing a sorted `WorstCaseReport`.

There are **40** valid combinations (4 scenarios × 2 buildings × 2 sexes × [3 ages for residential / allotments + 1 age for Commercial/Industrial]). The function returns all of them plus the argmax.

Usage:

- **Web:** switch the **Calculation mode** radio on the Assess tab to **Generic**. The Worst-case panel appears beside Results; age/sex/building dropdowns are disabled because the engine picks them for you.
- **CLI:** `rclea worst-case --iso Ra-226=1000` or `rclea assess --iso Ra-226=1000 --mode generic`.

Classic result: for Ra-226–dominated sites, the worst combo is always `Residential_with_Home_Grown_Produce` / `Timber` / `infant`. The tutorial lesson 7 walks through why.

### 3.8 Per-isotope RSGVs

The workbook's `GuidelineValues` sheet computed **Radioactivity in Soil Guideline Values**: the Bq/kg concentration of a single isotope that would alone produce the 3 mSv/y criterion under a given scenario. `compute_rsgvs()` in `analysis.py` does the same by solving the inverse problem: set C_i = 1 Bq/kg, run the assessment, `RSGV_i = criterion / dose_i`.

Characteristic values (residential infant, default K):

| Isotope | RSGV (Bq/kg) | Driver |
|---|---|---|
| Ra-226 | ~35 | Indoor radon |
| Co-60 | ~800 | Strong γ |
| Cs-137 | ~3 500 | γ + produce |
| Pu-239 | ~70 000 | Inhalation-limited |
| H-3 | ~100 000 | Low DCF despite high transfer |

RSGVs vary by four orders of magnitude across the catalogue — they're the fastest way to see which isotopes drive decisions on a given site.

Usage:

- **Web:** Guidelines tab. Select scenario + receptor + radon mode; the table recalculates. Site concentrations entered on the Assess tab appear as a status column. CSV download available.
- **CLI:** `rclea rsgv --scenario Residential_with_Home_Grown_Produce --age infant --format table` (or `csv` / `json`). Add `--site-iso ID=VALUE` to get the status column.

### 3.9 Per-parameter overrides

Every library value used by any pathway is overridable at assessment time via `AssessmentInput.overrides`. Keys are hierarchical strings. The engine consults `overrides.get(key, fallback)` via the `_param()` helper — unknown keys have no effect.

Common override keys:

| Key | Default | What it affects |
|---|---|---|
| `dust_loading_kg_per_m3` | 5 × 10⁻⁸ | Inhalation (dust) |
| `fraction_indoor_dust_from_local_soil` | 0.75 | Inhalation (dust) |
| `shielding_factor` | per building | External (γ) |
| `rn222_emanation_fraction` | 0.2 | Radon (site-specific mode) |
| `rn222_effective_diffusion_m2_per_s` | 2 × 10⁻⁶ | Radon (site-specific mode) |
| `building_rn222_ventilation_rate_per_s` | 8.33 × 10⁻⁵ | Radon (site-specific mode) |
| `building_rn222_height_m` | 3.0 | Radon (site-specific mode) |
| `soil_ingestion_kg_per_y.<age>` | varies | Soil ingestion |
| `occupancy_indoor_fraction.<age>` | varies | External, radon |
| `occupancy_outdoor_fraction.<age>` | varies | External |
| `active_fraction_indoor.<age>` | varies | Inhalation (dust) |
| `passive_fraction_indoor.<age>` | varies | Inhalation (dust) |
| `skin_soil_loading_indoor_mg_per_cm2.<age>` | varies | Skin |
| `soil_to_plant_cf.<element>` | varies | Produce |
| `home_fraction.<crop>` | varies | Produce |
| `rho_B_soil_bulk_density_kg_per_m3` | 1400 | External, site-specific radon |

Usage:

- **Web:** Advanced disclosure on the Assess tab → **Per-parameter overrides** editor (common keys + free-form custom keys).
- **CLI:** `--override KEY=VALUE`, repeatable. YAML scenario files can also carry `overrides: {...}`.

Overrides are per-assessment only — nothing is persisted. The `notes` list records which keys were applied, so every exported report shows departures from library defaults.

### 3.10 Custom land-use scenarios

Clone a shipped scenario and edit its per-age parameters. Useful when your site doesn't fit one of the four references — unusual occupancy patterns, non-standard vegetable fraction, bespoke commercial case.

- **Web:** Custom tab → pick base → Load base parameters → edit the grid → Save. Scenarios are stored in browser `localStorage["rclea:customScenarios:v1"]` only; nothing is uploaded. The custom scenario then appears in the main Scenario picker on the Assess tab (with `(custom)` badge).
- **CLI:** `rclea scenarios template my_scenario.json --base Residential_with_Home_Grown_Produce`, edit the JSON, then `rclea scenarios register my_scenario.json`. The overlay lives at `~/.rclea/scenarios.json` and is auto-merged on every dataset load. `rclea scenarios unregister <id>` removes a registered scenario.

The CLI overlay and the web `localStorage` are independent (a CLI-registered scenario is not visible in the browser, and vice versa).

### 3.11 Conservative defaults

RCLEA is a **screening-tier** method. Built-in assumptions are cautious so that if the result is below 3 mSv/y, further assessment is generally unnecessary:

| Assumption | Default | Why conservative |
|---|---|---|
| Fraction of land contaminated | 1.0 | Assumes the whole site is equally contaminated. |
| Contamination depth | uniform 1 m | Ignores attenuation by clean overburden. |
| Indoor dust from local soil | 0.75 | High end of plausible. |
| Building type | Timber | No shielding — conservative for external γ. |
| Radon mode | `default` (K=3) | ~34 % higher than site-specific K under default soil parameters. |
| Age group (in generic mode) | Worst-case (typically infant) | If infant exposure is plausible, run it. |

A result above 3 mSv/y does **not** automatically mean the land is contaminated under Part 2A — it means tier-2 / tier-3 assessment (site-specific refinement, probability of exposure, specialist input) is warranted.

---

## 4. The radionuclide catalogue

The shipping catalogue covers **48 radionuclides** (the 47 in the reference workbook plus Po-210, added during the extensibility proof).

| Group | Isotopes |
|---|---|
| Light | H-3, C-14, K-40 |
| Transition metals | Fe-55, Co-60, Ni-63, Se-79, Mo-93, Tc-99, Ag-108m |
| Alkali / alkaline earth | Sr-90, Cs-134, Cs-137 |
| Niobium / tin / antimony | Nb-93m, Nb-94, Sn-121m, Sn-126, Sb-125 |
| Halogen | I-129 |
| Rare earths | Pm-147, Sm-147, Sm-151, Eu-152, Eu-154, Eu-155 |
| U / Th series | Pb-210, Po-210, Ra-226, Ra-228, Ac-227, Th-228/229/230/232, Natural Th, Pa-231 |
| Uranium | U-233, U-234, U-235, U-236, U-238, Natural U |
| Transuranics | Np-237, Pu-238, Pu-239, Pu-240, Pu-241, Am-241 |

Per isotope: element, ingestion DCF per age group, inhalation DCF per age group, external DCF, skin β DCF, skin γ DCF.

28 chemical elements have soil-plant transfer factors and Kd values in [`data/elements.json`](data/elements.json), driving the produce pathway.

---

## 5. Data reference

All data lives in top-level `data/*.json`. Each file is loaded at startup and validated by the pydantic models in `src/rclea_core/models.py`.

### `data/isotopes.json`

```json
{
  "source": "…",
  "radon": {
    "rn222_inhalation_Sv_per_h_per_Bq_per_m3": 9e-09,
    "rn222_equilibrium_factor": 0.4,
    "rn222_decay_constant_per_s": 2.1e-06,
    "default_rn222_conversion_Bq_m3_per_Bq_kg": 3.0
  },
  "isotopes": [
    {
      "id": "Cs-137",
      "name": "Cs-137",
      "element": "Cs",
      "ingestion_Sv_per_Bq": { "infant": 1.2e-08, "child": 1.0e-08, "adult": 1.3e-08 },
      "inhalation_Sv_per_Bq": { "infant": 5.4e-09, "child": 3.7e-09, "adult": 4.6e-09 },
      "external_Sv_per_y_per_Bq_per_m3": 6.1e-10,
      "skin_beta_Sv_per_y_per_Bq_per_cm2": 0.022,
      "skin_gamma_Sv_per_y_per_Bq_per_cm2": 0.00029
    }
  ]
}
```

### `data/elements.json`

Element-level soil chemistry + site-wide soil properties for the radon model:

```json
{
  "soil_global": {
    "enrichment_factor": 3.0,
    "water_filled_porosity": 0.25,
    "total_porosity": 0.5,
    "bulk_density_kg_per_m3": 1400.0,
    "rn222_emanation_fraction": 0.2,
    "rn222_effective_diffusion_m2_per_s": 2e-06
  },
  "elements": [
    { "id": "Cs", "kd_m3_per_kg": 1.0, "plant_uptake_affinity": 5.0, "soil_to_plant_cf_fw_per_dw": 0.004 }
  ]
}
```

### `data/scenarios.json`

Land-use scenarios with per-age exposure parameters. See §3.2.

### `data/receptors.json`

Body weight and respiration by sex and age; UV skin fraction and tissue weighting factor.

### `data/buildings.json`

```json
{
  "buildings": [
    {
      "id": "Timber",
      "shielding_factor": 0.0,
      "rn222_height_m": 3.0,
      "rn222_ventilation_rate_per_s": 8.33e-05
    },
    {
      "id": "Concrete_Brick",
      "label": "Concrete/Brick",
      "shielding_factor": 0.9,
      "rn222_height_m": 3.0,
      "rn222_ventilation_rate_per_s": 8.33e-05
    }
  ]
}
```

### `data/consumption.json`

Per-age consumption rates (kg fresh weight / kg body weight / y) for 6 crops, plus crop-level `home_fraction` and `soil_loading_kg_dw_per_kg_fw`.

### `data/pathways.json`

Human-readable metadata for the six pathways.

### `data/constants.json`

```json
{
  "effective_dose_criterion_mSv_per_y": 3.0,
  "equivalent_skin_dose_criterion_mSv_per_y": 50.0,
  "hours_per_year": 8760.0,
  "Sv_per_mSv": 0.001,
  "default_fraction_land_contaminated": 1.0,
  "rho_B_soil_bulk_density_kg_per_m3": 1400.0,
  "uv_tissue_weighting_factor": 0.01,
  "dust_loading_kg_per_m3": 5e-08
}
```

### `data/_raw_dump.json`

Full cell-by-cell dump of the original workbook for audit purposes. Not read by the engine.

---

## 6. The Python CLI (`rclea`)

### 6.1 Installation

```bash
pip install -e .[cli]
rclea --help
```

Python ≥ 3.11. Dependencies: `pydantic`, `pyyaml`, `typer`, `rich`.

Or invoke directly without installing:

```bash
PYTHONPATH=src python -m rclea_cli.main --help
```

### 6.2 Disclaimer banner

Every command prints a yellow disclaimer panel before output. Suppress with `--quiet`/`-q` (useful for scripting).

### 6.3 Top-level commands

| Command | Purpose |
|---|---|
| `rclea assess` | Run a single dose assessment. |
| `rclea worst-case` | Enumerate every receptor combination; report the max. |
| `rclea rsgv` | Compute per-isotope Radioactivity in Soil Guideline Values. |
| `rclea isotopes` | Browse the radionuclide catalogue. |
| `rclea scenarios` | Browse + customise land-use scenarios. |
| `rclea tutorial` | Walk an interactive tutorial in the terminal. |

### 6.4 `rclea assess`

| Flag | Type | Default | Description |
|---|---|---|---|
| `--input`, `-i` | PATH | — | YAML file describing the scenario input (§6.9). |
| `--output`, `-o` | PATH | — | Write the full `AssessmentResult` as JSON. |
| `--example` | TEXT | — | Run a built-in example. Known: `appendix-d`. |
| `--iso` | TEXT | — | Inline `ID=VALUE`, repeatable. |
| `--mode` | generic \| site_specific | `site_specific` | Generic finds the worst receptor automatically. |
| `--scenario` | TEXT | `Residential_with_Home_Grown_Produce` | Scenario id. |
| `--age` | infant \| child \| adult | `adult` | |
| `--sex` | male \| female | `male` | |
| `--building` | TEXT | `Timber` | |
| `--fraction` | FLOAT | `1.0` | Fraction of land contaminated (0–1). |
| `--radon-mode` | default \| measured \| site_specific | `default` | See §3.6. |
| `--radon-measured` | FLOAT | — | Bq/m³ for `--radon-mode measured`. |
| `--override` | KEY=VALUE | — | Repeatable. See §3.9. |

Examples:

```bash
# Inline, default adult
rclea assess --iso Cs-137=1000 --iso Sr-90=200

# Generic mode: find worst receptor
rclea assess --iso Ra-226=2500 --mode generic

# Site-specific radon with measured value
rclea assess --iso Ra-226=2500 --radon-mode measured --radon-measured 120

# Site-specific K + heavier shielding override
rclea assess --iso Ra-226=2500 --radon-mode site_specific --override shielding_factor=0.5

# YAML input, JSON output
rclea assess -i my.yaml -o report.json

# Built-in CLR-13 example
rclea assess --example appendix-d
```

`rclea assess template PATH` writes a YAML template you can edit and re-run.

### 6.5 `rclea worst-case`

Enumerate all 40 combinations and report the worst.

```bash
rclea worst-case --iso Ra-226=1000
rclea worst-case --iso Ra-226=1000 --full-table       # show all 40 rows
rclea worst-case --iso Ra-226=1000 --radon-mode site_specific
```

Flags: `--iso`, `--fraction`, `--radon-mode`, `--radon-measured`, `--override`, `--full-table`.

### 6.6 `rclea rsgv`

Compute per-isotope RSGVs for the given scenario/receptor.

```bash
rclea rsgv --scenario Residential_with_Home_Grown_Produce --age infant
rclea rsgv --age infant --site-iso Ra-226=50 --site-iso Cs-137=500     # with site comparison
rclea rsgv --age infant --format csv > rsgv.csv
rclea rsgv --age infant --format json | jq '.report.rsgvs_Bq_per_kg["Ra-226"]'
```

Flags: `--scenario`, `--age`, `--sex`, `--building`, `--radon-mode`, `--override`, `--site-iso` (repeatable), `--format {table,csv,json}`.

### 6.7 `rclea isotopes` and `rclea scenarios`

```bash
rclea isotopes list
rclea isotopes show Cs-137

rclea scenarios list                                  # shipped + custom
rclea scenarios show Allotments
rclea scenarios template custom.json --base Residential_with_Home_Grown_Produce
rclea scenarios register custom.json                  # → ~/.rclea/scenarios.json
rclea scenarios unregister custom_xyz
```

### 6.8 `rclea tutorial`

```bash
rclea tutorial list
rclea tutorial run 01-contaminated-land
rclea tutorial run 07-advanced-workflows --auto          # run every embedded step without prompting
rclea tutorial run 03-exposure-pathways --no-interactive # prose only
```

When a tutorial contains `rclea-run` fences, the runner walks the Markdown, pauses at each fence to prompt "Run this step?", and on yes executes the real engine inline (including `radon_mode`, `measured_rn222_Bq_per_m3`, and `overrides` from the fence body).

### 6.9 YAML scenario file format

```yaml
soil_concentrations_Bq_per_kg:
  Cs-137: 500.0
  Ra-226: 100.0
scenario_id: Residential_with_Home_Grown_Produce
age: adult                         # infant | child | adult
sex: male                          # male | female
building_id: Timber                # Timber | Concrete_Brick
fraction_land_contaminated: 1.0
radon_mode: default                # default | measured | site_specific
measured_rn222_Bq_per_m3: null     # Bq/m³, only used with radon_mode: measured
overrides:                         # hierarchical keys per §3.9
  dust_loading_kg_per_m3: 1e-7
  soil_ingestion_kg_per_y.adult: 0.05
```

---

## 7. The web application (`webRCLEA`)

### 7.1 Quickstart

```bash
cd web
npm install
npm run dev                 # dev server at http://localhost:5173
# or
npm run build               # static bundle in web/dist/
```

Node ≥ 18. First browser visit downloads Pyodide (~8 MB) from the jsDelivr CDN; subsequent visits are cached.

### 7.2 Five tabs

- **Assess** — the main form + results panel + optional worst-case panel (Generic mode).
- **Guidelines** — per-isotope RSGVs as a scenario-dependent table with CSV export.
- **Custom** — clone a scenario, edit per-age parameters, save to `localStorage`.
- **Tutorials** — the 7-module curriculum with inline interactive steps.
- **Glossary** — radiation + regulatory terms, cross-linked with tooltips.

### 7.3 Assessment form features

- **Calculation mode radio** at the top: Site-specific (classic) or Generic (auto-find worst).
- **Isotope picker** with search by id or element symbol.
- **Soil concentration inputs** with per-isotope Bq/kg fields.
- **Scenario / Age / Sex / Building dropdowns** (the last three disable in Generic mode).
- **Fraction slider** for patchy contamination.
- **Advanced disclosure** that reveals:
  - **Radon-mode control** — radio with three options + conditional Bq/m³ input for `measured`.
  - **Overrides editor** — quick-entry for common keys + free-form custom keys.
- **Run button** (reads "Find worst case" in Generic mode).

### 7.4 Results panel features

- **Total effective dose** with red/green threshold bar vs 3 mSv/y criterion.
- **Safety margin** single-number summary.
- **Skin equivalent dose** vs 50 mSv/y criterion.
- **Per-pathway breakdown** with expandable per-isotope contributions.
- **Notes pane** (including override summary and radon-mode warnings).

### 7.5 Disclaimer surfaces

- First-run modal (must acknowledge to proceed; localStorage flag `rclea:disclaimer:acknowledged:v1`).
- Sticky yellow banner on every page.
- Footer on every page.
- Every tutorial's first page.
- Every exported JSON report (`AssessmentResult.disclaimer`).

### 7.6 Hover guidance

Every form input has a Radix-UI-based tooltip (hover-, click-, keyboard-accessible) explaining what the field means, its unit, its typical range, and its source. The glossary tab mirrors this in long form.

### 7.7 How it runs Python in the browser

Vite serves the top-level `src/rclea_core/*.py`, `data/*.json`, and `tutorials/*.md` at well-known URLs plus manifest files. On page load, [`web/src/pyodide/loader.ts`](web/src/pyodide/loader.ts):

1. Downloads the Pyodide runtime from the jsDelivr CDN.
2. Installs `pydantic` and `pyyaml` via `micropip`.
3. Fetches each manifest and file; writes them into Pyodide's virtual filesystem.
4. Prepends `/home/pyodide` to `sys.path` so `import rclea_core` finds the package.
5. Calls `load_dataset()` to prime the pydantic-validated data cache. If custom scenarios are saved in `localStorage`, they are merged into the Pyodide dataset on every reload.

---

## 8. Tutorials

Seven Markdown lessons in `tutorials/`, shared between CLI and web. Each opens with the educational disclaimer.

| # | Slug | Title | Interactive steps |
|---|---|---|---|
| 1 | `01-contaminated-land` | Contaminated Land and the Part 2A Regime | 0 |
| 2 | `02-radiation-basics` | Radiation Basics | 2 |
| 3 | `03-exposure-pathways` | Exposure Pathways | 3 |
| 4 | `04-first-assessment` | Your First Assessment | 2 |
| 5 | `05-interpreting-results` | Interpreting Results | 1 |
| 6 | `06-legislation-stakeholders` | Legislation and Stakeholders | 0 |
| 7 | `07-advanced-workflows` | Advanced Workflows | 3 |

**Lesson 7** covers generic mode / worst-case analysis, the three radon modes (with a side-by-side numeric comparison), per-isotope RSGVs, custom scenarios, and per-parameter overrides.

### 8.1 Interactive step format — `rclea-run` fences

Tutorials embed live assessments using YAML-bodied code fences:

````markdown
```rclea-run
title: Ra-226 site, site-specific K
soil_concentrations_Bq_per_kg:
  Ra-226: 2500
scenario_id: Residential_with_Home_Grown_Produce
age: infant
building_id: Timber
radon_mode: site_specific
measured_rn222_Bq_per_m3: null
overrides:
  rn222_emanation_fraction: 0.15
question: "Why is this dose lower than default K=3?"
try_changing: "Switch to radon_mode: measured and compare."
```
````

Supported keys (mirror `AssessmentInput`): `soil_concentrations_Bq_per_kg` (required), `scenario_id` (required), `age`, `sex`, `building_id`, `fraction_land_contaminated`, `radon_mode`, `measured_rn222_Bq_per_m3`, `overrides`. Plus presentational: `title`, `question`, `try_changing`.

**Web rendering:** the code block is replaced by an editable, runnable widget that calls the real engine via Pyodide. Reset restores the preset.

**CLI rendering:** `rclea tutorial run` walks the Markdown, prompts "Run this step?", executes each step, and prints a Rich pathway table.

### 8.2 Authoring a new tutorial

Drop `tutorials/08-my-lesson.md`. Start with `# 8: My Lesson Title` on the first line (used for the sidebar title). Embed interactive steps with `rclea-run` fences. The web sidebar and CLI `tutorial list` both pick it up automatically. Run `pytest tests/python/test_tutorial_fences.py` to confirm every embedded step parses and executes.

---

## 9. Extending the tool

### 9.1 Add a new radionuclide

Append to [`data/isotopes.json`](data/isotopes.json). Ingestion + inhalation DCFs must include all three age keys. For the produce pathway to contribute, the element must also appear in [`data/elements.json`](data/elements.json).

### 9.2 Add a new land-use scenario

Either edit `data/scenarios.json` directly (ships with the tool) or use the **custom scenario** mechanism (§3.10) for site-specific tweaks that don't deserve to be shipped.

### 9.3 Add a building type

Append to [`data/buildings.json`](data/buildings.json) with shielding factor, radon height, and ventilation rate.

### 9.4 Add a crop

Edit [`data/consumption.json`](data/consumption.json): add `by_age.<age>.<crop>` entries and a `crop_meta.<crop>` record.

### 9.5 Add a glossary term (web only)

Edit `web/src/lib/glossary.ts`.

### 9.6 Add a new pathway (rare — requires code)

Implement a new function in `src/rclea_core/pathways.py`, register it in `PATHWAY_FUNCTIONS`, add metadata to `data/pathways.json`, add a boolean flag to `ScenarioPathwayFlags`, and add a pathway test.

---

## 10. Architecture

### 10.1 Shared-engine principle

There is **exactly one** implementation of the dose mathematics. The web app does not re-implement it in TypeScript. It loads the same Python source into the browser via Pyodide and calls into it, so CLI output and web output are numerically identical to within floating-point noise.

```
                 ┌──────────────────────────┐
                 │  data/*.json (JSON)      │
                 │  tutorials/*.md          │
                 └─────────────┬────────────┘
                               │ loaded once per process
        ┌──────────────────────┴──────────────────────┐
        ▼                                             ▼
┌─────────────────────┐                ┌──────────────────────────┐
│  src/rclea_core/    │                │  SAME files, mounted     │
│  Python engine      │                │  into Pyodide FS         │
│  (run_assessment,   │                │                          │
│   find_worst_case,  │                │                          │
│   compute_rsgvs)    │                │                          │
└───────────┬─────────┘                └────────────┬─────────────┘
            │                                       │
┌───────────▼─────────┐                ┌────────────▼─────────────┐
│   rclea_cli         │                │   webRCLEA (React shell) │
│   typer + rich      │                │   renders UI; Python     │
│                     │                │   runs the math          │
└─────────────────────┘                └──────────────────────────┘
```

### 10.2 Repository layout

```
rclea/
├── README.md                ← this file
├── DISCLAIMER.md
├── LICENSE
├── pyproject.toml
│
├── data/                    source-of-truth JSON
│   ├── isotopes.json           (48 radionuclides + Rn-222 params)
│   ├── elements.json           (28 elements + soil_global)
│   ├── scenarios.json          (4 shipped scenarios)
│   ├── receptors.json          (body weight + respiration)
│   ├── buildings.json          (shielding + per-building radon params)
│   ├── consumption.json        (6 crops, per-age rates)
│   ├── pathways.json           (pathway metadata)
│   ├── constants.json          (thresholds + physical constants)
│   └── _raw_dump.json          (audit dump of original workbook)
│
├── tutorials/               shared Markdown, 7 lessons
│   ├── 01-contaminated-land.md
│   ├── 02-radiation-basics.md
│   ├── 03-exposure-pathways.md
│   ├── 04-first-assessment.md
│   ├── 05-interpreting-results.md
│   ├── 06-legislation-stakeholders.md
│   └── 07-advanced-workflows.md
│
├── extraction/              one-time scripts that populated data/ from the .xls
│
├── src/
│   ├── rclea_core/
│   │   ├── models.py           pydantic: AssessmentInput, RadonMode, WorstCaseReport, RSGVReport, …
│   │   ├── loader.py           loads data/*.json; merges user overlay
│   │   ├── pathways.py         the six dose functions + _site_specific_K
│   │   ├── assessment.py       run_assessment() + safety_margin
│   │   ├── analysis.py         find_worst_case() + compute_rsgvs()
│   │   ├── tutorials.py        tutorial discovery
│   │   └── disclaimer.py       canonical disclaimer string
│   │
│   └── rclea_cli/
│       ├── main.py             `rclea` entry point + disclaimer banner
│       ├── commands/
│       │   ├── _shared.py      --iso, --override parsers
│       │   ├── assess.py       `rclea assess` + template
│       │   ├── isotopes.py
│       │   ├── scenarios.py    list/show/template/register/unregister
│       │   ├── tutorial.py
│       │   ├── worst_case.py
│       │   └── rsgv.py
│       └── templates/
│
├── web/                     React + Vite + Tailwind + Pyodide SPA
│   ├── vite.config.ts       plugin serves /rclea_core/*, /rclea_data/*, /rclea_tutorials/*
│   ├── src/
│   │   ├── App.tsx             5 tabs
│   │   ├── pyodide/
│   │   │   ├── loader.ts       boots Pyodide, mounts the package
│   │   │   └── api.ts          typed wrappers (loadCatalogue, assess, findWorstCase, computeRsgvs)
│   │   ├── components/
│   │   │   ├── DisclaimerBanner.tsx
│   │   │   ├── DisclaimerModal.tsx
│   │   │   ├── InfoTooltip.tsx
│   │   │   ├── AssessmentForm.tsx        mode radio + Advanced disclosure
│   │   │   ├── RadonModeControl.tsx
│   │   │   ├── OverridesEditor.tsx
│   │   │   ├── ResultsPanel.tsx          + safety margin display
│   │   │   ├── WorstCasePanel.tsx
│   │   │   ├── GuidelinesPanel.tsx
│   │   │   ├── CustomScenarioPanel.tsx
│   │   │   ├── TutorialView.tsx
│   │   │   ├── InteractiveStep.tsx       supports radon_mode + overrides
│   │   │   └── GlossaryPanel.tsx
│   │   └── lib/
│   │       └── glossary.ts
│   │
├── tests/python/
│   ├── conftest.py
│   ├── test_loader.py
│   ├── test_pathways.py
│   ├── test_radon_modes.py             three-mode + reverse-engineered K
│   ├── test_overrides.py               parameter-override mechanism
│   ├── test_analysis.py                worst-case + RSGV round-trip
│   ├── test_extensibility.py
│   └── test_tutorial_fences.py
```

### 10.3 Disclaimer surfaces (six)

1. CLI banner (suppressible with `--quiet`).
2. Web first-run modal.
3. Web sticky banner.
4. Web footer.
5. Exported reports (JSON).
6. Every tutorial's first page.

---

## 11. Development and testing

### 11.1 Python — run the test suite

```bash
PYTHONPATH=src python -m pytest tests/python -v
```

**48 tests** across seven files:

| File | What it covers |
|---|---|
| `test_loader.py` | Dataset loads, ≥47 isotopes, Cs-137 / Ra-226 / Pu-239 present, criteria 3.0 / 50.0 mSv/y. |
| `test_pathways.py` | Per-pathway unit tests: zero at zero input, linear in concentration, fraction scaling, shielding reduces external only, infant ingestion > adult, radon-Ra-226 coupling, unknown-isotope graceful handling. |
| `test_radon_modes.py` | Default mode reproduces baseline; measured mode bypasses K; site-specific K matches workbook `K_calc` to <1 %; building ventilation override halves K; measured-mode missing value warns; zero-Ra-226 returns zero. |
| `test_overrides.py` | Dust-loading override scales inhalation linearly; per-age override is scoped; shielding override affects external; notes record overrides; unknown keys are silently ignored. |
| `test_analysis.py` | Worst-case returns 40 rows sorted descending; Ra-226 worst is residential infant timber; site-specific radon mode lowers worst dose; RSGV round-trip (running RSGV back through assess reproduces the criterion); RSGV monotonicity under K ratio; all 48 isotopes have an RSGV. |
| `test_extensibility.py` | Injecting a fictitious isotope in-memory makes it visible to assessments. |
| `test_tutorial_fences.py` | Every tutorial parses; every `rclea-run` fence runs the engine to a finite dose. |

### 11.2 Type-check and lint

```bash
ruff check .
mypy --strict src
```

### 11.3 Web — install, type-check, build

```bash
cd web
npm install
npx tsc --noEmit
npm run build               # ~164 kB gzipped
```

### 11.4 One-time data extraction

If the underlying workbook changes, regenerate the JSON data files:

```bash
python extraction/build_data.py
```

---

## 12. Deployment

### 12.1 Web — static hosting

`npm run build` produces a self-contained `web/dist/` directory (~164 kB gzipped app + ~8 MB Pyodide CDN download on first visit). Deploy to any static host: GitHub Pages, Netlify, Cloudflare Pages, S3 + CloudFront. No server-side code runs.

### 12.2 CLI — publish to PyPI

```bash
python -m build
python -m twine upload dist/*
```

---

## 13. References

**Primary materials**: RCLEA software workbook, UKHSA CRCE-RAD-003-2020, Environment Agency CLR-13, Part 2A Statutory Guidance (2018).

**Legislation**: Environmental Protection Act 1990 Part 2A (as amended); Radioactive Contaminated Land (Enabling Powers) (England) Regulations 2005/2010/2018; Council Directive 2013/59/Euratom.

**Dose coefficients**: ICRP Publication 72 (age-specific intake DCFs); ICRP Publication 119 (compendium).

**Radon exhalation model**: Nazaroff (1992, *Rev. Geophys.* 30 137); Porstendörfer (1994, *J. Aerosol Sci.* 25 219). 1-D semi-infinite source formulation used here.

**Adjacent frameworks**: IRR17 (worker exposure, separate from Part 2A); EPR 2016 (radioactive substances regulation).

---

## 14. Licence

MIT with an added educational-use clause disclaiming liability. Full text: [`LICENSE`](LICENSE). MIT obligations (preserve the copyright notice in source redistribution) apply; for outputs, the full disclaimer text travels with every exported report automatically.

---

*This is an educational re-implementation. It is not affiliated with the UK Environment Agency or UKHSA. When in doubt, read the real guidance and consult a Radiation Protection Adviser.*
