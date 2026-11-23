# COMEL — firmware do Commodore 64 para a placa COMEL (Raspberry Pi Pico 2 / RP2350)
#
#   bash scripts/deps.sh            # baixa pico-sdk 2.2.0 e Pico-PIO-USB em deps/
#   cmake -B build -G Ninja && cmake --build build
#   → build/comel.uf2
cmake_minimum_required(VERSION 3.13)

set(PICO_PLATFORM rp2350-arm-s)
set(PICO_BOARD pico2)

if(NOT DEFINED PICO_SDK_PATH AND NOT DEFINED ENV{PICO_SDK_PATH})
    set(PICO_SDK_PATH ${CMAKE_CURRENT_LIST_DIR}/deps/pico-sdk)
endif()
if(NOT DEFINED PICO_PIO_USB_PATH)
    set(PICO_PIO_USB_PATH ${CMAKE_CURRENT_LIST_DIR}/deps/Pico-PIO-USB)
endif()

include(pico_sdk_import.cmake)
project(comel C CXX ASM)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)
pico_sdk_init()

# Open ROMs (LGPL-3+) embutidas como arrays C
set(OPENROMS_H ${CMAKE_CURRENT_BINARY_DIR}/generated/openroms.h)
file(MAKE_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/generated)
set(_roms "/* Gerado pelo CMake a partir de roms/openroms-*.bin (Open ROMs, MEGA65 — LGPL-3+) */\n#pragma once\n")
foreach(name basic kernal chargen)
    file(READ ${CMAKE_CURRENT_LIST_DIR}/roms/openroms-${name}.bin _hex HEX)
    string(REGEX REPLACE "([0-9a-f][0-9a-f])" "0x\\1," _arr "${_hex}")
    string(APPEND _roms "static const unsigned char openroms_${name}[] = {${_arr}};\n")
endforeach()
file(WRITE ${OPENROMS_H}.tmp "${_roms}")
configure_file(${OPENROMS_H}.tmp ${OPENROMS_H} COPYONLY)

add_executable(comel
    src/main.cpp
    src/comel_c64.cpp
    src/roms.cpp
    src/vga.c
    src/audio.c
    src/keyboard.c
    src/usb_host.c
    src/sdcard.c
    core/cpu.cpp
    core/cia1.cpp
    core/cia2.cpp
    core/pla.cpp
    core/vic.cpp
    core/timerutil.cpp
    core/reSID.cpp
    core/sid.cpp
    third_party/fatfs/source/ff.c
    third_party/fatfs/source/ffunicode.c
)

pico_generate_pio_header(comel ${CMAKE_CURRENT_LIST_DIR}/src/vga.pio)

target_include_directories(comel PRIVATE
    ${CMAKE_CURRENT_LIST_DIR}
    ${CMAKE_CURRENT_LIST_DIR}/src
    ${CMAKE_CURRENT_LIST_DIR}/config
    ${CMAKE_CURRENT_LIST_DIR}/core
    ${CMAKE_CURRENT_LIST_DIR}/third_party/fatfs/source
    ${CMAKE_CURRENT_BINARY_DIR}/generated
)

target_compile_definitions(comel PRIVATE
    HAS_SND=1
    PAL=1
    KBD_LAYOUT=KBD_LAYOUT_ABNT2          # ou KBD_LAYOUT_US
    PICO_CLOCK_ADJUST_PERI_CLOCK_WITH_SYS_CLOCK=1
    PICO_STACK_SIZE=0x1000                # 4 KiB para cada núcleo
    PICO_CORE1_STACK_SIZE=0x1000
)

target_compile_options(comel PRIVATE -O3 -Wno-unused-parameter -Wno-unused-variable -Wno-narrowing)

target_link_libraries(comel
    pico_stdlib
    pico_multicore
    hardware_pio
    hardware_dma
    hardware_pwm
    hardware_spi
    tinyusb_host
    tinyusb_board
    tinyusb_pico_pio_usb
)

# Roda tudo da RAM: o emulador não sofre com falhas do cache da flash
pico_set_binary_type(comel copy_to_ram)
pico_set_program_name(comel "COMEL")
pico_set_program_description(comel "Commodore 64 na placa COMEL (VGA, 2 x USB, SID)")
pico_set_program_url(comel "https://github.com/aragonxpd154/COMEL")
pico_add_extra_outputs(comel)
