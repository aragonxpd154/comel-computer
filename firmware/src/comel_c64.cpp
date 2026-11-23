/*
 * COMEL — ligação do núcleo do C64 (Teensy64, de Frank Bösing, adaptado no
 * MCUME por Jean-Marc Harvengt) com a placa: vídeo, teclado, joystick, som e
 * LOAD/SAVE no microSD. GPL-3.0.
 */
#include <stdarg.h>
#include <string.h>
#include <ctype.h>
#include <initializer_list>
#include "pico/stdlib.h"
#include "hardware/gpio.h"

extern "C" {
#include "emuapi.h"
#include "vga.h"
#include "keyboard.h"
#include "comel_board.h"
#include "ff.h"
}
#include "Teensy64.h"
#include "reSID.h"
#include "comel_c64.h"

AudioPlaySID playSID;
extern "C" volatile uint32_t systick_millis_count;
volatile uint32_t systick_millis_count;

static bool sd_ok;
static bool joy_port1;                 /* falso = joystick da placa na porta 2 (padrão dos jogos) */
static uint64_t next_frame_us;

#define FRAME_US 19950                 /* PAL: 312 linhas × 63 ciclos / 985 248 Hz */

/* ------------------------------------------------------------------ vídeo */

extern "C" void emu_printf(const char *fmt, ...) { (void)fmt; }

extern "C" void __not_in_flash_func(emu_DrawLine16)(unsigned short *buf, int width, int height, int line) {
    (void)height;
    vga_put_line565(line, buf, width);
}

/* Fim de quadro: ações do teclado, digitação automática e ritmo de 50 Hz. */
extern "C" void emu_DrawVsync(void) {
    uint8_t a = kbd_take_actions();
    if (a & KBD_ACT_RESET) c64_reset();
    if (a & KBD_ACT_RESTORE) cpu_nmi();
    if (a & KBD_ACT_SWAPJOY) joy_port1 = !joy_port1;
    if (a & KBD_ACT_LOADDIR) kbd_type("LOAD\"$\",8\rLIST\r");
    if (a & KBD_ACT_LOADRUN) kbd_type("LOAD\"*\",8,1\rRUN\r");
    kbd_type_tick();

    uint64_t now = time_us_64();
    if (now < next_frame_us) {
        sleep_until(from_us_since_boot(next_frame_us));
        next_frame_us += FRAME_US;
    } else {
        next_frame_us = now + FRAME_US;       /* atrasou: não tenta recuperar, só segue */
    }
}

/* ------------------------------------------------------------------ joystick e teclado */

static uint8_t joystick_bits(void) {
    uint8_t j = kbd_joystick;
    if (!gpio_get(PIN_JOY_UP))    j |= JOY_MASK_UP;
    if (!gpio_get(PIN_JOY_DOWN))  j |= JOY_MASK_DOWN;
    if (!gpio_get(PIN_JOY_LEFT))  j |= JOY_MASK_LEFT;
    if (!gpio_get(PIN_JOY_RIGHT)) j |= JOY_MASK_RIGHT;
    if (!gpio_get(PIN_JOY_FIRE))  j |= JOY_MASK_FIRE;
    return j;   /* bits 0–4 = cima, baixo, esquerda, direita, tiro — igual ao CIA */
}

static inline uint8_t matrix_col(int c) { return kbd_matrix[c] | kbd_inject[c]; }

/* $DC00: colunas do teclado (saída) e joystick 2 */
uint8_t cia1PORTA(void) {
    uint8_t v = ~cpu.cia1.R[0x02] | (cpu.cia1.R[0x00] & cpu.cia1.R[0x02]);
    if (!joy_port1) v &= ~joystick_bits();
    uint8_t rows = ~cpu.cia1.R[0x01] & cpu.cia1.R[0x03];      /* linhas puxadas para 0 pelo PB */
    if (rows)
        for (int c = 0; c < 8; c++)
            if (matrix_col(c) & rows) v &= ~(1u << c);
    return v;
}

/* $DC01: linhas do teclado (entrada) e joystick 1 */
uint8_t cia1PORTB(void) {
    uint8_t v = ~cpu.cia1.R[0x03] | (cpu.cia1.R[0x01] & cpu.cia1.R[0x03]);
    if (joy_port1) v &= ~joystick_bits();
    uint8_t cols = ~cpu.cia1.R[0x00] & cpu.cia1.R[0x02];      /* colunas puxadas para 0 pelo PA */
    for (int c = 0; c < 8; c++)
        if (cols & (1u << c)) v &= ~matrix_col(c);
    return v;
}

/* ------------------------------------------------------------------ som */

void c64_audio_render(int16_t *out, int n) {
    playSID.update(AUDIO_RATE, out, n);
}

/* ------------------------------------------------------------------ máquina */

void c64_reset(void) {
    disableEventResponder();
    resetPLA();
    resetCia1();
    resetCia2();
    resetVic();
    playSID.reset();
    cpu_reset();
}

