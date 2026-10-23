"""Bloco 5 (linhas 10 e 11): por que a média. Só o que é deste bloco; o resto vem do comum.py.

- Linha 10: o zoom nas 100 curtas (plano_zoom do comum.py numa caixa que deixa tudo acima do canto), o centro tirado
  1 e 2 min da média na espera (losango, contorno cinza na média, setinha "1 min"/"2 min"), as linhas de cada curta
  até o centro (amarela se esticou, branca se encolheu: comparado com a média, em minutos) e as contas do
  para_tela.por_que_a_media em três filas no alto (A "3.456 + 100 × 1² = 3.556", B "3.456 + 100 × 2²",
  C "= 3.456 + 400 = 3.856", com C encostada à direita da A). fim_linha_10(): o último quadro da 10 e o 1º da 11.
- Linha 11: Curva(): a soma das curtas com o centro d min fora da média, calculada nos dados (soma_em), que é
  3.456 + 100 × d²; eixo em pé de 3.400 a 3.900 com zigue-zague no pé. Tudo acima do canto.
"""
from estilo import *
from comum import *
from comum import _confere

PM = R["por_que_a_media"]["curto"]
TM = T["por_que_a_media"]
MEDIA = CENTROS[5][0]  # (2,0943; 54,75): a média das 100 curtas (o centro final azul)
CURTAS = [i for i in range(N) if GRUPOS[5][i] == 0]
NC = PM["n"]  # 100


def soma_em(d, dd=0.0):
    """Soma dos quadrados das curtas com o centro d min acima da média na espera (dd na duração), nos dados."""
    c0, c1 = MEDIA[0] + dd, MEDIA[1] + d
    return sum((DUR[i] - c0) ** 2 + (ESP[i] - c1) ** 2 for i in CURTAS)


S0 = soma_em(0)  # 3.456,18 min²
_confere(len(CURTAS) == NC == 100 and abs(S0 - PM["soma_com_centro_na_media"]) < 0.5, "100 curtas, soma 3.456")
_confere(f"{br(S0)} + {NC} × 1² = {br(soma_em(1))}" == TM["centro_1_min_para_cima_na_espera"], "3.456 + 100 × 1²")
_confere(f"{br(S0)} + {NC} × 2² = {br(soma_em(2))}" == TM["centro_2_min_na_espera"], "3.456 + 100 × 2² = 3.856")
_confere(br(soma_em(-1)) == br(soma_em(1)) and br(NC * 2 ** 2) == br(PM["deslocado"]["espera_mais_2"]["n_vezes_d2"]),
         "simetria e 400")
_confere(f"{br(PM['parte_da_duracao'])} (duração) + {br(PM['parte_da_espera'])} (espera) = {br(S0)}" == TM["partes"],
         "15 + 3.441 = 3.456")

# ---------------------------------------------------------------- linha 10: o zoom nas curtas

ZOOM = (-2.75, -1.2, 2.75, 2.7)  # caixa do plano_zoom: 1 min em pé = 0,15; números do eixo deitado em y −1,65
YC = (5.25, 4.55, 3.85)  # filas das contas na linha 10 (o "espera (min)" do zoom fica em y 3,15)
YC_ALTO = (5.3, 4.77, 4.24)  # e na linha 11, encolhidas (PEQUENO)
X_ROT = 0.8  # coluna vazia à direita da nuvem (duração > 3 min): "100 curtas", "média", "(2,1; 54,8)"


def zoom():
    """plano_zoom() na caixa ZOOM, com "duração (min)" dentro, no canto vazio de baixo à direita (fora do gráfico
    ficaria abaixo do limite do canto)."""
    pz = plano_zoom(ZOOM)
    pz.nome_x.move_to([pz.dir - 0.05 - pz.nome_x.width / 2, pz.base + 0.38, 0])
    return pz


