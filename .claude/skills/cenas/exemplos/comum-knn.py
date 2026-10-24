"""KNN: o vocabulário visual comum a todas as linhas (posição, tamanho e cor fixos; nada depende de tempo).

CONTRATO (tudo em unidades Manim; o canto de quem apresenta é x < −0,44 e y < −2,37; desenhe acima de y = −2,07)
  Tamanhos: G 52 (rótulo principal), FC 48 (contas), PQ 40 (números de eixo, créditos em cinza). Nada menor que PQ.
  Cores: COR["Adélia"] LARANJA, COR["Gentoo"] AZUL, COR["Barbicha"] ROXO; o misterioso é BRANCO.
  Dados: PONTOS {linha_csv: (espécie, bico, peso)} com os 342; M = 320 (o misterioso, 50,9 mm, 3.550 g);
    VIZ_CRU [39, 87, 28, 107, 74] (5 Adélias de 3.550 g), VIZ_Z [280, 322, 287, 304, 312] (5 Barbichas);
    T = para_tela de resultados.json (use os textos dele para a tela).
  Faixas fixas:
    topo        y ≈ 5,2   título do dado (linha 2) e, da linha 5 ao fim, rotulo_knn() à esquerda (x −3,45 a −0,6);
                          a metade direita do topo (x 0 a 3,45) fica livre para fórmula pequena / cartões mínimos.
    faixa à dir x −0,15 a 3,45, y −2,45 a −4,6 (ao lado do canto, vale em [CANTO]): contador e legenda (linhas 2–5),
                          placar (6 e 14). Uma coisa por vez.
  plano_cru(cores=True) -> Plano. Bico 32–60 mm em x −1,95..3,2; peso 2.700–6.300 g em y −1,25..3,6.
      .eixos (linhas, marcas, "32" "60" "2.700" "6.300", "bico (mm)" embaixo, "peso (g)" dentro, no alto à esq.),
      .pontos {linha: Dot} só os 341 (sem o 320), .grupo_pontos VGroup deles, .misterioso (Dot branco, r 0,1),
      .interrogacao ("?" embaixo à direita dele, num vão sem pontos), .p(bico, peso) -> ponto na tela,
      .pos(linha) -> ponto de um pinguim, .tudo VGroup de tudo. cores=False: os 341 em CINZA.
  plano_z(cores=True) -> Plano igual, em desvios (−2,5 a +3 nos dois eixos, MESMA escala nos dois: 0,7 por desvio),
      quadrado x −1,4..2,45, y −0,25..3,6; "peso (desvios)" em cima (y 4,1), "bico (desvios)" embaixo (y −1,25);
      números −2,5 (no canto, vale para os dois), 0 e +3. formula_z() embaixo dele (y −1,98):
      "z = (x − média) ÷ desvio" com [2] = "− média", [4] = "÷ desvio". Não sobra fila: "padronizar" vai no topo.
  Plano(x0, x1, y0, y1, caixa=(esq, base, dir, topo), ...) -> o mesmo desenho com outro intervalo (zoom da linha 6:
      um Plano novo com o trecho ampliado, nunca escalar o plano por cima dos números).
  linhas_ate(plano, linhas, cor=AMARELO, espessura=4) -> VGroup de Line do misterioso até cada pinguim.
  aneis(plano, linhas) -> VGroup de anéis amarelos (r 0,14) em volta dos pinguins.
  titulo_dados() -> VGroup("Palmer, Antártida" y 5,33, "2007–2009" y 4,7, cinza "dados: Gorman et al., 2014" y 4,12)
      (a frase numa fila só não cabe com letra legível).
  rotulo_knn() -> "KNN · k = 5" numa moldura, no topo à esquerda (fica da linha 5 ao fim).
  contador(n=0) -> Integer grande na faixa à direita (em cima); soma_342() -> conta "341 + ? = 342" embaixo dele.
  legenda() -> VGroup de 3 linhas (letra 42, x −0,1..3,3) (bolinha + "Adélia 151" / "Gentoo 123" / "Barbicha 68") na faixa à direita.
  placar(("Adélia", 5), ("Barbicha", 0)) -> caixa x −0,2..3,48 no alto da faixa, duas filas "5 Adélia" / "0 Barbicha"
      (o 1º é quem ganhou): VGroup(caixa, nome1, n1, nome2, n2), .n1/.n2 Integer (troque no pouso), .vaga
      (onde pousa o ✗/✓); xis(centro, lado) e certo(centro, lado) desenham ✗ vermelho e ✓ verde (a Lato não tem).
  pinguim(cor, altura) -> desenho simples (corpo, barriga branca, olhos, bico e pés amarelos), centrado na origem.
  abertura() -> dict da linha 1 (pinguim cinza, "?", "50,9 mm" y 0,42, "3.550 g" y −0,45, crédito cinza em 2 filas até y −1,9); balao() -> "IA: Adélia" + ✗.
      fim_linha_1() -> o mesmo dict com os números em AMARELO e o balão: é o 1º quadro da linha 2.
  fim_linha_2() -> (plano_cru colorido, titulo_dados(), legenda()): o último quadro da 2 e o 1º da 3.
  cartao(cor, linha1, linha2) -> cartão 3,0 × 2,9 (moldura na cor, pinguim na cor, dois textos G):
      .caixa .bicho .l1 .l2; posições CARTAO_ESQ (−1,75; 3,05) e CARTAO_DIR (1,75; 3,05), abaixo do rótulo KNN;
      contas embaixo, em filas de y 1,1 até −1,8 (FC 48 cabe ~14 caracteres em meia tela, ~24 na tela toda).
  reguas() -> (bico, peso): duas Regua de 6,6 de comprimento (x −3,3..3,3), bico 32–60 com base em y 2,85,
      peso 2.700–6.300 com base em y −0,35; 342 pontos empilhados em cima (.pontos {linha: Dot}, o 320 roxo), nome
      em cima à direita (onde as pilhas são baixas), "32"/"60" e "2.700"/"6.300" nas pontas embaixo. Regua.p(valor) -> ponto na base; Regua.y1, Regua.y2:
      as duas filas de rótulos embaixo da base. .tudo VGroup.
  trecho(regua, de, ate, cor, texto, fila=1) -> VGroup(barra grossa na base, rótulo na fila 1 ou 2 embaixo).
  marca(regua, valor, texto, cor, fila=1) -> VGroup(tracinho, rótulo) embaixo da base.
  trechos_desvio() -> (trecho branco "5,45 mm" a partir da média do bico, trecho "801 g" a partir da do peso).
  fim_linha_12() -> (bico, peso, trecho_bico, trecho_peso, rotulo_knn()): o último quadro da 12 e o 1º da 13.
"""
import json
from pathlib import Path

