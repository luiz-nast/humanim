"""[CANTO] Regra 2: cada centro vai pra duração média e espera média do grupo.

Começa onde a linha 5 termina (fim_linha_5 do bloco_2.py: rodada 1 depois da regra 1). Os anéis dos 91, os "191"/"81"
e a conta 191 − 91 saem e "2. média" entra embaixo do "1. mais perto"; em "centro" os losangos piscam e o "centro" da
linha 4 volta ao lado de cada um. Em "duração" os losangos deslizam na horizontal até a duração média do grupo (3,1 e 4,4 min),
e aparece "(3,1;" / "(4,4;" (o "centro" azul vai para a direita do losango; o laranja dá lugar às coordenadas, que
no alto só cabem acima da fronteira); em "espera", na vertical até a espera média (64,9 e 85,1 min), completando as
coordenadas, e o "centro" azul ganha "(centroide)". A fronteira é recalculada (em minutos) a cada quadro, onde os centros
estiverem: termina na fronteira(pl, 1) do comum.py, a que a regra 1 da rodada 2 usa. Tudo acima do canto.
"""
from estilo import *
from comum import *
from bloco_3 import *
import bloco_2 as b2


class Cena(CenaHumanim):
    def construct(self):
        a = fim_linha_5()
        adicionar(self, a)  # emenda com o fim da linha 5
        pl, los = a["plano"], a["centros"]
        fim = fim_linha_6()

        r2 = fim["regra2"]
        self.play(FadeOut(a["aneis"]), FadeOut(a["grupos"]), FadeOut(a["conta"]), FadeIn(r2, shift=UP * 0.2),
                  run_time=0.5)

        rot = b2.rotulos_centro(pl)  # o "centro" da linha 4, no mesmo lugar
        self.ate("centro")
        self.play(*(Indicate(l, scale_factor=1.35, color=AMARELO) for l in los), FadeIn(rot, shift=UP * 0.1),
                  run_time=0.6)

        # a fronteira passa a ser a dos losangos onde eles estiverem (igual à da linha 5 neste quadro)
        viva = fronteira_viva(pl, los)
        self.remove(a["fronteira"])
        self.add(viva)

        cs = fim["coords"]
        self.ate("duração")
        self.play(*(los[g].animate.move_to(pl.p(CENTROS[1][g][0], CENTROS[0][g][1])) for g in (0, 1)),
                  rot[0].animate.move_to(fim["centro"]), FadeOut(rot[1]), run_time=0.6)
        self.play(*(FadeIn(VGroup(*cs[g][:3]), shift=UP * 0.1) for g in (0, 1)), run_time=0.3)

        self.ate("espera")
        self.play(*(los[g].animate.move_to(pl.p(*CENTROS[1][g])) for g in (0, 1)), run_time=0.6)
        self.play(*(FadeIn(VGroup(*cs[g][3:]), shift=UP * 0.1) for g in (0, 1)),
                  FadeIn(fim["centroide"], shift=DOWN * 0.1), run_time=min(0.35, self.restante()))

        # parado, a fronteira viva é a fronteira(pl, 1) do comum.py: troca pela do estado, para a linha 7 emendar
        self.remove(viva)
        self.add(fim["fronteira"])
        self.completar()
