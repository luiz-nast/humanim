"""O que as linhas compartilham: os números (lidos de dados/), os desenhos e as posições fixas.

Todo número da tela sai de dados/resultados.json, dados/numeros_roteiro.json e dados/conferir_teoria.json,
e as contas de 2 casas são conferidas aqui (o import para com erro se alguma deixar de fechar).

Blocos que continuam de uma linha para a outra (o fim de uma é o começo da outra):
  1 -> 2      as três perguntas, que somem quando a nuvem de clientes cai
  4 -> 5 -> 6 os dois clientes sorteados viram o quadrado das chances (tela toda na 5 e na 6)
  8 -> 9 -> 10 -> 11  a pergunta vencedora: grupos, régua da bagunça, barras e média ponderada (acima do canto)
  13 -> 14 -> 15 -> 16  outras perguntas na régua, a árvore que cresce e a árvore fantasma (acima do canto)

A régua da bagunça vai inteira (0 a 0,5) nas linhas 8 e 9; da 10 em diante, quando as diferenças são de 0,01,
ela vira uma lupa do trecho de 0,27 a 0,36 (0,01 = 126 px), e o que passa disso fica numa seta no alto.
"""
import json
from pathlib import Path

from estilo import *

# ---------------------------------------------------------------- números

DADOS = Path(__file__).resolve().parent.parent / "dados"
R = json.loads((DADOS / "resultados.json").read_text(encoding="utf-8"))
NR = json.loads((DADOS / "numeros_roteiro.json").read_text(encoding="utf-8"))
TE = json.loads((DADOS / "conferir_teoria.json").read_text(encoding="utf-8"))


def br(x, casas=2):
    """0.3445 -> "0,34"; 30000 -> "30.000" (casas=0)."""
    s = f"{x:,.{casas}f}"
    return s.translate(str.maketrans(",.", ".,"))


def r2(x):
    """Arredonda como a tela mostra (2 casas), para as contas fecharem com o que se vê."""
    return round(x + 1e-12, 2)


def _confere(cond, msg):
    if not cond:
        raise ValueError(f"comum.py: {msg} (os números de dados/ mudaram?)")


N_TOTAL = R["gini_raiz"]["n"]  # 30 000
N_CALOTE = R["gini_raiz"]["calote"]  # 6 636
P_PAGA, P_CAL = r2(R["gini_raiz"]["p_pagou"]), r2(R["gini_raiz"]["p_calote"])  # 0,78 e 0,22
Q_PAGA, Q_CAL = r2(P_PAGA ** 2), r2(P_CAL ** 2)  # 0,61 e 0,05
IGUAIS = r2(Q_PAGA + Q_CAL)  # 0,66
G_RAIZ = r2(1 - IGUAIS)  # 0,34
_confere(f"1 − ({br(P_PAGA)}² + {br(P_CAL)}²) = 1 − ({br(Q_PAGA)} + {br(Q_CAL)}) = 1 − {br(IGUAIS)} = {br(G_RAIZ)}"
         == R["para_tela"]["raiz_2_casas"], "a conta da raiz com 2 casas")
_confere(G_RAIZ == r2(R["gini_raiz"]["gini"]), "Gini da raiz")

V = R["perguntas_candidatas"][0]  # a vencedora: PAY_0 >= 2
_confere(V["regra"] == "PAY_0 >= 2", "a primeira candidata é a vencedora")
SIM, NAO = V["sim"], V["nao"]
S_PAGA, S_CAL = r2(SIM["p_pagou"]), r2(SIM["p_calote"])  # 0,30 e 0,70
S_Q = (r2(S_PAGA ** 2), r2(S_CAL ** 2))  # 0,09 e 0,49
G_SIM = r2(1 - sum(S_Q))  # 0,42
N_PAGA, N_CAL = r2(NAO["p_pagou"]), r2(NAO["p_calote"])  # 0,83 e 0,17
N_Q = (r2(N_PAGA ** 2), r2(N_CAL ** 2))  # 0,69 e 0,03
G_NAO = r2(1 - sum(N_Q))  # 0,28
W_SIM, W_NAO = r2(V["peso_sim"]), r2(V["peso_nao"])  # 0,10 e 0,90
PROD_SIM, PROD_NAO = r2(W_SIM * G_SIM), r2(W_NAO * G_NAO)  # 0,04 e 0,25
G_POND = r2(PROD_SIM + PROD_NAO)  # 0,29
MEDIA_SEM_PESO = r2((G_SIM + G_NAO) / 2)  # 0,35
GANHO = r2(G_RAIZ - G_POND)  # 0,05
PCT_TIRADO = round(100 * GANHO / G_RAIZ)  # 15 (o exato é 15,2)
_tela = R["para_tela"]["vencedora_2_casas"]
_confere(_tela["gini_sim"] == f"1 − ({br(S_PAGA)}² + {br(S_CAL)}²) = 1 − ({br(S_Q[0])} + {br(S_Q[1])}) = "
         f"1 − {br(sum(S_Q))} = {br(G_SIM)}", "Gini do lado sim")
_confere(_tela["gini_nao"] == f"1 − ({br(N_PAGA)}² + {br(N_CAL)}²) = 1 − ({br(N_Q[0])} + {br(N_Q[1])}) = "
         f"1 − {br(sum(N_Q))} = {br(G_NAO)}", "Gini do lado não")
_confere(_tela["ponderado"] == f"{br(W_SIM)} × {br(G_SIM)} + {br(W_NAO)} × {br(G_NAO)} = "
         f"{br(PROD_SIM)} + {br(PROD_NAO)} = {br(G_POND)}", "média ponderada")
_confere(_tela["ganho"] == f"{br(G_RAIZ)} − {br(G_POND)} = {br(GANHO)}", "redução de impureza")
_confere(NR["vencedora"]["media_sem_peso_tela"] == f"({br(G_SIM)} + {br(G_NAO)}) ÷ 2 = {br(MEDIA_SEM_PESO)}",
         "média sem peso")
_confere(PCT_TIRADO == round(V["ganho_pct_da_raiz"]), "15% da bagunça")

PCT_CAL_RAIZ = round(100 * N_CALOTE / N_TOTAL)  # 22
PCT_CAL_SIM = br(100 * SIM["calote"] / SIM["n"], 1)  # 69,6
PCT_CAL_NAO = br(100 * NAO["calote"] / NAO["n"], 1)  # 16,6

# 1 ponto = 100 clientes
NUVEM = NR["base"]["nuvem_300_pontos"]  # 234 verdes, 66 vermelhos
PT_SIM = NR["vencedora"]["sim"]["nuvem_31_pontos"]  # 22 vermelhos, 9 verdes
PT_NAO = NR["vencedora"]["nao"]["nuvem_269_pontos"]  # 44 vermelhos, 225 verdes
_confere(PT_SIM["vermelhos"] + PT_NAO["vermelhos"] == NUVEM["vermelhos"]
         and PT_SIM["verdes"] + PT_NAO["verdes"] == NUVEM["verdes"], "os pontos dos dois lados somam a nuvem")

