#!/usr/bin/env python3
"""Gera, roteia e finaliza as placas (.kicad_pcb) via API pcbnew do KiCad 7.

Etapas por placa:
  1. place   — contorno, footprints, redes, classes de rede, serigrafia
  2. route   — exporta Specctra DSN → Freerouting (CLI) → importa SES
  3. finish  — planos de GND nas duas faces, preenchimento, relatório DRC

Uso: python3 gen_pcb.py comel [--no-route]
"""
from __future__ import annotations

import math
import os
import re
import subprocess
import sys
from pathlib import Path

import pcbnew

from designs import COMEL_PARTS
from pcb_layouts import COMEL_POS, COMEL_SIZE
from sexpr import det_uuid

ROOT = Path(__file__).resolve().parents[2]
FPLIB = Path("/usr/share/kicad/footprints")
CUSTOM_FP = {"COMEL": ROOT / "hardware" / "lib" / "COMEL.pretty"}
FREEROUTING = Path(os.environ.get("FREEROUTING_JAR", ROOT / "tools" / "bin" / "freerouting-1.9.0.jar"))
MODEL_OVERRIDE = {"USB_A_Wuerth_61400826021_Horizontal_Stacked": "${KIPRJMOD}/../lib/3d/USB_A_Stacked_2x.step"}
OX, OY = 100.0, 100.0   # origem da placa na folha (mm)

BOARDS = {
    "comel": dict(name="comel", parts=COMEL_PARTS, pos=COMEL_POS, size=COMEL_SIZE, corner=2.5,
                  title="COMEL", ref_on_silk=False, power_w=0.8,
                  power=["GND", "+5V", "+5V_IN", "+12V", "+12V_IN", "VSYS", "+3V3"],
                  medium=["VBUS"],
                  fanout=[("U3", "2", -1.45, 0.0)]),     # via de GND do USBLC6 antes de rotear
}


def mm(v):
    return pcbnew.FromMM(v)


def pt(x, y):
    return pcbnew.VECTOR2I(mm(OX + x), mm(OY + y))


# ----------------------------------------------------------------------------- 1
def outline(board, w, h, r):
    def seg(x1, y1, x2, y2):
        s = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(pt(x1, y1)); s.SetEnd(pt(x2, y2))
        s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(mm(0.1)); board.Add(s)

    def arc(cx, cy, sx, sy, ang):
        a = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_ARC)
        a.SetCenter(pt(cx, cy)); a.SetStart(pt(sx, sy))
        a.SetArcAngleAndEnd(pcbnew.EDA_ANGLE(ang, pcbnew.DEGREES_T), True)
        a.SetLayer(pcbnew.Edge_Cuts); a.SetWidth(mm(0.1)); board.Add(a)

    seg(r, 0, w - r, 0); seg(w, r, w, h - r); seg(w - r, h, r, h); seg(0, h - r, 0, r)
    arc(w - r, r, w - r, 0, 90); arc(w - r, h - r, w, h - r, 90)
    arc(r, h - r, r, h, 90); arc(r, r, 0, r, 90)


def text(board, s, x, y, size, layer, bold=True, mirror=False, just_left=False, angle=0, halign=None):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(s); t.SetPosition(pt(x, y)); t.SetLayer(layer)
    t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size)))
    t.SetTextThickness(mm(size * (0.18 if bold else 0.12)))
    t.SetBold(bold); t.SetMirrored(mirror)
    if halign == "right":
        t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_RIGHT)
    if angle:
        t.SetTextAngle(pcbnew.EDA_ANGLE(angle, pcbnew.DEGREES_T))
    if just_left:
        t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_RIGHT if mirror else pcbnew.GR_TEXT_H_ALIGN_LEFT)
    board.Add(t)


def board_rules(board):
    ds = board.GetDesignSettings()
    ds.SetCopperLayerCount(2)
    ds.SetBoardThickness(mm(1.6))


