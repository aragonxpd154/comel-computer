/*
 * COMEL — host USB nas duas portas USB-A da placa, pelo PIO (Pico-PIO-USB +
 * TinyUSB). Roda inteiro no núcleo 1. GPL-3.0.
 *
 *   USB 1 (porta de baixo do J2) = GP4 D+ / GP5 D−  → raiz 1 do TinyUSB
 *   USB 2 (porta de cima do J2)  = GP2 D+ / GP3 D−  → raiz 2 do TinyUSB
 *
 * Teclados entram em modo "boot" (relatório fixo de 8 bytes) e vão para
 * keyboard.c. Um hub USB numa das portas também funciona.
 */
#include "pico/stdlib.h"
#include "pio_usb.h"
#include "tusb.h"

#include "keyboard.h"
#include "comel_board.h"

#define MAX_HID 8
static struct { uint8_t dev_addr, instance; bool used; } slots[MAX_HID];

static int slot_of(uint8_t dev_addr, uint8_t instance, bool create) {
    int free_slot = -1;
    for (int i = 0; i < MAX_HID; i++) {
        if (slots[i].used && slots[i].dev_addr == dev_addr && slots[i].instance == instance) return i;
        if (!slots[i].used && free_slot < 0) free_slot = i;
    }
    if (!create || free_slot < 0) return -1;
    slots[free_slot].dev_addr = dev_addr;
    slots[free_slot].instance = instance;
    slots[free_slot].used = true;
    return free_slot;
}

void usb_host_init(void) {
    pio_usb_configuration_t cfg = PIO_USB_DEFAULT_CONFIG;
    cfg.pin_dp = PIN_USB1_DP;                 /* PIO0: TX na SM0, RX/EOP nas SM1/SM2, DMA 0 */
    cfg.pinout = PIO_USB_PINOUT_DPDM;
    tuh_configure(BOARD_TUH_RHPORT, TUH_CFGID_RPI_PIO_USB_CONFIGURATION, &cfg);
    tuh_init(BOARD_TUH_RHPORT);
    pio_usb_host_add_port(PIN_USB2_DP, PIO_USB_PINOUT_DPDM);
}

void usb_host_task(void) {
    tuh_task();
}

/* ------------------------------------------------------------------ TinyUSB */

void tuh_hid_mount_cb(uint8_t dev_addr, uint8_t instance, uint8_t const *desc_report, uint16_t desc_len) {
    (void)desc_report; (void)desc_len;
    if (tuh_hid_interface_protocol(dev_addr, instance) == HID_ITF_PROTOCOL_KEYBOARD) {
        slot_of(dev_addr, instance, true);
        tuh_hid_receive_report(dev_addr, instance);
    }
}

void tuh_hid_umount_cb(uint8_t dev_addr, uint8_t instance) {
    int s = slot_of(dev_addr, instance, false);
    if (s >= 0) {
        kbd_release((uint8_t)s);
        slots[s].used = false;
    }
}

void tuh_hid_report_received_cb(uint8_t dev_addr, uint8_t instance, uint8_t const *report, uint16_t len) {
    int s = slot_of(dev_addr, instance, false);
    if (s >= 0 && len >= 8) kbd_report((uint8_t)s, report);
    tuh_hid_receive_report(dev_addr, instance);
}