# Outras perguntas (linhas 13 e 14)
UM_MES = R["perguntas_candidatas"][1]
_confere(UM_MES["regra"] == "PAY_0 >= 1", "a segunda candidata é 'algum atraso'")
G_POND_1MES = r2(UM_MES["gini_ponderado"])  # 0,30
G_SIM_1MES = r2(UM_MES["sim"]["gini"])  # 0,50
PCT_SIM_1MES = round(100 * UM_MES["sim"]["calote"] / UM_MES["sim"]["n"])  # 50
SC = NR["senso_comum"]
PCT_IDADE, PCT_CIVIL = SC["idade"]["tela"], SC["estado_civil"]["tela"]  # "0,2%" e "0,1%"
_confere(max(SC["idade"]["pct_tirado"], SC["estado_civil"]["pct_tirado"]) < 1, "idade e estado civil tiram menos de 1%")
G_IDADE = R["gini_raiz"]["gini"] * (1 - SC["idade"]["pct_tirado"] / 100)
G_CIVIL = R["gini_raiz"]["gini"] * (1 - SC["estado_civil"]["pct_tirado"] / 100)

# Gulosa x a que começa por "1+ mês?" (linhas 15 e 16)
F = TE["F_guloso_vs_otimo_prof2"]
GULOSA = br(F["guloso"]["gini_nas_folhas"], 4)  # 0,2810
_outra = NR["gulosa"]["comeca_por_1_mes"]["gini_nas_folhas"]
OUTRA = br(_outra, 4)  # 0,2808
_confere(_outra < F["guloso"]["gini_nas_folhas"], "a árvore que começa por 1 mês tem menos bagunça")

# ---------------------------------------------------------------- tamanhos e peças

G = 52  # rótulo principal (letra maiúscula de ~70 px no vídeo)
FC = 48  # contas
PQ = 40  # o menor que usamos (créditos, apartes em cinza)
FINO = " "  # espacinho entre o "²" e o ")" (sem ele o expoente encosta no parêntese)


def ponto(x, y):
    return np.array([x, y, 0.0])


def texto(t, cor=BRANCO, tamanho=G, **kw):
    """Rótulo; "\\n" quebra em linhas centradas (cada linha com até 3 palavras)."""
    linhas = [rotulo(p, cor=cor, tamanho=tamanho, **kw) for p in t.split("\n")]
    return VGroup(*linhas).arrange(DOWN, buff=0.14) if len(linhas) > 1 else linhas[0]


def conta(*partes, tamanho=FC, cor=BRANCO, cores=None):
    """Uma conta num Text só (as partes ficam na mesma linha de base) e cada parte acessível: VGroup de partes.
    Ex.: conta("0,78", " × ", "0,78", " = ", "0,61")[4] é o "0,61". cores: {índice da parte: cor}.
    O "²" sai um pouco maior que o da fonte (60% do dígito), para se ler no celular."""
    s = "".join(partes)
    t = Text(s, font_size=tamanho, color=cor, disable_ligatures=True)
    if len(t.submobjects) != len(s):
        raise ValueError(f"conta {s!r}: {len(t.submobjects)} glifos para {len(s)} caracteres")
    for i, c in enumerate(s):
        if c == "²":
            t.submobjects[i].scale(1.25, about_edge=DL)
    grupos, i = VGroup(), 0
    for k, p in enumerate(partes):
        g = VGroup(*t.submobjects[i:i + len(p)])  # sem ligaduras: um glifo por caractere, espaços inclusive
        if cores and k in cores:
            g.set_color(cores[k])
        grupos.add(g)
        i += len(p)
    return grupos


def caixa(t, cor=AZUL, tamanho=G, largura=None, altura=None, preenchida=False, cor_texto=BRANCO, tracejada=False):
    """Caixa de pergunta: VGroup(borda, texto). tracejada: contorno em traços (a árvore fantasma)."""
    escrito = texto(t, cor=cor_texto, tamanho=tamanho)
    borda = RoundedRectangle(corner_radius=0.18, width=largura or escrito.width + 0.6,
                             height=altura or escrito.height + 0.45, color=cor, stroke_width=ESPESSURA)
    if preenchida:
        borda.set_fill(cor, opacity=0.25)
    if tracejada:
        borda = DashedVMobject(borda, num_dashes=28, dashed_ratio=0.6)
    return VGroup(borda, escrito.move_to(borda))


def riscar(obj, cor=VERMELHO):
    return Line(obj.get_corner(DL) + LEFT * 0.1, obj.get_corner(UR) + RIGHT * 0.1, color=cor, stroke_width=ESPESSURA)


def seta(a, b, cor=BRANCO, **kw):
    return Arrow(a, b, buff=0.08, color=cor, stroke_width=ESPESSURA, tip_length=0.26,
                 max_tip_length_to_length_ratio=0.35, **kw)


def ao_lado(s, t, lado, tamanho=44, cor=BRANCO, buff=0.22):
    """"sim"/"não" ao lado de uma seta (lado = LEFT ou RIGHT), na altura do meio dela, sem tocar a linha."""
    r = rotulo(t, cor=cor, tamanho=tamanho)
    meio = s.get_center()
    r.move_to(meio)
    # o x da seta na altura do rótulo (seta inclinada): encosta pelo lado de fora
    ini, fim = s.get_start(), s.get_end()
    def x_em(y):
        if abs(fim[1] - ini[1]) < 1e-6:
            return meio[0]
        return ini[0] + (y - ini[1]) * (fim[0] - ini[0]) / (fim[1] - ini[1])
    xs = [x_em(meio[1] + d) for d in (-r.height / 2, r.height / 2)]
    if lado[0] < 0:
        r.set_x(min(xs) - buff - r.width / 2)
    else:
        r.set_x(max(xs) + buff + r.width / 2)
    return r


def cadeado(cor=AZUL):
    corpo = RoundedRectangle(corner_radius=0.05, width=0.42, height=0.34, color=cor, stroke_width=0,
                             fill_color=cor, fill_opacity=1)
    alca = Arc(radius=0.14, start_angle=0, angle=PI, color=cor, stroke_width=ESPESSURA).next_to(corpo, UP, buff=-0.02)
    return VGroup(alca, corpo)


def cartao(cor=AZUL):
    corpo = RoundedRectangle(corner_radius=0.1, width=1.05, height=0.68, color=cor, stroke_width=ESPESSURA)
    faixa = Line(corpo.get_left() + UP * 0.12, corpo.get_right() + UP * 0.12, color=cor, stroke_width=ESPESSURA)
    chip = RoundedRectangle(corner_radius=0.03, width=0.22, height=0.16, color=AMARELO, stroke_width=0,
                            fill_color=AMARELO, fill_opacity=1).move_to(corpo.get_center() + LEFT * 0.28 + DOWN * 0.12)
    return VGroup(corpo, faixa, chip)


# ---------------------------------------------------------------- linhas 1 e 2: as três perguntas

PERGUNTAS = ["menos de 30?", "casado?", "atraso 2+ meses?"]
Y_PERGUNTAS = [3.15, 1.0, -1.15]
LARG_PERGUNTA, ALT_PERGUNTA = 6.6, 1.6


def titulo_prever():
    """Cartão + "prever calote" grande no alto (linha 1): VGroup(cartão, conta("prever", " ", "calote"))."""
    t = conta("prever", " ", "calote", tamanho=64, cores={2: VERMELHO})
    return VGroup(cartao(), t).arrange(RIGHT, buff=0.35).move_to(ponto(0, 4.95))


