#!/usr/bin/env python3
"""
Carcaça COMEL — gerador dos arquivos de corte a laser.

Caixa de chapa de 3 mm (MDF ou acrílico) em perfil de terminal: frente baixa,
tela de 7" num painel inclinado 25° para trás e tampa reta. As laterais têm o
perfil da caixa e recebem os dentes de todos os outros painéis (junta a 90°
sempre: todos os painéis são perpendiculares às laterais). A placa COMEL e a
TSDA 4011R1 ficam no fundo, encostadas no painel traseiro; a fonte RD-35A fica
no piso, na frente da TSDA, e é a única coisa fora da placa.

A furação da placa e a posição dos conectores são lidas de
tools/eda/pcb_layouts.py — mudou a placa, rode de novo e os cortes acompanham.

Uso:
    python3 gerar_carcaca.py                 # medidas nominais
    python3 gerar_carcaca.py --kerf 0.15     # compensa a espessura do feixe

Saída (pasta ./saida):
    chapa-1.svg / chapa-1.dxf, chapa-2.svg / chapa-2.dxf  -> para a máquina
    pecas/<peca>.svg                                      -> cada peça sozinha
    carcaca.json                                          -> usado pelo visualizador 3D

Camadas: CORTE (vermelho, linha fina) e GRAVAR (azul, preenchido).
Coordenadas internas em mm. Origem da caixa: canto inferior esquerdo da frente;
X para a direita (olhando de frente), Y para cima, Z para o fundo.
"""
import argparse, json, math, os, sys
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties
from shapely.geometry import Polygon
from shapely.ops import unary_union

# ---------------- parâmetros principais ----------------
W, H, D, T = 230.0, 128.0, 190.0, 3.0       # largura, altura atrás, profundidade, espessura da chapa
LIP = 18.0                                   # altura da frente baixa (abaixo da tela)
ANG = 25.0                                   # inclinação da tela (graus, a partir da vertical)
DENTE = 15.0                                 # largura aproximada de cada dente
CHAPA = (600.0, 400.0)                       # mesa da máquina
STANDOFF = 8.0                               # altura dos espaçadores M3 das placas
M3 = 3.2                                     # furo para parafuso M3

CA, SA = math.cos(math.radians(ANG)), math.sin(math.radians(ANG))
ZT = (H - LIP) * SA / CA                     # onde a tampa começa (topo da tela)
LF = (H - LIP) / CA                          # comprimento da aresta inclinada do perfil
LS = (H - T - LIP) / CA                      # comprimento do painel da tela (vai até a tampa)
LIP_IN = LIP - T * SA                        # topo do painel da frente (encosta embaixo do painel da tela)

TELA = dict(cx=W / 2, v=LS / 2, janela=(156.0, 88.0), modulo=(165.0, 100.0))
MOLDURA = dict(ext=(189.0, 113.0), furos=(88.5, 52.5), espaco=(166.0, 101.0), trava=(140.0, 80.0))
Z_BORDA = D - T - 0.5                        # borda dos conectores das placas
TSDA_X0 = 225.0                              # X da borda x=0 da TSDA (placa girada 180°)
COMEL_X0 = 3.5                               # X da borda esquerda da COMEL (borda y=0 voltada para trás)
FONTE = dict(x0=127.0, z0=36.0, L=99.0, P=82.0, A=36.0)
IEC = dict(X=185.0, Y=66.0, w=48.0, h=28.0)  # módulo IEC C14 + chave + fusível, no painel traseiro acima da TSDA
USB = dict(w=15.2, h=16.2)                   # recorte do USB-A duplo empilhado (corpo 14,6 × 15,6 mm)

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tools', 'eda'))
from pcb_layouts import COMEL_POS, COMEL_SIZE   # noqa: E402
Y_PLACA = T + STANDOFF                       # face de baixo das placas


def tsda(bx, by):     # coordenada da TSDA (foto) -> caixa (X, Z)
    return TSDA_X0 - bx, Z_BORDA - (47.0 - by)


def comel(bx, by):    # coordenada da COMEL (KiCad, y para baixo, conectores em y = 0) -> caixa (X, Z)
    return COMEL_X0 + bx, Z_BORDA - by


# ---------------- geometria ----------------
def odd(n):
    n = max(3, int(round(n)))
    return n if n % 2 else n + 1


