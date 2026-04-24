// Typed API facade for the Python engine. Every exported function is safe to
// call from React components: it awaits Pyodide, runs the Python code, and
// returns plain JSON objects.

import { getPyodide } from "./loader";

export type RadonMode = "default" | "measured" | "site_specific";
export type AgeGroup = "infant" | "child" | "adult";
export type Sex = "male" | "female";
export type AssessmentMode = "generic" | "site_specific";

export interface Isotope {
  id: string;
  name: string;
  element: string;
  ingestion_Sv_per_Bq: Record<string, number>;
  inhalation_Sv_per_Bq: Record<string, number>;
  external_Sv_per_y_per_Bq_per_m3: number;
  skin_beta_Sv_per_y_per_Bq_per_cm2: number;
  skin_gamma_Sv_per_y_per_Bq_per_cm2: number;
}

export interface Scenario {
  id: string;
  label: string;
  area_hectares: number;
  pathways: Record<string, boolean>;
  per_age: Record<string, Record<string, number>>;
}

export interface Building {
  id: string;
  label?: string | null;
  shielding_factor: number;
  rn222_height_m: number;
  rn222_ventilation_rate_per_s: number;
}

export interface PathwayResult {
  pathway: string;
  label: string;
  dose_mSv_per_year: number;
  contributing_isotopes: Record<string, number>;
}

export interface AssessmentResult {
  total_effective_dose_mSv_per_y: number;
  total_skin_equivalent_dose_mSv_per_y: number;
  effective_dose_criterion_mSv_per_y: number;
  skin_dose_criterion_mSv_per_y: number;
  exceeds_effective_criterion: boolean;
  exceeds_skin_criterion: boolean;
  safety_margin: number | null;
  per_pathway: PathwayResult[];
  inputs_echo: AssessmentInput;
  notes: string[];
  disclaimer: string;
}

export interface AssessmentInput {
  soil_concentrations_Bq_per_kg: Record<string, number>;
  scenario_id: string;
  age: AgeGroup;
  sex: Sex;
  building_id: string;
  fraction_land_contaminated: number;
  radon_mode?: RadonMode;
  measured_rn222_Bq_per_m3?: number | null;
  overrides?: Record<string, number>;
}

export interface WorstCaseEntry {
  scenario_id: string;
  scenario_label: string;
  building_id: string;
  age: AgeGroup;
  sex: Sex;
  total_effective_dose_mSv_per_y: number;
  exceeds_effective_criterion: boolean;
}

export interface WorstCaseReport {
  soil_concentrations_Bq_per_kg: Record<string, number>;
  fraction_land_contaminated: number;
  radon_mode: RadonMode;
  measured_rn222_Bq_per_m3: number | null;
  effective_dose_criterion_mSv_per_y: number;
  entries: WorstCaseEntry[];
  worst: WorstCaseEntry;
  disclaimer: string;
}

export interface RSGVReport {
  scenario_id: string;
  scenario_label: string;
  age: AgeGroup;
  sex: Sex;
  building_id: string;
  radon_mode: RadonMode;
  effective_dose_criterion_mSv_per_y: number;
  rsgvs_Bq_per_kg: Record<string, number>;
  disclaimer: string;
}

export interface Catalogue {
  isotopes: Isotope[];
  scenarios: Scenario[];
  buildings: Building[];
}

/**
 * Inject any user-saved custom scenarios (from localStorage) into the Python
 * dataset, then load the catalogue. Called at app boot and again whenever the
 * user saves/deletes a custom scenario.
 */
export async function loadCatalogue(): Promise<Catalogue> {
  const py = await getPyodide();
  const customScenarios = loadCustomScenariosFromLocalStorage();
  py.globals.set("js_custom_scenarios_json", JSON.stringify(customScenarios));
  const result = py.runPython(`
import json
from rclea_core.loader import reload_dataset
from rclea_core.models import Scenario

# Clear the cached dataset so our custom scenarios re-apply on each boot
ds = reload_dataset()
custom = json.loads(js_custom_scenarios_json)
for entry in custom:
    s = Scenario.model_validate(entry)
    ds.scenarios[s.id] = s

json.dumps({
    "isotopes": [i.model_dump() for i in ds.isotopes.values()],
    "scenarios": [
        {
            "id": s.id,
            "label": s.label,
            "area_hectares": s.area_hectares,
            "pathways": s.pathways.model_dump(),
            "per_age": {age: params.model_dump() for age, params in s.per_age.items()},
        }
        for s in ds.scenarios.values()
    ],
    "buildings": [b.model_dump() for b in ds.buildings.values()],
})
`) as string;
  return JSON.parse(result);
}

