# COMEL — atalhos do fluxo de projeto
#   make help        lista os alvos
PY ?= python3
BUILD = $(PY) tools/build_all.py

.PHONY: help setup check sch pcb fab render case viewer firmware fwtest all clean

help:            ## mostra esta ajuda
	@grep -E '^[a-z]+:.*##' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  \033[1m%-8s\033[0m %s\n", $$1, $$2}'

setup:           ## instala dependências (Ubuntu/Debian/Zorin)
	./scripts/setup-ubuntu.sh

check:           ## netlist == designs.py e DRC = 0 na placa COMEL
	$(PY) tools/eda/check.py

sch:             ## regenera biblioteca própria e esquemáticos a partir de tools/eda/designs.py
	$(BUILD) sym sch

pcb:             ## posiciona, roteia (Freerouting), planos de GND, DRC
	$(BUILD) pcb

fab:             ## Gerbers, furação, BOM, pick-and-place, STEP, PDFs
	$(BUILD) fab

render:          ## texturas, GLB/STL, imagens 2D e 3D, visualizador
	$(BUILD) tex mesh images case viewer

case:            ## carcaça cortada a laser (SVG/DXF) — use KERF=0.15 para compensar o feixe
	$(PY) case/gerar_carcaca.py --kerf $(or $(KERF),0)

viewer:          ## abre o visualizador 3D no navegador
	xdg-open docs/3d/viewer.html 2>/dev/null || open docs/3d/viewer.html

firmware:        ## compila o firmware do C64 (firmware/build/comel.uf2)
	cd firmware && bash scripts/deps.sh && cmake -B build -G Ninja && cmake --build build && cp build/comel.uf2 bin/comel.uf2

fwtest:          ## roda o emulador no PC (boot, teclado, LOAD/SAVE, SID, joystick)
	cd firmware/tests/host && ./build.sh && $(PY) make_sd.py && ./comel_host

all:             ## pipeline completo (sym → sch → pcb → fab → render → case)
	$(BUILD)

clean:           ## remove artefatos temporários
	rm -rf build tools/eda/logs