def netclass(name, clr, tw, via=0.6, drill=0.3):
    return {"name": name, "clearance": clr, "track_width": tw, "via_diameter": via, "via_drill": drill,
            "bus_width": 12, "diff_pair_gap": 0.25, "diff_pair_via_gap": 0.25, "diff_pair_width": 0.2,
            "line_style": 0, "microvia_diameter": 0.3, "microvia_drill": 0.1,
            "pcb_color": "rgba(0, 0, 0, 0.000)", "schematic_color": "rgba(0, 0, 0, 0.000)", "wire_width": 6}


def write_project(cfg, out_dir: Path):
    """.kicad_pro com regras de projeto e classes de rede (Default / Power / HV)."""
    import json
    pro = {
        "board": {"design_settings": {
            "defaults": {"board_outline_line_width": 0.1, "copper_line_width": 0.2,
                         "silk_line_width": 0.12, "silk_text_size_h": 1.0, "silk_text_size_v": 1.0,
                         "silk_text_thickness": 0.15, "fab_text_size_h": 0.6, "fab_text_size_v": 0.6},
            "diff_pair_dimensions": [], "drc_exclusions": [],
            "rule_severities": {"silk_overlap": "ignore", "silk_over_copper": "ignore",
                                "lib_footprint_issues": "ignore", "lib_footprint_mismatch": "ignore",
                                "courtyards_overlap": "error", "silk_edge_clearance": "ignore",
                                "text_height": "ignore", "text_thickness": "ignore"},
            "rules": {"min_clearance": 0.2, "min_track_width": 0.2, "min_via_diameter": 0.6,
                      "min_via_annular_width": 0.13, "min_through_hole_diameter": 0.3,
                      "min_copper_edge_clearance": 0.4, "min_hole_clearance": 0.25,
                      "min_hole_to_hole": 0.25, "min_silk_clearance": 0.0,
                      "min_text_height": 0.6, "min_text_thickness": 0.08,
                      "min_microvia_diameter": 0.2, "min_microvia_drill": 0.1,
                      "allow_blind_buried_vias": False, "allow_microvias": False},
            "track_widths": [0.0, 0.25, 0.3, 0.5, 0.8],
            "via_dimensions": [{"diameter": 0.0, "drill": 0.0}, {"diameter": 0.6, "drill": 0.3},
                               {"diameter": 0.7, "drill": 0.35}]}},
        "boards": [],
        "libraries": {"pinned_footprint_libs": [], "pinned_symbol_libs": []},
        "meta": {"filename": f"{cfg['name']}.kicad_pro", "version": 1},
        "net_settings": {
            "classes": [netclass("Default", 0.2, 0.25), netclass("Power", 0.25, cfg["power_w"], 0.8, 0.4),
                        netclass("Medium", 0.2, 0.5, 0.6, 0.3)],
            "meta": {"version": 3}, "net_colors": None, "netclass_assignments": None,
            "netclass_patterns": [{"netclass": "Power", "pattern": n} for n in cfg["power"]]
                                 + [{"netclass": "Medium", "pattern": n} for n in cfg.get("medium", [])]},
        "pcbnew": {"last_paths": {"gencad": "", "idf": "", "netlist": "", "specctra_dsn": "",
                                  "step": "", "vrml": ""}, "page_layout_descr_file": ""},
        "schematic": {"legacy_lib_dir": "", "legacy_lib_list": []},
        "sheets": [[det_uuid(cfg["name"], "root"), ""]],
        "text_variables": {},
    }
    (out_dir / f"{cfg['name']}.kicad_pro").write_text(json.dumps(pro, indent=2, ensure_ascii=False))
    (out_dir / "sym-lib-table").write_text(
        '(sym_lib_table\n  (lib (name "COMEL")(type "KiCad")(uri "${KIPRJMOD}/../lib/COMEL.kicad_sym")'
        '(options "")(descr "Símbolos do projeto COMEL (Raspberry Pi Pico 2)"))\n)\n')
    (out_dir / "fp-lib-table").write_text(
        '(fp_lib_table\n  (lib (name "COMEL")(type "KiCad")(uri "${KIPRJMOD}/../lib/COMEL.pretty")'
        '(options "")(descr "Footprints do projeto COMEL"))\n)\n')


