"""Bloco 2 (linhas 4 e 5): o que só estas duas linhas usam, e os estados em que cada uma termina.

  fim_linha_4(pl=None) -> o último quadro da 4 e o 1º da 5: plano(0) (brancas), centros(pl, 0), rotulo_k() e
    rotulos_centro(pl) ("centro" azul embaixo à direita do losango azul, laranja à esquerda do laranja).
  fim_linha_5() -> o último quadro da 5 (a linha 6 recomeça daqui e apaga anéis e contas): estado(1, fase=1) do
    comum.py (plano(1), centros(pl, 0), fronteira(pl, 0)), rotulo_k(), regra(1), aneis(pl, ERRADOS),
    "grupos" ("191" + "erupções" azul na vaga 0; "81 erupções" laranja numa fila no alto à esquerda, acima da
    fronteira) e "conta" (191 − 91 = 100 curtas em coluna, na FAIXA à direita do canto: fora do canto).
    Para emendar: self.add(*mobs(fim_linha_5())).
  exemplo(pl) -> a erupção 13 (rownames; índice 12) e as duas distâncias da regra 1 (para_tela.comeco.exemplo_regra_1).
"""
from comum import *
from comum import _confere

EX = 12  # erupção 13 do R (rownames = índice + 1): 4,2 min; 78 min
_ER = T["comeco"]["exemplo_regra_1"]
_confere((DUR[EX], ESP[EX]) == (4.2, 78) and _ER["erupcao"].startswith("erupção 13:"), "erupção 13 (4,2; 78)")
_confere(GRUPOS[1][EX] == 0 and EX in ERRADOS, "a erupção 13 cai com o centro de baixo e está entre os 91")
_confere(T["comeco"]["conta_errados"] == "191 − 91 = 100", "191 − 91 = 100")
_confere(CENTROS[0][0] == (DUR[73], ESP[73]) and CENTROS[0][1] == (DUR[202], ESP[202]), "centros = erupções 74 e 203")
INICIAIS = (73, 202)  # as erupções (rownames 74 e 203) que viram os dois centros


def rotulos_centro(pl):
    """"centro" ao lado de cada losango, na cor do grupo, nos vãos sem erupção: o azul embaixo à direita do losango
    azul (abaixo da nuvem de cima), o laranja à esquerda do laranja (entre a nuvem e o "espera (min)")."""
    a, l = (pl.p(*CENTROS[0][g]) for g in (0, 1))
    ta = Text("centro", font_size=NOME, color=COR_G[0])
    ta.move_to([a[0] + 0.15 + ta.width / 2, a[1] - 0.35 - ta.height / 2, 0])
    tl = Text("centro", font_size=NOME, color=COR_G[1])
    tl.move_to([l[0] - 0.37 - tl.width / 2, l[1] - 0.1, 0])
    return VGroup(ta, tl)


def fim_linha_4(pl=None):
    pl = plano(0) if pl is None else pl
    return {"plano": pl, "centros": centros(pl, 0), "k": rotulo_k(), "rotulos": rotulos_centro(pl)}


def rotulos_grupos(pl):
    """"191" + "erupções" (azul, empilhado na vaga 0) e "81 erupções" (laranja, uma fila no alto à esquerda: a vaga 1
    fica colada na fronteira). Os dois longe da tracejada (81 min)."""
    g0 = rotulo_grupo(pl, 0, str(TAMANHOS[1][0]), "erupções")
    n = Text(str(TAMANHOS[1][1]), font_size=G + 4, color=COR_G[1])
    t = Text("erupções", font_size=PQ, color=COR_G[1])
    t.next_to(n, RIGHT, buff=0.15).align_to(n, DOWN).shift(DOWN * (t[0].get_bottom()[1] - t.get_bottom()[1]))
    g1 = VGroup(n, t)  # mesma linha de base (o "ç" e o "p" descem)
    g1.move_to([pl.esq + 0.2 + g1.width / 2, pl.p(0, 89)[1], 0])
    return VGroup(g0, g1)


