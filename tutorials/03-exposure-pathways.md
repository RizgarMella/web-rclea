# 3: Exposure Pathways

> **Educational use only.** The authors accept no liability.

RCLEA computes dose from six pathways. Understanding what each captures — and when each matters — is the core of radiological risk thinking.

## 1. Whole-body external irradiation

**Mechanism.** Gamma-emitting radionuclides in the soil irradiate people standing or living on that soil. The DCF converts soil activity concentration into an annual effective dose rate assuming continuous exposure at 1 Bq/m³.

**Formula (simplified):**

```
D_ext = Σᵢ  Cᵢ × ρ_B × DCF_ext,i × [O_in × (1 − SF) + O_out] × f_contam
```

- `Cᵢ`: soil concentration of isotope *i* (Bq/kg)
- `ρ_B`: soil bulk density (1400 kg/m³ default)
- `DCF_ext,i`: external dose coefficient (Sv/y per Bq/m³)
- `O_in, O_out`: fractional indoor / outdoor occupancy over contaminated land
- `SF`: building shielding factor (0.0 timber, 0.9 brick/concrete)
- `f_contam`: fraction of land that is contaminated

**Matters for:** strong gamma-emitters: Co-60, Cs-137, Cs-134, Eu-152/154, Ra-226, Nb-94, Ac-227.

## 2. Inadvertent soil ingestion

**Mechanism.** Especially young children mouth dirty hands, toys, food. Adults swallow dust indoors. I_soil (kg soil/y) is age- and land-use-specific.

**Formula:** `D_ing = Σᵢ Cᵢ × I_soil × DCF_ing,i(age) × f_contam`

**Matters for:** all internal emitters, but especially α-emitters that have huge ingestion DCFs for infants (Pu-239, Am-241, Ra-226, Th isotopes).

## 3. Inhalation of resuspended dust

**Mechanism.** Wind, foot traffic, gardening re-suspends contaminated soil particles into breathable air. The dust concentration is taken as 5 × 10⁻⁸ kg/m³ (conservative default). Indoor inhalation is scaled by `F_dust`, the fraction of indoor dust derived from local soil (0.75 default residential).

**Formula:** uses active + passive respiration rates integrated over the year.

**Matters for:** highly toxic α-emitters (Pu, Am, Th, U-233/234/238) — their inhalation DCFs are thousands of times higher than their ingestion DCFs because lung tissue retains particulates.

## 4. Skin equivalent dose (β + γ)

**Mechanism.** Soil on exposed skin gives a local tissue dose. Uses a skin loading (mg/cm²), exposed skin fraction, and a dose rate coefficient from ICRP.

**Matters for:** moderate β-emitters (Sr-90, Y-90 daughter, Cs-137, Pm-147) and some γ-emitters. Compared against a **separate 50 mSv/y criterion** for skin.

## 5. Consumption of home-grown produce

**Mechanism.** Two sub-pathways contribute:
   1. **Root uptake** — plants absorb isotopes from soil. Element-specific concentration factor `CF_veg` (highly variable — H has CF ≈ 5, Pu has CF ≈ 4×10⁻⁴).
   2. **Soil adhering to vegetables** — unwashed carrots, potatoes, leafy salads. Loading `SL_veg` in kg dry soil per kg fresh veg.

**Formula:**

```
D_prod = Σᵢ Σ_crops  Cᵢ × (CF_veg,element + SL_veg,crop) × CR(age,crop) × BW × HF(crop) × DCF_ing,i(age) × f_contam
```

**Matters for:** mobile, plant-accumulating isotopes — H-3 (CF = 5.6!), C-14, Cs-137, Sr-90, I-129, Tc-99, Se-79.

## 6. Indoor Rn-222

**Mechanism.** Ra-226 decays to Rn-222, a noble gas that diffuses out of soil and accumulates in poorly ventilated buildings. The default assumption: 1 Bq/kg Ra-226 in soil → 3 Bq/m³ indoor Rn-222 at equilibrium. With a very low DCF (9 × 10⁻⁹ Sv/h per Bq/m³) but many indoor hours (7000+ hours/year residential), radon often dominates the total dose when Ra-226 is present.

**Matters for:** Ra-226 (and hence any site with U-series contamination — old luminiser sites, mine tailings, shale residues).

## Exercise: which pathway dominates?

Three contaminants, same concentration order of magnitude, same scenario — run each one and compare the pathway breakdowns.

```rclea-run
title: Caesium-137 — a γ-emitter
soil_concentrations_Bq_per_kg:
  Cs-137: 5000
scenario_id: Residential_with_Home_Grown_Produce
age: adult
building_id: Timber
question: "Which pathway dominates?"
try_changing: "Change the building to Concrete/Brick. How much does the dominant pathway drop?"
```

```rclea-run
title: Plutonium-239 — an α-emitter
soil_concentrations_Bq_per_kg:
  Pu-239: 100
scenario_id: Residential_with_Home_Grown_Produce
age: adult
building_id: Timber
question: "Pu-239 at a much lower concentration. Which pathway now dominates? Why does inhalation matter so much more for α than for γ?"
```

```rclea-run
title: Radium-226 — invites the radon problem
soil_concentrations_Bq_per_kg:
  Ra-226: 1000
scenario_id: Residential_with_Home_Grown_Produce
age: adult
building_id: Timber
question: "What dominates? Why does this only happen for isotopes in the U/Th decay chains?"
try_changing: "Switch the scenario to Allotments. The radon pathway disappears — why?"
```

You should see:
- **Cs-137**: dominated by external γ (no radon, modest internal dose).
- **Pu-239**: dominated by inhalation (α-emitter, huge lung DCF) and — for adults who eat vegetables — produce.
- **Ra-226**: dominated by indoor radon (by a wide margin).

This is why the six pathways aren't optional decoration — each captures a different physical mechanism and different isotopes dominate different pathways.

---

**Next:** Tutorial 4 — Running your first full assessment.
