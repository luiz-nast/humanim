"""[ANIM] Diferentes: o resto, 0,34. Isso tem nome: impureza de Gini.

No mesmo quadrado, as duas celas fora da diagonal acendem em amarelo ("diferentes", em branco, por cima): é o que
sobra de 1. Em "resto", as contas das celas viram quadrados ("0,78²", "0,22² = 0,05"), e a soma da linha 5 vira a
conta inteira, termo a termo: 1 − (0,78² + 0,22²) = 1 − 0,66 = 0,34. Em "Isso", o resto sai de foco e a conta sai;
em "nome", o 0,34 dela cresce e ganha "impureza de Gini"; embaixo, pequenos e em cinza, "≠ Gini da renda" e
"outra medida: entropia" (a régua do ID3, que não é sinônimo).
"""
from estilo import *
from comum import *


class Cena(CenaHumanim):
    def construct(self):
        q = acender_5(quadrado())
        c = contas_5()
        self.add(quadrado_base(q), *(c[k] for k in ("vezes_p", "igual_p", "dois_pagam", "vezes_c", "dois_calote",
                                                     "soma", "iguais")))

        # Diferentes: as duas celas de fora da diagonal.
        pc, cp = q["celas"]["pc"], q["celas"]["cp"]
        dif = rotulo("diferentes", tamanho=G).move_to(cp)
        self.play(pc.animate.set_fill(opacity=0.35), cp.animate.set_fill(opacity=0.35),
                  FadeOut(VGroup(c["dois_calote"], c["iguais"]), shift=DOWN * 0.2), run_time=0.45)
        self.bring_to_front(q["grade"], q["borda"], c["vezes_p"], c["igual_p"], c["dois_pagam"])
        self.play(FadeIn(dif, scale=1.2), run_time=0.3)

        # O resto: as contas das celas viram quadrados e a soma vira a conta inteira.
        qp, qc = quadrados_6()
        l1, l2, grande, nome, aparte = contas_6()
        s = c["soma"]
        self.ate("resto")
        self.play(FadeTransform(c["vezes_p"], qp), FadeTransform(c["vezes_c"][:3], qc[0]),
                  Transform(c["vezes_c"][3:], qc[1:]), run_time=0.4)
        self.play(FadeTransform(s[0], l1[1]), Transform(s[1], l1[2]), FadeTransform(s[2], l1[3]),
                  FadeIn(l1[0], shift=RIGHT * 0.2), FadeIn(l1[4], shift=LEFT * 0.2),
                  FadeOut(s[3]), Transform(s[4], l2[1]), FadeIn(l2[0], shift=RIGHT * 0.2), run_time=0.55)
        self.ate("34")
        self.play(FadeIn(l2[2:], shift=LEFT * 0.2), Indicate(VGroup(pc, cp), color=AMARELO, scale_factor=1.0),
                  run_time=0.4)
        self.bring_to_front(q["grade"], q["borda"], dif, qp, c["igual_p"], c["dois_pagam"])

        # Isso tem nome: o resto sai de foco; o 0,34 da conta cresce e ganha o nome.
        fora = VGroup(qp, c["igual_p"], c["dois_pagam"], q["n_lado"], q["n_topo"], q["quem_lado"], q["quem_topo"])
        self.ate("isso")
        self.play(fora.animate.set_color(APAGADO), dif.animate.set_color(CINZA),
                  FadeOut(VGroup(qc[0], c["vezes_c"][3:]), shift=UP * 0.15),
                  FadeOut(VGroup(l1[0], s[1], l1[4], l2[0], s[4], l2[2]), shift=DOWN * 0.15),
                  FadeOut(VGroup(l1[1], l1[3]), shift=DOWN * 0.15), run_time=0.4)
        self.ate("nome")
        self.play(ReplacementTransform(l2[3], grande), FadeIn(nome, shift=UP * 0.2), run_time=0.45)
        self.play(FadeIn(aparte, shift=UP * 0.15), run_time=0.4)
        self.ate("impureza")
        self.play(Indicate(nome, color=AMARELO, scale_factor=1.08), run_time=min(0.5, self.restante() - 0.05))
        self.completar()
