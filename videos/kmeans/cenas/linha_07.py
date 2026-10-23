"""[ANIM] E repete. Trocam 65, depois 23, depois 3. Quando ninguém troca, para: 100 curtas e 172 longas.

Começa onde a linha 6 termina. Em "repete", "rodada 2" no alto. Em cada número (65, 23, 3): a rodada muda, as
erupções que estão do outro lado da fronteira (calculada) ganham um anel amarelo e trocam de cor (regra 1), o contador
"N trocam" embaixo mostra quantas, e os losangos vão para a média do grupo novo (regra 2), com a fronteira recalculada
a cada quadro (desce) e as coordenadas trocadas no pouso. Em "ninguém", "rodada 5" e "0 trocam": nada se mexe. Em
"para", as regras e as coordenadas saem e "parou" acende ao lado do "rodada 5". Em "100", "100 curtas" e "172 longas"
nas vagas do comum.py, com "100 + 172 = 272" montando embaixo. A linha 8 é [CARA]: o fim não precisa emendar.
"""
from estilo import *
from comum import *
from bloco_3 import *


class Cena(CenaHumanim):
    def construct(self):
        a = fim_linha_6()
        adicionar(self, a)  # emenda com o fim da linha 6
        pl, los, cs = a["plano"], a["centros"], a["coords"]
        fronteira_parada = a["fronteira"]

        rod = rodada(2)
        self.ate("repete")
        self.play(FadeIn(rod, shift=DOWN * 0.15), FadeOut(a["centro"]), FadeOut(a["centroide"]), run_time=0.45)

        cont = trocam(len(TROCAS[2]))
        for r, palavra in ((2, "65"), (3, "23"), (4, "3")):
            self.ate(palavra)
            # regra 1: quem está do outro lado da fronteira troca de grupo
            an = aneis(pl, TROCAS[r])
            cores = [pl.pontos[i].animate.set_color(COR_G[GRUPOS[r][i]]) for i in TROCAS[r]]
            if r == 2:
                extra = [FadeIn(cont, shift=UP * 0.15)]
            else:
                cont.n.set_value(len(TROCAS[r]))
                extra = [Transform(rod, rodada(r)), Indicate(cont.n, scale_factor=1.15, color=AMARELO)]
            curto = r == 4  # entre o "3" e o "ninguém" a fala dá menos de 1 s
            self.play(FadeIn(an, scale=1.6), *cores, *extra, run_time=0.3 if curto else 0.35)
            self.play(FadeOut(an), run_time=0.15 if curto else 0.2)

            # regra 2: os losangos vão para a média do grupo novo; a fronteira acompanha (calculada)
            viva = fronteira_viva(pl, los)
            self.remove(fronteira_parada)
            self.add(viva)
            self.play(*(los[g].animate.move_to(pl.p(*CENTROS[r][g])) for g in (0, 1)),
                      run_time=0.4 if curto else 0.55)
            fronteira_parada = fronteira(pl, r)
            self.remove(viva)
            self.add(fronteira_parada)
            novas = VGroup(coords(0, r), coords(1, r))
            self.remove(cs)  # coordenadas novas no pouso
            self.add(novas)
            cs = novas

        self.ate("ninguém")
        cont.n.set_value(0)
        self.play(Transform(rod, rodada(5)), Indicate(cont.n, scale_factor=1.25, color=AMARELO), run_time=0.45)

        self.ate("para")
        parou = Text("parou", font_size=ROTULO, color=AMARELO)
        parou.move_to([rod.get_right()[0] + 0.35 + parou.width / 2, Y2, 0])
        parou.shift(UP * (rod[0].get_bottom()[1] - parou[1].get_bottom()[1]))  # mesma linha de base do "rodada 5"
        self.play(AnimationGroup(FadeOut(VGroup(a["regra1"], a["regra2"]), shift=UP * 0.15), FadeOut(cs),
                                 FadeIn(parou, scale=1.3), lag_ratio=0.5), run_time=0.45)

        soma = conta("100", " + ", "172", " = ", "272", tamanho=G, cores={0: AZUL, 2: LARANJA}).move_to([0, -3.0, 0])
        self.ate("100")
        self.play(FadeIn(rotulo_grupo(pl, 0, "100", "curtas"), scale=1.15), FadeOut(cont),
                  FadeIn(soma[0], shift=UP * 0.15), run_time=0.5)
        self.ate("172")
        self.play(FadeIn(rotulo_grupo(pl, 1, "172", "longas"), scale=1.15),
                  FadeIn(VGroup(soma[1], soma[2]), shift=UP * 0.15), run_time=0.5)
        self.play(FadeIn(VGroup(soma[3], soma[4]), shift=UP * 0.15), run_time=min(0.45, self.restante()))
        self.completar()
