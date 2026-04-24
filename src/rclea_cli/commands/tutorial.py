"""`rclea tutorial` — interactive learning modules."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

import typer
import yaml
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Confirm
from rich.table import Table

from rclea_core import AssessmentInput, run_assessment
from rclea_core.tutorials import get_tutorial, list_tutorials

app = typer.Typer(help="Interactive learning modules.")
console = Console()

FENCE_RE = re.compile(r"```rclea-run\s*\n(.*?)\n```", re.DOTALL)


@dataclass
class _ProseSection:
    kind: Literal["prose"]
    text: str


@dataclass
class _StepSection:
    kind: Literal["step"]
    spec: dict


_Section = _ProseSection | _StepSection


def _split_sections(markdown: str) -> list[_Section]:
    """Split the markdown into alternating prose and rclea-run step sections."""
    sections: list[_Section] = []
    cursor = 0
    for match in FENCE_RE.finditer(markdown):
        start, end = match.span()
        if start > cursor:
            sections.append(_ProseSection("prose", markdown[cursor:start]))
        try:
            spec = yaml.safe_load(match.group(1)) or {}
            sections.append(_StepSection("step", spec))
        except yaml.YAMLError as exc:
            sections.append(
                _ProseSection("prose", f"\n> _Could not parse interactive step: {exc}_\n")
            )
        cursor = end
    if cursor < len(markdown):
        sections.append(_ProseSection("prose", markdown[cursor:]))
    return sections


def _render_step_prompt(spec: dict) -> None:
    title = spec.get("title", "Interactive step")
    console.print(Panel.fit(f"[bold]>> Interactive step:[/bold] {title}", style="cyan"))
    table = Table.grid(padding=(0, 2))
    table.add_column(style="bold dim")
    table.add_column()
    for key in ("scenario_id", "age", "sex", "building_id", "fraction_land_contaminated"):
        if key in spec:
            table.add_row(key + ":", str(spec[key]))
    if "soil_concentrations_Bq_per_kg" in spec:
        table.add_row(
            "soil (Bq/kg):",
            ", ".join(f"{k}={v}" for k, v in spec["soil_concentrations_Bq_per_kg"].items()),
        )
    console.print(table)


def _render_step_result(spec: dict) -> None:
    input_dict = {
        "soil_concentrations_Bq_per_kg": spec.get("soil_concentrations_Bq_per_kg", {}),
        "scenario_id": spec["scenario_id"],
        "age": spec.get("age", "adult"),
        "sex": spec.get("sex", "male"),
        "building_id": spec.get("building_id", "Timber"),
        "fraction_land_contaminated": spec.get("fraction_land_contaminated", 1.0),
        "radon_mode": spec.get("radon_mode", "default"),
        "measured_rn222_Bq_per_m3": spec.get("measured_rn222_Bq_per_m3"),
        "overrides": spec.get("overrides", {}),
    }
    inp = AssessmentInput.model_validate(input_dict)
    result = run_assessment(inp)

    t = Table(title="Pathway doses (mSv/y)")
    t.add_column("Pathway", style="cyan")
    t.add_column("Dose", justify="right", style="magenta")
    for p in sorted(result.per_pathway, key=lambda r: -r.dose_mSv_per_year):
        t.add_row(p.label, f"{p.dose_mSv_per_year:.4g}")
    console.print(t)
    colour = "red" if result.exceeds_effective_criterion else "green"
    pct = (
        result.total_effective_dose_mSv_per_y
        / result.effective_dose_criterion_mSv_per_y
        * 100.0
    )
    console.print(
        f"[bold]Total effective dose:[/bold] "
        f"[{colour}]{result.total_effective_dose_mSv_per_y:.4g} mSv/y[/{colour}]  "
        f"({pct:.0f}% of 3 mSv/y)"
    )
    if result.notes:
        for n in result.notes:
            console.print(f"  [yellow]note:[/yellow] {n}")


@app.command("list")
def cmd_list() -> None:
    tuts = list_tutorials()
    if not tuts:
        console.print("[yellow]No tutorials found.[/yellow]")
        return
    t = Table(title="Available tutorials")
    t.add_column("Slug", style="cyan")
    t.add_column("Title")
    t.add_column("Steps", justify="right")
    for tut in tuts:
        n_steps = len(FENCE_RE.findall(tut.markdown))
        t.add_row(tut.slug, tut.title, str(n_steps))
    console.print(t)


@app.command("run")
def cmd_run(
    slug: str,
    auto: bool = typer.Option(False, "--auto", help="Run every interactive step without prompting."),
    no_interactive: bool = typer.Option(
        False, "--no-interactive", help="Render prose only; skip interactive steps."
    ),
) -> None:
    """Walk through a tutorial. Interactive steps pause to ask whether to run them."""
    tut = get_tutorial(slug)
    if tut is None:
        console.print(f"[red]No tutorial with slug {slug!r}[/red]")
        raise typer.Exit(code=1)

    for section in _split_sections(tut.markdown):
        if section.kind == "prose":
            # Skip empty sections that only contain whitespace
            if section.text.strip():
                console.print(Markdown(section.text))
            continue

        # Interactive step
        spec = section.spec
        _render_step_prompt(spec)
        if no_interactive:
            console.print("[dim](skipping; --no-interactive)[/dim]\n")
            continue
        if auto or Confirm.ask("Run this step?", default=True):
            try:
                _render_step_result(spec)
            except Exception as exc:  # noqa: BLE001
                console.print(f"[red]Step failed:[/red] {exc}")
        if "question" in spec:
            console.print(f"\n[yellow]Think about:[/yellow] {spec['question']}")
        if "try_changing" in spec:
            console.print(f"[yellow]Try changing:[/yellow] {spec['try_changing']}")
        console.print()
