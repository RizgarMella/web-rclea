# 4: Your First Assessment

> **Educational use only.** The authors accept no liability.

We will walk through a simplified version of the **Appendix D worked example** from CLR-13: a former industrial site being considered for residential redevelopment.

## The scenario

- **Site history:** Until the 1970s, the site housed a small luminiser that used radium paint on aircraft dials. Contamination is predominantly **Ra-226** distributed to ~1 m depth.
- **Proposed land use:** Residential with private gardens. Houses to be timber-framed.
- **Soil sampling** gave a mean Ra-226 activity of **2,500 Bq/kg** and U-238 of **100 Bq/kg**. No significant Pb-210 above background is assumed here for simplicity.
- **Question:** Would the redevelopment cause a significant possibility of significant harm to future residents?

## Step 1: Pick the most sensitive receptor

Infants receive the highest dose for most internal pathways (especially soil ingestion), so start with an **infant** receptor and only broaden if needed.

## Step 2: Run the screening assessment

Click **Run** below to execute the actual engine with these inputs.

```rclea-run
title: Appendix D — radium site, residential, infant receptor
soil_concentrations_Bq_per_kg:
  Ra-226: 2500
  U-238: 100
scenario_id: Residential_with_Home_Grown_Produce
age: infant
building_id: Timber
question: "Total dose compared with the 3 mSv/y criterion — is it below, near, or far above?"
```

## Step 3: Read the pathway breakdown

You will see something like (indicative — exact numbers depend on model version):

| Pathway | Dose (mSv/y) |
|---|---:|
| Whole-body external irradiation | ~6.6 |
| Inadvertent soil ingestion | ~0.13 |
| Inhalation of resuspended dust | ~0.015 |
| Skin equivalent (β+γ) | ~0.008 |
| Consumption of home-grown produce | ~0.018 |
| **Indoor Rn-222** | **~50–70** |
| **Total effective dose** | **~60–80 mSv/y** |

Compare against **3 mSv/y**. The dose is an order of magnitude above the criterion. **Indoor radon is the dominant pathway** — a very common outcome on Ra-226 sites.

## Step 4: Decision and remediation options

At this dose level the answer is unambiguous: **the site cannot be used for residential redevelopment in its current state**. Options include:

1. **Excavation and off-site disposal** of the most contaminated material.
2. **Capping** to break the external / ingestion / dust pathways, combined with building design measures (radon membrane, sub-slab depressurisation) to break the radon pathway.
3. **Change of land use** — park land with no residential dwellings might screen in under the Allotments or Commercial scenarios.

You can test option (3) by running the same contamination as an allotment instead:

```rclea-run
title: Same contamination, reclassified as allotments
soil_concentrations_Bq_per_kg:
  Ra-226: 2500
  U-238: 100
scenario_id: Allotments
age: adult
building_id: Timber
question: "Allotments scenario has no indoor radon pathway. How much does the total dose fall compared with the residential case above? What does that tell you about the radon contribution?"
```

## Step 5: Record the caveats

Always note in any report:

1. **Age group used** (infant vs adult) and rationale.
2. **Default parameters** (3.0 Bq/m³ per Bq/kg Ra→Rn conversion is generic — site-specific measurement can refine this).
3. **The 1-m depth assumption** — deeper-than-1-m contamination is not assessable by RCLEA as-is.
4. **Point sources / discrete objects** are out of scope.
5. **Background radiation is excluded** — do not compare against typical "total" natural dose.

## Reflection

A real Part 2A determination involves more than running a number through a tool. What else would a defensible assessment need? (Site investigation report, conceptual site model, pathway-linkage justification, statutory consultation, probability-weighted risk narrative.) RCLEA is a *screening* tool — it tells you whether it is worth going further.

---

**Next:** Tutorial 5 — Interpreting Results.