void c64_init(bool sd_mounted) {
    sd_ok = sd_mounted;
    for (uint p : {PIN_JOY_UP, PIN_JOY_DOWN, PIN_JOY_LEFT, PIN_JOY_RIGHT, PIN_JOY_FIRE}) {
        gpio_init(p);
        gpio_set_dir(p, GPIO_IN);
        gpio_pull_up(p);
    }
    playSID.begin(AUDIO_RATE, AUDIO_BLOCK);
    c64_reset();
    next_frame_us = time_us_64() + FRAME_US;
}

/* Uma linha de varredura (63 ciclos do 6510 + VIC-II) */
void __not_in_flash_func(c64_step)(void) {
    static unsigned lc = 1;
    for (;;) {
        cpu.lineStartTime = fbmicros();
        cpu.lineCycles = cpu.lineCyclesAbs = 0;
        if (!cpu.exactTiming) vic_do(); else vic_do_simple();
        if (--lc == 0) {                               /* relógio de hora dos CIAs a 10 Hz */
            lc = LINEFREQ / 10;
            cia1_checkRTCAlarm();
            cia2_checkRTCAlarm();
        }
        if (!cpu.exactTiming) break;
        if ((fbmicros() - cpu.exactTimingStartTime) * 1000 >= EXACTTIMINGDURATION) {
            cpu_disableExactTiming();
            break;
        }
    }
}

/* ------------------------------------------------------------------ LOAD / SAVE no microSD
 *
 * O KERNAL tem, em $FFD5 (LOAD) e $FFD8 (SAVE), um JMP para a rotina real.
 * roms.cpp troca esses JMP pelos códigos $D2 e $F2, que o núcleo trata como
 * "armadilhas" e chamam as funções abaixo. Os dispositivos 1 e 8 vão para a
 * pasta /c64 do microSD; os outros seguem pelo KERNAL normal.
 * Funciona com o KERNAL original e com o das Open ROMs.
 */

#define C64_DIR "/c64"

static void kernal_return(bool error, uint8_t code) {
    uint16_t lo = cpu.RAM[BASE_STACK + ((cpu.sp + 1) & 0xFF)];
    uint16_t hi = cpu.RAM[BASE_STACK + ((cpu.sp + 2) & 0xFF)];
    cpu.sp += 2;
    cpu.pc = (uint16_t)(((hi << 8) | lo) + 1);       /* RTS */
    if (error) { cpu.cpustatus |= 0x01; cpu.a = code; }
    else cpu.cpustatus &= ~0x01;
    cpu.ticks = 6;
}

static void jump_to_original(void) {
    /* cpu.pc aponta para o operando do JMP original (logo depois do código da armadilha) */
    cpu.pc = rom_kernal[(cpu.pc + 1) - 0xE000] * 256 + rom_kernal[cpu.pc - 0xE000];
    cpu.ticks = 3;
}

static void c64_filename(char *out, int max) {
    int len = cpu.RAM[0xB7];
    uint16_t p = cpu.RAM[0xBB] | (cpu.RAM[0xBC] << 8);
    int n = 0;
    for (int i = 0; i < len && n < max - 1; i++) {
        uint8_t ch = cpu.RAM[(uint16_t)(p + i)];
        if (ch >= 0xC1 && ch <= 0xDA) ch -= 0x80;       /* letras com shift → ASCII */
        out[n++] = (char)ch;
    }
    out[n] = 0;
    if (n > 2 && out[1] == ':' && isdigit((unsigned char)out[0])) memmove(out, out + 2, strlen(out + 2) + 1);
}

/* Compara um nome do C64 (com * e ?) com o nome do arquivo no cartão, sem ligar para maiúsculas e .prg */
static bool name_matches(const char *pat, const char *file) {
    char f[64];
    strncpy(f, file, sizeof f - 1);
    f[sizeof f - 1] = 0;
    char *dot = strrchr(f, '.');
    if (dot && !strcasecmp(dot, ".prg")) *dot = 0;
    const char *a = pat, *b = f;
    while (*a) {
        if (*a == '*') return true;
        if (!*b) return false;
        if (*a != '?' && toupper((unsigned char)*a) != toupper((unsigned char)*b)) return false;
        a++; b++;
    }
    return *b == 0;
}

static bool find_file(const char *pat, char *path, int max) {
    static DIR d;
    static FILINFO fi;
    if (f_opendir(&d, C64_DIR) != FR_OK) return false;
    bool found = false;
    while (f_readdir(&d, &fi) == FR_OK && fi.fname[0]) {
        if (fi.fattrib & (AM_DIR | AM_HID | AM_SYS)) continue;
        if (name_matches(pat, fi.fname)) {
            snprintf(path, max, C64_DIR "/%s", fi.fname);
            found = true;
            break;
        }
    }
    f_closedir(&d);
    return found;
}

