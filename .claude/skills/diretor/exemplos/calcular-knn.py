"""Números do vídeo KNN (k vizinhos mais próximos) com o Palmer Penguins.

Roda da raiz do repositório:  .venv/bin/python videos/knn/dados/calcular.py
Lê dados/penguins.csv e escreve dados/resultados.json. Leve: ~160 MB de memória, ~10 s.

Convenção (pauta do diretor):
- 342 pinguins: os 344 do penguins.csv menos os 2 sem medidas.
- Demonstração em 2 medidas: comprimento do bico (mm) e massa corporal (g). Apoio: as 4 medidas.
- KNN de classificação, k = 5, distância euclidiana d = √(Δbico² + Δmassa²), voto da maioria.
  Empate no voto (2 a 2): entre as espécies empatadas, ganha a do vizinho mais próximo.
  Empate de distância na 5ª vaga: entra quem vem antes no arquivo; o script confere que isso nunca muda a previsão.
- Padronização: z = (x − média) ÷ desvio-padrão populacional (ddof=0, como o StandardScaler).
- Avaliação: deixar-um-de-fora. Esconde um pinguim, os outros 341 votam, repete para os 342.
  Padronizado "por rodada": média e desvio refeitos a cada rodada só com os 341 que votam (sem vazar).
- As medidas vêm com 1 casa (bico) ou inteiras (massa, múltiplos de 25 g); as diferenças são feitas em
  décimos inteiros, para que empates de distância sejam exatos (sem ruído de ponto flutuante).
- Conferência independente com o scikit-learn (KNeighborsClassifier(n_neighbors=5) + LeaveOneOut).
"""

import hashlib
import itertools
import json
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.model_selection import LeaveOneOut, cross_val_predict
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

PASTA = Path(__file__).resolve().parent
CSV = PASTA / "penguins.csv"
K = 5
ESPECIES = ["Adelie", "Chinstrap", "Gentoo"]
NOME = {"Adelie": "Adélia", "Gentoo": "Gentoo", "Chinstrap": "Barbicha"}
DUAS = ["bill_length_mm", "body_mass_g"]
QUATRO = ["bill_length_mm", "bill_depth_mm", "flipper_length_mm", "body_mass_g"]
MENOS = "−"  # U+2212, o mesmo do estilo/estilo.py
# O pinguim misterioso: linha 320 do penguins.csv (o cabeçalho é a linha 1), o 319º dos 344.
# Escolha: entre os que o KNN erra sem padronizar e acerta padronizado, só 2 têm voto 5 a 0 nos dois jeitos
# (o script confere); este tem bico e massa típicos de Barbicha, e o outro (linha 341) tem um dos maiores bicos.
LINHA_MISTERIO = 320


def br(x, casas=0, sinal=False):
    """Igual ao br() de estilo/estilo.py: br(4201.75) "4.202", br(-0.814, 2) "−0,81"."""
    s = f"{x:,.{casas}f}"
    zero = not any(c in "123456789" for c in s)
    if zero and s.startswith("-"):
        s = s[1:]
    if sinal and not zero and not s.startswith("-"):
        s = "+" + s
    return s.translate(str.maketrans(",.-", ".," + MENOS))


def br_enxuto(x, casas):
    """br() sem os zeros à direita da parte decimal: 2,5600 vira 2,56; 0,0000 vira 0."""
    s = br(x, casas)
    if "," in s:
        s = s.rstrip("0").rstrip(",")
    return s


def num(s):
    """O valor de um número escrito como a tela escreve."""
    return float(s.replace(".", "").replace(",", ".").replace(MENOS, "-").replace("+", ""))


def pct(acertos, total):
    return br(100 * acertos / total, 1) + "%"


def carregar():
    bruto = pd.read_csv(CSV)
    bruto["linha_csv"] = bruto.index + 2
    faltam = bruto[bruto[QUATRO].isna().any(axis=1)]
    d = bruto.dropna(subset=QUATRO).reset_index(drop=True)
    return bruto, faltam, d


def decimos(d, cols):
    """Medidas em décimos inteiros (bico 50,9 mm → 509): diferenças exatas."""
    Xi = np.round(d[cols].to_numpy(float) * 10).astype(np.int64)
    assert np.allclose(Xi / 10, d[cols].to_numpy(float))
    return Xi


def distancias(Xi, i, padronizar, base=None):
    """Distância do pinguim i a cada um dos outros. Devolve (outros, dist, sd). base=(mu, sd) fixa a padronização."""
    outros = np.flatnonzero(np.arange(len(Xi)) != i)
    D = (Xi[outros] - Xi[i]) / 10.0  # Δ de cada medida, na unidade da medida
    sd = None
    if padronizar:
        sd = (Xi[outros] / 10.0).std(0) if base is None else base[1]
        D = D / sd  # z_j − z_i = (x_j − x_i) ÷ desvio: a média se cancela
    return outros, np.sqrt((D ** 2).sum(1)), sd


