"""[CANTO] Pra prever calote, o que você pergunta primeiro? Menos de 30 anos? Casado? Dois meses de atraso?

Já no primeiro quadro (a prévia do feed): no alto, um cartão e "prever calote" grande, e embaixo as três caixas
com "?". Em "que você pergunta", os "?" pulsam; em "primeiro", a primeira caixa. Cada "?" vira a pergunta quando
ela é dita e acende em amarelo (a anterior volta ao azul). Tudo acima do canto.
"""
from estilo import *
from comum import *


class Cena(CenaHumanim):
    def construct(self):
        cart, frase = titulo_prever()
        azuis = perguntas(acesa=None)
        amarelas = [perguntas(acesa=i)[i] for i in range(3)]
        bordas = [c[0] for c in azuis]
        interr = [rotulo("?", tamanho=90).move_to(b) for b in bordas]
        self.add(cart, frase, *bordas, *interr)

        self.play(Wiggle(cart, scale_value=1.15), run_time=0.6)
        self.ate("calote")
        self.play(Indicate(frase[2], color=VERMELHO, scale_factor=1.12), run_time=0.5)
        self.ate("que")
        self.play(LaggedStart(*(Indicate(q, color=AMARELO, scale_factor=1.3) for q in interr), lag_ratio=0.3),
                  run_time=0.8)
        self.ate("primeiro")
        self.play(Indicate(VGroup(bordas[0], interr[0]), color=AMARELO, scale_factor=1.05), run_time=0.5)

        for i, palavra in enumerate(("menos", "casado", "dois")):
            self.ate(palavra)
            anim = [bordas[i].animate.set_color(AMARELO), FadeOut(interr[i], scale=0.4)]
            if i:  # a anterior volta ao azul
                anim += [bordas[i - 1].animate.set_color(AZUL), amarelas[i - 1][1].animate.set_color(BRANCO)]
            self.play(*anim, run_time=0.15)
            self.play(FadeIn(amarelas[i][1], scale=1.25), run_time=0.3)
        self.ate("atraso")
        self.play(Indicate(VGroup(bordas[2], amarelas[2][1]), color=AMARELO, scale_factor=1.06),
                  run_time=min(0.5, self.restante() - 0.05))
        self.completar()
