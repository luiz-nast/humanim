"""[ANIM] Em 272 erupções, curta anda com espera curta; longa, com espera longa.

Começa em fim_linha_1() (o último quadro da linha 1). Os gêiseres saem e nasce o plano duração × espera, com a
definição da espera, pequena e cinza, no alto à esquerda (bloco_1: numa fila não cabe). Em "272" caem as 272
erupções, brancas, com o contador "272 erupções" no alto à direita, e o crédito dos dados embaixo. Em "curta", o halo
cinza contorna o miolo da nuvem de baixo, com a barra e "curta" no eixo deitado; em "espera curta", a barra no eixo em
pé e "espera curta". O mesmo para a longa. Os pontos continuam brancos: ninguém tem grupo ainda. A linha 3 é [CARA]:
o fim não precisa emendar.
"""
from estilo import *
from comum import *
from bloco_1 import *


class Cena(CenaHumanim):
    def construct(self):
        a = fim_linha_1()
        self.add(*a.values())

        pl = plano(0)
        self.play(LaggedStart(FadeOut(VGroup(*a.values()), shift=UP * 0.3), Create(pl.eixos),
                              FadeIn(definicao_espera()), lag_ratio=0.35), run_time=0.11 * self.duracao)

        self.ate("272")
        cont = contador_empilhado(0)
        self.play(LaggedStart(*(FadeIn(p, shift=DOWN * 0.4) for p in pl.grupo_pontos), lag_ratio=0.006),
                  ChangeDecimalToValue(cont.n, N), FadeIn(cont.nome), run_time=0.27 * self.duracao)
        self.play(FadeIn(credito(), shift=UP * 0.1), run_time=0.06 * self.duracao)

        for g, nome in ((0, "curta"), (1, "longa")):
            bx, rx, by, ry = marcas_nuvem(pl, g)
            h = halo(pl, g).set_stroke(CLARO, 3)
            self.ate(nome)
            self.play(FadeIn(h), Create(bx), FadeIn(rx, shift=UP * 0.15), run_time=0.45)
            self.ate("espera", vez=g + 1)
            self.play(Create(by), FadeIn(ry, shift=RIGHT * 0.15 * (1 if g == 0 else -1)),
                      run_time=min(0.45, self.restante()))
        self.completar()
