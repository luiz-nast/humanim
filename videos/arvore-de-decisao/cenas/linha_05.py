"""[ANIM] Iguais: 0,78 vezes 0,78, mais 0,22 vezes 0,22. Dá 0,66.

Os dois clientes da linha 4 vão até o começo das réguas do quadrado das chances e as réguas crescem a partir
deles: o 1º (linhas, de cima para baixo) e o 2º (colunas), cada régua cortada em 0,78 (verde, paga) e 0,22
(vermelho, calote). No primeiro "0,78" pisca a régua do 1º; no primeiro "vezes", a do 2º e acende a cela verde
com "0,78 × 0,78"; no segundo "0,78", "= 0,61" e "os dois pagam". Em "mais", o 0,61 sai da cela e desce para
a soma. No "0,22", acende a cela vermelha; no segundo "vezes", "0,22 × 0,22" logo embaixo dela (não cabe nela),
"os dois: calote"; no segundo "0,22", "= 0,05". Em "Dá", o 0,05 desce para a soma; em "66", "= 0,66" e "iguais".
"""
from estilo import *
from comum import *


class Cena(CenaHumanim):
    def construct(self):
        nv = nuvem(**NUVEM_4)
        d, nomes, dif = dois_clientes(revelados=True)
        self.add(nv, d, nomes, dif)

        # Os dois clientes vão para o começo das réguas e as réguas crescem a partir deles.
        q = quadrado()
        c = contas_5()
        ini_lado, ini_topo = pontas_reguas()
        self.play(FadeOut(nv, shift=UP * 0.6), FadeOut(dif, scale=0.5),
                  d[0].animate.scale(0.2).move_to(ini_lado), d[1].animate.scale(0.2).move_to(ini_topo),
                  FadeTransform(nomes[0], q["quem_lado"]), FadeTransform(nomes[1], q["quem_topo"]), run_time=0.5)
        self.play(FadeOut(d[0]), FadeOut(d[1]),
                  LaggedStart(GrowFromEdge(q["lado"][0], UP), GrowFromEdge(q["lado"][1], UP), lag_ratio=0.6),
                  LaggedStart(GrowFromEdge(q["topo"][0], LEFT), GrowFromEdge(q["topo"][1], LEFT), lag_ratio=0.6),
                  Create(q["borda"]), Create(q["grade"]), FadeIn(q["n_lado"]), FadeIn(q["n_topo"]), run_time=0.6)
        pp, cc = q["celas"]["pp"], q["celas"]["cc"]
        self.add(*q["celas"].values())
        self.bring_to_front(q["grade"], q["borda"])

        # 0,78 × 0,78: os dois pagam.
        self.ate("78")
        self.play(Indicate(VGroup(q["lado"][0], q["n_lado"][0]), scale_factor=1.0, color=AMARELO), run_time=0.5)
        self.ate("vezes")
        self.play(pp.animate.set_fill(opacity=0.4), FadeIn(c["vezes_p"], shift=UP * 0.15),
                  Indicate(VGroup(q["topo"][0], q["n_topo"][0]), scale_factor=1.0, color=AMARELO), run_time=0.5)
        self.bring_to_front(q["grade"], q["borda"], c["vezes_p"])
        self.ate("78", vez=2)
        self.play(FadeIn(c["igual_p"], shift=UP * 0.15), FadeIn(c["dois_pagam"]), run_time=0.4)

        # "mais": o 0,61 sai da cela verde e vira o primeiro termo da soma.
        soma = c["soma"]
        self.ate("mais")
        self.play(ReplacementTransform(c["igual_p"][1].copy(), soma[0], path_arc=0.5), FadeIn(soma[1]), run_time=0.6)

        # 0,22 × 0,22: os dois dão calote (cela pequena: a conta fica logo embaixo dela).
        self.ate("22")
        self.play(cc.animate.set_fill(opacity=0.8),
                  Indicate(VGroup(q["lado"][1], q["n_lado"][1]), scale_factor=1.0, color=AMARELO), run_time=0.45)
        self.bring_to_front(q["grade"], q["borda"])
        self.ate("vezes", vez=2)
        self.play(FadeIn(c["vezes_c"][:3], shift=UP * 0.15), FadeIn(c["dois_calote"], shift=UP * 0.15),
                  Indicate(VGroup(q["topo"][1], q["n_topo"][1]), scale_factor=1.0, color=AMARELO), run_time=0.5)
        self.ate("22", vez=2)
        self.play(FadeIn(c["vezes_c"][3:], shift=UP * 0.15), run_time=0.35)

        # Dá 0,66: o 0,05 desce para a soma.
        self.ate("dá")
        self.play(ReplacementTransform(c["vezes_c"][4].copy(), soma[2], path_arc=-0.5), run_time=0.6)
        self.ate("66")
        self.play(FadeIn(soma[3:], shift=LEFT * 0.2), FadeIn(c["iguais"], shift=UP * 0.2),
                  Indicate(VGroup(pp, cc), color=AMARELO, scale_factor=1.0), run_time=min(0.5, self.restante() - 0.1))
        # a ordem do começo da linha 6 (celas embaixo; grade, borda e textos em cima), para a emenda não saltar
        self.bring_to_front(q["grade"], q["borda"], q["lado"], q["topo"], q["n_lado"], q["n_topo"], q["quem_lado"],
                            q["quem_topo"], c["vezes_p"], c["igual_p"], c["dois_pagam"])
        self.completar()
