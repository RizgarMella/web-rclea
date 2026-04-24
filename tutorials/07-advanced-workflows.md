# 7: Advanced Workflows

> **Educational use only.** The authors accept no liability.

The first six lessons covered the engine and the core workflow. This final lesson demonstrates the three workflows that matched the original Excel tool but lived in separate sheets: **worst-case scenario finding**, **Radioactivity in Soil Guideline Values (RSGVs)**, and the **three radon modes**.

## 1. Worst-case scenario — "generic" mode

In the original Excel tool, the `AllDoses` sheet listed every combination of (land use × building × age × sex) for your site concentrations. The `GuidelineValues` sheet then used the worst combination as the reference for decision-making. This is the classic **generic assessment** workflow: you don't yet know which receptor applies, so you find the one who gets the biggest dose and plan around them.

This remake does the same, either from the CLI:

```
rclea assess --iso Ra-226=2500 --mode generic
rclea worst-case --iso Ra-226=2500 --full-table
```

or in the web app by switching the **Calculation mode** radio at the top of the Assess form to **Generic**.

You should see that for sites dominated by Ra-226, the worst receptor is the **infant in a timber-framed residence with a home-grown-produce garden**. Indoor radon dominates; the timber building has no shielding but also no meaningful radon mitigation; infants spend a lot of time indoors; the produce pathway adds a further internal dose.

## 2. Comparing radon modes

The original tool offered three ways to determine the indoor Rn-222 concentration. This remake supports all three — you can select the mode on the Assess tab's **Advanced** disclosure.

**Step A: Default K=3.** This is what every previous tutorial used.

```rclea-run
title: Ra-226 site, default K=3
soil_concentrations_Bq_per_kg:
  Ra-226: 2500
scenario_id: Residential_with_Home_Grown_Produce
age: infant
building_id: Timber
radon_mode: default
question: "Note the total dose. The indoor radon pathway will dominate."
```

**Step B: Site-specific K.** Same site, same receptor, but the K value is computed from the soil emanation/diffusion parameters (α=0.2, D_e=2×10⁻⁶ m²/s) and the building height/ventilation (h=3 m, λ_v=8.33×10⁻⁵ s⁻¹) via the 1-D exhalation model:

```
K = (α × ρ_B × √(D_e × λ_Rn)) / (h × (λ_v + λ_Rn))
```

Under the default parameters this gives K ≈ 2.24 Bq/m³ per Bq/kg, so the site-specific radon dose is about **75 %** of the default-K value.

```rclea-run
title: Ra-226 site, site-specific K
soil_concentrations_Bq_per_kg:
  Ra-226: 2500
scenario_id: Residential_with_Home_Grown_Produce
age: infant
building_id: Timber
radon_mode: site_specific
question: "Total dose should be lower than Step A. Why? (Hint: check the K formula.)"
try_changing: "Use the Overrides editor on the Assess tab to bump the ventilation rate. How low can you drive the radon dose?"
```

**Step C: Measured Rn-222.** If you had an actual indoor radon survey (e.g. 120 Bq/m³), the K-based calculation is bypassed entirely and your measurement is used directly.

```rclea-run
title: Ra-226 site, measured Rn-222 = 120 Bq/m³
soil_concentrations_Bq_per_kg:
  Ra-226: 2500
scenario_id: Residential_with_Home_Grown_Produce
age: infant
building_id: Timber
radon_mode: measured
measured_rn222_Bq_per_m3: 120
question: "Is the resulting dose higher or lower than the K=3 default? What does that tell you about the generic assumption in this case?"
```

Notice: in measured mode, the Ra-226 soil concentration is irrelevant to the radon pathway — the measured value is authoritative. The other Ra-226 pathways (external, ingestion, produce) still depend on the soil concentration.

## 3. Radioactivity in Soil Guideline Values (RSGVs)

The RCLEA `GuidelineValues` sheet answered an inverse question: **if only one isotope were present, what concentration would alone produce 3 mSv/y?** These "RSGVs" are indispensable for screening decisions — if your site's isotope concentration is *well below* its RSGV, you can usually stop worrying.

The CLI:

```
rclea rsgv --scenario Residential_with_Home_Grown_Produce --age infant --format table
rclea rsgv --age infant --site-iso Ra-226=50 --site-iso Cs-137=500
```

The web app: **Guidelines** tab. Choose a scenario and receptor; the table recalculates. If you've typed site concentrations on the Assess tab, they appear here as a ratio + status column.

Characteristic numbers to check:

