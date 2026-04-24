import { useCallback, useEffect, useState } from "react";
import { AssessmentForm, type FormState } from "./components/AssessmentForm";
import { CustomScenarioPanel } from "./components/CustomScenarioPanel";
import { DisclaimerBanner, useDisclaimerGate } from "./components/DisclaimerBanner";
import { DisclaimerModal } from "./components/DisclaimerModal";
import { GlossaryPanel } from "./components/GlossaryPanel";
import { GuidelinesPanel } from "./components/GuidelinesPanel";
import { ResultsPanel } from "./components/ResultsPanel";
import { TutorialView } from "./components/TutorialView";
import { WorstCasePanel } from "./components/WorstCasePanel";
import {
  assess,
  loadCatalogue,
  type AssessmentInput,
  type AssessmentMode,
  type AssessmentResult,
  type Catalogue,
} from "./pyodide/api";

type Tab = "assess" | "guidelines" | "custom" | "tutorials" | "glossary";

export function App() {
  const [tab, setTab] = useState<Tab>("assess");
  const { acknowledged, acknowledge } = useDisclaimerGate();
  const [showInfoDisclaimer, setShowInfoDisclaimer] = useState(false);

  const [catalogue, setCatalogue] = useState<Catalogue | null>(null);
  const [loadingMsg, setLoadingMsg] = useState<string>("Booting Python engine…");
  const [loadError, setLoadError] = useState<string | null>(null);
  const [result, setResult] = useState<AssessmentResult | null>(null);
  const [running, setRunning] = useState(false);
  const [formState, setFormState] = useState<FormState | null>(null);

  const reloadCatalogue = useCallback(() => {
    setLoadingMsg("Reloading catalogue…");
    loadCatalogue()
      .then((c) => {
        setCatalogue(c);
        setLoadingMsg("");
      })
      .catch((e) => {
        console.error(e);
        setLoadError(String(e));
        setLoadingMsg("");
      });
  }, []);

  useEffect(() => {
    if (!acknowledged) return;
    setLoadingMsg("Downloading Pyodide runtime (first load ~8 MB)…");
    reloadCatalogue();
  }, [acknowledged, reloadCatalogue]);

  const runAssess = async (input: AssessmentInput, mode: AssessmentMode) => {
    setRunning(true);
    try {
      if (mode === "generic") {
        // Let WorstCasePanel do the heavy lifting via its own effect;
        // we still run the current (scenario, age, sex, building) to populate the Results panel.
      }
      const r = await assess(input);
      setResult(r);
    } catch (e) {
      console.error(e);
      setLoadError(String(e));
    } finally {
      setRunning(false);
    }
  };

  return (
    <>
      <DisclaimerBanner onShowFull={() => setShowInfoDisclaimer(true)} />
      <DisclaimerModal open={!acknowledged} onAcknowledge={acknowledge} />
      <DisclaimerModal
        open={showInfoDisclaimer}
        onAcknowledge={() => setShowInfoDisclaimer(false)}
        informational
        onClose={() => setShowInfoDisclaimer(false)}
      />

      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
          <div>
            <h1 className="text-xl">webRCLEA - not affiliated with the Environment Agency</h1>
            <p className="text-xs text-slate-600">
              Radioactively Contaminated Land Exposure Assessment · runs entirely in your browser
            </p>
          </div>
          <nav className="flex gap-2" aria-label="Main navigation">
            <TabButton active={tab === "assess"} onClick={() => setTab("assess")}>
              Assess
            </TabButton>
            <TabButton active={tab === "guidelines"} onClick={() => setTab("guidelines")}>
              Guidelines
            </TabButton>
            <TabButton active={tab === "custom"} onClick={() => setTab("custom")}>
              Custom
            </TabButton>
            <TabButton active={tab === "tutorials"} onClick={() => setTab("tutorials")}>
              Tutorials
            </TabButton>
            <TabButton active={tab === "glossary"} onClick={() => setTab("glossary")}>
              Glossary
            </TabButton>
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-6">
        {acknowledged && loadingMsg && (
          <div className="rounded border border-slate-200 bg-white p-6 text-center text-slate-700">
            <div className="font-medium">{loadingMsg}</div>
            <div className="mt-2 text-sm text-slate-500">
              The Python calculation engine is loading into your browser. Cached after first visit.
            </div>
          </div>
        )}
        {loadError && (
          <div className="rounded border border-red-300 bg-red-50 p-4 text-sm text-red-800">
            <strong>Failed to load the Python engine.</strong>
            <pre className="mt-2 overflow-auto text-xs">{loadError}</pre>
          </div>
        )}

        {catalogue && tab === "assess" && (
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <AssessmentForm
              catalogue={catalogue}
              onSubmit={runAssess}
              onChange={setFormState}
              running={running}
            />
            <div className="space-y-6">
              <ResultsPanel result={result} />
              {formState?.mode === "generic" && (
                <WorstCasePanel
                  soilConcentrations={formState.soil}
                  fraction={formState.fraction}
                  radonMode={formState.radonMode}
                  measuredValue={formState.measuredRn}
                  overrides={formState.overrides}
                />
              )}
            </div>
          </div>
        )}
        {catalogue && tab === "guidelines" && (
          <GuidelinesPanel
            catalogue={catalogue}
            siteSoil={formState?.soil ?? {}}
          />
        )}
        {catalogue && tab === "custom" && (
          <CustomScenarioPanel catalogue={catalogue} onReloadCatalogue={reloadCatalogue} />
        )}
        {catalogue && tab === "tutorials" && <TutorialView />}
        {catalogue && tab === "glossary" && <GlossaryPanel />}
      </main>

      <footer className="border-t border-slate-200 bg-white py-4 text-center text-xs text-slate-500">
        Educational implementation, not a regulatory tool. Author(s) accept no liability. See{" "}
        <button
          type="button"
          onClick={() => setShowInfoDisclaimer(true)}
          className="underline"
        >
          full disclaimer
        </button>
        . Dose coefficients from the RCLEA reference data (ICRP). Methodology per CRCE-RAD-003-2020 / CLR-13.
      </footer>
    </>
  );
}

function TabButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded px-3 py-1.5 text-sm font-medium ${
        active ? "bg-rclea-700 text-white" : "text-slate-700 hover:bg-slate-100"
      }`}
    >
      {children}
    </button>
  );
}
