/*
 * COMEL — saída VGA 640×480 @ 60 Hz, quadro de 320×240 em RGB332. GPL-3.0.
 *
 * Tudo roda em hardware: três máquinas de estado no PIO2 (HSYNC, VSYNC e RGB)
 * e dois canais de DMA. O canal de controle percorre uma lista de 512 ponteiros
 * de linha (cada linha do quadro aparece duas vezes, mais 32 linhas pretas) e
 * dispara o canal de dados, que empurra a linha para o PIO. A lista fica
 * alinhada em 2 KiB e o DMA dá a volta sozinho (modo anel), então a CPU não
 * participa da varredura.
 */
#include <string.h>
#include "pico/stdlib.h"
#include "hardware/pio.h"
#include "hardware/dma.h"
#include "hardware/clocks.h"

#include "vga.h"
#include "vga.pio.h"
#include "comel_board.h"

#define LIST_LEN 512                                  /* 32 pretas + 480 visíveis */

static uint8_t framebuffer[VGA_H][VGA_STRIDE] __attribute__((aligned(4)));
static uint8_t black_line[VGA_STRIDE] __attribute__((aligned(4)));
static const uint8_t *line_list[LIST_LEN] __attribute__((aligned(LIST_LEN * sizeof(void *))));

uint8_t *vga_line(int y) { return framebuffer[y]; }

void vga_clear(uint8_t color) {
    for (int y = 0; y < VGA_H; y++) {
        memset(framebuffer[y], color, VGA_W);
        memset(framebuffer[y] + VGA_W, 0, VGA_STRIDE - VGA_W);
    }
}

/* RGB565 → RGB332 (R2 R1 R0 G2 G1 G0 B1 B0, o mesmo byte que o DAC da placa espera) */
void __not_in_flash_func(vga_put_line565)(int y, const uint16_t *src, int n) {
    if ((unsigned)y >= VGA_H) return;
    uint8_t *d = framebuffer[y];
    if (n > VGA_W) n = VGA_W;
    for (int i = 0; i < n; i++) {
        uint32_t p = src[i];
        d[i] = (uint8_t)(((p >> 8) & 0xE0) | ((p >> 6) & 0x1C) | ((p >> 3) & 0x03));
    }
}

static void sm_setup(PIO pio, uint sm, uint offset, pio_sm_config c, uint32_t init_word) {
    sm_config_set_clkdiv(&c, (float)clock_get_hz(clk_sys) / 25200000.0f);
    pio_sm_init(pio, sm, offset, &c);
    pio_sm_put_blocking(pio, sm, init_word);
}

void vga_init(void) {
    PIO pio = VGA_PIO;
    const uint sm_h = 0, sm_v = 1, sm_rgb = 2;

    memset(black_line, 0, sizeof black_line);
    vga_clear(0);
    for (int i = 0; i < 32; i++) line_list[i] = black_line;
    for (int y = 0; y < VGA_H; y++) line_list[32 + 2 * y] = line_list[33 + 2 * y] = framebuffer[y];

    for (uint p = PIN_VGA_BASE; p <= PIN_VGA_VSYNC; p++) {
        pio_gpio_init(pio, p);
        gpio_set_drive_strength(p, GPIO_DRIVE_STRENGTH_8MA);
        gpio_set_slew_rate(p, GPIO_SLEW_RATE_FAST);
    }
    pio_sm_claim(pio, sm_h); pio_sm_claim(pio, sm_v); pio_sm_claim(pio, sm_rgb);

    uint off_h = pio_add_program(pio, &vga_hsync_program);
    uint off_v = pio_add_program(pio, &vga_vsync_program);
    uint off_rgb = pio_add_program(pio, &vga_rgb_program);

    pio_sm_config c = vga_hsync_program_get_default_config(off_h);
    sm_config_set_set_pins(&c, PIN_VGA_HSYNC, 1);
    pio_sm_set_consecutive_pindirs(pio, sm_h, PIN_VGA_HSYNC, 1, true);
    sm_setup(pio, sm_h, off_h, c, 654);

    c = vga_vsync_program_get_default_config(off_v);
    sm_config_set_set_pins(&c, PIN_VGA_VSYNC, 1);
    pio_sm_set_consecutive_pindirs(pio, sm_v, PIN_VGA_VSYNC, 1, true);
    sm_setup(pio, sm_v, off_v, c, 511);

    c = vga_rgb_program_get_default_config(off_rgb);
    sm_config_set_out_pins(&c, PIN_VGA_BASE, 8);
    sm_config_set_out_shift(&c, true, true, 32);           /* pixel 0 = byte menos significativo */
    pio_sm_set_consecutive_pindirs(pio, sm_rgb, PIN_VGA_BASE, 8, true);
    sm_setup(pio, sm_rgb, off_rgb, c, VGA_STRIDE - 1);

    /* sincronismos começam em nível alto (inativos) */
    pio_sm_exec(pio, sm_h, pio_encode_set(pio_pins, 1));
    pio_sm_exec(pio, sm_v, pio_encode_set(pio_pins, 1));

    /* DMA: dados (linha → FIFO do RGB) e controle (lista de linhas → endereço do canal de dados) */
    dma_channel_claim(VGA_DMA_DATA);
    dma_channel_claim(VGA_DMA_CTRL);

    dma_channel_config cd = dma_channel_get_default_config(VGA_DMA_DATA);
    channel_config_set_transfer_data_size(&cd, DMA_SIZE_32);
    channel_config_set_read_increment(&cd, true);
    channel_config_set_write_increment(&cd, false);
    channel_config_set_dreq(&cd, pio_get_dreq(pio, sm_rgb, true));
    channel_config_set_chain_to(&cd, VGA_DMA_CTRL);
    channel_config_set_high_priority(&cd, true);
    dma_channel_configure(VGA_DMA_DATA, &cd, &pio->txf[sm_rgb], NULL, VGA_STRIDE / 4, false);

    dma_channel_config cc = dma_channel_get_default_config(VGA_DMA_CTRL);
    channel_config_set_transfer_data_size(&cc, DMA_SIZE_32);
    channel_config_set_read_increment(&cc, true);
    channel_config_set_write_increment(&cc, false);
    channel_config_set_ring(&cc, false, 11);               /* 512 ponteiros × 4 bytes = 2^11 */
    channel_config_set_high_priority(&cc, true);
    dma_channel_configure(VGA_DMA_CTRL, &cc, &dma_hw->ch[VGA_DMA_DATA].al3_read_addr_trig,
                          line_list, 1, false);

    dma_channel_start(VGA_DMA_CTRL);
    pio_enable_sm_mask_in_sync(pio, (1u << sm_h) | (1u << sm_v) | (1u << sm_rgb));
}
