import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { resolve } from "node:path";
import { copyFileSync, mkdirSync, readdirSync, readFileSync, statSync, writeFileSync } from "node:fs";

// Dev plugin: expose /rclea_core/*.py and /rclea_data/*.json and /rclea_tutorials/*.md
// so Pyodide can fetch them and write them into its virtual FS.
function rcleaAssetsPlugin() {
  const root = resolve(__dirname, "..");
  const coreDir = resolve(root, "src/rclea_core");
  const dataDir = resolve(root, "data");
  const tutDir = resolve(root, "tutorials");
  return {
    name: "rclea-assets",
    configureServer(server: any) {
      server.middlewares.use((req: any, res: any, next: any) => {
        if (!req.url) return next();
        const serve = (disk: string, contentType: string) => {
          try {
            const buf = readFileSync(disk);
            res.setHeader("Content-Type", contentType);
            res.setHeader("Cache-Control", "no-cache");
            res.end(buf);
          } catch {
            res.statusCode = 404;
            res.end("Not Found");
          }
        };
        if (req.url.startsWith("/rclea_core/")) {
          return serve(resolve(coreDir, req.url.replace("/rclea_core/", "")), "text/x-python");
        }
        if (req.url === "/rclea_core_manifest.json") {
          const list = listRecursive(coreDir, coreDir);
          res.setHeader("Content-Type", "application/json");
          res.end(JSON.stringify(list));
          return;
        }
        if (req.url.startsWith("/rclea_data/")) {
          return serve(resolve(dataDir, req.url.replace("/rclea_data/", "")), "application/json");
        }
        if (req.url === "/rclea_data_manifest.json") {
          res.setHeader("Content-Type", "application/json");
          res.end(JSON.stringify(readdirSync(dataDir).filter((f) => f.endsWith(".json") && !f.startsWith("_"))));
          return;
        }
        if (req.url.startsWith("/rclea_tutorials/")) {
          return serve(resolve(tutDir, req.url.replace("/rclea_tutorials/", "")), "text/markdown");
        }
        if (req.url === "/rclea_tutorials_manifest.json") {
          res.setHeader("Content-Type", "application/json");
          res.end(JSON.stringify(readdirSync(tutDir).filter((f) => f.endsWith(".md")).sort()));
          return;
        }
        return next();
      });
    },
    buildStart() {
      const copyTree = (src: string, dst: string) => {
        mkdirSync(dst, { recursive: true });
        for (const name of readdirSync(src)) {
          if (name === "__pycache__" || name.startsWith(".")) continue;
          const s = resolve(src, name);
          const d = resolve(dst, name);
          if (statSync(s).isDirectory()) {
            copyTree(s, d);
          } else {
            copyFileSync(s, d);
          }
        }
      };
      const publicRoot = resolve(__dirname, "public");
      const destCore = resolve(publicRoot, "rclea_core");
      const destData = resolve(publicRoot, "rclea_data");
      const destTut = resolve(publicRoot, "rclea_tutorials");
      copyTree(coreDir, destCore);
      copyTree(dataDir, destData);
      copyTree(tutDir, destTut);
      // Write manifest files the loader fetches on boot
      writeFileSync(
        resolve(publicRoot, "rclea_core_manifest.json"),
        JSON.stringify(listRecursive(destCore, destCore)),
      );
      writeFileSync(
        resolve(publicRoot, "rclea_data_manifest.json"),
        JSON.stringify(
          readdirSync(destData).filter((f) => f.endsWith(".json") && !f.startsWith("_")),
        ),
      );
      writeFileSync(
        resolve(publicRoot, "rclea_tutorials_manifest.json"),
        JSON.stringify(readdirSync(destTut).filter((f) => f.endsWith(".md")).sort()),
      );
    },
  };
}

function listRecursive(base: string, dir: string, acc: string[] = []): string[] {
  for (const name of readdirSync(dir)) {
    const p = resolve(dir, name);
    if (statSync(p).isDirectory()) listRecursive(base, p, acc);
    else if (name.endsWith(".py")) acc.push(p.replace(base, "").replace(/\\/g, "/").replace(/^\//, ""));
  }
  return acc;
}

export default defineConfig({
  plugins: [react(), rcleaAssetsPlugin()],
  server: {
    port: 5173,
    // Pyodide needs cross-origin isolation for SharedArrayBuffer (not strictly required, but improves perf)
    headers: {
      "Cross-Origin-Opener-Policy": "same-origin",
      "Cross-Origin-Embedder-Policy": "require-corp",
    },
  },
  optimizeDeps: {
    // Pyodide ships its own loader; don't try to optimise it
    exclude: ["pyodide"],
  },
});
