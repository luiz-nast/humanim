"""[CANTO] Tirou 15% da bagunça: é a redução de impureza.

Continua a linha 10. As barras e os passos da conta saem; o resultado fica: "0,29, média ponderada" sobe para o
alto. Na régua ampliada, uma seta amarela grossa desce do 0,34 ao 0,29. Ao lado, a conta: 0,34 − 0,29 = 0,05 e
0,05 ÷ 0,34 ≈ 15% (o exato é 15,2%). Em "bagunça", o 15% cresce: "15% da bagunça". Em "redução de impureza",
esse nome aparece embaixo do 0,05 (a redução de impureza é a diferença, 0,05; os 15% são quanto ela é da
bagunça de antes). Acima do canto; a régua passa à direita dele.
"""
from estilo import *
from comum import *


class Cena(CenaHumanim):
    def construct(self):
        e = estado_10()
        p1, p2, p3, p4, p_nome = e["conta"]
        self.add(e["regua"], e["barras"], *e["rb"].values(), p1, p2, p3, p4, p_nome, *e["m"].values())

        pond, a, nome, b, grande, da = contas_11()
        s = seta_regua()
        self.play(FadeOut(VGroup(e["barras"], *e["rb"].values(), p1, p2, p3, p4[0]), shift=UP * 0.2), run_time=0.25)
        self.play(ReplacementTransform(p4[1], pond[0]), ReplacementTransform(p_nome, pond[1]), GrowArrow(s),
                  run_time=0.35)
        self.ate("15")
        self.play(FadeIn(a, shift=UP * 0.2), run_time=0.4)
        self.play(FadeIn(b, shift=UP * 0.2), run_time=0.4)
        self.ate("bagunça")
        self.play(ReplacementTransform(b[4].copy(), grande), FadeIn(da, shift=UP * 0.2), run_time=0.45)
        self.ate("redução")
        self.play(FadeIn(nome, shift=UP * 0.2), Indicate(a[4], color=AMARELO, scale_factor=1.3),
                  Indicate(s, scale_factor=1.1), run_time=min(0.5, self.restante() - 0.05))
        self.completar()
