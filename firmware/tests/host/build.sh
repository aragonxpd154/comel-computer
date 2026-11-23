#!/bin/bash
# COMEL — compila o emulador para o PC (teste sem a placa). Precisa do build do firmware
# antes (gera build/generated/openroms.h).
set -e
cd "$(dirname "$0")"
F=../..
INC="-Istub -I$F -I$F/src -I$F/core -I$F/config -I$F/third_party/fatfs/source -I$F/build/generated"
DEF="-DHAS_SND=1 -DPAL=1 -DKBD_LAYOUT=KBD_LAYOUT_ABNT2"
mkdir -p obj out
for f in test_main.cpp $F/src/comel_c64.cpp $F/src/roms.cpp $F/core/cpu.cpp $F/core/cia1.cpp $F/core/cia2.cpp \
         $F/core/pla.cpp $F/core/vic.cpp $F/core/timerutil.cpp $F/core/reSID.cpp $F/core/sid.cpp; do
  g++ -O2 -std=gnu++17 -w $DEF $INC -c "$f" -o "obj/$(basename "$f").o"
done
for f in $F/src/keyboard.c host_vga.c host_diskio.c $F/third_party/fatfs/source/ff.c $F/third_party/fatfs/source/ffunicode.c; do
  gcc -O2 -std=gnu11 -w $DEF $INC -c "$f" -o "obj/$(basename "$f").o"
done
g++ obj/*.o -lm -o comel_host