def perguntas(acesa=2):
    """As três caixas com o texto, a `acesa` em amarelo (fim da linha 1); acesa=None: todas em azul."""
    cx = []
    for i, (t, y) in enumerate(zip(PERGUNTAS, Y_PERGUNTAS)):
        c = caixa(t, tamanho=56, largura=LARG_PERGUNTA, altura=ALT_PERGUNTA).move_to(ponto(0, y))
        if i == acesa:
            c.set_color(AMARELO)
        cx.append(c)
    return VGroup(*cx)


# ---------------------------------------------------------------- a nuvem de 300 clientes (1 ponto = 100)

def _nuvem_base():
    """300 posições num quadriculado de 20 x 15 com um tremido, centradas em 0, e as cores (vermelho = calote)."""
    rng = np.random.default_rng(7)
    pos = []
    for lin in range(15):
        for col in range(20):
            pos.append(ponto(col - 9.5 + rng.uniform(-0.28, 0.28), 7 - lin + rng.uniform(-0.28, 0.28)))
    vermelhos = set(rng.choice(300, NUVEM["vermelhos"], replace=False).tolist())
    cores = [VERMELHO if i in vermelhos else VERDE for i in range(300)]
    # Quem vai para o lado "sim" na linha 8: 22 dos vermelhos e 9 dos verdes, sorteados.
    v = sorted(vermelhos)
    g = [i for i in range(300) if i not in vermelhos]
    sim = set(rng.choice(v, PT_SIM["vermelhos"], replace=False).tolist()) | set(
        rng.choice(g, PT_SIM["verdes"], replace=False).tolist())
    return np.array(pos), cores, sim


NUVEM_POS, NUVEM_COR, NUVEM_SIM = _nuvem_base()


def legenda_cores(tamanho=G, raio=0.12):
    """"● pagou   ● calote" na mesma linha de base: VGroup(VGroup(ponto, pagou), VGroup(ponto, calote))."""
    t = conta("pagou", "        ", "calote", tamanho=tamanho, cores={0: VERDE, 2: VERMELHO})
    itens = []
    for parte, cor in ((t[0], VERDE), (t[2], VERMELHO)):
        d = Dot(radius=raio, color=cor).next_to(parte, LEFT, buff=0.18)
        d.set_y(parte[1].get_y())  # o "a" das duas palavras: mesma altura
        itens.append(VGroup(d, parte))
    return VGroup(*itens)


def nuvem(centro, passo, raio, cor=True):
    """Os 300 pontos com o centro em `centro` e `passo` unidades entre vizinhos. cor=False: todos cinza."""
    return VGroup(*(Dot(np.array(centro) + p * passo, radius=raio, color=(c if cor else CINZA))
                    for p, c in zip(NUVEM_POS, NUVEM_COR)))


# Linha 2 (tela toda): título e crédito no alto, a nuvem, as legendas e o contador embaixo.
NUVEM_2 = dict(centro=ponto(0, 1.55), passo=0.29, raio=0.1)
Y_TITULO_2, Y_FONTE_2 = 5.17, 4.3
Y_LEGENDA_2, Y_CORES_2, Y_CONTADOR_2, Y_FRACAO_2 = -1.2, -1.98, -3.1, -4.08
# Linha 4 (no alto, acima do canto)
NUVEM_4 = dict(centro=ponto(0, 3.6), passo=0.25, raio=0.085)
SORTEADOS = (int(np.flatnonzero(np.array(NUVEM_COR) == VERDE)[123]), int(np.flatnonzero(np.array(NUVEM_COR) == VERMELHO)[17]))
POS_DOIS = (ponto(-1.55, -0.05), ponto(1.55, -0.05))
RAIO_DOIS = 0.7


def dois_clientes(revelados=True):
    """Fim da linha 4: os dois clientes sorteados, "1º" e "2º" embaixo, e o "≠" amarelo entre eles."""
    d = VGroup(*(Dot(p, radius=RAIO_DOIS, color=(NUVEM_COR[i] if revelados else CINZA))
                 for p, i in zip(POS_DOIS, SORTEADOS)))
    nomes = VGroup(*(rotulo(t, tamanho=G).next_to(x, DOWN, buff=0.3) for t, x in zip(("1º", "2º"), d)))
    dif = rotulo("≠", cor=AMARELO, tamanho=130).move_to(ponto(0, POS_DOIS[0][1]))
    return d, nomes, dif


# ---------------------------------------------------------------- linhas 5 e 6: o quadrado das chances

# Linhas = 1º cliente (de cima para baixo: paga, calote); colunas = 2º cliente (paga, calote).
Q_LADO = 4.6
Q_ESQ, Q_TOPO = -1.5, 4.32  # canto de cima à esquerda do quadrado
Q_A = Q_LADO * P_PAGA  # trecho "paga" (0,78)
Q_B = Q_LADO * P_CAL  # trecho "calote" (0,22)
X1, X2 = Q_ESQ + Q_A, Q_ESQ + Q_LADO
Y1, Y2 = Q_TOPO - Q_A, Q_TOPO - Q_LADO
E_REGUA = 0.2  # espessura das réguas de cor
FOLGA_REGUA = 0.14


def _ret(x0, y0, x1, y1, cor, opac=0.0):
    """Retângulo pelos cantos: (x0, y0) em cima à esquerda, (x1, y1) embaixo à direita."""
    return Rectangle(width=x1 - x0, height=y0 - y1, stroke_width=0, fill_color=cor,
                     fill_opacity=opac).move_to(ponto((x0 + x1) / 2, (y0 + y1) / 2))


def quadrado():
    """O quadrado das chances: dict com as celas (pp, pc, cp, cc), a borda, a grade, as réguas de cor dos dois
    lados com os números e os nomes "1º" (linhas) e "2º" (colunas)."""
    x0, y0, e, f = Q_ESQ, Q_TOPO, E_REGUA, FOLGA_REGUA
    celas = {"pp": _ret(x0, y0, X1, Y1, VERDE), "pc": _ret(X1, y0, X2, Y1, AMARELO),
             "cp": _ret(x0, Y1, X1, Y2, AMARELO), "cc": _ret(X1, Y1, X2, Y2, VERMELHO)}
    borda = Rectangle(width=Q_LADO, height=Q_LADO, color=BRANCO, stroke_width=ESPESSURA).move_to(
        ponto((x0 + X2) / 2, (y0 + Y2) / 2))
    grade = VGroup(Line(ponto(X1, y0), ponto(X1, Y2)), Line(ponto(x0, Y1), ponto(X2, Y1))).set_stroke(BRANCO, 3)
    lado = VGroup(_ret(x0 - f - e, y0, x0 - f, Y1, VERDE, 1), _ret(x0 - f - e, Y1, x0 - f, Y2, VERMELHO, 1))
    topo = VGroup(_ret(x0, y0 + f + e, X1, y0 + f, VERDE, 1), _ret(X1, y0 + f + e, X2, y0 + f, VERMELHO, 1))
    n_lado = VGroup(rotulo(br(P_PAGA), cor=VERDE, tamanho=48).next_to(lado[0], LEFT, buff=0.15),
                    rotulo(br(P_CAL), cor=VERMELHO, tamanho=48).next_to(lado[1], LEFT, buff=0.15))
    n_topo = VGroup(rotulo(br(P_PAGA), cor=VERDE, tamanho=48).next_to(topo[0], UP, buff=0.15),
                    rotulo(br(P_CAL), cor=VERMELHO, tamanho=48).next_to(topo[1], UP, buff=0.15))
    # "2º →" no canto de cima, na altura dos números de cima; "1º ↓" embaixo dele, sobre os números do lado
    r2_ = rotulo("2º", tamanho=G)
    s2 = Arrow(ORIGIN, RIGHT * 0.7, buff=0, color=BRANCO, stroke_width=ESPESSURA, tip_length=0.22)
    quem_topo = VGroup(r2_, s2).arrange(RIGHT, buff=0.12).next_to(n_topo[0], LEFT, buff=0.5)
    quem_topo.set_y(n_topo[0].get_y())
    r1_ = rotulo("1º", tamanho=G)
    s1 = Arrow(ORIGIN, DOWN * 0.7, buff=0, color=BRANCO, stroke_width=ESPESSURA, tip_length=0.22)
    quem_lado = VGroup(r1_, s1).arrange(DOWN, buff=0.1).next_to(n_lado[0], UP, buff=0.3)
    return dict(celas=celas, borda=borda, grade=grade, lado=lado, topo=topo, n_lado=n_lado, n_topo=n_topo,
                quem_lado=quem_lado, quem_topo=quem_topo)


