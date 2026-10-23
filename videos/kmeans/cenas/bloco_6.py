"""Bloco 6 (linhas 13 e 14): por que ele para, e por que rodar vários começos. Só o que é deste bloco; o resto vem do
comum.py. Todo número sai de dados/resultados.json (conferido abaixo com _confere).

- Linha 13: a Escada() do comum.py; embaixo dela jeitos() ("2²⁷¹ − 1 jeitos" numa moldura azul) e algarismos()
  ("82 algarismos", cinza). fim_linha_13(): o último quadro da 13 e o 1º da 14 (o último degrau em amarelo, com o
  "rodada 5: parou"). Tudo acima do canto (y > −2,07).
- Linha 14: plano_k2() (o plano final de k = 2, menor, caixa CAIXA_K2) e comecos() ("36.840 começos, 1 final"
  embaixo dele); planos_k3() (dois planos pequenos, sem números, com as erupções pintadas no centro mais perto de cada
  final de k = 3: à esquerda o de soma 5.189, à direita o de 5.839), centros_k3(), soma_k3() e vezes() ("8 de 100",
  "28 de 100"). Cores de k = 3: AZUL as curtas, LARANJA o centro de espera mais alta, ROXO o centro a mais.
"""
from estilo import *
from comum import *
from comum import _confere

# ---------------------------------------------------------------- números (de dados/)

_PARA = T["por_que_para"]["jeitos_de_dividir"]  # "2^271 − 1 (...): um número de 82 algarismos, ..."
EXPOENTE = N - 1  # 271: cada erupção fica num grupo ou no outro (2^272), metade pela troca de nomes, menos o vazio
ALGARISMOS = len(str(2 ** EXPOENTE - 1))  # 82
_confere(_PARA.startswith(f"2^{EXPOENTE} {MENOS} 1") and f"{ALGARISMOS} algarismos" in _PARA, "2^271 − 1, 82 algarismos")

PARES = R["todos_os_pares_k2"]  # 36.840 pares de erupções usados como começo, todos chegam na mesma divisão
_confere(PARES["chegam_na_mesma_divisao"] == PARES["pares"] and br(PARES["pares"]) in T["otimo_local"]["k_2"],
         "36.840 começos, 1 final")

_K3 = R["partidas_aleatorias"]["k_3"]
PARTIDAS = sum(p["partidas"] for p in _K3)  # 100 começos sorteados
MELHOR = min(_K3, key=lambda p: p["soma"])  # soma 5.189: 8 de 100 (um centro nas curtas, dois nas longas)
OUTRO = next(p for p in _K3 if p["soma_tela"] == "5.839")  # soma 5.839: 28 de 100 (dois nas curtas, um nas longas)
_confere(T["otimo_local"]["k_3_melhor"].startswith(f"soma {MELHOR['soma_tela']}: só {MELHOR['partidas']} de {PARTIDAS}")
         and T["otimo_local"]["k_3_pior"] == f"soma {OUTRO['soma_tela']}: {OUTRO['partidas']} de {PARTIDAS}",
         "k = 3: 5.189 (8 de 100) e 5.839 (28 de 100)")

_XY = np.array([DUR, ESP]).T


def grupos_k3(sol):
    """Grupo (0, 1, 2) de cada erupção: o centro mais perto em minutos (empate: o de número menor, como nos dados).
    Confere com os tamanhos e a soma do resultados.json."""
    c = np.array([(x["duracao_min"], x["espera_min"]) for x in sol["centros"]])
    d2 = ((_XY[:, None, :] - c[None, :, :]) ** 2).sum(axis=2)
    g = d2.argmin(axis=1)
    _confere([int((g == j).sum()) for j in range(3)] == sol["tamanhos"] and br(d2.min(axis=1).sum()) == sol["soma_tela"],
             f"k = 3, soma {sol['soma_tela']}: tamanhos e soma")
    return [int(x) for x in g]


COR3 = (AZUL, ROXO, LARANJA)  # pela ordem dos centros nos dados (espera crescente nos dois finais)
_confere(all([x["espera_min"] for x in s["centros"]] == sorted(x["espera_min"] for x in s["centros"])
             for s in (MELHOR, OUTRO)), "centros de k = 3 em espera crescente")

# ---------------------------------------------------------------- linha 13: embaixo da escada

TAM_J = 60
Y_JEITOS = 0.0  # centro do "2²⁷¹ − 1 jeitos" (a Escada deixa livre de y 0,9 a −2,0)
_SOBRE = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")


