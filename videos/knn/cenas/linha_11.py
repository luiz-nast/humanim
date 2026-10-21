"""[ANIM] Só que 100 gramas é pouco pra um pinguim, e 8,7 milímetros é muito.

Duas réguas do mesmo comprimento (bico 32–60 mm, peso 2.700–6.300 g) com os 342 em cima. Em "100" acende o
trecho fininho de 100 g; em "pinguim", as médias de peso da Adélia e da Barbicha (3.701 e 3.733, quase no mesmo lugar);
em "8,7", o trecho largo de 8,7 mm; em "milímetros", as médias de bico (38,8 e 48,8, bem separadas); em "muito" o trecho pisca. Termina em fim_linha_11().
"""
from estilo import *
from comum import *
from bloco_4 import *


class Cena(CenaHumanim):
    def construct(self):
        f = fim_linha_11()
        bico, peso, tb, tp, mb, mp = f["bico"], f["peso"], f["tb"], f["tp"], f["mb"], f["mp"]
        self.add(f["knn"], bico.eixo, bico.nome, peso.eixo, peso.nome)

        self.play(*(LaggedStart(*(FadeIn(d, shift=DOWN * 0.25) for d in r.grupo_pontos), lag_ratio=0.004)
                    for r in (bico, peso)), run_time=0.18 * self.duracao)
        self.ate("100")
        self.play(Create(tp[0]), FadeIn(tp[1], shift=UP * 0.1), run_time=0.45)
        self.ate("pouco")
        self.play(Indicate(tp, color=AMARELO, scale_factor=1.25), run_time=0.5)
        self.ate("pinguim")
        self.play(LaggedStart(FadeIn(mp[0]), FadeIn(mp[1]), lag_ratio=0.4), run_time=0.5)
        self.ate("8,7")
        self.play(Create(tb[0]), FadeIn(tb[1], shift=UP * 0.1), run_time=0.45)
        self.ate("milímetros")
        self.play(LaggedStart(FadeIn(mb[0]), FadeIn(mb[1]), lag_ratio=0.4), run_time=0.5)
        self.ate("muito")
        self.play(Indicate(tb, color=AMARELO, scale_factor=1.15), run_time=min(0.6, self.restante()))
        self.completar()
