"""[CANTO] Isso é padronizar: quantos desvios da média. Agora os 5 mais perto são Barbichas: acertou.

Os cartões encolhem para o alto e saem com as contas; o "agora 0,14 < 1,60" fica na faixa. Volta o plano em
desvios com "z = (x − média) ÷ desvio" embaixo e os anéis das 5 Adélias. Em "padronizar", o rótulo acende em cima
do plano, o "÷ desvio" fica amarelo e o "− média" cinza; em "Agora" os anéis apagam; em "perto", 5 linhas amarelas
até os 5 Barbichas colados no misterioso; em "Barbichas", o placar "5 Barbicha / 0 Adélia"; em "acertou", o ✓.
Termina em fim_linha_14(); tudo acima do canto.
"""
from estilo import *
from comum import *
from bloco_5 import *


class Cena(CenaHumanim):
    def construct(self):
        knn, cb, ca, c, v = fim_linha_13()
        self.add(knn, cb, ca, c, v)

        pz = plano_z(True)
        f = formula_14()
        an_cru = aneis(pz, VIZ_CRU)
        self.play(FadeOut(cb, scale=0.3, shift=UP * 1.3 + LEFT * 0.4), FadeOut(ca, scale=0.3, shift=UP * 1.3 + RIGHT * 0.4),
                  FadeOut(c), Create(pz.eixos), FadeIn(pz.grupo_pontos), FadeIn(pz.misterioso), FadeIn(f),
                  run_time=0.14 * self.duracao)
        self.play(Create(an_cru), run_time=0.06 * self.duracao)

        f1, pad = formula_14(True), padronizar()
        self.ate("padronizar")
        self.play(FadeIn(pad, shift=DOWN * 0.15), f[2].animate.set_color(CINZA), f[4].animate.set_color(AMARELO),
                  run_time=0.08 * self.duracao)
        self.ate("desvios")
        self.play(Indicate(f[4], color=AMARELO, scale_factor=1.15), run_time=0.08 * self.duracao)
        self.ate("Agora")
        self.play(FadeOut(an_cru), run_time=0.06 * self.duracao)

        linhas, an = linhas_ate(pz, VIZ_Z), aneis(pz, VIZ_Z)
        self.ate("perto")
        self.play(Create(linhas), Create(an), run_time=0.08 * self.duracao)

        pl = placar(("Barbicha", 5), ("Adélia", 0))
        self.ate("Barbichas")
        self.play(FadeOut(v), FadeIn(pl), run_time=0.07 * self.duracao)
        ok = certo(pl.vaga)
        self.ate("acertou")
        self.play(Create(ok), run_time=min(0.4, self.restante()))

        knn2, pz2, f2, pad2, linhas2, an2, pl2, ok2 = fim_linha_14()
        self.remove(*self.mobjects)
        self.add(knn2, pz2.eixos, pz2.grupo_pontos, pz2.misterioso, f2, pad2, linhas2, an2, pl2, ok2)  # o mesmo estado, com os objetos do bloco_5.py: a linha 15 começa daqui
        self.completar()