def moldura(pl, cor=AMARELO):
    """O trecho do plano principal que o zoom amplia (duração 1,5–4, espera 42–68): de onde a moldura sai."""
    a, b = pl.p(1.5, 42), pl.p(4.0, 68)
    return Rectangle(width=b[0] - a[0], height=b[1] - a[1], color=cor, stroke_width=4).move_to((a + b) / 2)


def moldura_zoom(cor=AMARELO):
    """A moldura crescida: a caixa do zoom."""
    esq, base, dir_, topo = ZOOM
    return Rectangle(width=dir_ - esq, height=topo - base, color=cor, stroke_width=4).move_to(
        [(esq + dir_) / 2, (base + topo) / 2, 0])


def centro_em(pz, d=0):
    """O losango azul d min acima da média, na espera."""
    return losango(AZUL).move_to(pz.p(MEDIA[0], MEDIA[1] + d))


def fantasma(pz):
    """Contorno cinza do losango na média: onde o centro estava (fica atrás do losango que andou)."""
    return Square(side_length=0.36).rotate(PI / 4).set_fill(FUNDO, 0).set_stroke(CINZA, 3).move_to(
        pz.p(*MEDIA)).set_z_index(2)


def distancia(i, d):
    """Distância (min) da erupção i ao centro d min acima da média: a conta de verdade, nas duas medidas."""
    return np.hypot(DUR[i] - MEDIA[0], ESP[i] - MEDIA[1] - d)


def linhas_zoom(pz, d=0, cores=True):
    """Uma linha de cada curta até o centro d min acima da média. d = 0 (ou cores=False): cinza fina, como as
    linhas_ate do comum.py; senão amarela se ficou mais comprida que até a média, branca se encolheu."""
    c = pz.p(MEDIA[0], MEDIA[1] + d)
    g = VGroup()
    for i in CURTAS:
        if d == 0 or not cores:
            cor, w, op = CINZA, 1.5, 0.7
        elif distancia(i, d) > distancia(i, 0):
            cor, w, op = AMARELO, 2.5, 0.9
        else:
            cor, w, op = BRANCO, 2, 0.8
        g.add(Line(pz.pos(i), c, stroke_width=w, color=cor, stroke_opacity=op))
    return g.set_z_index(-1)


def regua(pz, d):
    """A setinha "d min" logo à direita do losango, do nível da média ao nível do centro (1 min = 0,15 na tela:
    pequena de verdade; sem tracinho na base, que com a ponta parecia um "±"). Fundo preto atrás, por cima das
    erupções."""
    x = pz.p(*MEDIA)[0] + 0.45
    y0, y1 = pz.p(*MEDIA)[1], pz.p(MEDIA[0], MEDIA[1] + d)[1]
    ponta = Triangle().set_fill(AMARELO, 1).set_stroke(width=0).stretch_to_fit_width(0.22).stretch_to_fit_height(0.14)
    ponta.move_to([x, y1 - 0.07, 0])
    haste = Line([x, y0, 0], [x, max(y0 + 0.01, y1 - 0.1), 0], stroke_width=5, color=AMARELO)
    t = Text(f"{d} min", font_size=PQ, color=AMARELO)
    t.move_to([x + 0.17 + t.width / 2, (y0 + y1) / 2, 0])
    fundo = BackgroundRectangle(VGroup(haste, ponta, t), color=FUNDO, fill_opacity=0.9, buff=0.07)
    return VGroup(fundo, haste, ponta, t).set_z_index(4)


