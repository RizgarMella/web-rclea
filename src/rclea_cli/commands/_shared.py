"""Parsing helpers shared between CLI subcommands."""
from __future__ import annotations

import typer


def parse_iso(iso_args: list[str]) -> dict[str, float]:
    out: dict[str, float] = {}
    for pair in iso_args:
        if "=" not in pair:
            raise typer.BadParameter(f"Expected --iso ID=VALUE, got {pair!r}")
        k, v = pair.split("=", 1)
        try:
            out[k.strip()] = float(v)
        except ValueError as exc:
            raise typer.BadParameter(f"--iso {pair!r} is not a number: {exc}") from exc
    return out


def parse_overrides(override_args: list[str] | None) -> dict[str, float]:
    if not override_args:
        return {}
    out: dict[str, float] = {}
    for pair in override_args:
        if "=" not in pair:
            raise typer.BadParameter(
                f"Expected --override KEY=VALUE, got {pair!r}. "
                "See README §Data reference for valid keys."
            )
        k, v = pair.split("=", 1)
        try:
            out[k.strip()] = float(v)
        except ValueError as exc:
            raise typer.BadParameter(f"--override {pair!r} is not a number: {exc}") from exc
    return out