from estilo import *

# ---------------------------------------------------------------- dados

DADOS = Path(__file__).resolve().parent.parent / "dados"
R = json.loads((DADOS / "resultados.json").read_text(encoding="utf-8"))
T = R["para_tela"]
PONTOS = {l: (esp, b, m) for l, esp, b, m in R["pontos_2_medidas"]["linhas"]}
M = R["pinguim_misterioso"]["linha_csv"]  # 320
M_BICO, M_PESO = PONTOS[M][1], PONTOS[M][2]  # 50,9 mm e 3.550 g
VIZ_CRU = [v["linha_csv"] for v in R["pinguim_misterioso"]["cru"]["vizinhos"]]
VIZ_Z = [v["linha_csv"] for v in R["pinguim_misterioso"]["padronizado"]["vizinhos"]]
_E = R["estatisticas_342"]
MEDIA_BICO, DESV_BICO = _E["media_bico_mm"], _E["desvio_bico_mm"]
MEDIA_PESO, DESV_PESO = _E["media_massa_g"], _E["desvio_massa_g"]


def _confere(cond, msg):
    if not cond:
        raise ValueError(f"comum.py: {msg} (os números de dados/ mudaram?)")


_confere(len(PONTOS) == 342 and (M_BICO, M_PESO) == (50.9, 3550), "342 pinguins e o misterioso 50,9 mm / 3.550 g")
_confere(VIZ_CRU == [39, 87, 28, 107, 74] and VIZ_Z == [280, 322, 287, 304, 312], "os vizinhos")
_confere(T["desvios"] == {"bico": f"{br(DESV_BICO, 2)} mm", "massa": f"{br(DESV_PESO)} g"}, "desvios 5,45 e 801")

