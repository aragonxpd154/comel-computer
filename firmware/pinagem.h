/*
 * COMEL — mapa de pinos da placa COMEL (Raspberry Pi Pico 2 / RP2350)
 * Gerado a partir de tools/eda/designs.py (PICO_PINS). Use no port do emulador.
 */
#pragma once

/* Serial até a TSDA 4011R1 (Digi Connect ME) — UART0 sem controle de fluxo
 * (configure o Digi Connect ME com "Flow control: None") */
#define TSDA_UART        uart0
#define PIN_TSDA_TX      0   /* GP0  → J3.1 (TTL) e MAX3232 T1IN  */
#define PIN_TSDA_RX      1   /* GP1  ← JP1 (J3.2 TTL ou MAX3232 R1OUT) */

/* 2 × USB host (teclado, mouse, joystick USB) pelo PIO — biblioteca Pico-PIO-USB.
 * D− é sempre o pino seguinte ao D+ (PIO_USB_PINOUT_DPDM). 27 Ω em série na placa. */
#define PIN_USB1_DP      4   /* GP4 → J2 porta de baixo, D+ (GP5 = D−) */
#define PIN_USB2_DP      2   /* GP2 → J2 porta de cima,  D+ (GP3 = D−) */

/* Vídeo VGA RGB332 — 8 pinos consecutivos para o PIO (B0 é o menos significativo) */
#define PIN_VGA_BASE     6   /* GP6 B0, GP7 B1, GP8 G0, GP9 G1, GP10 G2, GP11 R0, GP12 R1, GP13 R2 */
#define PIN_VGA_HSYNC    14
#define PIN_VGA_VSYNC    15

/* microSD — SPI0 */
#define SD_SPI           spi0
#define PIN_SD_MISO      16
#define PIN_SD_CS        17
#define PIN_SD_SCK       18
#define PIN_SD_MOSI      19

/* Áudio (SID) — PWM no GP20, filtro RC de 2 polos na placa */
#define PIN_AUDIO_PWM    20

/* Joystick Atari/C64 (ativo em nível baixo — ligar os pull-ups internos) */
#define PIN_JOY_UP       21
#define PIN_JOY_DOWN     22
#define PIN_JOY_LEFT     26
#define PIN_JOY_RIGHT    27
#define PIN_JOY_FIRE     28
