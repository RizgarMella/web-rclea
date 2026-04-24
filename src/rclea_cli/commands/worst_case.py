"""`rclea worst-case` — run all scenario/building/age/sex combinations and find the worst."""
from __future__ import annotations

from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from rclea_core import RadonMode, find_worst_case
from rclea_cli.commands._shared import parse_iso, parse_overrides

app = typer.Typer(invoke_without_command=True, help="Find the worst-case (scenario × building × age × sex) dose for a given site.")
console = Console()


@app.callback(invoke_without_command=True)
def main(
    iso: Annotated[
        list[str] | None,
        typer.Option("--iso", help="Inline isotope=conc, e.g. --iso Cs-137=1000. Repeatable."),
    ] = None,
    fraction: Annotated[float, typer.Option("--fraction")] = 1.0,
    radon_mode: Annotated[RadonMode, typer.Option("--radon-mode")] = RadonMode.DEFAULT,
    radon_measured: Annotated[
        float | None,
        typer.Option("--radon-measured", help="Measured indoor Rn-222 in Bq/m³. Requires --radon-mode measured."),
    ] = None,
    override: Annotated[
        list[str] | None,
        typer.Option("--override", help="KEY=VALUE, repeatable. See README §Data reference → Overrides."),
    ] = None,
    full_table: Annotated[
        bool,
        typer.Option("--full-table", help="Print every combination (default: top 10 only)."),
    ] = False,
) -> None:
    """Compute dose across every valid combination and report the maximum."""
    if not iso:
        raise typer.BadParameter("Provide at least one --iso ID=VALUE.")
    soil = parse_iso(iso)
    overrides = parse_overrides(override)

    report = find_worst_case(
        soil_concentrations_Bq_per_kg=soil,
        fraction_land_contaminated=fraction,
        radon_mode=radon_mode,
        measured_rn222_Bq_per_m3=radon_measured,
        overrides=overrides,
    )

    console.print(f"\n[bold]Soil:[/bold] {soil}")
    console.print(
        f"[bold]Radon mode:[/bold] {radon_mode.value}"
        + (f" (measured {radon_measured} Bq/m³)" if radon_measured is not None else "")
    )
    console.print(f"[bold]Fraction contaminated:[/bold] {fraction:.2f}")

    w = report.worst
    colour = "red" if w.exceeds_effective_criterion else "green"
    console.print(
        f"\n[bold]Worst case:[/bold] "
        f"[{colour}]{w.total_effective_dose_mSv_per_y:.4g} mSv/y[/{colour}]  "
        f"({w.scenario_label} / {w.building_id} / {w.age.value} / {w.sex.value})"
    )
    console.print(f"[bold]Criterion:[/bold] {report.effective_dose_criterion_mSv_per_y} mSv/y")

    shown = report.entries if full_table else report.entries[:10]
    table = Table(title=f"Top {len(shown)} of {len(report.entries)} combinations (sorted)")
    table.add_column("Scenario", style="cyan")
    table.add_column("Building")
    table.add_column("Age")
    table.add_column("Sex")
    table.add_column("Dose (mSv/y)", justify="right", style="magenta")
    table.add_column("> 3 mSv/y?", justify="center")
    for e in shown:
        table.add_row(
            e.scenario_label,
            e.building_id,
            e.age.value,
            e.sex.value,
            f"{e.total_effective_dose_mSv_per_y:.4g}",
            "[red]yes[/red]" if e.exceeds_effective_criterion else "[green]no[/green]",
        )
    console.print(table)
    if not full_table and len(report.entries) > 10:
        console.print(f"[dim]({len(report.entries) - 10} more rows — pass --full-table to see all)[/dim]")
