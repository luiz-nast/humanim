"""[CANTO] Ninguém disse pra IA qual erupção é curta ou longa. Ela separou sozinha.

Já no 1º quadro, o gêiser com "Old Faithful" e "Yellowstone, EUA" (abertura()); ele jorra no começo e de novo em
"erupção". Em "curta" vira dois gêiseres iguais, com a barra curta e "curta" à esquerda; em "longa", a barra comprida
e "longa" à direita (mesma escala de minutos). Em "separou" a tracejada desce entre os dois e os rótulos viram "?"
cinza: termina em fim_linha_1(), o 1º quadro da linha 2. Tudo acima do canto (o mais baixo é o "Yellowstone", y −1,5).
"""
from estilo import *
from comum import *
from bloco_1 import *


class Cena(CenaHumanim):
    def construct(self):
        a = abertura()
        self.add(*a.values())
        f = fim_linha_1()
        curta, longa = rotulos_linha_1()

        self.play(jorro(a["geiser"]), run_time=min(0.9, 0.4 * self.momento("erupção")))
        self.ate("erupção")
        self.play(jorro(a["geiser"], 1.14), run_time=min(0.7, 0.8 * (self.momento("curta") - self.time)))

        self.ate("curta")
        self.play(ReplacementTransform(a["geiser"], f["geiser_esq"]), FadeIn(f["geiser_dir"], shift=RIGHT * 1.75),
                  Create(f["barra_esq"]), FadeIn(curta, shift=UP * 0.15), run_time=0.55)
        self.ate("longa")
        self.play(Create(f["barra_dir"]), FadeIn(longa, shift=UP * 0.15), run_time=0.5)

        self.ate("separou")
        self.play(Create(f["tracejada"]), FadeTransform(curta, f["rotulo_esq"]), FadeTransform(longa, f["rotulo_dir"]),
                  run_time=min(0.6, self.restante()))
        self.completar()