def place(cfg) -> pcbnew.BOARD:
    board = pcbnew.CreateEmptyBoard() if hasattr(pcbnew, "CreateEmptyBoard") else pcbnew.BOARD()
    w, h = cfg["size"]
    outline(board, w, h, cfg["corner"])
    board_rules(board)

    nets = {}
    for p in cfg["parts"]:
        for n in p.pins.values():
            if n and n not in nets:
                ni = pcbnew.NETINFO_ITEM(board, n)
                board.Add(ni)
                nets[n] = ni

    for p in cfg["parts"]:
        lib, name = p.fp.split(":")
        fp = pcbnew.FootprintLoad(str(CUSTOM_FP.get(lib, FPLIB / f"{lib}.pretty")), name)
        assert fp is not None, p.fp
        for it in list(fp.GraphicalItems()):          # recortes de borda vindos do footprint (jack P2)
            if it.GetLayer() == pcbnew.Edge_Cuts:
                fp.Remove(it)
        fp.SetFPID(pcbnew.LIB_ID(lib, name))
        fp.SetReference(p.ref)
        fp.SetValue(p.value)
        fp.SetPath(pcbnew.KIID_PATH(f"/{det_uuid(cfg['name'], 's', p.ref)}"))
        x, y, rot = cfg["pos"][p.ref]
        fp.SetPosition(pt(x, y))
        fp.SetOrientationDegrees(rot)
        for pad in fp.Pads():
            n = p.pins.get(pad.GetNumber())
            if n:
                pad.SetNet(nets[n])
        if p.dnp and hasattr(fp, "SetDNP"):
            fp.SetDNP(True)
        ref = fp.Reference()
        ref.SetTextSize(pcbnew.VECTOR2I(mm(0.8), mm(0.8)))
        ref.SetTextThickness(mm(0.12))
        if not cfg["ref_on_silk"]:
            ref.SetLayer(pcbnew.F_Fab if fp.GetLayer() == pcbnew.F_Cu else pcbnew.B_Fab)
            ref.SetTextSize(pcbnew.VECTOR2I(mm(0.6), mm(0.6)))
            ref.SetTextThickness(mm(0.09))
        board.Add(fp)

    return board


# ----------------------------------------------------------------------------- 2
def edge_keepouts(board, w, h, m=0.6):
    """Faixas de keep-out (trilhas/vias) junto às bordas — o Freerouting não
    recebe a regra de distância cobre-borda do KiCad pelo DSN."""
    zones = []
    for x1, y1, x2, y2 in [(0, 0, w, m), (0, h - m, w, h), (0, 0, m, h), (w - m, 0, w, h)]:
        z = pcbnew.ZONE(board)
        z.SetIsRuleArea(True); z.SetDoNotAllowTracks(True); z.SetDoNotAllowVias(True)
        z.SetDoNotAllowCopperPour(False); z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
        ls = pcbnew.LSET(); ls.AddLayer(pcbnew.F_Cu); ls.AddLayer(pcbnew.B_Cu); z.SetLayerSet(ls)
        ol = z.Outline(); ol.NewOutline()
        for x, y in [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]:
            ol.Append(mm(OX + x), mm(OY + y))
        board.Add(z); zones.append(z)
    return zones


def route(board, work: Path, passes=40, size=None):
    dsn, ses = work / "board.dsn", work / "board.ses"
    keep = edge_keepouts(board, *size) if size else []
    ok = pcbnew.ExportSpecctraDSN(board, str(dsn))
    for z in keep:
        board.Remove(z)
    if not ok:
        raise RuntimeError("falha ao exportar DSN")
    cmd = ["java", "-jar", str(FREEROUTING), "-de", str(dsn), "-do", str(ses), "-mp", str(passes)]
    if os.environ.get("DISPLAY") is None and subprocess.run(["which", "xvfb-run"], capture_output=True).returncode == 0:
        cmd = ["xvfb-run", "-a"] + cmd
    print("·", " ".join(cmd))
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=1200, cwd=work)
    import_ses(board, ses)


