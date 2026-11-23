"""Fonte única da verdade do projeto (netlist + valores + footprints).

Tudo o que está em hardware/ é GERADO a partir deste arquivo:
    python3 tools/build_all.py

COMEL — "Commodore" ligado na rede, numa placa só: Raspberry Pi Pico 2 emulando o C64,
        vídeo VGA RGB332 para a tela de 7", 2 portas USB host (teclado), microSD, áudio (SID), joystick,
        serial até a TSDA 4011R1 (Digi Connect ME) e a distribuição de energia da
        Mean Well RD-35A (5 V / 12 V) com TVS, polyfuse e LED em cada trilho.
        Só a fonte fica fora da placa.

Convenção de pinos (bibliotecas KiCad):
  Device:R / C / C_Polarized : 1 = topo (+ no eletrolítico), 2 = base
  Device:D / LED / Schottky  : 1 = catodo (K), 2 = anodo (A)
  Transistor_FET:BSS138      : 1 = G, 2 = S, 3 = D
  Jumper:SolderJumper_3      : 1 = A, 2 = comum, 3 = B   (fechado de fábrica 1-2)
"""
from dataclasses import dataclass


@dataclass
class Part:
    ref: str
    lib: str
    value: str
    fp: str
    pins: dict
    desc: str = ""
    note: str = ""
    mpn: str = ""
    dnp: bool = False


R0805 = "Resistor_SMD:R_0805_2012Metric"
C0805 = "Capacitor_SMD:C_0805_2012Metric"
XH = "Connector_JST:JST_XH_B{n}B-XH-A_1x{n:02d}_P2.50mm_Vertical"
OPC = "opcional"


def R(ref, val, a, b, desc="", note="", fp=R0805, dnp=False):
    return Part(ref, "Device:R", val, fp, {"1": a, "2": b}, desc or "Resistor 0805 1 %", note, dnp=dnp)


def C(ref, val, a, b, desc="", note="", fp=C0805, dnp=False):
    return Part(ref, "Device:C", val, fp, {"1": a, "2": b}, desc or "Capacitor cerâmico 0805 X7R", note, dnp=dnp)


def jst(ref, n, nets, val, desc):
    return Part(ref, f"Connector_Generic:Conn_01x{n:02d}", val, XH.format(n=n),
                {str(i + 1): net for i, net in enumerate(nets)}, desc, mpn=f"B{n}B-XH-A")


# =============================================================================
#  COMEL — placa única (132 × 64 mm)
# =============================================================================
PICO_PINS = {
    "1": "TSDA_TX", "2": "UART_RX", "3": "GND", "4": "USB2_DP_IO", "5": "USB2_DM_IO",
    "6": "USB1_DP_IO", "7": "USB1_DM_IO", "8": "GND",
    "9": "VGA_B0", "10": "VGA_B1", "11": "VGA_G0", "12": "VGA_G1", "13": "GND",
    "14": "VGA_G2", "15": "VGA_R0", "16": "VGA_R1", "17": "VGA_R2", "18": "GND",
    "19": "VGA_HS_IO", "20": "VGA_VS_IO",
    "21": "SD_MISO", "22": "SD_CS", "23": "GND", "24": "SD_SCK", "25": "SD_MOSI",
    "26": "AUDIO_PWM", "27": "JOY_UP", "28": "GND", "29": "JOY_DOWN", "30": "RUN",
    "31": "JOY_LEFT", "32": "JOY_RIGHT", "33": "GND", "34": "JOY_FIRE", "35": None,
    "36": "+3V3", "37": None, "38": "GND", "39": "VSYS", "40": None,
}

