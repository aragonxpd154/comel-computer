#!/usr/bin/env python3
"""COMEL — cria sd.img (FAT32, 64 MB) com /c64/hello.prg para o teste no PC."""
import os, subprocess
lines = [(10, b'\x99"OLA, COMEL!"'), (20, b'\x99"VGA + USB + SID NA PLACA UNICA"'), (30, b'\x99"PRONTO."')]
addr, out = 0x0801, bytearray()
for num, body in lines:
    nxt = addr + 4 + len(body) + 1
    out += bytes([nxt & 0xFF, nxt >> 8, num & 0xFF, num >> 8]) + body + b'\0'
    addr = nxt
out += b'\0\0'
os.makedirs('tmp', exist_ok=True)
open('tmp/hello.prg', 'wb').write(bytes([0x01, 0x08]) + out)
if os.path.exists('sd.img'): os.remove('sd.img')
subprocess.run(['dd', 'if=/dev/zero', 'of=sd.img', 'bs=1M', 'count=64', 'status=none'], check=True)
subprocess.run(['mkfs.fat', '-F', '32', '-n', 'COMEL', 'sd.img'], check=True, stdout=subprocess.DEVNULL)
subprocess.run(['mmd', '-i', 'sd.img', '::/c64'], check=True)
subprocess.run(['mcopy', '-i', 'sd.img', 'tmp/hello.prg', '::/c64/hello.prg'], check=True)
print('sd.img pronto')
