import { GLOSSARY } from "../lib/glossary";

export function GlossaryPanel() {
  const entries = Object.values(GLOSSARY);
  return (
    <div className="rounded border border-slate-200 bg-white p-5">
      <h2>Glossary</h2>
      <p className="text-sm text-slate-600">
        Hover over any term in this glossary for a one-sentence definition. Terms cross-reference
        the tooltips attached to form inputs.
      </p>
      <dl className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2">
        {entries.map((e) => (
          <div key={e.term} className="rounded border border-slate-200 p-3">
            <dt className="font-semibold text-rclea-900">{e.term}</dt>
            <dd className="mt-1 text-sm text-slate-700">{e.definition}</dd>
            {e.source && <dd className="mt-1 text-xs text-slate-500">Source: {e.source}</dd>}
          </div>
        ))}
      </dl>
    </div>
  );
}
