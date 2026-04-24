# 2: Radiation Basics

> **Educational use only.** The authors accept no liability for any use of this material.

Before running an assessment it helps to be clear on the units RCLEA uses and why there are so many of them.

## Activity: the becquerel (Bq)

**1 Bq = 1 radioactive decay per second.**

Soil activity concentrations are given in **Bq per kg dry weight**. A typical uncontaminated UK topsoil has ~30–60 Bq/kg of natural K-40 and a few tens of Bq/kg of Ra-226. Contaminated sites may reach thousands or hundreds of thousands of Bq/kg.

## Dose: absorbed, equivalent, and effective

Three different "dose" quantities matter:

| Quantity | Unit | What it measures |
|---|---|---|
| **Absorbed dose** | gray (Gy) = J/kg | Energy deposited per unit mass. Physical quantity. |
| **Equivalent dose** | sievert (Sv) | Absorbed dose weighted by radiation quality factor (α = 20, β/γ = 1). Tissue-level. |
| **Effective dose** | sievert (Sv) | Sum of equivalent doses across organs, weighted by tissue sensitivity. Whole-body metric for stochastic risk. |

RCLEA reports:

- **Total effective dose** in mSv/y (compared against 3 mSv/y)
- **Equivalent skin dose** in mSv/y (compared against 50 mSv/y)

## Dose coefficients

A **dose coefficient (DCF)** converts an intake (Bq) into a committed effective dose (Sv). ICRP publishes age-specific coefficients for each radionuclide and each intake route.

Example — Cs-137 ingestion:

| Age group | DCF (Sv/Bq) |
|---|---|
| Infant (1 y) | 1.2 × 10⁻⁸ |
| Child (10 y) | 1.0 × 10⁻⁸ |
| Adult (20 y) | 1.3 × 10⁻⁸ |

Why is the adult coefficient *higher* than the child's for Cs-137? Because Cs-137 biological half-life lengthens with body size — adults retain it longer. Contrast this with Sr-90, where infants bear a much higher dose per Bq because of active bone growth.

## ICRP age groups

RCLEA uses three age-representative receptors:

- **Infant** (1 year old)
- **Child** (10 years old)
- **Adult** (20 years old — representative of all older age groups)

Each has its own body weight, breathing rate, soil ingestion rate, and consumption rates. The assessment is run for one age at a time; best practice is to repeat for all three and take the **worst case**.

## Exercise: run it yourself

Each `Run` button below executes the **real** RCLEA engine with the parameters shown. Edit the concentration or age, press Run, and see what changes.

```rclea-run
title: Cs-137 in a residential garden — infant
soil_concentrations_Bq_per_kg:
  Cs-137: 500
scenario_id: Residential_with_Home_Grown_Produce
age: infant
building_id: Timber
question: "Which pathway dominates the dose for an infant at 500 Bq/kg Cs-137?"
try_changing: "Raise the Cs-137 concentration to 5000. Does the pathway ranking change, or just the total?"
```

```rclea-run
title: Same site, adult receptor
soil_concentrations_Bq_per_kg:
  Cs-137: 500
scenario_id: Residential_with_Home_Grown_Produce
age: adult
building_id: Timber
question: "Is the adult dose higher or lower than the infant's? Which pathway differs most between the two ages, and why?"
```

*(Hint — infants ingest more soil per kg body weight, so the **soil ingestion** pathway spikes for them even though the Cs-137 ingestion DCF is actually slightly lower than for adults.)*

---

**Next:** Tutorial 3 — Exposure Pathways.