def borda(L, tipo):
    """Perfil de uma borda de comprimento L: lista de (inicio, fim, recuo)."""
    n = odd(L / DENTE)
    seg = []
    for k in range(n):
        par = k % 2 == 0
        dentro = (not par) if tipo == 'M' else par
        seg.append((k * L / n, (k + 1) * L / n, T if dentro else 0.0))
    return seg


def contorno(Wp, Hp, tipos):
    """Contorno da peça (sentido anti-horário). tipos = dict b, r, t, l -> 'M' (dentes) ou 'F' (encaixes) ou '-' (liso)."""
    x0 = T if tipos['l'] == 'F' else 0.0
    x1 = Wp - T if tipos['r'] == 'F' else Wp
    y0 = T if tipos['b'] == 'F' else 0.0
    y1 = Hp - T if tipos['t'] == 'F' else Hp
    pts = []

    def lado(L, tipo, mapa, a, b):
        segs = borda(L, tipo) if tipo != '-' else [(0.0, L, 0.0)]
        for s0, s1, r in segs:
            s0, s1 = max(s0, a), min(s1, b)
            if s1 <= s0:
                continue
            for s in (s0, s1):
                p = mapa(s, r)
                if not pts or (abs(pts[-1][0] - p[0]) > 1e-9 or abs(pts[-1][1] - p[1]) > 1e-9):
                    pts.append(p)
    lado(Wp, tipos['b'], lambda s, r: (s, r), x0, x1)                    # baixo, esquerda -> direita
    lado(Hp, tipos['r'], lambda s, r: (Wp - r, s), y0, y1)               # direita, baixo -> cima
    lado(Wp, tipos['t'], lambda s, r: (Wp - s, Hp - r), Wp - x1, Wp - x0)  # cima, direita -> esquerda
    lado(Hp, tipos['l'], lambda s, r: (r, Hp - s), Hp - y1, Hp - y0)     # esquerda, cima -> baixo
    return pts


def ret(cx, cy, w, h, r=0.0):
    if r <= 0:
        return [(cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2), (cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2)]
    out = []
    for (qx, qy, a0) in [(cx + w / 2 - r, cy - h / 2 + r, -90), (cx + w / 2 - r, cy + h / 2 - r, 0),
                         (cx - w / 2 + r, cy + h / 2 - r, 90), (cx - w / 2 + r, cy - h / 2 + r, 180)]:
        for i in range(7):
            a = math.radians(a0 + i * 15)
            out.append((qx + r * math.cos(a), qy + r * math.sin(a)))
    return out


def circ(cx, cy, d, n=40):
    return [(cx + d / 2 * math.cos(2 * math.pi * i / n), cy + d / 2 * math.sin(2 * math.pi * i / n)) for i in range(n)]


def oblongo(cx, cy, w, h):
    return ret(cx, cy, w, h, min(w, h) / 2 - 1e-3)


def texto(s, x, y, alt, alinhar='center'):
    """Texto em contornos (para gravar). Retorna lista de polígonos."""
    tp = TextPath((0, 0), s, size=alt, prop=FontProperties(family='DejaVu Sans', weight='bold'))
    polys = [p for p in tp.to_polygons() if len(p) > 2]
    if not polys:
        return []
    xs = [p[0] for poly in polys for p in poly]
    larg = max(xs) - min(xs)
    dx = x - (larg / 2 if alinhar == 'center' else 0) - min(xs)
    return [[(px + dx, py + y) for px, py in poly] for poly in polys]


# ---------------- perfil e dentes ----------------
PERFIL = [(0.0, 0.0), (D, 0.0), (D, H), (ZT, H), (0.0, LIP)]     # (Z, Y), anti-horário
# painel -> (aresta do perfil, trecho [s0, s1] coberto ao longo da aresta, função s -> v do painel)
EXTENSAO = {
    'base':     (0, 0.0, D, lambda s: s),
    'traseiro': (1, T, H - T, lambda s: s - T),
    'tampa':    (2, 0.0, D - ZT, lambda s: (D - s) - ZT),
    'tela':     (3, T / CA, LF, lambda s: LF - s),
    'frente':   (4, T * SA, LIP - T, lambda s: (LIP - s) - T),
}


def dentes(a, b):
    n = odd((b - a) / DENTE)
    L = (b - a) / n
    return [(a + k * L, a + (k + 1) * L) for k in range(1, n, 2)]


