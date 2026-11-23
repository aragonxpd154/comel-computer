/*
 * COMEL — firmware do Commodore 64 na placa COMEL (Raspberry Pi Pico 2 / RP2350).
 * GPL-3.0 — github.com/aragonxpd154/COMEL
 *
 *   Núcleo 0: 6510 + VIC-II + CIAs (uma linha de varredura por vez, 50 Hz PAL).
 *   Núcleo 1: host USB nas duas portas (Pico-PIO-USB + TinyUSB) e o SID (reSID)
 *             preenchendo o áudio PWM.
 *   Hardware: VGA inteira em PIO2 + DMA, áudio por DMA, sem CPU na varredura.
 */
#include "pico/stdlib.h"
#include "pico/multicore.h"
#include "hardware/vreg.h"
#include "hardware/clocks.h"

extern "C" {
#include "vga.h"
#include "audio.h"
#include "ff.h"
#include "comel_board.h"
void usb_host_init(void);
void usb_host_task(void);
}
#include "comel_c64.h"

static FATFS fs;

static void core1_main(void) {
    usb_host_init();                 /* o temporizador de 1 ms do USB fica neste núcleo */
    audio_init(c64_audio_render);
    for (;;) {
        usb_host_task();
        audio_task();
    }
}

int main(void) {
    vreg_set_voltage(VREG_VOLTAGE_1_15);
    sleep_ms(2);
    set_sys_clock_khz(VGA_SYS_KHZ, true);   /* 252 MHz: 10 × 25,2 MHz (VGA) e 21 × 12 MHz (USB) */

    vga_init();

    bool sd = f_mount(&fs, "", 1) == FR_OK;
    roms_load(sd);
    c64_init(sd);

    multicore_launch_core1(core1_main);

    for (;;) c64_step();
}
