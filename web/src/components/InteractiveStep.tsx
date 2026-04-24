import { useState } from "react";
import { parse as parseYaml } from "yaml";
import { assess, type AssessmentInput, type AssessmentResult, type RadonMode } from "../pyodide/api";

interface StepSpec {
  title?: string;
  question?: string;
  try_changing?: string;
  soil_concentrations_Bq_per_kg: Record<string, number>;
  scenario_id: string;
  age?: "infant" | "child" | "adult";
  sex?: "male" | "female";
  building_id?: string;
  fraction_land_contaminated?: number;
  radon_mode?: RadonMode;
  measured_rn222_Bq_per_m3?: number | null;
  overrides?: Record<string, number>;
}

/**
 * Renders a tutorial's `rclea-run` code fence as an inline, editable,
 * runnable assessment. Parses the fence body as YAML and binds the result
 * to a local form — each run re-invokes the Python engine in Pyodide.
 */
export function InteractiveStep({ source }: { source: string }) {
  let spec: StepSpec | null = null;
  let parseError: string | null = null;
  try {
    spec = parseYaml(source) as StepSpec;
  } catch (e) {
    parseError = String(e);
  }

  if (parseError || !spec) {
    return (
      <div className="my-4 rounded border border-red-300 bg-red-50 p-3 text-sm text-red-800">
        <strong>Could not parse interactive step.</strong>
        <pre className="mt-2 whitespace-pre-wrap text-xs">{parseError ?? "Empty spec"}</pre>
      </div>
    );
  }

  const [input, setInput] = useState<AssessmentInput>(() => ({
    soil_concentrations_Bq_per_kg: { ...spec!.soil_concentrations_Bq_per_kg },
    scenario_id: spec!.scenario_id,
    age: spec!.age ?? "adult",
    sex: spec!.sex ?? "male",
    building_id: spec!.building_id ?? "Timber",
    fraction_land_contaminated: spec!.fraction_land_contaminated ?? 1.0,
    radon_mode: spec!.radon_mode ?? "default",
    measured_rn222_Bq_per_m3: spec!.measured_rn222_Bq_per_m3 ?? null,
    overrides: spec!.overrides ?? {},
  }));
  const [result, setResult] = useState<AssessmentResult | null>(null);
  const [running, setRunning] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const run = async () => {
    setRunning(true);
    setErr(null);
    try {
      setResult(await assess(input));
    } catch (e) {
      setErr(String(e));
    } finally {
      setRunning(false);
    }
  };

  const updateConc = (iso: string, v: string) => {
    const n = Number(v);
    setInput({
      ...input,
      soil_concentrations_Bq_per_kg: {
        ...input.soil_concentrations_Bq_per_kg,
        [iso]: Number.isNaN(n) ? 0 : n,
      },
    });
  };

  const patchInput = <K extends keyof AssessmentInput>(key: K, value: AssessmentInput[K]) =>
    setInput({ ...input, [key]: value });

  const reset = () => {
    setInput({
      soil_concentrations_Bq_per_kg: { ...spec!.soil_concentrations_Bq_per_kg },
      scenario_id: spec!.scenario_id,
      age: spec!.age ?? "adult",
      sex: spec!.sex ?? "male",
      building_id: spec!.building_id ?? "Timber",
      fraction_land_contaminated: spec!.fraction_land_contaminated ?? 1.0,
      radon_mode: spec!.radon_mode ?? "default",
      measured_rn222_Bq_per_m3: spec!.measured_rn222_Bq_per_m3 ?? null,
      overrides: spec!.overrides ?? {},
    });
    setResult(null);
    setErr(null);
  };

  return (
    <div className="not-prose my-5 rounded border-2 border-rclea-200 bg-rclea-50 p-4 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="text-xs font-semibold uppercase tracking-wide text-rclea-700">
            Interactive step
          </div>
          {spec.title && (
            <h4 className="mt-1 text-lg font-semibold text-rclea-900">{spec.title}</h4>
          )}
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={reset}
            className="rounded border border-slate-300 bg-white px-3 py-1.5 text-sm hover:bg-slate-50"
          >
            Reset
          </button>
          <button
            type="button"
            onClick={run}
            disabled={running}
            className="rounded bg-rclea-700 px-4 py-1.5 text-sm font-medium text-white hover:bg-rclea-900 disabled:opacity-50"
          >
            {running ? "Running…" : "Run"}
          </button>
        </div>
      </div>

      <div className="mt-3 grid grid-cols-1 gap-3 lg:grid-cols-2">
        <div>
          <div className="text-xs font-semibold text-slate-600">Soil concentrations (Bq/kg)</div>
          <ul className="mt-1 space-y-1">
            {Object.entries(input.soil_concentrations_Bq_per_kg).map(([iso, conc]) => (
              <li key={iso} className="flex items-center gap-2 text-sm">
                <span className="w-16 font-mono">{iso}</span>
                <input
                  type="number"
                  min="0"
                  step="any"
                  value={conc}
                  onChange={(e) => updateConc(iso, e.target.value)}
                  className="w-28 rounded border border-slate-300 px-2 py-1 text-sm"
                  aria-label={`${iso} concentration`}
                />
              </li>
            ))}
          </ul>
        </div>
        <div className="space-y-2 text-sm">
          <div className="flex items-center gap-2">
            <label className="w-24 text-xs text-slate-600">Scenario</label>
            <code className="truncate text-xs">{input.scenario_id}</code>
          </div>
          <div className="flex items-center gap-2">
            <label className="w-24 text-xs text-slate-600">Age</label>
            <select
              value={input.age}
              onChange={(e) => patchInput("age", e.target.value as AssessmentInput["age"])}
              className="rounded border border-slate-300 px-2 py-1 text-sm"
            >
              <option value="infant">Infant</option>
              <option value="child">Child</option>
              <option value="adult">Adult</option>
            </select>
          </div>
          <div className="flex items-center gap-2">
            <label className="w-24 text-xs text-slate-600">Building</label>
            <select
              value={input.building_id}
              onChange={(e) => patchInput("building_id", e.target.value)}
              className="rounded border border-slate-300 px-2 py-1 text-sm"
            >
              <option value="Timber">Timber</option>
              <option value="Concrete_Brick">Concrete/Brick</option>
            </select>
          </div>
          <div className="flex items-center gap-2">
            <label className="w-24 text-xs text-slate-600">
              Fraction ({input.fraction_land_contaminated.toFixed(2)})
            </label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={input.fraction_land_contaminated}
              onChange={(e) => patchInput("fraction_land_contaminated", Number(e.target.value))}
              className="flex-1"
            />
          </div>
        </div>
      </div>

      {spec.question && (
        <div className="mt-3 rounded bg-white p-2 text-sm">
          <strong className="text-rclea-700">Think about:</strong> {spec.question}
        </div>
      )}
      {spec.try_changing && (
        <div className="mt-2 rounded bg-white/70 p-2 text-sm text-slate-700">
          <strong>Try changing:</strong> {spec.try_changing}
        </div>
      )}

      {err && (
        <div className="mt-3 rounded border border-red-300 bg-red-50 p-2 text-sm text-red-800">
          {err}
        </div>
      )}

      {result && <MiniResults result={result} />}
    </div>
  );
}