def aresta(i):
    (z0, y0), (z1, y1) = PERFIL[i], PERFIL[(i + 1) % len(PERFIL)]
    L = math.hypot(z1 - z0, y1 - y0)
    d = ((z1 - z0) / L, (y1 - y0) / L)
    return (z0, y0), d, (-d[1], d[0])


def lateral_contorno():
    entalhes = []
    for nome, (i, a, b, _) in EXTENSAO.items():
        p0, d, n = aresta(i)
        for s0, s1 in dentes(a, b):
            q = lambda s, t: (p0[0] + d[0] * s + n[0] * t, p0[1] + d[1] * s + n[1] * t)
            entalhes.append(Polygon([q(s0, -1), q(s1, -1), q(s1, T), q(s0, T)]))
    g = Polygon(PERFIL).difference(unary_union(entalhes))
    return [(round(x, 4), round(y, 4)) for x, y in list(g.exterior.coords)[:-1]]


def painel(nome):
    """Contorno de um painel entre as laterais: corpo de W − 2T com dentes de T nas duas pontas."""
    i, a, b, f = EXTENSAO[nome]
    L = f(b) - f(a) if f(b) > f(a) else f(a) - f(b)
    tabs = sorted(tuple(sorted((f(s0), f(s1)))) for s0, s1 in dentes(a, b))
    pts = [(T, 0.0), (W - T, 0.0)]
    for v0, v1 in tabs:
        pts += [(W - T, v0), (W, v0), (W, v1), (W - T, v1)]
    pts += [(W - T, L), (T, L)]
    for v0, v1 in reversed(tabs):
        pts += [(T, v1), (0.0, v1), (0.0, v0), (T, v0)]
    return pts, L