def jeitos():
    """VGroup(moldura azul, "2²⁷¹ − 1 jeitos"): um Text só (mesma linha de base), com o expoente 30% maior
    (o sobrescrito da Lato é miúdo no celular) e o resto empurrado para a direita."""
    s = f"2{str(EXPOENTE).translate(_SOBRE)} {MENOS} 1 jeitos"
    t = Text(s, font_size=TAM_J, color=BRANCO, disable_ligatures=True)
    _confere(len(t.submobjects) == len(s), "glifos do 2²⁷¹")
    n = len(str(EXPOENTE))
    exp = VGroup(*t.submobjects[1:1 + n])
    antes = exp.get_right()[0]
    exp.scale(1.3, about_point=exp.get_corner(DL))
    VGroup(*t.submobjects[1 + n:]).shift(RIGHT * (exp.get_right()[0] - antes + 0.04))
    t.move_to([0, Y_JEITOS, 0])
    caixa = RoundedRectangle(width=t.width + 0.6, height=t.height + 0.5, corner_radius=0.18, stroke_color=AZUL,
                             stroke_width=5).move_to(t)
    return VGroup(caixa, t)


def algarismos(caixa):
    """"82 algarismos", pequeno e cinza, embaixo da moldura."""
    t = Text(f"{ALGARISMOS} algarismos", font_size=PQ, color=CINZA)
    return t.move_to([0, caixa.get_bottom()[1] - 0.25 - t.height / 2, 0])


def fim_linha_13():
    """O último quadro da linha 13 (e o 1º da 14): a escada inteira com o último degrau (o 8.902 de novo) amarelo e
    o "rodada 5: parou", a moldura dos jeitos e os 82 algarismos. dict: escada, jeitos, algarismos (tudo_linha_13)."""
    esc = Escada()
    esc.degraus[8].set_color(AMARELO)
    j = jeitos()
    return {"escada": esc, "jeitos": j, "algarismos": algarismos(j[0])}


def tudo_linha_13(a):
    esc = a["escada"]
    return VGroup(esc.tudo, esc.parou, a["jeitos"], a["algarismos"])


# ---------------------------------------------------------------- linha 14: k = 2 e os dois finais de k = 3

CAIXA_K2 = (-2.3, 0.0, 3.1, 3.75)  # o plano final de k = 2, menor (números do eixo deitado em y −0,45)
Y_COMECOS = -1.1  # "36.840 começos, 1 final"
CAIXAS_K3 = ((-3.3, -0.35, -0.4, 3.75), (0.45, -0.35, 3.35, 3.75))  # os dois planos pequenos de k = 3
Y_SOMA = Y2  # "soma 5.189" acima de cada plano pequeno
Y_VEZES = -1.1  # "8 de 100" e "28 de 100" embaixo de cada um
_MARCAS = dict(marcas_x=(2, 3, 4, 5), marcas_y=(50, 60, 70, 80, 90))


def plano_k2():
    """O plano final de k = 2 (cores da rodada 5), menor que o principal, com os mesmos números e nomes."""
    return Plano(1.5, 5.5, 40, 100, CAIXA_K2, numeros_x={2: "2", 4: "4"},
                 numeros_y={40: "40", 70: "70", 100: "100"}, grupos=GRUPOS[5], **_MARCAS)


def comecos():
    """"36.840 começos, 1 final" embaixo do plano de k = 2: [0] "36.840 começos", [1] ", ", [2] "1 final"."""
    return conta(f"{br(PARES['pares'])} começos", ", ", "1 final", tamanho=FC).move_to([0, Y_COMECOS, 0])


def planos_k3():
    """Os dois planos pequenos (mesmos trechos e marcas do plano de k = 2, sem números nem nomes): à esquerda o final
    de soma 5.189, à direita o de 5.839, cada erupção na cor do centro mais perto (COR3)."""
    pls = []
    for caixa, sol in zip(CAIXAS_K3, (MELHOR, OUTRO)):
        pl = Plano(1.5, 5.5, 40, 100, caixa, numeros_x={}, numeros_y={}, raio=0.042, **_MARCAS)
        pl.eixos.remove(pl.nome_x, pl.nome_y)
        for i, g in enumerate(grupos_k3(sol)):
            pl.pontos[i].set_color(COR3[g])
        pls.append(pl)
    return pls


def centros_k3(pl, sol):
    """VGroup dos 3 losangos (COR3) nos centros do final sol."""
    return VGroup(*(losango(COR3[j], lado=0.27).move_to(pl.p(c["duracao_min"], c["espera_min"]))
                    for j, c in enumerate(sol["centros"])))


def soma_k3(pl, sol):
    """"soma 5.189" acima do plano pequeno: [0] "soma " (cinza), [1] o número."""
    return conta("soma ", sol["soma_tela"], tamanho=FC, cores={0: CINZA}).move_to(
        [(pl.esq + pl.dir) / 2, Y_SOMA, 0])


def vezes(pl, sol, cor):
    """"8 de 100" (ou "28 de 100") embaixo do plano pequeno."""
    return Text(f"{sol['partidas']} de {PARTIDAS}", font_size=G, color=cor).move_to([(pl.esq + pl.dir) / 2, Y_VEZES, 0])
