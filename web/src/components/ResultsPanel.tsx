import { useState } from "react";
import type { AssessmentResult } from "../pyodide/api";
import { InfoTooltip } from "./InfoTooltip";

export function ResultsPanel({ result }: { result: AssessmentResult | null }) {
  if (!result) {
    return (
      <div className="rounded border border-dashed border-slate-300 bg-white p-8 text-center text-slate-500">
        Enter soil concentrations and click <strong>Run assessment</strong>.
      </div>
    );
  }

  const crit = result.effective_dose_criterion_mSv_per_y;
  const dose = result.total_effective_dose_mSv_per_y;
  const pct = Math.min(100, (dose / crit) * 100);
  const exceed = result.exceeds_effective_criterion;

  return (
    <div className="space-y-5">
      <div className="rounded border border-slate-200 bg-white p-4">
        <h3 className="flex items-center gap-2">
          Total effective dose
          <InfoTooltip content="Sum of doses from all pathways except skin (which has its own criterion). Compared against the 3 mSv/y statutory harm threshold under Part 2A." />
        </h3>
        <div className="mt-3 flex items-baseline gap-3">
          <div className={`text-4xl font-bold ${exceed ? "text-red-600" : "text-emerald-700"}`}>
            {dose.toPrecision(3)}
          </div>
          <div className="text-sm text-slate-600">mSv/y</div>
          <div className="text-sm text-slate-500">
            ({(pct).toFixed(0)}% of the 3 mSv/y criterion)
          </div>
        </div>
        <div className="mt-2 h-4 w-full overflow-hidden rounded bg-slate-200">
          <div
            className={`h-full ${exceed ? "bg-red-500" : "bg-emerald-500"}`}
            style={{ width: `${Math.max(2, pct)}%` }}
          />
        </div>
        <div className="mt-1 flex justify-between text-xs text-slate-500">
          <span>0</span>
          <span>3 mSv/y (criterion)</span>
        </div>
        <div className="mt-2 text-sm">
          {exceed ? (
            <span className="text-red-700">
              <strong>Above criterion.</strong> Further investigation warranted.
            </span>
          ) : (
            <span className="text-emerald-700">
              <strong>Below criterion.</strong> (Interpret in context; see interpretation tutorial.)
            </span>
          )}
        </div>
        {result.safety_margin !== null && (
          <div className="mt-2 text-sm">
            <strong>Safety margin:</strong>{" "}
            <span className={exceed ? "font-bold text-red-600" : "font-bold text-emerald-700"}>
              {result.safety_margin.toPrecision(3)}×
            </span>{" "}
            <span className="text-slate-500">(criterion / total dose)</span>
          </div>
        )}
      </div>

      <div className="rounded border border-slate-200 bg-white p-4">
        <h3>Skin equivalent dose</h3>
        <div className="mt-1 text-sm">
          <span className="text-lg font-semibold">
            {result.total_skin_equivalent_dose_mSv_per_y.toPrecision(3)}
          </span>{" "}
          mSv/y{" "}
          <span className="text-slate-500">
            (criterion {result.skin_dose_criterion_mSv_per_y} mSv/y —{" "}
            {result.exceeds_skin_criterion ? "exceeded" : "within limit"})
          </span>
        </div>
      </div>

      <div className="rounded border border-slate-200 bg-white p-4">
        <h3 className="flex items-center gap-2">
          Dose by pathway
          <InfoTooltip content="Click a pathway to see which isotopes contribute most to that dose. Together these let you diagnose which contaminant and which pathway drive your result." />
        </h3>
        <PathwayBreakdown result={result} />
      </div>

      {result.notes.length > 0 && (
        <div className="rounded border border-amber-200 bg-amber-50 p-4">
          <h3 className="text-amber-800">Notes</h3>
          <ul className="mt-2 list-disc pl-6 text-sm text-amber-900">
            {result.notes.map((n, i) => (
              <li key={i}>{n}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function PathwayBreakdown({ result }: { result: AssessmentResult }) {
  const [open, setOpen] = useState<string | null>(null);
  const maxDose = Math.max(...result.per_pathway.map((p) => p.dose_mSv_per_year), 1e-12);
  return (
    <ul className="mt-3 space-y-2">
      {result.per_pathway.map((p) => {
        const pct = (p.dose_mSv_per_year / maxDose) * 100;
        const isOpen = open === p.pathway;
        const contribs = Object.entries(p.contributing_isotopes)
          .filter(([, v]) => v > 0)
          .sort((a, b) => b[1] - a[1]);
        return (
          <li key={p.pathway} className="rounded border border-slate-200">
            <button
              type="button"
              onClick={() => setOpen(isOpen ? null : p.pathway)}
              className="flex w-full items-center gap-3 px-3 py-2 text-left hover:bg-slate-50"
              aria-expanded={isOpen}
            >
              <div className="w-56 text-sm font-medium">{p.label}</div>
              <div className="relative h-3 flex-1 overflow-hidden rounded bg-slate-100">
                <div
                  className="h-full bg-rclea-500"
                  style={{ width: `${Math.max(1, pct)}%` }}
                />
              </div>
              <div className="w-32 text-right font-mono text-sm">
                {p.dose_mSv_per_year.toPrecision(3)}{" "}
                <span className="text-xs text-slate-500">mSv/y</span>
              </div>
            </button>
            {isOpen && contribs.length > 0 && (
              <div className="border-t border-slate-200 bg-slate-50 px-3 py-2 text-xs">
                <div className="font-medium text-slate-700">Isotope contributions:</div>
                <ul className="mt-1 grid grid-cols-1 gap-1 sm:grid-cols-2 md:grid-cols-3">
                  {contribs.map(([iso, d]) => (
                    <li key={iso} className="font-mono">
                      {iso}: {d.toPrecision(3)} <span className="text-slate-500">mSv/y</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {isOpen && contribs.length === 0 && (
              <div className="border-t border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-500">
                No isotope contributes to this pathway for the current inputs.
              </div>
            )}
          </li>
        );
      })}
    </ul>
  );
}