# ---------------- peças ----------------
def pecas():
    P = {}

    def nova(nome, chave=None):
        c, L = painel(chave or nome)
        P[nome] = dict(nome=nome, tam=(W, L), contorno=c, furos=[], gravar=[])
        return P[nome]

    # PAINEL DA TELA (vista de fora): u = X, v ao longo da inclinação a partir da frente
    tl = nova('tela')
    tl['furos'].append(ret(TELA['cx'], TELA['v'], *TELA['janela'], r=2))
    for sx in (-1, 1):
        for sy in (-1, 1):
            tl['furos'].append(circ(TELA['cx'] + sx * MOLDURA['furos'][0], TELA['v'] + sy * MOLDURA['furos'][1], M3))

    # FRENTE BAIXA (vista de fora): u = X, v = Y − T
    fr = nova('frente')
    vm = fr['tam'][1] / 2
    fr['furos'].append(circ(W - 16, vm, 5.2))                            # LED de ligado (5 mm)
    fr['gravar'] += texto('COMEL', 34, vm - 3.0, 6.5) + texto('BASIC V2 · 64K', 96, vm - 1.6, 3.2) + texto('LIGADO', W - 34, vm - 1.4, 3.0)

    # TRASEIRO (vista de fora, por trás): u = W − X, v = Y − T
    tr = nova('traseiro')
    U = lambda X: W - X
    V = lambda Y: Y - T
    X, _ = tsda(68.4, 47)                                                # RJ-45 do Digi Connect ME
    tr['furos'].append(ret(U(X), V(Y_PLACA + 1.9 + 9.6), 20.4, 19.8, r=1))
    tr['gravar'] += texto('REDE', U(X), V(Y_PLACA + 26), 4)
    X, _ = tsda(23, 47)                                                  # DB9 da TSDA
    ydb = V(Y_PLACA + 1.6 + 6.6)
    tr['furos'].append(ret(U(X), ydb, 19.0, 9.0, r=2))
    for s_ in (-1, 1):
        tr['furos'].append(circ(U(X) + s_ * 12.5, ydb, M3))
    tr['gravar'] += texto('RS-232', U(X), ydb + 10, 4)
    jx, _ = comel(COMEL_POS['J7'][0] - 5.54, 0)                          # joystick (DB9 macho em 90°)
    tr['furos'].append(ret(U(jx), ydb, 19.0, 9.0, r=2))
    for s_ in (-1, 1):
        tr['furos'].append(circ(U(jx) + s_ * 12.5, ydb, M3))
    tr['gravar'] += texto('JOYSTICK', U(jx), ydb + 10, 4)
    ax, _ = comel(COMEL_POS['J6'][0], 0)                                 # áudio P2 (boca na borda da placa)
    tr['furos'].append(circ(U(ax), V(Y_PLACA + 1.6 + 2.6), 6.5))
    tr['gravar'] += texto('AUDIO', U(ax), V(Y_PLACA + 13), 4)
    ux, _ = comel(COMEL_POS['J2'][0] - 3.5, 0)                          # USB-A duplo (teclado), boca na borda
    uy = V(Y_PLACA + 1.6 + 7.8)
    tr['furos'].append(ret(U(ux), uy, USB['w'], USB['h'], r=1))
    tr['gravar'] += texto('USB', U(ux), uy + USB['h'] / 2 + 3, 4)
    tr['furos'].append(ret(U(IEC['X']), V(IEC['Y']), IEC['w'], IEC['h'], r=1))   # IEC C14 com chave e fusível
    tr['gravar'] += texto('100-240 V~  ·  FUSIVEL 1 A', U(IEC['X']), V(IEC['Y'] + 19), 3.4)
    for i in range(10):                                                  # ventilação no alto
        tr['furos'].append(oblongo(U(14 + i * 9.5), V(100), 4, 26))
    tr['gravar'] += texto('COMEL', U(112), V(62), 9)
    P['traseiro'] = tr

    # BASE (vista de cima, de dentro): u = X, v = Z
    ba = nova('base')
    for bx, by in [(4.6, 18.8), (4.6, 31.9)]:                          # furos de fixação da TSDA
        ba['furos'].append(circ(*tsda(bx, by), M3))
    xr, _ = tsda(40, 0)
    for local in (6.0, 14.0):                                           # encaixes do apoio da TSDA
        _, z = tsda(40, 10.0 + local)
        ba['furos'].append(ret(xr, z, T + 0.2, 6.2))
    for h in ('H1', 'H2', 'H3', 'H4'):                                   # placa COMEL
        ba['furos'].append(circ(*comel(*COMEL_POS[h][:2]), M3))
    fx = FONTE['x0'] + FONTE['L'] / 2
    for s_ in (-1, 1):                                                  # fonte: 2 × M3, 87 mm (oblongos)
        ba['furos'].append(oblongo(fx + s_ * 43.5, FONTE['z0'] + FONTE['P'] / 2, 3.6, 12))
    for i in range(12):                                                 # ventilação embaixo da tela
        ba['furos'].append(oblongo(14 + i * 9.0, 22, 4, 24))
    ba['gravar'] += texto('TSDA', tsda(62, 30)[0], tsda(62, 30)[1] - 1.5, 4) + texto('COMEL', *comel(45, 32), 5)
    ba['gravar'] += texto('FONTE RD-35A', fx, FONTE['z0'] + FONTE['P'] / 2 - 1.5, 4)

    # TAMPA (vista de cima): u = X, v = Z − ZT — ventilação sobre a fonte e sobre as placas
    tp = nova('tampa')
    for i in range(9):
        tp['furos'].append(oblongo(FONTE['x0'] + 10 + i * 9.5, 75 - ZT, 4, 40))
    for i in range(13):
        tp['furos'].append(oblongo(14 + i * 9.5, 158 - ZT, 4, 30))

    # LATERAIS (vista de fora). Esquerda: u = Z, v = Y. Direita: u = D − Z (espelhada).
    perfil = lateral_contorno()
    le = dict(nome='lateral-esquerda', tam=(D, H), contorno=perfil, furos=[], gravar=[])
    _, zu = comel(0, COMEL_POS['U1'][1])                                 # USB do Pico 2 e microSD
    le['furos'].append(ret(zu, Y_PLACA + 1.6 + 8.5 + 1.0 + 1.45, 12.0, 8.0, r=1.5))
    le['gravar'] += texto('USB', zu, Y_PLACA + 20.5, 3.4)
    _, zs = comel(0, COMEL_POS['J5'][1])
    le['furos'].append(ret(zs, Y_PLACA + 1.6 + 1.0, 18.0, 5.0, r=1.5))
    le['gravar'] += texto('microSD', zs, Y_PLACA + 6.5, 3.4)
    for i in range(7):
        le['furos'].append(oblongo(112 + i * 10, 96, 4, 30))
    P['lateral-esquerda'] = le

    esp = lambda poly: [(D - x, y) for x, y in reversed(poly)]
    furos_d = [oblongo(FONTE['z0'] + 8 + i * 9.5, T + 20, 4, 26) for i in range(8)]
    furos_d += [oblongo(112 + i * 10, 96, 4, 30) for i in range(7)]
    P['lateral-direita'] = dict(nome='lateral-direita', tam=(D, H), contorno=esp(perfil), furos=[esp(f) for f in furos_d], gravar=[])

    # MOLDURAS DA TELA (sanduíche atrás do painel inclinado)
    mw, mh = MOLDURA['ext']
    for nome, janela in [('moldura-espacador-1', MOLDURA['espaco']), ('moldura-espacador-2', MOLDURA['espaco']), ('moldura-trava', MOLDURA['trava'])]:
        m = dict(nome=nome, tam=(mw, mh), contorno=ret(mw / 2, mh / 2, mw, mh, r=3), furos=[ret(mw / 2, mh / 2, *janela, r=1)], gravar=[])
        for sx in (-1, 1):
            for sy in (-1, 1):
                m['furos'].append(circ(mw / 2 + sx * MOLDURA['furos'][0], mh / 2 + sy * MOLDURA['furos'][1], M3))
        P[nome] = m

    # APOIO da TSDA (costela com 2 dentes que encaixam na base)
    L, A = 20.0, STANDOFF
    ap = [(0, T), (3, T), (3, 0), (9, 0), (9, T), (11, T), (11, 0), (17, 0), (17, T), (L, T), (L, T + A), (0, T + A)]
    P['apoio-tsda'] = dict(nome='apoio-tsda', tam=(L, T + A), contorno=ap, furos=[], gravar=[])
    return P


