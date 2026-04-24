"""`rclea isotopes` — browse the catalogue."""
from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from rclea_core import load_dataset

app = typer.Typer(help="Browse the radionuclide catalogue.")
console = Console()


@app.command("list")
def cmd_list() -> None:
    """List all isotopes in the catalogue."""
    ds = load_dataset()
    t = Table(title=f"Radionuclides ({len(ds.isotopes)})")
    t.add_column("ID", style="cyan")
    t.add_column("Element", style="green")
    t.add_column("Ing. Adult (Sv/Bq)", justify="right")
    t.add_column("Inh. Adult (Sv/Bq)", justify="right")
    t.add_column("Ext. (Sv/y / Bq/m³)", justify="right")
    for iso in ds.isotopes.values():
        t.add_row(
            iso.id,
            iso.element,
            f"{iso.ingestion_Sv_per_Bq.get('adult', 0):.2e}",
            f"{iso.inhalation_Sv_per_Bq.get('adult', 0):.2e}",
            f"{iso.external_Sv_per_y_per_Bq_per_m3:.2e}",
        )
    console.print(t)


@app.command("show")
def cmd_show(iso_id: str) -> None:
    """Show full data for one isotope."""
    ds = load_dataset()
    iso = ds.isotopes.get(iso_id)
    if iso is None:
        console.print(f"[red]No isotope with id {iso_id!r}[/red]")
        raise typer.Exit(code=1)
    console.print(iso.model_dump_json(indent=2))
