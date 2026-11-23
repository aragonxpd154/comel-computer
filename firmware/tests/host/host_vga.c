/* COMEL — "VGA" do teste: guarda o quadro 320×240 RGB332 e grava PPM. GPL-3.0. */
#include <stdio.h>
#include <string.h>
#include "vga.h"
static uint8_t fb[VGA_H][VGA_STRIDE];
uint8_t *vga_line(int y) { return fb[y]; }
void vga_clear(uint8_t c) { memset(fb, c, sizeof fb); }
void vga_init(void) { vga_clear(0); }
void vga_put_line565(int y, const uint16_t *src, int n) {
    if ((unsigned)y >= VGA_H) return;
    for (int i = 0; i < n && i < VGA_W; i++) { uint32_t p = src[i]; fb[y][i] = (uint8_t)(((p >> 8) & 0xE0) | ((p >> 6) & 0x1C) | ((p >> 3) & 0x03)); }
}
void host_save_ppm(const char *path) {
    FILE *f = fopen(path, "wb");
    fprintf(f, "P6\n%d %d\n255\n", VGA_W, VGA_H);
    for (int y = 0; y < VGA_H; y++) for (int x = 0; x < VGA_W; x++) {
        uint8_t p = fb[y][x];
        uint8_t rgb[3] = { (uint8_t)((p >> 5) * 255 / 7), (uint8_t)(((p >> 2) & 7) * 255 / 7), (uint8_t)((p & 3) * 255 / 3) };
        fwrite(rgb, 1, 3, f);
    }
    fclose(f);
}
