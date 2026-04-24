import { useEffect, useState } from "react";
import {
  findWorstCase,
  type RadonMode,
  type WorstCaseReport,
} from "../pyodide/api";
import { InfoTooltip } from "./InfoTooltip";

interface Props {
  soilConcentrations: Record<string, number>;
  fraction: number;
  radonMode: RadonMode;
  measuredValue: number | null;
  overrides: Record<string, number>;
}

export function WorstCasePanel({
  soilConcentrations,
  fraction,
  radonMode,
  measuredValue,
  overrides,
}: Props) {
  const [report, setReport] = useState<WorstCaseReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [showFull, setShowFull] = useState(false);

  const canRun = Object.values(soilConcentrations).some((v) => v > 0);

  useEffect(() => {
    if (!canRun) {
      setReport(null);
      return;
    }
    setLoading(true);
    setErr(null);
    findWorstCase({
      soil_concentrations_Bq_per_kg: soilConcentrations,
      fraction_land_contaminated: fraction,
      radon_mode: radonMode,
      measured_rn222_Bq_per_m3: measuredValue,
      overrides,
    })
      .then(setReport)
      .catch((e) => setErr(String(e)))
      .finally(() => setLoading(false));
  }, [
    JSON.stringify(soilConcentrations),
    fraction,
    radonMode,
    measuredValue,
    JSON.stringify(overrides),
  ]);

  if (!canRun) {
    return (
      <div className="rounded border border-dashed border-slate-300 bg-white p-6 text-center text-sm text-slate-500">
        Enter positive soil concentrations to find the worst-case combination.
      </div>
    );
  }
  if (loading) return <div className="text-slate-500">Running all combinations…</div>;
  if (err) return <div className="rounded border border-red-300 bg-red-50 p-3 text-red-800">{err}</div>;
  if (!report) return null;

  const crit = report.effective_dose_criterion_mSv_per_y;
  const w = report.worst;
  const shown = showFull ? report.entries : report.entries.slice(0, 10);

  return (
    <div className="space-y-3">
      <div className="rounded border border-slate-200 bg-white p-4">
        <div className="flex items-center gap-2">
          <h3>
            Worst-case combination
          </h3>
          <InfoTooltip content={`Ran ${report.entries.length} valid (scenario × building × age × sex) combinations. Commercial/Industrial is adult-only, so the matrix has 40 rows rather than 48.`} />
        </div>
        <div className="mt-2 text-sm">
          <div>
            <strong>Scenario:</strong> {w.scenario_label}
          </div>
          <div>
            <strong>Building:</strong> {w.building_id}
          </div>
          <div>
            <strong>Receptor:</strong> {w.age} / {w.sex}
          </div>
          <div>
            <strong>Total effective dose:</strong>{" "}
            <span className={w.exceeds_effective_criterion ? "font-bold text-red-600" : "font-bold text-emerald-700"}>
              {w.total_effective_dose_mSv_per_y.toPrecision(3)} mSv/y
            </span>{" "}
            <span className="text-slate-500">
              ({((w.total_effective_dose_mSv_per_y / crit) * 100).toFixed(0)}% of 3 mSv/y)
            </span>
          </div>
        </div>
      </div>

      <div className="rounded border border-slate-200 bg-white p-4">
        <div className="flex items-center justify-between">
          <h3>All {report.entries.length} combinations</h3>
          <button
            type="button"
            onClick={() => setShowFull(!showFull)}
            className="text-sm text-rclea-700 underline hover:text-rclea-900"
          >
            {showFull ? "Show top 10" : "Show all"}
          </button>
        </div>
        <div className="mt-3 overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead className="bg-slate-100">
              <tr>
                <th className="text-left">Scenario</th>
                <th className="text-left">Building</th>
                <th className="text-left">Age</th>
                <th className="text-left">Sex</th>
                <th className="text-right">Dose (mSv/y)</th>
                <th className="text-center">{'>'}3 mSv/y</th>
              </tr>
            </thead>
            <tbody>
              {shown.map((e, i) => (
                <tr
                  key={`${e.scenario_id}-${e.building_id}-${e.age}-${e.sex}`}
                  className={i === 0 ? "bg-rclea-50 font-medium" : i % 2 ? "bg-slate-50" : ""}
                >
                  <td>{e.scenario_label}</td>
                  <td>{e.building_id}</td>
                  <td>{e.age}</td>
                  <td>{e.sex}</td>
                  <td className="text-right font-mono">{e.total_effective_dose_mSv_per_y.toPrecision(3)}</td>
                  <td className="text-center">
                    {e.exceeds_effective_criterion ? (
                      <span className="text-red-600">yes</span>
                    ) : (
                      <span className="text-emerald-600">no</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