export async function assess(input: AssessmentInput): Promise<AssessmentResult> {
  const py = await getPyodide();
  py.globals.set("js_input_json", JSON.stringify(input));
  const result = py.runPython(`
import json
from rclea_core import AssessmentInput, run_assessment
inp = AssessmentInput.model_validate_json(js_input_json)
result = run_assessment(inp)
result.model_dump_json()
`) as string;
  return JSON.parse(result);
}

export async function findWorstCase(args: {
  soil_concentrations_Bq_per_kg: Record<string, number>;
  fraction_land_contaminated?: number;
  radon_mode?: RadonMode;
  measured_rn222_Bq_per_m3?: number | null;
  overrides?: Record<string, number>;
}): Promise<WorstCaseReport> {
  const py = await getPyodide();
  py.globals.set("js_wc_args", JSON.stringify(args));
  const result = py.runPython(`
import json
from rclea_core import find_worst_case, RadonMode
args = json.loads(js_wc_args)
rep = find_worst_case(
    soil_concentrations_Bq_per_kg=args.get("soil_concentrations_Bq_per_kg", {}),
    fraction_land_contaminated=args.get("fraction_land_contaminated", 1.0),
    radon_mode=RadonMode(args.get("radon_mode", "default")),
    measured_rn222_Bq_per_m3=args.get("measured_rn222_Bq_per_m3"),
    overrides=args.get("overrides") or {},
)
rep.model_dump_json()
`) as string;
  return JSON.parse(result);
}

export async function computeRsgvs(args: {
  scenario_id: string;
  age?: AgeGroup;
  sex?: Sex;
  building_id?: string;
  radon_mode?: RadonMode;
  overrides?: Record<string, number>;
}): Promise<RSGVReport> {
  const py = await getPyodide();
  py.globals.set("js_rsgv_args", JSON.stringify(args));
  const result = py.runPython(`
import json
from rclea_core import compute_rsgvs, AgeGroup, Sex, RadonMode
args = json.loads(js_rsgv_args)
rep = compute_rsgvs(
    scenario_id=args["scenario_id"],
    age=AgeGroup(args.get("age", "adult")),
    sex=Sex(args.get("sex", "male")),
    building_id=args.get("building_id", "Timber"),
    radon_mode=RadonMode(args.get("radon_mode", "default")),
    overrides=args.get("overrides") or {},
)
rep.model_dump_json()
`) as string;
  return JSON.parse(result);
}

export interface Tutorial {
  slug: string;
  title: string;
  markdown: string;
}

export async function listTutorials(): Promise<Tutorial[]> {
  const py = await getPyodide();
  const result = py.runPython(`
import json
from rclea_core.tutorials import list_tutorials
json.dumps([{"slug": t.slug, "title": t.title, "markdown": t.markdown} for t in list_tutorials()])
`) as string;
  return JSON.parse(result);
}

export async function getDisclaimer(): Promise<{ full: string; short: string }> {
  const py = await getPyodide();
  const result = py.runPython(`
import json
from rclea_core import DISCLAIMER_FULL, DISCLAIMER_SHORT
json.dumps({"full": DISCLAIMER_FULL, "short": DISCLAIMER_SHORT})
`) as string;
  return JSON.parse(result);
}

// ---------------------------------------------------------------------------
// Custom scenarios — client-side persistence via localStorage
// ---------------------------------------------------------------------------

const CUSTOM_SCENARIOS_KEY = "rclea:customScenarios:v1";

export function loadCustomScenariosFromLocalStorage(): unknown[] {
  try {
    const raw = localStorage.getItem(CUSTOM_SCENARIOS_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function saveCustomScenariosToLocalStorage(scenarios: unknown[]): void {
  localStorage.setItem(CUSTOM_SCENARIOS_KEY, JSON.stringify(scenarios));
}
