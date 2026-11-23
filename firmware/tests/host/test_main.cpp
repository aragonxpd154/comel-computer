/*
 * COMEL — teste do firmware no PC: liga o C64 com as Open ROMs, digita pelo
 * caminho do teclado USB (relatórios HID ABNT2), lista e carrega um programa do
 * "microSD" (imagem FAT), toca uma nota no SID e grava um SAVE. GPL-3.0.
 */
#include <stdio.h>
#include <string.h>
#include <math.h>
extern "C" {
#include "vga.h"
#include "keyboard.h"
#include "ff.h"
#include "comel_board.h"
void host_save_ppm(const char *path);
}
#include "comel_c64.h"
#include "Teensy64.h"
#include "reSID.h"
extern AudioPlaySID playSID;

uint32_t host_gpio_low_mask;
static void frames(int n) { for (int i = 0; i < n * 312; i++) c64_step(); }

/* caractere → (modificador, uso HID) no layout ABNT2 */
static void hid_for(char c, uint8_t *mod, uint8_t *u) {
    *mod = 0;
    if (c >= 'A' && c <= 'Z') { *u = 0x04 + (c - 'A'); return; }     /* sem shift = letra normal do C64 */
    if (c >= '1' && c <= '9') { *u = 0x1E + (c - '1'); return; }
    switch (c) {
    case '0': *u = 0x27; return;
    case '\n': *u = 0x28; return;
    case ' ': *u = 0x2C; return;
    case ',': *u = 0x36; return;
    case '.': *u = 0x37; return;
    case ':': *mod = 0x02; *u = 0x38; return;
    case '"': *mod = 0x02; *u = 0x35; return;
    case '$': *mod = 0x02; *u = 0x21; return;
    case '*': *mod = 0x02; *u = 0x25; return;
    case '(': *mod = 0x02; *u = 0x26; return;
    case ')': *mod = 0x02; *u = 0x27; return;
    default: *u = 0; return;
    }
}

static void hid_type(const char *s) {
    for (; *s; s++) {
        uint8_t r[8] = {0}, mod, u;
        hid_for(*s, &mod, &u);
        r[0] = mod; r[2] = u;
        kbd_report(0, r);
        frames(3);
        memset(r, 0, 8);
        kbd_report(0, r);
        frames(3);
    }
}

int main(void) {
    static FATFS fs;
    bool sd = f_mount(&fs, "", 1) == FR_OK;
    printf("microSD montado: %s\n", sd ? "sim" : "não");
    printf("ROMs: %s\n", roms_load(sd));
    c64_init(sd);

    frames(150);  host_save_ppm("out/1-boot.ppm");

    hid_type("LOAD\"$\",8\n");  frames(30);
    hid_type("LIST\n");         frames(60);
    host_save_ppm("out/2-diretorio.ppm");

    hid_type("LOAD\"HELLO\",8\n"); frames(30);
    hid_type("RUN\n");             frames(60);
    host_save_ppm("out/3-run.ppm");

    /* SID: toca uma nota (registradores escritos direto no reSID) e mede o sinal */
    const uint8_t regs[][2] = {{24, 15}, {5, 9}, {6, 240}, {1, 30}, {0, 0}, {4, 17}};
    for (auto &r : regs) playSID.setreg(r[0], r[1]);
    static int16_t s[AUDIO_BLOCK * 4];
    c64_audio_render(s, AUDIO_BLOCK * 4);
    double rms = 0; for (int i = 0; i < AUDIO_BLOCK * 4; i++) rms += (double)s[i] * s[i];
    rms = sqrt(rms / (AUDIO_BLOCK * 4));
    printf("SID: RMS com a nota tocando = %.0f (silêncio ≈ 0)\n", rms);
    playSID.setreg(4, 16);

    /* POKE pelo BASIC (borda preta) e SAVE no cartão, digitados pela fila automática */
    kbd_type("POKE53280,2\rSAVE\"TESTE\",8\r");
    frames(250);
    FILINFO fi;
    printf("SAVE: /c64/teste.prg %s\n", f_stat("/c64/teste.prg", &fi) == FR_OK ? "criado" : "NAO criado");

    /* joystick da placa: tiro apertado → bit 4 do $DC00 em zero */
    cpu.cia1.R[0x02] = 0xFF; cpu.cia1.R[0x00] = 0xFF;
    host_gpio_low_mask = 1u << PIN_JOY_FIRE;
    uint8_t a1 = cia1PORTA();
    host_gpio_low_mask = 0;
    uint8_t a0 = cia1PORTA();
    printf("Joystick: $DC00 solto=%02X, tiro apertado=%02X\n", a0, a1);
    host_save_ppm("out/4-poke-save.ppm");
    return 0;
}
