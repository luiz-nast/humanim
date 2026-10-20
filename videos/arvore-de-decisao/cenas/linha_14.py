"""[ANIM] Vence dois meses de atraso. Cortar em um mês perde: os atrasados ficam meio a meio.

Saem idade e estado civil (caixas, marcas e ligações). A referência apagada do 0,29 vira a vencedora,
"2+ meses?", em amarelo, com o nome à esquerda da régua e o número à direita; entra "1+ mês?" no 0,30, do mesmo
jeito. Em "Cortar", o nome "1+ mês?" sai da régua e vira uma caixa à esquerda, que se divide: o lado "sim"
(6.818 clientes, 1 ponto = 100) fica metade vermelho, metade verde, e o "não" é só a contagem, 23.182, em cinza.
Em "perde", o 0,30 pisca em vermelho, acima do 0,29. Em "atrasados", "50% calote" e a bagunça desse
lado: 0,50, o máximo; em "ficam", o grupo pisca. A linha 15 continua daqui.
"""
from estilo import *
from comum import *


class Cena(CenaHumanim):
    def construct(self):
        z = regua_zoom()
        antes_ = marca_antes()
        ref = referencia_atraso()
        cx13, tira = candidatos_13(final=True)
        tri13 = setinhas_13()
        lig = ligacoes_13(cx13, tri13)
        for k in tira:
            tira[k].set_color(VERMELHO)
        self.add(z, antes_, ref, *cx13.values(), *tira.values(), *tri13.values(), *lig.values())

        # Saem idade e estado civil; a referência do atraso vira a vencedora; entra o "1+ mês?".
        m = marcas_14()
        self.play(FadeOut(VGroup(*cx13.values(), *tira.values(), *tri13.values(), *lig.values()), scale=0.9),
                  ReplacementTransform(ref[0], m["dois"][0]), FadeTransform(ref[1], m["dois"][1]),
                  FadeTransform(ref[2], m["dois"][2]), FadeIn(m["um"], shift=LEFT * 0.3), run_time=0.45)
        self.play(Flash(m["dois"][0].get_center(), color=AMARELO, flash_radius=0.45, line_length=0.25),
                  Indicate(m["dois"][2], color=BRANCO, scale_factor=1.08), run_time=0.5)

        # Cortar em 1 mês: o nome sai da régua e vira a caixa, que se divide.
        c = corte_1mes()
        self.ate("cortar")
        self.play(FadeTransform(m["um"][2].copy(), c["caixa"]), run_time=0.45)
        self.ate("um")
        self.play(GrowArrow(c["s_sim"]), GrowArrow(c["s_nao"]), FadeIn(c["n_sim"]), FadeIn(c["n_nao"]),
                  FadeIn(c["nao"]), FadeIn(c["n6818"]),
                  LaggedStart(*(FadeIn(p, shift=DOWN * 0.6) for p in c["pts"]), lag_ratio=0.01), run_time=0.6)
        self.ate("perde")
        self.play(Indicate(m["um"], color=VERMELHO, scale_factor=1.03), run_time=0.45)

        # Os atrasados ficam meio a meio: 50% de calote, bagunça 0,50 (o máximo).
        self.ate("atrasados")
        self.play(FadeIn(c["pct"], scale=1.4), FadeIn(c["calote"]), FadeIn(c["gini"], shift=UP * 0.2), run_time=0.45)
        self.ate("ficam")
        self.play(Indicate(c["pts"], color=AMARELO, scale_factor=1.06), run_time=0.45)
        self.completar()