| Isotope | RSGV (residential infant, default K) | Why |
|---|---|---|
| Ra-226 | ~35 Bq/kg | Radon-dominated; very restrictive |
| Co-60 | ~800 Bq/kg | Strong γ-emitter |
| Cs-137 | ~3 500 Bq/kg | γ-emitter, no radon |
| Pu-239 | ~70 000 Bq/kg | α-emitter, inhalation-limited |
| H-3 | ~100 000 Bq/kg | Mobile in plants but tiny DCF |

Note how wildly the RSGV varies — by **four orders of magnitude**. RSGVs are what let you know *which* isotope on a site deserves attention, even when total activities look similar.

### Shift the scenario

RSGVs are scenario-dependent. Compare:

- **Residential (with produce)** infant receptor: Ra-226 RSGV ≈ 35 Bq/kg.
- **Allotments** adult receptor: Ra-226 RSGV ≈ a thousand-fold higher — allotments don't include the indoor radon pathway and the adult receptor has lower ingestion and soil-contact.

Open the web Guidelines tab and flip the scenario to see this in real time.

## 4. Defining a custom scenario

Real sites aren't always one of the four reference land uses. For assessments where you need to deviate — an unusual occupancy pattern, higher dust loading, non-standard vegetable fraction — you can **clone a shipped scenario and edit its parameters**.

**Web path:** open the **Custom** tab, pick a base scenario, click **Load base parameters**, edit the per-age numbers (e.g. push `occupancy_indoor_fraction.adult` to 0.95 for a city-centre office worker, or `soil_ingestion_kg_per_y.infant` to 0.1 for a rural infant), give the scenario a new id (must start with `custom_`) and label, click **Save**. The new scenario immediately appears in the Scenario dropdown on the Assess tab.

**CLI path:**

```
rclea scenarios template my_scenario.json --base Residential_with_Home_Grown_Produce
# edit the file (id must start with custom_)
rclea scenarios register my_scenario.json
rclea scenarios list   # your scenario now appears as 'custom'
```

The CLI stores the overlay at `~/.rclea/scenarios.json`. The web app stores it in browser `localStorage` — the two are independent (browser scenarios aren't shared with the CLI).

## 5. Per-parameter overrides

For assessments where you don't want a whole new scenario but just need to override one or two values (e.g. site-specific dust loading or a different ventilation rate), use the **Overrides** editor on the Assess tab (Advanced disclosure), or the `--override KEY=VALUE` flag:

```
rclea assess --iso Cs-137=2500 \
    --override dust_loading_kg_per_m3=1e-7 \
    --override shielding_factor=0.5
```

Common override keys:

| Key | Effect | Default |
|---|---|---|
| `dust_loading_kg_per_m3` | Airborne respirable dust | 5 × 10⁻⁸ |
| `fraction_indoor_dust_from_local_soil` | Indoor-dust origin | 0.75 |
| `shielding_factor` | Building γ shielding | per building |
| `rn222_emanation_fraction` | Radon exhalation α | 0.2 |
| `rn222_effective_diffusion_m2_per_s` | Radon diffusion D_e | 2 × 10⁻⁶ |
| `building_rn222_ventilation_rate_per_s` | Ventilation λ_v | 8.33 × 10⁻⁵ |
| `soil_ingestion_kg_per_y.<age>` | Age-specific soil ingestion | varies |
| `occupancy_indoor_fraction.<age>` | Indoor occupancy | varies |

Overrides are applied to the current run only — nothing is persisted. The result's `notes` list records which keys were overridden, so your assessment report always shows when it departed from library values.

## 6. Putting it all together — a full site workflow

1. **Measure** soil concentrations at the site. Enter them on the Assess tab.
2. **Run a generic assessment** (Calculation mode: Generic) to find the worst-case receptor.
3. **Check the RSGVs** (Guidelines tab) to see which single isotopes are driving the dose and whether any are well below their single-isotope screening values.
4. If radon dominates and you have (or can afford) a radon survey, **re-run with `radon_mode: measured`** or site-specific. Usually reduces the total by 20–60 %.
5. If site receptors are non-standard (e.g. part-time occupation, unusual building), **register a custom scenario** and re-run against it.
6. Export the JSON result (`--output report.json` on the CLI) for your records. The disclaimer travels inside the JSON.

This is the full workflow the original Excel tool was designed around — now in two modern platforms.

---

**End of curriculum.** You now know what RCLEA does, how each dose is computed, what the regulatory framework requires, how to interpret a result, how to find worst cases and guideline values, and how to customise the tool for real sites. The rest is practice — and, when it matters, a qualified radiological consultant.
