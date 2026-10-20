"""[ANIM] Do outro lado, só 1 em 6: a bagunça cai.

O lado "sim" apaga e a conta dele sai (o 0,42 fica na régua); já em "Do outro lado" começa a conta do "não", que
pisca, com 26.870 e, em "1 em 6", 16,6% embaixo. A conta fecha em 0,28; em "bagunça" ela sai descendo e a marca
verde nasce no 0,34 e cai até o 0,28, levando o número. A linha termina só acima do canto (a 10 é [CANTO]).
"""
from estilo import *
from comum import *


class Cena(CenaHumanim):
    def construct(self):
        e = estado_8()
        self.add(e["raiz"], *e["setas"].values(), *e["nomes"].values(), e["pts"], e["cont_s"], e["pct_s"],
                 *e["linhas"], e["regua"], e["m"]["todos"], e["m"]["sim"])

        # O "sim" sai de foco e a conta dele sai; a do "não" começa.
        l1, l2 = conta_lado(N_PAGA, N_CAL, G_NAO)
        l2[3].set_color(VERDE)
        self.play(*(e["pts"][i].animate.set_opacity(0.3) for i in indices("sim")),
                  e["setas"]["sim"].animate.set_color(APAGADO), e["nomes"]["sim"].animate.set_color(CINZA),
                  e["cont_s"].animate.set_color(CINZA), e["pct_s"].animate.set_color(APAGADO),
                  *(FadeOut(l, shift=DOWN * 0.3) for l in e["linhas"]), run_time=0.35)
        self.play(FadeIn(l1, shift=UP * 0.2), run_time=0.25)

        # O "não": 26.870 clientes, 16,6% de calote.
        rg = rotulos_grupos()
        nao = VGroup(*(e["pts"][i] for i in indices("nao")))
        self.ate("lado")
        self.play(FadeIn(rg["cont_n"], shift=UP * 0.2), Indicate(nao, color=AMARELO, scale_factor=1.06), run_time=0.4)
        self.ate("1")
        self.play(FadeIn(rg["pct_n"], scale=1.4), run_time=0.3)
        self.play(FadeIn(l2[:3], shift=UP * 0.2), run_time=0.25)
        self.play(FadeIn(l2[3], shift=UP * 0.2), run_time=0.2)

        # A bagunça cai: a conta sai e a marca verde nasce no 0,34 e desce até o 0,28, com o número.
        m = marcadores_8()["nao"]
        traco = m[0].copy().move_to(ponto(X_R, y_g(G_RAIZ)))
        self.ate("bagunça")
        self.play(FadeOut(VGroup(l1, l2[:3]), shift=DOWN * 0.3), FadeIn(traco, scale=1.6), run_time=0.25)
        self.play(Transform(traco, m[0]), ReplacementTransform(l2[3], m[1], path_arc=-0.3),
                  run_time=min(0.4, self.restante() - 0.05))
        self.completar()
