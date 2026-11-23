#ifndef Teensy64_roms_h_
#define Teensy64_roms_h_

#define APPLY_PATCHES 1

/* COMEL: as ROMs ficam em RAM. No boot são copiadas das Open ROMs embutidas
 * (LGPL-3+) e, se existirem, substituídas pelas do microSD (/c64/basic.bin,
 * kernal.bin, chargen.bin) — ver src/roms.cpp. */
extern unsigned char rom_basic[8192];
extern unsigned char rom_kernal[8192];
extern unsigned char rom_characters[4096];

#endif