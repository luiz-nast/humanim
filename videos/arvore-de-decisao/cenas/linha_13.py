"""[CANTO] Idade e estado civil? Em nenhum corte tiram nem 1%.

À direita, a régua ampliada (0,27 a 0,36), com os 30 mil ("antes") no 0,34 e, apagada no 0,29, a pergunta do
atraso ("atraso, tira 15%"): o que um corte bom faz. À esquerda voltam as caixas da linha 1 ("menos de 30?",
"casado?") e viram as colunas inteiras ("idade", "estado civil"): a busca testa todo corte de cada uma. Cada uma
solta uma marca cinza, ligada a ela por uma linha tracejada, que para colada no 0,34; embaixo da caixa, o quanto
o melhor corte tira: 0,2% e 0,1%. Em "nem 1%", as duas piscam em vermelho. Tudo acima do canto.
"""
from estilo import *
from comum import *


class Cena(CenaHumanim):
    def construct(self):
        z = regua_zoom()
        antes_ = marca_antes()
        ref = referencia_atraso()
        antes, _ = candidatos_13(final=False)
        self.add(z, antes_, ref)
        self.play(*(FadeIn(antes[k], scale=0.9) for k in ("idade", "civil")), run_time=0.3)

        # As perguntas viram as colunas inteiras (a borda fica; o texto troca).
        cx, tira = candidatos_13(final=True)
        tri = setinhas_13()
        lig = ligacoes_13(cx, tri)
        for k, palavra in (("idade", "idade"), ("civil", "estado")):
            self.ate(palavra)
            self.play(FadeOut(antes[k][1], scale=0.7), antes[k][0].animate.set_color(AMARELO), run_time=0.15)
            self.play(FadeIn(cx[k][1], scale=1.3), antes[k][0].animate.set_color(AZUL), run_time=0.25)
            self.remove(antes[k][0])
            self.add(cx[k][0])

        # Cada coluna solta a sua marca, ligada a ela, que para no 0,34.
        for k in ("idade", "civil"):
            ini = tri[k].copy().move_to(cx[k].get_right() + RIGHT * 0.25)
            self.ate("em" if k == "idade" else "corte")
            self.play(ReplacementTransform(ini, tri[k]), Create(lig[k]), FadeIn(tira[k], shift=UP * 0.2), run_time=0.5)

        self.ate("nem")
        piscar = [Indicate(tri[k], color=VERMELHO, scale_factor=1.6) for k in tri]
        piscar += [tira[k].animate.set_color(VERMELHO) for k in tira]
        self.play(*piscar, run_time=min(0.6, self.restante() - 0.05))
        self.completar()
