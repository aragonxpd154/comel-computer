/*
 * COMEL — recursos do RP2350 usados pelo firmware. Os pinos vêm de pinagem.h
 * (o mesmo mapa da placa em hardware/comel). GPL-3.0.
 */
#pragma once
#include "pinagem.h"

/* PIO: PIO0 = USB host (Pico-PIO-USB, TX/RX/EOP), PIO2 = VGA. PIO1 fica livre. */
#define VGA_PIO         pio2

/* DMA: canal 0 = TX do Pico-PIO-USB, 2–3 = VGA, 4–5 = áudio */
#define VGA_DMA_DATA    2
#define VGA_DMA_CTRL    3
#define AUDIO_DMA_A     4
#define AUDIO_DMA_B     5
#define AUDIO_DMA_TIMER 0

/* Áudio */
#define AUDIO_RATE      32000       /* Hz — 252 MHz / 7875 */
#define AUDIO_BLOCK     512         /* amostras por bloco do reSID (16 ms) */

/* Joystick: as chaves fecham para o GND */
#define JOY_MASK_UP     0x01
#define JOY_MASK_DOWN   0x02
#define JOY_MASK_LEFT   0x04
#define JOY_MASK_RIGHT  0x08
#define JOY_MASK_FIRE   0x10