def quadrado_base(q):
    return VGroup(*q["celas"].values(), q["grade"], q["borda"], q["lado"], q["topo"], q["n_lado"], q["n_topo"],
                  q["quem_lado"], q["quem_topo"])


def pontas_reguas():
    """Onde os dois clientes da linha 4 param antes de virar as réguas: no começo de cada régua."""
    x0, y0 = Q_ESQ - FOLGA_REGUA - E_REGUA / 2, Q_TOPO
    return ponto(x0, y0), ponto(Q_ESQ, Q_TOPO + FOLGA_REGUA + E_REGUA / 2)


Y_CALOTE_5, Y_ROTULO_CAL_5, Y_SOMA, Y_IGUAIS = -0.9, -1.6, -2.85, -3.65


def contas_5():
    """Peças das contas da linha 5 (posições finais)."""
    q = quadrado()
    pp = q["celas"]["pp"]
    vezes_p = conta(br(P_PAGA), " × ", br(P_PAGA), tamanho=FC)
    igual_p = conta("= ", br(Q_PAGA), tamanho=64).next_to(vezes_p, DOWN, buff=0.3)
    dois_pagam = rotulo("os dois pagam", tamanho=PQ).next_to(vezes_p, UP, buff=0.45)
    VGroup(vezes_p, igual_p, dois_pagam).move_to(pp)
    # A cela vermelha é pequena: a conta dela fica logo embaixo, encostada à direita, com o nome embaixo.
    vezes_c = conta(br(P_CAL), " × ", br(P_CAL), " = ", br(Q_CAL), tamanho=G)
    vezes_c.move_to(ponto(0, Y_CALOTE_5)).align_to(ponto(X2, 0), RIGHT)
    dois_calote = rotulo("os dois: calote", cor=VERMELHO, tamanho=44).move_to(ponto(0, Y_ROTULO_CAL_5)).align_to(
        ponto(X2, 0), RIGHT)
    soma = conta(br(Q_PAGA), " + ", br(Q_CAL), " = ", br(IGUAIS), tamanho=56).move_to(ponto(0, Y_SOMA))
    iguais = rotulo("iguais", cor=AMARELO, tamanho=G).move_to(ponto(0, Y_IGUAIS))
    return dict(vezes_p=vezes_p, igual_p=igual_p, dois_pagam=dois_pagam, vezes_c=vezes_c, dois_calote=dois_calote,
                soma=soma, iguais=iguais)


def acender_5(q):
    """As celas da diagonal acesas (estado do fim da linha 5)."""
    q["celas"]["pp"].set_fill(opacity=0.4)
    q["celas"]["cc"].set_fill(opacity=0.8)
    return q


def quadrados_6():
    """Linha 6, em "resto": "0,78 × 0,78" vira "0,78²" na cela verde e "0,22 × 0,22 = 0,05" vira "0,22² = 0,05"."""
    c = contas_5()
    qp = conta(br(P_PAGA) + "²", tamanho=56).move_to(c["vezes_p"])
    qc = conta(br(P_CAL) + "²", " = ", br(Q_CAL), tamanho=G).move_to(c["vezes_c"]).align_to(ponto(X2, 0), RIGHT)
    return qp, qc


def contas_6():
    """Linha 6: a conta inteira (a soma da linha 5, agora com os quadrados) e, em "nome", o 0,34 grande com o
    nome e dois apartes em cinza (a conta sai: o 0,34 dela é o que cresce)."""
    l1 = conta("1 − (", br(P_PAGA) + "²", " + ", br(P_CAL) + "²" + FINO, ")", tamanho=56, cores={1: VERDE, 3: VERMELHO})
    l2 = conta("= 1 − ", br(IGUAIS), " = ", br(G_RAIZ), tamanho=56, cores={3: AMARELO})
    l1.move_to(ponto(0, -1.95))
    l2.move_to(ponto(0, -2.8))
    grande = rotulo(br(G_RAIZ), cor=AMARELO, tamanho=110).move_to(ponto(0, -1.8))
    nome = rotulo("impureza de Gini", cor=AMARELO, tamanho=60).move_to(ponto(0, -2.9))
    aparte = VGroup(rotulo("≠ Gini da renda", cor=CINZA, tamanho=PQ),
                    rotulo("outra medida: entropia", cor=CINZA, tamanho=PQ)).arrange(DOWN, buff=0.18)
    aparte.move_to(ponto(0, -3.95))
    return l1, l2, grande, nome, aparte


# ---------------------------------------------------------------- linhas 8 e 9: a régua da bagunça inteira

# A régua fica na coluna da direita; embaixo ela passa à direita do seu canto (que vai só até x = -0,44).
X_R = 1.8
Y0, Y_MEIO = -3.2, 3.5  # Gini 0 ("puro") e 0,5 ("meio a meio")
K = (Y_MEIO - Y0) / 0.5  # 13,4 unidades por 1 de Gini: 0,01 = 18 px


def y_g(g):
    return Y0 + K * g


def _bloco(cores, centro, raio=0.1):
    return VGroup(*(Dot(radius=raio, color=c) for c in cores)).arrange_in_grid(2, 2, buff=0.07).move_to(centro)


