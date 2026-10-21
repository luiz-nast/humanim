"""[ANIM] Dividindo pelo desvio: a Barbicha fica a 0,14, e a Adélia, a 1,60.

As réguas da 12 saem e voltam os cartões (Barbicha 0,4 mm / 100 g, Adélia 8,7 mm / 0 g), com "antes 100,0 > 8,7"
na faixa. Em "Dividindo", as duas divisões da Barbicha com o desvio em amarelo; em "desvio", o rótulo
"desvio-padrão"; em "Barbicha", d = √(0,07² + 0,12²) = √0,0193 = 0,14; em "Adélia", d = 8,7 ÷ 5,45 = 1,60;
no fim o veredito vira "agora 0,14 < 1,60". Termina em fim_linha_13(), acima do canto.
"""
from estilo import *
from comum import *
from bloco_5 import *


class Cena(CenaHumanim):
    def construct(self):
        b, p, tb, tp, knn = fim_linha_12()
        self.add(knn, b.tudo, p.tudo, tb, tp)

        cb, ca = cartoes_13()
        c = contas_13()
        v0 = veredito()
        self.play(FadeOut(VGroup(b.tudo, p.tudo, tb, tp), shift=DOWN * 0.3),
                  FadeIn(cb, shift=DOWN * 0.3), FadeIn(ca, shift=DOWN * 0.3), FadeIn(v0, shift=UP * 0.15),
                  run_time=0.12 * self.duracao)
        self.ate("Dividindo")
        self.play(Write(c.r1), Write(c.r2), run_time=0.13 * self.duracao)
        self.ate("desvio")
        self.play(FadeIn(c.dp, shift=LEFT * 0.15), Indicate(c.r1[2], color=AMARELO), Indicate(c.r2[2], color=AMARELO),
                  run_time=0.1 * self.duracao)
        self.ate("Barbicha")
        self.play(Write(c.r3), run_time=0.11 * self.duracao)
        self.play(Write(c.r4), Indicate(cb.caixa, color=ROXO, scale_factor=1.04), run_time=0.11 * self.duracao)
        self.ate("Adélia")
        self.play(Write(c.r5), Indicate(ca.caixa, color=LARANJA, scale_factor=1.04), run_time=0.12 * self.duracao)
        v1 = veredito(agora=True)
        self.play(Transform(v0[0], v1[0]), Transform(v0[1], v1[1]), run_time=min(0.5, self.restante()))

        fim = fim_linha_13()
        self.remove(*self.mobjects)
        self.add(*fim)  # o mesmo estado, com os objetos do bloco_5.py: a linha 14 começa daqui
        self.completar()
