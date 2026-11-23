#!/usr/bin/env python3
"""Gera a biblioteca própria do projeto em hardware/lib/:

  COMEL.kicad_sym                          símbolo do Raspberry Pi Pico 2 (40 pinos)
  COMEL.pretty/RaspberryPi_Pico_Socket     footprint THT (2 barras fêmea 1×20, fileiras a 17,78 mm)

O modelo 3D (STEP) é gerado por make_3d_models.py.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "hardware" / "lib"

LEFT = [  # pinos 1..20, de cima para baixo (USB em cima)
    ("1", "GP0", "bidirectional"), ("2", "GP1", "bidirectional"), ("3", "GND", "power_in"),
    ("4", "GP2", "bidirectional"), ("5", "GP3", "bidirectional"), ("6", "GP4", "bidirectional"),
    ("7", "GP5", "bidirectional"), ("8", "GND", "power_in"), ("9", "GP6", "bidirectional"),
    ("10", "GP7", "bidirectional"), ("11", "GP8", "bidirectional"), ("12", "GP9", "bidirectional"),
    ("13", "GND", "power_in"), ("14", "GP10", "bidirectional"), ("15", "GP11", "bidirectional"),
    ("16", "GP12", "bidirectional"), ("17", "GP13", "bidirectional"), ("18", "GND", "power_in"),
    ("19", "GP14", "bidirectional"), ("20", "GP15", "bidirectional"),
]
RIGHT = [  # pinos 40..21, de cima para baixo
    ("40", "VBUS", "power_out"), ("39", "VSYS", "power_in"), ("38", "GND", "power_in"),
    ("37", "3V3_EN", "input"), ("36", "3V3_OUT", "power_out"), ("35", "ADC_VREF", "input"),
    ("34", "GP28/A2", "bidirectional"), ("33", "AGND", "power_in"), ("32", "GP27/A1", "bidirectional"),
    ("31", "GP26/A0", "bidirectional"), ("30", "RUN", "input"), ("29", "GP22", "bidirectional"),
    ("28", "GND", "power_in"), ("27", "GP21", "bidirectional"), ("26", "GP20", "bidirectional"),
    ("25", "GP19", "bidirectional"), ("24", "GP18", "bidirectional"), ("23", "GND", "power_in"),
    ("22", "GP17", "bidirectional"), ("21", "GP16", "bidirectional"),
]
F = "(effects (font (size 1.27 1.27)))"
FH = "(effects (font (size 1.27 1.27)) hide)"


def pin(kind, x, y, ang, name, num):
    return (f'      (pin {kind} line (at {x} {y} {ang}) (length 5.08)\n'
            f'        (name "{name}" {F})\n        (number "{num}" {F}))\n')


def symbol_lib() -> str:
    out = ['(kicad_symbol_lib (version 20220914) (generator comel_tools)\n',
           '  (symbol "RaspberryPi_Pico2" (pin_names (offset 1.016)) (in_bom yes) (on_board yes)\n',
           f'    (property "Reference" "U" (at 0 29.21 0) {F})\n',
           f'    (property "Value" "Pico 2" (at 0 -29.21 0) {F})\n',
           f'    (property "Footprint" "COMEL:RaspberryPi_Pico_Socket" (at 0 -31.75 0) {FH})\n',
           f'    (property "Datasheet" "https://datasheets.raspberrypi.com/pico/pico-2-datasheet.pdf" (at 0 0 0) {FH})\n',
           f'    (property "ki_keywords" "RP2350 Raspberry Pi Pico 2 module" (at 0 0 0) {FH})\n',
           f'    (property "ki_description" "Raspberry Pi Pico 2 (RP2350, 520 kB SRAM, 4 MB flash) — módulo de 40 pinos" (at 0 0 0) {FH})\n',
           '    (symbol "RaspberryPi_Pico2_0_1"\n',
           '      (rectangle (start -12.7 26.67) (end 12.7 -26.67) (stroke (width 0.254) (type default)) (fill (type background)))\n',
           '    )\n',
           '    (symbol "RaspberryPi_Pico2_1_1"\n']
    for i, (n, name, kind) in enumerate(LEFT):
        out.append(pin(kind, -17.78, round(24.13 - 2.54 * i, 2), 0, name, n))
    for i, (n, name, kind) in enumerate(RIGHT):
        out.append(pin(kind, 17.78, round(24.13 - 2.54 * i, 2), 180, name, n))
    out.append('    )\n  )\n)\n')
    return "".join(out)


def footprint() -> str:
    """Footprint (KiCad 7). Origem no centro do módulo, USB para cima (y negativo)."""
    pads = []
    for i in range(20):
        y = round(-24.13 + 2.54 * i, 2)
        shape = "rect" if i == 0 else "circle"
        pads.append((str(i + 1), -8.89, y, shape))
        pads.append((str(40 - i), 8.89, y, "circle"))
    lines = ['(footprint "RaspberryPi_Pico_Socket" (version 20221018) (generator comel_tools)',
             '  (layer "F.Cu")',
             '  (descr "Raspberry Pi Pico / Pico 2 encaixado em 2 barras fêmea 1×20 (2,54 mm), fileiras a 17,78 mm")',
             '  (tags "RP2040 RP2350 Pico socket")',
             '  (attr through_hole)',
             '  (fp_text reference "REF**" (at 0 -27.4) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))',
             '  (fp_text value "Pico 2" (at 0 27.4) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))',
             '  (fp_text user "USB" (at 0 -23.6) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))',
             '  (fp_text user "${REFERENCE}" (at 0 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))']

    def rect(layer, x1, y1, x2, y2, w):
        for a, b in [((x1, y1), (x2, y1)), ((x2, y1), (x2, y2)), ((x2, y2), (x1, y2)), ((x1, y2), (x1, y1))]:
            lines.append(f'  (fp_line (start {a[0]} {a[1]}) (end {b[0]} {b[1]}) (stroke (width {w}) (type solid)) (layer "{layer}"))')
    rect("F.SilkS", -10.6, -25.6, 10.6, 25.6, 0.12)
    rect("F.Fab", -10.5, -25.5, 10.5, 25.5, 0.1)
    rect("F.CrtYd", -11.0, -26.8, 11.0, 26.0, 0.05)
    rect("F.SilkS", -4.0, -25.6, 4.0, -22.6, 0.12)            # posição do conector USB
    lines.append('  (fp_line (start -11.1 -24.13) (end -10.7 -24.13) (stroke (width 0.2) (type solid)) (layer "F.SilkS"))')
    for num, x, y, shape in pads:
        lines.append(f'  (pad "{num}" thru_hole {shape} (at {x} {y}) (size 1.7 1.7) (drill 1.0) (layers "*.Cu" "*.Mask"))')
    lines.append('  (model "${KIPRJMOD}/../lib/3d/RaspberryPi_Pico2_Socket.step" (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))')
    lines.append(')')
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    LIB.mkdir(parents=True, exist_ok=True)
    (LIB / "COMEL.kicad_sym").write_text(symbol_lib(), encoding="utf-8")
    (LIB / "COMEL.pretty").mkdir(exist_ok=True)
    (LIB / "COMEL.pretty" / "RaspberryPi_Pico_Socket.kicad_mod").write_text(footprint(), encoding="utf-8")
    print("escrito", LIB / "COMEL.kicad_sym", "e", LIB / "COMEL.pretty")
