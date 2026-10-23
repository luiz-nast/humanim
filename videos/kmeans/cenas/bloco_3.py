"""Bloco 3 (linhas 6 e 7): a regra 2 e as rodadas 2 a 5. Só o que é deste bloco; o resto vem do comum.py.

- fronteira_viva(pl, los): a fronteira calculada (em minutos) dos losangos onde eles estiverem, quadro a quadro: anda
  junto com os centros, sem mediatriz no olho. Parada, é igual à fronteira(pl, r) do comum.py.
- Rótulos dos centros nos dois cantos vazios do plano: azul embaixo à direita, laranja no alto à esquerda.
- fim_linha_5(): o 1º quadro da linha 6, que é o fim_linha_5() do bloco_2.py (a linha 5 termina nele).
- fim_linha_6(): o último quadro da 6 e o 1º da 7.
"""
from estilo import *
from comum import *
import bloco_2 as b2  # o fim da linha 5 (só leitura)


def minutos(pl, ponto):
    """Inverso de pl.p: (duração, espera) em minutos de um ponto da tela."""
    return (pl.x0 + (ponto[0] - pl.esq) / (pl.dir - pl.esq) * (pl.x1 - pl.x0),
            pl.y0 + (ponto[1] - pl.base) / (pl.topo - pl.base) * (pl.y1 - pl.y0))


def fronteira_de(pl, ca, cb, cor=BRANCO):
    """A fronteira() do comum.py para dois centros quaisquer (em minutos): mesma conta, mesmo desenho."""
    (a0, b0), (a1, b1) = ca, cb
    n = np.array([a1 - a0, b1 - b0])
    m = np.array([(a0 + a1) / 2, (b0 + b1) / 2])
    d = np.array([-n[1], n[0]]) / np.linalg.norm(n)
    ts = []
    for k, (lo, hi) in enumerate(((pl.x0, pl.x1), (pl.y0, pl.y1))):
        if abs(d[k]) > 1e-9:
            ts += sorted(((lo - m[k]) / d[k], (hi - m[k]) / d[k]))
    t0 = max(ts[0], ts[2]) if len(ts) == 4 else ts[0]
    t1 = min(ts[1], ts[3]) if len(ts) == 4 else ts[1]
    a, b = m + t0 * d, m + t1 * d
    return DashedLine(pl.p(*a), pl.p(*b), dash_length=0.16, color=cor, stroke_width=EIXO).set_z_index(2)


def fronteira_viva(pl, los):
    """Fronteira redesenhada a cada quadro a partir de onde os losangos estão (convertido para minutos)."""
    return always_redraw(lambda: fronteira_de(pl, minutos(pl, los[0].get_center()), minutos(pl, los[1].get_center())))


# ---------------------------------------------------------------- rótulos dos centros (posições fixas)
# Os dois cantos vazios do plano (conferido nos dados): embaixo à direita (x −0,3..3,3 em y −0,5..0,55, e x 1,1..3,3
# até y 1,05) e no alto à esquerda (x −2,3..0,12, y 1,45..3,13). A fronteira passa em 81 min (y 2,15) até a regra 2 e
# depois desce: no alto à esquerda só cabe uma fila acima dela, a das coordenadas laranja.

X_AZUL = 1.09  # azul: textos com a borda esquerda aqui, à direita do losango azul (as coordenadas vão até 3,49)
X_LARANJA = 0.07  # laranja: textos com a borda direita aqui, à esquerda da nuvem longa
Y_CENTRO = 0.825  # "centro" azul, na altura do losango azul no fim da linha 6
Y_CENTROIDE = 0.33  # "(centroide)", uma vez, sob o "centro" azul
Y_COORD = (-0.215, 2.55)  # coordenadas de cada grupo (azul acima do "duração (min)"; laranja acima da fronteira)


def _encosta(m, g, y):
    """Azul: borda esquerda em X_AZUL; laranja: borda direita em X_LARANJA."""
    x = X_AZUL + m.width / 2 if g == 0 else X_LARANJA - m.width / 2
    return m.move_to([x, y, 0])


def coords(g, r):
    """"(3,1; 64,9)" do centro g depois da rodada r, na cor do grupo: conta com [1] a duração e [3] a espera."""
    d, e = CENTROS[r][g]
    if f"({br(d, 1)}; {br(e, 1)})" != coord(g, r):
        raise ValueError("bloco_3.py: coordenadas diferentes do coord() do comum.py")
    c = conta("(", br(d, 1), "; ", br(e, 1), ")", tamanho=PQ, cor=COR_G[g])
    return _encosta(c, g, Y_COORD[g]).set_z_index(4)


def rotulo_centro():
    """"centro" azul (NOME, como na linha 4) à direita do losango azul, no canto vazio de baixo (fim da linha 6).
    O laranja não fica com o seu: no alto à esquerda só cabem as coordenadas."""
    return _encosta(Text("centro", font_size=NOME, color=COR_G[0]), 0, Y_CENTRO).set_z_index(4)


def centroide():
    """"(centroide)" pequeno e cinza, sob o "centro" azul (o nome técnico, uma vez)."""
    return _encosta(Text("(centroide)", font_size=PEQUENO, color=CINZA), 0, Y_CENTROIDE).set_z_index(4)


# ---------------------------------------------------------------- emendas


def fim_linha_5():
    """1º quadro da linha 6 = último da 5: o fim_linha_5() do bloco_2.py (plano, fronteira, centros, k, regra,
    aneis, grupos, conta; a conta fica na FAIXA, fora do canto)."""
    return b2.fim_linha_5()


def fim_linha_6():
    """Último quadro da linha 6 (e 1º da 7): rodada 1 depois da regra 2 (centros na média, fronteira onde eles
    empatam), "k = 2", as duas regras, "centro" (centroide) do azul e as coordenadas de cada centro."""
    e = estado(1, fase=2)
    return {"k": rotulo_k("k = 2"), "regra1": regra(1), "regra2": regra(2), "plano": e["plano"],
            "centros": e["centros"], "fronteira": e["fronteira"],
            "centro": rotulo_centro(), "centroide": centroide(),
            "coords": VGroup(coords(0, 1), coords(1, 1))}


def adicionar(cena, partes):
    """self.add de um estado (dict do fim_linha_N), com o plano por inteiro."""
    for k, v in partes.items():
        cena.add(v.tudo if isinstance(v, Plano) else v)
