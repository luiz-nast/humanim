"""K-means no Old Faithful: o vocabulário visual comum a todas as linhas (posição, tamanho e cor fixos; nada depende
de tempo). CONTRATO completo logo abaixo; números sempre de dados/resultados.json.

CONTRATO (unidades Manim; o canto de quem apresenta é x < −0,44 e y < −2,37: em [CANTO] nada abaixo de y −2,07)
  Tamanhos: G 52 (rótulo), FC 46 (contas curtas), NOME 44 (nome de eixo), PQ 40 (o menor: números de eixo, crédito,
    contas longas; maiúscula de ~54 px). Cores: COR_G = (AZUL, LARANJA): grupo 0 (o que vira as 100 curtas) e grupo 1
    (as 172 longas); NEUTRO = BRANCO, erupção sem grupo; AMARELO só o que a fala aponta.
  Dados (índice i = 0..271, rownames = i + 1): DUR[i], ESP[i] (min); GRUPOS[r][i] (0/1) da rodada r = 1..5;
    CENTROS[r] = [(dur, esp) azul, (dur, esp) laranja]: r = 0 o começo (4,0; 71) e (4,133; 91), r ≥ 1 depois da regra 2
    (a média); TAMANHOS[r] (191, 81) … (100, 172); TROCAS[r] índices que trocam na rodada r (65, 23, 3, 0 para r = 2..5);
    ERRADOS: os 91 da 1ª divisão no grupo errado; SOMAS (8 meias rodadas) e SOMAS_TELA (as 9 da escada, em texto);
    COTOVELO [(k, soma, "50.440")…]; K3 [("5.189", 8)…] os 10 finais de k = 3; T = para_tela (textos prontos);
    coord(g, r) -> "(3,1; 64,9)". Números escritos com br() (ponto no milhar, vírgula decimal).
  Faixas fixas: alto Y1 5,25 e Y2 4,42 (duas filas, x −3,45 a 3,45, acima do plano em toda linha); embaixo do plano
    YB1 −2,85, YB2 −3,6, YB3 −4,2 (só em [ANIM]); FAIXA x −0,2..3,45, y −4,65..−2,45 (à direita do canto: vale em [CANTO],
    um elemento pequeno).
  plano(r=0) -> Plano: duração 1,5–5,5 min em x −2,4..3,4 (números 2 e 4) × espera 40–100 min em y −1,2..3,7 (números
    40, 70, 100); "espera (min)" dentro, no alto à esquerda, e "duração (min)" dentro, embaixo à direita (os dois cantos
    sem erupção); números do eixo deitado em y −1,65. Sempre acima do canto: o mesmo plano em todas as linhas.
    .eixos, .pontos {i: Dot} (r = 0 brancas, senão cores da rodada r), .grupo_pontos, .tudo, .p(dur, esp) -> ponto,
    .pos(i), .cores(r) -> {i: cor} para pintar (p.animate.set_color).
  Plano(x0, x1, y0, y1, caixa, numeros_x, numeros_y, marcas_x, marcas_y, grupos, so, raio, nomes_fora) -> o mesmo desenho
    com outro trecho. plano_zoom() -> as 100 curtas ampliadas (duração 1,5–4, espera 42–68; caixa x −2,3..3,3,
    y −0,3..3,2; nomes fora: espera em y 3,65, duração em y −1,3). Ampliar com moldura que cresce, nunca escalar.
  estado(r, fase=2) -> {plano, centros, fronteira} no fim da regra 1 ou 2 da rodada r (emendas entre linhas e blocos).
  centros(pl, r) -> VGroup(losango azul, losango laranja) em CENTROS[r]; losango(cor): cheio, contorno branco, z 3.
  fronteira(pl, r) -> DashedLine branca onde CENTROS[r] empatam (calculada em minutos), recortada no plano: r = 0 é a
    1ª divisão, quase deitada em 81 min; r = 1..4 desce rodada a rodada.
  linhas_ate(pl, r, c=r, so=None) -> VGroup de Line cinza finas (1,5; opacidade 0,7) de cada erupção (grupo da rodada r)
    até CENTROS[c][grupo] (c = r − 1 mostra a regra 1 da rodada r). Atrás dos pontos.
  aneis(pl, ids) -> anéis amarelos r 0,095 (aneis(pl, ERRADOS) = os 91 errados).
  vaga(pl, g): os cantos vazios do plano para rótulos do grupo g: 0 embaixo à direita (4,3 min; 57 min ≈ x 1,66,
    y 0,2), 1 no alto à esquerda (2,4; 85 ≈ x −1,1, y 2,5). rotulo_grupo(pl, g, "100", "curtas") -> número G+4 (e nome
    PQ embaixo) na cor do grupo, centrado na vaga ("191" / "81" sem nome).
  rotulo_k("k = 2") -> moldura amarela no alto à esquerda (Y1), da linha 4 ao fim da 7. regra(1) "1. mais perto"
    (Y1, encostada à direita), regra(2) "2. média" (Y2, alinhada com a 1). rodada(n) "rodada n" (Y2, à esquerda, sob
    o k). trocam(n) -> "65 trocam" grande embaixo do plano (YB1, [ANIM]); .n Integer amarelo, que cresce para a esquerda.
  conta_soma() -> "3.456 + 5.446 = 8.902" (Y1, FC; [0] azul, [2] laranja, [4] total); nome_soma() "soma dos quadrados
    (min²)" (Y2, PQ).
  Linha 1–2: geiser(altura) (morrinho cinza, jato branco, base no ORIGIN); abertura() {geiser, nome, lugar}: 1º quadro
    da linha 1 (gêiser com base em y 1,7, "Old Faithful" y −0,55, "Yellowstone, EUA" cinza y −1,3); rotulos_linha_1()
    ("curta", "longa" em y 0,45); fim_linha_1() {nome, lugar, geiser_esq, geiser_dir (x ±1,75), barra_esq/dir (2,1 e
    4,3 min, y 1,15), rotulo_esq/dir ("?" cinza, y 0,45), tracejada (x 0)}: o último quadro da 1 e o 1º da 2.
    contador_erupcoes(n) -> "272 erupções" no alto (.n Integer 96, borda esquerda fixa); credito() -> "dados: faithful,
    R" / "Härdle, 1991" cinza em YB2 e YB3 ([ANIM]). halo(pl, g) -> elipse cinza translúcida atrás do miolo da nuvem g
    (0 curta, 1 longa); marcas_nuvem(pl, g) -> VGroup(barra no eixo deitado, "curta"/"longa" em y −2,25 ([ANIM]),
    barra no eixo em pé, "espera curta" à direita da nuvem curta / "espera"+"longa" à esquerda da longa).
  Escada() -> as 9 somas das meias rodadas em degraus (linhas 13–14, acima do canto; veja a classe).
  Cotovelo() -> soma por k = 1..6, k em pé e soma deitada, para cada número caber na fila (linha 16; veja a classe).
"""
import json
from pathlib import Path