def votar(especies, regra="proximo"):
    """especies: as dos K vizinhos, do mais perto ao mais longe.
    regra 'proximo' (a da pauta): empate → entre as empatadas, a do vizinho mais próximo.
    'primeiro': empate → a espécie do 1º vizinho, mesmo fora do empate. 'alfabetica': como o scikit-learn."""
    cont = Counter(especies)
    mx = max(cont.values())
    topo = [e for e in cont if cont[e] == mx]
    if len(topo) == 1:
        return topo[0]
    if regra == "proximo":
        return next(e for e in especies if e in topo)
    if regra == "primeiro":
        return especies[0]
    return sorted(topo)[0]


def rodada(Xi, y, i, padronizar, base=None):
    """Uma rodada do deixar-um-de-fora para o pinguim i."""
    outros, dist, sd = distancias(Xi, i, padronizar, base)
    ordem = np.argsort(dist, kind="stable")
    ds = dist[ordem]
    viz = outros[ordem[:K]]
    esp = list(y[viz])
    # empate de distância na 5ª vaga: testa toda escolha possível entre os empatados
    na_fronteira = np.isclose(ds, ds[K - 1], rtol=1e-12, atol=0)
    empate_dist = bool(na_fronteira[K])
    possiveis = {votar(esp)}
    if empate_dist:
        certos = list(ordem[:K][~na_fronteira[:K]])
        grupo = list(ordem[na_fronteira])
        for comb in itertools.combinations(grupo, K - len(certos)):
            sel = certos + sorted(comb, key=lambda j: dist[j])
            possiveis.add(votar(list(y[outros[sel]])))
    cont = Counter(esp)
    return {"viz": viz, "dist": ds[:K], "sd": sd, "prev": votar(esp),
            "prev_primeiro": votar(esp, "primeiro"), "prev_alfabetica": votar(esp, "alfabetica"),
            "empate_voto": sum(1 for c in cont.values() if c == max(cont.values())) > 1,
            "empate_dist": empate_dist, "fronteira_muda_previsao": len(possiveis) > 1}


def deixar_um_de_fora(Xi, y, modo):
    """modo: 'cru', 'rodada' (padroniza com os 341 de cada rodada) ou 'tudo' (padroniza os 342 de uma vez)."""
    base = ((Xi / 10.0).mean(0), (Xi / 10.0).std(0)) if modo == "tudo" else None
    return [rodada(Xi, y, i, modo != "cru", base) for i in range(len(Xi))]


def resumo(y, rs):
    p = np.array([r["prev"] for r in rs])
    acertos = int((p == y).sum())
    por_especie = {}
    for e in ESPECIES:
        m = y == e
        a = int((p[m] == e).sum())
        por_especie[NOME[e]] = {"acertos": a, "total": int(m.sum()), "acuracia": round(a / m.sum(), 4),
                                "previsto_como": {NOME[f]: int((p[m] == f).sum()) for f in ESPECIES}}
    outras = {regra: int((np.array([r["prev_" + regra] for r in rs]) == y).sum()) for regra in ["primeiro", "alfabetica"]}
    return {"acertos": acertos, "total": len(y), "acuracia": round(acertos / len(y), 4),
            "acuracia_tela": pct(acertos, len(y)), "conta_tela": f"{acertos} ÷ {len(y)} = {pct(acertos, len(y))}",
            "por_especie": por_especie,
            "empates_no_voto": sum(r["empate_voto"] for r in rs),
            "acertos_com_outro_desempate_do_voto": {"vizinho_1_decide": outras["primeiro"],
                                                    "alfabetica_como_scikit_learn": outras["alfabetica"]},
            "empates_de_distancia_na_5a_vaga": sum(r["empate_dist"] for r in rs),
            "empates_de_distancia_que_mudam_a_previsao": sum(r["fronteira_muda_previsao"] for r in rs)}


def comparar(y, a, b):
    muda = a != b
    return {"mudam_de_previsao": int(muda.sum()),
            "de_errado_para_certo": int((muda & (a != y) & (b == y)).sum()),
            "de_certo_para_errado": int((muda & (a == y) & (b != y)).sum()),
            "de_errado_para_outro_errado": int((muda & (a != y) & (b != y)).sum())}


def sklearn_loo(X, y, padronizar):
    est = KNeighborsClassifier(n_neighbors=K)
    if padronizar:
        est = make_pipeline(StandardScaler(), est)  # o StandardScaler é refeito em cada rodada do LeaveOneOut
    return cross_val_predict(est, X, y, cv=LeaveOneOut())


def conta(db, dm, sd=None):
    """Distância termo a termo, encadeada: cada passo parte do número mostrado no anterior.
    Crua: Δbico (1 casa), Δmassa (inteira), quadrados com 2 casas, raiz com 1 casa.
    Padronizada: Δ ÷ desvio (5,45 e 801 mostrados) com 2 casas, quadrados com 4, raiz com 2."""
    t = {}
    tdb, tdm = br(abs(db), 1), br(abs(dm))
    if sd is None:
        tb, tm, cq, cr = tdb, tdm, 2, 1
    else:
        tsb, tsm = br(sd[0], 2), br(sd[1])
        tb, tm, cq, cr = br(num(tdb) / num(tsb), 2), br(num(tdm) / num(tsm), 2), 4, 2
        tb, tm = ("0" if num(tb) == 0 else tb), ("0" if num(tm) == 0 else tm)
        t["delta_bico_em_desvios"] = f"{tdb} mm ÷ {tsb} = {tb}"
        t["delta_massa_em_desvios"] = f"{tdm} g ÷ {tsm} = {tm}"
    tm_conta = "0" if num(tm) == 0 else tm
    qb, qm = br_enxuto(num(tb) ** 2, cq), br_enxuto(num(tm) ** 2, cq)
    soma = br_enxuto(num(qb) + num(qm), cq)
    raiz = br(np.sqrt(num(soma)), cr)
    t["termos"] = {"delta_bico": tb, "delta_massa": tm, "bico_ao_quadrado": qb, "massa_ao_quadrado": qm, "soma": soma, "raiz": raiz}
    t["linha_unica"] = f"d = √({tb}² + {tm_conta}²) = √({qb} + {qm}) = √{soma} = {raiz}"
    t["massa_na_soma"] = br(100 * num(qm) / num(soma), 2) + "%" if num(soma) else "—"
    return t, raiz


