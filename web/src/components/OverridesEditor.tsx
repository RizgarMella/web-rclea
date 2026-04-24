import { useState } from "react";
import { InfoTooltip } from "./InfoTooltip";

interface Props {
  value: Record<string, number>;
  onChange: (next: Record<string, number>) => void;
}

interface KeyRef {
  key: string;           // Literal key, or template with {placeholders}
  label: string;
  unit: string;          // Empty string = dimensionless
  description: string;
  defaultValue: string;  // Library value or range
  pathways: string[];    // Which pathways read this key
}

/** Full reference of every override key the engine honours.
 * Grouped by category for the expandable index panel. */
const KEY_GROUPS: Array<{ title: string; keys: KeyRef[] }> = [
  {
    title: "Site & soil (global)",
    keys: [
      {
        key: "rho_B_soil_bulk_density_kg_per_m3",
        label: "Soil bulk density ρ_B",
        unit: "kg/m³",
        description: "Dry bulk density of the contaminated soil layer. Converts Bq/kg to Bq/m³ for the external pathway and the radon exhalation model.",
        defaultValue: "1400",
        pathways: ["external", "radon (site-specific)"],
      },
      {
        key: "dust_loading_kg_per_m3",
        label: "Respirable dust loading",
        unit: "kg/m³",
        description: "Airborne respirable particulate concentration. Conservative default assumes ongoing windblown / traffic resuspension.",
        defaultValue: "5 × 10⁻⁸",
        pathways: ["inhalation_dust"],
      },
      {
        key: "fraction_indoor_dust_from_local_soil",
        label: "Fraction of indoor dust from local soil",
        unit: "— (0–1)",
        description: "How much of the dust you breathe indoors originates from site-local soil (rather than clean outdoor air).",
        defaultValue: "0.75 (residential / commercial), 0.375 (allotments)",
        pathways: ["inhalation_dust"],
      },
      {
        key: "shielding_factor",
        label: "Building γ shielding factor",
        unit: "— (0–1)",
        description: "Fractional reduction of external γ dose rate while indoors. 0 = no shielding, 0.9 = 90% reduction.",
        defaultValue: "Timber: 0.0 · Concrete/Brick: 0.9",
        pathways: ["external"],
      },
    ],
  },
  {
    title: "Radon (site-specific K)",
    keys: [
      {
        key: "rn222_emanation_fraction",
        label: "Emanation fraction α",
        unit: "— (0–1)",
        description: "Fraction of Rn-222 produced in the soil grain that escapes into pore space and can then diffuse out.",
        defaultValue: "0.2",
        pathways: ["radon (site-specific)"],
      },
      {
        key: "rn222_effective_diffusion_m2_per_s",
        label: "Effective diffusion D_e",
        unit: "m²/s",
        description: "Effective Rn-222 diffusion coefficient through the soil (drier/looser soil → larger).",
        defaultValue: "2 × 10⁻⁶",
        pathways: ["radon (site-specific)"],
      },
      {
        key: "rn222_decay_constant_per_s",
        label: "Rn-222 decay constant λ_Rn",
        unit: "s⁻¹",
        description: "Radon-222 physical decay constant (3.82-day half-life).",
        defaultValue: "2.1 × 10⁻⁶",
        pathways: ["radon (site-specific)"],
      },
      {
        key: "building_rn222_height_m",
        label: "Building height h",
        unit: "m",
        description: "Internal height over which radon accumulates; used in the indoor mass-balance.",
        defaultValue: "3.0",
        pathways: ["radon (site-specific)"],
      },
      {
        key: "building_rn222_ventilation_rate_per_s",
        label: "Ventilation rate λ_v",
        unit: "s⁻¹",
        description: "Air-change rate. 8.33e-5 s⁻¹ ≈ 0.3 air-changes/hour (typical UK dwelling).",
        defaultValue: "8.33 × 10⁻⁵",
        pathways: ["radon (site-specific)"],
      },
      {
        key: "rn222_equilibrium_factor",
        label: "Equilibrium factor F_eq",
        unit: "—",
        description: "Fraction of equilibrium between Rn-222 and its short-lived progeny indoors. ICRP default 0.4.",
        defaultValue: "0.4",
        pathways: ["radon (all modes)"],
      },
      {
        key: "rn222_inhalation_Sv_per_h_per_Bq_per_m3",
        label: "Rn-222 inhalation DCF",
        unit: "Sv/h per Bq/m³",
        description: "Effective dose per unit radon exposure in air. From ICRP recommendations.",
        defaultValue: "9 × 10⁻⁹",
        pathways: ["radon (all modes)"],
      },
      {
        key: "rn222_conversion_Bq_m3_per_Bq_kg",
        label: "Default K (Rn-222 conversion)",
        unit: "(Bq/m³) / (Bq/kg)",
        description: "Override only affects radon_mode = default. Replaces the generic K=3 assumption.",
        defaultValue: "3.0",
        pathways: ["radon (default mode)"],
      },
    ],
  },
  {
    title: "Occupancy & respiration (per age)",
    keys: [
      {
        key: "occupancy_indoor_fraction.{age}",
        label: "Indoor occupancy fraction",
        unit: "— (0–1)",
        description: "Fraction of the year spent indoors on the contaminated land.",
        defaultValue: "Residential adult: 0.833 · infant: 0.875",
        pathways: ["external", "radon"],
      },
      {
        key: "occupancy_outdoor_fraction.{age}",
        label: "Outdoor occupancy fraction",
        unit: "— (0–1)",
        description: "Fraction of the year spent outdoors on the contaminated land.",
        defaultValue: "Residential adult: 0.104 · infant: 0.125",
        pathways: ["external"],
      },
      {
        key: "active_fraction_indoor.{age}",
        label: "Active-breathing fraction indoors",
        unit: "— (0–1)",
        description: "Of indoor occupancy, fraction spent in the active-breathing state.",
        defaultValue: "Residential adult: 0.125",
        pathways: ["inhalation_dust"],
      },
      {
        key: "passive_fraction_indoor.{age}",
        label: "Passive-breathing fraction indoors",
        unit: "— (0–1)",
        description: "Of indoor occupancy, fraction spent in the passive-breathing state.",
        defaultValue: "Residential adult: 0.708",
        pathways: ["inhalation_dust"],
      },
      {
        key: "active_fraction_outdoor.{age}",
        label: "Active-breathing fraction outdoors",
        unit: "— (0–1)",
        description: "Of outdoor occupancy, fraction spent in the active-breathing state (e.g. gardening).",
        defaultValue: "Residential adult: 0.063",
        pathways: ["inhalation_dust"],
      },
      {
        key: "passive_fraction_outdoor.{age}",
        label: "Passive-breathing fraction outdoors",
        unit: "— (0–1)",
        description: "Of outdoor occupancy, fraction spent in the passive-breathing state.",
        defaultValue: "Residential adult: 0.042",
        pathways: ["inhalation_dust"],
      },
      {
        key: "respiration_active_m3_per_h.{age}",
        label: "Active respiration rate",
        unit: "m³/h",
        description: "Air volume breathed per hour during active activity.",
        defaultValue: "Adult M: 1.456 · adult F: 1.234 · child: ~1.1 · infant: ~0.33",
        pathways: ["inhalation_dust"],
      },
      {
        key: "respiration_passive_m3_per_h.{age}",
        label: "Passive respiration rate",
        unit: "m³/h",
        description: "Air volume breathed per hour during rest/passive activity.",
        defaultValue: "Adult M: 0.485 · adult F: 0.411 · child: ~0.4 · infant: ~0.12",
        pathways: ["inhalation_dust"],
      },
    ],
  },
  {
    title: "Soil ingestion & skin (per age)",
    keys: [
      {
        key: "soil_ingestion_kg_per_y.{age}",
        label: "Inadvertent soil ingestion rate",
        unit: "kg/y",
        description: "Mass of soil/dust unintentionally swallowed per year.",
        defaultValue: "Residential infant: 0.055 · child: 0.037 · adult: 0.022",
        pathways: ["soil_ingestion"],
      },
      {
        key: "skin_soil_loading_indoor_mg_per_cm2.{age}",
        label: "Skin soil loading indoors",
        unit: "mg/cm²",
        description: "Soil mass adhered to exposed skin while indoors.",
        defaultValue: "0.06",
        pathways: ["skin"],
      },
      {
        key: "skin_soil_loading_outdoor_mg_per_cm2.{age}",
        label: "Skin soil loading outdoors",
        unit: "mg/cm²",
        description: "Soil mass adhered to exposed skin while outdoors (typically much higher).",
        defaultValue: "Residential: 0.3–1.0",
        pathways: ["skin"],
      },
      {
        key: "skin_contact_fraction_indoor.{age}",
        label: "Skin-contact fraction indoors",
        unit: "— (0–1)",
        description: "Fraction of indoor time with skin in contact with contaminated soil/dust.",
        defaultValue: "0.5",
        pathways: ["skin"],
      },
      {
        key: "skin_contact_fraction_outdoor.{age}",
        label: "Skin-contact fraction outdoors",
        unit: "— (0–1)",
        description: "Fraction of outdoor time with skin in contact with contaminated soil.",
        defaultValue: "0.178–0.5",
        pathways: ["skin"],
      },
      {
        key: "skin_exposed_fraction_indoor.{age}",
        label: "Skin exposed fraction indoors",
        unit: "— (0–1)",
        description: "Fraction of total skin area exposed (not covered by clothing) while indoors.",
        defaultValue: "Adult: 0.33 · child: 0.22",
        pathways: ["skin"],
      },
      {
        key: "skin_exposed_fraction_outdoor.{age}",
        label: "Skin exposed fraction outdoors",
        unit: "— (0–1)",
        description: "Fraction of total skin area exposed while outdoors.",
        defaultValue: "Adult: 0.26 · child: 0.15",
        pathways: ["skin"],
      },
    ],
  },
  {
    title: "Produce pathway",
    keys: [
      {
        key: "body_weight_kg.{sex}.{age}",
        label: "Body weight",
        unit: "kg",
        description: "Used to scale per-kg-body-weight consumption rates into per-year consumption.",
        defaultValue: "Adult M: 81 · adult F: 68 · child: 37 · infant: 11",
        pathways: ["produce"],
      },
      {
        key: "soil_to_plant_cf.{element}",
        label: "Soil-to-plant transfer factor CF_veg",
        unit: "Bq/kg-fresh-veg per Bq/kg-dry-soil",
        description: "Element-specific concentration factor. Ranges from ~4×10⁻⁴ (Pu) to ~5.6 (H tritium).",
        defaultValue: "See data/elements.json",
        pathways: ["produce"],
      },
      {
        key: "home_fraction.{crop}",
        label: "Home fraction per crop",
        unit: "— (0–1)",
        description: "Fraction of this crop eaten by the receptor that came from the contaminated site.",
        defaultValue: "0.51–0.92",
        pathways: ["produce"],
      },
      {
        key: "soil_loading_kg_dw_per_kg_fw.{crop}",
        label: "Soil loading on vegetable",
        unit: "kg dry soil per kg fresh veg",
        description: "Adherent soil when eaten (root veg > leafy veg).",
        defaultValue: "1e-4 to 1e-3",
        pathways: ["produce"],
      },
    ],
  },
];