def regua():
    """A régua vertical de 0 ("puro") a 0,5 ("meio a meio"), com tracinhos a cada 0,1, os números das pontas,
    os grupinhos (puro: todos da mesma cor; meio a meio: xadrez) e o título "bagunça" no alto."""
    linha = Line(ponto(X_R, Y0), ponto(X_R, Y_MEIO), color=BRANCO, stroke_width=ESPESSURA)
    tiques = VGroup(*(Line(ponto(X_R - 0.13, y_g(g / 10)), ponto(X_R + 0.13, y_g(g / 10)), color=CINZA,
                           stroke_width=3) for g in range(6)))
    n0 = rotulo("0", cor=CINZA, tamanho=PEQUENO).next_to(ponto(X_R + 0.13, Y0), RIGHT, buff=0.15)
    n5 = rotulo("0,5", cor=CINZA, tamanho=PEQUENO).next_to(ponto(X_R + 0.13, Y_MEIO), RIGHT, buff=0.15)
    puro = rotulo("puro", tamanho=PQ).move_to(ponto(X_R, Y0 - 0.45))
    g_puro = _bloco([VERDE] * 4, ponto(X_R, Y0 - 0.98))
    g_meio = _bloco([VERDE, VERMELHO, VERMELHO, VERDE], ponto(X_R, Y_MEIO + 0.42))
    meio = rotulo("meio a meio", tamanho=PQ).move_to(ponto(X_R, Y_MEIO + 0.98))
    nome = rotulo("bagunça", tamanho=44).move_to(ponto(X_R, Y_MEIO + 1.55))
    return dict(linha=linha, tiques=tiques, n0=n0, n5=n5, puro=puro, g_puro=g_puro, g_meio=g_meio, meio=meio,
                nome=nome)


def regua_toda():
    r = regua()
    return VGroup(*r.values())


def marcador(g, cor=BRANCO, numero=None, nome=None, tamanho=PQ, y=None):
    """Marca na régua: VGroup(traço, número[, nome]). Número à direita, nome (texto ou mobject) à esquerda."""
    yy = y_g(g) if y is None else y
    traco = Line(ponto(X_R - 0.24, yy), ponto(X_R + 0.24, yy), color=cor, stroke_width=ESPESSURA + 2)
    num = rotulo(numero or br(g), cor=cor, tamanho=tamanho).next_to(traco, RIGHT, buff=0.13)
    partes = [traco, num]
    if nome is not None:
        n = rotulo(nome, cor=cor, tamanho=PQ) if isinstance(nome, str) else nome
        partes.append(n.next_to(traco, LEFT, buff=0.15))
    return VGroup(*partes)


def com_antes(m, lado=UP):
    """Põe "antes" em cima (ou embaixo) do número de uma marca: a bagunça dos 30 mil, antes de qualquer pergunta."""
    return VGroup(*m, rotulo("antes", tamanho=PEQUENO).next_to(m[1], lado, buff=0.1).align_to(m[1], LEFT))


def marcadores_8():
    """Marcas das linhas 8 e 9 (só o traço e o número, à direita: à esquerda ficam os grupos): os 30 mil
    ("antes", 0,34), o lado sim (0,42, vermelho) e o lado não (0,28, verde)."""
    return dict(todos=com_antes(marcador(G_RAIZ, BRANCO)), sim=marcador(G_SIM, VERMELHO),
                nao=marcador(G_NAO, VERDE))


# A árvore das linhas 8 e 9, na coluna da esquerda: pergunta no alto, "sim" à esquerda, "não" à direita.
RAIZ_8 = ponto(-1.6, 4.62)
PASSO_W, RAIO_W = 0.19, 0.075  # quadriculado dos grupos (1 ponto = 100 clientes)
W_SIM_COLS, W_NAO_COLS = 6, 14  # o "sim" quase quadrado (cabem os números embaixo dele), o "não" alto
BASE_W = -0.66  # base dos dois quadriculados
X_W_SIM, X_W_NAO = -2.8, -0.49  # centros
X_SAI = {"sim": -1.95, "nao": X_W_NAO}  # de onde cada seta sai, embaixo da pergunta


def pergunta_vencedora():
    return caixa("atraso\n2+ meses?", tamanho=44).move_to(RAIZ_8)


def quadriculado(n_verm, n_verde, cols, cx):
    """Posições de um grupo arrumado de baixo para cima, vermelhos primeiro (a mistura vira um nível)."""
    pos = []
    for k in range(n_verm + n_verde):
        lin, col = divmod(k, cols)
        pos.append(ponto(cx + (col - (cols - 1) / 2) * PASSO_W, BASE_W + RAIO_W + lin * PASSO_W))
    return pos[:n_verm], pos[n_verm:]


def _lados_8():
    """{índice do ponto: posição} depois da divisão."""
    v_s, g_s = quadriculado(PT_SIM["vermelhos"], PT_SIM["verdes"], W_SIM_COLS, X_W_SIM)
    v_n, g_n = quadriculado(PT_NAO["vermelhos"], PT_NAO["verdes"], W_NAO_COLS, X_W_NAO)
    filas = {"sv": iter(v_s), "sg": iter(g_s), "nv": iter(v_n), "ng": iter(g_n)}
    return {i: next(filas[("s" if i in NUVEM_SIM else "n") + ("v" if c == VERMELHO else "g")])
            for i, c in enumerate(NUVEM_COR)}


LADOS_8 = _lados_8()
NUVEM_8 = dict(centro=ponto(-1.25, 1.2), passo=0.19, raio=RAIO_W)


def pontos_divididos():
    return VGroup(*(Dot(LADOS_8[i], radius=RAIO_W, color=c) for i, c in enumerate(NUVEM_COR)))


def indices(lado):
    return [i for i in range(300) if (i in NUVEM_SIM) == (lado == "sim")]


def topo_grupo(lado):
    return max(LADOS_8[i][1] for i in indices(lado)) + RAIO_W


def galhos_8():
    """As duas setas, desenhadas igual, da pergunta até o topo de cada grupo, e "sim"/"não" ao lado delas."""
    raiz = pergunta_vencedora()
    setas, nomes = {}, {}
    for lado, cx in (("sim", X_W_SIM), ("nao", X_W_NAO)):
        setas[lado] = seta(ponto(X_SAI[lado], raiz.get_bottom()[1]), ponto(cx, topo_grupo(lado) + 0.14), cor=CINZA)
        nomes[lado] = ao_lado(setas[lado], "sim" if lado == "sim" else "não", LEFT if lado == "sim" else RIGHT,
                              tamanho=PQ, buff=0.18)
    return setas, nomes


def rotulos_grupos():
    """Contagem e % de calote embaixo de cada grupo, centradas nele."""
    out = {}
    for lado, cx, d, pct in (("s", X_W_SIM, SIM, PCT_CAL_SIM), ("n", X_W_NAO, NAO, PCT_CAL_NAO)):
        out["cont_" + lado] = rotulo(br(d["n"], 0), tamanho=PEQUENO).move_to(ponto(cx, BASE_W - 0.34))
        out["pct_" + lado] = rotulo(pct + "%", cor=VERMELHO, tamanho=PEQUENO).move_to(ponto(cx, BASE_W - 0.84))
    return out


Y_LINHAS = (-2.35, -3.15)  # as duas linhas da conta de um lado (linhas 8 e 9), embaixo à esquerda


def conta_lado(pa, pc, g, tamanho=44):
    """A conta do Gini de um lado em duas linhas, alinhadas à esquerda: 1 − (0,30² + 0,70²) / = 1 − 0,58 = 0,42"""
    qa, qc = r2(pa ** 2), r2(pc ** 2)
    l1 = conta("1 − (", br(pa), "²", " + ", br(pc), "²" + FINO, ")", tamanho=tamanho, cores={1: VERDE, 4: VERMELHO})
    l2 = conta("= 1 − ", br(r2(qa + qc)), " = ", br(g), tamanho=tamanho)
    for linha, y in zip((l1, l2), Y_LINHAS):
        linha.move_to(ponto(0, y)).align_to(ponto(-LADO + 0.08, 0), LEFT)
    return l1, l2


