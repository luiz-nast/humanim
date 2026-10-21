"""[CANTO] Ela mede a distância dele até cada um e pega os 5 mais perto.

Começa em fim_linha_2(). Em "distância" a legenda sai, linhas finas e cinza vão do ponto branco até os 341
(da mais perta à mais longe), com o contador até 341. Em "5" as cinza somem e ficam 5 amarelas até as
5 Adélias de 3.550 g (VIZ_CRU), à esquerda; em "perto" elas ganham o anel amarelo.
"""
from estilo import *
from comum import *


class Cena(CenaHumanim):
    def construct(self):
        pl, tit, leg = fim_linha_2()
        self.add(pl.tudo, tit, leg)

        o = pl.misterioso.get_center()
        ordem = sorted(pl.pontos, key=lambda l: (PONTOS[l][1] - M_BICO) ** 2 + (PONTOS[l][2] - M_PESO) ** 2)
        cinza = VGroup(*(Line(o, pl.pos(l), stroke_width=1.5, color=CINZA, stroke_opacity=0.5) for l in ordem))
        cinza.set_z_index(-1)
        cont = contador(0)
        nome = Text("distâncias", font_size=PQ, color=CINZA).move_to(FAIXA_CENTRO + [0, -0.6, 0])

        self.play(Indicate(pl.misterioso, scale_factor=1.6, color=BRANCO), run_time=min(0.5, self.momento("distância")))
        self.ate("distância")
        self.play(FadeOut(leg), FadeIn(cont), FadeIn(nome), run_time=0.3)
        t_lin = max(0.6, self.momento("5") - self.momento("distância") - 0.45)
        self.play(LaggedStart(*(Create(c) for c in cinza), lag_ratio=0.01), ChangeDecimalToValue(cont, 341),
                  run_time=t_lin)

        amarelas = linhas_ate(pl, VIZ_CRU).set_z_index(1)
        cinco = contador(5).set_color(AMARELO)
        nome5 = Text("mais perto", font_size=PQ, color=AMARELO).move_to(nome)
        self.ate("5")
        self.play(FadeOut(cinza), Create(amarelas), FadeTransform(cont, cinco),
                  FadeTransform(nome, nome5), run_time=0.5)
        an = aneis(pl, VIZ_CRU).set_z_index(1)
        self.ate("perto")
        self.play(Create(an), run_time=min(0.4, self.restante()))
        self.play(Indicate(VGroup(*(pl.pontos[l] for l in VIZ_CRU)), color=AMARELO, scale_factor=1.3),
                  run_time=min(0.6, self.restante()))
        self.completar()
