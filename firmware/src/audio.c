/*
 * COMEL — áudio em PWM no GP20 (filtro RC de 2 polos na placa). GPL-3.0.
 *
 * PWM de 10 bits a 246 kHz. Um temporizador de DMA a 32 kHz copia uma amostra
 * por vez para o registrador de comparação. Dois blocos de 512 amostras se
 * alternam (pingue-pongue): quando um termina, a interrupção só marca que ele
 * precisa ser preenchido de novo; o preenchimento (reSID) é feito no laço do
 * núcleo 1, fora da interrupção, para não atrapalhar o USB.
 */
#include "pico/stdlib.h"
#include "hardware/pwm.h"
#include "hardware/dma.h"
#include "hardware/irq.h"
#include "hardware/clocks.h"

#include "audio.h"
#include "comel_board.h"

#define PWM_BITS 10
#define PWM_TOP  ((1u << PWM_BITS) - 1)

static uint16_t buf[2][AUDIO_BLOCK] __attribute__((aligned(4)));
static volatile uint8_t pending;            /* bit 0 = bloco A vazio, bit 1 = bloco B vazio */
static audio_render_fn render_cb;
static int16_t scratch[AUDIO_BLOCK];

static void __isr __not_in_flash_func(audio_dma_isr)(void) {
    if (dma_channel_get_irq1_status(AUDIO_DMA_A)) {
        dma_channel_acknowledge_irq1(AUDIO_DMA_A);
        dma_channel_set_read_addr(AUDIO_DMA_A, buf[0], false);
        pending |= 1;
    }
    if (dma_channel_get_irq1_status(AUDIO_DMA_B)) {
        dma_channel_acknowledge_irq1(AUDIO_DMA_B);
        dma_channel_set_read_addr(AUDIO_DMA_B, buf[1], false);
        pending |= 2;
    }
}

static void fill(int i) {
    if (render_cb) {
        render_cb(scratch, AUDIO_BLOCK);
        for (int k = 0; k < AUDIO_BLOCK; k++)
            buf[i][k] = (uint16_t)(((int32_t)scratch[k] + 32768) >> (16 - PWM_BITS));
    } else {
        for (int k = 0; k < AUDIO_BLOCK; k++) buf[i][k] = PWM_TOP / 2;
    }
}

void audio_task(void) {
    uint8_t p = pending;
    if (!p) return;
    if (p & 1) { fill(0); pending &= (uint8_t)~1; }
    if (p & 2) { fill(1); pending &= (uint8_t)~2; }
}

static void cfg_channel(uint ch, uint other, uint16_t *src, volatile void *dst) {
    dma_channel_config c = dma_channel_get_default_config(ch);
    channel_config_set_transfer_data_size(&c, DMA_SIZE_16);   /* replicado nas duas metades do CC */
    channel_config_set_read_increment(&c, true);
    channel_config_set_write_increment(&c, false);
    channel_config_set_dreq(&c, dma_get_timer_dreq(AUDIO_DMA_TIMER));
    channel_config_set_chain_to(&c, other);
    dma_channel_configure(ch, &c, dst, src, AUDIO_BLOCK, false);
    dma_channel_set_irq1_enabled(ch, true);
}

/* Chamar no núcleo que vai atender a interrupção (núcleo 1). */
void audio_init(audio_render_fn cb) {
    render_cb = cb;
    gpio_set_function(PIN_AUDIO_PWM, GPIO_FUNC_PWM);
    uint slice = pwm_gpio_to_slice_num(PIN_AUDIO_PWM);
    uint chan = pwm_gpio_to_channel(PIN_AUDIO_PWM);
    pwm_config pc = pwm_get_default_config();
    pwm_config_set_clkdiv(&pc, 1.0f);
    pwm_config_set_wrap(&pc, PWM_TOP);
    pwm_init(slice, &pc, true);
    pwm_set_chan_level(slice, chan, PWM_TOP / 2);

    for (int k = 0; k < AUDIO_BLOCK; k++) buf[0][k] = buf[1][k] = PWM_TOP / 2;

    /* 32 kHz exatos a partir de 252 MHz: 1/7875 */
    dma_timer_claim(AUDIO_DMA_TIMER);
    uint32_t sys = clock_get_hz(clk_sys);
    dma_timer_set_fraction(AUDIO_DMA_TIMER, 1, (uint16_t)(sys / AUDIO_RATE));

    dma_channel_claim(AUDIO_DMA_A);
    dma_channel_claim(AUDIO_DMA_B);
    volatile void *cc = &pwm_hw->slice[slice].cc;
    cfg_channel(AUDIO_DMA_A, AUDIO_DMA_B, buf[0], cc);
    cfg_channel(AUDIO_DMA_B, AUDIO_DMA_A, buf[1], cc);

    irq_set_exclusive_handler(DMA_IRQ_1, audio_dma_isr);
    irq_set_enabled(DMA_IRQ_1, true);
    dma_channel_start(AUDIO_DMA_A);
}