COR = {"Adélia": LARANJA, "Gentoo": AZUL, "Barbicha": ROXO}
ORDEM = ["Adélia", "Gentoo", "Barbicha"]

G = 52  # rótulo principal (maiúscula de ~70 px no vídeo)
FC = 48  # contas
PQ = 40  # o menor que usamos: números de eixo, créditos em cinza
EIXO = 4  # traço dos eixos e réguas


def z_bico(b):
    return (b - MEDIA_BICO) / DESV_BICO


def z_peso(m):
    return (m - MEDIA_PESO) / DESV_PESO


# ---------------------------------------------------------------- faixas fixas

Y_TOPO = 5.15  # título / rótulo KNN
ESQ = -3.45  # margem esquerda dos textos
FAIXA = (-0.15, -4.6, 3.45, -2.45)  # à direita do canto: esq, base, dir, topo
FAIXA_CENTRO = np.array([(FAIXA[0] + FAIXA[2]) / 2, (FAIXA[1] + FAIXA[3]) / 2, 0.0])


def xis(centro=ORIGIN, lado=0.42, cor=VERMELHO):
    """✗ desenhado (a Lato não tem o caractere)."""
    c, h = np.array(centro, dtype=float), lado / 2
    return VGroup(Line(c + [-h, -h, 0], c + [h, h, 0]), Line(c + [-h, h, 0], c + [h, -h, 0])).set_stroke(
        cor, width=ESPESSURA + 2)


def certo(centro=ORIGIN, lado=0.46, cor=VERDE):
    """✓ desenhado."""
    c, h = np.array(centro, dtype=float), lado / 2
    return VMobject().set_points_as_corners([c + [-h, 0, 0], c + [-h * 0.25, -h * 0.8, 0], c + [h, h * 0.9, 0]]
                                            ).set_stroke(cor, width=ESPESSURA + 2)


def titulo_dados():
    """Três filas no alto (a frase inteira não cabe numa fila com letra legível): lugar, anos e, em cinza, a fonte."""
    lugar = Text("Palmer, Antártida", font_size=G - 4, color=BRANCO).move_to([0, 5.33, 0])
    anos = Text("2007–2009", font_size=G - 8, color=BRANCO).move_to([0, 4.7, 0])
    fonte = Text("dados: Gorman et al., 2014", font_size=PQ, color=CINZA).move_to([0, 4.12, 0])
    return VGroup(lugar, anos, fonte)


def rotulo_knn():
    t = Text("KNN · k = 5", font_size=G, color=BRANCO)
    caixa = RoundedRectangle(width=t.width + 0.45, height=t.height + 0.35, corner_radius=0.15,
                             stroke_color=AMARELO, stroke_width=4)
    g = VGroup(caixa, t)
    t.move_to(caixa)
    g.move_to([ESQ + caixa.width / 2, Y_TOPO, 0])
    return g


def contador(n=0):
    c = Integer(n, font_size=96, color=BRANCO)
    c.move_to(FAIXA_CENTRO + [0, 0.45, 0])
    return c


def soma_342():
    return conta("341", " + ", "?", " = ", "342", tamanho=PQ, cores={2: BRANCO}).move_to(FAIXA_CENTRO + [0, -0.6, 0])


def legenda(contagem=True):
    linhas = VGroup()
    for esp in ORDEM:
        texto = f"{esp} {T['contagem'][esp]}" if contagem else esp
        linhas.add(VGroup(Dot(radius=0.13, color=COR[esp]), Text(texto, font_size=42, color=COR[esp])).arrange(
            RIGHT, buff=0.22))
    linhas.arrange(DOWN, buff=0.28, aligned_edge=LEFT)
    linhas.move_to(FAIXA_CENTRO).align_to([FAIXA[0] + 0.05, 0, 0], LEFT)
    return linhas


