"""[CANTO] Aqui, começar por um mês dava um tiquinho menos bagunça.

A árvore gulosa encolhe para a metade de cima, com o cadeado e "gulosa" ao lado dele e a bagunça final dela
(0,2810) à direita da raiz. Na metade de baixo, ainda acima do canto, nasce a árvore fantasma, toda em cinza e
tracejada, que começa por "1+ mês?" ("2+ meses?" no "sim", "julho 2+?" no "não"), com 0,2808 na mesma coluna,
embaixo do 0,2810: só os dois últimos dígitos mudam. Em "tiquinho", o "08" acende em amarelo e aparece "por um
fio". (Busca em 11 colunas; é menos bagunça nas folhas, não mais acerto: a fala diz só "menos bagunça".)
"""
from estilo import *
from comum import *

PARTES = ("raiz", "a", "b", "s_a", "s_b", "n_a", "n_b")


class Cena(CenaHumanim):
    def construct(self):
        g = gulosa()
        cad = raiz_travada(g["raiz"])
        nome = rotulo("busca gulosa", cor=AMARELO, tamanho=48).next_to(g["raiz"], UP, buff=0.22)
        num = numero_grande(GULOSA)
        self.add(*(g[k] for k in PARTES + ("c_a", "c_b")), cad, nome, num)

        # A gulosa encolhe para cima, com o número à direita da raiz.
        p = gulosa(grande=False)
        cad_p = raiz_travada(p["raiz"], escala=1.0)
        num_p = numero_16(GULOSA, p["raiz"].get_y() + 0.1)
        nome_p = rotulo("gulosa", cor=AZUL, tamanho=PEQUENO).next_to(num_p, DOWN, buff=0.15).align_to(num_p, RIGHT)
        self.play(*(Transform(g[k], p[k]) for k in PARTES), Transform(cad, cad_p), FadeOut(nome, shift=UP * 0.2),
                  FadeOut(VGroup(g["c_a"], g["c_b"], num)), run_time=0.45)
        self.play(FadeIn(nome_p, shift=LEFT * 0.2), FadeIn(num_p, shift=LEFT * 0.3), run_time=0.3)

        # A fantasma: começa por "1+ mês?".
        f = fantasma()
        num_f = numero_16(OUTRA, f["raiz"].get_y() + 0.1, cor=CINZA)
        self.ate("começar")
        self.play(FadeIn(f["raiz"], shift=UP * 0.3), run_time=0.35)
        self.ate("um")
        self.play(*(GrowArrow(f[k]) for k in ("s_a", "s_b")), *(FadeIn(f[k]) for k in ("n_a", "n_b", "a", "b")),
                  run_time=0.4)
        self.ate("dava")
        self.play(FadeIn(num_f, shift=LEFT * 0.2), run_time=0.35)

        fio = rotulo("por um fio", cor=AMARELO, tamanho=PQ).next_to(num_f, DOWN, buff=0.25)
        self.ate("tiquinho")
        self.play(num_f[1].animate.set_color(AMARELO), num_p[1].animate.set_color(BRANCO), FadeIn(fio, shift=UP * 0.2),
                  run_time=0.4)
        self.ate("menos")
        self.play(Indicate(num_f[1], color=AMARELO, scale_factor=1.3), run_time=min(0.5, self.restante() - 0.05))
        self.completar()
