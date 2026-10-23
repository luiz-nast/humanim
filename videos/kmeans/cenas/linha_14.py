"""[CANTO] Com 2 grupos, todo começo chega aqui. Com 3, só 8 de 100 acham a menor soma.

Começa no último quadro da linha 13 (fim_linha_13). A escada sai e volta o plano final de k = 2, menor, com "k = 2"
no alto. Em "começo", embaixo do plano, "36.840 começos"; em "aqui", ", 1 final" e os dois centros pulsam. Em "3",
"k = 3": o plano vira o pequeno da esquerda (o final de soma 5.189: as longas se dividem, o losango laranja solta o
roxo) e entra o da direita (5.839: as curtas divididas), cada erupção pintada no centro mais perto. Em "8", "8 de
100" amarelo e "28 de 100" cinza. Em "menor", o 5.189 acende. Tudo acima do canto. A linha 15 é [CARA].
"""
from estilo import *
from comum import *
from bloco_6 import *


class Cena(CenaHumanim):
    def construct(self):
        velho = tudo_linha_13(fim_linha_13())
        self.add(velho)  # emenda com o fim da linha 13

        pl2 = plano_k2()
        los2 = centros(pl2, 5)
        k = rotulo_k("k = 2")
        self.play(FadeOut(velho), FadeIn(pl2.tudo), FadeIn(los2), FadeIn(k), run_time=0.6)

        frase = comecos()
        self.ate("começo")
        self.play(FadeIn(frase[0], shift=UP * 0.12), run_time=0.4)
        self.ate("aqui")
        self.play(FadeIn(VGroup(frase[1], frase[2]), shift=UP * 0.12),
                  *(Indicate(l, scale_factor=1.35, color=AMARELO) for l in los2), run_time=0.45)

        esq, dir_ = planos_k3()
        los_e, los_d = centros_k3(esq, MELHOR), centros_k3(dir_, OUTRO)
        soma_e, soma_d = soma_k3(esq, MELHOR), soma_k3(dir_, OUTRO)
        k3 = rotulo_k("k = 3")
        self.ate("3")
        self.play(Transform(k[1], k3[1]),
                  ReplacementTransform(VGroup(*pl2.eixos[:3]), VGroup(*esq.eixos[:3])),
                  FadeOut(VGroup(pl2.numeros, pl2.nome_x, pl2.nome_y)),
                  ReplacementTransform(pl2.grupo_pontos, esq.grupo_pontos),
                  ReplacementTransform(los2[0], los_e[0]), ReplacementTransform(los2[1], los_e[2]),
                  GrowFromPoint(los_e[1], los2[1].get_center()),
                  FadeIn(dir_.tudo), FadeIn(los_d), FadeOut(frase), FadeIn(soma_e), FadeIn(soma_d),
                  run_time=0.55)

        oito, vinte_e_oito = vezes(esq, MELHOR, AMARELO), vezes(dir_, OUTRO, CINZA)
        self.ate("8")
        self.play(FadeIn(oito, scale=0.8), run_time=0.35)
        self.play(FadeIn(vinte_e_oito, scale=0.8), run_time=0.35)

        self.ate("menor")
        self.play(soma_e[1].animate.set_color(AMARELO).scale(1.12, about_edge=LEFT), run_time=min(0.45, self.restante()))
        self.completar()
