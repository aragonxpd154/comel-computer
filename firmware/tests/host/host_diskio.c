/* COMEL — unidade do FatFs lendo uma imagem de cartão (teste no PC). GPL-3.0. */
#include <stdio.h>
#include "ff.h"
#include "diskio.h"
static FILE *img;
const char *host_sd_image = "sd.img";
DSTATUS disk_status(BYTE d) { return (d || !img) ? STA_NOINIT : 0; }
DSTATUS disk_initialize(BYTE d) { if (d) return STA_NOINIT; if (!img) img = fopen(host_sd_image, "r+b"); return img ? 0 : STA_NOINIT; }
DRESULT disk_read(BYTE d, BYTE *b, LBA_t s, UINT n) { (void)d; fseek(img, (long)s * 512, SEEK_SET); return fread(b, 512, n, img) == n ? RES_OK : RES_ERROR; }
DRESULT disk_write(BYTE d, const BYTE *b, LBA_t s, UINT n) { (void)d; fseek(img, (long)s * 512, SEEK_SET); return fwrite(b, 512, n, img) == n ? RES_OK : RES_ERROR; }
DRESULT disk_ioctl(BYTE d, BYTE c, void *b) { (void)d; if (c == CTRL_SYNC) { fflush(img); return RES_OK; } if (c == GET_BLOCK_SIZE) { *(DWORD *)b = 1; return RES_OK; } return RES_PARERR; }
DWORD get_fattime(void) { return ((DWORD)(2026 - 1980) << 25) | (1u << 21) | (1u << 16); }