def placar(cima, baixo):
    """Placar de votos em duas linhas: placar(("Adélia", 5), ("Barbicha", 0)). O 1º é quem ganhou."""
    esq, base, dir_, topo = FAIXA
    esq, dir_ = -0.2, 3.48
    caixa = RoundedRectangle(width=dir_ - esq, height=1.75, corner_radius=0.18, stroke_color=CINZA, stroke_width=4)
    caixa.move_to([(esq + dir_) / 2, topo - 0.05 - 0.875, 0])
    g = VGroup(caixa)
    for i, (nome, n) in enumerate((cima, baixo)):
        y = caixa.get_top()[1] - 0.47 - 0.8 * i
        num = Integer(n, font_size=64, color=BRANCO).move_to([esq + 0.37, y, 0])
        t = Text(nome, font_size=G - 10, color=COR[nome])
        t.move_to([esq + 0.75 + t.width / 2, y, 0])
        g.add(t, num)
    g.vaga = np.array([esq + 3.3, caixa.get_center()[1], 0])  # onde pousa o ✗ ou o ✓ (lado 0,42)
    g.nome1, g.n1, g.nome2, g.n2 = g[1], g[2], g[3], g[4]
    return g


# ---------------------------------------------------------------- o pinguim desenhado

def pinguim(cor=CINZA, altura=2.6):
    corpo = Ellipse(width=1.55, height=2.3).set_fill(cor, 1).set_stroke(width=0)
    asas = VGroup(*(Ellipse(width=0.4, height=1.2).set_fill(cor, 1).set_stroke(width=0).rotate(a).move_to(
        [x, -0.15, 0]) for x, a in ((-0.78, -0.35), (0.78, 0.35))))
    barriga = Ellipse(width=1.05, height=1.6).set_fill(BRANCO, 1).set_stroke(width=0).move_to([0, -0.3, 0])
    olhos = VGroup(*(VGroup(Circle(radius=0.13).set_fill(BRANCO, 1).set_stroke(width=0),
                            Circle(radius=0.065).set_fill(FUNDO, 1).set_stroke(width=0).shift([0.02 * s, 0, 0])
                            ).move_to([0.24 * s, 0.72, 0]) for s in (-1, 1)))
    bico = Triangle().set_fill(AMARELO, 1).set_stroke(width=0).rotate(PI).stretch_to_fit_width(0.32).stretch_to_fit_height(
        0.26).move_to([0, 0.46, 0])
    pes = VGroup(*(Ellipse(width=0.45, height=0.2).set_fill(AMARELO, 1).set_stroke(width=0).move_to([0.3 * s, -1.15, 0])
                   for s in (-1, 1)))
    g = VGroup(pes, asas, corpo, barriga, olhos, bico)
    g.scale(altura / g.height).move_to(ORIGIN)
    return g


# Linha 1: pinguim no alto, "?" ao lado, os dois números e o crédito embaixo; tudo acima do canto.
PINGUIM_L1 = np.array([-1.25, 2.55, 0])


def abertura():
    bicho = pinguim(CINZA, 3.0).move_to(PINGUIM_L1)
    q = Text("?", font_size=200, color=BRANCO, weight=BOLD).move_to([1.45, 2.65, 0])
    bico_txt = Text(T["misterioso"]["bico"], font_size=64, color=BRANCO).move_to([0, 0.42, 0])
    peso_txt = Text(T["misterioso"]["massa"], font_size=64, color=BRANCO).move_to([0, -0.45, 0])
    credito = VGroup(Text("pinguim real", font_size=PQ, color=CINZA), Text("ilha Dream, 2008", font_size=PQ, color=CINZA)
                     ).arrange(DOWN, buff=0.12).move_to([0, -1.5, 0])  # numa fila só não cabe com letra legível
    return {"pinguim": bicho, "interrogacao": q, "bico": bico_txt, "peso": peso_txt, "credito": credito}


