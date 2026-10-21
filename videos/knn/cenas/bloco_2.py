"""Bloco 2 (linhas 5 e 6): o triângulo da distância, a fórmula e o zoom nos 5 vizinhos crus.

fim_linha_3() refaz o último quadro da linha 3 (linha_03.py): plano, título, 5 linhas amarelas, anéis, "5 mais perto".
fim_linha_5() é o último quadro da 5 e o primeiro da 6.
"""
from comum import *

GENTOO = 187  # Gentoo de 59,6 mm e 6.050 g: no alto à direita do misterioso (triângulo mais largo que cabe)
Y_FORMULA = 4.25  # entre o topo do plano (3,6) e o rótulo KNN (base 4,71); o título dos dados saiu


def faixa_5():
    """O que a linha 3 deixa na faixa à direita: "5" amarelo e "mais perto"."""
    cinco = contador(5).set_color(AMARELO)
    nome = Text("mais perto", font_size=PQ, color=AMARELO).move_to(FAIXA_CENTRO + [0, -0.6, 0])
    return VGroup(cinco, nome)


def fim_linha_3():
    pl, tit, _ = fim_linha_2()
    amarelas = linhas_ate(pl, VIZ_CRU).set_z_index(1)
    an = aneis(pl, VIZ_CRU).set_z_index(1)
    return pl, tit, amarelas, an, faixa_5()


def _fundo(m):
    return BackgroundRectangle(m, color=FUNDO, fill_opacity=0.9, buff=0.06)


def triangulo(pl):
    """Hipotenusa amarela do misterioso ao Gentoo, catetos brancos, marca do ângulo reto, "Δbico" e "Δpeso"."""
    a, g = pl.misterioso.get_center(), pl.pos(GENTOO)
    c = np.array([g[0], a[1], 0])
    hip = Line(a, g, color=AMARELO, stroke_width=5).set_z_index(1)
    deitado = Line(a, c, color=BRANCO, stroke_width=4).set_z_index(1)
    em_pe = Line(c, g, color=BRANCO, stroke_width=4).set_z_index(1)
    reto = VMobject().set_points_as_corners([c + [-0.22, 0, 0], c + [-0.22, 0.22, 0], c + [0, 0.22, 0]]).set_stroke(
        BRANCO, 3).set_z_index(1)
    lb = Text("Δbico", font_size=PQ, color=BRANCO)
    lb.move_to([(a[0] + c[0]) / 2, a[1] - 0.42, 0])  # embaixo do cateto (o "?" sai na linha 5)
    lp = Text("Δpeso", font_size=PQ, color=BRANCO).rotate(PI / 2)
    lp.move_to([g[0] - 0.12 - lp.width / 2, (a[1] + g[1]) / 2 + 0.25, 0])  # dentro, colado no cateto em pé
    lb, lp = VGroup(_fundo(lb), lb).set_z_index(2), VGroup(_fundo(lp), lp).set_z_index(2)
    t = VGroup(hip, deitado, em_pe, reto, lb, lp)
    t.hip, t.deitado, t.em_pe, t.reto, t.lb, t.lp = hip, deitado, em_pe, reto, lb, lp
    return t


def formula_d(tamanho=FC):
    """"d = √(Δbico² + Δpeso²)": [0] "d = √(", [1] "Δbico²", [2] " + ", [3] "Δpeso²", [4] ")"."""
    return conta("d = √(", "Δbico²", " + ", "Δpeso²", FINO + ")", tamanho=tamanho).move_to([0, Y_FORMULA, 0])


def fim_linha_5():
    pl, _, _, an, fx = fim_linha_3()
    pl.tudo.remove(pl.interrogacao)  # o "?" sai quando o triângulo nasce; volta no zoom da linha 6
    return {"plano": pl, "aneis": an, "faixa": fx, "knn": rotulo_knn(), "tri": triangulo(pl), "formula": formula_d()}
