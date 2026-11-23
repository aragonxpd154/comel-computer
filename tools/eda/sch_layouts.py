"""Disposição dos blocos funcionais nas folhas A3 das duas placas."""
from pathlib import Path

from designs import COMEL_PARTS
from gen_schematic import Sheet, g

COMPANY = "Marcos Santos · github.com/aragonxpd154"


def build_comel(out: Path):
    s = Sheet("comel", "COMEL — Commodore 64 em Pico 2 ligado à TSDA 4011R1 (placa única)", [
        "Pico 2 (RP2350) emulando o C64 · VGA RGB332 · 2 × USB host · microSD · áudio · joystick · serial até a TSDA · energia da RD-35A",
        "U2, C1–C5 e J4 só são montados se o CN3 da TSDA for RS-232 (JP1 em 2-3)",
        "Licença GPL-3.0 · github.com/aragonxpd154/COMEL",
    ], paper="A2")
    P = {p.ref: p for p in COMEL_PARTS}

    # ---------- Linha A
    x, y = s.block("PROCESSADOR · U1 Raspberry Pi Pico 2 (RP2350)", 15, 20, 135, 122, [
        "GP0/1 UART0 · GP2/3 USB 2 · GP4/5 USB 1 · GP6–13 RGB332 · GP14/15 sync",
        "GP16–19 SPI0 (microSD) · GP20 PWM áudio · GP21/22/26/27/28 joystick",
    ])
    ux, uy = g(x + 52), g(y + 58)
    s.place(P["U1"], ux, uy, 0, ref_xy=(ux, g(uy - 29.21)), val_xy=(ux, g(uy + 29.21)))
    for i in range(7):
        p = P[f"TP{i + 1}"]
        cx, cy = x + 103, y + 14 + i * 8.89
        s.place(p, cx, cy, 90, ref_xy=(g(cx - 2.54), g(cy - 3.81)), hide_val=True)
    for i in range(4):
        p = P[f"H{i + 1}"]
        cx, cy = x + 120, y + 16 + i * 12.7
        s.place(p, cx, cy, 0, ref_xy=(g(cx + 5.08), g(cy - 1.27)), val_xy=(g(cx + 5.08), g(cy + 1.27)))

    x, y = s.block("VÍDEO VGA RGB332 · J1 → controladora da tela (J4)", 155, 20, 125, 122, [
        "0,7 V em 75 Ω: R 499/1k/2k · G 499/1k/2k · B 390/820 (256 cores)",
        "Sincronismos com 100 Ω em série · cabo flat 2×5 até a PCB800099",
    ])
    s.column_parts(P, [["R1", "R2", "R3", "R4", "R5", "R6"], ["R7", "R8", "R9", "R10"]], x, y, top=17.78)
    jx, jy = g(x + 100), g(y + 45)
    s.place(P["J1"], jx, jy, 0, ref_xy=(jx, g(jy - 10.16)), val_xy=(jx, g(jy + 10.16)))

    x, y = s.block("TECLADO · 2 × USB HOST · J2 (USB-A duplo)", 285, 20, 120, 122, [
        "USB 1 = GP4 D+ / GP5 D− · USB 2 = GP2 D+ / GP3 D− (full/low speed pelo PIO)",
        "F1 1 A no VBUS · U3 USBLC6-4SC6 contra ESD · 27 Ω em série nas linhas de dados",
    ])
    s.column_parts(P, [["R11", "R12", "F1"], ["R13", "R14", "C17"]], x, y, top=17.78, x0=20.32)
    qx, qy = g(x + 30.48), g(y + 75)
    s.place(P["U3"], qx, qy, 0, ref_xy=(qx, g(qy - 8.89)), val_xy=(qx, g(qy + 8.89)))
    jx, jy = g(x + 88.9), g(y + 70)
    s.place(P["J2"], jx, jy, 0, ref_xy=(jx, g(jy - 16.51)), val_xy=(jx, g(jy + 16.51)))

    # ---------- Linha B
    x, y = s.block("SERIAL ATÉ A TSDA 4011R1 · J3 TTL · J4 RS-232 (opcional)", 15, 148, 160, 125, [
        "Digi Connect ME em modo servidor TCP: Telnet no IP da TSDA = porta RS-232 do C64",
        "Sem controle de fluxo · JP1 fechado 1-2 (TTL) · para RS-232: abrir 1-2, fechar 2-3 e montar U2/C1–C5",
    ])
    ux, uy = g(x + 45), g(y + 52)
    s.place(P["U2"], ux, uy, 0, ref_xy=(ux, g(uy - 26.67)), val_xy=(ux, g(uy + 26.67)))
    s.column_parts(P, [["C1", "C2", "C3", "C4", "C5"]], x, y, top=20.32, x0=101.6)
    jx = g(x + 140)
    s.place(P["J3"], jx, g(y + 25), 0, ref_xy=(jx, g(y + 15)), val_xy=(jx, g(y + 38)))
    s.place(P["J4"], jx, g(y + 70), 0, ref_xy=(jx, g(y + 60)), val_xy=(jx, g(y + 83)))
    px, py = g(x + 15.24), g(y + 100)
    s.place(P["JP1"], px, py, 0, ref_xy=(px, g(py - 5.08)), val_xy=(px, g(py + 5.08)))

    x, y = s.block("microSD · J5 (SPI0)", 180, 148, 110, 62, ["Pull-ups de 10k em todas as linhas de dados"])
    jx, jy = g(x + 33), g(y + 30)
    s.place(P["J5"], jx, jy, 0, ref_xy=(jx, g(jy - 17.78)), val_xy=(jx, g(jy + 20.32)))
    s.column_parts(P, [["R15", "R16", "R17"], ["R18", "R19", "C6"]], x, y, top=15.24, x0=63.5, colw=30.48)

    x, y = s.block("ÁUDIO (SID) · J6", 180, 213, 110, 60, [
        "PWM de GP20 → RC 2 polos (≈ 16 kHz) → 10 µF → P2 mono",
    ])
    s.column_parts(P, [["R20", "C7", "R21"], ["C8", "C9", "R22"]], x, y, top=15.24, x0=20.32, colw=35.56)
    jx, jy = g(x + 80), g(y + 25)
    s.place(P["J6"], jx, jy, 0, ref_xy=(jx, g(jy - 7.62)), val_xy=(jx, g(jy + 7.62)))

    x, y = s.block("JOYSTICK · J7 (Atari / C64)", 295, 148, 110, 62, [
        "Chaves fecham para o GND · pull-ups internos do RP2350 · 1k de proteção",
    ])
    s.column_parts(P, [["R23", "R24", "R25", "R26", "R27"]], x, y, top=12.7, x0=20.32, )
    jx, jy = g(x + 80), g(y + 28)
    s.place(P["J7"], jx, jy, 0, ref_xy=(jx, g(jy - 15.24)), val_xy=(jx, g(jy + 15.24)))

    x, y = s.block("PICO · VSYS · RESET", 295, 213, 110, 60, [
        "+5 V da placa → SS34 → VSYS (o USB do Pico continua isolado)",
    ])
    s.column_parts(P, [["D1", "C10", "C11"], ["C12", "R28", "D2"]], x, y, top=15.24, x0=20.32, colw=35.56)
    sx, sy = g(x + 99), g(y + 25.4)
    s.place(P["SW1"], sx, sy, 90, ref_xy=(g(sx + 3.81), g(sy - 1.27)), val_xy=(g(sx + 3.81), g(sy + 1.27)))

    # ---------- Coluna da energia (RD-35A)
    x, y = s.block("ENTRADA · J10 (Mean Well RD-35A)", 415, 20, 165, 70, [
        "1 +5 V · 2 COM · 3 +12 V · 4 COM — borne na borda da frente, entrada dos fios para fora",
        "Carga mínima da RD-35A: 0,3 A no 5 V e 0,2 A no 12 V",
    ])
    jx, jy = g(x + 82), g(y + 30)
    s.place(P["J10"], jx, jy, 0, ref_xy=(jx, g(jy - 10.16)), val_xy=(jx, g(jy + 12.7)))
    for i, n in enumerate(["+5V_IN", "+12V_IN", "VSYS", "GND"]):
        s.flag(n, x + 15.24 + i * 22.86, y + 48.26)

    x, y = s.block("TRILHO 5 V · F2 2 A · D3 TVS", 415, 95, 165, 75, [
        "SMBJ5.0CA grampeia surtos · polyfuse rearma sozinho · R31 alimenta o LED da frente",
    ])
    s.column_parts(P, [["F2", "D3", "C13"], ["C14", "R29", "D5"], ["R31"]], x, y, top=17.78, x0=25.4, colw=48.26)

    x, y = s.block("TRILHO 12 V · F3 1 A · D4 TVS", 415, 175, 165, 75, [
        "Somente a tela de 7\" usa o 12 V (backlight ≈ 0,5 A)",
    ])
    s.column_parts(P, [["F3", "D4", "C15"], ["C16", "R30", "D6"]], x, y, top=17.78, x0=25.4, colw=48.26)

    x, y = s.block("SAÍDAS DE ENERGIA · JST-XH 2 vias", 15, 280, 390, 60, [
        "J11 → CN2 da TSDA (cabo conforme a pinagem medida) · J12 → controladora da tela · J13 → 5 V auxiliar · J14 → LED da frente",
    ])
    for i, j in enumerate(["J11", "J12", "J13", "J14"]):
        jx, jy = g(x + 40 + i * 95), g(y + 25)
        s.place(P[j], jx, jy, 0, ref_xy=(jx, g(jy - 7.62)), val_xy=(jx, g(jy + 7.62)))

    s.write(out, company=COMPANY)