def balao():
    t = Text("IA: Adélia", font_size=G, color=BRANCO)
    x = xis(lado=0.45)
    VGroup(t, x).arrange(RIGHT, buff=0.3)
    caixa = RoundedRectangle(width=t.width + x.width + 0.9, height=1.0, corner_radius=0.25, stroke_color=BRANCO,
                             stroke_width=4).set_fill(FUNDO, 1)
    VGroup(t, x).move_to(caixa)
    g = VGroup(caixa, t, x).move_to([1.15, 4.85, 0])
    rabo = Polygon(caixa.get_corner(DL) + [0.5, 0.02, 0], caixa.get_corner(DL) + [1.05, 0.02, 0],
                   PINGUIM_L1 + [0.35, 1.55, 0]).set_fill(FUNDO, 1).set_stroke(BRANCO, 4)
    tampa = Line(caixa.get_corner(DL) + [0.53, 0, 0], caixa.get_corner(DL) + [1.02, 0, 0]).set_stroke(FUNDO, 6)
    return VGroup(rabo, caixa, tampa, t, x)


def fim_linha_1():
    a = abertura()
    a["bico"].set_color(AMARELO)
    a["peso"].set_color(AMARELO)
    a["balao"] = balao()
    return a


# ---------------------------------------------------------------- o plano

class Plano:
    """Plano bico × peso desenhado à mão (eixos no canto inferior esquerdo, números só nas pontas)."""

    def __init__(self, x0, x1, y0, y1, caixa, fx=lambda b: b, fy=lambda m: m, nome_x="bico (mm)",
                 nome_y="peso (g)", numeros_x=None, numeros_y=None, marcas_x=(), marcas_y=(), cores=True,
                 raio=0.058, so=None, nome_y_dentro=False, nome_x_abaixo=False):
        self.x0, self.x1, self.y0, self.y1 = x0, x1, y0, y1
        self.esq, self.base, self.dir, self.topo = caixa
        self.fx, self.fy = fx, fy
        o = self.canto = np.array([self.esq, self.base, 0])
        eixo_x = Line(o, [self.dir + 0.1, self.base, 0], stroke_width=EIXO, color=CINZA)
        eixo_y = Line(o, [self.esq, self.topo + 0.1, 0], stroke_width=EIXO, color=CINZA)
        marcas = VGroup(*(Line(self._x(v) + [0, -0.09, 0], self._x(v) + [0, 0.09, 0]) for v in marcas_x),
                        *(Line(self._y(v) + [-0.09, 0, 0], self._y(v) + [0.09, 0, 0]) for v in marcas_y)).set_stroke(
            CINZA, EIXO)
        nums = VGroup()
        for v, t in (numeros_x or {}).items():
            nums.add(Text(t, font_size=PQ, color=BRANCO).move_to(self._x(v) + [0, -0.48, 0]))
        for v, t in (numeros_y or {}).items():
            n = Text(t, font_size=PQ, color=BRANCO)
            nums.add(n.move_to(self._y(v) + [-0.15 - n.width / 2, 0, 0]))
        nx = Text(nome_x, font_size=G - 6, color=BRANCO).move_to(
            [(self.esq + self.dir) / 2, self.base - (1.08 if nome_x_abaixo else 0.5), 0])
        ny = Text(nome_y, font_size=G - 6, color=BRANCO)
        if nome_y_dentro:  # no canto de cima à esquerda do gráfico, que não tem pinguim
            ny.move_to([self.esq + 0.2 + ny.width / 2, self.topo - 0.12, 0])
        else:
            ny.move_to([ESQ + ny.width / 2, self.topo + 0.5, 0])
        self.eixos = VGroup(eixo_x, eixo_y, marcas, nums, nx, ny)
        self.nome_x, self.nome_y, self.numeros = nx, ny, nums

        self.pontos = {}
        for linha, (esp, b, m) in PONTOS.items():
            if linha == M or (so is not None and linha not in so):
                continue
            self.pontos[linha] = Dot(self.p(b, m), radius=raio, color=COR[esp] if cores else CINZA,
                                     fill_opacity=0.95)
        self.grupo_pontos = VGroup(*self.pontos.values())
        self.misterioso = Dot(self.p(M_BICO, M_PESO), radius=0.1, color=BRANCO).set_stroke(FUNDO, 2.5)
        self.misterioso.set_z_index(2)
        self.interrogacao = Text("?", font_size=64, color=BRANCO, weight=BOLD).move_to(
            self.misterioso.get_center() + [0.4, -0.42, 0])
        self.tudo = VGroup(self.eixos, self.grupo_pontos, self.misterioso, self.interrogacao)

    def _x(self, v):
        return np.array([self.esq + (v - self.x0) / (self.x1 - self.x0) * (self.dir - self.esq), self.base, 0])

    def _y(self, v):
        return np.array([self.esq, self.base + (v - self.y0) / (self.y1 - self.y0) * (self.topo - self.base), 0])

    def p(self, bico, peso):
        """Ponto na tela de um pinguim com esse bico (mm) e peso (g)."""
        return np.array([self._x(self.fx(bico))[0], self._y(self.fy(peso))[1], 0])

    def pos(self, linha):
        esp, b, m = PONTOS[linha]
        return self.p(b, m)


