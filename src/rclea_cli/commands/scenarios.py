"""`rclea scenarios` — browse and customise land-use scenarios."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from rclea_core import load_dataset
from rclea_core.models import Scenario

app = typer.Typer(help="Browse and customise land-use scenarios.")
console = Console()


USER_OVERLAY_PATH = Path.home() / ".rclea" / "scenarios.json"


@app.command("list")
def cmd_list() -> None:
    ds = load_dataset()
    t = Table(title="Land-use scenarios")
    t.add_column("ID", style="cyan")
    t.add_column("Label")
    t.add_column("Area (ha)", justify="right")
    t.add_column("Pathways included")
    t.add_column("Source", style="dim")
    user_ids = _user_overlay_ids()
    for s in ds.scenarios.values():
        enabled = [k for k, v in s.pathways.model_dump().items() if v]
        source = "custom" if s.id in user_ids else "library"
        t.add_row(s.id, s.label, f"{s.area_hectares:.1f}", ", ".join(enabled), source)
    console.print(t)
    if user_ids:
        console.print(f"\n[dim]User overlay: {USER_OVERLAY_PATH}[/dim]")


@app.command("show")
def cmd_show(scenario_id: str) -> None:
    ds = load_dataset()
    s = ds.scenarios.get(scenario_id)
    if s is None:
        console.print(f"[red]No scenario with id {scenario_id!r}[/red]")
        raise typer.Exit(code=1)
    console.print(s.model_dump_json(indent=2))


@app.command("template")
def cmd_template(
    path: Annotated[Path, typer.Argument(help="Where to write the JSON template.")] = Path(
        "custom_scenario.json"
    ),
    base: Annotated[
        str,
        typer.Option(
            "--base",
            help="Existing scenario id to use as a starting point (copies all values).",
        ),
    ] = "Residential_with_Home_Grown_Produce",
) -> None:
    """Write a JSON template for a new custom land-use scenario.

    Edit the file, then register it with `rclea scenarios register PATH`.
    """
    ds = load_dataset()
    if base not in ds.scenarios:
        raise typer.BadParameter(f"Unknown --base {base!r}. Known: {list(ds.scenarios)}")
    src = ds.scenarios[base]
    # Deep copy via pydantic round-trip; rename id/label to placeholders for editing.
    out = src.model_dump()
    out["id"] = "my_custom_scenario"
    out["label"] = "My Custom Scenario"
    path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    console.print(f"[green]Template written:[/green] {path}")
    console.print(
        "[dim]Edit the `id`, `label`, `per_age` parameters, `pathways` flags, etc. "
        f"Then run:\n  rclea scenarios register {path}[/dim]"
    )


@app.command("register")
def cmd_register(
    path: Annotated[Path, typer.Argument(help="Path to a scenario JSON file to register.")],
) -> None:
    """Validate a custom scenario JSON and append it to the user overlay.

    The overlay lives at `~/.rclea/scenarios.json`. Registered scenarios become
    selectable in all `rclea` commands and in `rclea scenarios list`.
    """
    raw = json.loads(path.read_text(encoding="utf-8"))
    # Validate against the pydantic model; raises pretty error if malformed.
    scenario = Scenario.model_validate(raw)

    USER_OVERLAY_PATH.parent.mkdir(parents=True, exist_ok=True)
    existing: list[dict] = []
    if USER_OVERLAY_PATH.exists():
        doc = json.loads(USER_OVERLAY_PATH.read_text(encoding="utf-8"))
        existing = doc.get("scenarios", [])

    # Replace if id already registered, else append
    existing = [e for e in existing if e.get("id") != scenario.id]
    existing.append(scenario.model_dump())
    USER_OVERLAY_PATH.write_text(
        json.dumps({"scenarios": existing}, indent=2), encoding="utf-8"
    )
    console.print(
        f"[green]Registered scenario '{scenario.id}' ({scenario.label}) "
        f"into {USER_OVERLAY_PATH}.[/green]"
    )


@app.command("unregister")
def cmd_unregister(scenario_id: str) -> None:
    """Remove a custom scenario from the user overlay."""
    if not USER_OVERLAY_PATH.exists():
        console.print("[yellow]No user overlay present; nothing to remove.[/yellow]")
        return
    doc = json.loads(USER_OVERLAY_PATH.read_text(encoding="utf-8"))
    before = doc.get("scenarios", [])
    after = [s for s in before if s.get("id") != scenario_id]
    if len(after) == len(before):
        console.print(f"[yellow]No custom scenario with id {scenario_id!r}.[/yellow]")
        return
    USER_OVERLAY_PATH.write_text(json.dumps({"scenarios": after}, indent=2), encoding="utf-8")
    console.print(f"[green]Removed custom scenario {scenario_id!r}.[/green]")


def _user_overlay_ids() -> set[str]:
    if not USER_OVERLAY_PATH.exists():
        return set()
    try:
        doc = json.loads(USER_OVERLAY_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return set()
    return {s.get("id") for s in doc.get("scenarios", []) if s.get("id")}
