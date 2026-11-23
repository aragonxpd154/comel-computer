/* COMEL — ligação do núcleo do C64 com a placa. GPL-3.0. */
#pragma once
#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

void c64_init(bool sd_mounted);
void c64_reset(void);
void c64_step(void);                          /* uma linha de varredura */
void c64_audio_render(int16_t *out, int n);   /* núcleo 1 */

/* ROMs: retorna uma descrição curta do conjunto carregado */
const char *roms_load(bool sd_mounted);

#ifdef __cplusplus
}
#endif
