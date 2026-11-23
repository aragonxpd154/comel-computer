/*
 * COMEL — TinyUSB só como host, nas duas portas USB-A da placa (Pico-PIO-USB).
 * Raiz 1 = USB 1 (GP4/GP5), raiz 2 = USB 2 (GP2/GP3). O USB nativo do Pico fica
 * de fora do TinyUSB (só bootloader para gravar o firmware). GPL-3.0.
 */
#ifndef TUSB_CONFIG_H
#define TUSB_CONFIG_H

#ifndef CFG_TUSB_MCU
#error CFG_TUSB_MCU deve vir do pico-sdk
#endif

#define CFG_TUSB_OS                 OPT_OS_PICO
#define CFG_TUSB_DEBUG              0
#define CFG_TUSB_MEM_SECTION
#define CFG_TUSB_MEM_ALIGN          __attribute__((aligned(4)))

#define CFG_TUH_ENABLED             1
#define CFG_TUH_RPI_PIO_USB         1
#define BOARD_TUH_RHPORT            1
#define CFG_TUH_MAX_SPEED           OPT_MODE_FULL_SPEED

#define CFG_TUH_ENUMERATION_BUFSIZE 256
#define CFG_TUH_HUB                 1    /* um hub em qualquer porta também funciona */
#define CFG_TUH_DEVICE_MAX          6
#define CFG_TUH_HID                 8    /* teclados com várias interfaces + joystick/mouse */
#define CFG_TUH_HID_EPIN_BUFSIZE    64
#define CFG_TUH_HID_EPOUT_BUFSIZE   64
#define CFG_TUH_CDC                 0
#define CFG_TUH_MSC                 0
#define CFG_TUH_VENDOR              0

#endif
