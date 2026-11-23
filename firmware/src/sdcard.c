/*
 * COMEL — microSD em SPI0 (GP16 MISO, GP17 CS, GP18 SCK, GP19 MOSI) como
 * unidade 0 do FatFs. Driver SPI simples, sem DMA. GPL-3.0.
 */
#include <string.h>
#include "pico/stdlib.h"
#include "hardware/spi.h"
#include "hardware/gpio.h"

#include "ff.h"
#include "diskio.h"
#include "comel_board.h"

#define CMD0   0
#define CMD8   8
#define CMD9   9
#define CMD12  12
#define CMD16  16
#define CMD17  17
#define CMD18  18
#define CMD24  24
#define CMD25  25
#define CMD55  55
#define CMD58  58
#define ACMD41 (0x80 | 41)

static volatile DSTATUS stat = STA_NOINIT;
static bool block_addr;                      /* SDHC/SDXC endereçam por bloco */

static inline void cs_low(void)  { gpio_put(PIN_SD_CS, 0); }
static inline void cs_high(void) { gpio_put(PIN_SD_CS, 1); }

static uint8_t xchg(uint8_t b) {
    uint8_t r;
    spi_write_read_blocking(SD_SPI, &b, &r, 1);
    return r;
}

static bool wait_ready(uint32_t ms) {
    absolute_time_t t = make_timeout_time_ms(ms);
    do {
        if (xchg(0xFF) == 0xFF) return true;
    } while (!time_reached(t));
    return false;
}

static void deselect(void) { cs_high(); xchg(0xFF); }

static bool select(void) {
    cs_low();
    xchg(0xFF);
    if (wait_ready(500)) return true;
    deselect();
    return false;
}

static uint8_t send_cmd(uint8_t cmd, uint32_t arg) {
    if (cmd & 0x80) {                         /* ACMD = CMD55 + CMD */
        cmd &= 0x7F;
        uint8_t r = send_cmd(CMD55, 0);
        if (r > 1) return r;
    }
    if (cmd != CMD12) {
        deselect();
        if (!select()) return 0xFF;
    }
    uint8_t buf[6] = {(uint8_t)(0x40 | cmd), (uint8_t)(arg >> 24), (uint8_t)(arg >> 16),
                      (uint8_t)(arg >> 8), (uint8_t)arg, 0x01};
    if (cmd == CMD0) buf[5] = 0x95;
    if (cmd == CMD8) buf[5] = 0x87;
    spi_write_blocking(SD_SPI, buf, 6);
    if (cmd == CMD12) xchg(0xFF);
    uint8_t r, n = 10;
    do r = xchg(0xFF); while ((r & 0x80) && --n);
    return r;
}

static bool rcvr_block(uint8_t *buf, uint n) {
    absolute_time_t t = make_timeout_time_ms(200);
    uint8_t token;
    do token = xchg(0xFF); while (token == 0xFF && !time_reached(t));
    if (token != 0xFE) return false;
    memset(buf, 0xFF, n);
    spi_write_read_blocking(SD_SPI, buf, buf, n);
    xchg(0xFF); xchg(0xFF);                   /* CRC */
    return true;
}

static bool xmit_block(const uint8_t *buf, uint8_t token) {
    if (!wait_ready(500)) return false;
    xchg(token);
    if (token != 0xFD) {
        spi_write_blocking(SD_SPI, buf, 512);
        xchg(0xFF); xchg(0xFF);
        if ((xchg(0xFF) & 0x1F) != 0x05) return false;
    }
    return true;
}

DSTATUS disk_status(BYTE drv) { return drv ? STA_NOINIT : stat; }

