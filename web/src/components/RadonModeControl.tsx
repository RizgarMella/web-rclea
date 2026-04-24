import type { RadonMode } from "../pyodide/api";
import { InfoTooltip } from "./InfoTooltip";

interface Props {
  mode: RadonMode;
  measuredValue: number | null;
  onModeChange: (mode: RadonMode) => void;
  onMeasuredChange: (value: number | null) => void;
}

/** Radio selector for Rn-222 mode + conditional Bq/m³ input for "measured". */
export function RadonModeControl({ mode, measuredValue, onModeChange, onMeasuredChange }: Props) {
  return (
    <div className="rounded border border-slate-200 p-3">
      <div className="flex items-center gap-2">
        <span className="text-sm font-medium">Indoor Rn-222 mode</span>
        <InfoTooltip
          content={
            <div className="space-y-2">
              <p>
                Three ways to determine the indoor Rn-222 concentration that drives the radon pathway:
              </p>
              <ul className="list-disc pl-4">
                <li>
                  <strong>Default (K=3):</strong> assumes 3 Bq/m³ indoor Rn-222 per Bq/kg Ra-226 soil. Conservative generic.
                </li>
                <li>
                  <strong>Measured:</strong> use your measured indoor Rn-222 directly. Most accurate when a survey exists.
                </li>
                <li>
                  <strong>Site-specific:</strong> calculate K from soil emanation/diffusion and building height/ventilation (Nazaroff/Porstendörfer 1-D model).
                </li>
              </ul>
            </div>
          }
        />
      </div>
      <div className="mt-2 flex flex-col gap-2">
        <Option
          id="rm_default"
          active={mode === "default"}
          onSelect={() => onModeChange("default")}
          label="Default (K = 3 Bq/m³ per Bq/kg Ra-226)"
        />
        <Option
          id="rm_measured"
          active={mode === "measured"}
          onSelect={() => onModeChange("measured")}
          label="Measured indoor Rn-222"
        />
        {mode === "measured" && (
          <div className="ml-6 flex items-center gap-2 text-sm">
            <label>Measured value (Bq/m³):</label>
            <input
              type="number"
              min="0"
              step="any"
              value={measuredValue ?? ""}
              onChange={(e) => {
                const v = e.target.value;
                onMeasuredChange(v === "" ? null : Number(v));
              }}
              className="w-32 rounded border border-slate-300 px-2 py-1"
              aria-label="Measured Rn-222 in Bq/m3"
            />
          </div>
        )}
        <Option
          id="rm_site"
          active={mode === "site_specific"}
          onSelect={() => onModeChange("site_specific")}
          label="Site-specific (calculate K from soil + building)"
        />
        {mode === "site_specific" && (
          <div className="ml-6 text-xs text-slate-600">
            K ≈ 2.24 under default soil/building parameters — edit those in <strong>Overrides</strong> to tune.
          </div>
        )}
      </div>
    </div>
  );
}

function Option({
  id,
  active,
  onSelect,
  label,
}: {
  id: string;
  active: boolean;
  onSelect: () => void;
  label: string;
}) {
  return (
    <label htmlFor={id} className="flex cursor-pointer items-center gap-2 text-sm">
      <input
        type="radio"
        id={id}
        checked={active}
        onChange={onSelect}
        className="h-4 w-4 text-rclea-700"
      />
      {label}
    </label>
  );
}