def fanout(board, cfg):
    """Vias de GND fixas junto a pads SMD que o roteador poderia cercar (ele conta com o plano)."""
    for ref, pad, dx, dy in cfg.get("fanout", []):
        p = board.FindFootprintByReference(ref).FindPadByNumber(pad)
        a = p.GetPosition(); b = pcbnew.VECTOR2I(a.x + mm(dx), a.y + mm(dy))
        t = pcbnew.PCB_TRACK(board); t.SetStart(a); t.SetEnd(b); t.SetWidth(mm(0.5))
        t.SetLayer(pcbnew.F_Cu); t.SetNet(p.GetNet()); t.SetLocked(True); board.Add(t)
        v = pcbnew.PCB_VIA(board); v.SetPosition(b); v.SetWidth(mm(0.6)); v.SetDrill(mm(0.3))
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(p.GetNet()); v.SetLocked(True); board.Add(v)


def import_ses(board, ses: Path):
    """Importa trilhas e vias de uma sessão Specctra (.ses) do Freerouting.

    (ImportSpecctraSES do KiCad 7 só atua na placa aberta na GUI.)
    Unidades da sessão: 0,1 µm, eixo Y invertido.
    """
    import re
    from sexpr import find, find_all, parse
    tree = parse(ses.read_text(encoding="utf-8", errors="replace"))
    routes = find(tree, "routes")
    res = find(routes, "resolution")
    scale = 1e-3 / float(res[2]) if res else 1e-4
    layers = {"F.Cu": pcbnew.F_Cu, "B.Cu": pcbnew.B_Cu}

    def P(x, y):
        return pcbnew.VECTOR2I(mm(float(x) * scale), mm(-float(y) * scale))

    for t in list(board.GetTracks()):            # a sessão traz tudo, inclusive o que já existia
        board.Delete(t)
    n_t = n_v = 0
    for net in find_all(find(routes, "network_out"), "net"):
        ni = board.FindNet(net[1])
        for w in find_all(net, "wire"):
            path = find(w, "path")
            layer, width, coords = path[1], float(path[2]) * scale, path[3:]
            pts = [P(coords[i], coords[i + 1]) for i in range(0, len(coords) - 1, 2)]
            for a, b in zip(pts, pts[1:]):
                t = pcbnew.PCB_TRACK(board)
                t.SetStart(a); t.SetEnd(b); t.SetWidth(mm(width))
                t.SetLayer(layers[layer]); t.SetNet(ni); board.Add(t); n_t += 1
        for v in find_all(net, "via"):
            m = re.search(r"_(\d+):(\d+)_um", v[1])
            dia, drill = (int(m.group(1)) / 1000, int(m.group(2)) / 1000) if m else (0.6, 0.3)
            via = pcbnew.PCB_VIA(board)
            via.SetPosition(P(v[2], v[3])); via.SetWidth(mm(dia)); via.SetDrill(mm(drill))
            via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); via.SetNet(ni); board.Add(via); n_v += 1
    print(f"  SES importado: {n_t} segmentos, {n_v} vias")


# ----------------------------------------------------------------------------- 3
def gnd_zones(board, cfg):
    w, h = cfg["size"]
    gnd = board.FindNet("GND")
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
        z = pcbnew.ZONE(board)
        z.SetLayer(layer); z.SetNet(gnd); z.SetZoneName("GND")
        z.SetLocalClearance(mm(0.3)); z.SetMinThickness(mm(0.25))
        z.SetThermalReliefGap(mm(0.3)); z.SetThermalReliefSpokeWidth(mm(0.4))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        ol = z.Outline(); ol.NewOutline()
        for x, y in [(0, 0), (w, 0), (w, h), (0, h)]:
            ol.Append(mm(OX + x), mm(OY + y))
        board.Add(z)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    stitch(board, cfg, gnd)


