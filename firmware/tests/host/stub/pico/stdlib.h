/* COMEL — stubs do pico-sdk para rodar o emulador no PC (teste). GPL-3.0. */
#pragma once
#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>
#include <time.h>
#ifdef __cplusplus
extern "C" {
#endif
typedef unsigned int uint;
typedef uint64_t absolute_time_t;
static inline uint64_t time_us_64(void) { struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t); return (uint64_t)t.tv_sec * 1000000u + (uint64_t)t.tv_nsec / 1000u; }
static inline uint32_t time_us_32(void) { return (uint32_t)time_us_64(); }
static inline absolute_time_t get_absolute_time(void) { return time_us_64(); }
static inline uint32_t to_ms_since_boot(absolute_time_t t) { return (uint32_t)(t / 1000); }
static inline absolute_time_t from_us_since_boot(uint64_t us) { return us; }
static inline void sleep_until(absolute_time_t t) { (void)t; }
static inline void sleep_ms(uint32_t ms) { (void)ms; }
static inline absolute_time_t make_timeout_time_ms(uint32_t ms) { return time_us_64() + ms * 1000ull; }
static inline bool time_reached(absolute_time_t t) { return time_us_64() >= t; }
#define __not_in_flash_func(f) f
#define GPIO_IN 0
#define GPIO_OUT 1
static inline void gpio_init(uint p) { (void)p; }
static inline void gpio_set_dir(uint p, int d) { (void)p; (void)d; }
static inline void gpio_pull_up(uint p) { (void)p; }
extern uint32_t host_gpio_low_mask;
static inline bool gpio_get(uint p) { return !(host_gpio_low_mask & (1u << p)); }
#ifdef __cplusplus
}
#endif
