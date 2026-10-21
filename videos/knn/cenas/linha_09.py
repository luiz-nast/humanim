"""[CANTO] Já a Adélia do mesmo peso: sobra o bico, 8,7. Menos que 100.

Começa no fim da linha 8. A conta da Barbicha sai e o cartão dela encolhe para a faixa à direita do canto,
"d = 100,0"; entra a Adélia vizinha (laranja, 42,2 mm, 3.550 g). Termo a termo: 3.550 − 3.550 = 0,
50,9 − 42,2 = 8,7, d = √(8,7² + 0²) = √(75,69 + 0) = √75,69 = 8,7. Em "Menos", "8,7 < 100,0" na faixa e a
Adélia acesa em amarelo. Nada no canto (x < −0,44 e y < −2,37).
"""
from estilo import *
from comum import *
from bloco_3 import *


class Cena(CenaHumanim):
    def construct(self):
        f = fim_linha_8()
        m, b, velhas = f["m"], f["b"], f["filas"]
        self.add(f["knn"], m, b, *velhas)

        b.bicho.set_z_index(3)  # o FadeOut da caixa (fundo preto) vem por cima no 1º quadro
        a = cartao_adelia()
        mini = mini_barbicha()
        r1, r2, r3, r4, r5 = filas_9()
        comp = comparacao()

        self.play(FadeOut(VGroup(*velhas[:4], *velhas[4][:4])),
                  ReplacementTransform(velhas[4][4], mini[1][1]), FadeIn(mini[1][0]),
                  ReplacementTransform(b.bicho, mini[0]),
                  FadeOut(VGroup(b.caixa, b.l1, b.l2), target_position=mini[0].get_center(), scale=0.25),
                  run_time=0.55)
        self.play(FadeIn(a, shift=LEFT * 0.4), run_time=0.4)

        self.ate("mesmo peso")
        self.play(Write(r2), Indicate(m.l2, color=AMARELO), Indicate(a.l2, color=AMARELO), run_time=0.7)
        self.ate("bico")
        self.play(Write(r1), Indicate(m.l1, color=AMARELO), Indicate(a.l1, color=AMARELO), run_time=0.6)
        self.ate("8 7")
        self.play(LaggedStart(Write(r3), Write(r4), Write(r5), lag_ratio=0.55),
                  run_time=max(0.6, self.momento("Menos") - self.time - 0.05))

        self.ate("Menos")
        self.play(a.caixa.animate.set_stroke(AMARELO), TransformFromCopy(r5[4], comp[0]), Write(comp[1]),
                  TransformFromCopy(mini[1][1], comp[2]), run_time=min(0.5, self.restante()))
        self.ate("100")
        if self.restante() > 0.25:
            self.play(Indicate(comp[2], color=AMARELO), run_time=min(0.45, self.restante()))
        self.completar()