from estilo import *

# ---------------------------------------------------------------- dados

DADOS = Path(__file__).resolve().parent.parent / "dados"
R = json.loads((DADOS / "resultados.json").read_text(encoding="utf-8"))
T = R["para_tela"]
_D = R["demonstracao"]
PONTOS = [tuple(l) for l in _D["pontos"]["linhas"]]  # (rownames, duração, espera, grupo r1, r2, r3, r4, r5)
N = len(PONTOS)
DUR = [p[1] for p in PONTOS]
ESP = [p[2] for p in PONTOS]
GRUPOS = {r: [p[2 + r] for p in PONTOS] for r in range(1, 6)}  # GRUPOS[r][i]: 0 (azul, vira as curtas) ou 1
CENTROS = {0: [(c["duracao_min"], c["espera_min"]) for c in _D["iniciais"]]}  # CENTROS[0]: o começo
for _r in _D["rodadas"]:  # CENTROS[r]: depois da regra 2 da rodada r (a média do grupo)
    _c = _r["centros_depois_da_regra_2"]
    CENTROS[_r["rodada"]] = [(_c[g]["duracao_min"], _c[g]["espera_min"]) for g in ("grupo_0", "grupo_1")]
TAMANHOS = {r["rodada"]: (r["tamanhos"]["grupo_0"], r["tamanhos"]["grupo_1"]) for r in _D["rodadas"]}
TROCAS = {r: [i for i in range(N) if GRUPOS[r][i] != GRUPOS[r - 1][i]] for r in range(2, 6)}
ERRADOS = [i for i in range(N) if GRUPOS[1][i] != GRUPOS[5][i]]  # os 91 da 1ª divisão no grupo errado
SOMAS = [float(s) for s in _D["somas_meias_rodadas"]]  # depois da regra 1 e da regra 2 de cada rodada
SOMAS_TELA = T["soma_caindo"]["meias_rodadas"]  # as 9 da escada (a última repete: a rodada 5 não muda nada)
COTOVELO = [(c["k"], c["soma"], c["soma_tela"]) for c in R["cotovelo"]]
K3 = [(p["soma_tela"], p["partidas"]) for p in R["partidas_aleatorias"]["k_3"]]  # 10 finais de 100 começos


def _confere(cond, msg):
    if not cond:
        raise ValueError(f"comum.py: {msg} (os números de dados/ mudaram?)")


_confere(N == 272 and TAMANHOS[1] == (191, 81) and TAMANHOS[5] == (100, 172), "272 erupções, 191 × 81, 100 × 172")
_confere([len(TROCAS[r]) for r in range(2, 6)] == [65, 23, 3, 0] and len(ERRADOS) == 91, "trocas 65, 23, 3, 0 e 91")
_confere(CENTROS[0] == [(4.0, 71), (4.133, 91)], "centros iniciais (4,0; 71) e (4,133; 91)")
_confere(len(SOMAS_TELA) == 9 and [c[2] for c in COTOVELO][:2] == ["50.440", "8.902"], "escada e cotovelo")

COR_G = (AZUL, LARANJA)  # grupo 0 (vira as 100 curtas) e grupo 1 (as 172 longas)
NEUTRO = BRANCO  # ponto sem grupo (antes da 1ª regra)

