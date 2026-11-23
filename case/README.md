# Carcaça COMEL — corte a laser

Caixa compacta em perfil de terminal para a placa COMEL (C64 em Pico 2 + 2 USB + entrada da fonte), a TSDA 4011R1, a tela de
7" VGA e a fonte Mean Well RD-35A. A furação da placa e a posição dos conectores vêm de `tools/eda/pcb_layouts.py`.

- **Medida externa:** 230 × 128 × 190 mm (largura × altura atrás × profundidade)
- **Perfil:** frente baixa de 18 mm, tela num painel inclinado 25° para trás, tampa reta
- **Chapa:** 3 mm (MDF ou acrílico). As laterais têm o perfil da caixa e recebem os dentes de todos os painéis
- **Mesa:** 2 chapas de 600 × 400 mm

## Arquivos (`saida/`)

| Arquivo | Uso |
|---|---|
| `chapa-1.svg` / `chapa-1.dxf` | base, traseiro, tampa, painel da tela, frente baixa e apoio da TSDA |
| `chapa-2.svg` / `chapa-2.dxf` | laterais e as 3 molduras da tela |
| `pecas/*.svg` | cada peça separada |
| `carcaca.json` | geometria usada pelo visualizador 3D |

Cores e camadas: **vermelho / CORTE** = cortar; **azul / GRAVAR** = gravar (preenchido). O texto cinza com o nome da peça no SVG é só referência: apague ou desligue antes de mandar para a máquina. No DXF a camada `CHAPA` mostra o contorno da mesa.

## Compensar o feixe (kerf)

As medidas são nominais. Para os dentes ficarem justos, gere de novo com a largura de corte da sua máquina:

```bash
make case KERF=0.15
# ou: python3 case/gerar_carcaca.py --kerf 0.15
```

Antes de cortar tudo, corte um canto de teste para acertar o kerf.

## Onde fica cada coisa

| Item | Posição |
|---|---|
| Placa COMEL | no piso, encostada no painel traseiro, lado esquerdo (USB e microSD saem pela lateral esquerda) |
| TSDA 4011R1 | no piso, encostada no painel traseiro, lado direito (RJ-45 e DB9 no traseiro) |
| Fonte RD-35A | no piso, à direita, na frente da TSDA — fica embaixo da ventilação da tampa e da lateral direita |
| Tela de 7" | no painel inclinado, presa pelas 3 molduras; a controladora vai colada atrás da trava |
| Módulo IEC | no traseiro, acima da TSDA · as 2 USB saem direto da placa pelo traseiro |

## O que conferir antes de cortar

- Recorte do módulo IEC (48 × 28 mm) com a peça comprada.
- Furos da RD-35A: pelo desenho da Mean Well (Case 932A) são 2 × M3 a 87 mm; por isso os furos da base são oblongos.
- Medidas da tela (165 × 100 mm, área ativa 154,2 × 85,9 mm) e da controladora PCB800099.
- A espessura real da chapa. Se não for 3,0 mm, troque `T` no começo do script.

## Ferragens

- 6 espaçadores M3 × 8 mm (nylon) com parafusos: 2 na TSDA e 4 na placa COMEL
- 4 parafusos M3 × 16 mm com porca: molduras da tela
- Nada para o teclado: o USB-A duplo da placa sai direto pelo recorte de 15,2 × 16,2 mm do traseiro
- 2 parafusos M3 × 6 mm: fonte, por baixo
- Módulo IEC C14 com chave e porta-fusível de encaixe, fusível de 1 A
- LED vermelho de 5 mm (o resistor de 330 Ω já está na placa)
- 4 pés de borracha adesivos

## Ordem de montagem

1. Cole o traseiro e uma lateral na base; depois a outra lateral.
2. Encaixe o apoio da TSDA nos 2 rasgos da base e cole.
3. Prenda os espaçadores, a TSDA, a placa COMEL e a fonte.
4. Encaixe o módulo IEC e o LED na frente baixa.
5. Fiação: +V/COM do 5 V e do 12 V da RD-35A no borne J10 da COMEL (entrada dos fios virada para a fonte);
   J11 no CN2 da TSDA; J12 na controladora da tela; J14 no LED. Fase, neutro e terra no módulo IEC.
6. Monte a tela no painel inclinado: painel, 2 espaçadores, trava e 4 parafusos M3. Cole a controladora atrás da trava.
7. Ligue o cabo da TSDA (J3 ou J4 → CN3) e o flat VGA (J1 → J4 da tela).
8. Cole a frente baixa e o painel da tela. As juntas entre eles e com a tampa são de topo (em ângulo) e vão coladas.
9. Encaixe a tampa.

Mexer na fiação de 127/220 V só com a caixa desligada da tomada. O terra (FG) da fonte vai no pino de terra do módulo IEC.