def main():
    bruto, faltam, d = carregar()
    y = d["species"].to_numpy()
    X2, X4 = d[DUAS].to_numpy(float), d[QUATRO].to_numpy(float)
    X2i, X4i = decimos(d, DUAS), decimos(d, QUATRO)
    n = len(d)
    assert n == 342 and len(bruto) == 344

    # 1. Contagem, médias e desvios (ddof=0)
    cont = d["species"].value_counts()
    media, desvio = X2.mean(0), X2.std(0)
    esp = d.groupby("species")[DUAS].agg(["mean", "min", "max"])
    me = {e: (float(esp.loc[e, ("bill_length_mm", "mean")]), float(esp.loc[e, ("body_mass_g", "mean")])) for e in ESPECIES}
    massas_mult_25 = bool((d["body_mass_g"] % 25 == 0).all())

    # 2. Deixar-um-de-fora, à mão e com o scikit-learn
    aval, rs, sk = {}, {}, {}
    for medidas, X, Xi in [("2_medidas", X2, X2i), ("4_medidas", X4, X4i)]:
        aval[medidas] = {}
        for modo in ["cru", "rodada", "tudo"]:
            rs[(medidas, modo)] = deixar_um_de_fora(Xi, y, modo)
            aval[medidas][modo] = resumo(y, rs[(medidas, modo)])
        prev = {modo: np.array([r["prev"] for r in rs[(medidas, modo)]]) for modo in ["cru", "rodada", "tudo"]}
        aval[medidas]["cru_para_padronizado"] = comparar(y, prev["cru"], prev["rodada"])
        aval[medidas]["padronizar_por_rodada_vs_de_uma_vez"] = {
            "previsoes_diferentes": int((prev["rodada"] != prev["tudo"]).sum()),
            "acertos_por_rodada": aval[medidas]["rodada"]["acertos"], "acertos_de_uma_vez": aval[medidas]["tudo"]["acertos"]}
        sk[medidas] = {}
        for nome_modo, modo, padr in [("cru", "cru", False), ("padronizado", "rodada", True)]:
            p_sk = sklearn_loo(X, y, padr)
            r_m = rs[(medidas, modo)]
            alf = np.array([r["prev_alfabetica"] for r in r_m])
            difere = np.flatnonzero(p_sk != prev[modo])
            difere_alf = np.flatnonzero(p_sk != alf)
            sk[medidas][nome_modo] = {
                "acertos_scikit_learn": int((p_sk == y).sum()),
                "acertos_a_mao_com_o_desempate_da_pauta": int((prev[modo] == y).sum()),
                "previsoes_diferentes_da_pauta": int(len(difere)),
                "todas_as_diferencas_sao_empate_no_voto": bool(all(r_m[i]["empate_voto"] for i in difere)),
                "previsoes_diferentes_com_o_mesmo_desempate_alfabetico": int(len(difere_alf)),
            }
            assert len(difere_alf) == 0, f"scikit-learn discorda fora de empate ({medidas}, {nome_modo})"
            assert all(r_m[i]["empate_voto"] for i in difere)
        for modo in ["cru", "rodada", "tudo"]:
            assert aval[medidas][modo]["empates_de_distancia_que_mudam_a_previsao"] == 0

    # 3. Quanto da distância crua vem da massa
    #    (a) entre todos os pares de pinguins: Σ(xi − xj)² = 2·n²·variância, então a fração é var_massa ÷ (var_bico + var_massa)
    var = desvio ** 2
    fr_todos = var[1] / var.sum()
    #    (b) entre cada pinguim e os seus 5 vizinhos crus
    r2c = rs[("2_medidas", "cru")]
    pares = mesma_massa = identicos = lexico = 0
    soma_b = soma_m = 0.0
    fr_par = []
    for i, r in enumerate(r2c):
        D = (X2i[r["viz"]] - X2i[i]) / 10.0
        db2, dm2 = D[:, 0] ** 2, D[:, 1] ** 2
        pares += K
        mesma_massa += int((dm2 == 0).sum())
        identicos += int(((dm2 == 0) & (db2 == 0)).sum())
        soma_b, soma_m = soma_b + db2.sum(), soma_m + dm2.sum()
        ok = (db2 + dm2) > 0
        fr_par += list(dm2[ok] / (db2[ok] + dm2[ok]))
        # os 5 de massa mais parecida, o bico só desempatando (mesma ordem estável do arquivo)
        outros = np.flatnonzero(np.arange(n) != i)
        Do = np.abs(X2i[outros] - X2i[i])
        chave = np.lexsort((Do[:, 0], Do[:, 1]))
        lexico += int(set(outros[chave[:K]]) == set(r["viz"]))
    peso_massa = {
        "todos_os_pares_fracao_da_soma_que_vem_da_massa": round(float(fr_todos), 6),
        "todos_os_pares_nota": "Σ Δmassa² ÷ Σ (Δbico² + Δmassa²) sobre todos os pares = var_massa ÷ (var_bico + var_massa), exato",
        "pares_pinguim_vizinho_cru": pares,
        "vizinhos_crus_com_a_mesma_massa_exata": mesma_massa,
        "vizinhos_crus_identicos_nas_duas_medidas": identicos,
        "vizinhos_crus_fracao_da_soma_total_que_vem_da_massa": round(soma_m / (soma_b + soma_m), 4),
        "vizinhos_crus_fracao_media_por_par_sem_os_identicos": round(float(np.mean(fr_par)), 4),
        "pinguins_cujos_5_vizinhos_crus_sao_os_5_de_massa_mais_parecida": lexico,
        "razao_desvio_massa_por_desvio_bico": round(float(desvio[1] / desvio[0]), 2),
        "nota": "A fração média por par é baixa porque, nos vizinhos de massa igual, Δmassa² = 0 e só o bico sobra: "
                "é a massa que escolhe os vizinhos (os de peso igual), e o bico só desempata entre eles.",
    }
    assert massas_mult_25 and lexico == n

    # 4. O pinguim misterioso
    im = int(np.flatnonzero(d["linha_csv"].to_numpy() == LINHA_MISTERIO)[0])
    r2p = rs[("2_medidas", "rodada")]
    cand = [i for i in range(n) if r2c[i]["prev"] != y[i] and r2p[i]["prev"] == y[i]]
    cinco_a_zero = [int(d.loc[i, "linha_csv"]) for i in cand
                    if Counter(y[r2c[i]["viz"]]).most_common(1)[0][1] == K and set(y[r2p[i]["viz"]]) == {y[i]}]
    assert LINHA_MISTERIO in cinco_a_zero
    rc, rp = r2c[im], r2p[im]
    assert not rc["empate_dist"] and not rp["empate_dist"]
    sd_r = rp["sd"]
    mu_r = (np.delete(X2i, im, axis=0) / 10.0).mean(0)
    assert br(sd_r[0], 2) == br(desvio[0], 2) and br(sd_r[1]) == br(desvio[1])

    def ficha(j, dist, padr):
        return {"linha_csv": int(d.loc[j, "linha_csv"]), "especie": NOME[y[j]], "ilha": d.loc[j, "island"],
                "sexo": d.loc[j, "sex"] if isinstance(d.loc[j, "sex"], str) else None, "ano": int(d.loc[j, "year"]),
                "bico_mm": float(X2[j, 0]), "massa_g": int(X2[j, 1]),
                "delta_bico_mm": round(float(X2[j, 0] - X2[im, 0]), 1), "delta_massa_g": int(X2[j, 1] - X2[im, 1]),
                "distancia": round(float(dist), 4),
                "tela": {"bico": br(X2[j, 0], 1) + " mm", "massa": br(X2[j, 1]) + " g",
                         "distancia": br(dist, 2) if padr else br(dist, 1)}}

    viz_c = [ficha(j, t, False) for j, t in zip(rc["viz"], rc["dist"])]
    viz_p = [ficha(j, t, True) for j, t in zip(rp["viz"], rp["dist"])]
    outros, dc_all, _ = distancias(X2i, im, False)
    _, dp_all, _ = distancias(X2i, im, True)
    fila_c = outros[np.argsort(dc_all, kind="stable")]
    fila_p = outros[np.argsort(dp_all, kind="stable")]
    j_ad, j_ch = rc["viz"][0], rp["viz"][0]  # a Adélia mais perto sem padronizar; a Barbicha mais perto padronizado
    assert y[j_ad] == "Adelie" and y[j_ch] == "Chinstrap"
    pos = {
        "primeira_barbicha_na_fila_crua": int(np.flatnonzero(y[fila_c] == "Chinstrap")[0]) + 1,
        "barbicha_mais_perto_padronizado_na_fila_crua": int(np.flatnonzero(fila_c == j_ch)[0]) + 1,
        "adelia_mais_perto_cru_na_fila_padronizada": int(np.flatnonzero(fila_p == j_ad)[0]) + 1,
        "primeira_adelia_na_fila_padronizada": int(np.flatnonzero(y[fila_p] == "Adelie")[0]) + 1,
        "adelias_com_a_mesma_massa": int(((y == "Adelie") & (X2[:, 1] == X2[im, 1])).sum()),
        "barbichas_com_a_mesma_massa_alem_dele": int(((y == "Chinstrap") & (X2[:, 1] == X2[im, 1])).sum()) - 1,
        "gentoos_com_a_mesma_massa": int(((y == "Gentoo") & (X2[:, 1] == X2[im, 1])).sum()),
    }
    contas = {}
    for chave_v, j in [("ate_a_adelia", j_ad), ("ate_a_barbicha", j_ch)]:
        db, dm = X2[j, 0] - X2[im, 0], X2[j, 1] - X2[im, 1]
        cru, raiz_cru = conta(db, dm)
        pad, raiz_pad = conta(db, dm, sd=sd_r)
        ex_cru = float(np.sqrt(db ** 2 + dm ** 2))
        ex_pad = float(np.sqrt((db / sd_r[0]) ** 2 + (dm / sd_r[1]) ** 2))
        assert raiz_cru == br(ex_cru, 1) and raiz_pad == br(ex_pad, 2), (chave_v, raiz_cru, ex_cru, raiz_pad, ex_pad)
        contas[chave_v] = {"vizinho": ficha(j, ex_cru, False), "cru": cru, "cru_exato": round(ex_cru, 4),
                           "padronizado": pad, "padronizado_exato": round(ex_pad, 4),
                           "confere": "a raiz da conta encadeada é igual à distância exata arredondada, nos dois jeitos"}
    z_im = (X2[im] - mu_r) / sd_r
    voto_c, voto_p = Counter(NOME[e] for e in y[rc["viz"]]), Counter(NOME[e] for e in y[rp["viz"]])
    misterio = {
        "linha_csv": LINHA_MISTERIO, "numero_entre_os_344": LINHA_MISTERIO - 1,
        "especie_real": NOME[y[im]], "ilha": d.loc[im, "island"], "sexo": d.loc[im, "sex"], "ano": int(d.loc[im, "year"]),
        "bico_mm": float(X2[im, 0]), "massa_g": int(X2[im, 1]),
        "z_da_rodada": {"bico": round(float(z_im[0]), 4), "massa": round(float(z_im[1]), 4)},
        "z_com_os_342": {"bico": round(float((X2[im, 0] - media[0]) / desvio[0]), 4), "massa": round(float((X2[im, 1] - media[1]) / desvio[1]), 4)},
        "padronizacao_da_rodada": {"media_bico_mm": round(float(mu_r[0]), 4), "desvio_bico_mm": round(float(sd_r[0]), 4),
                                   "media_massa_g": round(float(mu_r[1]), 2), "desvio_massa_g": round(float(sd_r[1]), 2),
                                   "nota": "dos 341 que votam (sem ele); arredondados, são os mesmos 5,45 mm e 801 g dos 342"},
        "candidatos_5_a_0_nos_dois_jeitos": cinco_a_zero,
        "erra_cru_acerta_padronizado_total": len(cand),
        "cru": {"vizinhos": viz_c, "voto": dict(voto_c), "previsao": NOME[rc["prev"]], "empate_no_voto": rc["empate_voto"]},
        "padronizado": {"vizinhos": viz_p, "voto": dict(voto_p), "previsao": NOME[rp["prev"]], "empate_no_voto": rp["empate_voto"],
                        "nota_ordem": "o 3º e o 4º estão exatamente empatados (Δbico ±0,4 mm, Δmassa ±150 g); a ordem entre eles é a do arquivo e não muda nada"},
        "vizinhos_em_comum": len(set(rc["viz"]) & set(rp["viz"])),
        "filas": pos,
        "contas": contas,
    }

    # 5. Bloco para a tela
    a2, a4 = aval["2_medidas"], aval["4_medidas"]
    ca, cb = contas["ate_a_adelia"], contas["ate_a_barbicha"]
    va, vb = ca["vizinho"], cb["vizinho"]
    tb_mis, tm_mis = br(X2[im, 0], 1), br(X2[im, 1])
    tmedb, tmedm = br(media[0], 1), br(media[1])
    tsb, tsm = br(desvio[0], 2), br(desvio[1])
    zb_t = br((num(tb_mis) - num(tmedb)) / num(tsb), 2, sinal=True)
    zm_t = br((num(tm_mis) - num(tmedm)) / num(tsm), 2, sinal=True)
    z_glob = (X2[im] - media) / desvio  # a tela usa a média e o desvio dos 342 (os da rodada diferem no 3º dígito)
    assert zb_t == br(z_glob[0], 2, sinal=True) and zm_t == br(z_glob[1], 2, sinal=True)
    razao_t = br(num(tsm) / num(tsb))
    db_c = [abs(v["delta_bico_mm"]) for v in viz_c]
    db_p = [abs(v["delta_bico_mm"]) for v in viz_p]
    dm_p = [abs(v["delta_massa_g"]) for v in viz_p]
    assert all(v["delta_massa_g"] == 0 for v in viz_c)
    erros_c, erros_p = n - a2["cru"]["acertos"], n - a2["rodada"]["acertos"]
    mud = a2["cru_para_padronizado"]
    ba_c, ba_p = a2["cru"]["por_especie"]["Barbicha"], a2["rodada"]["por_especie"]["Barbicha"]
    pt_e = {e: {"bico": br(me[e][0], 1) + " mm", "massa": br(me[e][1]) + " g"} for e in ESPECIES}
    para_tela = {
        "formato": "Como o br() de estilo/estilo.py: ponto no milhar, vírgula no decimal, menos U+2212. Bico em mm com 1 casa; "
                   "massa em g inteira; desvio do bico com 2 casas e da massa inteiro; distância crua com 1 casa e sem unidade "
                   "(ela soma mm com g); distância padronizada com 2 casas (em desvios); acurácia em % com 1 casa.",
        "dataset": "Palmer Penguins: 342 pinguins de verdade do arquipélago de Palmer, Antártida, medidos de 2007 a 2009",
        "fonte_curta": "Gorman, Williams & Fraser (2014), PLOS ONE · pacote palmerpenguins (Horst, Hill & Gorman, 2020) · CC0",
        "contagem": {NOME[e]: str(int(cont[e])) for e in ["Adelie", "Gentoo", "Chinstrap"]},
        "contagem_conta": f"{cont['Adelie']} + {cont['Gentoo']} + {cont['Chinstrap']} = {n}",
        "medias": {"bico": tmedb + " mm", "massa": tmedm + " g"},
        "desvios": {"bico": tsb + " mm", "massa": tsm + " g"},
        "medias_por_especie": {NOME[e]: pt_e[e] for e in ESPECIES},
        "intuicao_especies": f"Adélia e Barbicha pesam quase o mesmo ({pt_e['Adelie']['massa']} e {pt_e['Chinstrap']['massa']}, "
                             f"{br(me['Chinstrap'][1] - me['Adelie'][1])} g de diferença); o que separa as duas é o bico: "
                             f"{pt_e['Adelie']['bico']} contra {pt_e['Chinstrap']['bico']}, {br(me['Chinstrap'][0] - me['Adelie'][0])} mm a mais na Barbicha. "
                             f"A Gentoo é a pesada ({pt_e['Gentoo']['massa']}).",
        "distancia": {
            "formula": "d = √(Δbico² + Δmassa²)",
            "intuicao": "A régua de linha reta no gráfico: diferença de bico ao quadrado mais diferença de massa ao quadrado, e a raiz.",
        },
        "padronizar": {
            "formula": "z = (x − média) ÷ desvio",
            "em_palavras": "quantos desvios da média",
            "desvios": f"1 desvio de bico = {tsb} mm; 1 desvio de massa = {tsm} g",
            "intuicao": f"O desvio é a régua de cada medida. Padronizado, {tsb} mm de bico pesam o mesmo que {tsm} g de massa; "
                        f"sem padronizar, 1 mm pesa o mesmo que 1 g.",
            "conta_razao": f"{tsm} ÷ {tsb} = {razao_t}",
            "intuicao_razao": f"Sem padronizar, um desvio de diferença na massa entra na conta {razao_t} vezes maior que um desvio de diferença no bico.",
        },
        "peso_da_massa_sem_padronizar": {
            "todos_os_pares": br(100 * fr_todos, 3) + "%",
            "todos_os_pares_bico": br(100 * (1 - fr_todos), 3) + "%",
            "intuicao_todos_os_pares": f"Somando as diferenças ao quadrado entre todos os pares de pinguins, {br(100 * fr_todos, 3)}% vem da massa "
                                       f"e {br(100 * (1 - fr_todos), 3)}% do bico.",
            "conta_todos_os_pares": f"{tsm}² ÷ ({tsb}² + {tsm}²) = {br(num(tsm) ** 2)} ÷ ({br_enxuto(num(tsb) ** 2, 4)} + {br(num(tsm) ** 2)}) = "
                                    f"{br(100 * num(tsm) ** 2 / (num(tsb) ** 2 + num(tsm) ** 2), 3)}%",
            "vizinhos": f"{lexico} de {n}",
            "intuicao_vizinhos": f"Sem padronizar, para todos os {n} pinguins, os 5 vizinhos são simplesmente os 5 de peso mais parecido; "
                                 f"o bico só desempata entre os de peso igual ({br(100 * mesma_massa / pares)}% dos vizinhos têm exatamente o mesmo peso).",
        },
        "misterioso": {
            "quem": f"um pinguim {NOME[y[im]]} de verdade, macho, da ilha {d.loc[im, 'island']}, medido em {int(d.loc[im, 'year'])} (linha {LINHA_MISTERIO} do arquivo)",
            "bico": tb_mis + " mm", "massa": tm_mis + " g",
            "z": {"bico": zb_t, "massa": zm_t,
                  "conta_bico": f"({tb_mis} − {tmedb}) ÷ {tsb} = {zb_t}",
                  "conta_massa": f"({tm_mis} − {tmedm}) ÷ {tsm} = {zm_t}",
                  "em_palavras": f"bico {br(z_glob[0], 1)} desvio acima da média; massa {br(-z_glob[1], 1)} desvio abaixo",
                  "nota": "com a média e o desvio dos 342; com os 341 da rodada (sem ele) dá " + br(z_im[0], 2, sinal=True) + " e " + br(z_im[1], 2, sinal=True) + ", e os vizinhos são os mesmos"},
            "sem_padronizar": {
                "vizinhos": [f"{v['especie']} · {v['tela']['bico']} · {v['tela']['massa']} · d = {v['tela']['distancia']}" for v in viz_c],
                "voto": f"{voto_c.get('Adélia', 0)} Adélias × {voto_c.get('Barbicha', 0)} Barbicha",
                "previsao": f"{NOME[rc['prev']]} (errou)",
                "intuicao": f"Os 5 vizinhos são Adélias com exatamente {tm_mis} g, o mesmo peso dele, e bico {br(min(db_c), 1)} a {br(max(db_c), 1)} mm mais curto. "
                            f"A massa escolheu sozinha; a primeira Barbicha só aparece em {pos['primeira_barbicha_na_fila_crua']}º lugar na fila.",
            },
            "padronizado": {
                "vizinhos": [f"{v['especie']} · {v['tela']['bico']} · {v['tela']['massa']} · d = {v['tela']['distancia']}" for v in viz_p],
                "voto": f"{voto_p.get('Barbicha', 0)} Barbichas × {voto_p.get('Adélia', 0)} Adélia",
                "previsao": f"{NOME[rp['prev']]} (acertou)",
                "intuicao": f"Medindo as duas em desvios, os 5 vizinhos viram Barbichas: bico até {br(max(db_p), 1)} mm diferente e peso até {br(max(dm_p))} g. "
                            f"Nenhum vizinho em comum com a lista de antes; a primeira Adélia agora só aparece em {pos['primeira_adelia_na_fila_padronizada']}º lugar.",
            },
            "conta_ate_a_adelia": {
                "vizinho": f"Adélia · {va['tela']['bico']} · {va['tela']['massa']}",
                "deltas": f"Δbico = {tb_mis} − {va['tela']['bico'][:-3]} = {ca['cru']['termos']['delta_bico']} mm · Δmassa = {tm_mis} − {va['tela']['massa'][:-2]} = {ca['cru']['termos']['delta_massa']} g",
                "sem_padronizar": ca["cru"]["linha_unica"],
                "padronizado_deltas": [ca["padronizado"]["delta_bico_em_desvios"], ca["padronizado"]["delta_massa_em_desvios"]],
                "padronizado": ca["padronizado"]["linha_unica"],
            },
            "conta_ate_a_barbicha": {
                "vizinho": f"Barbicha · {vb['tela']['bico']} · {vb['tela']['massa']}",
                "deltas": f"Δbico = {vb['tela']['bico'][:-3]} − {tb_mis} = {cb['cru']['termos']['delta_bico']} mm · Δmassa = {vb['tela']['massa'][:-2]} − {tm_mis} = {cb['cru']['termos']['delta_massa']} g",
                "sem_padronizar": cb["cru"]["linha_unica"],
                "padronizado_deltas": [cb["padronizado"]["delta_bico_em_desvios"], cb["padronizado"]["delta_massa_em_desvios"]],
                "padronizado": cb["padronizado"]["linha_unica"],
            },
            "veredito": {
                "sem_padronizar": f"Adélia {ca['cru']['termos']['raiz']} < Barbicha {cb['cru']['termos']['raiz']}: a Adélia parece mais perto",
                "padronizado": f"Barbicha {cb['padronizado']['termos']['raiz']} < Adélia {ca['padronizado']['termos']['raiz']}: agora a Barbicha está mais perto",
                "intuicao": f"Sem padronizar, os {cb['cru']['termos']['delta_massa']} g de diferença viram {cb['cru']['termos']['massa_ao_quadrado']} na soma "
                            f"e os {cb['cru']['termos']['delta_bico']} mm de bico viram {cb['cru']['termos']['bico_ao_quadrado']}: a massa grita. "
                            f"A Adélia tem o mesmo peso, e os {ca['cru']['termos']['delta_bico']} mm de bico viram só {ca['cru']['termos']['bico_ao_quadrado']}, "
                            f"então ela 'ganha'. Padronizado, aqueles {ca['cru']['termos']['delta_bico']} mm são {ca['padronizado']['termos']['delta_bico']} desvio (longe), "
                            f"e {cb['cru']['termos']['delta_bico']} mm e {cb['cru']['termos']['delta_massa']} g são {cb['padronizado']['termos']['delta_bico']} e "
                            f"{cb['padronizado']['termos']['delta_massa']} desvio (perto).",
            },
        },
        "acuracia_2_medidas": {
            "como": "deixar-um-de-fora: esconde um pinguim, os outros 341 votam, repete para os 342; acurácia = acertos ÷ 342",
            "sem_padronizar": a2["cru"]["conta_tela"],
            "padronizado": a2["rodada"]["conta_tela"],
            "erros": {"sem_padronizar": str(erros_c), "padronizado": str(erros_p)},
            "barbichas_certas": {"sem_padronizar": f"{ba_c['acertos']} de {ba_c['total']}", "padronizado": f"{ba_p['acertos']} de {ba_p['total']}"},
            "barbichas_chamadas_de_adelia": {"sem_padronizar": str(ba_c["previsto_como"]["Adélia"]), "padronizado": str(ba_p["previsto_como"]["Adélia"])},
            "mudam": f"{mud['mudam_de_previsao']} pinguins mudam de previsão: {mud['de_errado_para_certo']} passam a acertar, "
                     f"{mud['de_certo_para_errado']} passam a errar",
            "conta_mudam": f"{a2['cru']['acertos']} + {mud['de_errado_para_certo']} − {mud['de_certo_para_errado']} = {a2['rodada']['acertos']}",
            "intuicao": f"Só de medir as duas na mesma régua, os erros caem de {erros_c} para {erros_p}. Quem mais ganha é a Barbicha, que pesa igual à Adélia: "
                        f"sem padronizar, o KNN acerta {ba_c['acertos']} das {ba_c['total']} (chama {ba_c['previsto_como']['Adélia']} de Adélia); padronizado, {ba_p['acertos']}.",
            "ressalva_desempate": f"Sem padronizar há {a2['cru']['empates_no_voto']} empates 2 a 2 no voto; o número cru depende do desempate: "
                                  f"{a2['cru']['acertos']} com o da pauta, {a2['cru']['acertos_com_outro_desempate_do_voto']['vizinho_1_decide']} se o 1º vizinho decide sempre, "
                                  f"{a2['cru']['acertos_com_outro_desempate_do_voto']['alfabetica_como_scikit_learn']} no scikit-learn. Padronizado dá {a2['rodada']['acertos']} em qualquer desempate.",
        },
        "acuracia_4_medidas_apoio": {
            "medidas": "bico (comprimento e altura), nadadeira e massa",
            "sem_padronizar": a4["cru"]["conta_tela"],
            "padronizado": a4["rodada"]["conta_tela"],
            "intuicao": f"Com as 4 medidas o efeito é o mesmo, e maior: padronizado, o KNN erra só {n - a4['rodada']['acertos']} de {n}; "
                        f"sem padronizar, {n - a4['cru']['acertos']}, porque a massa em gramas ainda manda nas outras três, em mm.",
        },
    }

    res = {
        "dataset": {
            "nome": "Palmer Penguins (penguins.csv do pacote R palmerpenguins)",
            "url": "https://raw.githubusercontent.com/allisonhorst/palmerpenguins/main/inst/extdata/penguins.csv",
            "sha256": hashlib.sha256(CSV.read_bytes()).hexdigest(), "bytes": CSV.stat().st_size,
            "licenca": "CC0 1.0 (LICENSE.md do repositório)",
            "linhas_no_arquivo": len(bruto),
            "tiradas_sem_medidas": [{"linha_csv": int(r.linha_csv), "especie": NOME[r.species], "ilha": r.island} for r in faltam.itertuples()],
            "ficam": n,
            "massas_todas_multiplas_de_25_g": massas_mult_25,
            "faixas": {"bico_mm": [float(X2[:, 0].min()), float(X2[:, 0].max())], "massa_g": [int(X2[:, 1].min()), int(X2[:, 1].max())]},
        },
        "convencao": {"k": K, "distancia": "euclidiana, d = √(Δbico² + Δmassa²)",
                      "voto": "maioria; empate 2 a 2: entre as empatadas, a espécie do vizinho mais próximo",
                      "empate_de_distancia": "na 5ª vaga, entra quem vem antes no arquivo (nunca muda a previsão: conferido)",
                      "padronizacao": "z = (x − média) ÷ desvio, ddof=0, refeita a cada rodada com os 341 que votam",
                      "avaliacao": "deixar-um-de-fora (342 rodadas)", "nomes": NOME},
        "contagem": {NOME[e]: int(cont[e]) for e in ["Adelie", "Gentoo", "Chinstrap"]},
        "estatisticas_342": {"media_bico_mm": round(float(media[0]), 4), "desvio_bico_mm": round(float(desvio[0]), 4),
                             "media_massa_g": round(float(media[1]), 2), "desvio_massa_g": round(float(desvio[1]), 2), "ddof": 0,
                             "por_especie": {NOME[e]: {"bico_mm": round(me[e][0], 3), "massa_g": round(me[e][1], 1),
                                                       "bico_min_max_mm": [float(esp.loc[e, ("bill_length_mm", "min")]), float(esp.loc[e, ("bill_length_mm", "max")])],
                                                       "massa_min_max_g": [int(esp.loc[e, ("body_mass_g", "min")]), int(esp.loc[e, ("body_mass_g", "max")])]}
                                             for e in ESPECIES}},
        "avaliacao": aval,
        "scikit_learn": {"versao": sklearn.__version__, **sk,
                         "nota": "O scikit-learn desempata o voto pela espécie de nome menor (Adelie < Chinstrap < Gentoo). "
                                 "Com esse mesmo desempate, a conta à mão dá previsões idênticas às dele nos 342, nos 4 casos."},
        "peso_da_massa": peso_massa,
        "pinguim_misterioso": misterio,
        "para_tela": para_tela,
        "pontos_2_medidas": {"colunas": ["linha_csv", "especie", "bico_mm", "massa_g"],
                             "linhas": [[int(d.loc[i, "linha_csv"]), NOME[y[i]], float(X2[i, 0]), int(X2[i, 1])] for i in range(n)]},
    }
    (PASTA / "resultados.json").write_text(json.dumps(res, ensure_ascii=False, indent=1,
                                                      default=lambda o: o.item() if hasattr(o, "item") else str(o)) + "\n")
    print("OK videos/knn/dados/resultados.json")
    for m in aval:
        print(f"  {m}: cru {aval[m]['cru']['conta_tela']} · padronizado {aval[m]['rodada']['conta_tela']}")
    print(f"  misterioso: linha {LINHA_MISTERIO}, {NOME[y[im]]} {tb_mis} mm {tm_mis} g → cru {NOME[rc['prev']]}, padronizado {NOME[rp['prev']]}")


if __name__ == "__main__":
    main()