def plano_cru(cores=True):
    return Plano(32, 60, 2700, 6300, (-1.95, -1.25, 3.2, 3.6),
                 numeros_x={32: "32", 60: "60"}, numeros_y={2700: br(2700), 6300: br(6300)},
                 marcas_x=(32, 40, 50, 60), marcas_y=(2700, 3600, 4500, 5400, 6300), cores=cores, nome_y_dentro=True)


def plano_z(cores=True):
    num = {-2.5: br(-2.5, 1), 0: "0", 3: br(3, sinal=True)}  # o −2,5 do canto vale para os dois eixos
    return Plano(-2.5, 3, -2.5, 3, (-1.4, -0.25, 2.45, 3.6), fx=z_bico, fy=z_peso,
                 nome_x="bico (desvios)", nome_y="peso (desvios)", numeros_x=num, numeros_y={0: "0", 3: num[3]},
                 marcas_x=(-2, -1, 0, 1, 2, 3), marcas_y=(-2, -1, 0, 1, 2, 3), cores=cores, nome_x_abaixo=True)


def formula_z():
    return conta("z", " = (x ", "− média", ") ", "÷ desvio", tamanho=G - 8).move_to([0, -1.98, 0])


def linhas_ate(plano, linhas, cor=AMARELO, espessura=4):
    o = plano.misterioso.get_center()
    return VGroup(*(Line(o, plano.pos(l), color=cor, stroke_width=espessura) for l in linhas))


def aneis(plano, linhas, cor=AMARELO):
    return VGroup(*(Circle(radius=0.14, color=cor, stroke_width=4).move_to(plano.pos(l)) for l in linhas))


def fim_linha_2():
    return plano_cru(True), titulo_dados(), legenda()


# ---------------------------------------------------------------- cartões

CARTAO_ESQ = np.array([-1.75, 3.05, 0])
CARTAO_DIR = np.array([1.75, 3.05, 0])


def cartao(cor, linha1, linha2):
    caixa = RoundedRectangle(width=3.0, height=2.9, corner_radius=0.22, stroke_color=cor, stroke_width=5)
    caixa.set_fill(FUNDO, 1)
    bicho = pinguim(cor, 1.1).move_to(caixa.get_top() + [0, -0.72, 0])
    l1 = Text(linha1, font_size=G, color=BRANCO).move_to(caixa.get_center() + [0, -0.32, 0])
    l2 = Text(linha2, font_size=G, color=BRANCO).move_to(caixa.get_center() + [0, -1.0, 0])
    g = VGroup(caixa, bicho, l1, l2)
    g.caixa, g.bicho, g.l1, g.l2 = caixa, bicho, l1, l2
    return g


# ---------------------------------------------------------------- as réguas

