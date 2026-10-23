"""[ANIM] Toda troca baixa a soma, e os jeitos são finitos: ele sempre para.

Depois de uma [CARA]: começa com os eixos da Escada() e o 1º degrau (37.347). Em "baixa", os 8 degraus seguintes
descem um a um (um por regra), com 27.203, 12.821, 9.057 e 8.902 no fim de cada rodada. Em "finitos", cresce a
moldura "2²⁷¹ − 1 jeitos" e entra "82 algarismos". Em "sempre", o último degrau (8.902 de novo) fica amarelo com
"rodada 5: parou". Tudo acima do canto: a linha 14 ([CANTO]) começa neste último quadro (fim_linha_13).
"""
from estilo import *
from comum import *
from bloco_6 import *


class Cena(CenaHumanim):
    def construct(self):
        a = fim_linha_13()
        esc = a["escada"]
        esc.degraus[8].set_color(BRANCO)  # acende só em "sempre"
        self.add(esc.eixos)
        self.play(Create(esc.degraus[0], rate_func=linear), FadeIn(esc.rotulos[0], shift=DOWN * 0.1), run_time=0.45)

        self.ate("baixa")
        passos = []
        for k in range(1, 9):  # espelho (a queda) e depois o degrau, como uma caneta que só desce
            deg = [Create(esc.degraus[k], rate_func=linear)]
            if k in esc.rotulos:
                deg.append(FadeIn(esc.rotulos[k], shift=DOWN * 0.1))
            passos.append(AnimationGroup(Create(esc.espelhos[k - 1], rate_func=linear), AnimationGroup(*deg),
                                         lag_ratio=1))
        self.play(AnimationGroup(*passos, lag_ratio=1),
                  run_time=max(1.0, self.momento("finitos") - 0.05 - self.time))

        self.ate("finitos")
        self.play(GrowFromCenter(a["jeitos"]), run_time=0.45)
        self.play(FadeIn(a["algarismos"], shift=UP * 0.1), run_time=0.35)

        self.ate("sempre")
        self.play(esc.degraus[8].animate.set_color(AMARELO), FadeIn(esc.parou, scale=0.85),
                  run_time=min(0.45, self.restante()))
        self.completar()
