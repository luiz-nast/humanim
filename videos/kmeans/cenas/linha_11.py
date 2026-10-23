"""[CANTO] Pra qualquer lado: 100 erupções vezes os minutos ao quadrado. O fundo é a média.

Começa no fim da linha 10. As contas encolhem para o alto, o zoom sai e nasce embaixo delas a curva em U (a soma das
curtas calculada com o centro d min fora da média, de −2 a 2), eixo em pé de 3.400 a 3.900 com zigue-zague no pé, os
valores 3.456, 3.556 e 3.856 no eixo com guias até os pontos. Em "lado", os pontos −1 e 1 piscam juntos; em
"erupções", "3.456 + 100 × d²" com "erupções" cinza sob o 100; em "minutos", o "d" e o eixo deitado; em "quadrado", o
d² acende; em "fundo", o fundo do U acende com "média". Tudo acima do canto.
"""
from estilo import *
from comum import *
from bloco_5 import *


class Cena(CenaHumanim):
    def construct(self):
        f = fim_linha_10()
        self.add(*f.values())  # emenda com o fim da linha 10

        cv = Curva()
        a2, b2, c2 = contas(alto=True)
        c2[3].set_color(AMARELO)
        zoom_sai = VGroup(*(f[k] for k in ("eixos", "linhas", "pontos", "fantasma", "centro", "regua", "rotulos")))
        self.play(Transform(f["a"], a2), Transform(f["b"], b2), Transform(f["c"], c2), FadeOut(zoom_sai),
                  FadeIn(cv.eixos), run_time=0.35)
        self.play(Create(cv.curva), LaggedStart(*(FadeIn(p, scale=0.4) for p in cv.pontos), lag_ratio=0.15),
                  FadeIn(VGroup(*cv.guias, *cv.valores)), run_time=0.45)

        self.ate("lado")
        self.play(*(Indicate(cv.pontos[k], color=AMARELO, scale_factor=2) for k in (1, 3)), run_time=0.45)
        self.ate("erupções")
        self.play(Write(cv.formula), FadeIn(cv.erupcoes, shift=UP * 0.1), run_time=0.5)
        self.ate("minutos")
        self.play(Indicate(cv.formula[4], color=AMARELO), Indicate(cv.nome_x[0], color=AMARELO, scale_factor=1.3),
                  Indicate(cv.nome_x[2], color=AMARELO, scale_factor=1), run_time=0.5)
        self.ate("quadrado")
        self.play(cv.formula[4].animate.set_color(AMARELO).scale(1.15), run_time=0.35)
        self.ate("fundo")
        self.play(cv.pontos[2].animate.set_color(AMARELO).scale(1.5), cv.valores[0].animate.set_color(AMARELO),
                  FadeIn(cv.media, shift=UP * 0.1), run_time=min(0.5, self.restante()))
        self.completar()
