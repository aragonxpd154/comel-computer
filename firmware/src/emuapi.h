/*
 * COMEL — camada mínima entre o núcleo do C64 (Teensy64/MCUME) e a placa.
 * Só existe o que o núcleo realmente chama. GPL-3.0.
 */
#pragma once
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* RGB565, usado pela paleta do VIC-II. A conversão para RGB332 acontece em vga.c. */
#define RGBVAL16(r, g, b) ((((r >> 3) & 0x1f) << 11) | (((g >> 2) & 0x3f) << 5) | (((b >> 3) & 0x1f) << 0))

void emu_printf(const char *fmt, ...);
void emu_DrawLine16(unsigned short *VBuf, int width, int height, int line);
void emu_DrawVsync(void);

#ifdef __cplusplus
}
#endif
