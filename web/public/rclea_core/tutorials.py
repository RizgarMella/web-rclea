"""Tutorial registry — discovers tutorials/*.md at import time."""
from __future__ import annotations

from dataclasses import dataclass
from importlib import resources
from pathlib import Path


@dataclass(frozen=True)
class Tutorial:
    slug: str
    title: str
    markdown: str


def _tutorial_dir() -> Path | None:
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "tutorials"
        if candidate.is_dir() and any(candidate.glob("*.md")):
            return candidate
    return None


def list_tutorials() -> list[Tutorial]:
    out: list[Tutorial] = []
    # Try packaged resources first (Pyodide / installed wheel)
    try:
        root = resources.files("rclea_core").joinpath("tutorials")
        for item in sorted(root.iterdir(), key=lambda p: p.name):
            if item.name.endswith(".md"):
                text = item.read_text(encoding="utf-8")
                out.append(_parse(item.name, text))
        if out:
            return out
    except (FileNotFoundError, ModuleNotFoundError, AttributeError):
        pass

    src = _tutorial_dir()
    if src is None:
        return []
    for path in sorted(src.glob("*.md")):
        out.append(_parse(path.name, path.read_text(encoding="utf-8")))
    return out


def _parse(filename: str, text: str) -> Tutorial:
    slug = filename.removesuffix(".md")
    title = slug
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("# "):
            title = s[2:].strip()
            break
    return Tutorial(slug=slug, title=title, markdown=text)


def get_tutorial(slug: str) -> Tutorial | None:
    for t in list_tutorials():
        if t.slug == slug:
            return t
    return None
