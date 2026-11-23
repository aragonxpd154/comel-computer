/*
 * COMEL — teclado USB (HID boot) → matriz 8×8 do C64. GPL-3.0.
 */
#pragma once
#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Layout físico do teclado USB (o que está impresso nas teclas). */
#define KBD_LAYOUT_ABNT2 0
#define KBD_LAYOUT_US    1
#ifndef KBD_LAYOUT
#define KBD_LAYOUT KBD_LAYOUT_ABNT2
#endif

/* Matriz atual: kbd_matrix[coluna] tem o bit da linha ligado para cada tecla pressionada.
 * Coluna = bit do $DC00 (PA), linha = bit do $DC01 (PB). Escrita no núcleo 1, lida no 0. */
extern volatile uint8_t kbd_matrix[8];
/* Teclas "digitadas" pelo próprio firmware (F9 / Shift+F9), somadas à matriz acima. */
extern volatile uint8_t kbd_inject[8];

/* Joystick feito no teclado numérico (Num Lock desligado): mesmos bits do joystick da placa */
extern volatile uint8_t kbd_joystick;

/* Ações especiais, consumidas pelo núcleo 0 a cada quadro */
#define KBD_ACT_RESET     0x01   /* F12        → reset do C64 */
#define KBD_ACT_RESTORE   0x02   /* Page Up    → RESTORE (NMI) */
#define KBD_ACT_SWAPJOY   0x04   /* F10        → troca o joystick de porta */
#define KBD_ACT_LOADDIR   0x08   /* F9         → digita LOAD"$",8 e LIST */
#define KBD_ACT_LOADRUN   0x10   /* Shift+F9   → digita LOAD"*",8,1 e RUN */
uint8_t kbd_take_actions(void);

/* Relatório de teclado (formato boot: modificadores, reservado, 6 teclas) de um dispositivo. */
void kbd_report(uint8_t slot, const uint8_t *report);
void kbd_release(uint8_t slot);

/* Digitação automática (núcleo 0): fila de texto ASCII que vai sendo "teclado" quadro a quadro. */
void kbd_type(const char *text);
void kbd_type_tick(void);      /* chamar uma vez por quadro */

#ifdef __cplusplus
}
#endif