DSTATUS disk_initialize(BYTE drv) {
    if (drv) return STA_NOINIT;
    spi_init(SD_SPI, 400 * 1000);
    gpio_set_function(PIN_SD_MISO, GPIO_FUNC_SPI);
    gpio_set_function(PIN_SD_SCK, GPIO_FUNC_SPI);
    gpio_set_function(PIN_SD_MOSI, GPIO_FUNC_SPI);
    gpio_pull_up(PIN_SD_MISO);
    gpio_init(PIN_SD_CS);
    gpio_set_dir(PIN_SD_CS, GPIO_OUT);
    cs_high();
    for (int i = 0; i < 10; i++) xchg(0xFF);  /* 80 pulsos de relógio */

    uint8_t ok = 0, ocr[4];
    if (send_cmd(CMD0, 0) == 1) {
        absolute_time_t t = make_timeout_time_ms(1000);
        if (send_cmd(CMD8, 0x1AA) == 1) {     /* SD v2 */
            for (int i = 0; i < 4; i++) ocr[i] = xchg(0xFF);
            if (ocr[2] == 0x01 && ocr[3] == 0xAA) {
                while (!time_reached(t) && send_cmd(ACMD41, 1UL << 30)) ;
                if (!time_reached(t) && send_cmd(CMD58, 0) == 0) {
                    for (int i = 0; i < 4; i++) ocr[i] = xchg(0xFF);
                    block_addr = (ocr[0] & 0x40) != 0;
                    ok = 1;
                }
            }
        } else {                               /* SD v1 */
            while (!time_reached(t) && send_cmd(ACMD41, 0)) ;
            if (!time_reached(t) && send_cmd(CMD16, 512) == 0) { block_addr = false; ok = 1; }
        }
    }
    deselect();
    if (ok) {
        spi_set_baudrate(SD_SPI, 25 * 1000 * 1000);
        stat &= (DSTATUS)~STA_NOINIT;
    }
    return stat;
}

DRESULT disk_read(BYTE drv, BYTE *buf, LBA_t sector, UINT count) {
    if (drv || !count) return RES_PARERR;
    if (stat & STA_NOINIT) return RES_NOTRDY;
    uint32_t a = block_addr ? (uint32_t)sector : (uint32_t)sector * 512;
    if (count == 1) {
        if (send_cmd(CMD17, a) == 0 && rcvr_block(buf, 512)) count = 0;
    } else if (send_cmd(CMD18, a) == 0) {
        do {
            if (!rcvr_block(buf, 512)) break;
            buf += 512;
        } while (--count);
        send_cmd(CMD12, 0);
    }
    deselect();
    return count ? RES_ERROR : RES_OK;
}

DRESULT disk_write(BYTE drv, const BYTE *buf, LBA_t sector, UINT count) {
    if (drv || !count) return RES_PARERR;
    if (stat & STA_NOINIT) return RES_NOTRDY;
    uint32_t a = block_addr ? (uint32_t)sector : (uint32_t)sector * 512;
    if (count == 1) {
        if (send_cmd(CMD24, a) == 0 && xmit_block(buf, 0xFE)) count = 0;
    } else if (send_cmd(CMD25, a) == 0) {
        do {
            if (!xmit_block(buf, 0xFC)) break;
            buf += 512;
        } while (--count);
        if (!xmit_block(NULL, 0xFD)) count = 1;
    }
    deselect();
    return count ? RES_ERROR : RES_OK;
}

DRESULT disk_ioctl(BYTE drv, BYTE cmd, void *buf) {
    if (drv) return RES_PARERR;
    if (stat & STA_NOINIT) return RES_NOTRDY;
    switch (cmd) {
    case CTRL_SYNC:
        if (select()) { deselect(); return RES_OK; }
        return RES_ERROR;
    case GET_BLOCK_SIZE:
        *(DWORD *)buf = 1;
        return RES_OK;
    default:
        return RES_PARERR;
    }
}

DWORD get_fattime(void) {
    /* sem relógio de tempo real: 1º de janeiro de 2026, 00:00 */
    return ((DWORD)(2026 - 1980) << 25) | ((DWORD)1 << 21) | ((DWORD)1 << 16);
}