# posição de cada peça na caixa: origem O e eixos U (u), V (v), N (espessura)
VT, NT = (0.0, CA, SA), (0.0, -SA, CA)             # direção "para cima" da tela e normal para dentro
POSE = {
    'tela': dict(O=(0, LIP, 0), U=(1, 0, 0), V=VT, N=NT),
    'frente': dict(O=(0, T, 0), U=(1, 0, 0), V=(0, 1, 0), N=(0, 0, 1)),
    'traseiro': dict(O=(W, T, D), U=(-1, 0, 0), V=(0, 1, 0), N=(0, 0, -1)),
    'lateral-esquerda': dict(O=(0, 0, 0), U=(0, 0, 1), V=(0, 1, 0), N=(1, 0, 0)),
    'lateral-direita': dict(O=(W, 0, D), U=(0, 0, -1), V=(0, 1, 0), N=(-1, 0, 0)),
    'base': dict(O=(0, 0, 0), U=(1, 0, 0), V=(0, 0, 1), N=(0, 1, 0)),
    'tampa': dict(O=(0, H - T, ZT), U=(1, 0, 0), V=(0, 0, 1), N=(0, 1, 0)),
}
_mw, _mh = MOLDURA['ext']
for _k, _n in enumerate(['moldura-espacador-1', 'moldura-espacador-2', 'moldura-trava'], 1):
    _c = (TELA['cx'], LIP + TELA['v'] * CA, TELA['v'] * SA)
    _o = tuple(_c[j] + NT[j] * _k * T - (1, 0, 0)[j] * _mw / 2 - VT[j] * _mh / 2 for j in range(3))
    POSE[_n] = dict(O=_o, U=(1, 0, 0), V=VT, N=NT)
_xr, _zr = tsda(40, 10)
POSE['apoio-tsda'] = dict(O=(_xr + T / 2, 0, _zr), U=(0, 0, 1), V=(0, 1, 0), N=(-1, 0, 0))

# arranjo nas chapas (peça, x, y)
ARRANJO = [
    [('base', 5, 5), ('traseiro', 5, 200), ('tampa', 245, 5), ('tela', 245, 150), ('frente', 245, 275), ('apoio-tsda', 485, 5)],
    [('lateral-esquerda', 5, 5), ('lateral-direita', 205, 5),
     ('moldura-espacador-1', 5, 145), ('moldura-espacador-2', 200, 145), ('moldura-trava', 395, 145)],
]


def kerf_offset(pol, k, externo):
    if k <= 0:
        return pol
    from shapely.geometry import Polygon
    g = Polygon(pol).buffer(k / 2 if externo else -k / 2, join_style=2, mitre_limit=3)
    return list(g.exterior.coords)[:-1]


