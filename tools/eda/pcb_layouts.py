"""Posicionamento físico (mm, relativo ao canto superior esquerdo da placa).

(x, y, rotação°) — KiCad: rotação positiva = anti-horária vista de cima.
A borda de cima (y = 0) da placa fica voltada para o painel traseiro da carcaça e a de baixo
(y = 64, com o borne da fonte) fica voltada para a fonte.
Todos os componentes ficam na face superior (montagem manual em uma só face).
"""

# =============================================================================
#  COMEL — 132 × 64 mm
# =============================================================================
COMEL_SIZE = (132.0, 64.0)
V, H = 90, 0

COMEL_POS = {
    # Borda traseira: USB-A duplo (bocas na borda), áudio (boca do P2 na borda) e joystick
    "J2": (33.5, 15.2, 180), "J6": (46.0, 6.6, 180), "J7": (75.54, 9.9, 180),

    # Alimentação (canto esquerdo de trás)
    "D1": (17.5, 11.0, 180), "C10": (8.0, 14.5, 0), "C11": (23.0, 19.5, H), "C12": (19.5, 19.5, H),
    "R28": (16.0, 19.5, 180), "D2": (12.2, 19.5, 0),

    # USB host — proteção ESD, resistores série, polyfuse e reservatório do VBUS
    "U3": (27.8, 21.6, 0),
    "R11": (31.4, 21.6, V), "R12": (33.35, 21.6, V), "R13": (35.3, 21.6, V), "R14": (37.25, 21.6, V),
    "F1": (15.5, 7.4, H), "C17": (15.5, 3.6, H),

    # Áudio — filtro RC de 2 polos junto ao jack
    "R20": (50.0, 17.5, 180), "C7": (50.0, 20.5, 180), "R21": (45.0, 17.5, 180), "C8": (45.0, 20.5, 180),
    "C9": (41.0, 18.0, 180), "R22": (41.0, 21.0, 180),

    # Joystick — resistores de proteção junto ao DB9
    "R23": (80.5, 17.5, V), "R24": (77.1, 17.5, V), "R25": (73.7, 17.5, V), "R26": (70.3, 17.5, V), "R27": (66.9, 17.5, V),

    # Serial até a TSDA (borda direita, do lado da TSDA na carcaça)
    "J3": (70.0, 26.0, 0), "J4": (70.0, 34.0, 0),
    "U2": (60.0, 27.0, 0), "C1": (53.5, 22.5, 180), "C2": (53.5, 25.5, 180), "C3": (53.5, 28.5, 180),
    "C4": (53.5, 31.5, 180), "C5": (49.0, 26.0, V),
    "JP1": (62.0, 19.5, 0),

    # microSD na borda esquerda (cartão entra pela lateral da carcaça) e reset
    "J5": (13.8, 30.0, 270),
    "R15": (30.0, 26.0, H), "R16": (30.0, 29.0, H), "R17": (30.0, 32.0, H),
    "R18": (26.0, 26.0, H), "R19": (26.0, 29.0, H), "C6": (26.0, 32.0, H),
    "SW1": (36.0, 28.0, 0),

    # Pico 2 com o USB saindo pela borda esquerda; DAC VGA e cabeçalho VGA à direita
    "U1": (25.5, 50.0, 90),
    **{f"R{i}": (54.0 + 4.5 * ((i - 1) // 5), 41.5 + 2.5 * ((i - 1) % 5), H) for i in range(1, 11)},
    "J1": (68.0, 57.0, 90),

    # Pontos de teste e furação
    **{f"TP{i}": (62.0 + 3.6 * (i - 1), 44.5, 0) for i in range(1, 8)},
    "H1": (4.0, 4.0, 0), "H2": (128.0, 4.0, 0), "H3": (128.0, 60.0, 0), "H4": (56.5, 60.0, 0),

    # Energia: saídas JST na borda traseira, proteção no meio, borne da RD-35A na borda da frente
    "J11": (92.5, 4.5, 0), "J12": (101.0, 4.5, 0), "J13": (109.5, 4.5, 0), "J14": (118.0, 4.5, 0),
    "R29": (104.0, 14.0, H), "D5": (108.5, 14.0, 180), "R30": (104.0, 17.5, H), "D6": (108.5, 17.5, 180),
    "R31": (114.5, 14.0, H), "C14": (119.0, 14.0, H), "C16": (119.0, 17.5, H),
    "C13": (100.5, 27.0, 0), "C15": (100.5, 38.5, 0),
    "D3": (113.5, 27.0, 0), "D4": (113.5, 33.0, 0),
    "F2": (125.0, 27.0, V), "F3": (125.0, 38.0, V),
    "J10": (100.0, 58.5, 0),
}

