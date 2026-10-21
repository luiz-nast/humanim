"""[CANTO] A IA errou a espécie deste pinguim por misturar gramas com milímetros.

Já no 1º quadro: pinguim cinza, "?", "50,9 mm", "3.550 g" e o crédito em cinza (abertura()).
Em "errou" sai o balão "IA: Adélia" com o ✗; em "misturar" os dois números acendem em amarelo.
Termina em fim_linha_1(), o 1º quadro da linha 2.
"""
from estilo import *
from comum import *


class Cena(CenaHumanim):
    def construct(self):
        a = abertura()
        self.add(*a.values())

        self.play(Wiggle(a["interrogacao"]), run_time=min(0.6, 0.15 * self.duracao))
        fim = fim_linha_1()
        self.ate("errou")
        ponta = PINGUIM_L1 + [0.35, 1.55, 0]
        self.play(GrowFromPoint(fim["balao"], ponta), run_time=0.45)
        self.ate("pinguim")
        self.play(a["pinguim"].animate(rate_func=there_and_back).scale(1.1), run_time=0.5)
        self.ate("misturar")
        self.play(a["bico"].animate.set_color(AMARELO), a["peso"].animate.set_color(AMARELO), run_time=0.35)
        self.ate("gramas")
        self.play(Indicate(a["peso"], scale_factor=1.15, color=AMARELO), run_time=min(0.5, self.restante()))
        self.ate("milímetros")
        self.play(Indicate(a["bico"], scale_factor=1.15, color=AMARELO), run_time=min(0.5, self.restante()))
        self.remove(*self.mobjects)
        self.add(*fim.values())  # o mesmo estado, com os objetos do comum.py: a linha 2 começa daqui
        self.completar()