G = 52  # rótulo principal
FC = 46  # contas curtas (as longas: PQ)
PQ = 40  # o menor que usamos: números de eixo, créditos (maiúscula de ~54 px no vídeo)
NOME = 44  # nome de eixo
EIXO = 4  # traço dos eixos
RAIO = 0.055  # ponto de uma erupção

# ---------------------------------------------------------------- faixas fixas

ESQ, DIR = -3.45, 3.45  # margens dos textos
Y1, Y2 = 5.25, 4.42  # faixa do alto, duas filas (acima do plano em toda linha)
YB1, YB2, YB3 = -2.85, -3.6, -4.2  # embaixo do plano: só em [ANIM] (em [CANTO] é o seu canto)
FAIXA = (-0.2, -4.65, 3.45, -2.45)  # à direita do canto (vale em [CANTO]): um elemento pequeno
FAIXA_CENTRO = np.array([(FAIXA[0] + FAIXA[2]) / 2, (FAIXA[1] + FAIXA[3]) / 2, 0.0])

# ---------------------------------------------------------------- o plano duração × espera


class Plano:
    """Plano desenhado à mão: eixos no canto de baixo à esquerda, poucos números, nomes dentro do gráfico (nos dois
    cantos sem erupção: espera no alto à esquerda, duração embaixo à direita). Um ponto por erupção (índice i = 0..271,
    rownames = i + 1). grupos: lista de 0/1 por erupção (None = NEUTRO); so: só esses índices."""

    def __init__(self, x0, x1, y0, y1, caixa, numeros_x, numeros_y, marcas_x, marcas_y, grupos=None, so=None,
                 raio=RAIO, nome_x="duração (min)", nome_y="espera (min)", nomes_fora=False):
        self.x0, self.x1, self.y0, self.y1 = x0, x1, y0, y1
        self.esq, self.base, self.dir, self.topo = caixa
        o = np.array([self.esq, self.base, 0])
        eixo_x = Line(o, [self.dir + 0.08, self.base, 0], stroke_width=EIXO, color=CINZA)
        eixo_y = Line(o, [self.esq, self.topo + 0.08, 0], stroke_width=EIXO, color=CINZA)
        marcas = VGroup(*(Line(self.p(v, y0) + [0, -0.09, 0], self.p(v, y0) + [0, 0.09, 0]) for v in marcas_x),
                        *(Line(self.p(x0, v) + [-0.09, 0, 0], self.p(x0, v) + [0.09, 0, 0]) for v in marcas_y)
                        ).set_stroke(CINZA, EIXO)
        nums = VGroup()
        for v, t in numeros_x.items():
            nums.add(Text(t, font_size=PQ, color=BRANCO).move_to(self.p(v, y0) + [0, -0.45, 0]))
        for v, t in numeros_y.items():
            n = Text(t, font_size=PQ, color=BRANCO)
            nums.add(n.move_to(self.p(x0, v) + [-0.16 - n.width / 2, 0, 0]))
        self.nome_x = Text(nome_x, font_size=NOME, color=BRANCO)
        self.nome_y = Text(nome_y, font_size=NOME, color=BRANCO)
        if nomes_fora:  # embaixo dos números e em cima do eixo em pé (quando os cantos do gráfico têm pontos)
            self.nome_x.move_to([(self.esq + self.dir) / 2, self.base - 1.0, 0])
            self.nome_y.move_to([ESQ + self.nome_y.width / 2, self.topo + 0.45, 0])
        else:
            self.nome_x.move_to([self.dir - 0.05 - self.nome_x.width / 2, self.base + 0.38, 0])
            self.nome_y.move_to([self.esq + 0.2 + self.nome_y.width / 2, self.topo - 0.25, 0])
        self.eixos = VGroup(eixo_x, eixo_y, marcas, nums, self.nome_x, self.nome_y)
        self.numeros = nums
        self.pontos = {}
        for i in range(N):
            if so is not None and i not in so:
                continue
            cor = NEUTRO if grupos is None else COR_G[grupos[i]]
            self.pontos[i] = Dot(self.p(DUR[i], ESP[i]), radius=raio, color=cor)
        self.grupo_pontos = VGroup(*self.pontos.values())
        self.tudo = VGroup(self.eixos, self.grupo_pontos)

    def p(self, dur, esp):
        """Ponto na tela de (duração, espera) em minutos."""
        return np.array([self.esq + (dur - self.x0) / (self.x1 - self.x0) * (self.dir - self.esq),
                         self.base + (esp - self.y0) / (self.y1 - self.y0) * (self.topo - self.base), 0.0])

    def pos(self, i):
        return self.p(DUR[i], ESP[i])

    def cores(self, r):
        """{i: cor} da rodada r (0 = NEUTRO): para pintar com p.animate.set_color(cor)."""
        return {i: NEUTRO if r == 0 else COR_G[GRUPOS[r][i]] for i in self.pontos}


CAIXA = (-2.4, -1.2, 3.4, 3.7)  # o plano principal: x 1,5–5,5 min, y 40–100 min (1,45 por min deitado, 0,082 em pé)


