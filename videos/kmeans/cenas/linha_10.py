"""[ANIM] Nas 100 curtas, afaste o centro 1 minuto da média: a soma sobe 100. Dois minutos: sobe 400.

Começa no fim da linha 9 (fim_linha_9 do bloco_4.py: plano final, linhas cinza até os centros, régua amarela com
"distância²", "3.456 + 5.446 = 8.902" e a setinha; régua, rótulo e setinha saem junto com o laranja). Em "Nas 100
curtas", uma moldura amarela pega o trecho das curtas e cresce até o zoom (outro plano, com a escala nova); o laranja
sai e o 3.456 fica sozinho no alto, com "15 duração + 3.441 espera" embaixo. Em "afaste", o losango sobe 1 min na espera
(contorno cinza onde estava), as linhas vão junto e ficam amarelas (esticaram) ou brancas (encolheram), comparado em
minutos; em "minuto", a setinha "1 min". Em "sobe", "3.456 + 100 × 1² = 3.556". Em "Dois", mais 1 min ("2 min") e
"3.456 + 100 × 2²" / "= 3.456 + 400 = 3.856"; em "400", o 400 acende. Termina acima do canto (a 11 é [CANTO]).
"""
from estilo import *
from comum import *
from bloco_5 import *
from bloco_4 import fim_linha_9


class Cena(CenaHumanim):
    def construct(self):
        # emenda com o fim da linha 9 (a régua amarela, o "distância²" e a setinha saem junto com o laranja)
        f9 = fim_linha_9()
        pl, cs, lin = f9["plano"], f9["centros"], f9["linhas"]
        soma, nome = f9["conta"], f9["nome"]
        extra = VGroup(f9["regua"], f9["rotulo"], f9["setinha"])
        self.add(lin, pl.eixos, *pl.pontos.values(), cs, f9["regua"], f9["rotulo"], soma, nome, f9["setinha"])

        pz = zoom()
        lz, cz = linhas_zoom(pz, 0), centro_em(pz, 0)
        tres, parte, rot = tres_no_alto(), partes(), rotulos_zoom(pz)
        a, b, c = contas()
        mold = moldura(pl)

        # "Nas 100 curtas": a moldura pega as curtas e cresce até o zoom
        longas = [i for i in pl.pontos if GRUPOS[5][i] == 1]
        sai = VGroup(*(pl.pontos[i] for i in longas), *(lin[i] for i in longas), cs[1], *soma[1:], nome)
        self.play(Create(mold), FadeOut(sai), FadeOut(extra), ReplacementTransform(soma[0], tres), run_time=0.3)
        self.play(Transform(mold, moldura_zoom()), FadeOut(pl.eixos), FadeIn(pz.eixos),
                  *(ReplacementTransform(pl.pontos[i], pz.pontos[i]) for i in CURTAS),
                  *(ReplacementTransform(lin[i], lz[k]) for k, i in enumerate(CURTAS)),
                  ReplacementTransform(cs[0], cz), FadeIn(rot), FadeIn(parte, shift=DOWN * 0.1), run_time=0.6)

        # "afaste o centro 1 minuto": o losango sobe 1 min e cada linha muda de verdade
        self.ate("afaste")
        self.add(fantasma(pz))
        self.play(FadeOut(mold), cz.animate.move_to(centro_em(pz, 1)), Transform(lz, linhas_zoom(pz, 1, cores=False)),
                  run_time=0.5)
        self.play(Transform(lz, linhas_zoom(pz, 1)), run_time=0.4)
        self.ate("minuto")
        reg = regua(pz, 1)
        self.play(FadeIn(reg), run_time=0.35)
        self.ate("média")
        self.play(Indicate(rot[1], color=AMARELO), Indicate(rot[2], color=AMARELO), run_time=0.5)
        self.ate("soma")
        self.play(Indicate(tres, color=AMARELO, scale_factor=1.15), run_time=0.35)

        # "a soma sobe 100"
        self.ate("sobe")
        self.play(AnimationGroup(ReplacementTransform(tres, a[0]), Write(a[1:3]), lag_ratio=0.45), run_time=0.45)
        self.ate("100", vez=2)
        self.play(Write(a[3:]), run_time=0.3)

        # "Dois minutos: sobe 400"
        self.ate("Dois")
        self.play(cz.animate.move_to(centro_em(pz, 2)), Transform(lz, linhas_zoom(pz, 2)), Transform(reg, regua(pz, 2)),
                  FadeOut(parte), run_time=0.5)
        self.play(Write(b), run_time=0.4)
        self.ate("sobe", vez=2)
        self.play(Write(c), run_time=0.35)
        self.ate("400")
        c[3].set_color(AMARELO)
        self.play(Indicate(c[3], color=AMARELO, scale_factor=1.35), run_time=min(0.45, self.restante()))
        self.completar()
