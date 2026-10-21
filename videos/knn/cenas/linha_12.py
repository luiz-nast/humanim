"""[CANTO] Cada medida tem a sua régua: quanto ela costuma variar, o desvio-padrão.

Começa em fim_linha_11(). Em "medida" os nomes das réguas acendem; em "régua" os trechos amarelos e as médias
apagam e, a partir da média de cada régua, acendem em branco "5,45 mm" e "801 g" (quase do mesmo tamanho);
em "costuma" e em "desvio" os dois piscam. Termina em fim_linha_12(). Tudo acima de y −2,07.
"""
from estilo import *
from comum import *
from bloco_4 import *


class Cena(CenaHumanim):
    def construct(self):
        f = fim_linha_11()
        bico, peso, tb, tp, mb, mp = f["bico"], f["peso"], f["tb"], f["tp"], f["mb"], f["mp"]
        self.add(f["knn"], bico.tudo, peso.tudo, tb, tp, mb, mp)

        self.ate("medida")
        self.play(Indicate(bico.nome, color=AMARELO), Indicate(peso.nome, color=AMARELO), run_time=0.6)
        tbw, tpw = trechos_desvio(bico, peso)
        self.ate("régua")
        self.play(FadeOut(VGroup(tb, tp, mb, mp)), Create(tbw[0]), Create(tpw[0]), FadeIn(tbw[1]), FadeIn(tpw[1]),
                  run_time=0.6)
        self.ate("costuma")
        self.play(Indicate(tbw, color=AMARELO, scale_factor=1.12), Indicate(tpw, color=AMARELO, scale_factor=1.12),
                  run_time=0.6)
        self.ate("desvio")
        self.play(Indicate(tbw, color=AMARELO, scale_factor=1.12), Indicate(tpw, color=AMARELO, scale_factor=1.12),
                  run_time=min(0.6, self.restante()))
        b2, p2, tb2, tp2, knn2 = fim_linha_12()
        self.remove(*self.mobjects)
        self.add(knn2, b2.tudo, p2.tudo, tb2, tp2)  # o mesmo estado, com os objetos do comum.py: a linha 13 começa daqui
        self.completar()