def plano(r=0):
    """O plano principal, sempre acima do canto, com as 272 erupções nas cores da rodada r (0 = brancas)."""
    return Plano(1.5, 5.5, 40, 100, CAIXA, numeros_x={2: "2", 4: "4"}, numeros_y={40: "40", 70: "70", 100: "100"},
                 marcas_x=(2, 3, 4, 5), marcas_y=(50, 60, 70, 80, 90), grupos=None if r == 0 else GRUPOS[r])


def plano_zoom(caixa=(-2.3, -0.3, 3.3, 3.2)):
    """O grupo azul ampliado (linha 10): um Plano novo, duração 1,5–4 e espera 42–68, só com as 100 curtas (azuis),
    nomes fora do gráfico (o nome da espera em y 3,65, o da duração em y −1,3). Ampliar = moldura que sai do trecho do
    plano principal e cresce até este (nunca escalar o plano por cima). Mude a caixa se precisar; 1 min em pé = 0,13."""
    curtas = [i for i in range(N) if GRUPOS[5][i] == 0]
    return Plano(1.5, 4.0, 42, 68, caixa, numeros_x={2: "2", 3: "3"}, numeros_y={45: "45", 55: "55", 65: "65"},
                 marcas_x=(2, 3), marcas_y=(45, 50, 55, 60, 65), grupos=GRUPOS[5], so=set(curtas), raio=0.065,
                 nomes_fora=True)


# Vagas: os dois cantos do plano sem erupção, para rótulos de grupo ("191", "100 curtas", "centro", coordenadas).
VAGA = {0: (4.3, 57.0), 1: (2.4, 85.0)}  # (duração, espera): 0 embaixo à direita, 1 no alto à esquerda


def vaga(pl, g):
    return pl.p(*VAGA[g])


def rotulo_grupo(pl, g, numero, nome=None):
    """Número do grupo g (cor do grupo) na vaga dele, com o nome embaixo (PQ): rotulo_grupo(pl, 0, "100", "curtas")."""
    n = Text(numero, font_size=G + 4, color=COR_G[g])
    if nome is None:
        return n.move_to(vaga(pl, g))
    t = Text(nome, font_size=PQ, color=COR_G[g])
    return VGroup(n, t).arrange(DOWN, buff=0.12).move_to(vaga(pl, g))


# ---------------------------------------------------------------- centros, fronteira, ligações


def losango(cor, lado=0.36):
    """O centro de um grupo: losango cheio na cor do grupo, contorno branco (aparece sobre pontos da mesma cor)."""
    return Square(side_length=lado).rotate(PI / 4).set_fill(cor, 1).set_stroke(BRANCO, 3).set_z_index(3)


def centros(pl, r=0):
    """VGroup(azul, laranja) nos CENTROS[r] (0 = começo; r = média depois da regra 2 da rodada r)."""
    return VGroup(*(losango(COR_G[g]).move_to(pl.p(*CENTROS[r][g])) for g in (0, 1)))


def coord(g, r):
    """Texto das coordenadas do centro: "(3,1; 64,9)"."""
    d, e = CENTROS[r][g]
    return f"({br(d, 1)}; {br(e, 1)})"


def fronteira(pl, r=0, cor=BRANCO):
    """Linha tracejada onde a distância aos dois CENTROS[r] empata: quem fica de cada lado na regra 1 da rodada r + 1
    (r = 0: a 1ª divisão, quase deitada em 81 min). Calculada em minutos, nunca mediatriz na tela (escalas diferentes)."""
    (a0, b0), (a1, b1) = CENTROS[r]
    n = np.array([a1 - a0, b1 - b0])
    m = np.array([(a0 + a1) / 2, (b0 + b1) / 2])
    d = np.array([-n[1], n[0]]) / np.linalg.norm(n)
    ts = []
    for k, (lo, hi) in enumerate(((pl.x0, pl.x1), (pl.y0, pl.y1))):
        if abs(d[k]) > 1e-9:
            ts += sorted(((lo - m[k]) / d[k], (hi - m[k]) / d[k]))
    t0 = max(ts[0], ts[2]) if len(ts) == 4 else ts[0]
    t1 = min(ts[1], ts[3]) if len(ts) == 4 else ts[1]
    a, b = m + t0 * d, m + t1 * d
    return DashedLine(pl.p(*a), pl.p(*b), dash_length=0.16, color=cor, stroke_width=EIXO).set_z_index(2)


def linhas_ate(pl, r, c=None, cor=CINZA, espessura=1.5, opacidade=0.7, so=None):
    """Uma linha de cada erupção (grupo da rodada r) até o seu centro CENTROS[c] (c = r: a média do grupo; para a
    regra 1 da rodada r, c = r − 1). VGroup na ordem dos índices; so: só esses índices."""
    c = r if c is None else c
    ids = [i for i in pl.pontos if so is None or i in so]
    return VGroup(*(Line(pl.pos(i), pl.p(*CENTROS[c][GRUPOS[r][i]]), stroke_width=espessura, color=cor,
                         stroke_opacity=opacidade) for i in ids)).set_z_index(-1)


