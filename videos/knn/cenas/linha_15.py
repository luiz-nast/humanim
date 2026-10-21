"""[ANIM] Testando os 342: sem padronizar, acerta 79%; padronizado, 93%.

O plano em desvios encolhe para o alto à direita (vira a nuvem, sem números) e o resto sai; em "Testando", um
pinguim por vez pisca branco na nuvem com um contador até 342; embaixo, duas barras do zero, "sem padronizar" e
"padronizado", rótulo "acerto". Em "acerta", a da esquerda sobe até 271 ÷ 342 = 79,2%; em "padronizado", a da
direita, verde, até 318 ÷ 342 = 93,0%, e embaixo "Barbichas certas: 30 → 60 de 68"; no rodapé, em cinza,
"13 empates no voto: decide o mais perto". A linha 16 é [CARA]: o fim não precisa emendar.
"""
from estilo import *
from comum import *
from bloco_5 import *

A2 = T["acuracia_2_medidas"]
BASE_Y, ALTURA = -1.1, 2.85  # base das barras e a altura de 100%
X_SEM, X_PAD, LARG = -1.65, 1.85, 1.6


def barra(x, acuracia, cor, conta_tela):
    r = Rectangle(width=LARG, height=ALTURA * acuracia).set_fill(cor, 1).set_stroke(width=0)
    r.move_to([x, BASE_Y + r.height / 2, 0])
    divisao, pct = conta_tela.split(" = ")
    p = Text(pct, font_size=56, color=cor if cor != CINZA else BRANCO).move_to([x, r.get_top()[1] + 0.42, 0])
    d = Text(divisao, font_size=PQ, color=BRANCO).move_to([x, r.get_top()[1] + 1.0, 0])
    return r, VGroup(p, d)


class Cena(CenaHumanim):
    def construct(self):
        knn, pz, f, pad, linhas, an, pl, ok = fim_linha_14()
        self.add(knn, pz.eixos, pz.grupo_pontos, pz.misterioso, f, pad, linhas, an, pl, ok)

        # o plano encolhe para o alto à direita: só a nuvem (eixos, marcas e pontos), sem números nem nomes
        c, alvo, s = np.array([0.525, 1.675, 0]), np.array([2.0, 4.05, 0]), 2.2 / 3.85
        nuvem = VGroup(pz.eixos[0], pz.eixos[1], pz.eixos[2], pz.grupo_pontos, pz.misterioso)
        linhas_csv = sorted(PONTOS)
        posicoes = [(pz.pos(l) - c) * s + alvo for l in linhas_csv]

        cont = Integer(0, font_size=96, color=BRANCO).move_to([-1.6, 3.55, 0])
        testados = Text("testados", font_size=PQ, color=CINZA).move_to([-1.6, 2.72, 0])
        base = Line([-2.75, BASE_Y, 0], [2.95, BASE_Y, 0], stroke_width=EIXO, color=CINZA)
        # "sem padronizar" e "padronizado" numa fila só se encostam: o da esquerda vai em duas
        sem = VGroup(Text("sem", font_size=PQ, color=BRANCO), Text("padronizar", font_size=PQ, color=BRANCO)).arrange(
            DOWN, buff=0.1)
        sem.move_to([X_SEM, BASE_Y - 0.2 - sem.height / 2, 0])
        nome_pad = Text("padronizado", font_size=PQ, color=BRANCO)
        nome_pad.move_to([X_PAD, BASE_Y - 0.2 - nome_pad.height / 2, 0])
        nomes = VGroup(sem, nome_pad)
        acerto = Text("acerto", font_size=PQ, color=CINZA).move_to([(X_SEM + X_PAD) / 2, BASE_Y + 0.45, 0])
        self.play(nuvem.animate.scale(s, about_point=c).shift(alvo - c),
                  FadeOut(VGroup(pz.eixos[3], pz.eixos[4], pz.eixos[5], f, pad, linhas, an, pl, ok)),
                  FadeIn(VGroup(cont, testados)), Create(base), FadeIn(nomes), FadeIn(acerto),
                  run_time=0.1 * self.duracao)

        # um pinguim por vez pisca branco, com o contador até 342
        t = ValueTracker(0)
        flash = Dot(radius=0.075, color=BRANCO).move_to(posicoes[0]).set_z_index(3)
        flash.add_updater(lambda m: m.move_to(posicoes[min(341, int(t.get_value()))]))
        self.add(flash)
        self.play(t.animate.set_value(341.99), ChangeDecimalToValue(cont, 342), rate_func=linear,
                  run_time=max(0.7, self.momento("sem") - self.time))
        flash.clear_updaters()

        b_sem, r_sem = barra(X_SEM, R["avaliacao"]["2_medidas"]["cru"]["acuracia"], CINZA, A2["sem_padronizar"])
        b_pad, r_pad = barra(X_PAD, R["avaliacao"]["2_medidas"]["rodada"]["acuracia"], VERDE, A2["padronizado"])
        self.ate("acerta")
        self.play(FadeOut(flash), GrowFromEdge(b_sem, DOWN), FadeIn(r_sem, shift=UP * 0.2),
                  run_time=0.1 * self.duracao)
        self.ate("padronizado")
        self.play(GrowFromEdge(b_pad, DOWN), FadeIn(r_pad, shift=UP * 0.2), run_time=0.1 * self.duracao)

        bc = A2["barbichas_certas"]
        n_sem, n_pad = bc["sem_padronizar"].split(" de ")[0], bc["padronizado"].split(" de ")[0]
        total = bc["padronizado"].split(" de ")[1]
        barb = VGroup(Text("Barbichas certas:", font_size=FS, color=ROXO).move_to([0, -2.66, 0]),
                      conta(n_sem, " → ", n_pad, f" de {total}", tamanho=FC, cores={2: VERDE}).move_to([0, -3.24, 0]))
        empates = R["avaliacao"]["2_medidas"]["cru"]["empates_no_voto"]
        rodape = VGroup(Text(f"{empates} empates no voto:", font_size=PQ, color=CINZA),
                        Text("decide o mais perto", font_size=PQ, color=CINZA)).arrange(DOWN, buff=0.1).move_to(
            [0, -4.14, 0])
        self.play(FadeIn(barb, shift=UP * 0.15), run_time=min(0.4, self.restante()))
        self.play(FadeIn(rodape), run_time=min(0.4, self.restante()))
        self.completar()
