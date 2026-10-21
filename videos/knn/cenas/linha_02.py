"""[ANIM] Ela conhece outros 341 pinguins: espécie, bico e peso.

O balão sai e o pinguim vira o ponto branco com "?"; nasce o plano bico × peso e o ponto vai para (50,9; 3.550).
Em "341" caem os outros 341, cinza, com o contador e "341 + ? = 342"; no alto, Palmer, os anos e a fonte.
Em "espécie" cada ponto pega a cor da espécie e a legenda entra no lugar do contador. Termina em fim_linha_2().
"""
from estilo import *
from comum import *


class Cena(CenaHumanim):
    def construct(self):
        a = fim_linha_1()
        self.add(*a.values())

        pl = plano_cru(cores=False)
        bolinha = pl.misterioso.copy().move_to(PINGUIM_L1)
        q = pl.interrogacao.copy().move_to(bolinha.get_center() + (pl.interrogacao.get_center() - pl.misterioso.get_center()))
        self.play(FadeOut(VGroup(a["balao"], a["credito"], a["bico"], a["peso"]), shift=UP * 0.2),
                  ReplacementTransform(a["pinguim"], bolinha), ReplacementTransform(a["interrogacao"], q),
                  run_time=0.13 * self.duracao)
        self.play(Create(pl.eixos), bolinha.animate.move_to(pl.misterioso), q.animate.move_to(pl.interrogacao),
                  run_time=0.15 * self.duracao)
        self.remove(bolinha, q)
        self.add(pl.misterioso, pl.interrogacao)

        cont, soma, titulo = contador(0), soma_342(), titulo_dados()
        self.ate("341")
        self.add(cont)
        self.play(LaggedStart(*(FadeIn(p, shift=DOWN * 0.4) for p in pl.grupo_pontos), lag_ratio=0.004),
                  ChangeDecimalToValue(cont, 341), FadeIn(titulo, shift=DOWN * 0.15), run_time=0.24 * self.duracao)
        self.play(FadeIn(soma, shift=UP * 0.15), run_time=0.07 * self.duracao)

        fim, tit_fim, leg = fim_linha_2()
        self.ate("espécie")
        self.play(*(p.animate.set_color(COR[PONTOS[l][0]]) for l, p in pl.pontos.items()),
                  FadeOut(VGroup(cont, soma)), FadeIn(leg, shift=LEFT * 0.2), run_time=min(0.6, self.restante() - 0.2))
        self.remove(*self.mobjects)
        self.add(fim.tudo, tit_fim, leg)  # o mesmo estado, com os objetos do comum.py: a linha 3 começa daqui
        self.completar()
