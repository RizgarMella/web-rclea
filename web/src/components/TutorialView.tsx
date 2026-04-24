import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { listTutorials, type Tutorial } from "../pyodide/api";
import { InteractiveStep } from "./InteractiveStep";

export function TutorialView() {
  const [tuts, setTuts] = useState<Tutorial[]>([]);
  const [active, setActive] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    listTutorials()
      .then((list) => {
        setTuts(list);
        setActive(list[0]?.slug ?? null);
      })
      .catch((e) => setErr(String(e)));
  }, []);

  const current = tuts.find((t) => t.slug === active);
  if (err) return <div className="text-red-700">Failed to load tutorials: {err}</div>;
  if (!tuts.length) return <div className="text-slate-500">Loading tutorials…</div>;

  return (
    <div className="grid grid-cols-1 gap-6 md:grid-cols-[240px,1fr]">
      <aside className="rounded border border-slate-200 bg-white p-3">
        <h3 className="text-sm font-semibold text-rclea-900">Curriculum</h3>
        <ul className="mt-2 space-y-1 text-sm">
          {tuts.map((t) => (
            <li key={t.slug}>
              <button
                type="button"
                onClick={() => setActive(t.slug)}
                className={`w-full rounded px-2 py-1 text-left ${
                  active === t.slug ? "bg-rclea-100 font-medium" : "hover:bg-slate-100"
                }`}
              >
                {t.title}
              </button>
            </li>
          ))}
        </ul>
        <p className="mt-3 border-t border-slate-200 pt-3 text-xs text-slate-500">
          Lessons contain <strong>interactive steps</strong> — editable assessment widgets that
          run the real engine inline.
        </p>
      </aside>
      <article className="rounded border border-slate-200 bg-white p-5">
        {current && (
          <div className="prose max-w-none">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                code(props) {
                  const { className, children } = props as {
                    className?: string;
                    children?: React.ReactNode;
                  };
                  const match = /language-(\w[\w-]*)/.exec(className ?? "");
                  const lang = match?.[1];
                  if (lang === "rclea-run") {
                    return <InteractiveStep source={String(children ?? "").replace(/\n$/, "")} />;
                  }
                  return (
                    <code className={className}>
                      {children}
                    </code>
                  );
                },
              }}
            >
              {current.markdown}
            </ReactMarkdown>
          </div>
        )}
      </article>
    </div>
  );
}
