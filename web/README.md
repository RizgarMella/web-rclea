# RCLEA web app

Vite + React + TypeScript + Tailwind + Pyodide.

## First-time setup

```bash
cd web
npm install
```

Node 18+ and npm 9+ recommended. Pyodide (~8 MB) downloads on first browser
visit and is cached by the service worker.

## Run dev server

```bash
npm run dev
```

Open http://localhost:5173.

The Vite dev-server plugin in [`vite.config.ts`](vite.config.ts) serves the
Python source (`../src/rclea_core/*.py`), the data JSON (`../data/*.json`),
and the Markdown tutorials (`../tutorials/*.md`) at well-known URLs. On page
load, `src/pyodide/loader.ts` fetches them and writes them into Pyodide's
virtual filesystem, then imports `rclea_core`.

The web app therefore runs the **identical** Python calculation engine as
the CLI. No separate JS/TS port of the dose math exists.

## Build for deployment

```bash
npm run build
```

The build step copies `../data/`, `../tutorials/`, and `../src/rclea_core/`
into `web/public/` so they are served as static assets. Deploy the `dist/`
directory to any static host (GitHub Pages, Netlify, Cloudflare Pages, S3).

## Extending

- **New isotope** — add an entry to `../data/isotopes.json`; reload the dev
  server (or rebuild for production) and it appears in the form.
- **New tutorial** — drop a `07-xxx.md` file into `../tutorials/`.
- **New glossary entry** — add to `src/lib/glossary.ts`.

## Disclaimer

This is an **educational** tool. It is not a regulatory instrument and
author(s) accept no liability. See `../DISCLAIMER.md`.