def stitch(board, cfg, gnd, step=5.0):
    """Vias de costura do GND: liga os dois planos onde ambos estão preenchidos com folga,
    evitando que o plano de uma face fique partido em pedaços ligados só por pads."""
    w, h = cfg["size"]
    zones = {z.GetLayer(): z for z in board.Zones() if z.GetNetname() == "GND"}
    polys = {l: z.GetFilledPolysList(l) for l, z in zones.items()}
    ring = [(0, 0)] + [(0.55 * math.cos(a * math.pi / 4), 0.55 * math.sin(a * math.pi / 4)) for a in range(8)]
    n = 0
    y = 2.0
    while y < h - 1.5:
        x = 2.0 + (step / 2 if int(y / step) % 2 else 0)
        while x < w - 1.5:
            ok = all(polys[l].Contains(pcbnew.VECTOR2I(mm(OX + x + dx), mm(OY + y + dy)))
                     for l in polys for dx, dy in ring)
            if ok:
                v = pcbnew.PCB_VIA(board)
                v.SetPosition(pcbnew.VECTOR2I(mm(OX + x), mm(OY + y)))
                v.SetWidth(mm(0.6)); v.SetDrill(mm(0.3))
                v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(gnd); board.Add(v); n += 1
            x += step
        y += step
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())

    # pedaços de plano que ficaram sem via (ligados só a um pad): uma via em cada, se couber
    def add_via(x, y):
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(pcbnew.VECTOR2I(x, y)); v.SetWidth(mm(0.6)); v.SetDrill(mm(0.3))
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(gnd); board.Add(v)

    for _ in range(3):
        polys = {l: z.GetFilledPolysList(l) for l, z in zones.items()}
        vias = [t.GetPosition() for t in board.GetTracks() if isinstance(t, pcbnew.PCB_VIA) and t.GetNetname() == "GND"]
        added = 0
        for l, ps in polys.items():
            other = [p for k, p in polys.items() if k != l]
            for i in range(ps.OutlineCount()):
                if any(ps.Contains(v, i) for v in vias):
                    continue
                bb = ps.Outline(i).BBox()
                found = None
                yy = bb.GetY()
                while yy <= bb.GetBottom() and not found:
                    xx = bb.GetX()
                    while xx <= bb.GetRight():
                        pts = [pcbnew.VECTOR2I(int(xx + mm(dx * 0.6)), int(yy + mm(dy * 0.6))) for dx, dy in ring]
                        if all(ps.Contains(q, i) for q in pts) and all(o.Contains(q) for o in other for q in pts):
                            found = (xx, yy); break
                        xx += mm(0.1)
                    yy += mm(0.1)
                if found:
                    add_via(*found); added += 1
                    vias.append(pcbnew.VECTOR2I(*found))
        n += added
        pcbnew.ZONE_FILLER(board).Fill(board.Zones())
        if not added:
            break
    print(f"  {n} vias de costura no GND")


def silk(board, cfg):
    B, F = pcbnew.B_SilkS, pcbnew.F_SilkS
    # Face inferior: identidade e pinagem dos conectores (texto espelhado)
    text(board, "COMEL", 116.5, 20.0, 3.0, B, mirror=True)
    text(board, "Commodore 64 em Pico 2", 116.5, 24.6, 1.1, B, bold=False, mirror=True)
    text(board, "rede via TSDA 4011R1", 116.5, 26.9, 1.1, B, bold=False, mirror=True)
    text(board, "REV 1.0 · 2026 · GPL-3.0", 116.5, 29.2, 1.0, B, bold=False, mirror=True)
    text(board, "github.com/aragonxpd154/COMEL", 116.5, 31.4, 0.9, B, bold=False, mirror=True)
    for x, y, s in [(72.5, 30.6, "J3 TSDA TTL: TX RX GND"), (72.5, 38.6, "J4 TSDA 232: TX RX GND"),
                    (30.0, 19.2, "J2 USB 1 (baixo) / USB 2 (cima)"), (72.0, 49.2, "J1 VGA: R G B HS VS"),
                    (107.6, 51.0, "J10 RD-35A: +5V COM +12V COM")]:
        text(board, s, x, y, 0.8, B, bold=False, mirror=True)
    for x, y, s in [(70.0, 14.6, "JOY"), (46.0, 15.6, "AUDIO"), (8.0, 22.6, "microSD"),
                    (39.0, 36.0, "RESET"), (56.25, 39.0, "VGA DAC"),
                    (62.0, 17.0, "RX"), (76.0, 22.6, "TTL"), (76.0, 38.5, "RS-232 (opc.)"),
                    (93.75, 9.4, "TSDA"), (102.25, 9.4, "TELA"), (110.75, 9.4, "AUX"), (119.25, 9.4, "LED"),
                    (110.0, 52.0, "+5V  COM  +12V  COM"), (122.0, 30.0, "5V"), (122.0, 33.0, "12V")]:
        text(board, s, x, y, 0.9, F, bold=False)


