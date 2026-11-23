#!/usr/bin/env python3
"""Modelo 3D (STEP colorido) do Raspberry Pi Pico 2 encaixado nas barras fêmea.

O KiCad 7 não traz o Pico na biblioteca 3D; este script monta um modelo simples
com OpenCascade (pip install cadquery-ocp): duas barras fêmea 1×20, a placa verde
do módulo, o RP2350, a flash, o cristal, o conector micro-USB, o botão BOOTSEL,
o LED e os 40 furos dourados.

Coordenadas do modelo 3D do KiCad: x para a direita, y para CIMA (o pino 1 fica
em y = +24,13), z para cima a partir da face da placa-mãe.
"""
from pathlib import Path

from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakeCylinder
from OCP.gp import gp_Pnt, gp_Ax2, gp_Dir
from OCP.IFSelect import IFSelect_RetDone
from OCP.Quantity import Quantity_Color, Quantity_TOC_RGB
from OCP.STEPCAFControl import STEPCAFControl_Writer
from OCP.STEPControl import STEPControl_AsIs
from OCP.TCollection import TCollection_ExtendedString
from OCP.TDocStd import TDocStd_Document
from OCP.XCAFDoc import XCAFDoc_DocumentTool, XCAFDoc_ColorType

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "hardware" / "lib" / "3d"

SOCKET_H = 8.5          # altura da barra fêmea
PCB_T = 1.0             # espessura da placa do Pico


def box(x0, y0, z0, dx, dy, dz):
    return BRepPrimAPI_MakeBox(gp_Pnt(x0, y0, z0), dx, dy, dz).Shape()


def cyl(x, y, z, r, h):
    return BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(x, y, z), gp_Dir(0, 0, 1)), r, h).Shape()


def write(doc, name):
    OUT.mkdir(parents=True, exist_ok=True)
    w = STEPCAFControl_Writer()
    w.SetColorMode(True)
    w.Transfer(doc, STEPControl_AsIs)
    path = OUT / name
    assert w.Write(str(path)) == IFSelect_RetDone
    print("escrito", path)


def build_usb():
    """USB-A duplo empilhado (Würth 61400826021) nas coordenadas do footprint do KiCad:
    corpo x −3,8…10,8, boca em y = −15,66 (no modelo 3D o y é invertido), altura 15,6 mm."""
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut
    doc = TDocStd_Document(TCollection_ExtendedString("usb"))
    shapes = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
    colors = XCAFDoc_DocumentTool.ColorTool_s(doc.Main())

    def add(shape, rgb):
        lab = shapes.AddShape(shape, False)
        colors.SetColor(lab, Quantity_Color(*[c / 255 for c in rgb], Quantity_TOC_RGB), XCAFDoc_ColorType.XCAFDoc_ColorSurf)

    shell = box(-3.8, -15.66, 0, 14.6, 17.1, 15.6)
    for z0 in (1.9, 9.0):                                              # as duas bocas
        shell = BRepAlgoAPI_Cut(shell, box(-2.75, -15.8, z0, 12.5, 13.0, 5.1)).Shape()
    add(shell, (196, 200, 206))
    for z0 in (1.9, 9.0):
        add(box(-2.55, -14.9, z0 + 0.3, 12.1, 12.0, 4.5), (18, 18, 20), )       # fundo escuro
        add(box(-2.0, -15.3, z0 + 2.9, 11.0, 12.0, 1.8), (30, 30, 34))           # língua de plástico
        for i in range(4):                                                       # contatos
            add(box(-1.4 + i * 2.6 + 0.0, -15.2, z0 + 2.85, 1.0, 8.0, 0.06), (214, 172, 72))
    write(doc, "USB_A_Stacked_2x.step")


def build():
    doc = TDocStd_Document(TCollection_ExtendedString("pico2"))
    shapes = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
    colors = XCAFDoc_DocumentTool.ColorTool_s(doc.Main())

    def add(shape, rgb, name):
        lab = shapes.AddShape(shape, False)
        colors.SetColor(lab, Quantity_Color(*[c / 255 for c in rgb], Quantity_TOC_RGB), XCAFDoc_ColorType.XCAFDoc_ColorSurf)

    zt = SOCKET_H + PCB_T
    for sx in (-1, 1):
        add(box(sx * 8.89 - 1.27, -25.4, 0, 2.54, 50.8, SOCKET_H), (24, 24, 26), "socket")
    add(box(-10.5, -25.5, SOCKET_H, 21.0, 51.0, PCB_T), (22, 110, 58), "pcb")
    for i in range(20):                                             # furos/castelações dourados
        y = 24.13 - 2.54 * i
        for sx in (-1, 1):
            add(cyl(sx * 8.89, y, zt, 0.75, 0.04), (214, 172, 72), "pad")
    add(box(-3.5, -3.5 + 2.0, zt, 7.0, 7.0, 0.9), (20, 20, 22), "rp2350")
    add(box(-3.0, -11.5, zt, 6.0, 5.0, 1.2), (28, 28, 30), "flash")
    add(box(1.8, 6.4, zt, 3.2, 2.5, 0.8), (190, 190, 196), "cristal")
    add(box(-4.0, 21.6, zt, 8.0, 5.6, 2.9), (200, 204, 208), "usb")       # micro-USB (sai 1,1 mm pela borda)
    add(box(-5.6, 13.0, zt, 3.6, 4.6, 1.4), (240, 240, 236), "bootsel")
    add(box(-4.8, 17.2, zt, 1.0, 1.6, 0.6), (120, 230, 120), "led")
    add(box(5.6, -22.0, zt, 2.5, 1.2, 0.8), (40, 40, 40), "debug")
    write(doc, "RaspberryPi_Pico2_Socket.step")


if __name__ == "__main__":
    build()
    build_usb()
