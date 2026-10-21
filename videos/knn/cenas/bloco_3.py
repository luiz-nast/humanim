"""Bloco 3 (linhas 8 e 9): os cartões e a conta termo a termo, Barbicha a 100,0 e Adélia a 8,7.

Cartões do comum.py a 80% (2,4 × 2,32) no alto, abaixo do rótulo KNN; cinco filas de conta embaixo (FC 48),
de y 1,8 a −1,62 (a última termina em y −1,95, acima do canto). As filas 3 a 5 se alinham pelo "=".
Na linha 9 (CANTO), a Barbicha vira "d = 100,0" na faixa à direita do canto, e "8,7 < 100,0" embaixo dele.
"""
import re

from comum import *
from comum import _confere

ESC = 0.8
C_ESQ = np.array([-1.65, 3.42, 0])
C_DIR = np.array([1.65, 3.42, 0])
Y_FILA = [1.8, 1.0, 0.1, -0.76, -1.62]
X_IG8 = -2.9  # x do "=" das filas 3 a 5 na linha 8 (a 5ª tem 6,35 de largura)
X_IG9 = -1.9

_BARB = PONTOS[VIZ_Z[0]]  # Barbicha, 51,3 mm, 3.650 g
_ADEL = PONTOS[VIZ_CRU[0]]  # Adélia, 42,2 mm, 3.550 g


def _so(s):
    return re.sub(r"\s", "", s)


def cartao_b3(cor, bico, peso, centro, misterioso=False):
    c = cartao(cor, f"{br(bico, 1)} mm", f"{br(peso)} g")
    if misterioso:
        q = Text("?", font_size=60, color=BRANCO, weight=BOLD).move_to(c.bicho.get_center() + [0.95, 0, 0])
        c.add(q)
    c.scale(ESC).move_to(centro)
    return c


def cartoes():
    return cartao_b3(ROXO, M_BICO, M_PESO, C_ESQ, misterioso=True), cartao_b3(ROXO, _BARB[1], _BARB[2], C_DIR)


def cartao_adelia():
    return cartao_b3(LARANJA, _ADEL[1], _ADEL[2], C_DIR)


def fila(partes, y, ig=None, x_ig=0.0, cores=None, maior=None):
    """Uma fila de conta (FC 48). ig: índice da parte "= " que fica em x_ig; sem ig, a fila fica centrada.
    maior {parte: fator}: a parte cresce na mesma linha de base e empurra o resto."""
    c = conta(*partes, tamanho=FC, cores=cores)
    for k, f in (maior or {}).items():
        w0 = c[k].width
        c[k].scale(f, about_edge=DL)
        for j in range(k + 1, len(c)):
            c[j].shift(RIGHT * (c[k].width - w0))
    if ig is None:
        c.move_to([0, y, 0])
    else:
        c.shift([x_ig - c[ig].get_left()[0], y - c[ig].get_center()[1], 0])
    return c


def filas_8():
    return [
        fila(("51,3", " − ", "50,9", " = ", "0,4"), Y_FILA[0]),
        fila(("3.650", " − ", "3.550", " = ", "100"), Y_FILA[1]),
        fila(("d ", "= ", "√(", "0,4²", " + ", "100²", FINO + ")"), Y_FILA[2], ig=1, x_ig=X_IG8),
        fila(("= ", "√(", "0,16", " + ", "10.000", ")"), Y_FILA[3], ig=0, x_ig=X_IG8, cores={4: AMARELO},
             maior={4: 1.45}),
        fila(("= ", "√", "10.000,16", " = ", "100,0"), Y_FILA[4], ig=0, x_ig=X_IG8, cores={4: AMARELO}),
    ]


def filas_9():
    return [
        fila(("50,9", " − ", "42,2", " = ", "8,7"), Y_FILA[0]),
        fila(("3.550", " − ", "3.550", " = ", "0"), Y_FILA[1]),
        fila(("d ", "= ", "√(", "8,7²", " + ", "0²", FINO + ")"), Y_FILA[2], ig=1, x_ig=X_IG9),
        fila(("= ", "√(", "75,69", " + ", "0", ")"), Y_FILA[3], ig=0, x_ig=X_IG9),
        fila(("= ", "√", "75,69", " = ", "8,7"), Y_FILA[4], ig=0, x_ig=X_IG9),
    ]


# As contas na tela são as de dados/resultados.json.
_CB, _CA = T["misterioso"]["conta_ate_a_barbicha"], T["misterioso"]["conta_ate_a_adelia"]
_confere(_so("d=√(0,4²+100²)=√(0,16+10.000)=√10.000,16=100,0") == _so(_CB["sem_padronizar"]), "conta da Barbicha")
_confere(_so("51,3−50,9=0,4") in _so(_CB["deltas"]) and _so("3.650−3.550=100") in _so(_CB["deltas"]), "deltas B")
_confere(_so("d=√(8,7²+0²)=√(75,69+0)=√75,69=8,7") == _so(_CA["sem_padronizar"]), "conta da Adélia")
_confere(_so("50,9−42,2=8,7") in _so(_CA["deltas"]) and _so("3.550−3.550=0") in _so(_CA["deltas"]), "deltas A")
_confere((_BARB[1], _BARB[2], _ADEL[1], _ADEL[2]) == (51.3, 3650, 42.2, 3550), "vizinhos dos cartões")


def mini_barbicha():
    """Na faixa à direita do canto: pinguim roxo pequeno e "d = 100,0" ([1][1] é o "100,0")."""
    t = conta("d = ", "100,0", tamanho=FC)
    g = VGroup(pinguim(ROXO, 0.72), t).arrange(RIGHT, buff=0.22)
    return g.move_to([FAIXA_CENTRO[0], -2.95, 0])


def comparacao():
    return conta("8,7", " < ", "100,0", tamanho=FC, cores={0: AMARELO}).move_to([FAIXA_CENTRO[0], -3.95, 0])


def fim_linha_8():
    """O último quadro da linha 8 e o primeiro da 9."""
    m, b = cartoes()
    return {"knn": rotulo_knn(), "m": m, "b": b, "filas": filas_8()}
