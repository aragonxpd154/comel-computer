# Componentes de terceiros no firmware

| Componente | Onde | Autor | Licença |
|---|---|---|---|
| Núcleo do C64 (6510, VIC-II, CIAs, PLA) | `core/*.cpp`, `core/*.h` | Teensy64 — Frank Bösing; adaptação para o Pico no MCUME — Jean-Marc Harvengt | GPL-3.0 ou posterior |
| reSID (emulação do SID 6581) | `core/reSID/` | Dag Lem | GPL-2.0 ou posterior (ver `core/reSID/COPYING`) |
| `IntervalTimer.h` | `core/` | PJRC.COM (Teensyduino), com alterações de Frank Bösing | licença do Teensyduino (estilo MIT) |
| FatFs R0.15 | `third_party/fatfs/` | ChaN | licença própria do FatFs, estilo BSD (ver `third_party/fatfs/LICENSE.txt`) |
| Open ROMs (BASIC, KERNAL, caracteres) | `roms/openroms-*.bin` | Paul Gardner-Stephen, Roman Standzikowski (MEGA65) | LGPL-3.0 ou posterior (ver `roms/OPENROMS-COPYRIGHT.txt`) |
| pico-sdk, TinyUSB | baixados em `deps/` | Raspberry Pi; Ha Thach | BSD-3-Clause; MIT |
| Pico-PIO-USB | baixado em `deps/` | sekigon-gonnoc | MIT |

Alterações do COMEL nos arquivos de terceiros:

- `core/roms.h`: as ROMs ficam em RAM (carregadas no boot).
- `core/vic.cpp`: as linhas de borda de cima e de baixo também vão para a tela.
- `core/reSID/sid.cc`: saída de 16 bits com sinal (o MCUME usava 8 bits).

O código próprio do COMEL fica em `src/` e `tests/`. As ROMs originais da Commodore **não** fazem parte do projeto.
