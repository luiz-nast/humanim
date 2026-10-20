"""[ANIM] E repete em cada lado, sem voltar atrás: busca gulosa. Não garante a melhor árvore.

Continua a linha 14: em "E repete", o resto sai e o nome "2+ meses?" da régua vira a raiz da árvore, no alto. A
árvore cresce um nível, a do scikit-learn com profundidade 2: no lado "não" (26.870) nasce "agosto 2+?" e no lado
"sim" (3.130) "julho quitado?" (julho pago em dia ou sem nada a pagar), cada um piscando. Em "sem voltar atrás",
a raiz fica travada em azul com um cadeado; em "gulosa", o rótulo "busca gulosa"; em "garante" e "melhor",
embaixo, a bagunça final dela: 0,2810. Acima do canto (a linha 16 é [CANTO] e continua daqui).
"""
from estilo import *
from comum import *


class Cena(CenaHumanim):
    def construct(self):
        e = estado_14()
        c = e["corte"]
        self.add(e["regua"], e["antes"], e["dois"], e["um"], *c.values())

        # O resto sai; o "2+ meses?" da régua vira a raiz.
        g = gulosa()
        self.play(FadeOut(VGroup(e["regua"], e["antes"], e["dois"][:2], e["um"], *c.values())), run_time=0.25)
        self.play(FadeTransform(e["dois"][2], g["raiz"]), run_time=0.3)

        self.ate("em")
        self.play(GrowArrow(g["s_a"]), GrowArrow(g["s_b"]), FadeIn(g["n_a"]), FadeIn(g["n_b"]),
                  FadeIn(g["c_a"]), FadeIn(g["c_b"]), run_time=0.4)
        self.ate("cada")
        self.play(FadeIn(g["b"], shift=DOWN * 0.3), run_time=0.3)
        self.play(Indicate(g["b"], color=AMARELO, scale_factor=1.1), run_time=0.3)
        self.ate("lado")
        self.play(FadeIn(g["a"], shift=DOWN * 0.3), run_time=0.3)
        self.play(Indicate(g["a"], color=AMARELO, scale_factor=1.1), run_time=0.3)

        alvo = g["raiz"].copy()
        cad = raiz_travada(alvo)
        self.ate("voltar")
        self.play(Transform(g["raiz"], alvo), FadeIn(cad, scale=1.6), run_time=0.45)

        nome = rotulo("busca gulosa", cor=AMARELO, tamanho=48).next_to(g["raiz"], UP, buff=0.22)
        self.ate("gulosa")
        self.play(FadeIn(nome, shift=DOWN * 0.2), run_time=0.4)

        num = numero_grande(GULOSA)
        self.ate("garante")
        self.play(FadeIn(num[1], shift=UP * 0.2), run_time=0.4)
        self.ate("melhor")
        self.play(FadeIn(num[0], scale=1.3), run_time=min(0.5, self.restante() - 0.05))
        self.completar()
