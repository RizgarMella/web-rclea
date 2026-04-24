# 6: Legislation and Stakeholders

> **Educational use only.** The authors accept no liability. Legal positions change; always consult current official guidance before acting.

This final tutorial maps who does what, and why RCLEA sits where it does in the regulatory landscape.

## The statutory stack: England

```
European legal framework
 └─ Council Directive 2013/59/Euratom (BSSD)
     └─ UK transposition:
         └─ Environmental Protection Act 1990, Part 2A (as amended)
             ├─ Radioactive Contaminated Land (Enabling Powers)
             │  (England) Regulations 2005 (as amended 2010, 2018)
             └─ Statutory Guidance (DEFRA/EA, 2018 consolidated)
                 └─ RCLEA methodology (CRCE-RAD-003-2020, CLR-13)
                     └─ Your assessment  ← you are here
```

Scotland, Wales and Northern Ireland have equivalent but separately made regulations and guidance. The **methodology** (RCLEA, dose coefficients, thresholds) is essentially the same across UK jurisdictions.

## Key definitions under Part 2A

- **Contaminant linkage** = substance (source) + pathway (means of travel) + receptor (person/water body that can be harmed).
- **Significant harm**:
  - Human health: death, serious injury, birth defect, serious physiological or reproductive malfunction. For radiation, quantified via 3 mSv/y effective dose (or 15 mSv/y lens / 50 mSv/y skin).
  - Controlled waters: any pollution of groundwater, or pollution of surface water above background.
- **SPOSH** ("significant possibility of significant harm") — the core test. Requires *both* the capacity to cause significant harm **and** significant probability of it occurring.

## The stakeholder map

### Local Authority

- **Duty to inspect** — must actively seek out potentially contaminated land.
- **Determination** — formally declares land as "contaminated" under Part 2A.
- **Remediation notice** — legally binding order requiring clean-up by the "Class A" (polluter) or "Class B" (current owner) liable party.
- For **radioactive** contaminated land: LA still determines, but acts *with advice from* the Environment Agency, which is the enforcing authority.

### Environment Agency (EA)

- **Enforcing authority** for radioactive contaminated land (replacing the LA for enforcement).
- **Technical advisor** to LAs on radiological assessment.
- **Regulator of radioactive substances** under other regimes (EPR 2016, RSA 1993).
- May **recover costs** of remediation it carries out itself from liable parties.

### UKHSA (formerly Public Health England)

- **Centre for Radiation, Chemical and Environmental Hazards (CRCE)** — publishes the technical principles RCLEA is built on.
- **Public health consultee** for remediation plans.
- Authors the dose coefficient lookups used in RCLEA.

### Secretary of State

- Liable for contamination from **nuclear occurrences** (s. 78F(1A) EPA 1990).
- Issues **statutory guidance** that binds how LAs and the EA interpret Part 2A.

### The liable person (Class A or B)

- **Class A** — the original polluter (who caused or knowingly permitted the substances to be on the land). Primary liability.
- **Class B** — current owner/occupier, in default of a Class A being found and solvent. Only liable in specified circumstances.
- Radiation history matters: pre-1948 contamination may have no identifiable Class A.

## Where does your assessment sit?

Your RCLEA run informs one of three possible conversations:

1. **Internal screening** (a consultant running a sanity check before site investigation). Dose well below 3 mSv/y → generally no further action needed.
2. **Pre-determination engagement** with the LA and EA. If RCLEA is borderline, site-specific refinement or targeted sampling is usually the next step, **before** any formal determination.
3. **Post-determination assessment** (RCLEA is one input to writing the remediation notice). Dose above 3 mSv/y, with other lines of evidence, justifies a remediation requirement.

In any formal use, the assessor takes professional responsibility. The author(s) of this educational tool emphatically do not.

## Outside England

- **Scotland**: equivalent under the **Radioactive Contaminated Land (Scotland) Regulations 2007** (and 2009 amendments). SEPA is the enforcing authority.
- **Wales**: **Radioactive Contaminated Land (Modification of Enactments) (Wales) Regulations 2006**. Natural Resources Wales is the enforcing authority.
- **Northern Ireland**: **Radioactive Contaminated Land Regulations (Northern Ireland) 2006**. NIEA / DAERA.
- **Euratom BSSD** applies to all EU member states; similar three-dose-threshold logic is widespread.

## Final reflection

Why does the law express the threshold as *3 mSv/y* and not simply "any dose"? Because:

1. Natural background varies by location — denying all anthropogenic dose would be absurd.
2. Public exposure limits for **planned** activities are 1 mSv/y; the 3 mSv/y harm threshold is derived from BSSD allowances for "existing exposure situations" where legacy contamination exists.
3. It is a **trigger for action**, not a guarantee of harm. Stochastic cancer risk at 3 mSv/y for a lifetime is small (single-digit percent of baseline) — but significant enough that intervention becomes reasonable.

## You are done: what next?

- Review the methodology documents in `Resouces/` — particularly CRCE-RAD-003-2020 for the technical principles and CLR-13 for the user guide's worked examples.
- Try the **extensibility walkthrough**: add a radionuclide to `data/isotopes.json` and see it appear in both the CLI and the web app, with no code change.
- Cross-check a few of your assessment results against the **Radioactivity in Soil Guideline Values (RSGVs)** tabulated in CRCE-RAD-003-2020's appendix — these are single-isotope screening concentrations for each land use.

---

**End of curriculum.** Thank you for engaging with the material. Now go read the real guidance.
