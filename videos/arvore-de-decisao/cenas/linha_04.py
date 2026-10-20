"""[CANTO] Bagunça é isto: sorteia dois clientes. Qual a chance de serem diferentes?

A nuvem dos 300 (verde pagou, vermelho calote) volta no alto e chacoalha: é a mistura. Dois pontos saem dela,
ficam cinza (cor escondida) e param lado a lado, com "1º" e "2º" embaixo; em "chance" aparece um "?" entre eles;
em "diferentes", os dois mostram a cor (um verde, um vermelho) e o "?" vira um "≠" amarelo. Tudo acima do canto.
"""
from estilo import *
from comum import *


class Cena(CenaHumanim):
    def construct(self):
        nv = nuvem(**NUVEM_4)
        self.add(nv)
        rng = np.random.default_rng(11)
        tremor = [np.array([*rng.uniform(-0.1, 0.1, 2), 0.0]) for _ in nv]
        self.play(*(p.animate.shift(v) for p, v in zip(nv, tremor)), rate_func=there_and_back, run_time=0.8)

        # Sorteia dois: saem da nuvem (cópias: ninguém sai da base), perdem a cor e param lado a lado.
        d, nomes, dif = dois_clientes(revelados=False)
        a, b = nv[SORTEADOS[0]].copy(), nv[SORTEADOS[1]].copy()
        self.ate("sorteia")
        self.play(Indicate(nv[SORTEADOS[0]], scale_factor=2.5, color=BRANCO),
                  Indicate(nv[SORTEADOS[1]], scale_factor=2.5, color=BRANCO), run_time=0.4)
        self.play(ReplacementTransform(a, d[0]), ReplacementTransform(b, d[1]), run_time=0.6)
        self.play(FadeIn(nomes, shift=UP * 0.2), run_time=0.3)

        q = rotulo("?", cor=AMARELO, tamanho=130).move_to(dif)
        self.ate("chance")
        self.play(FadeIn(q, scale=1.4), run_time=0.35)
        revelados = dois_clientes(revelados=True)[0]
        self.ate("serem")
        self.play(Transform(d[0], revelados[0]), Transform(d[1], revelados[1]), run_time=0.35)
        self.ate("diferentes")
        self.play(FadeTransform(q, dif), run_time=min(0.35, self.restante() - 0.05))
        self.completar()
