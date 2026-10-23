"""Bloco 4 (linha 9): cada erupção paga a distância ao seu centro, ao quadrado. Só o que é deste bloco; o resto vem do
comum.py (plano, centros, linhas_ate, conta_soma, nome_soma).

- EXEMPLO: a erupção 69 do R (índice 68): 2,1 min (2,067) de duração e 65 min de espera, azul no fim, logo acima do
  losango azul (2,1; 54,8). A distância dela até o centro é quase toda na espera (0,03 min deitado, 10,25 min em pé):
  a linha amarela vai do ponto ao centro calculado e sai em pé, sem forçar.
- regua(pl): a linha amarela (atrás dos pontos, na frente das linhas cinza). anel(pl): o anel amarelo do exemplo.
- rotulo_distancia(quadrado): "distância" / "distância²" amarelo (NOME 44) no vão acima da nuvem azul (x −2,3 a 0,0,
  y 1,5 a 2,0: acima da 211, abaixo da marca dos 80 min, longe da 3), mesma borda esquerda e linha de base, contorno preto.
- setinha(): seta amarela curta para baixo sob a ponta direita do "soma dos quadrados (min²)", no canto vazio do alto
  à direita do plano (x 3,3: nenhuma erupção dura mais de 5,1 min, x 2,83; curta para não apontar a erupção de 96 min).
- fim_linha_9(): o último quadro da linha 9.
"""
from estilo import *
from comum import *
from comum import _confere

EXEMPLO = 68  # rownames 69
_confere(DUR[EXEMPLO] == 2.067 and ESP[EXEMPLO] == 65 and GRUPOS[5][EXEMPLO] == 0
         and (br(DUR[EXEMPLO], 1), br(ESP[EXEMPLO])) == ("2,1", "65"), "erupção 69: (2,1 min; 65 min), azul")

X_DIST, Y_DIST = -2.3, 1.74  # borda esquerda e centro (em pé) do "distância": logo acima do 211 (y 1,33)


def regua(pl):
    """A distância da erupção 69 ao centro azul (CENTROS[5][0]), em amarelo: quase em pé, como nos dados."""
    return Line(pl.pos(EXEMPLO), pl.p(*CENTROS[5][0]), stroke_width=ESPESSURA, color=AMARELO).set_z_index(-0.5)


def anel(pl):
    """Anel amarelo na erupção 69 (r 0,12: não encosta na 249, logo acima dela)."""
    return Circle(radius=0.12, color=AMARELO, stroke_width=4).move_to(pl.pos(EXEMPLO)).set_z_index(1)


def rotulo_distancia(quadrado=False):
    """"distância" (ou "distância²", com as mesmas letras no mesmo lugar) no vão acima da nuvem azul."""
    base = Text("distância", font_size=NOME, color=AMARELO)
    base.move_to([X_DIST + base.width / 2, Y_DIST, 0])
    if not quadrado:
        return base.set_stroke(FUNDO, 8, background=True).set_z_index(4)
    t = Text("distância²", font_size=NOME, color=AMARELO)
    # contorno preto atrás das letras: a linha cinza da 211 passa sob o "cia" sem cortar a leitura
    return t.align_to(base, LEFT).align_to(base, DOWN).set_stroke(FUNDO, 8, background=True).set_z_index(4)


def setinha():
    """Seta amarela para baixo (a soma quer descer), sob a ponta direita do nome_soma(), acima do canto vazio do plano."""
    topo = nome_soma().get_bottom()[1] - 0.08
    return Arrow([3.3, topo, 0], [3.3, topo - 0.66, 0], buff=0, stroke_width=ESPESSURA, color=AMARELO,
                 max_tip_length_to_length_ratio=0.42, max_stroke_width_to_length_ratio=10)


def fim_linha_9():
    """Último quadro da linha 9: plano final com as linhas cinza até os centros, a régua amarela com "distância²",
    "3.456 + 5.446 = 8.902", "soma dos quadrados (min²)" e a setinha."""
    pl = plano(5)
    return {"plano": pl, "centros": centros(pl, 5), "linhas": linhas_ate(pl, 5), "regua": regua(pl),
            "rotulo": rotulo_distancia(True), "conta": conta_soma(), "nome": nome_soma(), "setinha": setinha()}
