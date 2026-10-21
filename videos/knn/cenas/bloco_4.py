"""Bloco 4 (linhas 11 e 12): as duas réguas.

trechos_amarelos(bico, peso) -> (trecho "8,7 mm" na régua do bico, trecho "100 g" na do peso), amarelos.
  8,7 mm = do bico da Adélia vizinha (42,2) ao do misterioso (50,9); 100 g = do peso dele (3.550) ao da Barbicha colada (3.650).
medias_especie(bico, peso) -> (marcas do bico "38,8"/"48,8", marcas do peso "3.701"/"3.733"), na 2ª fila de rótulos.
fim_linha_11() -> dict: o último quadro da 11 e o 1º da 12.
"""
from comum import *

ADELIA_VIZ = VIZ_CRU[0]  # Adélia 42,2 mm, 3.550 g
BARB_VIZ = VIZ_Z[0]  # Barbicha 51,3 mm, 3.650 g
D_BICO = round(M_BICO - PONTOS[ADELIA_VIZ][1], 1)  # 8,7
D_PESO = round(PONTOS[BARB_VIZ][2] - M_PESO)  # 100
assert (D_BICO, D_PESO) == (8.7, 100), (D_BICO, D_PESO)


def trechos_amarelos(bico, peso):
    tb = trecho(bico, PONTOS[ADELIA_VIZ][1], M_BICO, AMARELO, f"{br(D_BICO, 1)} mm")
    tp = trecho(peso, M_PESO, M_PESO + D_PESO, AMARELO, f"{br(D_PESO)} g")
    # o "100 g" centrado no trecho encosta no "2.700" da ponta: começa onde o trecho começa
    tp[1].align_to(tp[0], LEFT)
    for t in (tb, tp):
        t[0].set_z_index(1)
    return tb, tp


def _valor(s):
    return float(s.split()[0].replace(".", "").replace(",", "."))


def medias_especie(bico, peso):
    m = T["medias_por_especie"]
    mb = VGroup(*(marca(bico, _valor(m[e]["bico"]), m[e]["bico"].split()[0], COR[e], fila=2)
                  for e in ("Adélia", "Barbicha")))
    mp = VGroup(*(marca(peso, _valor(m[e]["massa"]), m[e]["massa"].split()[0], COR[e], fila=2)
                  for e in ("Adélia", "Barbicha")))
    # quase no mesmo lugar: os dois números lado a lado, um de cada lado das marcas
    xa, xb = mp[0][0].get_x(), mp[1][0].get_x()
    mp[0][1].align_to([xa - 0.06, 0, 0], RIGHT)
    mp[1][1].align_to([xb + 0.06, 0, 0], LEFT)
    for g in (*mb, *mp):
        g[0].set_z_index(3)
    return mb, mp


def fim_linha_11():
    bico, peso = reguas()
    tb, tp = trechos_amarelos(bico, peso)
    mb, mp = medias_especie(bico, peso)
    return {"bico": bico, "peso": peso, "tb": tb, "tp": tp, "mb": mb, "mp": mp, "knn": rotulo_knn()}