def rotulos_zoom(pz):
    """"100 curtas" (azul) no alto à direita, na fila do "espera (min)" (dentro do plano, as linhas das curtas da
    direita passariam por cima), e "média" e "(2,1; 54,8)" na coluna vazia à direita da nuvem, em volta do nível da
    média. VGroup(curtas, media, coordenada)."""
    ym = pz.p(*MEDIA)[1]
    curtas = Text(f"{NC} curtas", font_size=NOME, color=AZUL)
    media = Text("média", font_size=NOME, color=BRANCO)
    xy = Text(coord(0, 5), font_size=PQ, color=BRANCO)
    curtas.move_to([DIR - curtas.width / 2, pz.nome_y.get_center()[1], 0])
    for t, y in ((media, ym + 0.27), (xy, ym - 0.27)):
        t.move_to([X_ROT + t.width / 2, y, 0])
    return VGroup(curtas, media, xy)


def tres_no_alto():
    """O "3.456" sozinho no alto, centrado (FC, azul): a soma das curtas com o centro na média."""
    return Text(br(S0), font_size=FC, color=AZUL).move_to([0, YC[0], 0])


def partes():
    """"15 duração + 3.441 espera", pequeno e cinza, embaixo do 3.456 (fila 2)."""
    return conta(br(PM["parte_da_duracao"]), " duração", " + ", br(PM["parte_da_espera"]), " espera", tamanho=PQ,
                 cor=CINZA).move_to([0, YC[1], 0])


def contas(alto=False):
    """As três filas: A "3.456 + 100 × 1² = 3.556", B "3.456 + 100 × 2²" (alinhada à esquerda com a A) e
    C "= 3.456 + 400 = 3.856" (encostada à direita da A: 3.556 e 3.856 um embaixo do outro). Partes: A [0] 3.456,
    [2] "100 × 1²" (amarelo), [4] 3.556; B [2] "100 × 2²" (amarelo); C [1] 3.456, [3] 400, [5] 3.856.
    alto=True: as da linha 11, em PEQUENO, mais juntas. O 400 sai branco: a cena acende."""
    t, ys = (PEQUENO, YC_ALTO) if alto else (PQ, YC)
    a = conta(br(S0), " + ", f"{NC} × 1²", " = ", br(soma_em(1)), tamanho=t, cores={0: AZUL, 2: AMARELO})
    b = conta(br(S0), " + ", f"{NC} × 2²", tamanho=t, cores={0: AZUL, 2: AMARELO})
    c = conta("= ", br(S0), " + ", br(NC * 2 ** 2), " = ", br(soma_em(2)), tamanho=t, cores={1: AZUL})
    a.move_to([0, ys[0], 0])
    b.move_to([a.get_left()[0] + b.width / 2, ys[1], 0])
    c.move_to([a.get_right()[0] - c.width / 2, ys[2], 0])
    return a, b, c


def fim_linha_10():
    """O último quadro da linha 10 (e o 1º da 11): o zoom com o centro 2 min acima da média, as linhas coloridas, a
    setinha "2 min", os rótulos e as três contas, com o 400 amarelo."""
    pz = zoom()
    a, b, c = contas()
    c[3].set_color(AMARELO)
    return {"eixos": pz.eixos, "linhas": linhas_zoom(pz, 2), "pontos": pz.grupo_pontos, "fantasma": fantasma(pz),
            "centro": centro_em(pz, 2), "regua": regua(pz, 2), "rotulos": rotulos_zoom(pz), "a": a, "b": b, "c": c}


# ---------------------------------------------------------------- linha 11: a curva em U