/* LOAD"$" — monta a listagem da pasta como um programa BASIC */
static uint16_t build_directory(uint16_t addr) {
    uint16_t start = addr;
    auto line = [&](uint16_t number, const char *text) {
        uint16_t here = addr;
        int len = (int)strlen(text);
        uint16_t next = (uint16_t)(here + 4 + len + 1);
        cpu.RAM[addr++] = next & 0xFF;
        cpu.RAM[addr++] = next >> 8;
        cpu.RAM[addr++] = number & 0xFF;
        cpu.RAM[addr++] = number >> 8;
        memcpy(&cpu.RAM[addr], text, (size_t)len);
        addr += len;
        cpu.RAM[addr++] = 0;
    };
    line(0, "\x12\"COMEL MICROSD   \" 64 2A");
    static DIR d;
    static FILINFO fi;
    if (f_opendir(&d, C64_DIR) == FR_OK) {
        while (f_readdir(&d, &fi) == FR_OK && fi.fname[0] && addr < 0x9000) {
            if (fi.fattrib & (AM_DIR | AM_HID | AM_SYS)) continue;
            char name[20], text[40];
            strncpy(name, fi.fname, sizeof name - 1);
            name[sizeof name - 1] = 0;
            char *dot = strrchr(name, '.');
            const char *type = "PRG";
            if (dot) { if (strcasecmp(dot, ".prg")) type = "SEQ"; *dot = 0; }
            name[16] = 0;
            for (char *c = name; *c; c++) *c = (char)toupper((unsigned char)*c);
            unsigned blocks = (unsigned)((fi.fsize + 253) / 254);
            const char *pad = blocks < 10 ? "   " : blocks < 100 ? "  " : " ";
            char quoted[20];
            snprintf(quoted, sizeof quoted, "\"%s\"", name);
            snprintf(text, sizeof text, "%s%-18s %s", pad, quoted, type);
            line((uint16_t)blocks, text);
        }
        f_closedir(&d);
    }
    line(664, "BLOCKS FREE.");
    cpu.RAM[addr++] = 0;
    cpu.RAM[addr++] = 0;
    (void)start;
    return addr;
}

void patchLOAD(void) {
    uint8_t device = cpu.RAM[0xBA];
    if (device != 1 && device != 8) { jump_to_original(); return; }
    if (!sd_ok) { kernal_return(true, 5); return; }          /* DEVICE NOT PRESENT */

    char name[48], path[80];
    c64_filename(name, sizeof name);
    bool use_xy = cpu.RAM[0xB9] == 0;                       /* endereço secundário 0 = carrega em X/Y */
    uint16_t addr = use_xy ? (uint16_t)(cpu.x | (cpu.y << 8)) : 0x0801;
    uint16_t end;

    if (!strcmp(name, "$")) {
        if (!use_xy) addr = 0x0801;
        end = build_directory(addr);
    } else {
        if (!name[0] || !find_file(name, path, sizeof path)) { kernal_return(true, 4); return; }   /* FILE NOT FOUND */
        static FIL f;
        if (f_open(&f, path, FA_READ) != FR_OK) { kernal_return(true, 4); return; }
        uint8_t hdr[2];
        UINT got = 0;
        f_read(&f, hdr, 2, &got);
        if (got != 2) { f_close(&f); kernal_return(true, 4); return; }
        if (!use_xy) addr = (uint16_t)(hdr[0] | (hdr[1] << 8));
        UINT room = 0x10000u - addr;
        f_read(&f, &cpu.RAM[addr], room, &got);
        f_close(&f);
        end = (uint16_t)(addr + got);
    }
    cpu.RAM[0xAE] = end & 0xFF;
    cpu.RAM[0xAF] = end >> 8;
    cpu.x = end & 0xFF;
    cpu.y = end >> 8;
    kernal_return(false, 0);
}

void patchSAVE(void) {
    uint8_t device = cpu.RAM[0xBA];
    if (device != 1 && device != 8) { jump_to_original(); return; }
    if (!sd_ok) { kernal_return(true, 5); return; }

    char name[48], path[80];
    c64_filename(name, sizeof name);
    if (!name[0]) { kernal_return(true, 8); return; }        /* MISSING FILE NAME */
    if (name[0] == '@') memmove(name, name + 1, strlen(name));   /* SAVE"@NOME" — sempre substitui */
    f_mkdir(C64_DIR);
    snprintf(path, sizeof path, C64_DIR "/%s.prg", name);
    for (char *c = path + sizeof(C64_DIR); *c; c++) *c = (char)tolower((unsigned char)*c);

    uint8_t zp = cpu.a;
    uint16_t start = cpu.RAM[zp] | (cpu.RAM[(uint8_t)(zp + 1)] << 8);
    uint16_t end = (uint16_t)(cpu.x | (cpu.y << 8));
    static FIL f;
    if (f_open(&f, path, FA_WRITE | FA_CREATE_ALWAYS) != FR_OK) {
        kernal_return(true, 5);
        return;
    }
    uint8_t hdr[2] = {(uint8_t)(start & 0xFF), (uint8_t)(start >> 8)};
    UINT w;
    f_write(&f, hdr, 2, &w);
    if (end > start) f_write(&f, &cpu.RAM[start], (UINT)(end - start), &w);
    f_close(&f);
    kernal_return(false, 0);
}
