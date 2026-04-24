"""`rclea assess` — run a dose assessment."""
from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
import yaml
from rich.console import Console
from rich.table import Table

from rclea_core import (
    AgeGroup,
    AssessmentInput,
    AssessmentMode,
    AssessmentResult,
    RadonMode,
    Sex,
    find_worst_case,
    load_dataset,
    run_assessment,
)
from rclea_cli.commands._shared import parse_iso, parse_overrides

app = typer.Typer(invoke_without_command=True, help="Run a dose assessment.")
console = Console()


EXAMPLE_APPENDIX_D = AssessmentInput(
    soil_concentrations_Bq_per_kg={
        "Ra-226": 2500.0,
        "Pb-210": 2500.0,
        "Po-210": 0.0,  # ignored if Po-210 not in the catalogue
        "U-238": 100.0,
    },
    scenario_id="Residential_with_Home_Grown_Produce",
    age=AgeGroup.INFANT,
    sex=Sex.MALE,
    building_id="Timber",
    fraction_land_contaminated=1.0,
)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    input_file: Annotated[
        Path | None,
        typer.Option("--input", "-i", help="YAML file describing the scenario input."),
    ] = None,
    output_file: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Write the result as JSON to this file."),
    ] = None,
    example: Annotated[
        str | None,
        typer.Option("--example", help="Run a built-in example. Known: 'appendix-d'."),
    ] = None,
    iso: Annotated[
        list[str] | None,
        typer.Option("--iso", help="Inline isotope=conc, e.g. --iso Cs-137=2500. Repeatable."),
    ] = None,
    mode: Annotated[
        AssessmentMode,
        typer.Option(
            "--mode",
            help="'site_specific' uses exact --age/--sex/--building; 'generic' finds the worst combination.",
        ),
    ] = AssessmentMode.SITE_SPECIFIC,
    scenario: Annotated[
        str,
        typer.Option("--scenario", help="Scenario id (see `rclea scenarios list`)."),
    ] = "Residential_with_Home_Grown_Produce",
    age: Annotated[AgeGroup, typer.Option("--age")] = AgeGroup.ADULT,
    sex: Annotated[Sex, typer.Option("--sex")] = Sex.MALE,
    building: Annotated[str, typer.Option("--building")] = "Timber",
    fraction: Annotated[
        float, typer.Option("--fraction", help="Fraction of land contaminated.")
    ] = 1.0,
    radon_mode: Annotated[
        RadonMode,
        typer.Option("--radon-mode", help="How indoor Rn-222 is calculated."),
    ] = RadonMode.DEFAULT,
    radon_measured: Annotated[
        float | None,
        typer.Option(
            "--radon-measured",
            help="Measured indoor Rn-222 (Bq/m³). Used with --radon-mode measured.",
        ),
    ] = None,
    override: Annotated[
        list[str] | None,
        typer.Option(
            "--override",
            help="KEY=VALUE, repeatable. Override library parameters (see README §Overrides).",
        ),
    ] = None,
) -> None:
    """Run an assessment. Supply --input, --example, or --iso."""
    if ctx.invoked_subcommand is not None:
        return
    if example == "appendix-d":
        base = EXAMPLE_APPENDIX_D
        inp = base.model_copy(
            update={
                "radon_mode": radon_mode,
                "measured_rn222_Bq_per_m3": radon_measured,
                "overrides": parse_overrides(override),
            }
        )
    elif input_file is not None:
        inp = _load_input_yaml(input_file)
    elif iso:
        inp = AssessmentInput(
            soil_concentrations_Bq_per_kg=parse_iso(iso),
            scenario_id=scenario,
            age=age,
            sex=sex,
            building_id=building,
            fraction_land_contaminated=fraction,
            radon_mode=radon_mode,
            measured_rn222_Bq_per_m3=radon_measured,
            overrides=parse_overrides(override),
        )
    else:
        raise typer.BadParameter(
            "Provide --input FILE, --example appendix-d, or one or more --iso ID=VALUE."
        )

    if mode == AssessmentMode.GENERIC:
        report = find_worst_case(
            soil_concentrations_Bq_per_kg=inp.soil_concentrations_Bq_per_kg,
            fraction_land_contaminated=inp.fraction_land_contaminated,
            radon_mode=inp.radon_mode,
            measured_rn222_Bq_per_m3=inp.measured_rn222_Bq_per_m3,
            overrides=inp.overrides,
        )
        # Run the worst combination for the full breakdown
        worst_input = inp.model_copy(
            update={
                "scenario_id": report.worst.scenario_id,
                "building_id": report.worst.building_id,
                "age": report.worst.age,
                "sex": report.worst.sex,
            }
        )
        result = run_assessment(worst_input)
        console.print(
            f"\n[bold yellow]Generic mode:[/bold yellow] ran {len(report.entries)} combinations; "
            f"showing the worst: "
            f"{report.worst.scenario_label} / {report.worst.building_id} / "
            f"{report.worst.age.value} / {report.worst.sex.value}"
        )
    else:
        result = run_assessment(inp)

    _render(result)
    if output_file:
        output_file.write_text(result.model_dump_json(indent=2), encoding="utf-8")
        console.print(f"\n[green]Wrote JSON report:[/green] {output_file}")