def svg_path(poly, ox, oy, hgt):
    return 'M' + ' L'.join(f'{x + ox:.3f},{hgt - (y + oy):.3f}' for x, y in poly) + ' Z'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--kerf', type=float, default=0.0, help='largura do corte do laser em mm (ex.: 0.15)')
    ap.add_argument('--saida', default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'saida'))
    a = ap.parse_args()
    os.makedirs(os.path.join(a.saida, 'pecas'), exist_ok=True)
    P = pecas()
    for p in P.values():
        p['contorno_corte'] = kerf_offset(p['contorno'], a.kerf, True)
        p['furos_corte'] = [kerf_offset(f, a.kerf, False) for f in p['furos']]

    import ezdxf
    for i, folha in enumerate(ARRANJO, 1):
        cw, ch = CHAPA
        partes = []
        doc = ezdxf.new('R2010', setup=True); doc.units = ezdxf.units.MM
        doc.layers.add('CORTE', color=1); doc.layers.add('GRAVAR', color=5); doc.layers.add('CHAPA', color=8)
        msp = doc.modelspace()
        msp.add_lwpolyline([(0, 0), (cw, 0), (cw, ch), (0, ch)], close=True, dxfattribs={'layer': 'CHAPA'})
        for nome, ox, oy in folha:
            p = P[nome]
            d = ' '.join(svg_path(f, ox, oy, ch) for f in [p['contorno_corte']] + p['furos_corte'])
            partes.append(f'<path d="{d}" fill="none" stroke="#ff0000" stroke-width="0.1"/>')
            if p['gravar']:
                g = ' '.join(svg_path(f, ox, oy, ch) for f in p['gravar'])
                partes.append(f'<path d="{g}" fill="#0000ff" fill-rule="evenodd" stroke="none"/>')
            partes.append(f'<text x="{ox + 2:.1f}" y="{ch - oy - p["tam"][1] - 1.5:.1f}" font-size="3.5" fill="#888" font-family="sans-serif">{nome} (não cortar este texto)</text>')
            for f in [p['contorno_corte']] + p['furos_corte']:
                msp.add_lwpolyline([(x + ox, y + oy) for x, y in f], close=True, dxfattribs={'layer': 'CORTE'})
            for f in p['gravar']:
                msp.add_lwpolyline([(x + ox, y + oy) for x, y in f], close=True, dxfattribs={'layer': 'GRAVAR'})
        svg = (f'<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" width="{cw}mm" height="{ch}mm" viewBox="0 0 {cw} {ch}">\n'
               f'<rect x="0" y="0" width="{cw}" height="{ch}" fill="none" stroke="#cccccc" stroke-width="0.2"/>\n' + '\n'.join(partes) + '\n</svg>\n')
        open(os.path.join(a.saida, f'chapa-{i}.svg'), 'w').write(svg)
        doc.saveas(os.path.join(a.saida, f'chapa-{i}.dxf'))

    for nome, p in P.items():                                       # cada peça sozinha
        w, h = p['tam']; m = 4
        d = ' '.join(svg_path(f, m, m, h + 2 * m) for f in [p['contorno_corte']] + p['furos_corte'])
        g = ' '.join(svg_path(f, m, m, h + 2 * m) for f in p['gravar'])
        open(os.path.join(a.saida, 'pecas', f'{nome}.svg'), 'w').write(
            f'<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" width="{w + 2 * m}mm" height="{h + 2 * m}mm" viewBox="0 0 {w + 2 * m} {h + 2 * m}">\n'
            f'<path d="{d}" fill="none" stroke="#ff0000" stroke-width="0.1"/>\n' + (f'<path d="{g}" fill="#0000ff" fill-rule="evenodd"/>\n' if g else '') + '</svg>\n')

    out = dict(W=W, H=H, D=D, T=T, lip=LIP, ang=ANG, zt=ZT, tela=TELA, fonte=FONTE, zBorda=Z_BORDA, tsdaX0=TSDA_X0,
               comelX0=COMEL_X0, iec=IEC, yPlaca=Y_PLACA, comelSize=COMEL_SIZE,
               pecas=[dict(nome=n, contorno=[[round(x, 3), round(y, 3)] for x, y in p['contorno']],
                           furos=[[[round(x, 3), round(y, 3)] for x, y in f] for f in p['furos']], **POSE[n]) for n, p in P.items()])
    json.dump(out, open(os.path.join(a.saida, 'carcaca.json'), 'w'))
    area = sum(p['tam'][0] * p['tam'][1] for p in P.values()) / 1e6
    print(f'{len(P)} peças, {len(ARRANJO)} chapas de {CHAPA[0]:.0f} × {CHAPA[1]:.0f} mm, área das peças {area:.3f} m², kerf {a.kerf} mm')


if __name__ == '__main__':
    main()