def estado(r, fase=2):
    """O plano no fim da regra `fase` (1 ou 2) da rodada r: pontos nas cores de GRUPOS[r]; centros em CENTROS[r − 1]
    depois da regra 1 (ainda não andaram) e em CENTROS[r] depois da regra 2; fronteira onde esses centros empatam.
    r = 0: o começo (brancas, centros iniciais). dict: plano, centros, fronteira (o que a cena não mostra, não adiciona)."""
    pl = plano(r)
    c = r if (fase == 2 or r == 0) else r - 1
    return {"plano": pl, "centros": centros(pl, c), "fronteira": fronteira(pl, c)}


def aneis(pl, ids, cor=AMARELO):
    """Anéis em volta das erupções ids (os 91 errados: aneis(pl, ERRADOS))."""
    return VGroup(*(Circle(radius=0.095, color=cor, stroke_width=2.5).move_to(pl.pos(i)) for i in ids))


# ---------------------------------------------------------------- faixa do alto (linhas 4 a 7) e contadores


def rotulo_k(texto="k = 2"):
    """"k = 2" numa moldura amarela, no alto à esquerda (fila Y1). Da linha 4 até o fim da 7."""
    t = Text(texto, font_size=G, color=BRANCO)
    caixa = RoundedRectangle(width=t.width + 0.4, height=t.height + 0.14, corner_radius=0.15,
                             stroke_color=AMARELO, stroke_width=4)
    t.move_to(caixa)
    # o contorno não passa do topo da zona segura (5,6): no Y1 com folga maior, ele subia até 5,67
    return VGroup(caixa, t).move_to([ESQ + caixa.width / 2, min(Y1, 5.58 - caixa.height / 2), 0])


def regra(n):
    """"1. mais perto" (fila Y1, encostada à direita) e "2. média" (fila Y2, alinhada com a 1 à esquerda)."""
    r1 = Text("1. mais perto", font_size=ROTULO, color=BRANCO)
    r1.move_to([DIR - r1.width / 2, Y1, 0])
    if n == 1:
        return r1
    r2 = Text("2. média", font_size=ROTULO, color=BRANCO)
    return r2.move_to([r1.get_left()[0] + r2.width / 2, Y2, 0])


def rodada(n):
    """"rodada n" na fila Y2, à esquerda (embaixo do "k = 2")."""
    t = Text(f"rodada {n}", font_size=ROTULO, color=BRANCO)
    return t.move_to([ESQ + t.width / 2, Y2, 0])


def trocam(n):
    """Contador "65 trocam" embaixo do plano (YB1, só em [ANIM]): VGroup(Integer, texto); .n é o Integer
    (troque no pouso com .n.set_value: conta coisas, então pode rolar)."""
    num = Integer(n, font_size=96, color=AMARELO)
    t = Text("trocam", font_size=G, color=BRANCO)
    g = VGroup(num, t).arrange(RIGHT, buff=0.3, aligned_edge=DOWN).move_to([0, YB1, 0])
    num.edge_to_fix = RIGHT  # cresce para a esquerda: o "trocam" não se mexe
    g.n = num
    return g


def contador_erupcoes(n=0):
    """Linha 2: "272 erupções" no alto (o número conta as erupções que caem). VGroup(Integer, texto); .n o Integer,
    com a borda esquerda fixa em x −2,6 (cresce para a direita sem empurrar o texto, que fica em x −0,15)."""
    num = Integer(n, font_size=96, color=BRANCO)
    num.move_to([-2.6 + num.width / 2, 5.05, 0])
    t = Text("erupções", font_size=G, color=BRANCO)
    t.move_to([-0.15 + t.width / 2, 0, 0]).align_to(num, DOWN)
    g = VGroup(num, t)
    g.n = num
    return g


def credito():
    """Linha 2: a fonte dos dados, pequena e cinza, em duas filas embaixo (YB2, YB3; só em [ANIM])."""
    return VGroup(Text("dados: faithful, R", font_size=PQ, color=CINZA).move_to([0, YB2, 0]),
                  Text("Härdle, 1991", font_size=PQ, color=CINZA).move_to([0, YB3, 0]))


def conta_soma():
    """"3.456 + 5.446 = 8.902" no alto (fila Y1): [0] azul, [2] laranja, [4] o total."""
    a, b = (br(R["por_que_a_media"][k]["soma_com_centro_na_media"]) for k in ("curto", "longo"))
    _confere(f"{a} + {b} = {T['final']['soma']}" == T["final"]["partes_da_soma"], "3.456 + 5.446 = 8.902")
    return conta(a, " + ", b, " = ", T["final"]["soma"], tamanho=FC, cores={0: AZUL, 2: LARANJA}).move_to([0, Y1, 0])


def nome_soma():
    """"soma dos quadrados (min²)" na fila Y2, centrado (embaixo da conta_soma)."""
    return Text("soma dos quadrados (min²)", font_size=PQ, color=BRANCO).move_to([0, Y2, 0])


# ---------------------------------------------------------------- linha 2: as duas nuvens


