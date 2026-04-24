import { useMemo, useState } from "react";
import type {
  AssessmentInput,
  AssessmentMode,
  Catalogue,
  Isotope,
  RadonMode,
} from "../pyodide/api";
import { InfoTooltip } from "./InfoTooltip";
import { OverridesEditor } from "./OverridesEditor";
import { RadonModeControl } from "./RadonModeControl";

interface Props {
  catalogue: Catalogue;
  onSubmit: (input: AssessmentInput, mode: AssessmentMode) => void;
  onChange?: (state: FormState) => void;
  running: boolean;
}

export interface FormState {
  soil: Record<string, number>;
  scenarioId: string;
  buildingId: string;
  age: "infant" | "child" | "adult";
  sex: "male" | "female";
  fraction: number;
  mode: AssessmentMode;
  radonMode: RadonMode;
  measuredRn: number | null;
  overrides: Record<string, number>;
}

export function AssessmentForm({ catalogue, onSubmit, onChange, running }: Props) {
  const [scenarioId, setScenarioId] = useState(catalogue.scenarios[0]?.id ?? "");
  const [buildingId, setBuildingId] = useState(catalogue.buildings[0]?.id ?? "Timber");
  const [age, setAge] = useState<"infant" | "child" | "adult">("adult");
  const [sex, setSex] = useState<"male" | "female">("male");
  const [fraction, setFraction] = useState(1.0);
  const [soil, setSoil] = useState<Record<string, string>>({
    "Cs-137": "500",
    "Ra-226": "100",
  });
  const [search, setSearch] = useState("");
  const [mode, setMode] = useState<AssessmentMode>("site_specific");
  const [radonMode, setRadonMode] = useState<RadonMode>("default");
  const [measuredRn, setMeasuredRn] = useState<number | null>(null);
  const [overrides, setOverrides] = useState<Record<string, number>>({});
  const [showAdvanced, setShowAdvanced] = useState(false);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return catalogue.isotopes;
    return catalogue.isotopes.filter(
      (i) => i.id.toLowerCase().includes(q) || i.element.toLowerCase() === q,
    );
  }, [catalogue.isotopes, search]);

  const cleanedSoil = (): Record<string, number> => {
    const out: Record<string, number> = {};
    for (const [k, v] of Object.entries(soil)) {
      const n = Number(v);
      if (!Number.isNaN(n) && n > 0) out[k] = n;
    }
    return out;
  };

  // Broadcast state upwards so the worst-case panel / guidelines can react
  const broadcast = () => {
    onChange?.({
      soil: cleanedSoil(),
      scenarioId,
      buildingId,
      age,
      sex,
      fraction,
      mode,
      radonMode,
      measuredRn,
      overrides,
    });
  };

  const addIsotope = (id: string) => {
    if (!(id in soil)) {
      const next = { ...soil, [id]: "0" };
      setSoil(next);
    }
  };
  const removeIsotope = (id: string) => {
    const next = { ...soil };
    delete next[id];
    setSoil(next);
  };
  const setConc = (id: string, value: string) => setSoil({ ...soil, [id]: value });

  const submit = () => {
    onSubmit(
      {
        soil_concentrations_Bq_per_kg: cleanedSoil(),
        scenario_id: scenarioId,
        age,
        sex,
        building_id: buildingId,
        fraction_land_contaminated: fraction,
        radon_mode: radonMode,
        measured_rn222_Bq_per_m3: measuredRn,
        overrides,
      },
      mode,
    );
    broadcast();
  };

  const genericDisabled = mode === "generic";

  return (
    <div className="space-y-6" onBlur={broadcast}>
      {/* Mode selector — at the very top */}
      <section className="rounded border border-slate-200 bg-white p-4">
        <div className="flex items-center gap-2">
          <h3 className="!my-0">Calculation mode</h3>
          <InfoTooltip
            content={
              <span>
                <strong>Site-specific:</strong> uses your chosen scenario/age/sex/building. <br />
                <strong>Generic:</strong> runs every valid (scenario × building × age × sex) combination and shows the worst — ~3 seconds. Ideal for initial screening.
              </span>
            }
          />
        </div>
        <div className="mt-2 flex gap-4 text-sm">
          <label className="flex cursor-pointer items-center gap-2">
            <input
              type="radio"
              checked={mode === "site_specific"}
              onChange={() => setMode("site_specific")}
            />
            Site-specific
          </label>
          <label className="flex cursor-pointer items-center gap-2">
            <input
              type="radio"
              checked={mode === "generic"}
              onChange={() => setMode("generic")}
            />
            Generic (find worst case)
          </label>
        </div>
        {genericDisabled && (
          <p className="mt-2 text-xs text-slate-500">
            In generic mode the Age / Sex / Building dropdowns are disabled — the engine finds
            the worst combination for you.
          </p>
        )}
      </section>

      <section className="rounded border border-slate-200 bg-white p-4">
        <h3 className="flex items-center gap-2">
          Soil activity concentrations (Bq/kg dry weight)
          <InfoTooltip content="Enter the measured or estimated activity concentration for each radionuclide present in the soil, in becquerels per kilogram dry mass. Only positive values are used." />
        </h3>
        <div className="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-2">
          {Object.keys(soil).map((id) => (
            <div key={id} className="flex items-center gap-2">
              <label className="w-20 font-mono text-sm">{id}</label>
              <input
                type="number"
                min="0"
                step="any"
                value={soil[id]}
                onChange={(e) => setConc(id, e.target.value)}
                className="w-32 rounded border border-slate-300 px-2 py-1"
                aria-label={`${id} concentration Bq/kg`}
              />
              <span className="text-xs text-slate-500">Bq/kg</span>
              <button
                type="button"
                onClick={() => removeIsotope(id)}
                className="ml-auto text-sm text-red-600 hover:underline"
                aria-label={`Remove ${id}`}
              >
                ×
              </button>
            </div>
          ))}
        </div>

        <div className="mt-4 rounded border border-slate-200 p-3">
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium">Add radionuclide</label>
            <InfoTooltip content="Search by isotope id (e.g. 'Cs-137') or by element symbol (e.g. 'Pu' to show all plutonium isotopes)." />
            <input
              type="text"
              placeholder="Search…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="ml-2 flex-1 rounded border border-slate-300 px-2 py-1 text-sm"
            />
          </div>
          <div className="mt-2 flex max-h-32 flex-wrap gap-1 overflow-y-auto">
            {filtered.map((iso: Isotope) => (
              <button
                key={iso.id}
                type="button"
                onClick={() => addIsotope(iso.id)}
                disabled={iso.id in soil}
                className="rounded border border-slate-300 bg-white px-2 py-0.5 text-xs hover:bg-rclea-50 disabled:opacity-40"
              >
                {iso.id}
              </button>
            ))}
          </div>
        </div>
      </section>

      <section className="grid grid-cols-1 gap-4 rounded border border-slate-200 bg-white p-4 md:grid-cols-2">
        <div>
          <label className="flex items-center gap-2 text-sm font-medium">
            Land-use scenario
            <InfoTooltip content="Custom scenarios you've saved on the 'Custom' tab appear here automatically." />
          </label>
          <select
            value={scenarioId}
            onChange={(e) => setScenarioId(e.target.value)}
            className="mt-1 w-full rounded border border-slate-300 px-2 py-1.5"
          >
            {catalogue.scenarios.map((s) => (
              <option key={s.id} value={s.id}>
                {s.label}
                {s.id.startsWith("custom_") ? "  (custom)" : ""}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="flex items-center gap-2 text-sm font-medium">
            Receptor age
            <InfoTooltip content="ICRP representative age groups: infant (1y), child (10y), adult (20y). In generic mode this is picked automatically." />
          </label>
          <select
            value={age}
            disabled={genericDisabled}
            onChange={(e) => setAge(e.target.value as typeof age)}
            className="mt-1 w-full rounded border border-slate-300 px-2 py-1.5 disabled:bg-slate-100"
          >
            <option value="infant">Infant (1 yr)</option>
            <option value="child">Child (10 yr)</option>
            <option value="adult">Adult (20 yr)</option>
          </select>
        </div>
        <div>
          <label className="flex items-center gap-2 text-sm font-medium">
            Sex
            <InfoTooltip content="Affects body weight and breathing rate. In generic mode this is picked automatically." />
          </label>
          <select
            value={sex}
            disabled={genericDisabled}
            onChange={(e) => setSex(e.target.value as typeof sex)}
            className="mt-1 w-full rounded border border-slate-300 px-2 py-1.5 disabled:bg-slate-100"
          >
            <option value="male">Male</option>
            <option value="female">Female</option>
          </select>
        </div>
        <div>
          <label className="flex items-center gap-2 text-sm font-medium">
            Building type
            <InfoTooltip content="External-gamma shielding factor: Timber=0, Concrete/Brick=0.9. In generic mode this is picked automatically." />
          </label>
          <select
            value={buildingId}
            disabled={genericDisabled}
            onChange={(e) => setBuildingId(e.target.value)}
            className="mt-1 w-full rounded border border-slate-300 px-2 py-1.5 disabled:bg-slate-100"
          >
            {catalogue.buildings.map((b) => (
              <option key={b.id} value={b.id}>
                {b.label ?? b.id}
              </option>
            ))}
          </select>
        </div>
        <div className="md:col-span-2">
          <label className="flex items-center gap-2 text-sm font-medium">
            Fraction of land contaminated ({fraction.toFixed(2)})
            <InfoTooltip content="If contamination is patchy or only covers part of the site, set this below 1.0. Scales every pathway linearly." />
          </label>
          <input
            type="range"
            min="0"
            max="1"
            step="0.05"
            value={fraction}
            onChange={(e) => setFraction(Number(e.target.value))}
            className="mt-1 w-full"
          />
        </div>
      </section>

      <section className="rounded border border-slate-200 bg-white p-4">
        <button
          type="button"
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="flex items-center gap-2 text-sm font-medium text-rclea-700 hover:text-rclea-900"
          aria-expanded={showAdvanced}
        >
          <span>{showAdvanced ? "▾" : "▸"}</span>
          Advanced: radon mode + per-parameter overrides
        </button>
        {showAdvanced && (
          <div className="mt-4 space-y-4">
            <RadonModeControl
              mode={radonMode}
              measuredValue={measuredRn}
              onModeChange={setRadonMode}
              onMeasuredChange={setMeasuredRn}
            />
            <OverridesEditor value={overrides} onChange={setOverrides} />
          </div>
        )}
      </section>

      <div className="flex justify-end">
        <button
          type="button"
          onClick={submit}
          disabled={running || Object.keys(soil).length === 0}
          className="rounded bg-rclea-700 px-6 py-2 text-sm font-medium text-white shadow hover:bg-rclea-900 disabled:opacity-50"
        >
          {running ? "Running…" : mode === "generic" ? "Find worst case" : "Run assessment"}
        </button>
      </div>
    </div>
  );
}
