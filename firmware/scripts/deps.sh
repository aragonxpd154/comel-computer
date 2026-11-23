#!/usr/bin/env bash
# COMEL — baixa as dependências do firmware em firmware/deps/ (fora do Git).
#   pico-sdk 2.2.0 (com TinyUSB) e Pico-PIO-USB 0.7.3
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p deps
if [ ! -d deps/pico-sdk ]; then
  git clone --depth 1 -b 2.2.0 https://github.com/raspberrypi/pico-sdk.git deps/pico-sdk
  git -C deps/pico-sdk submodule update --init --depth 1 lib/tinyusb
fi
if [ ! -d deps/Pico-PIO-USB ]; then
  git clone --depth 1 -b 0.7.3 https://github.com/sekigon-gonnoc/Pico-PIO-USB.git deps/Pico-PIO-USB
fi
echo "Dependências prontas. Agora:  cmake -B build -G Ninja && cmake --build build"
