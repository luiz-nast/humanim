"""[CANTO] A distância é a raiz da diferença de bico ao quadrado, mais a de peso ao quadrado.

Começa no último quadro da linha 3 (fim_linha_3). No começo o título sai e entra o rótulo "KNN · k = 5"; as 5 linhas
amarelas saem (os anéis ficam). Em "distância" a linha até um Gentoo no alto à direita vira a hipotenusa do triângulo
(Δbico deitado, Δpeso em pé). Em "raiz" entra "d = √(   +   )"; em "bico", Δbico² vai para a 1ª vaga; em "peso",
Δpeso² para a 2ª. Termina em fim_linha_5().
"""
from estilo import *
from comum import *
from bloco_2 import *


class Cena(CenaHumanim):
    def construct(self):
        pl, tit, amarelas, an, fx = fim_linha_3()
        self.add(pl.tudo, tit, amarelas, an, fx)

        fim = fim_linha_5()
        knn, tri, f = fim["knn"], fim["tri"], fim["formula"]
        gentoo = pl.pontos[GENTOO]

        self.play(FadeOut(tit, shift=UP * 0.2), FadeOut(amarelas), run_time=0.2)
        self.ate("distância")
        self.play(FadeIn(knn), Create(tri.hip), Indicate(gentoo, color=AZUL, scale_factor=2.2),
                  FadeOut(pl.interrogacao), run_time=0.45)
        self.play(Create(tri.deitado), Create(tri.em_pe), run_time=0.4)
        self.play(FadeIn(tri.reto), FadeIn(tri.lb), FadeIn(tri.lp), run_time=0.3)

        self.ate("raiz")
        self.play(FadeIn(VGroup(f[0], f[2], f[4]), shift=DOWN * 0.15), run_time=0.35)
        self.ate("bico")
        self.play(ReplacementTransform(tri.lb[1].copy(), f[1]), Indicate(tri.deitado, color=AMARELO),
                  run_time=min(0.6, self.restante()))
        self.ate("peso")
        self.play(ReplacementTransform(tri.lp[1].copy(), f[3]), Indicate(tri.em_pe, color=AMARELO),
                  run_time=min(0.6, self.restante()))
        self.play(Indicate(tri.hip, color=AMARELO, scale_factor=1.05), Indicate(f[0][0], color=AMARELO),
                  run_time=min(0.6, self.restante()))

        self.remove(*self.mobjects)
        self.add(fim["plano"].tudo, an, fx, knn, tri, f)  # o mesmo estado com os objetos de fim_linha_5: a linha 6 começa daqui
        self.completar()
