"""[ANIM] Olha 30 mil clientes de cartão de Taiwan, 2005: 22% deram calote no mês seguinte.

As três perguntas sobem e somem. Caem 300 pontos cinza (1 ponto = 100 clientes). Em "Taiwan", no alto, "Taiwan,
2005" e, logo embaixo, pequeno e em cinza, a fonte. Em "22", os 66 pontos de calote ficam vermelhos enquanto o
contador sobe até 6.636 de 30.000; os outros 234 ficam verdes. O contador fica inteiro na tela por 1 s e, em
"calote", desce pequeno para baixo e no lugar dele entra "22%"; em "mês", "mês seguinte" ao lado.
"""
from estilo import *
from comum import *


class Cena(CenaHumanim):
    def construct(self):
        cart, frase = titulo_prever()
        cx = perguntas(acesa=2)
        self.add(cart, frase, cx)

        pts = nuvem(**NUVEM_2, cor=False)
        legenda = VGroup(Dot(radius=NUVEM_2["raio"] * 1.3, color=CINZA), rotulo("= 100 clientes", tamanho=G)).arrange(
            RIGHT, buff=0.25).move_to(ponto(0, Y_LEGENDA_2))
        self.play(FadeOut(VGroup(cart, frase, cx), shift=UP * 1.2), run_time=0.45)
        self.play(LaggedStart(*(FadeIn(p, shift=DOWN * 1.5) for p in pts), lag_ratio=0.004), run_time=1.0)
        self.ate("clientes")
        self.play(FadeIn(legenda, shift=UP * 0.2), run_time=0.4)

        onde = rotulo("Taiwan, 2005", tamanho=TITULO).move_to(ponto(0, Y_TITULO_2))
        fonte = rotulo("dados: Yeh, UCI", cor=CINZA, tamanho=PEQUENO).move_to(ponto(0, Y_FONTE_2))
        self.ate("Taiwan")
        self.play(Write(onde), FadeIn(fonte), run_time=0.6)

        # 22%: os pontos de calote acendem e o contador sobe junto.
        vermelhos = [p for p, c in zip(pts, NUVEM_COR) if c == VERMELHO]
        verdes = [p for p, c in zip(pts, NUVEM_COR) if c == VERDE]
        de = rotulo(f"de {br(N_TOTAL, 0)}", tamanho=G)
        VGroup(Integer(N_CALOTE, font_size=80), de).arrange(RIGHT, buff=0.3, aligned_edge=DOWN).move_to(
            ponto(0, Y_CONTADOR_2))  # posição final; o contador cresce para a esquerda até ela
        cont = Integer(0, font_size=80, color=VERMELHO, group_with_commas=True)
        cont.add_updater(lambda m: m.next_to(de, LEFT, buff=0.3, aligned_edge=DOWN))
        cores = legenda_cores().move_to(ponto(0, Y_CORES_2))
        self.ate("22")
        self.add(cont)
        self.play(FadeIn(de), FadeIn(cores[1]),
                  ChangeDecimalToValue(cont, N_CALOTE),
                  LaggedStart(*(p.animate.set_color(VERMELHO).scale(1.25) for p in vermelhos), lag_ratio=0.03),
                  run_time=0.6)
        cont.clear_updaters()
        self.play(LaggedStart(*(p.animate.set_color(VERDE) for p in verdes), lag_ratio=0.002), FadeIn(cores[0]),
                  *(p.animate.scale(1 / 1.25) for p in vermelhos), run_time=0.35)

        # Em "calote": a fração desce, pequena, e o 22% entra no lugar dela; "mês seguinte" ao lado.
        pct = rotulo(f"{PCT_CAL_RAIZ}%", cor=VERMELHO, tamanho=100)
        quando = rotulo("mês seguinte", tamanho=44)
        VGroup(pct, quando).arrange(RIGHT, buff=0.35, aligned_edge=DOWN).move_to(ponto(0, Y_CONTADOR_2))
        fracao = conta(br(N_CALOTE, 0), " de ", br(N_TOTAL, 0), tamanho=PQ, cores={0: VERMELHO}).move_to(
            ponto(0, Y_FRACAO_2))
        self.ate("calote")
        self.play(FadeTransform(VGroup(cont, de), fracao), run_time=0.3)
        self.play(FadeIn(pct, scale=1.4), run_time=0.3)
        self.ate("mês")
        self.play(FadeIn(quando, shift=LEFT * 0.2), run_time=min(0.4, self.restante() - 0.05))
        self.completar()