def _nuvem(pl, g):
    """Centro, eixos e ângulo da elipse que cobre ~95% do grupo final g, na tela."""
    xy = np.array([pl.pos(i)[:2] for i in range(N) if GRUPOS[5][i] == g])
    for _ in range(2):  # sem os pontos soltos (Mahalanobis² > 6: fora de ~95%), para a elipse abraçar o miolo
        c = xy.mean(axis=0)
        inv = np.linalg.inv(np.cov((xy - c).T))
        xy = xy[np.einsum("ij,jk,ik->i", xy - c, inv, xy - c) < 6]
    c = xy.mean(axis=0)
    val, vec = np.linalg.eigh(np.cov((xy - c).T))
    return c, 2 * 2.1 * np.sqrt(val[1]) + 0.2, 2 * 2.1 * np.sqrt(val[0]) + 0.2, np.arctan2(vec[1, 1], vec[0, 1])


def halo(pl, g, cor=CINZA):
    """A nuvem g (0 = curta, 1 = longa) acesa: elipse cinza translúcida atrás dos pontos (eles continuam brancos)."""
    c, a, b, ang = _nuvem(pl, g)
    return Ellipse(width=a, height=b).rotate(ang).move_to([*c, 0]).set_fill(cor, 0.35).set_stroke(
        cor, 3).set_z_index(-2)


def marcas_nuvem(pl, g):
    """Linha 2: onde a nuvem g cai em cada eixo. VGroup(barra_x, rotulo_x, barra_y, rotulo_y):
    barras grossas cinza-claras sobre os eixos (o trecho que a elipse cobre); "curta"/"longa" embaixo dos números do
    eixo deitado (fila y = base − 1,05, só em [ANIM]); "espera curta" à direita da nuvem curta (canto vazio de baixo)
    e "espera" / "longa" em duas filas à esquerda da nuvem longa (canto vazio de cima), na altura da nuvem."""
    e = halo(pl, g)
    x0, x1 = max(e.get_left()[0], pl.esq + 0.1), min(e.get_right()[0], pl.dir)
    y0, y1 = max(e.get_bottom()[1], pl.base + 0.1), min(e.get_top()[1], pl.topo)
    claro = interpolate_color(ManimColor(CINZA), ManimColor(BRANCO), 0.5)
    bx = Line([x0, pl.base, 0], [x1, pl.base, 0], stroke_width=12, color=claro)
    by = Line([pl.esq, y0, 0], [pl.esq, y1, 0], stroke_width=12, color=claro)
    nome = ("curta", "longa")[g]
    rx = Text(nome, font_size=G, color=BRANCO).move_to([(x0 + x1) / 2, pl.base - 1.05, 0])
    yc = (y0 + y1) / 2
    if g == 0:  # no vão de baixo (depois de 3 min não há curta), no alto da nuvem: longe do "duração (min)"
        ry = Text("espera curta", font_size=PQ + 4, color=BRANCO)
        ry.move_to([max(x1 + 0.2, pl.p(3.0, 0)[0]) + ry.width / 2, yc + 0.45, 0])
    else:
        ry = VGroup(Text("espera", font_size=PQ + 4, color=BRANCO), Text("longa", font_size=PQ + 4, color=BRANCO)
                    ).arrange(DOWN, buff=0.1, aligned_edge=RIGHT)
        ry.move_to([min(x0 - 0.3, pl.p(3.05, 0)[0]) - ry.width / 2, yc, 0])  # no vão de cima
    return VGroup(bx, rx, by, ry)


# ---------------------------------------------------------------- linha 1: o gêiser


def geiser(altura=3.4):
    """Gêiser de formas simples: morrinho cinza e jato branco com três nuvenzinhas no alto. Base no ORIGIN."""
    xs = np.linspace(-1, 1, 41)
    morro = Polygon(*[[1.3 * x, 0.75 * np.sqrt(max(0, 1 - x * x)), 0] for x in xs]).set_fill(CINZA, 1).set_stroke(
        width=0)
    jato = Polygon([-0.13, 0.6, 0], [0.13, 0.6, 0], [0.2, 1.6, 0], [0.4, 2.8, 0], [-0.4, 2.8, 0], [-0.2, 1.6, 0]
                   ).set_fill(BRANCO, 1).set_stroke(width=0)
    nuvens = VGroup(*(Circle(radius=r).set_fill(BRANCO, 1).set_stroke(width=0).move_to([x, y, 0])
                      for x, y, r in ((-0.5, 2.55, 0.3), (0.5, 2.55, 0.3), (-0.25, 2.9, 0.36), (0.28, 2.88, 0.34),
                                      (0, 3.2, 0.36), (-0.66, 2.3, 0.17), (0.68, 2.32, 0.17))))
    g = VGroup(jato, nuvens, morro)
    g.scale(altura / g.height, about_point=ORIGIN)
    return g


GEISER_Y = 1.7  # base dos gêiseres na linha 1


def abertura():
    """1º quadro da linha 1: um gêiser no alto, "Old Faithful" e, em cinza, "Yellowstone, EUA" embaixo dele."""
    return {"geiser": geiser().move_to([0, GEISER_Y, 0], aligned_edge=DOWN),
            "nome": Text("Old Faithful", font_size=60, color=BRANCO).move_to([0, -0.55, 0]),
            "lugar": Text("Yellowstone, EUA", font_size=PQ, color=CINZA).move_to([0, -1.3, 0])}


