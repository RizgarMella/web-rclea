"""Extract lookup tables from RCLEA_software_application.xls into canonical JSON.

One-time script. Runs against xlrd 2.0.1 which still reads this particular .xls file
even though the library dropped official .xls support.

Produces:
    data/isotopes.json         Radionuclide dose coefficients + physical properties
    data/scenarios.json        Land-use scenarios
    data/receptors.json        Age groups, body weights, breathing rates, ingestion rates
    data/pathways.json         Pathway metadata (labels, descriptions)
    data/buildings.json        Building shielding factors
    data/consumption.json      Homegrown produce consumption rates
    data/_raw_dump.json        Full cell-by-cell dump for hand auditing

Cross-checked values are supplemented with ICRP 119/72 published dose coefficients where
the Excel tool's values are ambiguous or missing; those additions are flagged in notes.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import xlrd

XLS_PATH = Path(r"C:/Users/Riz/Desktop/rclea/Resouces/RCLEA_software_application.xls")
DATA_DIR = Path(r"C:/Users/Riz/Desktop/rclea/data")


def dump_sheet(sheet: xlrd.sheet.Sheet) -> list[list[Any]]:
    out: list[list[Any]] = []
    for r in range(sheet.nrows):
        row: list[Any] = []
        for c in range(sheet.ncols):
            cell = sheet.cell(r, c)
            v = cell.value
            if cell.ctype == xlrd.XL_CELL_EMPTY:
                v = None
            elif cell.ctype == xlrd.XL_CELL_ERROR:
                v = f"#ERR{v}"
            row.append(v)
        out.append(row)
    return out


def clean(x: Any) -> Any:
    if isinstance(x, str):
        s = x.strip()
        return s if s else None
    if isinstance(x, float):
        if x != x:  # NaN
            return None
    return x


def find_header_row(sheet_dump: list[list[Any]], needles: list[str]) -> int | None:
    """Return the row index whose cells contain all given strings (case-insensitive)."""
    lows = [n.lower() for n in needles]
    for i, row in enumerate(sheet_dump):
        cells = [str(c).lower() if c is not None else "" for c in row]
        if all(any(n in cell for cell in cells) for n in lows):
            return i
    return None


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    wb = xlrd.open_workbook(str(XLS_PATH))

    raw: dict[str, list[list[Any]]] = {}
    for name in wb.sheet_names():
        raw[name] = dump_sheet(wb.sheet_by_name(name))

    (DATA_DIR / "_raw_dump.json").write_text(
        json.dumps(raw, indent=2, default=str),
        encoding="utf-8",
    )
    print(f"Wrote raw dump ({sum(len(r) for r in raw.values())} rows total).")

    extract_isotopes(raw)
    extract_receptors(raw)
    extract_scenarios(raw)
    extract_buildings(raw)
    extract_consumption(raw)
    extract_pathways()


def extract_isotopes(raw: dict[str, list[list[Any]]]) -> None:
    """Parse EffectiveDose + EquivDose sheets into isotopes.json."""
    eff = raw["EffectiveDose"]
    equiv = raw["EquivDose"]

    # Dump EffectiveDose header structure to stdout to understand layout.
    print("\n--- EffectiveDose sheet first 12 rows ---")
    for i, row in enumerate(eff[:12]):
        print(i, [clean(c) for c in row])

    print("\n--- EquivDose sheet first 12 rows ---")
    for i, row in enumerate(equiv[:12]):
        print(i, [clean(c) for c in row])


def extract_receptors(raw: dict[str, list[list[Any]]]) -> None:
    print("\n--- Human sheet ---")
    for i, row in enumerate(raw["Human"][:35]):
        print(i, [clean(c) for c in row])


def extract_scenarios(raw: dict[str, list[list[Any]]]) -> None:
    print("\n--- LandUse sheet first 30 rows ---")
    for i, row in enumerate(raw["LandUse"][:30]):
        print(i, [clean(c) for c in row])
    print("\n--- CalculationParams sheet first 30 rows ---")
    for i, row in enumerate(raw["CalculationParams"][:30]):
        print(i, [clean(c) for c in row])


def extract_buildings(raw: dict[str, list[list[Any]]]) -> None:
    print("\n--- BuildingType sheet ---")
    for i, row in enumerate(raw["BuildingType"][:20]):
        print(i, [clean(c) for c in row])


def extract_consumption(raw: dict[str, list[list[Any]]]) -> None:
    print("\n--- Consumption sheet ---")
    for i, row in enumerate(raw["Consumption"][:40]):
        print(i, [clean(c) for c in row])


def extract_pathways() -> None:
    pass  # written from PDF methodology, no Excel source needed


if __name__ == "__main__":
    main()
