#!/usr/bin/env python3
"""Pipeline completo do COMEL — da netlist (designs.py) aos arquivos de fábrica.

    python3 tools/build_all.py                 # tudo
    python3 tools/build_all.py sch pcb fab     # só algumas etapas

Etapas (em ordem):
    sym     biblioteca própria: símbolo, footprint e modelo 3D do Pico 2
    sch     esquemáticos KiCad + verificação do netlist exportado
    pcb     posicionamento, roteamento (Freerouting), planos de GND, DRC
    fab     Gerbers, furação, BOM, pick-and-place, STEP, PDFs
    tex     texturas realistas a partir dos Gerbers (gerbonara)
    mesh    STEP → GLB/STL (OpenCascade/OCP)
    images  renders 2D + esquemáticos em PNG/SVG para a documentação
    viewer  visualizador 3D (three.js) + renders 3D (Playwright)
    case    carcaça cortada a laser (SVG/DXF) a partir das posições das placas
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EDA = ROOT / "tools" / "eda"
RENDER = ROOT / "tools" / "render"
IMG = ROOT / "docs" / "images"
BOARDS = {"comel": ("comel", 132, 64, 2.5, 26)}
ENV = dict(os.environ,
           KICAD6_3DMODEL_DIR=os.environ.get("KICAD6_3DMODEL_DIR", "/usr/share/kicad/3dmodels"),
           KICAD7_3DMODEL_DIR=os.environ.get("KICAD7_3DMODEL_DIR", "/usr/share/kicad/3dmodels"),
           KICAD7_FOOTPRINT_DIR=os.environ.get("KICAD7_FOOTPRINT_DIR", "/usr/share/kicad/footprints"),
           KICAD7_SYMBOL_DIR=os.environ.get("KICAD7_SYMBOL_DIR", "/usr/share/kicad/symbols"))


def run(*cmd, cwd=ROOT):
    print("  $", " ".join(str(c) for c in cmd))
    subprocess.run([str(c) for c in cmd], cwd=cwd, env=ENV, check=True)


def stage_sym():
    run(sys.executable, EDA / "make_symbol_lib.py")
    subprocess.run([sys.executable, str(EDA / "make_3d_models.py")], cwd=ROOT, env=ENV, check=True,
                   stdout=subprocess.DEVNULL)


def stage_sch():
    sys.path.insert(0, str(EDA))
    import sch_layouts  # noqa: E402
    build = ROOT / "build"
    build.mkdir(exist_ok=True)
    for key, fn in (("comel", sch_layouts.build_comel),):
        name = BOARDS[key][0]
        sch = ROOT / "hardware" / name / f"{name}.kicad_sch"
        fn(sch)
        net = build / f"{name}.net"
        run("kicad-cli", "sch", "export", "netlist", "-o", net, sch)
        run(sys.executable, EDA / "verify_netlist.py", net, key, cwd=EDA)


def stage_pcb():
    for key in BOARDS:
        run(sys.executable, EDA / "gen_pcb.py", key)


def stage_fab():
    run(sys.executable, EDA / "export_fab.py")


def stage_tex():
    (ROOT / "build" / "tex").mkdir(parents=True, exist_ok=True)
    for name, w, h, r, ppm in BOARDS.values():
        run(sys.executable, RENDER / "textures.py", ROOT / "hardware" / name / "fab" / "gerbers",
            w, h, r, ROOT / "build" / "tex" / name, ppm)


def stage_mesh():
    (ROOT / "docs" / "3d").mkdir(parents=True, exist_ok=True)
    for name, *_ in BOARDS.values():
        run(sys.executable, RENDER / "step_to_mesh.py", ROOT / "hardware" / name / "fab" / f"{name}.step",
            ROOT / "docs" / "3d" / f"{name}.glb", ROOT / "docs" / "3d" / f"{name}.stl")


def stage_images():
    from PIL import Image
    IMG.mkdir(parents=True, exist_ok=True)
    tmp = ROOT / "build" / "img"
    tmp.mkdir(parents=True, exist_ok=True)
    for name, *_ in BOARDS.values():
        for side in ("top", "bottom"):
            im = Image.open(ROOT / "build" / "tex" / f"{name}-{side}.png")
            scale = 1400 / im.width
            im = im.resize((1400, round(im.height * scale)), Image.LANCZOS)
            im.save(IMG / f"{name}-{side}.png", optimize=True)
        # esquemático: SVG (vetorial) + PNG (pré-visualização)
        sch = ROOT / "hardware" / name / f"{name}.kicad_sch"
        run("kicad-cli", "sch", "export", "svg", "--exclude-drawing-sheet", "-o", f"{tmp}/", sch)
        svg = tmp / f"{name}.svg"
        shutil.copy(svg, IMG / f"{name}-schematic.svg")
        run("rsvg-convert", "-b", "white", "-w", "2800", svg, "-o", IMG / f"{name}-schematic.png")
        # camadas de cobre (vista técnica)
        pcb = ROOT / "hardware" / name / f"{name}.kicad_pcb"
        out = tmp / f"{name}-layers.svg"
        run("kicad-cli", "pcb", "export", "svg", "--layers", "F.Cu,B.Cu,F.SilkS,Edge.Cuts",
            "--page-size-mode", "2", "--exclude-drawing-sheet", "-o", out, pcb)
        run("rsvg-convert", "-b", "#101411", "-w", "1400", out, "-o", IMG / f"{name}-layers.png")


def stage_viewer():
    v = RENDER / "viewer"
    if not (v / "node_modules").exists():
        run("npm", "install", "--silent", cwd=v)
    run("node", "build.mjs", "../../..", "./node_modules", cwd=v)
    run("node", "shoot.mjs", "../../..", cwd=v)
    run(sys.executable, RENDER / "trim.py", *sorted(IMG.glob("*-3d*.png")))


def stage_case():
    run(sys.executable, ROOT / "case" / "gerar_carcaca.py")


STAGES = ["sym", "sch", "pcb", "fab", "tex", "mesh", "images", "case", "viewer"]

if __name__ == "__main__":
    wanted = sys.argv[1:] or STAGES
    for s in STAGES:
        if s in wanted:
            print(f"\n▶ {s}")
            globals()[f"stage_{s}"]()
    print("\n✓ concluído")