def estado_8():
    """Fim da linha 8 = começo da 9."""
    raiz = pergunta_vencedora()
    setas, nomes = galhos_8()
    rg = rotulos_grupos()
    linhas = conta_lado(S_PAGA, S_CAL, G_SIM)
    linhas[1][3].set_color(VERMELHO)
    return dict(raiz=raiz, setas=setas, nomes=nomes, pts=pontos_divididos(), cont_s=rg["cont_s"], pct_s=rg["pct_s"],
                linhas=linhas, regua=regua_toda(), m=marcadores_8())


def apagar_sim(e):
    """O lado "sim" sai de foco (linha 9 em diante): pontos, seta e números apagados."""
    for i in indices("sim"):
        e["pts"][i].set_opacity(0.3)
    e["setas"]["sim"].set_color(APAGADO)
    e["nomes"]["sim"].set_color(CINZA)
    e["cont_s"].set_color(CINZA)
    e["pct_s"].set_color(APAGADO)
    return e


def estado_9():
    """Fim da linha 9 = começo da 10: o lado "sim" apagado, o "não" com contagem e %, a régua com as três marcas."""
    e = estado_8()
    del e["linhas"]
    rg = rotulos_grupos()
    e["cont_n"], e["pct_n"] = rg["cont_n"], rg["pct_n"]
    return apagar_sim(e)


# ---------------------------------------------------------------- linhas 10 a 14: a régua ampliada (lupa)

# Da linha 10 em diante as diferenças são de 0,01 (0,34 x 0,35; 0,29 x 0,28 x 0,30): a régua mostra só o
# trecho de 0,27 a 0,36, ampliado (0,01 = 126 px). O que passa de 0,36 fica numa seta no alto.
Z_MIN, Z_MAX = 0.27, 0.36
ZY0, ZY1 = -3.9, 4.5
KZ = (ZY1 - ZY0) / (Z_MAX - Z_MIN)


def y_z(g):
    return ZY0 + KZ * (g - Z_MIN)


def regua_zoom():
    """A régua ampliada: linha, tracinhos a cada 0,01 e os números das pontas em cinza."""
    linha = Line(ponto(X_R, ZY0 - 0.15), ponto(X_R, ZY1 + 0.15), color=BRANCO, stroke_width=ESPESSURA)
    tiques = VGroup(*(Line(ponto(X_R - 0.12, y_z(Z_MIN + k / 100)), ponto(X_R + 0.12, y_z(Z_MIN + k / 100)),
                           color=CINZA, stroke_width=3) for k in range(10)))
    n_baixo = rotulo(br(Z_MIN), cor=CINZA, tamanho=PEQUENO).next_to(ponto(X_R + 0.12, ZY0), RIGHT, buff=0.15)
    n_cima = rotulo(br(Z_MAX), cor=CINZA, tamanho=PEQUENO).next_to(ponto(X_R + 0.12, ZY1), RIGHT, buff=0.15)
    return VGroup(linha, tiques, n_baixo, n_cima)


def marca_z(g, cor=BRANCO, numero=None, nome=None, tamanho=44):
    """Marca na régua ampliada (veja marcador)."""
    return marcador(g, cor, numero=numero, nome=nome, tamanho=tamanho, y=y_z(g))


def marca_antes():
    """0,34: a bagunça antes de qualquer pergunta. Número à direita e "antes" em cima dele."""
    return com_antes(marca_z(G_RAIZ, BRANCO), DOWN)  # em cima fica o 0,35 (linha 10)


def acima_da_regua(numero, cor):
    """Valor que passa do topo da régua ampliada: setinha para cima e o número, no alto."""
    tri = Triangle(color=cor, fill_opacity=1, stroke_width=0).scale(0.16).move_to(ponto(X_R, ZY1 + 0.55))
    num = rotulo(numero, cor=cor, tamanho=PQ).next_to(tri, RIGHT, buff=0.2)
    return VGroup(tri, num)


# Linha 10: os dois lados viram barras com largura proporcional ao número de clientes (0,10 e 0,90 de 3,2),
# cada uma com a sua mistura (vermelho embaixo, como nos quadriculados). Ficam no alto da coluna da esquerda.
BARRA_BASE, BARRA_ALT = 3.85, 0.8
LARG_BARRAS = 3.2
X_BARRA = {"sim": (-3.35, -3.35 + V["peso_sim"] * LARG_BARRAS), "nao": (1.25 - V["peso_nao"] * LARG_BARRAS, 1.25)}
Y_CONTAS_10 = (2.65, 1.8, 0.95, 0.1)  # linhas das contas embaixo das barras


def barra(lado):
    x0, x1 = X_BARRA[lado]
    d = SIM if lado == "sim" else NAO
    h_cal = BARRA_ALT * d["calote"] / d["n"]
    verm = _ret(x0, BARRA_BASE + h_cal, x1, BARRA_BASE, VERMELHO, 0.85)
    verde = _ret(x0, BARRA_BASE + BARRA_ALT, x1, BARRA_BASE + h_cal, VERDE, 0.85)
    return VGroup(verm, verde)


def rotulos_barras():
    """Gini em cima de cada barra; embaixo, a contagem (c_) e o peso (p_), a fração dos clientes."""
    sim, nao = barra("sim"), barra("nao")
    out = dict(g_s=rotulo(br(G_SIM), cor=VERMELHO, tamanho=44).next_to(sim, UP, buff=0.15).align_to(sim, LEFT),
               g_n=rotulo(br(G_NAO), cor=VERDE, tamanho=44).next_to(nao, UP, buff=0.15))
    for k, n, w, b in (("s", SIM["n"], W_SIM, sim), ("n", NAO["n"], W_NAO, nao)):
        for pre, t, tam in (("c_", br(n, 0), PQ), ("p_", br(w), 44)):
            r = rotulo(t, tamanho=tam).next_to(b, DOWN, buff=0.18)
            if k == "s":
                r.align_to(b, LEFT)
            out[pre + k] = r
    return out


def conta_sem_peso():
    l1 = conta("(", br(G_SIM), " + ", br(G_NAO), ") ÷ 2", tamanho=44, cores={1: VERMELHO, 3: VERDE})
    l2 = conta("= ", br(MEDIA_SEM_PESO), tamanho=FC, cor=VERMELHO)
    nome = rotulo("sem peso", cor=VERMELHO, tamanho=44).next_to(l2, RIGHT, buff=0.4)
    for l, y in zip((l1, l2), Y_CONTAS_10):
        l.move_to(ponto(0, y)).align_to(ponto(-LADO + 0.2, 0), LEFT)  # folga para o risco
    nome.next_to(l2, RIGHT, buff=0.4)
    return l1, l2, nome


