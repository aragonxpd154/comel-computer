/*
 * COMEL — saída VGA 640×480 @ 60 Hz com quadro de 320×240 em RGB332. GPL-3.0.
 */
#pragma once
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define VGA_W       320
#define VGA_H       240
#define VGA_STRIDE  324   /* 320 pixels + 4 pretos que seguram o apagamento horizontal */

/* Relógio do sistema exigido pela temporização (pixel VGA = sys / 10). */
#define VGA_SYS_KHZ 252000

void vga_init(void);
uint8_t *vga_line(int y);                       /* ponteiro para a linha y do quadro */
void vga_put_line565(int y, const uint16_t *src, int n);
void vga_clear(uint8_t color);

static inline uint8_t vga_rgb332(uint8_t r, uint8_t g, uint8_t b) {
    return (uint8_t)((r & 0xE0) | ((g >> 3) & 0x1C) | (b >> 6));
}

#ifdef __cplusplus
}
#endif