def _load_input_yaml(path: Path) -> AssessmentInput:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return AssessmentInput.model_validate(raw)


def _render(r: AssessmentResult) -> None:
    inp = r.inputs_echo
    header = (
        f"\n[bold]Scenario:[/bold] {inp.scenario_id} | "
        f"[bold]Age:[/bold] {inp.age.value} | "
        f"[bold]Sex:[/bold] {inp.sex.value} | "
        f"[bold]Building:[/bold] {inp.building_id} | "
        f"[bold]Fraction:[/bold] {inp.fraction_land_contaminated:.2f}"
    )
    if inp.radon_mode != RadonMode.DEFAULT:
        header += f" | [bold]Radon:[/bold] {inp.radon_mode.value}"
        if inp.measured_rn222_Bq_per_m3 is not None:
            header += f" ({inp.measured_rn222_Bq_per_m3} Bq/m³)"
    console.print(header)
    console.print(
        f"\n[bold]Soil concentrations (Bq/kg):[/bold] {inp.soil_concentrations_Bq_per_kg}"
    )
    if inp.overrides:
        console.print(
            f"[bold]Overrides:[/bold] {', '.join(f'{k}={v}' for k, v in inp.overrides.items())}"
        )

    table = Table(title="Dose per pathway")
    table.add_column("Pathway", style="cyan")
    table.add_column("Dose (mSv/y)", justify="right", style="magenta")
    table.add_column("Top contributor", style="yellow")
    for p in r.per_pathway:
        top = max(p.contributing_isotopes.items(), key=lambda kv: kv[1], default=("—", 0.0))
        table.add_row(p.label, f"{p.dose_mSv_per_year:.4g}", f"{top[0]} ({top[1]:.3g})")
    console.print(table)

    crit = r.effective_dose_criterion_mSv_per_y
    eff = r.total_effective_dose_mSv_per_y
    ratio = eff / crit if crit else float("nan")
    colour = "red" if r.exceeds_effective_criterion else "green"
    console.print(
        f"\n[bold]Total effective dose:[/bold] "
        f"[{colour}]{eff:.4g} mSv/y[/{colour}]  "
        f"(criterion {crit} mSv/y — {ratio*100:.1f}% of criterion)"
    )
    if r.safety_margin is not None:
        if r.safety_margin >= 1.0:
            console.print(f"[bold]Safety margin:[/bold] [green]{r.safety_margin:.3g}×[/green]  (site is below the criterion)")
        else:
            console.print(f"[bold]Safety margin:[/bold] [red]{r.safety_margin:.3g}×[/red]  (site is above the criterion)")
    else:
        console.print("[bold]Safety margin:[/bold] undefined (dose is zero)")
    console.print(
        f"[bold]Skin equivalent dose:[/bold] "
        f"{r.total_skin_equivalent_dose_mSv_per_y:.4g} mSv/y  "
        f"(criterion {r.skin_dose_criterion_mSv_per_y} mSv/y)"
    )

    if r.notes:
        console.print("\n[bold]Notes:[/bold]")
        for n in r.notes:
            console.print(f"  • {n}")


@app.command(name="template")
def write_template(path: Path = typer.Argument(Path("scenario.yaml"))) -> None:
    """Write a scenario YAML template to PATH that you can edit and re-run."""
    ds = load_dataset()
    example = {
        "soil_concentrations_Bq_per_kg": {"Cs-137": 500.0, "Ra-226": 100.0},
        "scenario_id": "Residential_with_Home_Grown_Produce",
        "age": "adult",
        "sex": "male",
        "building_id": "Timber",
        "fraction_land_contaminated": 1.0,
        "radon_mode": "default",
        "measured_rn222_Bq_per_m3": None,
        "overrides": {},
    }
    comment = (
        "# RCLEA scenario template. Edit and run with `rclea assess -i scenario.yaml`.\n"
        f"# Valid scenario_id: {list(ds.scenarios)}\n"
        f"# Valid age:         infant | child | adult\n"
        f"# Valid building_id: {list(ds.buildings)}\n"
        "# Valid radon_mode:  default | measured | site_specific\n"
        "# Overrides map is hierarchical; see README §Data reference → Overrides.\n"
    )
    path.write_text(comment + yaml.safe_dump(example, sort_keys=False), encoding="utf-8")
    console.print(f"[green]Template written:[/green] {path}")
