/* COMEL — áudio PWM no GP20. GPL-3.0. */
#pragma once
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef void (*audio_render_fn)(int16_t *out, int n);

void audio_init(audio_render_fn cb);   /* chamar no núcleo 1 */
void audio_task(void);                 /* chamar no laço do núcleo 1 */

#ifdef __cplusplus
}
#endif
