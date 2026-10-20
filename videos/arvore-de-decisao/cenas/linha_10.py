"""[CANTO] Piorou? Os atrasados são só 10%: pesando pelo tamanho, dá 0,29.

Logo no começo, num movimento só: os dois grupos viram barras com largura proporcional aos clientes, e a régua
vira uma lupa do trecho de 0,27 a 0,36 (as marcas andam para as novas alturas; o 0,42 passa do topo e fica numa
seta lá em cima; os Ginis dos lados vão para cima das barras). Em "Piorou?" já entra a média sem peso,
(0,42 + 0,28) ÷ 2 = 0,35, e a marca vermelha dela, acima do 0,34. Em "atrasados", a barra fininha pisca; em
"10", as contagens viram os pesos e a média sem peso é riscada e sai. Em "pesando", a média ponderada monta termo
a termo e fecha em "dá" com 0,29 (marca amarela, abaixo do 0,34); em "29", o nome "média ponderada".
Tudo acima do canto; só a régua desce, à direita dele.
"""
from estilo import *
from comum import *


class Cena(CenaHumanim):
    def construct(self):
        e = estado_9()
        self.add(e["raiz"], *e["setas"].values(), *e["nomes"].values(), e["pts"], e["cont_s"], e["pct_s"],
                 e["cont_n"], e["pct_n"], e["regua"], *e["m"].values())

        # Barras e lupa, num movimento só.
        sim, nao = barra("sim"), barra("nao")
        rb = rotulos_barras()
        z = regua_zoom()
        mz = marcas_10()
        pts_s = VGroup(*(e["pts"][i] for i in indices("sim")))
        pts_n = VGroup(*(e["pts"][i] for i in indices("nao")))
        m = e["m"]
        self.play(FadeOut(VGroup(e["raiz"], *e["setas"].values(), *e["nomes"].values(), e["pct_s"], e["pct_n"])),
                  FadeTransform(pts_s, sim), FadeTransform(pts_n, nao),
                  e["cont_s"].animate.set_color(BRANCO).move_to(rb["c_s"]), e["cont_n"].animate.move_to(rb["c_n"]),
                  FadeOut(VGroup(*e["regua"][1:])), ReplacementTransform(e["regua"][0], z[0]), FadeIn(z[1:]),
                  ReplacementTransform(m["todos"], mz["antes"]), ReplacementTransform(m["nao"], mz["nao"]),
                  TransformFromCopy(m["nao"][1], rb["g_n"]), TransformFromCopy(m["sim"][1], rb["g_s"]),
                  ReplacementTransform(m["sim"], mz["sim"]), run_time=0.5)
        self.bring_to_front(mz["antes"], mz["nao"], mz["sim"])

        # "Piorou?": a média sem peso fica acima do 0,34.
        s1, s2, s_nome = conta_sem_peso()
        m35 = marca_sem_peso()
        self.play(FadeIn(s1, shift=UP * 0.2), FadeIn(s2, shift=UP * 0.2), FadeIn(s_nome),
                  FadeIn(m35, shift=UP * 0.3), run_time=0.4)

        # "Os atrasados são só 10%": a barra fininha; as contagens viram os pesos e a média sem peso cai.
        self.ate("atrasados")
        self.play(Indicate(VGroup(sim, rb["g_s"], e["cont_s"]), color=VERMELHO, scale_factor=1.08), run_time=0.5)
        risco = VGroup(riscar(s1), riscar(s2))
        self.ate("10")
        self.play(FadeTransform(e["cont_s"], rb["p_s"]), FadeTransform(e["cont_n"], rb["p_n"]),
                  Create(risco), run_time=0.45)
        self.play(FadeOut(VGroup(s1, s2, s_nome, risco), shift=DOWN * 0.2), FadeOut(m35), run_time=0.3)

        # "pesando": a média ponderada monta termo a termo e fecha em "dá".
        p1, p2, p3, p4, p_nome = conta_ponderada()
        self.ate("pesando")
        self.play(FadeIn(p1, shift=UP * 0.2), run_time=0.3)
        self.ate("tamanho")
        self.play(FadeIn(p2, shift=UP * 0.2), run_time=0.3)
        self.ate("dá")
        self.play(FadeIn(p3, shift=UP * 0.2), FadeIn(p4, shift=UP * 0.2), run_time=0.35)
        self.play(TransformFromCopy(p4[1], mz["pond"][1], path_arc=-0.3), FadeIn(mz["pond"][0], shift=DOWN * 0.3),
                  run_time=0.35)
        self.ate("29")
        self.play(FadeIn(p_nome, shift=UP * 0.15), Indicate(mz["pond"], color=AMARELO, scale_factor=1.2),
                  run_time=min(0.45, self.restante() - 0.05))
        self.completar()
