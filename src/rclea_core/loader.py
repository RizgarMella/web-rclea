"""Load data/*.json into validated pydantic models.

Works in two environments:
  - Python package on disk: reads from `data/` sibling of the package root.
  - Pyodide: wheel-bundled resources via importlib.resources under
    `rclea_core/data/` (see pyproject.toml force-include).
"""
from __future__ import annotations

import json
from functools import lru_cache
from importlib import resources
from pathlib import Path
from typing import Any

from rclea_core.models import (
    Building,
    Constants,
    CropMeta,
    Dataset,
    Element,
    Isotope,
    Pathway,
    RadonParams,
    Receptors,
    Scenario,
    SoilGlobal,
)


def _repo_data_dir() -> Path | None:
    """When running from source checkout, find top-level data/ directory."""
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "data"
        if candidate.is_dir() and (candidate / "isotopes.json").exists():
            return candidate
    return None


def _read_json(name: str) -> Any:
    """Try the bundled location first (works in Pyodide), then source tree."""
    try:
        with resources.files("rclea_core").joinpath("data", name).open("r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, ModuleNotFoundError, AttributeError):
        pass
    repo = _repo_data_dir()
    if repo is None:
        raise FileNotFoundError(f"Cannot locate data/{name}: not in package resources or repo tree")
    return json.loads((repo / name).read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_dataset() -> Dataset:
    iso_raw = _read_json("isotopes.json")
    el_raw = _read_json("elements.json")
    sc_raw = _read_json("scenarios.json")
    rec_raw = _read_json("receptors.json")
    bldg_raw = _read_json("buildings.json")
    cons_raw = _read_json("consumption.json")
    pw_raw = _read_json("pathways.json")
    const_raw = _read_json("constants.json")

    isotopes = {entry["id"]: Isotope.model_validate(entry) for entry in iso_raw["isotopes"]}
    radon = RadonParams.model_validate(iso_raw["radon"])
    elements = {entry["id"]: Element.model_validate(entry) for entry in el_raw["elements"]}
    soil_global = SoilGlobal.model_validate(el_raw.get("soil_global", {}))
    scenarios = {entry["id"]: Scenario.model_validate(entry) for entry in sc_raw["scenarios"]}
    # Merge user-overlay scenarios registered via `rclea scenarios register`.
    # Overlay lives at ~/.rclea/scenarios.json and is not available in the browser
    # (where the home directory is Pyodide's virtual FS — so this is a no-op there).
    try:
        overlay_path = Path.home() / ".rclea" / "scenarios.json"
        if overlay_path.is_file():
            overlay = json.loads(overlay_path.read_text(encoding="utf-8"))
            for entry in overlay.get("scenarios", []):
                s = Scenario.model_validate(entry)
                scenarios[s.id] = s
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        pass
    receptors = Receptors.model_validate(rec_raw)

    buildings: dict[str, Building] = {}
    bldg_global = bldg_raw.get("global", {})
    for entry in bldg_raw["buildings"]:
        # Fall back to global radon params if the per-building ones are missing (back-compat).
        merged = {
            "rn222_height_m": bldg_global.get("height_m", 3.0),
            "rn222_ventilation_rate_per_s": bldg_global.get("ventilation_rate_per_s", 8.33e-5),
            **entry,
        }
        b = Building.model_validate(merged)
        buildings[b.id] = b

    crop_meta = {k: CropMeta.model_validate(v) for k, v in cons_raw["crop_meta"].items()}
    consumption_by_age: dict[str, dict[str, float]] = cons_raw["by_age"]

    pathways = {entry["id"]: Pathway.model_validate(entry) for entry in pw_raw["pathways"]}
    constants = Constants.model_validate(const_raw)

    return Dataset(
        isotopes=isotopes,
        radon=radon,
        elements=elements,
        soil_global=soil_global,
        scenarios=scenarios,
        receptors=receptors,
        buildings=buildings,
        consumption_by_age=consumption_by_age,
        crop_meta=crop_meta,
        pathways=pathways,
        constants=constants,
    )


def reload_dataset() -> Dataset:
    load_dataset.cache_clear()
    return load_dataset()
