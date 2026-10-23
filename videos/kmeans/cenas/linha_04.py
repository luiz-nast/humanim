"""[CANTO] Eu dei 2 centros, um por grupo, ruins de propósito: duas erupções longas.

Depois da linha 3 ([CARA]) o plano volta com as 272 erupções brancas, acima do canto. "k = 2" entra no alto (fica até
o fim da 7). Em "centros", as erupções 74 e 203 do R viram os losangos azul (4,0; 71) e laranja (4,1; 91), com
"centro" ao lado de cada um; em "grupo" o "k = 2" pisca (um centro por grupo); em "ruins" os losangos tremem; em
"duas" eles pulsam e a nuvem de cima (as longas) pisca: os dois começam nela. Termina em fim_linha_4() (bloco_2.py),
o 1º quadro da linha 5.
"""
from estilo import *
from comum import *
from bloco_2 import *


class Cena(CenaHumanim):
    def construct(self):
        f = fim_linha_4()
        pl, cs, k, rot = f["plano"], f["centros"], f["k"], f["rotulos"]
        self.add(pl.tudo)

        self.play(FadeIn(k, scale=0.8), run_time=0.4)

        self.ate("centros")
        self.play(*(ReplacementTransform(pl.pontos[i].copy(), c) for i, c in zip(INICIAIS, cs)),
                  FadeIn(rot, shift=UP * 0.1), run_time=0.6)

        self.ate("grupo")
        # só o texto pisca: a moldura já encosta no topo da zona segura
        self.play(Indicate(k[1], color=AMARELO, scale_factor=1.2), run_time=0.5)

        self.ate("ruins")
        self.play(*(Wiggle(c, scale_value=1.25, rotation_angle=0.06 * TAU) for c in cs), run_time=0.7)

        self.ate("duas")
        longas = VGroup(*(pl.pontos[i] for i in range(N) if GRUPOS[5][i] == 1))
        self.play(*(ScaleInPlace(c, 1.4, rate_func=there_and_back) for c in cs),
                  Indicate(longas, color=AMARELO, scale_factor=1.0), run_time=min(0.8, self.restante()))
        self.completar()
