// Gera docs/3d/viewer.html autocontido (three.js + GLB + texturas + carcaça embutidos)
// Uso: node build.mjs <raiz_do_repo> <node_modules_dir>
import { build } from "esbuild";
import fs from "node:fs";
import path from "node:path";

const [rootArg, nm] = process.argv.slice(2);
const root = path.resolve(rootArg);
const here = path.dirname(new URL(import.meta.url).pathname);
const res = await build({
  entryPoints: [path.join(here, "viewer.js")], bundle: true, minify: true, format: "iife",
  write: false, nodePaths: [nm], legalComments: "none",
});
const b64 = (f, mime) => `data:${mime};base64,${fs.readFileSync(f).toString("base64")}`;
const pcb = (id, name, w, h) => ({
  id, w, h, glb: b64(`${root}/docs/3d/${name}.glb`, "model/gltf-binary"),
  top: b64(`${root}/build/tex/${name}-top.png`, "image/png"), bottom: b64(`${root}/build/tex/${name}-bottom.png`, "image/png"),
});
const data = {
  pcbs: [pcb("comel", "comel", 132, 64)],
  tsda: b64(`${root}/docs/3d/tsda-4011r1.glb`, "model/gltf-binary"),
  case: JSON.parse(fs.readFileSync(`${root}/case/saida/carcaca.json`, "utf8")),
};
let html = fs.readFileSync(path.join(here, "template.html"), "utf8");
html = html.replace("/*BOARDS*/", () => JSON.stringify(data)).replace("/*BUNDLE*/", () => res.outputFiles[0].text);
fs.writeFileSync(`${root}/docs/3d/viewer.html`, html);
console.log(`✓ docs/3d/viewer.html (${(html.length / 1e6).toFixed(1)} MB)`);