const COMMON_KEYS: Array<{ key: string; label: string; help: string; sample: string; unit: string }> = [
  {
    key: "dust_loading_kg_per_m3",
    label: "Respirable dust loading",
    unit: "kg/m³",
    help: "Airborne respirable dust concentration. Default 5×10⁻⁸.",
    sample: "1e-7",
  },
  {
    key: "fraction_indoor_dust_from_local_soil",
    label: "Fraction of indoor dust from local soil",
    unit: "—",
    help: "0.0–1.0. Default 0.75 for residential.",
    sample: "0.5",
  },
  {
    key: "shielding_factor",
    label: "Building shielding factor",
    unit: "—",
    help: "Override the selected building's γ shielding. 0 = none, 1 = full.",
    sample: "0.5",
  },
  {
    key: "rn222_emanation_fraction",
    label: "Rn-222 emanation fraction (α)",
    unit: "—",
    help: "Fraction of Rn released from Ra-226 decay. Default 0.2.",
    sample: "0.15",
  },
  {
    key: "rn222_effective_diffusion_m2_per_s",
    label: "Rn-222 effective diffusion D_e",
    unit: "m²/s",
    help: "Site-specific radon only. Default 2×10⁻⁶.",
    sample: "1e-6",
  },
  {
    key: "building_rn222_ventilation_rate_per_s",
    label: "Building ventilation rate λ_v",
    unit: "s⁻¹",
    help: "Site-specific radon only. Default 8.33×10⁻⁵.",
    sample: "2.5e-4",
  },
  {
    key: "soil_ingestion_kg_per_y.adult",
    label: "Soil ingestion (adult)",
    unit: "kg/y",
    help: "Residential adult default 0.022 kg/y.",
    sample: "0.05",
  },
  {
    key: "soil_ingestion_kg_per_y.infant",
    label: "Soil ingestion (infant)",
    unit: "kg/y",
    help: "Residential infant default 0.055 kg/y.",
    sample: "0.1",
  },
];

