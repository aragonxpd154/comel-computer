/*
 * COMEL — ROMs do C64 em RAM. GPL-3.0.
 *
 * O firmware traz as Open ROMs do projeto MEGA65 (LGPL-3+, ver
 * roms/OPENROMS-COPYRIGHT.txt), então liga sem nada no cartão. Para usar as
 * ROMs originais da Commodore (melhor compatibilidade com jogos), copie para
 * o microSD:
 *     /c64/basic.bin    (8 KiB, 901226-01)
 *     /c64/kernal.bin   (8 KiB, 901227-03)
 *     /c64/chargen.bin  (4 KiB, 901225-01)
 * Cada uma é opcional: o que não estiver no cartão vem das Open ROMs.
 */
#include <string.h>
extern "C" {
#include "ff.h"
}
#include "roms.h"
#include "comel_c64.h"
#include "openroms.h"

unsigned char rom_basic[8192];
unsigned char rom_kernal[8192];
unsigned char rom_characters[4096];

static bool load_file(const char *path, unsigned char *dst, UINT size) {
    static FIL f;
    if (f_open(&f, path, FA_READ) != FR_OK) return false;
    bool ok = f_size(&f) == size;
    UINT got = 0;
    if (ok) ok = f_read(&f, dst, size, &got) == FR_OK && got == size;
    f_close(&f);
    return ok;
}

const char *roms_load(bool sd_mounted) {
    memcpy(rom_basic, openroms_basic, sizeof rom_basic);
    memcpy(rom_kernal, openroms_kernal, sizeof rom_kernal);
    memcpy(rom_characters, openroms_chargen, sizeof rom_characters);

    int from_sd = 0;
    if (sd_mounted) {
        static unsigned char tmp[8192];
        if (load_file("/c64/basic.bin", tmp, 8192)) { memcpy(rom_basic, tmp, 8192); from_sd++; }
        if (load_file("/c64/kernal.bin", tmp, 8192)) { memcpy(rom_kernal, tmp, 8192); from_sd++; }
        if (load_file("/c64/chargen.bin", tmp, 4096)) { memcpy(rom_characters, tmp, 4096); from_sd++; }
    }

    /* Armadilhas de LOAD ($FFD5) e SAVE ($FFD8) para o microSD — ver comel_c64.cpp */
    if (rom_kernal[0x1FD5] == 0x4C) rom_kernal[0x1FD5] = 0xD2;
    if (rom_kernal[0x1FD8] == 0x4C) rom_kernal[0x1FD8] = 0xF2;

    return from_sd == 3 ? "ROMs originais (microSD)" : from_sd ? "ROMs mistas" : "Open ROMs";
}