def conta_ponderada():
    l1 = conta(br(W_SIM), " × ", br(G_SIM), tamanho=FC, cores={2: VERMELHO})
    l2 = conta("+ ", br(W_NAO), " × ", br(G_NAO), tamanho=FC, cores={3: VERDE})
    l3 = conta("= ", br(PROD_SIM), " + ", br(PROD_NAO), tamanho=FC)
    l4 = conta("= ", br(G_POND), tamanho=FC, cor=AMARELO)
    for l, y in zip((l1, l2, l3, l4), Y_CONTAS_10):
        l.move_to(ponto(0, y)).align_to(ponto(-LADO + 0.08, 0), LEFT)
    l1.shift(RIGHT * (l2[1].get_left()[0] - l1[0].get_left()[0]))  # 0,10 embaixo do 0,90: os produtos alinhados
    nome = rotulo("média ponderada", cor=AMARELO, tamanho=44).next_to(l4, DOWN, buff=0.3).align_to(l4, LEFT)
    return l1, l2, l3, l4, nome


def marca_sem_peso():
    """0,35, a média sem peso, em vermelho na régua ampliada: acima do 0,34."""
    return marca_z(MEDIA_SEM_PESO, VERMELHO)


def marcas_10():
    """Fim da linha 10 na régua ampliada: antes (0,34), não (0,28, verde), sim (0,42, acima) e a ponderada (0,29)."""
    return dict(antes=marca_antes(), nao=marca_z(G_NAO, VERDE), sim=acima_da_regua(br(G_SIM), VERMELHO),
                pond=marca_z(G_POND, AMARELO))


def estado_10():
    """Fim da linha 10 = começo da 11: barras, contas da média ponderada, régua ampliada com as marcas."""
    rb = {k: v for k, v in rotulos_barras().items() if k[0] in "gp"}  # os Ginis e os pesos (as contagens já viraram pesos)
    return dict(regua=regua_zoom(), barras=VGroup(barra("sim"), barra("nao")), rb=rb, conta=conta_ponderada(),
                m=marcas_10())


def contas_11():
    """Linha 11: a ponderada sobe; quanto a pergunta tirou (0,05, a redução de impureza) e quanto isso é da
    bagunça de antes (15%)."""
    esq = ponto(-LADO + 0.08, 0)
    pond = VGroup(rotulo(br(G_POND), cor=AMARELO, tamanho=60), rotulo("média ponderada", cor=AMARELO, tamanho=PQ)
                  ).arrange(DOWN, buff=0.12, aligned_edge=LEFT).move_to(ponto(0, 4.55)).align_to(esq, LEFT)
    a = conta(br(G_RAIZ), " − ", br(G_POND), " = ", br(GANHO), tamanho=44, cores={2: AMARELO, 4: AMARELO})
    a.move_to(ponto(0, 3.15)).align_to(esq, LEFT)
    nome = texto("redução de\nimpureza", cor=AMARELO, tamanho=PQ).next_to(a, DOWN, buff=0.2).align_to(
        a[4], RIGHT).shift(LEFT * 0.3)
    b = conta(br(GANHO), " ÷ ", br(G_RAIZ), " ≈ ", f"{PCT_TIRADO}%", tamanho=44, cores={0: AMARELO})
    b.move_to(ponto(0, 1.2)).align_to(esq, LEFT)
    grande = rotulo(f"{PCT_TIRADO}%", cor=AMARELO, tamanho=110).move_to(ponto(0, 0.0)).align_to(esq, LEFT)
    da = rotulo("da bagunça", tamanho=G).next_to(grande, DOWN, buff=0.2).align_to(esq, LEFT)
    return pond, a, nome, b, grande, da


def seta_regua():
    """O trecho da régua ampliada do 0,34 ao 0,29, em amarelo, com a ponta para baixo."""
    return Arrow(ponto(X_R, y_z(G_RAIZ)), ponto(X_R, y_z(G_POND)), buff=0, color=AMARELO, stroke_width=ESPESSURA + 6,
                 tip_length=0.4, max_tip_length_to_length_ratio=0.2, max_stroke_width_to_length_ratio=20)


# ---------------------------------------------------------------- linhas 13 e 14: outras perguntas na mesma régua

X_COL = -1.55  # coluna das caixas à esquerda
POS_13 = {"idade": ponto(X_COL, 3.8), "civil": ponto(X_COL, 1.3)}
LARG_COL, ALT_COL = 3.8, 1.2


def referencia_atraso():
    """A pergunta do atraso, apagada no 0,29 (linha 13): o que um corte bom faz, para comparar."""
    nome = VGroup(rotulo("atraso", cor=CINZA, tamanho=PEQUENO), rotulo(f"tira {PCT_TIRADO}%", cor=CINZA,
                                                                       tamanho=PEQUENO)).arrange(DOWN, buff=0.1,
                                                                                                 aligned_edge=RIGHT)
    m = marca_z(G_POND, CINZA, nome=nome, tamanho=PQ)
    m[2].align_to(m[0], DOWN).shift(UP * 0.08)  # o nome em cima do traço: embaixo à esquerda fica o seu canto
    return m


def candidatos_13(final=True):
    """As caixas da linha 1 ("menos de 30?", "casado?") ou, final=True, as colunas ("idade", "estado civil"),
    com o quanto o melhor corte de cada uma tira da bagunça, embaixo."""
    textos = ("idade", "estado civil") if final else ("menos de 30?", "casado?")
    cx = {k: caixa(t, tamanho=48, largura=LARG_COL, altura=ALT_COL).move_to(POS_13[k])
          for k, t in zip(("idade", "civil"), textos)}
    tira = {k: rotulo(f"tira {p}", tamanho=G).next_to(cx[k], DOWN, buff=0.25)
            for k, p in (("idade", PCT_IDADE), ("civil", PCT_CIVIL))}
    return cx, tira


def triangulo(g, x, cor=CINZA):
    """Marca de uma pergunta na régua ampliada: triângulo apontando para ela, à esquerda, no Gini ponderado."""
    return Triangle(color=cor, fill_opacity=1, stroke_width=0).rotate(-PI / 2).scale(0.22).move_to(ponto(x, y_z(g)))


X_TRI = {"idade": X_R - 0.45, "civil": X_R - 0.88}


def setinhas_13():
    """As marcas de idade e estado civil: param coladas no 0,34 (o melhor corte de cada uma), lado a lado."""
    return {"idade": triangulo(G_IDADE, X_TRI["idade"]), "civil": triangulo(G_CIVIL, X_TRI["civil"])}


def ligacoes_13(cx, tri):
    """Linha tracejada da caixa até a marca dela na régua."""
    return {k: DashedLine(cx[k].get_right() + RIGHT * 0.08, tri[k].get_left() + LEFT * 0.06, color=AZUL,
                          stroke_width=4, dash_length=0.12) for k in cx}


UM_MES_SIM = (round(UM_MES["sim"]["calote"] / 100), round(UM_MES["sim"]["pagou"] / 100))  # 34 e 34 pontos


def marcas_14():
    """As duas perguntas da coluna de setembro na régua ampliada, cada uma com o nome à esquerda e o número
    à direita: "2+ meses?" no 0,29 (em amarelo, a vencedora) e "1+ mês?" no 0,30."""
    return {"dois": marca_z(G_POND, AMARELO, nome=rotulo("2+ meses?", cor=AMARELO, tamanho=44)),
            "um": marca_z(G_POND_1MES, BRANCO, nome=rotulo("1+ mês?", tamanho=44))}


