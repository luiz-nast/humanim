"""[ANIM] Pra Barbicha colada nele: 0,4 milímetro e 100 gramas. Ao quadrado, 0,16 e 10 mil. Com a raiz, dá 100.

No alto, o cartão do misterioso (roxo, com "?") e o da Barbicha colada nele. Embaixo, termo a termo:
as duas diferenças, d = √(0,4² + 100²), = √(0,16 + 10.000) com o 10.000 grande e amarelo, = √10.000,16 = 100,0.
Tudo acima de y −2,07 (a linha 9 é [CANTO] e começa daqui: fim_linha_8()).
"""
from estilo import *
from comum import *
from bloco_3 import *


class Cena(CenaHumanim):
    def construct(self):
        knn = rotulo_knn()
        m, b = cartoes()
        r1, r2, r3, r4, r5 = filas_8()
        self.add(knn, m)

        self.ate("Barbicha")
        self.play(FadeIn(b, shift=LEFT * 0.4), run_time=0.45)
        self.ate("colada")
        self.play(Indicate(m.bicho, color=AMARELO, scale_factor=1.15),
                  Indicate(b.bicho, color=AMARELO, scale_factor=1.15), run_time=0.55)

        self.ate("0 4")
        self.play(Write(r1), Indicate(m.l1, color=AMARELO), Indicate(b.l1, color=AMARELO), run_time=0.7)
        self.ate("milímetro")
        self.play(Indicate(r1[4], color=AMARELO, scale_factor=1.35), run_time=0.6)

        self.ate("100")
        self.play(Write(r2), Indicate(m.l2, color=AMARELO), Indicate(b.l2, color=AMARELO), run_time=0.7)

        self.ate("Ao quadrado")
        self.play(Write(VGroup(r3[0], r3[1], r3[2], r3[4], r3[6])), TransformFromCopy(r1[4], r3[3]),
                  TransformFromCopy(r2[4], r3[5]), run_time=0.8)

        self.ate("0 16")
        self.play(Write(VGroup(r4[0], r4[1], r4[3], r4[5])), TransformFromCopy(r3[3], r4[2]), run_time=0.6)
        self.ate("10 mil")
        self.play(TransformFromCopy(r3[5], r4[4]), run_time=0.6)

        self.ate("Com a raiz")
        self.play(Write(VGroup(r5[0], r5[1])), TransformFromCopy(VGroup(r4[2], r4[4]), r5[2]), run_time=0.6)
        self.ate("dá 100")
        self.play(Write(VGroup(r5[3], r5[4])), run_time=min(0.45, self.restante()))

        fim = fim_linha_8()  # o mesmo estado, com os objetos do bloco_3: a linha 9 começa daqui
        self.remove(*self.mobjects)
        self.add(fim["knn"], fim["m"], fim["b"], *fim["filas"])
        self.completar()