def fim_linha_1():
    """Último quadro da linha 1 (e 1º da 2): dois gêiseres (x ±1,75), barra de tempo embaixo de cada um (curta 2,1 min
    e longa 4,3 min, na mesma escala), "?" cinza no lugar de "curta"/"longa", tracejada descendo em x = 0, e o nome e o
    lugar onde estavam. Tudo acima do canto."""
    a = abertura()
    del a["geiser"]
    for k, x in (("esq", -1.75), ("dir", 1.75)):
        a[f"geiser_{k}"] = geiser().move_to([x, GEISER_Y, 0], aligned_edge=DOWN)
    escala = 0.6  # unidades por minuto de erupção
    for k, x, dur in (("esq", -1.75, 2.1), ("dir", 1.75, 4.3)):
        a[f"barra_{k}"] = Line([x - dur * escala / 2, 1.15, 0], [x + dur * escala / 2, 1.15, 0], stroke_width=14,
                               color=BRANCO)
        a[f"rotulo_{k}"] = Text("?", font_size=60, color=CINZA).move_to([x, 0.45, 0])
    a["tracejada"] = DashedLine([0, 5.3, 0], [0, 0.1, 0], dash_length=0.18, color=BRANCO, stroke_width=EIXO)
    return a


def rotulos_linha_1():
    """"curta" e "longa" no lugar dos "?" da linha 1 (o estado do meio da linha 1)."""
    return (Text("curta", font_size=G, color=BRANCO).move_to([-1.75, 0.45, 0]),
            Text("longa", font_size=G, color=BRANCO).move_to([1.75, 0.45, 0]))


# ---------------------------------------------------------------- linhas 13 e 14: a escada que nunca sobe


class Escada:
    """As 9 somas das meias rodadas (regra 1, regra 2, ...; a 9ª repete a 8ª: a rodada 5 não muda nada), um degrau
    por regra, acima do canto. Eixo em pé de 0 a 40.000 min² (y 1,3 a 4,3), x −2,9 a 3,4 (degrau de 0,7).
    .eixos (linhas, "0", "soma (min²)" no alto à esquerda, fila Y1), .degraus [9 Line], .espelhos [8 Line verticais],
    .rotulos {índice: Text} nos degraus 0, 1, 3, 5 e 7 ("37.347", "27.203", "12.821", "9.057", "8.902"; o do 7 cobre o
    7 e o 8), .parou ("rodada 5: parou", embaixo dos dois últimos degraus), .tudo.
    Embaixo dela, livres: y 0,9 a −2,0 (cabe "2²⁷¹ − 1 jeitos" em 60 e "82 algarismos" em PQ)."""

    def __init__(self):
        self.esq, self.base, self.dir, self.topo = -2.9, 1.3, 3.4, 4.3
        self.w = (self.dir - self.esq) / 9
        vals = SOMAS + [SOMAS[-1]]
        o = np.array([self.esq, self.base, 0])
        eixo_x = Line(o, [self.dir + 0.08, self.base, 0], stroke_width=EIXO, color=CINZA)
        eixo_y = Line(o, [self.esq, self.topo + 0.08, 0], stroke_width=EIXO, color=CINZA)
        zero = Text("0", font_size=PQ, color=BRANCO).move_to(o + [-0.3, 0, 0])
        nome = Text("soma (min²)", font_size=NOME, color=BRANCO)
        nome.move_to([ESQ + nome.width / 2, Y1, 0])
        self.eixos = VGroup(eixo_x, eixo_y, zero, nome)
        self.degraus = [Line([self.x(k), self.y(v), 0], [self.x(k + 1), self.y(v), 0], stroke_width=ESPESSURA,
                             color=BRANCO) for k, v in enumerate(vals)]
        self.espelhos = [Line([self.x(k), self.y(vals[k - 1]), 0], [self.x(k), self.y(vals[k]), 0],
                              stroke_width=ESPESSURA, color=BRANCO) for k in range(1, 9)]
        self.rotulos = {}
        for k, ate in ((0, 0), (1, 1), (3, 3), (5, 5), (7, 8)):
            t = Text(SOMAS_TELA[k], font_size=PQ, color=BRANCO)
            cx = (self.x(k) + self.x(ate + 1)) / 2
            x0 = min(max(cx - t.width / 2, self.x(k) - 0.15 if k else self.esq + 0.18), DIR - t.width)
            if k in (1, 5):  # à direita do espelho do degrau (o 9.057 assim não encosta no 8.902)
                x0 = self.x(k) + 0.14 - (0.35 if k == 5 else 0)
            sob = [vals[j] for j in range(9) if self.x(j + 1) > x0 and self.x(j) < x0 + t.width]
            t.move_to([x0 + t.width / 2, self.y(max(sob)) + 0.17 + t.height / 2, 0])
            self.rotulos[k] = t
        self.parou = Text("rodada 5: parou", font_size=PQ, color=AMARELO)
        self.parou.move_to([DIR - self.parou.width / 2, (self.base + self.y(vals[-1])) / 2, 0])
        self.tudo = VGroup(self.eixos, *self.degraus, *self.espelhos, *self.rotulos.values())

    def x(self, k):
        return self.esq + k * self.w

    def y(self, v):
        return self.base + v / 40000 * (self.topo - self.base)


# ---------------------------------------------------------------- linha 16: o cotovelo


