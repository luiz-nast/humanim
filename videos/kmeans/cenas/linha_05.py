"""[ANIM] Regra 1: cada erupção vai pro centro mais perto. Sai errado: 91 longas caem com as curtas.

Começa no fim da linha 4 (fim_linha_4: brancas, "k = 2", losangos e "centro"). "1. mais perto" entra no alto e os
"centro" saem. Em "erupção", a erupção 13 do R (4,2; 78) acende e se liga aos dois losangos: "7,0 min" (azul) e
"13,0 min" (laranja), com as contas embaixo do plano; em "centro" o 7,0 acende; em "perto" ela fica azul, cada erupção
pega a cor da rodada 1, a fronteira calculada (81 min) aparece com "191" e "81 erupções". Em "errado" saem a erupção e
as contas e entram os 91 anéis; em "91" a conta de armar 191 − 91 começa na faixa à direita do canto e, em "longas",
fecha em "100 curtas". Termina em fim_linha_5() (bloco_2.py): estado(1, fase=1) + anéis + rótulos e conta, tudo fora
do canto, para a linha 6 ([CANTO]) emendar e apagar anéis e contas.
"""
from estilo import *
from comum import *
from bloco_2 import *


class Cena(CenaHumanim):
    def construct(self):
        f = fim_linha_5()
        pl, cs, k = f["plano"], f["centros"], f["k"]
        pl.grupo_pontos.set_color(NEUTRO)  # ainda sem grupo: o 1º quadro é o último da linha 4
        rot = rotulos_centro(pl)
        self.add(rot, pl.tudo, cs, k)  # rot embaixo: na linha 4 as longas piscaram e ficaram por cima dele

        self.play(Write(f["regra"]), FadeOut(rot), run_time=0.6)

        ex = exemplo(pl)
        self.ate("erupção")
        self.play(FadeIn(ex["destaque"], scale=1.8), run_time=0.3)
        self.play(*(Create(l) for l in ex["linhas"]), *(FadeIn(r) for r in ex["rotulos"]),
                  LaggedStart(*(FadeIn(c, shift=UP * 0.1) for c in ex["contas"]), lag_ratio=0.35), run_time=0.7)

        self.ate("centro")
        self.play(Indicate(ex["contas"][0][2], color=AMARELO), Indicate(ex["rotulos"][0][1], color=AMARELO),
                  run_time=0.5)

        self.ate("perto")
        self.play(ex["destaque"][0].animate.set_color(COR_G[0]), ex["linhas"][1].animate.set_stroke(opacity=0.3),
                  FadeOut(ex["rotulos"][1]), run_time=0.35)
        grupos = [VGroup(*(pl.pontos[i] for i in range(N) if GRUPOS[1][i] == g)) for g in (0, 1)]
        self.play(*(grupos[g].animate.set_color(COR_G[g]) for g in (0, 1)), Create(f["fronteira"]),
                  FadeIn(f["grupos"]), run_time=0.6)

        self.ate("errado")
        sai = VGroup(ex["destaque"], *ex["linhas"], ex["rotulos"][0], *ex["contas"])
        self.play(FadeOut(sai), LaggedStart(*(Create(a) for a in f["aneis"]), lag_ratio=0.01), run_time=0.7)

        n1, m91, traco, res = f["conta"]
        self.ate("91")
        self.play(FadeIn(n1, shift=UP * 0.1), FadeIn(m91, shift=UP * 0.1),
                  f["aneis"].animate(rate_func=there_and_back).set_stroke(width=5), run_time=0.5)
        self.ate("longas")
        self.play(Create(traco), FadeIn(res, shift=UP * 0.1), run_time=min(0.5, self.restante()))
        self.ate("curtas")
        self.play(Indicate(res, color=AMARELO, scale_factor=1.1), run_time=min(0.5, self.restante()))
        self.completar()
