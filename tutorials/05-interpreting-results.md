# 5: Interpreting Results

> **Educational use only.** The authors accept no liability.

Getting a number out of RCLEA is easy. Knowing what it means — and what it *doesn't* mean — is harder.

## The three traffic lights

Compare the total effective dose against 3 mSv/y:

| Band | Interpretation |
|---|---|
| **< ~0.3 mSv/y (10% of criterion)** | Clearly below threshold. The linkage is very unlikely to cause significant harm. Generally no further assessment needed. |
| **0.3 – 3 mSv/y** | Below threshold, but within an order of magnitude. Worth sanity-checking assumptions before accepting. |
| **≥ 3 mSv/y** | Screening threshold exceeded. Does **not** automatically mean the land is contaminated — it means a tier-2 / tier-3 assessment is warranted: refine parameters with site-specific data, consider probability of exposure, consult a specialist. |

## Why conservative defaults matter

RCLEA is deliberately **cautious**:

- Fraction of land contaminated defaults to **1.0** (whole site).
- Soil depth is uniform to 1 m.
- Exposure durations are at the high end of plausible.
- Building shielding is minimal (timber default).
- Contamination fraction of indoor dust from local soil is high (0.75).

This means a dose **at** or **slightly above** 3 mSv/y often drops well below after realistic refinements. Before deciding a site is contaminated, the guidance requires you to check whether the default assumptions genuinely apply.

## Sensitivity questions to ask

After a run, interrogate the result:

1. **Which pathway dominates?** If it is radon — is Ra-226 actually present at that concentration, and is the default 3 Bq/m³-per-Bq/kg conversion appropriate for *this* soil and building? If external — is the hot-spot really uniformly distributed?
2. **Which isotope dominates?** Analyse whether its DCF is being used correctly (ingestion vs inhalation — is the airborne pathway really plausible indoors?).
3. **Is the age group representative?** Commercial land would never be occupied by an infant. Residential land always is.
4. **Is fraction contaminated = 1.0 realistic?** Patchy distributions can be handled by reducing `f_contam` to the time-averaged exposed fraction.

## Skin dose

If the skin equivalent dose approaches 50 mSv/y, it is usually because of a β-emitter like Sr-90 or Pm-147 at very high concentration. For almost all real sites, skin dose is a small fraction of the criterion — but keep an eye on it for legacy β-contamination.

## When *not* to use the RCLEA result

- **Emergency or accidental releases** — RCLEA assumes stable exposure over a year. Short-term events need different methodology (NPEG, etc.).
- **Discrete radioactive objects / hot particles** — a single shard doesn't fit the "uniform Bq/kg" model. Probability of encounter × dose-if-encountered is the right framework.
- **Migration to groundwater or surface water** — RCLEA assesses direct exposure; contaminant transport is out of scope. Use CSM tools (LandSim, ConSim) separately.
- **Radiological worker exposure** — IRR17 and occupational radiation protection are separate regulatory frameworks.

## A note on uncertainty

The tool reports point estimates only. Real radiological assessments in a regulatory setting would typically accompany point estimates with:

- **Bounding calculations** (min/max parameter sets)
- **Sensitivity analysis** (tornado plots for key parameters)
- **Narrative justification** for each assumption departed from default

This educational remake deliberately does **not** implement Monte Carlo or probabilistic analysis — those belong in the specialist toolkit (e.g. the Environment Agency's more detailed RCLEA-Plus or bespoke implementations).

## Exercise

Start with the Appendix D contamination profile and the infant receptor, but imagine the contamination is only in a small corner of the garden — `fraction_land_contaminated = 0.10`.

```rclea-run
title: Appendix D with 10% patchy contamination
soil_concentrations_Bq_per_kg:
  Ra-226: 2500
  U-238: 100
scenario_id: Residential_with_Home_Grown_Produce
age: infant
building_id: Timber
fraction_land_contaminated: 0.10
question: "Is the total still above 3 mSv/y? Which pathway now dominates? What does this tell you about remediation priorities?"
try_changing: "Gradually lower the fraction until the total drops below 3 mSv/y. That's the fraction at which conservative screening stops flagging the site."
```

Note how the `fraction` multiplier scales all pathways linearly — the dominant pathway stays dominant, but the threshold comparison flips. This is why in real assessments, understanding the *spatial* distribution of contamination matters as much as the total inventory.

---

**Next:** Tutorial 6 — Legislation & Stakeholders.
