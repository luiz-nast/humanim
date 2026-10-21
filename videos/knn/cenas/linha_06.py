"""[ANIM] Os 5 mais perto são Adélias do mesmo peso. Mas ele é Barbicha: errou.

Começa em fim_linha_5(). O triângulo sai e a fórmula fica pequena no alto; uma moldura sai do trecho bico 38–52 mm ×
peso 3.475–3.700 g do plano e cresce até um plano novo com esse trecho (zoom honesto), com o misterioso e os 5 anéis;
o bico de cada um embaixo, em leque (39,6 e 39,7 quase se tocam). Em "Adélias" os 5 piscam e 5 votos voam para o
placar "5 Adélia × 0 Barbicha"; em "mesmo peso" a tracejada de 3.550 g; em "Barbicha" o branco fica roxo, rótulo, ✗.
"""
from estilo import *
from comum import *
from bloco_2 import *

ZOOM = (38, 52, 3475, 3700)
CAIXA = (-3.0, -0.3, 3.2, 3.0)


class Cena(CenaHumanim):
    def construct(self):
        a = fim_linha_5()
        pl, an, fx, knn, tri, f = a["plano"], a["aneis"], a["faixa"], a["knn"], a["tri"], a["formula"]
        self.add(pl.tudo, an, fx, knn, tri, f)

        x0, x1, y0, y1 = ZOOM
        dentro = [l for l, (e, b, m) in PONTOS.items() if x0 <= b <= x1 and y0 <= m <= y1]
        novo = Plano(x0, x1, y0, y1, CAIXA, numeros_x={38: "38", 52: "52"}, marcas_x=(40, 45, 50),
                     marcas_y=(3500, 3600, 3700), so=dentro, raio=0.085, nome_y_dentro=True)
        novo.eixos.remove(novo.nome_x)  # os números do bico vão embaixo de cada vizinho
        novo.nome_y.move_to([CAIXA[0] + novo.nome_y.width / 2, CAIXA[3] + 0.42, 0])  # fora, sem pontos por cima
        novo.interrogacao.move_to(novo.misterioso.get_center() + [0.33, 0.42, 0])
        an2 = aneis(novo, VIZ_CRU).set_z_index(1)

        # moldura: do trecho no plano de antes até a caixa do plano novo
        de = Rectangle(width=pl.p(x1, y0)[0] - pl.p(x0, y0)[0], height=pl.p(x0, y1)[1] - pl.p(x0, y0)[1],
                       stroke_color=AMARELO, stroke_width=4).move_to((pl.p(x0, y0) + pl.p(x1, y1)) / 2)
        e, b, d, t = CAIXA
        para = Rectangle(width=d - e, height=t - b, stroke_color=AMARELO, stroke_width=4).move_to(
            [(e + d) / 2, (b + t) / 2, 0])
        f2 = formula_d(PQ).move_to([0.3, 4.3, 0])

        t_ad = self.momento("Adélias")
        self.play(FadeOut(tri), Transform(f, f2), Create(de), run_time=min(0.4, 0.3 * t_ad))
        self.play(Transform(de, para), FadeOut(VGroup(pl.tudo, an)), FadeIn(VGroup(novo.tudo, an2)),
                  run_time=min(0.6, 0.4 * t_ad))

        # bicos em leque, embaixo
        xs = [-2.9, -1.6, -0.3, 1.0, 2.3]
        ordem = sorted(VIZ_CRU, key=lambda l: PONTOS[l][1])
        bicos, leque = VGroup(), VGroup()
        for x, l in zip(xs, ordem):
            n = Text(br(PONTOS[l][1], 1), font_size=PQ, color=BRANCO).move_to([x, -1.75, 0])
            bicos.add(n)
            leque.add(Line(novo.pos(l) + [0, -0.16, 0], n.get_top() + [0, 0.08, 0], color=CINZA, stroke_width=2))
        self.play(FadeOut(de), LaggedStart(*(AnimationGroup(Create(li), FadeIn(n)) for li, n in zip(leque, bicos)),
                                           lag_ratio=0.25), run_time=min(0.6, max(0.3, t_ad - self.time - 1.0)))

        # "Adélias": piscam e votam
        pc = placar(("Adélia", 5), ("Barbicha", 0))
        pc.n1.set_value(0)
        self.ate("Adélias")
        cinco = VGroup(*(novo.pontos[l] for l in VIZ_CRU))
        self.play(Indicate(cinco, color=LARANJA, scale_factor=1.8), FadeOut(fx), FadeIn(pc), run_time=0.4)
        t_peso = self.momento("mesmo")
        passo = max(0.12, min(0.25, (t_peso - self.time - 0.1) / 5))
        for i, l in enumerate(ordem[::-1]):
            voto = Dot(novo.pos(l), radius=0.13, color=LARANJA).set_z_index(3)
            self.play(voto.animate.move_to(pc.n1).scale(0.6), run_time=passo)
            self.remove(voto)
            pc.n1.set_value(i + 1)

        # "mesmo peso": a tracejada dos 3.550 g
        y = novo.misterioso.get_center()[1]
        trac = DashedLine([e, y, 0], [d + 0.1, y, 0], color=BRANCO, stroke_width=3, dash_length=0.12).set_z_index(0)
        rot = Text(br(M_PESO) + " g", font_size=PQ, color=BRANCO).move_to([-0.35, y + 0.42, 0])
        rot = VGroup(BackgroundRectangle(rot, color=FUNDO, fill_opacity=0.9, buff=0.06), rot)
        self.ate("mesmo")
        self.play(Create(trac), FadeIn(rot), run_time=0.45)

        # "Barbicha": o branco fica roxo, rótulo e ✗ no placar
        nome = Text("Barbicha", font_size=FC, color=ROXO)
        nome.move_to([3.45 - nome.width / 2, y + 0.78, 0])
        nome = VGroup(BackgroundRectangle(nome, color=FUNDO, fill_opacity=0.9, buff=0.06), nome)
        x = xis(pc.vaga)
        self.ate("Barbicha")
        self.play(novo.misterioso.animate.set_color(ROXO).scale(1.4), FadeOut(novo.interrogacao), FadeIn(nome),
                  run_time=min(0.4, self.restante()))
        self.ate("errou")
        self.play(Create(x), run_time=min(0.35, self.restante()))
        self.play(Indicate(x, color=VERMELHO, scale_factor=1.3), run_time=min(0.5, self.restante()))
        self.completar()