def conta_errados():
    """191 − 91 = 100 curtas como conta de armar, na FAIXA à direita do canto (cabe em [CANTO]).
    VGroup(n191, menos_91, traco, resultado): [1] é VGroup(menos, 91 amarelo); [3] é VGroup(100, curtas)."""
    a, b = str(TAMANHOS[1][0]), str(len(ERRADOS))
    c = str(TAMANHOS[1][0] - len(ERRADOS))
    _confere(f"{a} {MENOS} {b} = {c}" == T["comeco"]["conta_errados"], "191 − 91 = 100")
    d = 1.35  # borda direita dos números
    n1 = Text(a, font_size=FC, color=COR_G[0])
    n1.move_to([d - n1.width / 2, -2.7, 0])
    n2 = Text(b, font_size=FC, color=AMARELO)
    n2.move_to([d - n2.width / 2, -3.35, 0])
    menos = Text(MENOS, font_size=FC, color=BRANCO).next_to(n1, LEFT, buff=0.12).set_y(n2.get_y())
    traco = Line([menos.get_left()[0] - 0.05, -3.75, 0], [d + 0.05, -3.75, 0], stroke_width=4, color=BRANCO)
    n3 = Text(c, font_size=FC, color=COR_G[0])
    n3.move_to([d - n3.width / 2, -4.2, 0])
    nome = Text("curtas", font_size=FC, color=COR_G[0]).next_to(n3, RIGHT, buff=0.2, aligned_edge=DOWN)
    return VGroup(n1, VGroup(menos, n2), traco, VGroup(n3, nome))


def fim_linha_5():
    e = estado(1, fase=1)
    pl = e["plano"]
    return {"plano": pl, "fronteira": e["fronteira"], "centros": e["centros"], "k": rotulo_k(), "regra": regra(1),
            "aneis": aneis(pl, ERRADOS), "grupos": rotulos_grupos(pl), "conta": conta_errados()}


def mobs(d):
    """Os Mobjects de um fim_linha_N(), na ordem de self.add (o Plano entra como .tudo)."""
    return [v.tudo if isinstance(v, Plano) else v for v in d.values()]


def _sem_min(s):
    return s.replace(" min", "")


def exemplo(pl):
    """A erupção 13 e as duas distâncias da regra 1. dict:
    destaque VGroup(ponto branco maior, anel amarelo); linhas [até o azul, até o laranja] (cor do centro, atrás dos
    losangos); rotulos ["7,0 min" azul à direita do losango azul, "13,0 min" laranja à esquerda da de cima], com
    fundo preto; contas [√(0,2² + 7²) = 7,0 em YB1, √(0,1² + 13²) = 13,0 em YB2] ([2] é o resultado, na cor do centro).
    Textos de para_tela.comeco.exemplo_regra_1."""
    e = pl.pos(EX)
    destaque = VGroup(Dot(e, radius=0.1, color=BRANCO), Circle(radius=0.19, color=AMARELO, stroke_width=4).move_to(e))
    destaque.set_z_index(2.5)
    linhas, rotulos, contas = [], [], []
    for g, k, y in ((0, "ate_o_centro_de_baixo", YB1), (1, "ate_o_centro_de_cima", YB2)):
        c = pl.p(*CENTROS[0][g])
        linhas.append(Line(e, c, stroke_width=5, color=COR_G[g]).set_z_index(1))
        esq, dir_ = _ER[k].split(" = ")  # "√(0,2² + 7²)", "7,0 min"
        t = Text(dir_, font_size=PQ, color=COR_G[g])
        m = (e + c) / 2
        if g == 0:  # à direita do losango azul (à direita da linha, abaixo do anel da erupção)
            t.move_to([c[0] + 0.4 + t.width / 2, c[1] + 0.07, 0])
        else:
            t.move_to([m[0] - 0.3 - t.width / 2, m[1] + 0.05, 0])
        fundo = BackgroundRectangle(t, color=FUNDO, fill_opacity=0.85, buff=0.07)
        rotulos.append(VGroup(fundo, t).set_z_index(2))
        contas.append(conta(esq[:-1] + FINO + ")", " = ", _sem_min(dir_), tamanho=PQ + 4, cores={2: COR_G[g]})
                      .move_to([0, y, 0]))
    return {"destaque": destaque, "linhas": linhas, "rotulos": rotulos, "contas": contas}