export function OverridesEditor({ value, onChange }: Props) {
  const [customKey, setCustomKey] = useState("");
  const [customValue, setCustomValue] = useState("");
  const [indexOpen, setIndexOpen] = useState(false);
  const [indexSearch, setIndexSearch] = useState("");

  const setKey = (key: string, raw: string) => {
    const n = Number(raw);
    const next = { ...value };
    if (raw === "") delete next[key];
    else if (!Number.isNaN(n)) next[key] = n;
    onChange(next);
  };

  const removeKey = (key: string) => {
    const next = { ...value };
    delete next[key];
    onChange(next);
  };

  const addCustom = () => {
    const k = customKey.trim();
    const n = Number(customValue);
    if (!k || Number.isNaN(n)) return;
    onChange({ ...value, [k]: n });
    setCustomKey("");
    setCustomValue("");
  };

  const customKeys = Object.keys(value).filter((k) => !COMMON_KEYS.some((c) => c.key === k));

  const filteredGroups = indexSearch.trim()
    ? KEY_GROUPS.map((g) => ({
        ...g,
        keys: g.keys.filter((k) => {
          const q = indexSearch.toLowerCase();
          return (
            k.key.toLowerCase().includes(q) ||
            k.label.toLowerCase().includes(q) ||
            k.description.toLowerCase().includes(q)
          );
        }),
      })).filter((g) => g.keys.length > 0)
    : KEY_GROUPS;

  return (
    <div className="space-y-3 rounded border border-slate-200 p-3">
      <div className="flex items-center gap-2">
        <h4 className="text-sm font-semibold">Per-parameter overrides</h4>
        <InfoTooltip
          content={
            <span>
              Replace library default values for this assessment only. Keys are hierarchical (e.g. <code>soil_ingestion_kg_per_y.adult</code>). Use the Key reference below to see every available key, its unit, and default.
            </span>
          }
        />
      </div>

      <ul className="space-y-2">
        {COMMON_KEYS.map((c) => (
          <li key={c.key} className="flex items-center gap-2 text-sm">
            <label className="w-72 flex items-center gap-1" htmlFor={`ov-${c.key}`}>
              {c.label}
              <InfoTooltip content={c.help} />
            </label>
            <input
              id={`ov-${c.key}`}
              type="number"
              step="any"
              value={c.key in value ? value[c.key] : ""}
              placeholder={`e.g. ${c.sample}`}
              onChange={(e) => setKey(c.key, e.target.value)}
              className="w-32 rounded border border-slate-300 px-2 py-1"
            />
            <span className="text-xs text-slate-500 w-16">{c.unit}</span>
          </li>
        ))}
      </ul>

      {customKeys.length > 0 && (
        <div>
          <div className="text-xs font-semibold text-slate-600">Other overrides</div>
          <ul className="mt-1 space-y-1 text-sm">
            {customKeys.map((k) => {
              const ref = findKeyRef(k);
              return (
                <li key={k} className="flex items-center gap-2">
                  <code className="flex-1 truncate">{k}</code>
                  <input
                    type="number"
                    step="any"
                    value={value[k]}
                    onChange={(e) => setKey(k, e.target.value)}
                    className="w-32 rounded border border-slate-300 px-2 py-1"
                  />
                  <span className="w-16 text-xs text-slate-500">{ref?.unit ?? ""}</span>
                  <button
                    type="button"
                    onClick={() => removeKey(k)}
                    className="text-red-600 hover:underline"
                    aria-label={`Remove ${k}`}
                  >
                    ×
                  </button>
                </li>
              );
            })}
          </ul>
        </div>
      )}

      <div className="flex items-center gap-2 text-sm">
        <input
          type="text"
          placeholder="Custom key (e.g. occupancy_indoor_fraction.adult)"
          value={customKey}
          onChange={(e) => setCustomKey(e.target.value)}
          className="flex-1 rounded border border-slate-300 px-2 py-1 font-mono text-xs"
        />
        <input
          type="number"
          step="any"
          placeholder="Value"
          value={customValue}
          onChange={(e) => setCustomValue(e.target.value)}
          className="w-28 rounded border border-slate-300 px-2 py-1"
        />
        <button
          type="button"
          onClick={addCustom}
          className="rounded border border-slate-300 bg-white px-3 py-1 text-sm hover:bg-slate-50"
        >
          Add
        </button>
      </div>

      {/* Key reference index */}
      <div className="mt-2 rounded border border-slate-200 bg-slate-50">
        <button
          type="button"
          onClick={() => setIndexOpen(!indexOpen)}
          className="flex w-full items-center justify-between px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100"
          aria-expanded={indexOpen}
        >
          <span className="flex items-center gap-2">
            <span>{indexOpen ? "▾" : "▸"}</span>
            Key reference ({KEY_GROUPS.reduce((n, g) => n + g.keys.length, 0)} keys across {KEY_GROUPS.length} groups)
          </span>
          <span className="text-xs text-slate-500">click to open</span>
        </button>
        {indexOpen && (
          <div className="border-t border-slate-200 bg-white p-3">
            <input
              type="text"
              placeholder="Filter — search by key, label, or description…"
              value={indexSearch}
              onChange={(e) => setIndexSearch(e.target.value)}
              className="mb-3 w-full rounded border border-slate-300 px-2 py-1 text-sm"
            />
            <p className="mb-3 text-xs text-slate-600">
              <code>{"{age}"}</code> expands to <code>infant</code>, <code>child</code>, or <code>adult</code>.{" "}
              <code>{"{sex}"}</code> expands to <code>male</code> or <code>female</code>.{" "}
              <code>{"{element}"}</code> is a chemical symbol (Cs, Pu, Ra, …). <code>{"{crop}"}</code> is one of the crop names in <code>data/consumption.json</code>.
              Click a key to copy it into the custom-key input.
            </p>
            <div className="space-y-4">
              {filteredGroups.map((g) => (
                <div key={g.title}>
                  <h5 className="text-sm font-semibold text-rclea-900">{g.title}</h5>
                  <ul className="mt-1 divide-y divide-slate-100">
                    {g.keys.map((k) => (
                      <li key={k.key} className="py-1.5 text-xs">
                        <div className="flex items-start gap-2">
                          <button
                            type="button"
                            onClick={() => setCustomKey(k.key)}
                            className="font-mono text-rclea-700 hover:text-rclea-900 hover:underline"
                            title="Click to fill custom-key input"
                          >
                            {k.key}
                          </button>
                          <span className="text-slate-400">·</span>
                          <span className="font-medium">{k.label}</span>
                          {k.unit && (
                            <span className="rounded bg-slate-100 px-1.5 text-[10px] font-medium text-slate-700">
                              {k.unit}
                            </span>
                          )}
                        </div>
                        <div className="ml-1 mt-0.5 text-slate-700">{k.description}</div>
                        <div className="ml-1 mt-0.5 text-slate-500">
                          <strong>Default:</strong> {k.defaultValue} ·{" "}
                          <strong>Pathways:</strong> {k.pathways.join(", ")}
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
              {filteredGroups.length === 0 && (
                <div className="text-center text-sm text-slate-500">
                  No keys match "{indexSearch}".
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function findKeyRef(key: string): KeyRef | undefined {
  for (const g of KEY_GROUPS) {
    for (const k of g.keys) {
      // Match literal keys directly
      if (k.key === key) return k;
      // Match template keys (e.g. "soil_ingestion_kg_per_y.{age}" vs user's "soil_ingestion_kg_per_y.adult")
      if (k.key.includes("{")) {
        const pattern = new RegExp(
          "^" + k.key.replace(/\./g, "\\.").replace(/\{[^}]+\}/g, "[A-Za-z0-9_-]+") + "$",
        );
        if (pattern.test(key)) return k;
      }
    }
  }
  return undefined;
}
