"""KNN, bloco 5 (linhas 13 a 15): as peças que só este bloco usa, em posições fixas.

Linha 13: cartões da Barbicha (esq) e da Adélia (dir), as contas embaixo e o veredito na FAIXA.
Linha 14: o plano em desvios com a fórmula, "padronizar", os 5 Barbichas e o placar.
"""
from comum import *
from comum import _confere

FS = 44  # contas desta linha: 5 filas de até 5,4 de largura cabem entre os cartões e o canto
X_CONTA = -3.4
_PD = T["misterioso"]["conta_ate_a_barbicha"]["padronizado_deltas"]  # "0,4 mm ÷ 5,45 = 0,07", "100 g ÷ 801 = 0,12"
_A = T["misterioso"]["conta_ate_a_adelia"]["padronizado_deltas"][0]  # "8,7 mm ÷ 5,45 = 1,60"
_confere(_PD == ["0,4 mm ÷ 5,45 = 0,07", "100 g ÷ 801 = 0,12"] and _A == "8,7 mm ÷ 5,45 = 1,60",
         "contas padronizadas da linha 13")
_confere(T["misterioso"]["conta_ate_a_barbicha"]["padronizado"].endswith("√0,0193 = 0,14"), "d da Barbicha 0,14")


def cartoes_13():
    cb = cartao(ROXO, "0,4 mm", "100 g").move_to(CARTAO_ESQ)
    ca = cartao(LARANJA, "8,7 mm", "0 g").move_to(CARTAO_DIR)
    return cb, ca


def contas_13():
    def fila(c, y, direita=False):
        if direita:
            return c.move_to([3.4 - c.width / 2, y, 0])
        return c.move_to([X_CONTA + c.width / 2, y, 0])

    r1 = fila(conta("0,4", " ÷ ", "5,45", " = ", "0,07", tamanho=FS, cores={2: AMARELO}), 1.05)
    r2 = fila(conta("100", " ÷ ", "801", " = ", "0,12", tamanho=FS, cores={2: AMARELO}), 0.4)
    r2.align_to(r1, LEFT)
    dp = VGroup(Text("desvio-", font_size=PQ, color=AMARELO), Text("padrão", font_size=PQ, color=AMARELO)).arrange(
        DOWN, buff=0.1, aligned_edge=LEFT).move_to([2.45, 0.72, 0])
    r3 = fila(conta("d = √(", "0,07²", " + ", "0,12²", FINO + ")", tamanho=FS), -0.3)
    r4 = fila(conta("= √0,0193", " = ", "0,14", tamanho=FS, cores={2: ROXO}), -0.98)
    r5 = fila(conta("d = ", "8,7 ÷ ", "5,45", " = ", "1,60", tamanho=FS, cores={2: AMARELO, 4: LARANJA}), -1.72,
              direita=True)
    g = VGroup(r1, r2, dp, r3, r4, r5)
    g.r1, g.r2, g.dp, g.r3, g.r4, g.r5 = g
    return g


def veredito(agora=False):
    """Na FAIXA: "antes" 100,0 > 8,7 (Barbicha > Adélia) ou "agora" 0,14 < 1,60."""
    cx = (FAIXA[0] + FAIXA[2]) / 2
    nome = Text("agora" if agora else "antes", font_size=PQ, color=CINZA).move_to([cx, -2.8, 0])
    c = (conta("0,14", " < ", "1,60", tamanho=FC, cores={0: ROXO, 2: LARANJA}) if agora else
         conta("100,0", " > ", "8,7", tamanho=FC, cores={0: ROXO, 2: LARANJA}))
    c.move_to([cx, -3.45, 0])
    return VGroup(nome, c)


def fim_linha_13():
    cb, ca = cartoes_13()
    return rotulo_knn(), cb, ca, contas_13(), veredito(agora=True)


# ---------------------------------------------------------------- linha 14

def formula_14(acesa=False):
    f = formula_z()
    if acesa:
        f[2].set_color(CINZA)
        f[4].set_color(AMARELO)
    return f


def padronizar():
    """Rótulo à direita de "peso (desvios)", em cima do quadrado."""
    t = Text("padronizar", font_size=FS, color=AMARELO)
    return t.move_to([3.42 - t.width / 2, 4.1, 0])


def fim_linha_14():
    pz = plano_z(True)
    linhas = linhas_ate(pz, VIZ_Z)
    an = aneis(pz, VIZ_Z)
    pl = placar(("Barbicha", 5), ("Adélia", 0))
    ok = certo(pl.vaga)
    return rotulo_knn(), pz, formula_14(True), padronizar(), linhas, an, pl, ok
