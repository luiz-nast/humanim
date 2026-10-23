"""[ANIM] A menor soma cai com mais grupos, até zero. O cotovelo é regra de bolso, não prova.

Depois de uma [CARA] (linha 15): começa do zero com os eixos do Cotovelo() do comum.py (k em pé, de 1 a 6; soma
deitada, em min²). Em "cai", os 6 pontos entram um a um, cada um com a sua soma e o trecho que o liga ao anterior. Em
"zero", embaixo, pequeno e cinza, "272 grupos: soma 0" (cada erupção sozinha no seu grupo). Em "cotovelo", "− 41.538"
e "− 3.713" ao lado dos dois primeiros trechos, anel amarelo no k = 2 e "cotovelo". Em "bolso", o anel fica tracejado
e entra "não é prova". A linha 17 é [CARA]. Números: dados/resultados.json (COTOVELO, quedas conferidas no comum.py).
"""
from estilo import *
from comum import *


class Cena(CenaHumanim):
    def construct(self):
        c = Cotovelo()
        cot, prova = c.nota
        # Ajustes só desta cena (o comum.py fica como está): o "(min²)" do nome do eixo descia a 4,79 abaixo do
        # centro, fora da zona segura (4,7): tudo sobe 0,15. "cotovelo" sobe 0,1 para não encostar no 1º trecho, e
        # "não é prova" sai de cima do traço do k = 1 (andava colado nele, como se fosse da fila do 1).
        VGroup(c.eixos, *c.pontos, *c.trechos, *c.valores, *c.quedas, c.anel, c.nota).shift(UP * 0.15)
        cot.shift(UP * 0.1)
        prova.move_to([cot.get_left()[0] + 0.32 + prova.width / 2, cot.get_top()[1] + 0.42 + prova.height / 2, 0])

        # os eixos, antes da fala chegar em "cai"
        linhas = VGroup(c.eixos[0], c.eixos[1], c.eixos[2])
        textos = VGroup(*c.eixos[3:])
        self.play(Create(linhas), FadeIn(textos), run_time=min(0.7, 0.8 * self.momento("cai")))

        # "cai": um ponto por k, com a soma dele e o trecho desde o anterior
        passos = [AnimationGroup(GrowFromCenter(c.pontos[0]), FadeIn(c.valores[0], shift=LEFT * 0.15))]
        for j in range(1, 6):
            passos.append(AnimationGroup(Create(c.trechos[j - 1]), GrowFromCenter(c.pontos[j]),
                                         FadeIn(c.valores[j], shift=LEFT * 0.15)))
        self.ate("cai")
        janela = self.momento("zero") - self.momento("cai")
        self.play(LaggedStart(*passos, lag_ratio=0.55), run_time=max(0.9, 0.9 * janela))

        # "zero": com 272 grupos (uma erupção em cada), a soma é 0
        zero = Text(f"{N} grupos: soma 0", font_size=PQ, color=CINZA)
        zero.move_to([DIR - zero.width / 2, (c.pontos[4].get_y() + c.pontos[5].get_y()) / 2, 0])
        self.ate("zero")
        self.play(FadeIn(zero, shift=UP * 0.12), run_time=0.4)

        # "cotovelo": as duas quedas, depois o anel e o nome
        self.ate("cotovelo")
        self.play(FadeIn(c.quedas[0], scale=1.15), Indicate(c.trechos[0], color=AMARELO, scale_factor=1), run_time=0.4)
        self.play(FadeIn(c.quedas[1], scale=1.15), Indicate(c.trechos[1], color=AMARELO, scale_factor=1), run_time=0.4)
        self.play(Create(c.anel), Write(cot), run_time=0.5)

        # "bolso": o anel fica tracejado (é palpite) e entra "não é prova"
        tracejado = DashedVMobject(c.anel.copy(), num_dashes=14, dashed_ratio=0.55)
        self.ate("bolso")
        self.play(FadeOut(c.anel), FadeIn(tracejado), FadeIn(prova, shift=DOWN * 0.1),
                  run_time=min(0.5, self.restante()))
        self.completar()
