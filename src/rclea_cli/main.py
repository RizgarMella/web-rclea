"""`rclea` CLI entrypoint."""
from __future__ import annotations

import sys

import typer
from rich.console import Console
from rich.panel import Panel

# Force UTF-8 output on Windows so rich's box-drawing characters don't crash
# cp1252 when stdout is piped. Safe no-op on non-Windows.
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass

from rclea_core import DISCLAIMER_SHORT
from rclea_cli.commands import assess as assess_cmd
from rclea_cli.commands import isotopes as isotopes_cmd
from rclea_cli.commands import rsgv as rsgv_cmd
from rclea_cli.commands import scenarios as scenarios_cmd
from rclea_cli.commands import tutorial as tutorial_cmd
from rclea_cli.commands import worst_case as worst_case_cmd

app = typer.Typer(
    name="rclea",
    help="RCLEA — Radioactively Contaminated Land Exposure Assessment (educational).",
    add_completion=False,
    no_args_is_help=True,
    rich_markup_mode="rich",
)

app.add_typer(assess_cmd.app, name="assess", help="Run a dose assessment.")
app.add_typer(isotopes_cmd.app, name="isotopes", help="Browse the radionuclide catalogue.")
app.add_typer(scenarios_cmd.app, name="scenarios", help="Browse and customise land-use scenarios.")
app.add_typer(tutorial_cmd.app, name="tutorial", help="Interactive learning modules.")
app.add_typer(worst_case_cmd.app, name="worst-case", help="Find the worst-case receptor combination for a given site.")
app.add_typer(rsgv_cmd.app, name="rsgv", help="Compute per-isotope Radioactivity in Soil Guideline Values (RSGVs).")


console = Console()


@app.callback()
def _banner(
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress the educational disclaimer banner."),
) -> None:
    """Print the short disclaimer before every command unless --quiet is given."""
    if quiet:
        return
    console.print(
        Panel(
            DISCLAIMER_SHORT,
            title="[bold yellow]RCLEA — educational use only[/bold yellow]",
            border_style="yellow",
        )
    )


if __name__ == "__main__":
    app()