function MiniResults({ result }: { result: AssessmentResult }) {
  const crit = result.effective_dose_criterion_mSv_per_y;
  const dose = result.total_effective_dose_mSv_per_y;
  const pct = Math.min(100, (dose / crit) * 100);
  const exceed = result.exceeds_effective_criterion;
  const sorted = [...result.per_pathway].sort((a, b) => b.dose_mSv_per_year - a.dose_mSv_per_year);
  const maxDose = Math.max(...sorted.map((p) => p.dose_mSv_per_year), 1e-12);

  return (
    <div className="mt-4 rounded border border-slate-200 bg-white p-3">
      <div className="flex items-baseline gap-3">
        <div className="text-xs font-semibold text-slate-600">Total effective dose</div>
        <div className={`text-2xl font-bold ${exceed ? "text-red-600" : "text-emerald-700"}`}>
          {dose.toPrecision(3)}
        </div>
        <div className="text-xs text-slate-500">mSv/y ({pct.toFixed(0)}% of 3 mSv/y)</div>
      </div>
      <div className="mt-1 h-3 w-full overflow-hidden rounded bg-slate-200">
        <div
          className={`h-full ${exceed ? "bg-red-500" : "bg-emerald-500"}`}
          style={{ width: `${Math.max(2, pct)}%` }}
        />
      </div>
      <ul className="mt-2 space-y-1 text-xs">
        {sorted.map((p) => (
          <li key={p.pathway} className="flex items-center gap-2">
            <span className="w-44 truncate">{p.label}</span>
            <div className="relative h-2 flex-1 overflow-hidden rounded bg-slate-100">
              <div
                className="h-full bg-rclea-500"
                style={{ width: `${Math.max(1, (p.dose_mSv_per_year / maxDose) * 100)}%` }}
              />
            </div>
            <span className="w-28 text-right font-mono">
              {p.dose_mSv_per_year.toPrecision(2)} <span className="text-slate-500">mSv/y</span>
            </span>
          </li>
        ))}
      </ul>
      {result.notes.length > 0 && (
        <ul className="mt-2 list-disc pl-5 text-xs text-amber-800">
          {result.notes.map((n, i) => (
            <li key={i}>{n}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