COMEL_PARTS = [
    Part("U1", "COMEL:RaspberryPi_Pico2", "Pico 2", "COMEL:RaspberryPi_Pico_Socket",
         PICO_PINS, "Raspberry Pi Pico 2 (RP2350) + 2 barras fêmea 1×20 de 2,54 mm — emulador C64"),

    # ---------------- vídeo VGA RGB332 (DAC de resistores para 75 Ω) ----------------
    R("R1", "499", "VGA_R2", "VGA_R", "DAC vermelho — bit 2 (MSB)"),
    R("R2", "1k", "VGA_R1", "VGA_R", "DAC vermelho — bit 1"),
    R("R3", "2k", "VGA_R0", "VGA_R", "DAC vermelho — bit 0"),
    R("R4", "499", "VGA_G2", "VGA_G", "DAC verde — bit 2 (MSB)"),
    R("R5", "1k", "VGA_G1", "VGA_G", "DAC verde — bit 1"),
    R("R6", "2k", "VGA_G0", "VGA_G", "DAC verde — bit 0"),
    R("R7", "390", "VGA_B1", "VGA_B", "DAC azul — bit 1 (MSB)"),
    R("R8", "820", "VGA_B0", "VGA_B", "DAC azul — bit 0"),
    R("R9", "100", "VGA_HS_IO", "VGA_HS", "Série do sincronismo horizontal"),
    R("R10", "100", "VGA_VS_IO", "VGA_VS", "Série do sincronismo vertical"),
    Part("J1", "Connector_Generic:Conn_02x05_Odd_Even", "VGA → TELA", "Connector_IDC:IDC-Header_2x05_P2.54mm_Vertical",
         {"1": "VGA_R", "2": "GND", "3": "VGA_G", "4": "GND", "5": "VGA_B", "6": "GND",
          "7": "VGA_HS", "8": "VGA_VS", "9": "GND", "10": None},
         "Cabeçalho IDC 2×5 — cabo flat até a entrada VGA (J4) da controladora PCB800099"),

    # ---------------- 2 × USB host (teclado) pelo PIO — Pico-PIO-USB ----------------
    Part("J2", "Connector:USB_A_Stacked", "USB 1 | USB 2", "Connector_USB:USB_A_Wuerth_61400826021_Horizontal_Stacked",
         {"1": "VBUS", "2": "USB1_DM", "3": "USB1_DP", "4": "GND",
          "5": "VBUS", "6": "USB2_DM", "7": "USB2_DP", "8": "GND", "9": "GND"},
         "USB-A duplo empilhado, 90° — teclado USB (e mouse/joystick USB no firmware)", mpn="61400826021"),
    R("R11", "27", "USB1_DP_IO", "USB1_DP", "Série D+ da USB 1 (GP4)"),
    R("R12", "27", "USB1_DM_IO", "USB1_DM", "Série D− da USB 1 (GP5)"),
    R("R13", "27", "USB2_DP_IO", "USB2_DP", "Série D+ da USB 2 (GP2)"),
    R("R14", "27", "USB2_DM_IO", "USB2_DM", "Série D− da USB 2 (GP3)"),
    Part("U3", "Power_Protection:USBLC6-4SC6", "USBLC6-4SC6", "Package_TO_SOT_SMD:SOT-23-6",
         {"1": "USB1_DP", "2": "GND", "3": "USB1_DM", "4": "USB2_DM", "5": "VBUS", "6": "USB2_DP"},
         "Proteção ESD das 4 linhas de dados das duas portas USB", mpn="USBLC6-4SC6"),
    Part("F1", "Device:Polyfuse", "1A", "Fuse:Fuse_1206_3216Metric", {"1": "+5V", "2": "VBUS"},
         "Polyfuse 1206 1 A — VBUS das duas portas USB", mpn="1206L110"),
    Part("C17", "Device:C", "47u", "Capacitor_SMD:C_1206_3216Metric", {"1": "VBUS", "2": "GND"},
         "Reservatório do VBUS (1206 X5R 10 V)"),

    # ---------------- serial até a TSDA (TTL direto ou RS-232 pelo MAX3232) ----------------
    jst("J3", 3, ["TSDA_TX", "TTL_RX", "GND"], "TSDA TTL",
        "JST-XH 3 vias — serial TTL 3,3 V até a TSDA (TX, RX, GND), sem controle de fluxo"),
    Part("JP1", "Jumper:SolderJumper_3_Bridged12", "RX TTL|232", "Jumper:SolderJumper-3_P1.3mm_Bridged12_RoundedPad1.0x1.5mm",
         {"1": "TTL_RX", "2": "UART_RX", "3": "RS_RX"}, "Escolhe a origem do RX: 1-2 TTL (de fábrica) · 2-3 MAX3232"),
    Part("U2", "Interface_UART:MAX3232", "MAX3232", "Package_SO:SOIC-16_3.9x9.9mm_P1.27mm",
         {"1": "U2_C1P", "2": "U2_VP", "3": "U2_C1N", "4": "U2_C2P", "5": "U2_C2N", "6": "U2_VN",
          "7": None, "8": None, "9": None, "10": "GND", "11": "TSDA_TX",
          "12": "RS_RX", "13": "RS_RXIN", "14": "RS_TX", "15": "GND", "16": "+3V3"},
         "Transceptor RS-232 3,3 V — só monte se o CN3 da TSDA for RS-232", OPC, "MAX3232ECDR", dnp=True),
    C("C1", "100n", "U2_C1P", "U2_C1N", "Bomba de carga MAX3232", OPC, dnp=True),
    C("C2", "100n", "U2_C2P", "U2_C2N", "Bomba de carga MAX3232", OPC, dnp=True),
    C("C3", "100n", "U2_VP", "GND", "Reservatório V+ do MAX3232", OPC, dnp=True),
    C("C4", "100n", "U2_VN", "GND", "Reservatório V− do MAX3232", OPC, dnp=True),
    C("C5", "100n", "+3V3", "GND", "Desacoplamento do MAX3232", OPC, dnp=True),
    jst("J4", 3, ["RS_TX", "RS_RXIN", "GND"], "TSDA RS-232",
        "JST-XH 3 vias — serial RS-232 até a TSDA (só com o U2 montado)"),

    # ---------------- microSD (SPI0) ----------------
    Part("J5", "Connector:Micro_SD_Card_Det_Hirose_DM3AT", "microSD", "Connector_Card:microSD_HC_Hirose_DM3AT-SF-PEJM5",
         {"1": "SD_DAT2", "2": "SD_CS", "3": "SD_MOSI", "4": "+3V3", "5": "SD_SCK", "6": "GND",
          "7": "SD_MISO", "8": "SD_DAT1", "9": None, "10": None, "11": "GND"},
         "Soquete microSD push-push — programas .PRG e imagens .D64", mpn="DM3AT-SF-PEJM5"),
    R("R15", "10k", "+3V3", "SD_CS", "Pull-up do CS do cartão"),
    R("R16", "10k", "+3V3", "SD_MOSI", "Pull-up do CMD"),
    R("R17", "10k", "+3V3", "SD_MISO", "Pull-up do DAT0"),
    R("R18", "10k", "+3V3", "SD_DAT1", "Pull-up do DAT1 (sem uso no SPI)"),
    R("R19", "10k", "+3V3", "SD_DAT2", "Pull-up do DAT2 (sem uso no SPI)"),
    C("C6", "100n", "+3V3", "GND", "Desacoplamento do cartão"),

    # ---------------- áudio (PWM → filtro RC de 2 polos) ----------------
    R("R20", "1k", "AUDIO_PWM", "AUD_F1", "Filtro passa-baixas — 1º polo (≈ 16 kHz)"),
    C("C7", "10n", "AUD_F1", "GND", "Filtro passa-baixas — 1º polo"),
    R("R21", "1k", "AUD_F1", "AUD_F2", "Filtro passa-baixas — 2º polo"),
    C("C8", "10n", "AUD_F2", "GND", "Filtro passa-baixas — 2º polo"),
    C("C9", "10u", "AUD_F2", "AUDIO_OUT", "Acoplamento AC da saída", fp="Capacitor_SMD:C_1206_3216Metric"),
    R("R22", "10k", "AUDIO_OUT", "GND", "Referência da saída de áudio"),
    Part("J6", "Connector_Audio:AudioJack3", "AUDIO", "Connector_Audio:Jack_3.5mm_CUI_SJ1-3523N_Horizontal",
         {"T": "AUDIO_OUT", "R": "AUDIO_OUT", "S": "GND"}, "Jack P2 3,5 mm — saída do SID (mono nos dois canais)",
         mpn="SJ1-3523N"),

    # ---------------- joystick (padrão Atari / C64) ----------------
    R("R23", "1k", "JOY_UP", "JOY_UP_C", "Proteção da entrada — cima"),
    R("R24", "1k", "JOY_DOWN", "JOY_DOWN_C", "Proteção da entrada — baixo"),
    R("R25", "1k", "JOY_LEFT", "JOY_LEFT_C", "Proteção da entrada — esquerda"),
    R("R26", "1k", "JOY_RIGHT", "JOY_RIGHT_C", "Proteção da entrada — direita"),
    R("R27", "1k", "JOY_FIRE", "JOY_FIRE_C", "Proteção da entrada — tiro"),
    Part("J7", "Connector:DE9_Plug_MountingHoles", "JOYSTICK",
         "Connector_Dsub:DSUB-9_Male_Horizontal_P2.77x2.84mm_EdgePinOffset9.90mm_Housed_MountingHolesOffset11.32mm",
         {"0": "GND", "1": "JOY_UP_C", "2": "JOY_DOWN_C", "3": "JOY_LEFT_C", "4": "JOY_RIGHT_C", "5": None,
          "6": "JOY_FIRE_C", "7": None, "8": "GND", "9": None},
         "DB9 macho 90° — joystick Atari/C64 (1 cima, 2 baixo, 3 esq., 4 dir., 6 tiro, 8 GND)"),

    # ---------------- alimentação ----------------
    Part("D1", "Device:D_Schottky", "SS34", "Diode_SMD:D_SMA", {"1": "VSYS", "2": "+5V"},
         "Schottky 3 A 40 V — 5 V → VSYS (isola o USB do Pico)", mpn="SS34"),
    Part("C10", "Device:C_Polarized", "100u/10V", "Capacitor_SMD:CP_Elec_6.3x7.7", {"1": "+5V", "2": "GND"},
         "Reservatório local de 5 V junto ao Pico"),
    C("C11", "100n", "VSYS", "GND", "Desacoplamento de VSYS"),
    C("C12", "100n", "+3V3", "GND", "Desacoplamento de 3V3"),
    R("R28", "1k", "+3V3", "LED_A", "Limitador do LED de 3,3 V"),
    Part("D2", "Device:LED", "Verde", "LED_SMD:LED_0805_2012Metric", {"1": "GND", "2": "LED_A"},
         "LED indicador de 3,3 V"),
    Part("SW1", "Switch:SW_Push", "RESET", "Button_Switch_THT:SW_PUSH_6mm", {"1": "RUN", "2": "GND"},
         "Botão de reset do Pico (RUN → GND)"),

    # ---------------- energia: entrada da Mean Well RD-35A e distribuição ----------------
    Part("J10", "Connector:Screw_Terminal_01x04", "RD-35A",
         "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-4-5.08_1x04_P5.08mm_Horizontal",
         {"1": "+5V_IN", "2": "GND", "3": "+12V_IN", "4": "GND"},
         "Borne 4 vias 5,08 mm na borda da frente — CH1 (+5 V) e CH2 (+12 V) da RD-35A"),
    Part("F2", "Device:Polyfuse", "2A", "Fuse:Fuse_1812_4532Metric", {"1": "+5V_IN", "2": "+5V"},
         "Polyfuse 1812 2 A — trilho de 5 V"),
    Part("F3", "Device:Polyfuse", "1A", "Fuse:Fuse_1812_4532Metric", {"1": "+12V_IN", "2": "+12V"},
         "Polyfuse 1812 1 A — trilho de 12 V"),
    Part("D3", "Device:D_TVS", "SMBJ5.0CA", "Diode_SMD:D_SMB", {"1": "+5V", "2": "GND"},
         "TVS 5 V bidirecional 600 W — surtos no 5 V", mpn="SMBJ5.0CA"),
    Part("D4", "Device:D_TVS", "SMBJ12CA", "Diode_SMD:D_SMB", {"1": "+12V", "2": "GND"},
         "TVS 12 V bidirecional 600 W — surtos no 12 V", mpn="SMBJ12CA"),
    Part("C13", "Device:C_Polarized", "220u/10V", "Capacitor_SMD:CP_Elec_8x10", {"1": "+5V", "2": "GND"},
         "Reservatório do 5 V"),
    C("C14", "100n", "+5V", "GND", "Desacoplamento do 5 V"),
    Part("C15", "Device:C_Polarized", "100u/25V", "Capacitor_SMD:CP_Elec_8x10", {"1": "+12V", "2": "GND"},
         "Reservatório do 12 V"),
    C("C16", "100n", "+12V", "GND", "Desacoplamento do 12 V"),
    R("R29", "1k", "+5V", "LED5_A", "Limitador do LED de 5 V"),
    Part("D5", "Device:LED", "Verde", "LED_SMD:LED_0805_2012Metric", {"1": "GND", "2": "LED5_A"}, "LED do trilho de 5 V"),
    R("R30", "2k2", "+12V", "LED12_A", "Limitador do LED de 12 V"),
    Part("D6", "Device:LED", "Amarelo", "LED_SMD:LED_0805_2012Metric", {"1": "GND", "2": "LED12_A"}, "LED do trilho de 12 V"),
    R("R31", "330", "+5V", "LED_FRENTE", "Limitador do LED vermelho do painel da frente"),
    jst("J11", 2, ["+5V", "GND"], "TSDA 5V", "Saída 5 V → CN2 da TSDA 4011R1 (cabo conforme a pinagem medida)"),
    jst("J12", 2, ["+12V", "GND"], "TELA 12V", "Saída 12 V → controladora PCB800099 da tela de 7\""),
    jst("J13", 2, ["+5V", "GND"], "AUX 5V", "Saída 5 V auxiliar (ventoinha, fita de LED...)"),
    jst("J14", 2, ["LED_FRENTE", "GND"], "LED FRENTE", "LED vermelho de 5 mm do painel da frente (anodo no pino 1)"),
]
for i, net in enumerate(["+5V", "+3V3", "GND", "VGA_HS", "TSDA_TX", "UART_RX", "+12V"], 1):
    COMEL_PARTS.append(Part(f"TP{i}", "Connector:TestPoint", net, "TestPoint:TestPoint_Pad_D1.5mm",
                            {"1": net}, "Ponto de teste SMD Ø1,5 mm"))
for i in range(1, 5):
    COMEL_PARTS.append(Part(f"H{i}", "Mechanical:MountingHole_Pad", "M3", "MountingHole:MountingHole_3.2mm_M3_Pad_Via",
                            {"1": "GND"}, "Furo de fixação M3 aterrado (espaçador de 8 mm)"))

COMEL_PWR_FLAGS = ["+5V_IN", "+12V_IN", "VSYS", "GND"]

BOARDS = {"comel": COMEL_PARTS}


def nets_of(parts):
    nets = {}
    for p in parts:
        for pin, n in p.pins.items():
            if n:
                nets.setdefault(n, []).append(f"{p.ref}.{pin}")
    return nets
