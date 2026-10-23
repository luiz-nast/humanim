"""Bloco 1 (linhas 1 e 2): o que só estas duas linhas usam, além do comum.py.

- jorro(geiser): o gêiser solta o jato (cresce e volta ao mesmo desenho: a emenda não muda).
- definicao_espera(): "espera: entre uma erupção e outra", pequeno e cinza, em duas filas no alto à esquerda, logo
  acima do eixo em pé. Numa fila só são 8,3 de largura (a tela tem 6,9) e, embaixo do "espera (min)", dentro do
  plano, as erupções longas ocupam o lugar; por isso fica em cima do eixo, colada à esquerda.
- contador_empilhado(n): o "272 erupções" da linha 2 em pé, no alto à direita ("272" em cima, "erupções" embaixo),
  para a definição caber à esquerda. O número cresce para a esquerda (borda direita fixa).
- CLARO: o cinza claro das barras de marcas_nuvem, também no contorno do halo.
"""
from comum import *

CLARO = interpolate_color(ManimColor(CINZA), ManimColor(BRANCO), 0.5)


def jorro(g, fator=1.1):
    """Animação: o jato e as nuvenzinhas do gêiser g (VGroup de geiser()) crescem a partir do morro e voltam."""
    return VGroup(g[0], g[1]).animate(rate_func=there_and_back).scale(fator, about_point=g[2].get_top())


def definicao_espera():
    """Linha 2: a definição da espera, duas filas cinza (PQ) no alto à esquerda, acima do "100" e do "espera (min)"."""
    t = VGroup(Text("espera: entre uma", font_size=PQ, color=CINZA),
               Text("erupção e outra", font_size=PQ, color=CINZA)).arrange(DOWN, buff=0.1, aligned_edge=LEFT)
    return t.move_to([ESQ + t.width / 2, 4.15 + t.height / 2, 0])


def contador_empilhado(n=0):
    """Linha 2: "272" (Integer 96) em cima de "erupções", encostados à direita no alto. VGroup(Integer, texto);
    .n o Integer (borda direita fixa), .nome o texto."""
    num = Integer(n, font_size=96, color=BRANCO)
    num.move_to([DIR - num.width / 2, 5.07, 0])
    t = Text("erupções", font_size=NOME, color=BRANCO)
    t.move_to([DIR - t.width / 2, num.get_bottom()[1] - 0.14 - t.height / 2, 0])
    num.edge_to_fix = RIGHT
    g = VGroup(num, t)
    g.n, g.nome = num, t
    return g
