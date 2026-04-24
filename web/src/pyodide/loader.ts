// Loads Pyodide, mounts rclea_core source + data + tutorials into its virtual
// filesystem, and returns typed wrappers around the Python engine.
//
// Source of truth is the top-level data/, tutorials/, and src/rclea_core/ in
// the repo. A Vite dev-server plugin (vite.config.ts) exposes these at well-
// known URLs, and at build time copies them into public/ for static hosting.

import type { PyodideInterface } from "pyodide";

declare global {
  interface Window {
    loadPyodide?: (opts: { indexURL: string }) => Promise<PyodideInterface>;
  }
}

const PYODIDE_VERSION = "0.28.3";
const PYODIDE_BASE = `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/`;

let pyodidePromise: Promise<PyodideInterface> | null = null;

function loadScript(src: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const existing = document.querySelector(`script[src="${src}"]`);
    if (existing) {
      existing.addEventListener("load", () => resolve());
      existing.addEventListener("error", () => reject(new Error(`Failed to load ${src}`)));
      return;
    }
    const script = document.createElement("script");
    script.src = src;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error(`Failed to load ${src}`));
    document.head.appendChild(script);
  });
}

async function fetchText(url: string): Promise<string> {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Fetch ${url} failed: ${response.status}`);
  }
  return response.text();
}

async function fetchJson<T>(url: string): Promise<T> {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Fetch ${url} failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

async function mountRCLEA(py: PyodideInterface): Promise<void> {
  // Create the package skeleton
  py.FS.mkdirTree("/home/pyodide/rclea_core");
  py.FS.mkdirTree("/home/pyodide/rclea_core/data");
  py.FS.mkdirTree("/home/pyodide/rclea_core/tutorials");

  // 1) Python source files
  const pyManifest = await fetchJson<string[]>("/rclea_core_manifest.json");
  for (const rel of pyManifest) {
    const text = await fetchText(`/rclea_core/${rel}`);
    const dir = `/home/pyodide/rclea_core/${rel.split("/").slice(0, -1).join("/")}`;
    if (dir !== "/home/pyodide/rclea_core/") py.FS.mkdirTree(dir);
    py.FS.writeFile(`/home/pyodide/rclea_core/${rel}`, text);
  }

  // 2) data/*.json -> rclea_core/data/
  const dataManifest = await fetchJson<string[]>("/rclea_data_manifest.json");
  for (const name of dataManifest) {
    const text = await fetchText(`/rclea_data/${name}`);
    py.FS.writeFile(`/home/pyodide/rclea_core/data/${name}`, text);
  }

  // 3) tutorials/*.md -> rclea_core/tutorials/
  const tutManifest = await fetchJson<string[]>("/rclea_tutorials_manifest.json");
  for (const name of tutManifest) {
    const text = await fetchText(`/rclea_tutorials/${name}`);
    py.FS.writeFile(`/home/pyodide/rclea_core/tutorials/${name}`, text);
  }

  // Make rclea_core importable
  py.runPython(`
import sys
if "/home/pyodide" not in sys.path:
    sys.path.insert(0, "/home/pyodide")
`);
}

export async function getPyodide(): Promise<PyodideInterface> {
  if (pyodidePromise) return pyodidePromise;
  pyodidePromise = (async () => {
    await loadScript(`${PYODIDE_BASE}pyodide.js`);
    const py = await window.loadPyodide!({ indexURL: PYODIDE_BASE });
    await py.loadPackage(["micropip"]);
    // pydantic is available as a Pyodide wheel (pure Python fallback works for v2 if no pyo3 wheel)
    await py.runPythonAsync(`
import micropip
await micropip.install(["pydantic", "pyyaml"])
`);
    await mountRCLEA(py);
    // Prime the dataset loader so the first real call is fast
    await py.runPythonAsync(`
from rclea_core import load_dataset
load_dataset()
`);
    return py;
  })();
  return pyodidePromise;
}