class Cotovelo:
    """Soma dos quadrados por k (1 a 6), deitado para cada número caber na sua fila: k em pé (1 no alto, 6 embaixo,
    filas de 1,4 em y 3,45 … −3,55, números à esquerda do eixo em x −2,55), soma deitada de 0 (x −2,55) a 50.440
    (x 3,05), eixo em y −4,05 com "0" e "soma (min²)" embaixo. A curva ainda dobra num cotovelo, no k = 2.
    .eixos, .pontos [6 Dot], .trechos [5 Line] (trecho j liga k = j+1 a k = j+2), .valores [6 Text] ("50.440" acima do
    ponto, os outros à direita dele), .quedas [2 Text] ("− 41.538" acima do 1º trecho, "− 3.713" à direita do 2º),
    .anel (amarelo, em volta do k = 2), .nota VGroup("cotovelo" amarelo logo acima do anel, "não é prova" cinza acima
    dele), no vão acima do 1º trecho. .tudo: eixos, pontos, trechos e valores. Livre: x 0,4 a 3,45, y −0,3 a −3,5."""

    def __init__(self):
        self.x0, self.x1, self.yb = -2.55, 3.05, -4.05
        ks = [c[0] for c in COTOVELO]
        o = np.array([self.x0, self.yb, 0])
        eixo_x = Line(o, [3.35, self.yb, 0], stroke_width=EIXO, color=CINZA)
        eixo_y = Line(o, [self.x0, 4.05, 0], stroke_width=EIXO, color=CINZA)
        marcas = VGroup(*(Line(self.p(v, 6) * [1, 0, 0] + [0, self.yb - 0.09, 0],
                               self.p(v, 6) * [1, 0, 0] + [0, self.yb + 0.09, 0]) for v in (10000, 20000, 30000, 40000, 50000)),
                        *(Line(self.p(0, k) + [-0.09, 0, 0], self.p(0, k) + [0.09, 0, 0]) for k in ks)).set_stroke(CINZA, EIXO)
        nums = VGroup(*(Text(str(k), font_size=G, color=BRANCO).move_to(self.p(0, k) + [-0.4, 0, 0]) for k in ks))
        zero = Text("0", font_size=PQ, color=BRANCO).move_to(o + [0, -0.45, 0])
        nome_x = Text("soma (min²)", font_size=NOME, color=BRANCO)
        nome_x.move_to([DIR - nome_x.width / 2, self.yb - 0.45, 0])
        nome_k = Text("k", font_size=G, color=BRANCO).move_to([self.x0, 4.5, 0])
        self.eixos = VGroup(eixo_x, eixo_y, marcas, nums, zero, nome_x, nome_k)
        self.pontos = [Dot(self.p(s, k), radius=0.11, color=AZUL).set_z_index(2) for k, s, _ in COTOVELO]
        self.trechos = [Line(self.pontos[j].get_center(), self.pontos[j + 1].get_center(), stroke_width=ESPESSURA,
                             color=AZUL) for j in range(5)]
        self.valores = []
        for j, (k, s, tela) in enumerate(COTOVELO):
            t = Text(tela, font_size=PQ + 4, color=BRANCO)
            if j == 0:
                t.move_to([DIR - t.width / 2, self.p(s, k)[1] + 0.5, 0])
            else:
                t.move_to(self.p(s, k) + [0.3 + t.width / 2, 0, 0])
            self.valores.append(t)
        s1, s2 = (f"{MENOS} {br(COTOVELO[j][1] - COTOVELO[j + 1][1])}" for j in (0, 1))
        _confere([s1, s2] == [f"{MENOS} 41.538", f"{MENOS} 3.713"], "quedas 41.538 e 3.713")
        q1 = Text(s1, font_size=PQ + 4, color=AMARELO)
        a, b = self.pontos[0].get_center(), self.pontos[1].get_center()
        q1.move_to([DIR - 0.1 - q1.width / 2, 2.3, 0])  # embaixo do 1º trecho, à direita
        q2 = Text(s2, font_size=PQ + 4, color=AMARELO)
        a, b = self.pontos[1].get_center(), self.pontos[2].get_center()
        q2.move_to([(a[0] + b[0]) / 2 + 0.35 + q2.width / 2, (a[1] + b[1]) / 2, 0])
        self.quedas = [q1, q2]
        self.anel = Circle(radius=0.3, color=AMARELO, stroke_width=5).move_to(self.pontos[1])
        cot = Text("cotovelo", font_size=G, color=AMARELO)  # logo acima do anel, acima do 1º trecho
        cot.move_to([self.x0 + 0.2 + cot.width / 2, self.anel.get_top()[1] + 0.3 + cot.height / 2, 0])
        prova = Text("não é prova", font_size=PQ, color=CINZA)
        prova.move_to([self.x0 + 0.2 + prova.width / 2, cot.get_top()[1] + 0.2 + prova.height / 2, 0])
        self.nota = VGroup(cot, prova)
        self.tudo = VGroup(self.eixos, *self.trechos, *self.pontos, *self.valores)

    def p(self, soma, k):
        return np.array([self.x0 + soma / COTOVELO[0][1] * (self.x1 - self.x0), 3.45 - (k - 1) * 1.4, 0.0])
