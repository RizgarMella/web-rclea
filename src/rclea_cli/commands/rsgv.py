"""`rclea rsgv` — compute per-isotope Radioactivity in Soil Guideline Values."""
from __future__ import annotations

import csv
import io
import json
import math
from enum import Enum
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from rclea_core import AgeGroup, RadonMode, Sex, compute_rsgvs, load_dataset
from rclea_cli.commands._shared import parse_iso, parse_overrides

app = typer.Typer(invoke_without_command=True, help="Compute per-isotope Radioactivity in Soil Guideline Values (RSGVs).")
console = Console()


class OutputFormat(str, Enum):
    TABLE = "table"
    CSV = "csv"
    JSON = "json"


@app.callback(invoke_without_command=True)
def main(
    scenario: Annotated[
        str,
        typer.Option("--scenario", help="Scenario id (see `rclea scenarios list`)."),
    ] = "Residential_with_Home_Grown_Produce",
    age: Annotated[AgeGroup, typer.Option("--age")] = AgeGroup.ADULT,
    sex: Annotated[Sex, typer.Option("--sex")] = Sex.MALE,
    building: Annotated[str, typer.Option("--building")] = "Timber",
    radon_mode: Annotated[RadonMode, typer.Option("--radon-mode")] = RadonMode.DEFAULT,
    override: Annotated[
        list[str] | None,
        typer.Option("--override", help="KEY=VALUE, repeatable."),
    ] = None,
    site_iso: Annotated[
        list[str] | None,
        typer.Option(
            "--site-iso",
            help="Your site's measured Bq/kg, e.g. --site-iso Cs-137=250. "
            "When given, the output table adds a 'your site' column and a status flag.",
        ),
    ] = None,
    output_format: Annotated[
        OutputFormat,
        typer.Option("--format", help="table | csv | json"),
    ] = OutputFormat.TABLE,
) -> None:
    """For each radionuclide, compute the Bq/kg soil concentration that would alone produce
    3 mSv/y under the selected scenario and receptor."""
    overrides = parse_overrides(override)
    site = parse_iso(site_iso or [])

    report = compute_rsgvs(
        scenario_id=scenario,
        age=age,
        sex=sex,
        building_id=building,
        radon_mode=radon_mode,
        overrides=overrides,
    )

    rows: list[dict[str, object]] = []
    for iso_id, rsgv in report.rsgvs_Bq_per_kg.items():
        row: dict[str, object] = {
            "isotope": iso_id,
            "rsgv_Bq_per_kg": rsgv,
        }
        if iso_id in site:
            row["site_Bq_per_kg"] = site[iso_id]
            row["ratio_site_over_rsgv"] = (
                site[iso_id] / rsgv if rsgv > 0 and math.isfinite(rsgv) else None
            )
        rows.append(row)

    if output_format == OutputFormat.JSON:
        console.print_json(data={"report": report.model_dump(), "table": rows})
        return

    if output_format == OutputFormat.CSV:
        buf = io.StringIO()
        writer = csv.writer(buf)
        cols = ["isotope", "rsgv_Bq_per_kg"]
        if site:
            cols += ["site_Bq_per_kg", "ratio_site_over_rsgv"]
        writer.writerow(cols)
        for row in rows:
            writer.writerow([row.get(c, "") for c in cols])
        console.print(buf.getvalue(), soft_wrap=True, highlight=False, end="")
        return

    # Default: pretty table
    table = Table(
        title=f"RSGVs — {report.scenario_label} / {age.value} / {sex.value} / {building} / radon={radon_mode.value}  (criterion {report.effective_dose_criterion_mSv_per_y} mSv/y)",
    )
    table.add_column("Isotope", style="cyan")
    table.add_column("RSGV (Bq/kg)", justify="right", style="magenta")
    if site:
        table.add_column("Your site (Bq/kg)", justify="right")
        table.add_column("Site / RSGV", justify="right")
        table.add_column("Status", justify="center")

    for row in rows:
        rsgv = row["rsgv_Bq_per_kg"]
        rsgv_str = "∞" if math.isinf(rsgv) else f"{rsgv:.3g}"  # type: ignore[arg-type]
        cells: list[str] = [str(row["isotope"]), rsgv_str]
        if site:
            site_val = row.get("site_Bq_per_kg")
            ratio = row.get("ratio_site_over_rsgv")
            if site_val is None:
                cells += ["—", "—", "—"]
            else:
                cells.append(f"{site_val:g}")
                if ratio is None:
                    cells += ["—", "N/A"]
                else:
                    if ratio >= 1.0:
                        status = "[red]ABOVE[/red]"
                    elif ratio >= 0.1:
                        status = "[yellow]near[/yellow]"
                    else:
                        status = "[green]below[/green]"
                    cells += [f"{ratio:.2g}", status]
        table.add_row(*cells)

    console.print(table)
    if site:
        console.print(
            f"\n[dim]Status rule: above=ratio≥1.0, near=≥0.1, below=<0.1. "
            f"Educational only — not a regulatory finding.[/dim]"
        )
