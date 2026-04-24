import { useEffect, useMemo, useState } from "react";
import {
  computeRsgvs,
  type AgeGroup,
  type Catalogue,
  type RadonMode,
  type RSGVReport,
  type Sex,
} from "../pyodide/api";
import { InfoTooltip } from "./InfoTooltip";

interface Props {
  catalogue: Catalogue;
  siteSoil: Record<string, number>;
}

export function GuidelinesPanel({ catalogue, siteSoil }: Props) {
  const [scenarioId, setScenarioId] = useState(catalogue.scenarios[0]?.id ?? "");
  const [age, setAge] = useState<AgeGroup>("infant");
  const [sex, setSex] = useState<Sex>("male");
  const [buildingId, setBuildingId] = useState(catalogue.buildings[0]?.id ?? "Timber");
  const [radonMode, setRadonMode] = useState<RadonMode>("default");
  const [report, setReport] = useState<RSGVReport | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    setErr(null);
    computeRsgvs({
      scenario_id: scenarioId,
      age,
      sex,
      building_id: buildingId,
      radon_mode: radonMode,
    })
      .then(setReport)
      .catch((e) => setErr(String(e)))
      .finally(() => setLoading(false));
  }, [scenarioId, age, sex, buildingId, radonMode]);

  const rows = useMemo(() => {
    if (!report) return [];
    return Object.entries(report.rsgvs_Bq_per_kg)
      .map(([iso, rsgv]) => {
        const site = siteSoil[iso];
        const ratio =
          site !== undefined && rsgv > 0 && isFinite(rsgv) ? site / rsgv : undefined;
        let status: "below" | "near" | "above" | undefined;
        if (ratio !== undefined) {
          if (ratio >= 1.0) status = "above";
          else if (ratio >= 0.1) status = "near";
          else status = "below";
        }
        return { iso, rsgv, site, ratio, status };
      })
      .sort((a, b) => a.rsgv - b.rsgv); // most restrictive first
  }, [report, siteSoil]);

  const downloadCsv = () => {
    if (!report) return;
    const lines = ["isotope,rsgv_Bq_per_kg,site_Bq_per_kg,ratio"];
    for (const r of rows) {
      lines.push(
        `${r.iso},${isFinite(r.rsgv) ? r.rsgv : ""},${r.site ?? ""},${r.ratio ?? ""}`,
      );
    }
    const blob = new Blob([lines.join("\n")], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `rsgv_${scenarioId}_${age}_${sex}_${buildingId}_${radonMode}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-4">
      <div className="rounded border border-slate-200 bg-white p-4">
        <div className="flex items-center gap-2">
          <h2 className="!mt-0">Radioactivity in Soil Guideline Values (RSGVs)</h2>
          <InfoTooltip
            content={
              <span>
                For each radionuclide, the Bq/kg soil concentration that alone produces the 3 mSv/y
                effective-dose criterion under the selected scenario and receptor. RSGVs are
                scenario-dependent: change the dropdowns to see how they shift.
              </span>
            }
          />
        </div>
        <p className="text-sm text-slate-600">
          Choose a scenario and receptor. Your site values from the Assess tab are reused
          automatically — the ratio and status columns appear when site values are present.
        </p>

        <div className="mt-3 grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-5">
          <div>
            <label className="text-xs font-medium">Scenario</label>
            <select
              value={scenarioId}
              onChange={(e) => setScenarioId(e.target.value)}
              className="mt-1 w-full rounded border border-slate-300 px-2 py-1 text-sm"
            >
              {catalogue.scenarios.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-xs font-medium">Age</label>
            <select
              value={age}
              onChange={(e) => setAge(e.target.value as AgeGroup)}
              className="mt-1 w-full rounded border border-slate-300 px-2 py-1 text-sm"
            >
              <option value="infant">Infant</option>
              <option value="child">Child</option>
              <option value="adult">Adult</option>
            </select>
          </div>
          <div>
            <label className="text-xs font-medium">Sex</label>
            <select
              value={sex}
              onChange={(e) => setSex(e.target.value as Sex)}
              className="mt-1 w-full rounded border border-slate-300 px-2 py-1 text-sm"
            >
              <option value="male">Male</option>
              <option value="female">Female</option>
            </select>
          </div>
          <div>
            <label className="text-xs font-medium">Building</label>
            <select
              value={buildingId}
              onChange={(e) => setBuildingId(e.target.value)}
              className="mt-1 w-full rounded border border-slate-300 px-2 py-1 text-sm"
            >
              {catalogue.buildings.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.label ?? b.id}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-xs font-medium">Radon</label>
            <select
              value={radonMode}
              onChange={(e) => setRadonMode(e.target.value as RadonMode)}
              className="mt-1 w-full rounded border border-slate-300 px-2 py-1 text-sm"
            >
              <option value="default">Default K=3</option>
              <option value="site_specific">Site-specific</option>
              <option value="measured">Measured (ignored)</option>
            </select>
          </div>
        </div>

        <div className="mt-3 flex items-center justify-between text-sm">
          <div className="text-slate-600">
            Criterion: {report?.effective_dose_criterion_mSv_per_y ?? 3} mSv/y
          </div>
          <button
            type="button"
            onClick={downloadCsv}
            disabled={!report}
            className="rounded border border-slate-300 bg-white px-3 py-1 hover:bg-slate-50 disabled:opacity-50"
          >
            Download CSV
          </button>
        </div>
      </div>

      {loading && <div className="text-slate-500">Computing RSGVs…</div>}
      {err && <div className="rounded border border-red-300 bg-red-50 p-3 text-red-800">{err}</div>}

      {report && (
        <div className="rounded border border-slate-200 bg-white p-4">
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead className="bg-slate-100">
                <tr>
                  <th className="text-left">Isotope</th>
                  <th className="text-right">RSGV (Bq/kg)</th>
                  <th className="text-right">Your site (Bq/kg)</th>
                  <th className="text-right">Site / RSGV</th>
                  <th className="text-center">Status</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r, i) => (
                  <tr key={r.iso} className={i % 2 ? "bg-slate-50" : ""}>
                    <td className="font-mono">{r.iso}</td>
                    <td className="text-right font-mono">
                      {isFinite(r.rsgv) ? r.rsgv.toPrecision(3) : "∞"}
                    </td>
                    <td className="text-right">{r.site ?? "—"}</td>
                    <td className="text-right">
                      {r.ratio !== undefined ? r.ratio.toPrecision(2) : "—"}
                    </td>
                    <td className="text-center">
                      {r.status === "above" && <span className="text-red-600">ABOVE</span>}
                      {r.status === "near" && <span className="text-amber-600">near</span>}
                      {r.status === "below" && <span className="text-emerald-600">below</span>}
                      {!r.status && "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-2 text-xs text-slate-500">
            Status rule: above = ratio ≥ 1.0 (site is at/over the single-isotope screening concentration),
            near = ratio ≥ 0.1, below = ratio &lt; 0.1. Educational only — not a regulatory finding.
          </p>
        </div>
      )}
    </div>
  );
}
