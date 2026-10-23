"""[CANTO] Cada erupção paga a distância ao seu centro, ao quadrado. O k-means quer a menor soma dos quadrados.

Depois do [CARA] da linha 8: abre no plano final (rodada 5, azul e laranja, losangos nas médias). Em "erupção", anel
amarelo na erupção 69 (2,1 min; 65 min), logo acima do losango azul. Em "distância", a linha amarela dela até o centro
(quase em pé: a distância é quase toda na espera) e o rótulo "distância". Em "centro", o losango azul pulsa. Em
"quadrado", o rótulo vira "distância²", saem as linhas cinza das 272 erupções até o seu centro e monta no alto
"3.456 + 5.446 = 8.902" (o 3.456 com o losango azul, o 5.446 com o laranja). Em "menor", "soma dos quadrados (min²)"
e a setinha amarela para baixo; em "quadrados", o 8.902 acende. Tudo acima do canto.
"""
from estilo import *
from comum import *
from bloco_4 import *


class Cena(CenaHumanim):
    def construct(self):
        pl = plano(5)
        cs = centros(pl, 5)
        self.add(pl.eixos, *pl.pontos.values(), cs)

        # "Cada erupção": a erupção 69, logo acima do losango azul
        an = anel(pl)
        self.ate("erupção")
        self.play(Create(an), Indicate(pl.pontos[EXEMPLO], scale_factor=1.8, color=AMARELO), run_time=0.45)

        # "paga a distância": a linha amarela até o centro (calculada) e o rótulo
        reg, rot = regua(pl), rotulo_distancia()
        self.ate("distância")
        self.play(Create(reg), FadeIn(rot, shift=DOWN * 0.12), run_time=0.45)

        # "ao seu centro"
        self.ate("centro")
        self.play(Indicate(cs[0], scale_factor=1.4, color=AZUL), run_time=0.45)

        # "ao quadrado": distância², e cada uma das 272 paga a sua (linhas cinza até o seu centro)
        lin = linhas_ate(pl, 5)
        self.ate("quadrado")
        self.play(Transform(rot, rotulo_distancia(True)), FadeOut(an), Create(lin, lag_ratio=0.004), run_time=0.6)

        # a soma de cada grupo: 3.456 (azul) + 5.446 (laranja) = 8.902
        soma = conta_soma()
        self.play(FadeIn(soma[0], shift=DOWN * 0.12), Indicate(cs[0], scale_factor=1.35, color=AZUL), run_time=0.35)
        self.play(FadeIn(soma[1:3], shift=DOWN * 0.12), Indicate(cs[1], scale_factor=1.35, color=LARANJA),
                  run_time=0.35)
        self.play(FadeIn(soma[3:], shift=DOWN * 0.12), run_time=0.3)

        # "quer a menor soma dos quadrados"
        nome, seta = nome_soma(), setinha()
        self.ate("menor")
        self.play(FadeIn(nome, shift=DOWN * 0.1), GrowArrow(seta), run_time=0.45)
        self.ate("quadrados")
        self.play(Indicate(soma[4], scale_factor=1.25, color=AMARELO), Indicate(seta, scale_factor=1.2),
                  run_time=min(0.45, self.restante()))
        self.completar()
