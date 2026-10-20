"""[ANIM] Entre os atrasados, quase 7 em 10 deram calote: mais perto do meio a meio, mais bagunça.

A nuvem de 300 pontos (1 = 100 clientes) se divide pela pergunta, com as duas setas desenhadas igual e "sim"/"não"
ao lado delas: 31 para o "sim" (22 vermelhos) e 269 para o "não" (44 vermelhos), cada grupo com os vermelhos
embaixo, para a mistura se ler como um nível. O "sim" pisca, com 3.130 e 69,6% centrados embaixo dele. Nasce a
régua da bagunça (0 = puro, com um grupinho só verde; 0,5 = meio a meio, com um xadrez; título "bagunça"), com
os 30 mil ("antes") no 0,34; a conta do lado "sim" sai em duas linhas, embaixo, e o 0,42 vai para a régua.
A conta sai no começo da linha 9; o 0,42 fica na régua (a linha 10 é [CANTO]).
"""
from estilo import *
from comum import *


class Cena(CenaHumanim):
    def construct(self):
        raiz = pergunta_vencedora()
        pts = nuvem(**NUVEM_8)
        self.add(raiz, pts)

        # A pergunta divide a nuvem.
        setas, nomes = galhos_8()
        alvo = pontos_divididos()
        self.play(*(GrowArrow(s) for s in setas.values()), *(FadeIn(n) for n in nomes.values()), run_time=0.35)
        self.play(LaggedStart(*(pts[i].animate.move_to(alvo[i].get_center()) for i in range(300)),
                              lag_ratio=0.002), run_time=0.8)

        # Os atrasados: 3.130 clientes, quase 7 em 10 deram calote.
        rg = rotulos_grupos()
        sim = VGroup(*(pts[i] for i in indices("sim")))
        self.ate("quase")
        self.play(FadeIn(rg["cont_s"], shift=UP * 0.2), Indicate(sim, color=AMARELO, scale_factor=1.15), run_time=0.5)
        vermelhos_sim = [pts[i] for i in indices("sim") if NUVEM_COR[i] == VERMELHO]
        self.play(LaggedStart(*(Indicate(p, color=VERMELHO, scale_factor=1.9) for p in vermelhos_sim),
                              lag_ratio=0.05), run_time=0.7)
        self.ate("calote")
        self.play(FadeIn(rg["pct_s"], scale=1.15), run_time=0.4)

        # A conta do lado "sim" começa; nasce a régua da bagunça.
        l1, l2 = conta_lado(S_PAGA, S_CAL, G_SIM)
        r = regua()
        m = marcadores_8()
        self.ate("mais")
        self.play(FadeIn(l1, shift=UP * 0.2), run_time=0.3)
        self.ate("perto")
        self.play(Create(r["linha"]), FadeIn(r["tiques"]), FadeIn(r["n0"]), FadeIn(r["puro"]), FadeIn(r["g_puro"]),
                  FadeIn(r["nome"]), FadeIn(m["todos"], shift=LEFT * 0.2), run_time=0.45)
        self.ate("meio")
        self.play(FadeIn(r["g_meio"], scale=1.5), FadeIn(r["meio"]), FadeIn(r["n5"]), run_time=0.35)
        self.ate("meio", vez=2)
        self.play(FadeIn(l2[:3], shift=UP * 0.2), run_time=0.25)
        self.ate("mais", vez=2)
        l2[3].set_color(VERMELHO)
        self.play(FadeIn(l2[3], shift=UP * 0.2), run_time=0.25)
        self.play(ReplacementTransform(l2[3].copy(), m["sim"][1], path_arc=-0.4), FadeIn(m["sim"][0]),
                  run_time=min(0.4, self.restante() - 0.05))
        self.completar()