class Regua:
    """Uma medida numa régua de 6,6, com os 342 pinguins empilhados em cima (1 bolinha = 1 pinguim)."""

    def __init__(self, nome, lo, hi, y, indice, numeros, raio=0.042):
        self.lo, self.hi, self.y = lo, hi, y
        self.x0, self.x1 = -3.3, 3.3
        self.y1, self.y2 = y - 0.45, y - 0.98  # filas de rótulos embaixo da base
        base = Line([self.x0, y, 0], [self.x1, y, 0], stroke_width=EIXO, color=CINZA)
        pontas = VGroup(*(Line(self.p(v) + [0, -0.1, 0], self.p(v) + [0, 0.1, 0]) for v in (lo, hi))).set_stroke(
            CINZA, EIXO)
        nums = VGroup(Text(numeros[0], font_size=PQ).move_to(self.p(lo) + [0, -0.45, 0]),
                      Text(numeros[1], font_size=PQ).move_to(self.p(hi) + [0, -0.45, 0]))
        nums[0].align_to([self.x0 - 0.2, 0, 0], LEFT)
        nums[1].align_to([self.x1 + 0.2, 0, 0], RIGHT)
        self.nome = Text(nome, font_size=G - 6, color=BRANCO)
        self.nome.move_to([self.x1 - self.nome.width / 2, y + 1.0, 0])  # à direita, onde as pilhas são baixas
        self.eixo = VGroup(base, pontas, nums)
        passo, n = 2 * raio + 0.006, int((self.x1 - self.x0) / (2 * raio + 0.006))
        pilhas = {}
        ordem = sorted(PONTOS.items(), key=lambda kv: (ORDEM.index(kv[1][0]), kv[1][indice]))
        for linha, v in ordem:
            k = min(n - 1, int((v[indice] - lo) / (hi - lo) * n))
            pilhas.setdefault(k, []).append(linha)
        self.pontos = {}
        for k, linhas in pilhas.items():
            x = self.x0 + (k + 0.5) * (self.x1 - self.x0) / n
            for i, linha in enumerate(linhas):
                self.pontos[linha] = Dot([x, y + raio + 0.03 + i * passo, 0], radius=raio,
                                         color=COR[PONTOS[linha][0]])
        self.grupo_pontos = VGroup(*self.pontos.values())
        self.tudo = VGroup(self.eixo, self.nome, self.grupo_pontos)

    def p(self, v):
        return np.array([self.x0 + (v - self.lo) / (self.hi - self.lo) * (self.x1 - self.x0), self.y, 0])


def reguas():
    bico = Regua("bico (mm)", 32, 60, 2.85, 1, ("32", "60"))
    peso = Regua("peso (g)", 2700, 6300, -0.35, 2, (br(2700), br(6300)))
    return bico, peso


def trecho(regua, de, ate, cor, texto, fila=1):
    barra = Line(regua.p(de), regua.p(ate), color=cor, stroke_width=14)
    r = Text(texto, font_size=G - 6, color=cor).move_to([(regua.p(de)[0] + regua.p(ate)[0]) / 2,
                                                          regua.y1 if fila == 1 else regua.y2, 0])
    return VGroup(barra, r)


def marca(regua, valor, texto, cor, fila=1):
    x = regua.p(valor)
    t = Line(x + [0, -0.16, 0], x + [0, 0.16, 0], color=cor, stroke_width=5)
    r = Text(texto, font_size=PQ, color=cor).move_to([x[0], regua.y1 if fila == 1 else regua.y2, 0])
    return VGroup(t, r)


def trechos_desvio(bico=None, peso=None):
    if bico is None:
        bico, peso = reguas()
    tb = trecho(bico, MEDIA_BICO, MEDIA_BICO + DESV_BICO, BRANCO, T["desvios"]["bico"])
    tp = trecho(peso, MEDIA_PESO, MEDIA_PESO + DESV_PESO, BRANCO, T["desvios"]["massa"])
    return tb, tp


def fim_linha_12():
    bico, peso = reguas()
    tb, tp = trechos_desvio(bico, peso)
    return bico, peso, tb, tp, rotulo_knn()
