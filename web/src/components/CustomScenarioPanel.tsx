import { useMemo, useState } from "react";
import type { Catalogue, Scenario } from "../pyodide/api";
import {
  loadCustomScenariosFromLocalStorage,
  saveCustomScenariosToLocalStorage,
} from "../pyodide/api";
import { InfoTooltip } from "./InfoTooltip";

interface Props {
  catalogue: Catalogue;
  onReloadCatalogue: () => void;
}

type EditablePerAge = Record<string, Record<string, number>>;

/** Clone an existing scenario and let the user edit its per-age parameters.
 * Saves to localStorage; the parent's onReloadCatalogue reloads the Pyodide
 * dataset so the new scenario is immediately selectable on the Assess tab.
 */
export function CustomScenarioPanel({ catalogue, onReloadCatalogue }: Props) {
  const shipped = useMemo(
    () => catalogue.scenarios.filter((s) => !s.id.startsWith("custom_")),
    [catalogue.scenarios],
  );
  const [baseId, setBaseId] = useState(shipped[0]?.id ?? "");
  const [id, setId] = useState("custom_my_site");
  const [label, setLabel] = useState("My Custom Site");
  const [perAge, setPerAge] = useState<EditablePerAge>({});
  const [loaded, setLoaded] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  // Pull in the full base scenario when the user picks one
  const loadBase = () => {
    const base = catalogue.scenarios.find((s) => s.id === baseId);
    if (!base) return;
    setPerAge(structuredClone(base.per_age));
    setLoaded(true);
    setMessage(null);
  };

  const save = () => {
    const base = catalogue.scenarios.find((s) => s.id === baseId);
    if (!base || !loaded) {
      setMessage("Load a base scenario first.");
      return;
    }
    if (!id.startsWith("custom_")) {
      setMessage("id must start with 'custom_' to avoid clashing with shipped scenarios.");
      return;
    }
    const newScenario: Scenario = {
      ...base,
      id,
      label,
      per_age: perAge as Scenario["per_age"],
    };
    const all = loadCustomScenariosFromLocalStorage();
    const next = [...all.filter((s: any) => s?.id !== id), newScenario];
    saveCustomScenariosToLocalStorage(next);
    setMessage(`Saved '${label}'. Reloading catalogue…`);
    onReloadCatalogue();
  };

  const remove = (scenarioId: string) => {
    const all = loadCustomScenariosFromLocalStorage();
    const next = all.filter((s: any) => s?.id !== scenarioId);
    saveCustomScenariosToLocalStorage(next);
    setMessage(`Removed '${scenarioId}'.`);
    onReloadCatalogue();
  };

  const existing = loadCustomScenariosFromLocalStorage() as Scenario[];
  const ageKeys = loaded ? Object.keys(perAge) : [];
  const paramKeys = loaded && ageKeys.length > 0 ? Object.keys(perAge[ageKeys[0]]!) : [];

  return (
    <div className="space-y-4">
      <div className="rounded border border-slate-200 bg-white p-4">
        <div className="flex items-center gap-2">
          <h2 className="!mt-0">Custom scenarios</h2>
          <InfoTooltip
            content={
              <span>
                Clone a shipped scenario and edit its per-age parameters. Saves to browser localStorage only — never uploaded. Registered scenarios appear in the Scenario picker on the Assess tab with the custom id.
              </span>
            }
          />
        </div>
        <p className="text-sm text-slate-600">
          Scenarios you create here are stored locally in your browser
          (<code>localStorage["rclea:customScenarios:v1"]</code>). They appear in the Scenario
          dropdown on the Assess tab.
        </p>

        <div className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-3">
          <div>
            <label className="text-xs font-medium">Base scenario (clone from)</label>
            <select
              value={baseId}
              onChange={(e) => setBaseId(e.target.value)}
              className="mt-1 w-full rounded border border-slate-300 px-2 py-1 text-sm"
            >
              {shipped.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-xs font-medium">
              New id (must start with <code>custom_</code>)
            </label>
            <input
              value={id}
              onChange={(e) => setId(e.target.value)}
              className="mt-1 w-full rounded border border-slate-300 px-2 py-1 text-sm"
            />
          </div>
          <div>
            <label className="text-xs font-medium">Display label</label>
            <input
              value={label}
              onChange={(e) => setLabel(e.target.value)}
              className="mt-1 w-full rounded border border-slate-300 px-2 py-1 text-sm"
            />
          </div>
        </div>

        <div className="mt-3 flex gap-2">
          <button
            type="button"
            onClick={loadBase}
            className="rounded bg-rclea-700 px-3 py-1 text-sm text-white hover:bg-rclea-900"
          >
            Load base parameters
          </button>
          <button
            type="button"
            onClick={save}
            disabled={!loaded}
            className="rounded border border-slate-300 bg-white px-3 py-1 text-sm hover:bg-slate-50 disabled:opacity-50"
          >
            Save
          </button>
        </div>
        {message && <div className="mt-2 text-sm text-emerald-700">{message}</div>}
      </div>

      {loaded && (
        <div className="rounded border border-slate-200 bg-white p-4">
          <h3 className="!mt-0">Per-age parameters</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead className="bg-slate-100">
                <tr>
                  <th className="text-left">Parameter</th>
                  {ageKeys.map((age) => (
                    <th key={age} className="text-right">{age}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {paramKeys.map((p) => (
                  <tr key={p}>
                    <td className="font-mono text-xs">{p}</td>
                    {ageKeys.map((age) => (
                      <td key={age} className="text-right">
                        <input
                          type="number"
                          step="any"
                          value={perAge[age]?.[p] ?? 0}
                          onChange={(e) => {
                            const v = Number(e.target.value);
                            setPerAge({
                              ...perAge,
                              [age]: { ...perAge[age], [p]: Number.isNaN(v) ? 0 : v },
                            });
                          }}
                          className="w-28 rounded border border-slate-300 px-2 py-1 text-right"
                        />
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {existing.length > 0 && (
        <div className="rounded border border-slate-200 bg-white p-4">
          <h3 className="!mt-0">Registered custom scenarios</h3>
          <ul className="mt-2 space-y-1 text-sm">
            {existing.map((s) => (
              <li key={s.id} className="flex items-center gap-2">
                <code className="flex-1">{s.id}</code>
                <span className="flex-1">{s.label}</span>
                <button
                  type="button"
                  onClick={() => remove(s.id)}
                  className="text-red-600 hover:underline"
                >
                  Remove
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