def drc(board, path: Path):
    pcbnew.WriteDRCReport(board, str(path), pcbnew.EDA_UNITS_MILLIMETRES, True)
    txt = path.read_text()
    import re
    vio = re.search(r"\*\* Found (\d+) DRC violations", txt)
    unc = re.search(r"\*\* Found (\d+) unconnected pads", txt)
    return int(vio.group(1)) if vio else -1, int(unc.group(1)) if unc else -1


def main():
    which = sys.argv[1]
    cfg = BOARDS[which]
    out_dir = ROOT / "hardware" / cfg["name"]
    work = ROOT / "build" / cfg["name"]
    work.mkdir(parents=True, exist_ok=True)
    pcb = out_dir / f"{cfg['name']}.kicad_pcb"

    if "--rezone" in sys.argv and "--stage2" not in sys.argv:
        subprocess.run([sys.executable, __file__] + sys.argv[1:] + ["--stage2", "--no-route"], check=True)
        return
    if "--stage2" not in sys.argv:
        # Estágio 1: posicionamento (processo próprio)
        board = place(cfg)
        silk(board, cfg)
        board.Save(str(pcb))
        # modelos 3D: referência direta aos .step (exportação STEP com componentes)
        txt = pcb.read_text(encoding="utf-8").replace('.wrl"', '.step"')
        for name, path in MODEL_OVERRIDE.items():    # modelo 3D próprio (a biblioteca do KiCad 7 não traz)
            txt = re.sub(r'\(model "[^"]*/' + re.escape(name) + r'\.step"', f'(model "{path}"', txt)
        pcb.write_text(txt, encoding="utf-8")
        write_project(cfg, out_dir)              # depois do Save (que regrava o .kicad_pro)
        # Estágio 2 em processo novo: o pcbnew precisa ler o .kicad_pro do zero
        subprocess.run([sys.executable, __file__] + sys.argv[1:] + ["--stage2"], check=True)
        return

    board = pcbnew.LoadBoard(str(pcb))
    nsx = board.GetDesignSettings().m_NetSettings
    assert nsx.GetEffectiveNetClass(cfg["power"][1]).GetName() == "Power", "classes de rede não carregadas"
    if "--no-route" not in sys.argv:
        fanout(board, cfg)
        route(board, work, size=cfg["size"])
    for z in list(board.Zones()):                 # --rezone: refaz só os planos de GND
        board.Remove(z)
    ends = {(t.GetStart().x, t.GetStart().y) for t in board.GetTracks() if not isinstance(t, pcbnew.PCB_VIA)}
    ends |= {(t.GetEnd().x, t.GetEnd().y) for t in board.GetTracks() if not isinstance(t, pcbnew.PCB_VIA)}
    for t in list(board.GetTracks()):              # vias de costura antigas (soltas, sem trilha)
        if isinstance(t, pcbnew.PCB_VIA) and t.GetNetname() == "GND" and (t.GetPosition().x, t.GetPosition().y) not in ends:
            board.Delete(t)
    gnd_zones(board, cfg)
    board.Save(str(pcb))
    board = pcbnew.LoadBoard(str(pcb))
    v, u = drc(board, work / "drc.rpt")
    print(f"✓ {pcb.name}: {len(board.GetFootprints())} footprints, "
          f"{len(board.GetTracks())} trilhas/vias, DRC={v} violações, {u} não conectados")


if __name__ == "__main__":
    os.environ.setdefault("KICAD7_FOOTPRINT_DIR", str(FPLIB))
    os.environ.setdefault("KICAD7_SYMBOL_DIR", "/usr/share/kicad/symbols")
    os.environ.setdefault("KICAD6_3DMODEL_DIR", "/usr/share/kicad/3dmodels")
    os.environ.setdefault("KICAD7_3DMODEL_DIR", "/usr/share/kicad/3dmodels")
    main()