class Curva:
    """A soma das 100 curtas com o centro d min fora da média, na espera (linha 11), acima do canto. d de −2 a 2 em
    x −1,45..3,25 (1,175 por min; d = 0 em x 0,9); soma de 3.400 (y −0,65) a 3.900 (y 2,35), eixo em pé em x −1,9;
    o eixo deitado fica em y −0,9 e o zigue-zague entre ele e o 3.400 (não começa no zero). A curva é soma_em(d) calculada nos dados, ponto a ponto.
    .eixos (linhas, zigue-zague, marcas, números −2..2, "soma (min²)" no alto à esquerda, "d = minutos fora da média"
    embaixo), .curva, .pontos [5 Dot] (d = −2..2), .valores [3 Text] no eixo em pé ("3.456", "3.556", "3.856") e
    .guias [3 DashedLine] do eixo até o ponto da esquerda (d = 0, −1, −2), .formula "3.456 + 100 × d²" ([0] azul,
    [2] 100, [4] d²) com .erupcoes cinza sob o 100, .media ("média" amarelo, dentro do U, sobre o fundo)."""

    EX, X0, X1, BASE, TOPO, EIXO_X = -1.9, -1.45, 3.25, -0.65, 2.35, -0.9
    S_MIN, S_MAX = 3400, 3900

    def x(self, d):
        return self.X0 + (d + 2) / 4 * (self.X1 - self.X0)

    def y(self, s):
        return self.BASE + (s - self.S_MIN) / (self.S_MAX - self.S_MIN) * (self.TOPO - self.BASE)

    def p(self, d):
        return np.array([self.x(d), self.y(soma_em(d)), 0.0])

    def __init__(self):
        _confere(self.S_MIN < S0 and soma_em(2) < self.S_MAX, "a curva cabe entre 3.400 e 3.900")
        ex, b = self.EX, self.EIXO_X
        eixo_x = Line([ex, b, 0], [self.X1 + 0.2, b, 0], stroke_width=EIXO, color=CINZA)
        zigue = VMobject(stroke_width=EIXO, color=CINZA).set_points_as_corners(
            [[ex, b, 0], [ex, b + 0.03, 0], [ex - 0.13, b + 0.07, 0], [ex + 0.13, b + 0.12, 0], [ex - 0.13, b + 0.17, 0],
             [ex + 0.13, b + 0.22, 0], [ex, b + 0.25, 0], [ex, self.TOPO + 0.1, 0]])
        ds = (-2, -1, 0, 1, 2)
        marcas = VGroup(*(Line([self.x(d), b - 0.09, 0], [self.x(d), b + 0.09, 0]) for d in ds)).set_stroke(CINZA, EIXO)
        nums = VGroup(*(Text(br(d), font_size=PQ, color=BRANCO).move_to([self.x(d), b - 0.45, 0]) for d in ds))
        nome_y = Text("soma (min²)", font_size=NOME, color=BRANCO)
        nome_y.move_to([ESQ + nome_y.width / 2, 2.85, 0])
        self.nome_x = conta("d", " = ", "minutos fora da média", tamanho=PQ)
        self.nome_x.move_to([min(DIR - self.nome_x.width / 2, 0.75), -1.83, 0])
        self.eixos = VGroup(eixo_x, zigue, marcas, nums, nome_y, self.nome_x)
        self.curva = ParametricFunction(lambda d: self.p(d), t_range=[-2, 2, 0.05], color=AZUL,
                                        stroke_width=ESPESSURA)
        self.pontos = [Dot(self.p(d), radius=0.1, color=BRANCO).set_z_index(2) for d in ds]
        self.valores, self.guias = [], []
        for d in (0, -1, -2):
            yv = self.p(d)[1]
            t = Text(br(soma_em(d)), font_size=PQ, color=BRANCO)
            self.valores.append(t.move_to([ex - 0.16 - t.width / 2, yv, 0]))
            self.guias.append(DashedLine([ex, yv, 0], self.p(d), dash_length=0.1, stroke_width=2, color=CINZA))
        self.formula = conta(br(S0), " + ", str(NC), " × ", "d²", tamanho=FC, cores={0: AZUL})
        self.formula.move_to([0.85, 3.5, 0])
        self.erupcoes = Text("erupções", font_size=PQ, color=CINZA)
        self.erupcoes.move_to([self.formula[2].get_center()[0], 2.95, 0])
        self.media = Text("média", font_size=NOME, color=AMARELO).move_to([self.x(0), self.y(S0) + 0.62, 0])
        self.tudo = VGroup(self.eixos, self.curva, *self.pontos, *self.valores, *self.guias)