def corte_1mes():
    """À esquerda: a caixa "1+ mês?" se divide. O lado "sim" (6.818 clientes, 1 ponto = 100: 34 vermelhos e
    34 verdes, meio a meio) e o "não" (23.182, em cinza)."""
    cx = caixa("1+ mês?", tamanho=G).move_to(ponto(-1.75, 4.45))
    v, g = UM_MES_SIM
    passo, cols, cx_w, base = 0.28, 8, -2.3, 0.35
    pos = []
    for k in range(v + g):
        lin, col = divmod(k, cols)
        pos.append(ponto(cx_w + (col - (cols - 1) / 2) * passo, base + lin * passo))
    pts = VGroup(*(Dot(p, radius=0.1, color=VERMELHO if k < v else VERDE) for k, p in enumerate(pos)))
    s_sim = seta(ponto(-2.2, cx.get_bottom()[1]), ponto(cx_w, pts.get_top()[1] + 0.12), cor=CINZA)
    nao = rotulo(br(UM_MES["nao"]["n"], 0), cor=CINZA, tamanho=44).move_to(ponto(0.2, 3.0))
    s_nao = seta(ponto(-1.2, cx.get_bottom()[1]), nao.get_top() + UP * 0.1 + LEFT * 0.3, cor=CINZA)
    n_sim, n_nao = ao_lado(s_sim, "sim", LEFT), ao_lado(s_nao, "não", RIGHT)
    n6818 = rotulo(br(UM_MES["sim"]["n"], 0), tamanho=44).next_to(pts, DOWN, buff=0.22)
    pct = rotulo(f"{PCT_SIM_1MES}%", cor=VERMELHO, tamanho=80).next_to(pts, RIGHT, buff=0.35).align_to(pts, UP)
    pct.shift(DOWN * 0.35)  # longe do 23.182, em cima
    calote = rotulo("calote", cor=VERMELHO, tamanho=PQ).next_to(pct, DOWN, buff=0.12)
    gini = VGroup(rotulo("bagunça", cor=VERMELHO, tamanho=PQ), rotulo(br(G_SIM_1MES), cor=VERMELHO, tamanho=60)
                  ).arrange(DOWN, buff=0.1, aligned_edge=LEFT).next_to(calote, DOWN, buff=0.35).align_to(pct, LEFT)
    return dict(caixa=cx, pts=pts, s_sim=s_sim, s_nao=s_nao, n_sim=n_sim, n_nao=n_nao, nao=nao, n6818=n6818,
                pct=pct, calote=calote, gini=gini)


def estado_14():
    """Fim da linha 14 = começo da 15."""
    m = marcas_14()
    return dict(regua=regua_zoom(), antes=marca_antes(), dois=m["dois"], um=m["um"], corte=corte_1mes())


# ---------------------------------------------------------------- linhas 15 e 16: a árvore gulosa e a fantasma

JULHO = "julho\nquitado?"  # PAY_3 <= -0,5: julho pago em dia (código -1) ou sem nada a pagar (-2)
AGOSTO = "agosto\n2+?"  # PAY_2 >= 2: dois meses ou mais de atraso em agosto


def arvore(raiz, esq, dir_, centro_raiz, y_filhos, x_filhos, tamanho=52, cor=AZUL, contas=None, fantasma=False,
           tam_filhos=None, lado_nao=RIGHT):
    """Árvore de 2 níveis: raiz, "sim" à esquerda e "não" à direita. dict com caixas, setas e rótulos das setas
    (ao lado delas). contas: (texto do lado sim, texto do lado não), em cinza, embaixo de cada filho.
    fantasma: tudo em cinza, contornos tracejados."""
    ct = CINZA if fantasma else BRANCO
    cor = CINZA if fantasma else cor
    r = caixa(raiz, tamanho=tamanho, cor=cor, cor_texto=ct, tracejada=fantasma).move_to(centro_raiz)
    tf = tam_filhos or tamanho
    a = caixa(esq, tamanho=tf, cor=cor, cor_texto=ct, tracejada=fantasma).move_to(ponto(x_filhos[0], y_filhos))
    b = caixa(dir_, tamanho=tf, cor=cor, cor_texto=ct, tracejada=fantasma).move_to(ponto(x_filhos[1], y_filhos))
    cs = APAGADO if fantasma else CINZA
    s_a = seta(r.get_bottom() + LEFT * 0.45, a.get_top(), cor=cs)
    s_b = seta(r.get_bottom() + RIGHT * 0.45, b.get_top(), cor=cs)
    n_a = ao_lado(s_a, "sim", LEFT, tamanho=44, cor=ct)
    n_b = ao_lado(s_b, "não", lado_nao, tamanho=44, cor=ct)
    d = dict(raiz=r, a=a, b=b, s_a=s_a, s_b=s_b, n_a=n_a, n_b=n_b)
    if contas:  # na mesma altura, embaixo do filho mais baixo
        y = min(a.get_bottom()[1], b.get_bottom()[1]) - 0.4
        d["c_a"] = rotulo(contas[0], cor=CINZA, tamanho=44).move_to(ponto(a.get_x(), y))
        d["c_b"] = rotulo(contas[1], cor=CINZA, tamanho=44).move_to(ponto(b.get_x(), y))
    return d


def gulosa(grande=True):
    """A árvore que o scikit-learn monta (gulosa). grande=True: a da linha 15; False: a do alto da linha 16."""
    if grande:
        return arvore("2+ meses?", JULHO, AGOSTO, ponto(0, 4.0), 1.6, (-1.75, 1.6),
                      tamanho=52, tam_filhos=48, contas=(br(SIM["n"], 0), br(NAO["n"], 0)))
    return arvore("2+ meses?", JULHO, AGOSTO, ponto(-0.85, 4.75), 2.85, (-2.05, 0.75), tamanho=40)


def fantasma():
    """A árvore que começa por "1+ mês?" (busca em 11 colunas): cinza e tracejada, na metade de baixo da linha 16."""
    return arvore("1+ mês?", "2+\nmeses?", "julho\n2+?", ponto(-0.85, 1.3), -0.75, (-2.2, 0.6), tamanho=40,
                  fantasma=True, lado_nao=LEFT)


def numero_grande(t):
    """A bagunça final da linha 15: VGroup(número, "bagunça final"), embaixo da árvore."""
    n = rotulo(t, tamanho=90).move_to(ponto(0, -0.6))
    return VGroup(n, rotulo("bagunça final", tamanho=44).next_to(n, DOWN, buff=0.18))


X_NUM_16 = 2.15


def numero_16(t, y, cor=BRANCO, cor_fim=None):
    """Linha 16: a bagunça final ao lado da raiz, com os dois últimos dígitos à parte (são os que mudam)."""
    n = conta(t[:-2], t[-2:], tamanho=56, cor=cor, cores={1: cor_fim or cor}).move_to(ponto(X_NUM_16, y))
    return n.align_to(ponto(X_NUM_16 - 1.2, 0), LEFT)  # alinhados pela esquerda: os dígitos um sobre o outro


def raiz_travada(raiz, escala=1.2):
    """Pinta a caixa da raiz (azul cheia) e devolve o cadeado no canto dela (sem voltar atrás)."""
    raiz[0].set_fill(AZUL, opacity=0.35)
    return cadeado().scale(escala).move_to(raiz.get_corner(UR))
