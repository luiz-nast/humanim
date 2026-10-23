"""Números do vídeo k-means com o gêiser Old Faithful (datasets::faithful do R).

O CSV não vai para o GitHub (sem licença aberta explícita para os dados: ver fontes-dados.md). Baixe antes, da raiz:
    curl -sSL -o videos/kmeans/pesquisa/faithful.csv \\
        https://vincentarelbundock.github.io/Rdatasets/csv/datasets/faithful.csv
    (3.260 bytes; SHA-256 5043db1e2c51c8e8fd67e0868c768ae589770cc76ad0ac0c5b7afd1fca31fc57)
Roda da raiz do repositório:  .venv/bin/python videos/kmeans/dados/calcular.py
Lê pesquisa/faithful.csv e escreve dados/resultados.json. Leve: ~150 MB de memória, ~15 s.

Convenção (pauta do diretor):
- 272 erupções; duas medidas em minutos: duração da erupção (coluna eruptions) e espera (coluna waiting).
- k-means de Lloyd, distância euclidiana nas medidas cruas (sem padronizar). Uma rodada = as duas regras:
  (1) cada erupção vai para o centro mais perto; (2) cada centro vai para a média do seu grupo.
  Para quando a regra (1) não troca ninguém de grupo. Empate de distância: o centro de número menor
  (o script confere que não há empate nenhum na demonstração).
- Soma dos quadrados (a inertia do scikit-learn): Σ, em todas as erupções, da distância ao quadrado até o centro
  do seu grupo, em min². "Soma da rodada r" = depois da regra (2) da rodada r (centros nas médias).
- Demonstração: k = 2, começando de duas erupções reais escolhidas para a primeira divisão sair errada
  (rownames 74 e 203; linhas 75 e 204 do CSV, que tem cabeçalho na linha 1).
- Conferências com o scikit-learn (KMeans, n_init=10, random_state=0).
"""

import hashlib
import json
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

PASTA = Path(__file__).resolve().parent
CSV = PASTA.parent / "pesquisa" / "faithful.csv"
URL = "https://vincentarelbundock.github.io/Rdatasets/csv/datasets/faithful.csv"
SHA256 = "5043db1e2c51c8e8fd67e0868c768ae589770cc76ad0ac0c5b7afd1fca31fc57"
INICIAIS = (74, 203)  # rownames do R (= linha do CSV − 1): duas erupções longas, 71 e 91 min de espera
SEMENTE = 0  # random_state do scikit-learn e semente das 100 partidas aleatórias
PARTIDAS = 100
MENOS = "−"  # U+2212, o mesmo do estilo/estilo.py


def br(x, casas=0, sinal=False):
    """Igual ao br() de estilo/estilo.py: br(8901.77) "8.902", br(-0.814, 2) "−0,81"."""
    s = f"{x:,.{casas}f}"
    zero = not any(c in "123456789" for c in s)
    if zero and s.startswith("-"):
        s = s[1:]
    if sinal and not zero and not s.startswith("-"):
        s = "+" + s
    return s.translate(str.maketrans(",.-", ".," + MENOS))


def num(s):
    """O valor de um número escrito como a tela escreve."""
    return float(s.replace(".", "").replace(",", ".").replace(MENOS, "-").replace("+", "").replace("%", ""))


def pct(a, b, casas=1):
    return br(100 * a / b, casas) + "%"


def carregar():
    if not CSV.exists():
        raise SystemExit(f"ERRO falta {CSV}. Baixe com:\n  curl -sSL -o videos/kmeans/pesquisa/faithful.csv {URL}")
    sha = hashlib.sha256(CSV.read_bytes()).hexdigest()
    if sha != SHA256:
        raise SystemExit(f"ERRO {CSV} mudou (SHA-256 {sha}, esperado {SHA256}): os números do vídeo dependem deste arquivo.")
    d = pd.read_csv(CSV)
    assert list(d.columns) == ["rownames", "eruptions", "waiting"] and len(d) == 272
    assert (d["rownames"].to_numpy() == np.arange(1, 273)).all()
    return d


def soma_q(X, lab, C):
    """Soma dos quadrados: Σ distância² de cada erupção até o centro do seu grupo (min²)."""
    return float(((X - C[lab]) ** 2).sum())


def atribuir(X, C):
    """Regra (1): cada erupção vai para o centro mais perto. Devolve (grupo, há empate?)."""
    D = ((X[:, None, :] - C[None]) ** 2).sum(2)
    lab = D.argmin(1)
    srt = np.sort(D, 1)
    return lab, bool((np.abs(srt[:, 0] - srt[:, 1]) < 1e-9).any()) if C.shape[0] > 1 else False


def medias(X, lab, k):
    """Regra (2): cada centro vai para a média do seu grupo."""
    assert len(set(lab.tolist())) == k, "grupo vazio"
    return np.array([X[lab == g].mean(0) for g in range(k)])


def lloyd(X, C0, max_rodadas=300):
    """Lloyd à mão, rodada a rodada. Cada rodada guarda a soma depois de cada meia-rodada."""
    C, prev, rodadas = np.array(C0, float), None, []
    for r in range(1, max_rodadas + 1):
        lab, empate = atribuir(X, C)
        trocas = None if prev is None else int((lab != prev).sum())
        s_regra1 = soma_q(X, lab, C)  # centros ainda no lugar antigo, erupções já no centro mais perto
        if trocas == 0:
            rodadas.append({"rodada": r, "trocaram": 0, "empate": empate, "soma_regra1": s_regra1, "parou": True,
                            "centros": C.copy(), "tamanhos": np.bincount(lab, minlength=len(C)), "soma": s_regra1, "lab": lab})
            return rodadas
        C = medias(X, lab, len(C))
        rodadas.append({"rodada": r, "trocaram": trocas, "empate": empate, "soma_regra1": s_regra1, "parou": False,
                        "centros": C.copy(), "tamanhos": np.bincount(lab, minlength=len(C)), "soma": soma_q(X, lab, C), "lab": lab})
        prev = lab
    raise RuntimeError("não parou")


def mesma_divisao(a, b):
    """As duas divisões põem as mesmas erupções juntas (o número do grupo não importa)?"""
    return len(set(zip(a.tolist(), b.tolist()))) == len(set(a.tolist())) == len(set(b.tolist()))


def chave(lab):
    """Divisão em forma canônica: os grupos renumerados pela ordem em que aparecem no arquivo."""
    mapa = {}
    return tuple(mapa.setdefault(g, len(mapa)) for g in lab.tolist())


def ficha_centro(c):
    return {"duracao_min": round(float(c[0]), 4), "espera_min": round(float(c[1]), 4),
            "tela": f"{br(c[0], 1)} min · {br(c[1], 1)} min"}


def demonstracao(d, X):
    """Itens b, c, d, f: a demonstração com k = 2 a partir de duas erupções reais."""
    idx = [r - 1 for r in INICIAIS]
    C0 = X[idx]
    rod = lloyd(X, C0)
    assert not any(r["empate"] for r in rod), "empate de distância na demonstração"
    fim = rod[-1]
    lab = fim["lab"]
    curto, longo = np.argsort(fim["centros"][:, 0])  # grupo de duração menor e maior
    assert (curto, longo) == (0, 1), "o centro que começou embaixo (espera 71) deveria virar o grupo curto"
    # a primeira divisão contra a final
    lab1 = rod[0]["lab"]
    lado_errado = int((lab1 != lab).sum())
    # meias-rodadas: a soma nunca sobe
    seq = [rod[0]["soma_regra1"]]
    for r in rod:
        if not r["parou"]:
            seq += [r["soma"]] if r is rod[0] else [r["soma_regra1"], r["soma"]]
    assert all(b <= a + 1e-9 for a, b in zip(seq, seq[1:])), "a soma subiu"
    # conferência: scikit-learn
    km = KMeans(2, n_init=10, random_state=SEMENTE).fit(X)
    km_do_comeco = KMeans(2, init=C0, n_init=1).fit(X)
    # padronizado: z = (x − média) ÷ desvio (ddof=0, StandardScaler)
    Z = StandardScaler().fit_transform(X)
    kz = KMeans(2, n_init=10, random_state=SEMENTE).fit(Z)
    lz = kz.labels_ if (kz.labels_ != lab).sum() <= len(X) // 2 else 1 - kz.labels_  # mesmo número de grupo do cru
    muda_z = np.flatnonzero(lz != lab)
    Cz = medias(X, lz, 2)
    rodadas = []
    for r in rod:
        rodadas.append({
            "rodada": r["rodada"], "trocaram_de_grupo": r["trocaram"], "parou": r["parou"],
            "soma_depois_da_regra_1": round(r["soma_regra1"], 4),
            "centros_depois_da_regra_2": {"grupo_0": ficha_centro(r["centros"][0]), "grupo_1": ficha_centro(r["centros"][1])},
            "tamanhos": {"grupo_0": int(r["tamanhos"][0]), "grupo_1": int(r["tamanhos"][1])},
            "soma_depois_da_regra_2": round(r["soma"], 4),
        })
    linhas = [[int(d.loc[i, "rownames"]), float(X[i, 0]), int(X[i, 1])] + [int(r["lab"][i]) for r in rod] for i in range(len(X))]
    return {
        "iniciais": [{"rownames": INICIAIS[g], "linha_csv": INICIAIS[g] + 1, "duracao_min": float(C0[g, 0]),
                      "espera_min": int(C0[g, 1]), "vira": ["grupo curto", "grupo longo"][g]} for g in range(2)],
        "por_que_esses": "Duas erupções longas, uma com 71 e outra com 91 min de espera: os dois centros começam dentro da "
                         "nuvem das longas, então a 1ª divisão corta a nuvem das longas ao meio e joga as curtas com a metade de baixo.",
        "primeira_divisao": {"tamanhos": [int(x) for x in rod[0]["tamanhos"]], "erupcoes_no_grupo_errado": lado_errado,
                             "nota": "errado = em grupo diferente do final"},
        "rodadas": rodadas,
        "n_rodadas": len(rod), "rodadas_com_troca": len(rod) - 1,
        "soma_no_comeco": round(rod[0]["soma_regra1"], 4),
        "somas_meias_rodadas": [round(s, 4) for s in seq],
        "final": {"centros": {"curto": ficha_centro(fim["centros"][0]), "longo": ficha_centro(fim["centros"][1])},
                  "tamanhos": {"curto": int(fim["tamanhos"][0]), "longo": int(fim["tamanhos"][1])},
                  "soma": round(fim["soma"], 4),
                  "faixas_duracao": {"curto": [float(X[lab == 0, 0].min()), float(X[lab == 0, 0].max())],
                                     "longo": [float(X[lab == 1, 0].min()), float(X[lab == 1, 0].max())]},
                  "faixas_espera": {"curto": [int(X[lab == 0, 1].min()), int(X[lab == 0, 1].max())],
                                    "longo": [int(X[lab == 1, 1].min()), int(X[lab == 1, 1].max())]}},
        "scikit_learn": {"versao": sklearn.__version__, "chamada": f"KMeans(2, n_init=10, random_state={SEMENTE})",
                         "inertia": round(float(km.inertia_), 4), "mesma_divisao": mesma_divisao(km.labels_, lab),
                         "do_mesmo_comeco": {"chamada": "KMeans(2, init=<as 2 erupções>, n_init=1)",
                                             "n_iter": int(km_do_comeco.n_iter_), "inertia": round(float(km_do_comeco.inertia_), 4),
                                             "mesma_divisao": mesma_divisao(km_do_comeco.labels_, lab)}},
        "padronizado": {"como": "z = (x − média) ÷ desvio (ddof=0); KMeans(2, n_init=10, random_state=0) nas medidas padronizadas",
                        "mudam_de_grupo": int(len(muda_z)),
                        "quais": [{"rownames": int(d.loc[i, "rownames"]), "duracao_min": float(X[i, 0]), "espera_min": int(X[i, 1]),
                                   "cru": ["curto", "longo"][lab[i]], "padronizado": ["curto", "longo"][lz[i]]} for i in muda_z],
                        "tamanhos": {"curto": int((lz == 0).sum()), "longo": int((lz == 1).sum())},
                        "centros_em_minutos": {"curto": ficha_centro(Cz[0]), "longo": ficha_centro(Cz[1])},
                        "soma_em_min2_da_divisao_padronizada": round(soma_q(X, lz, Cz), 4)},
        "_lab": lab, "_rod": rod,
        "pontos": {"colunas": ["rownames", "duracao_min", "espera_min"] + [f"grupo_rodada_{r['rodada']}" for r in rod],
                   "linhas": linhas},
    }


def todos_os_pares(X, lab_final):
    """Extra do item h: k = 2 começando de cada par de erupções diferentes (todos os pares)."""
    n = len(X)
    total = mesma = 0
    rodadas = Counter()
    for i in range(n):
        for j in range(i + 1, n):
            if (X[i] == X[j]).all():
                continue
            rod = lloyd(X, X[[i, j]])
            total += 1
            mesma += mesma_divisao(rod[-1]["lab"], lab_final)
            rodadas[len(rod)] += 1
    return {"pares": total, "chegam_na_mesma_divisao": mesma,
            "rodadas_ate_parar": {str(k): v for k, v in sorted(rodadas.items())},
            "nota": "pares de erupções com medidas diferentes (há 16 erupções repetidas); rodadas contam a última, em que ninguém troca"}


def partidas_aleatorias(X, k, rng):
    """Item h: PARTIDAS começos com k erupções sorteadas (medidas diferentes) como centros."""
    sol = {}
    for p in range(PARTIDAS):
        while True:
            idx = rng.choice(len(X), k, replace=False)
            if len(np.unique(X[idx], axis=0)) == k:
                break
        rod = lloyd(X, X[idx])
        lab = rod[-1]["lab"]
        ch = chave(lab)
        s = sol.setdefault(ch, {"partidas": 0, "soma": rod[-1]["soma"], "centros": rod[-1]["centros"],
                                "tamanhos": rod[-1]["tamanhos"], "rodadas": [], "empates": 0, "primeira": [int(i) + 1 for i in idx]})
        s["partidas"] += 1
        s["rodadas"].append(len(rod))
        s["empates"] += any(r["empate"] for r in rod)
    out = []
    for s in sorted(sol.values(), key=lambda s: s["soma"]):
        o = np.argsort(s["centros"][:, 0])
        out.append({"partidas": s["partidas"], "soma": round(s["soma"], 4), "soma_tela": br(s["soma"]),
                    "centros": [ficha_centro(s["centros"][g]) for g in o], "tamanhos": [int(s["tamanhos"][g]) for g in o],
                    "rodadas_min_max": [min(s["rodadas"]), max(s["rodadas"])], "partidas_com_empate": s["empates"],
                    "exemplo_de_comeco_rownames": s["primeira"]})
    return out


def por_que_a_media(X, lab):
    """Item e: num grupo final, a soma com o centro na média contra o centro deslocado. Sobe n·d² (conferido na força bruta)."""
    out = {}
    for g, nome in enumerate(["curto", "longo"]):
        P = X[lab == g]
        m = len(P)
        c = P.mean(0)
        s0 = float(((P - c) ** 2).sum())
        desl = {}
        for chave_d, dv in [("espera_mais_1", (0, 1)), ("duracao_mais_1", (1, 0)), ("os_dois_mais_1", (1, 1)),
                            ("espera_mais_2", (0, 2)), ("espera_menos_1", (0, -1))]:
            s = float(((P - (c + np.array(dv, float))) ** 2).sum())
            d2 = dv[0] ** 2 + dv[1] ** 2
            assert abs(s - (s0 + m * d2)) < 1e-6, "a identidade n·d² falhou"
            desl[chave_d] = {"deslocamento_min": list(dv), "d2": d2, "soma": round(s, 4), "subiu": round(s - s0, 4),
                             "n_vezes_d2": m * d2}
        # a média minimiza: procura numa grade de centros perto da média e confere que nenhum dá soma menor
        grade = [(c[0] + a, c[1] + b) for a in np.linspace(-0.5, 0.5, 21) for b in np.linspace(-5, 5, 41)]
        menor = min(float(((P - np.array(p)) ** 2).sum()) for p in grade)
        assert menor >= s0 - 1e-9
        out[nome] = {"n": m, "soma_duracoes": round(float(P[:, 0].sum()), 3), "soma_esperas": int(P[:, 1].sum()),
                     "media": ficha_centro(c), "soma_com_centro_na_media": round(s0, 4),
                     "parte_da_duracao": round(float(((P[:, 0] - c[0]) ** 2).sum()), 4),
                     "parte_da_espera": round(float(((P[:, 1] - c[1]) ** 2).sum()), 4),
                     "deslocado": desl,
                     "conferencia_grade": "nenhum de 861 centros numa grade em volta da média (±0,5 min de duração, ±5 min de espera) dá soma menor"}
    return out


def previsao(X, lab, C):
    """Item i: o grupo só pela duração (centro de duração mais perto) e a espera média do grupo como previsão."""
    dur, esp = X[:, 0], X[:, 1]
    n = len(X)

    def regra(cd, x):  # grupo do centro de duração mais perto (0 = curto, 1 = longo)
        return (np.abs(x[:, None] - cd[None]) ).argmin(1)

    g = regra(C[:, 0], dur)
    me = np.array([esp[g == k].mean() for k in range(2)])
    mg = esp.mean()
    eam_grupo = float(np.abs(esp - me[g]).mean())
    eam_geral = float(np.abs(esp - mg).mean())
    eam_centro = float(np.abs(esp - C[g, 1]).mean())
    # deixar-um-de-fora: tira a erupção i, refaz o k-means com as 271 (Lloyd a partir dos centros finais),
    # o grupo dela pela duração, e a espera média do grupo e a geral só com as 271
    p_g, p_m, p_c, mudou = np.empty(n), np.empty(n), np.empty(n), 0
    for i in range(n):
        Xr = np.delete(X, i, axis=0)
        rod = lloyd(Xr, C)
        Cr = rod[-1]["centros"]
        mudou += not mesma_divisao(rod[-1]["lab"], np.delete(lab, i))
        gr = regra(Cr[:, 0], Xr[:, 0])
        gi = regra(Cr[:, 0], X[i:i + 1, 0])[0]
        p_g[i] = Xr[gr == gi, 1].mean()
        p_c[i] = Cr[gi, 1]  # a espera do centro (a média do grupo do k-means das 271)
        p_m[i] = Xr[:, 1].mean()
    loo_grupo, loo_geral = float(np.abs(esp - p_g).mean()), float(np.abs(esp - p_m).mean())
    loo_centro = float(np.abs(esp - p_c).mean())
    limiar = float(C[:, 0].mean())
    # sem a espera no agrupamento: k-means (k = 2) só na duração, e a espera média de cada grupo
    D1 = dur[:, None]
    l1 = lloyd(D1, C[:, :1])[-1]["lab"]
    m1 = np.array([esp[l1 == k].mean() for k in range(2)])
    p1 = np.empty(n)
    for i in range(n):
        Dr = np.delete(D1, i, axis=0)
        r1 = lloyd(Dr, C[:, :1])[-1]
        gi = int(np.abs(r1["centros"][:, 0] - dur[i]).argmin())
        p1[i] = np.delete(esp, i)[r1["lab"] == gi].mean()
    so_duracao = {"como": "k-means com k = 2 só na duração (a espera fica de fora do agrupamento); previsão = espera média do grupo",
                  "centros_duracao_min": [round(float(x), 4) for x in medias(D1, l1, 2)[:, 0]],
                  "limiar_duracao_min": round(float(medias(D1, l1, 2)[:, 0].mean()), 4),
                  "tamanhos": [int((l1 == 0).sum()), int((l1 == 1).sum())],
                  "igual_a_regra_pelos_centros_2d": bool((l1 == g).all()),
                  "espera_media": [round(float(x), 4) for x in m1],
                  "erro_medio_absoluto_min": round(float(np.abs(esp - m1[l1]).mean()), 4),
                  "deixar_um_de_fora_min": round(float(np.abs(esp - p1).mean()), 4)}
    tres = dur < 3
    return {
        "regra": "grupo = o do centro de duração mais perto; previsão da espera = espera média do grupo",
        "limiar_duracao_min": round(limiar, 4),
        "tamanhos": {"curto": int((g == 0).sum()), "longo": int((g == 1).sum())},
        "discorda_do_kmeans": int((g != lab).sum()),
        "espera_media": {"curto": round(float(me[0]), 4), "longo": round(float(me[1]), 4), "geral": round(float(mg), 4)},
        "erro_medio_absoluto_min": {"pela_media_do_grupo": round(eam_grupo, 4), "pela_media_geral": round(eam_geral, 4),
                                    "pela_espera_do_centro_kmeans": round(eam_centro, 4)},
        "deixar_um_de_fora": {"pela_media_do_grupo": round(loo_grupo, 4), "pela_media_geral": round(loo_geral, 4),
                              "pela_espera_do_centro_kmeans": round(loo_centro, 4),
                              "rodadas_em_que_a_divisao_das_271_mudou": int(mudou),
                              "diferenca_grupo_loo_menos_dentro": round(loo_grupo - eam_grupo, 4),
                              "diferenca_geral_loo_menos_dentro": round(loo_geral - eam_geral, 4)},
        "regra_dos_3_minutos_extra": {"nota": "corte em 3 min (o da regra dos guardas do parque hoje), nos dados do faithful",
                                      "n_menos_de_3": int(tres.sum()), "n_3_ou_mais": int((~tres).sum()),
                                      "espera_media_menos_de_3": round(float(esp[tres].mean()), 4),
                                      "espera_media_3_ou_mais": round(float(esp[~tres].mean()), 4),
                                      "igual_a_regra_do_kmeans": bool(((dur < limiar) == tres).all()),
                                      "erupcoes_entre_3_e_o_limiar": int(((dur >= 3) & (dur < limiar)).sum())},
        "so_duracao_sem_a_espera_no_agrupamento": so_duracao,
        "_g": g, "_me": me, "_mg": mg, "_loo": (loo_grupo, loo_geral),
    }


def conferir_waiting(d):
    """Item 2: a espera é ATÉ a próxima erupção ou DESDE a anterior? Evidência interna (correlações) e o MASS::geyser.
    O geyser.csv é opcional (pesquisa/, baixe de https://vincentarelbundock.github.io/Rdatasets/csv/MASS/geyser.csv)."""
    e, w = d["eruptions"].to_numpy(float), d["waiting"].to_numpy(float)
    cor = lambda a, b: round(float(np.corrcoef(a, b)[0, 1]), 4)
    out = {"faithful": {"duracao_i_com_espera_i": cor(e, w), "duracao_i_com_espera_i_mais_1": cor(e[:-1], w[1:]),
                        "duracao_i_mais_1_com_espera_i": cor(e[1:], w[:-1])}}
    g = PASTA.parent / "pesquisa" / "geyser.csv"
    if g.exists():
        gd = pd.read_csv(g)
        dd, gw = gd["duration"].to_numpy(float), gd["waiting"].to_numpy(float)
        # o MASS (7.3-30 em diante) e o sm (2.2-5 em diante) dizem: waiting[i] é a espera ANTES da erupção i
        out["geyser_MASS"] = {"n": len(gd), "sha256": hashlib.sha256(g.read_bytes()).hexdigest(),
                              "duracao_i_com_a_espera_antes_dela": cor(dd, gw),
                              "duracao_i_com_a_espera_depois_dela": cor(dd[:-1], gw[1:])}
        # o faithful é um pedaço do geyser? procura qualquer sequência de 4 esperas iguais (ou 4 durações a menos de 1 s)
        fw, fe = w.astype(int).tolist(), e.tolist()
        gw_l, gd_l = gw.astype(int).tolist(), dd.tolist()
        seq_w = max((k for i in range(len(fw)) for j in range(len(gw_l))
                     for k in [next((t for t in range(len(fw)) if i + t >= len(fw) or j + t >= len(gw_l) or fw[i + t] != gw_l[j + t]), 0)]),
                    default=0)
        seq_d = max((k for i in range(len(fe)) for j in range(len(gd_l))
                     for k in [next((t for t in range(len(fe)) if i + t >= len(fe) or j + t >= len(gd_l) or abs(fe[i + t] - gd_l[j + t]) >= 1 / 60), 0)]),
                    default=0)
        out["faithful_dentro_do_geyser"] = {"maior_sequencia_de_esperas_iguais": seq_w, "maior_sequencia_de_duracoes_iguais": seq_d,
                                            "conclusao": "não: nenhuma sequência das 272 aparece nas 299 do geyser (são outras erupções)"
                                            if max(seq_w, seq_d) < 4 else "há trechos em comum: conferir"}
    return out


def cotovelo(X):
    """Item g: a melhor soma para k = 1 a 6 (scikit-learn, n_init=10, random_state=0)."""
    out = []
    for k in range(1, 7):
        km = KMeans(k, n_init=10, random_state=SEMENTE).fit(X)
        out.append({"k": k, "soma": round(float(km.inertia_), 4), "soma_tela": br(km.inertia_),
                    "tamanhos": sorted(np.bincount(km.labels_).tolist())})
    for a, b in zip(out, out[1:]):
        sa, sb = num(a["soma_tela"]), num(b["soma_tela"])
        b["queda_tela"] = f"{a['soma_tela']} − {b['soma_tela']} = {br(sa - sb)}"
        b["queda_pct"] = pct(sa - sb, sa)
        b["queda_pct_conta"] = f"{br(sa - sb)} ÷ {a['soma_tela']} = {pct(sa - sb, sa)}"
        b["queda_pct_exata"] = round(100 * (a["soma"] - b["soma"]) / a["soma"], 3)
    return out



EXEMPLO_REGRA_1 = 13  # rownames: uma longa (4,2 min; 78 min) que a regra 1 da rodada 1 manda para o centro de baixo


def exemplo_regra_1(X, rod, lab):
    """A regra 1 como conta, numa erupção longa que cai no grupo errado na rodada 1: a distância (em minutos) até
    cada centro inicial, com as duas medidas."""
    i = EXEMPLO_REGRA_1 - 1
    C0 = X[[r - 1 for r in INICIAIS]]
    d = np.sqrt(((X[i] - C0) ** 2).sum(axis=1))
    assert d[0] < d[1] and rod[0]["lab"][i] == 0 and lab[i] == 1, "o exemplo deixou de cair errado"
    partes = [f"√({br(abs(X[i, 0] - C0[g, 0]), 1)}² + {br(abs(X[i, 1] - C0[g, 1]))}²) = {br(d[g], 1)} min" for g in range(2)]
    return {"erupcao": f"erupção {EXEMPLO_REGRA_1}: {br(X[i, 0], 1)} min de duração, {br(X[i, 1])} min de espera (uma longa)",
            "ate_o_centro_de_baixo": partes[0], "ate_o_centro_de_cima": partes[1],
            "vai_para": "o centro de baixo (71 min de espera), o mais perto: cai com as curtas",
            "intuicao": "Na conta, quase toda a distância vem da espera: 7 min de diferença contra 0,2 min de duração."}


def fecha(conta, partes, op, total):
    """Confere que a conta escrita fecha com os números mostrados: op aplicado às partes (já lidas da tela) dá o total mostrado."""
    v = op(*[num(p) for p in partes])
    t = total.removesuffix("%")
    casas = len(t.split(",")[1]) if "," in t else 0
    assert br(v, casas) + ("%" if total.endswith("%") else "") == total, (conta, v, total)
    return conta


def tela_centro(c):
    return f"({br(c[0], 1)} min; {br(c[1], 1)} min)"


def montar_para_tela(X, dem, rod, lab, pares, aleat, cot, media, prev):
    n = len(X)
    dur, esp = X[:, 0], X[:, 1]
    fim = rod[-1]
    tc = [br(x) for x in fim["tamanhos"]]
    # 1. o gancho e o começo
    lab1 = rod[0]["lab"]
    t1 = [str(x) for x in rod[0]["tamanhos"]]
    errados = int((lab1 != lab).sum())
    assert ((lab1 == 1) <= (lab == 1)).all(), "esperado: o grupo de cima da 1ª divisão só tem longas"
    vao = int(((dur >= 2.5) & (dur < 3.5)).sum())
    # 2. as rodadas, com as trocas encadeadas (todas numa direção: do grupo 0 para o 1, conferido)
    rodadas, somas = [], [br(rod[0]["soma_regra1"])]
    for a, r in zip([None] + rod[:-1], rod):
        txt = {"rodada": str(r["rodada"])}
        if a is None:
            txt["regra_1"] = f"cada erupção vai para o centro mais perto: {t1[0]} × {t1[1]}"
            txt["conta_tamanhos"] = fecha(f"{t1[0]} + {t1[1]} = {n}", t1, lambda x, y: x + y, str(n))
        else:
            ida = int(((a["lab"] == 0) & (r["lab"] == 1)).sum())
            volta = int(((a["lab"] == 1) & (r["lab"] == 0)).sum())
            assert volta == 0 and ida == r["trocaram"]
            if r["parou"]:
                txt["regra_1"] = "ninguém troca de grupo: parou"
            else:
                ta, tb = [str(x) for x in a["tamanhos"]], [str(x) for x in r["tamanhos"]]
                txt["trocaram"] = str(ida)
                txt["regra_1"] = f"{ida} erupções trocam de grupo: {tb[0]} × {tb[1]}"
                txt["conta_tamanhos"] = (fecha(f"{ta[0]} − {ida} = {tb[0]}", [ta[0], str(ida)], lambda x, y: x - y, tb[0]) + " · " +
                                         fecha(f"{ta[1]} + {ida} = {tb[1]}", [ta[1], str(ida)], lambda x, y: x + y, tb[1]))
        if not r["parou"]:
            txt["regra_2"] = f"centros vão para a média: {tela_centro(r['centros'][0])} e {tela_centro(r['centros'][1])}"
            txt["centros"] = [tela_centro(r["centros"][0]), tela_centro(r["centros"][1])]
            txt["soma_depois_da_regra_1"] = br(r["soma_regra1"])
            txt["soma"] = br(r["soma"])
            somas.append(br(r["soma"]))
        rodadas.append(txt)
    quedas = [fecha(f"{a} − {b} = {br(num(a) - num(b))}", [a, b], lambda x, y: x - y, br(num(a) - num(b)))
              for a, b in zip(somas, somas[1:])]
    meias = [br(s) for s in dem["somas_meias_rodadas"]] + [br(fim["soma_regra1"])]
    assert all(num(b) <= num(a) for a, b in zip(meias, meias[1:]))
    queda_total = fecha(f"({somas[0]} − {somas[-1]}) ÷ {somas[0]} = {pct(num(somas[0]) - num(somas[-1]), num(somas[0]))}",
                        [somas[0], somas[-1]], lambda x, y: 100 * (x - y) / x, pct(num(somas[0]) - num(somas[-1]), num(somas[0])))
    # 3. por que a média (grupo curto: 100 erupções, a conta fica redonda)
    mc = media["curto"]
    s0 = br(mc["soma_com_centro_na_media"])
    nn = str(mc["n"])
    dl = mc["deslocado"]
    pqm = {
        "grupo": f"o grupo das curtas: {nn} erupções, centro {tela_centro((mc['media']['duracao_min'], mc['media']['espera_min']))}",
        "conta_do_centro": [fecha(f"duração: {br(mc['soma_duracoes'], 1)} ÷ {nn} = {br(mc['media']['duracao_min'], 1)} min",
                                  [br(mc["soma_duracoes"], 1), nn], lambda x, y: x / y, br(mc["media"]["duracao_min"], 1)),
                            fecha(f"espera: {br(mc['soma_esperas'])} ÷ {nn} = {br(mc['media']['espera_min'], 1)} min",
                                  [br(mc["soma_esperas"]), nn], lambda x, y: x / y, br(mc["media"]["espera_min"], 1))],
        "soma_com_o_centro_na_media": s0,
        "partes": fecha(f"{br(mc['parte_da_duracao'])} (duração) + {br(mc['parte_da_espera'])} (espera) = {s0}",
                        [br(mc["parte_da_duracao"]), br(mc["parte_da_espera"])], lambda x, y: x + y, s0),
        "centro_1_min_para_cima_na_espera": fecha(f"{s0} + {nn} × 1² = {br(dl['espera_mais_1']['soma'])}", [s0, nn],
                                                  lambda x, y: x + y, br(dl["espera_mais_1"]["soma"])),
        "centro_1_min_para_baixo_na_espera": f"{s0} + {nn} × 1² = {br(dl['espera_menos_1']['soma'])} (para qualquer lado, sobe igual)",
        "centro_1_min_na_duracao": fecha(f"{s0} + {nn} × 1² = {br(dl['duracao_mais_1']['soma'])}", [s0, nn],
                                         lambda x, y: x + y, br(dl["duracao_mais_1"]["soma"])),
        "centro_1_min_nas_duas": fecha(f"{s0} + {nn} × (1² + 1²) = {br(dl['os_dois_mais_1']['soma'])}", [s0, nn],
                                       lambda x, y: x + 2 * y, br(dl["os_dois_mais_1"]["soma"])),
        "centro_2_min_na_espera": fecha(f"{s0} + {nn} × 2² = {br(dl['espera_mais_2']['soma'])}", [s0, nn],
                                        lambda x, y: x + 4 * y, br(dl["espera_mais_2"]["soma"])),
        "regra": "tirar o centro d minutos da média soma n × d² (n = erupções do grupo); na média, a soma é a menor possível",
        "grupo_longo": f"nas longas ({media['longo']['n']}): {br(media['longo']['soma_com_centro_na_media'])} + {media['longo']['n']} × 1² = "
                       f"{br(media['longo']['deslocado']['espera_mais_1']['soma'])}",
        "intuicao": f"Cada erupção do grupo cobra o quadrado da distância até o centro. Andar 1 minuto para longe da média encarece a conta "
                    f"em exatamente 1 min² por erupção: {nn} erupções, +{nn}. Andar 2 minutos: +{nn} × 4. Não há lugar mais barato que a média.",
    }
    assert pqm["centro_1_min_para_baixo_na_espera"].startswith(f"{s0} + {nn} × 1² = ") and \
        br(num(s0) + num(nn)) == br(dl["espera_menos_1"]["soma"])
    # 4. cotovelo e ótimo local
    cot_t = [{"k": str(c["k"]), "soma": c["soma_tela"], **({"queda": c["queda_tela"], "queda_pct": c["queda_pct_conta"]} if "queda_tela" in c else {})}
             for c in cot]
    k3 = aleat["k_3"]
    melhor, comum, pior = k3[0], max(k3, key=lambda s: s["partidas"]), k3[-1]
    assert melhor["soma_tela"] == cot[2]["soma_tela"], "a melhor das 100 partidas com k = 3 deveria ser a do scikit-learn"
    acima = fecha(f"({pior['soma_tela']} − {melhor['soma_tela']}) ÷ {melhor['soma_tela']} = {pct(num(pior['soma_tela']) - num(melhor['soma_tela']), num(melhor['soma_tela']))}",
                  [pior["soma_tela"], melhor["soma_tela"]], lambda x, y: 100 * (x - y) / y,
                  pct(num(pior["soma_tela"]) - num(melhor["soma_tela"]), num(melhor["soma_tela"])))
    # 5. previsão pela duração
    cd = [br(fim["centros"][0, 0], 1), br(fim["centros"][1, 0], 1)]
    lim = br(prev["limiar_duracao_min"], 1)
    me = {k: br(v, 1) for k, v in prev["espera_media"].items()}
    ce = [br(fim["centros"][0, 1], 1), br(fim["centros"][1, 1], 1)]  # a espera de cada centro: a previsão
    eam, loo = prev["erro_medio_absoluto_min"], prev["deixar_um_de_fora"]
    ec, em = br(eam["pela_espera_do_centro_kmeans"], 1), br(eam["pela_media_geral"], 1)
    lc, lm = br(loo["pela_espera_do_centro_kmeans"], 1), br(loo["pela_media_geral"], 1)
    eg, lg = br(eam["pela_media_do_grupo"], 1), br(loo["pela_media_do_grupo"], 1)
    vezes = br(num(lm) / num(lc), 1)
    menor = pct(num(lm) - num(lc), num(lm))
    r3 = prev["regra_dos_3_minutos_extra"]
    # 6. por que padronizar quase não muda nada aqui: a espera é quase toda a soma
    sd_d, sd_e = float(np.sqrt(n * X[:, 0].var())), float(np.sqrt(n * X[:, 1].var()))
    pd_, pe_ = br(n * X[:, 0].var()), br(n * X[:, 1].var())
    s1 = cot[0]["soma_tela"]
    pz = dem["padronizado"]
    digitos = len(str(2 ** (n - 1) - 1))
    mant, expo = f"{2 ** (n - 1) - 1:.1e}".split("e+")
    razao = br(num(br(sd_e / np.sqrt(n), 1)) / num(br(sd_d / np.sqrt(n), 2)), 1)
    return {
        "formato": "Como o br() de estilo/estilo.py: ponto no milhar, vírgula no decimal, menos U+2212. Tempos em minutos com 1 casa "
                   "(as esperas do arquivo são inteiras); somas dos quadrados em min², inteiras; porcentagens com 1 casa.",
        "dataset": f"Old Faithful, Yellowstone (EUA): {n} erupções de verdade, cada uma com a duração e a espera, em minutos",
        "fonte_curta": "datasets::faithful do R (Härdle, 1991) · ver também Azzalini & Bowman (1990), Applied Statistics 39(3)",
        "nomes": {"centro": "centro (o nome técnico, uma vez: centróide)", "grupo": "grupo", "soma": "soma dos quadrados",
                  "k": "k = número de grupos", "medidas": "duração e espera"},
        "gancho": {
            "n": str(n),
            "faixas": f"duração de {br(dur.min(), 1)} a {br(dur.max(), 1)} min; espera de {br(esp.min())} a {br(esp.max())} min",
            "dois_tipos": f"{tc[0]} curtas e {tc[1]} longas",
            "conta": fecha(f"{tc[0]} + {tc[1]} = {n}", tc, lambda x, y: x + y, str(n)),
            "curtas": f"duram {cd[0]} min em média, com espera de {br(fim['centros'][0, 1], 1)} min",
            "longas": f"duram {cd[1]} min em média, com espera de {br(fim['centros'][1, 1], 1)} min",
            "vao": f"só {vao} das {n} erupções duram entre 2,5 e 3,5 min",
            "intuicao": "Erupção curta anda junto com espera curta; erupção longa, com espera longa. No gráfico, duas nuvens. "
                        "Ninguém disse ao k-means quantas são curtas: ele só recebeu k = 2.",
        },
        "regras": {"1": "cada erupção vai para o centro mais perto", "2": "cada centro vai para a média do seu grupo",
                   "para": "quando a regra 1 não troca ninguém de grupo"},
        "comeco": {
            "centros_iniciais": [f"erupção {INICIAIS[g]}: {br(X[INICIAIS[g] - 1, 0], 1)} min de duração, {br(X[INICIAIS[g] - 1, 1])} min de espera"
                                 for g in range(2)],
            "por_que_ruim": "as duas são erupções longas: os dois centros começam na mesma nuvem",
            "primeira_divisao": f"{t1[0]} × {t1[1]}",
            "conta": fecha(f"{t1[0]} + {t1[1]} = {n}", t1, lambda x, y: x + y, str(n)),
            "errados": f"{errados} longas caem no grupo das curtas",
            "conta_errados": fecha(f"{t1[0]} − {errados} = {tc[0]}", [t1[0], str(errados)], lambda x, y: x - y, tc[0]),
            "soma_no_comeco": somas[0],
            "exemplo_regra_1": exemplo_regra_1(X, rod, lab),
            "intuicao": "O corte sai quase na horizontal, na altura de 81 min de espera: parte as longas ao meio e junta a metade de baixo com todas as curtas.",
        },
        "rodadas": rodadas,
        "soma_caindo": {"lista": somas, "quedas": quedas, "queda_total": queda_total,
                        "meias_rodadas": meias,
                        "intuicao_meias_rodadas": "Cada regra, sozinha, só pode baixar a soma: trocar para o centro mais perto encurta "
                                                  "a distância de quem troca; pôr o centro na média é o lugar mais barato para o grupo."},
        "final": {"centros": [tela_centro(fim["centros"][0]), tela_centro(fim["centros"][1])], "tamanhos": f"{tc[0]} × {tc[1]}",
                  "soma": br(fim["soma"]), "rodadas": f"{len(rod)} rodadas (a {len(rod)}ª só confere que ninguém troca)",
                  "partes_da_soma": fecha(f"{br(media['curto']['soma_com_centro_na_media'])} + {br(media['longo']['soma_com_centro_na_media'])} = {br(fim['soma'])}",
                                          [br(media["curto"]["soma_com_centro_na_media"]), br(media["longo"]["soma_com_centro_na_media"])],
                                          lambda x, y: x + y, br(fim["soma"])),
                  "confere": "a mesma divisão do KMeans do scikit-learn (10 começos)"},
        "por_que_a_media": pqm,
        "por_que_para": {
            "jeitos_de_dividir": f"2^{n - 1} − 1 (2 elevado a {n - 1}, menos 1): um número de {digitos} algarismos, uns {br(float(mant), 1)} × 10^{int(expo)}",
            "intuicao": "A soma nunca sobe, e o número de jeitos de dividir as erupções em 2 grupos é enorme, mas finito: a soma não pode "
                        f"cair para sempre. Na prática, parou na {len(rod)}ª rodada.",
        },
        "otimo_local": {
            "k_2": f"de {br(pares['pares'])} pares de erupções usados como começo, {br(pares['chegam_na_mesma_divisao'])} chegam na mesma divisão "
                   f"(entre {min(map(int, pares['rodadas_ate_parar']))} e {max(map(int, pares['rodadas_ate_parar']))} rodadas)",
            "k_3": f"{PARTIDAS} começos sorteados, {len(k3)} finais diferentes",
            "k_3_melhor": f"soma {melhor['soma_tela']}: só {melhor['partidas']} de {PARTIDAS} começos chegam nela",
            "k_3_mais_comum": f"soma {comum['soma_tela']}: {comum['partidas']} de {PARTIDAS}",
            "k_3_pior": f"soma {pior['soma_tela']}: {pior['partidas']} de {PARTIDAS}",
            "k_3_pior_acima_da_melhor": acima,
            "k_3_somas": [f"{s['soma_tela']} ({s['partidas']}×)" for s in k3],
            "intuicao": "Com 2 grupos, qualquer começo chega no mesmo lugar. Com 3, o resultado depende de onde os centros nascem: "
                        "o algoritmo para no primeiro vale em que nenhuma regra melhora a soma, que não é sempre o mais fundo. "
                        "Por isso se roda várias vezes e fica a menor soma (o scikit-learn faz isso com n_init).",
        },
        "cotovelo": {
            "somas": cot_t,
            "intuicao": f"Mais grupos sempre baixam a soma (cada erupção sozinha no seu grupo dá soma zero), então a soma sozinha não escolhe o k. "
                        f"De 1 para 2 grupos a soma cai {cot[1]['queda_tela'].split(' = ')[1]} min² ({cot[1]['queda_pct']}); de 2 para 3, só "
                        f"{cot[2]['queda_tela'].split(' = ')[1]}: a curva dobra em k = 2, o cotovelo. É uma regra de bolso, não uma prova.",
        },
        "previsao": {
            "limiar": fecha(f"({cd[0]} + {cd[1]}) ÷ 2 = {lim} min", cd, lambda x, y: (x + y) / 2, lim),
            "regra": f"durou menos de {lim} min: grupo das curtas, espera prevista {ce[0]} min (a do centro); "
                     f"mais: grupo das longas, {ce[1]} min",
            "exemplo": f"uma erupção de 4 min: mais perto de {cd[1]} que de {cd[0]}, grupo das longas, espera prevista {ce[1]} min",
            "sem_grupo": f"sem grupo, o melhor chute é a média de todas: {me['geral']} min",
            "erro_medio": {"pelo_centro": ec + " min", "sem_grupo": em + " min"},
            "deixar_um_de_fora": {"pelo_centro": lc + " min", "sem_grupo": lm + " min",
                                  "como": "esconde uma erupção, refaz o k-means com as outras 271, prevê a escondida; repete para as 272"},
            "vezes_menor": fecha(f"{lm} ÷ {lc} = {vezes}", [lm, lc], lambda x, y: x / y, vezes),
            "quanto_menor": fecha(f"({lm} − {lc}) ÷ {lm} = {menor}", [lm, lc], lambda x, y: 100 * (x - y) / x, menor),
            "variante_media_pela_duracao": f"refazendo os grupos só pela duração ({prev['tamanhos']['curto']} curtas e {prev['tamanhos']['longo']} longas), "
                                           f"as esperas médias são {me['curto']} e {me['longo']} min; erro {eg} min (deixar-um-de-fora: {lg} min)",
            "regra_3_minutos": f"com o corte em 3 min (o dos guardas do parque), {r3['n_menos_de_3']} curtas com espera média de "
                               f"{br(r3['espera_media_menos_de_3'], 1)} min e {r3['n_3_ou_mais']} longas com {br(r3['espera_media_3_ou_mais'], 1)} min",
            "intuicao": f"Saber só quanto durou a erupção já diz o grupo, e o centro do grupo diz a espera: erro médio de {lc} min, contra {lm} min "
                        f"chutando a média de todas. Contado de forma honesta, escondendo cada erupção da conta, o erro fica igual ao de dentro da amostra ({ec} min).",
        },
        "padronizar": {
            "soma_com_k_1": fecha(f"{pd_} (duração) + {pe_} (espera) = {s1}", [pd_, pe_], lambda x, y: x + y, s1),
            "peso_da_espera": fecha(f"{pe_} ÷ {s1} = {pct(num(pe_), num(s1))}", [pe_, s1], lambda x, y: 100 * x / y, pct(num(pe_), num(s1))),
            "desvios": f"duração {br(sd_d / np.sqrt(n), 2)} min; espera {br(sd_e / np.sqrt(n), 1)} min",
            "mudam": f"{pz['mudam_de_grupo']} de {n} erupções mudam de grupo padronizando as duas medidas",
            "razao_dos_desvios": fecha(f"{br(sd_e / np.sqrt(n), 1)} ÷ {br(sd_d / np.sqrt(n), 2)} = {razao}",
                                       [br(sd_e / np.sqrt(n), 1), br(sd_d / np.sqrt(n), 2)], lambda x, y: x / y, razao),
            "intuicao": f"As duas estão em minutos, mas a espera varia {razao} vezes mais que a duração, então ela manda na distância. "
                        "Aqui isso quase não muda o resultado, porque as duas medidas separam os mesmos dois grupos.",
        },
    }


def main():
    d = carregar()
    X = d[["eruptions", "waiting"]].to_numpy(float)
    n = len(X)
    dem = demonstracao(d, X)
    lab, rod = dem.pop("_lab"), dem.pop("_rod")
    C = rod[-1]["centros"]
    pares = todos_os_pares(X, lab)
    rng = np.random.default_rng(SEMENTE)
    aleat = {f"k_{k}": partidas_aleatorias(X, k, rng) for k in (2, 3)}
    cot = cotovelo(X)
    media = por_que_a_media(X, lab)
    prev = previsao(X, lab, C)
    wt = conferir_waiting(d)
    tela = montar_para_tela(X, dem, rod, lab, pares, aleat, cot, media, prev)
    prev = {k: v for k, v in prev.items() if not k.startswith("_")}
    assert dem["scikit_learn"]["mesma_divisao"] and dem["scikit_learn"]["do_mesmo_comeco"]["mesma_divisao"]
    assert abs(dem["scikit_learn"]["inertia"] - dem["final"]["soma"]) < 1e-3
    assert abs(prev["deixar_um_de_fora"]["pela_media_do_grupo"] - prev["erro_medio_absoluto_min"]["pela_media_do_grupo"]) < 0.5
    assert cot[3]["queda_pct_exata"] > cot[2]["queda_pct_exata"], "o cuidado do cotovelo diz que de 3 para 4 cai mais, em %, que de 2 para 3"
    cuidados = [
        "Direção da espera: a documentação do R diz que waiting é a espera ATÉ A PRÓXIMA erupção. Não deu para fechar com fonte primária "
        "(Härdle 1991 e Azzalini & Bowman 1990 estão atrás de paywall e não foram lidos). Na outra versão dos dados (MASS::geyser, de Azzalini & Bowman), "
        "a descrição 'até a próxima' estava errada e foi corrigida para 'antes desta erupção' (MASS 7.3-30; pacote sm 2.2-5, dos próprios autores). "
        "As 272 erupções do faithful não estão entre as 299 do geyser (nenhuma sequência de 4 esperas em comum), então a correção não se transfere. "
        f"Evidência interna: no faithful, duração e espera da mesma linha têm correlação {br(wt['faithful']['duracao_i_com_espera_i'], 2)}; no geyser, "
        f"a duração tem {br(wt.get('geyser_MASS', {}).get('duracao_i_com_a_espera_depois_dela', float('nan')), 2)} com a espera DEPOIS dela e "
        f"{br(wt.get('geyser_MASS', {}).get('duracao_i_com_a_espera_antes_dela', float('nan')), 2)} com a espera ANTES. Então o faithful se comporta como "
        "'erupção e a espera depois dela', como diz o R e como a regra dos guardas usa. Mesmo assim: na fala e na tela, sem direção no tempo "
        "('erupção curta anda junto com espera curta'), nunca 'a duração prevê a próxima' como fato da fonte.",
        "Origem: o R cita W. Härdle (1991) como fonte do faithful e diz que Azzalini & Bowman (1990) usam 'uma versão mais completa'. "
        "Não dizer que as 272 são as medições de agosto de 1985 do artigo: a data das 272 não está documentada (são anteriores a 1991).",
        "Durações arredondadas: a documentação do R avisa que as durações foram anotadas em segundos e arredondadas (múltiplos de 5 s aparecem demais). "
        "Não muda nenhum número do vídeo; não mostrar durações com mais de 1 casa.",
        f"Sem padronizar, a espera responde por {tela['padronizar']['peso_da_espera'].split(' = ')[1]} da soma dos quadrados com k = 1: "
        f"o k-means aqui separa quase só pela espera. Padronizando, só {dem['padronizado']['mudam_de_grupo']} das {n} trocam de grupo; "
        "dizer 'as duas medidas concordam', não 'a duração não importa'.",
        "A previsão: a espera entra no agrupamento, então prever a espera pelo grupo é em parte circular. Duas conferências: deixar-um-de-fora "
        f"(erro {br(prev['deixar_um_de_fora']['pela_media_do_grupo'], 2)} min contra {br(prev['erro_medio_absoluto_min']['pela_media_do_grupo'], 2)} min "
        "dentro da amostra) e um k-means só na duração, sem a espera (mesma divisão, mesmo erro). O erro é médio absoluto, em minutos.",
        "A regra dos guardas (menos de 3 min: 68 min; mais de 3 min: 94 min) é a de hoje, de uma atividade do Serviço de Parques dos EUA; as esperas "
        f"do gêiser ficaram mais longas desde os dados do faithful (centros em {br(C[0, 1], 1)} e {br(C[1, 1], 1)} min). "
        "Usar só o corte de 3 min como comparação.",
        "Rodadas: a 1ª rodada é a primeira divisão (ninguém 'troca' porque ninguém tinha grupo); a última só confere que ninguém troca. "
        f"O KMeans do scikit-learn, do mesmo começo, também para com n_iter = {dem['scikit_learn']['do_mesmo_comeco']['n_iter']}.",
        f"Ótimo local: com k = 2 não há (todos os {br(pares['pares'])} pares de começo chegam na mesma divisão); o exemplo de ótimo local é com k = 3. "
        "Empates de distância: nenhum na demonstração; nas partidas sorteadas, poucos, resolvidos a favor do centro de número menor (registrado).",
        f"Cotovelo: em porcentagem do que sobrou, as quedas depois de k = 2 não são pequenas (de {min(c['queda_pct'] for c in cot[2:])} "
        f"a {max(c['queda_pct'] for c in cot[2:])}; de 3 para 4 cai mais, em %, "
        f"que de 2 para 3). O cotovelo aparece na curva em min² ({cot[1]['queda_tela'].split(' = ')[1]} contra {cot[2]['queda_tela'].split(' = ')[1]}), "
        "não nas porcentagens. Não dizer 'depois de 2 quase não cai'.",
        f"Previsão na tela: a espera do centro ({br(C[0, 1], 1)} e {br(C[1, 1], 1)} min). A leitura literal do pedido (refazer os grupos pela "
        f"duração e tirar a média) dá {br(prev['espera_media']['curto'], 1)} e {br(prev['espera_media']['longo'], 1)} min, com "
        f"{prev['tamanhos']['curto']} e {prev['tamanhos']['longo']} erupções; o erro é o mesmo, "
        f"{br(prev['deixar_um_de_fora']['pela_media_do_grupo'], 1)} min. Não misturar as duas na mesma tela.",
        "Por que para: 'a soma nunca sobe' vale para as duas regras; com empate de distância seria preciso manter o grupo atual para garantir "
        "que não fica trocando sem a soma mudar. Não acontece aqui.",
        "Licença: o arquivo não tem licença aberta explícita para os dados; fica em pesquisa/ (fora do GitHub). Os números vão para a tela com a fonte.",
    ]
    res = {
        "dataset": {
            "nome": "faithful (pacote datasets do R), via Rdatasets", "url": URL, "sha256": SHA256, "bytes": CSV.stat().st_size,
            "baixado_em": "2026-10-23", "arquivo": "videos/kmeans/pesquisa/faithful.csv (fora do GitHub)",
            "igual_ao_do_R": "conferido valor a valor com src/library/datasets/data/faithful.R do código-fonte do R (espelho wch/r-source)",
            "licenca": "sem licença aberta explícita para os dados: o pacote datasets é 'Part of R' (GPL-2 | GPL-3, que cobre o software), "
                       "e o Rdatasets diz que não conseguiu determinar a licença dos dados",
            "linhas": n, "colunas": {"eruptions": "duração da erupção (min)", "waiting": "espera (min; ver cuidados)"},
            "erupcoes_repetidas": int(n - len(np.unique(X, axis=0))),
            "faixas": {"duracao_min": [float(X[:, 0].min()), float(X[:, 0].max())], "espera_min": [int(X[:, 1].min()), int(X[:, 1].max())]},
            "medias": {"duracao_min": round(float(X[:, 0].mean()), 4), "espera_min": round(float(X[:, 1].mean()), 4)},
            "desvios_ddof0": {"duracao_min": round(float(X[:, 0].std()), 4), "espera_min": round(float(X[:, 1].std()), 4)},
        },
        "convencao": {"algoritmo": "Lloyd: regra 1 (centro mais perto) e regra 2 (centro na média), até a regra 1 não trocar ninguém",
                      "distancia": "euclidiana nas medidas cruas (min), sem padronizar",
                      "soma": "Σ distância² até o centro do grupo, em min² (inertia do scikit-learn)",
                      "empate": "o centro de número menor", "semente": SEMENTE, "partidas": PARTIDAS},
        "espera_direcao": wt,
        "demonstracao": dem,
        "todos_os_pares_k2": pares,
        "partidas_aleatorias": aleat,
        "cotovelo": cot,
        "por_que_a_media": media,
        "previsao": prev,
        "para_tela": tela,
        "cuidados": cuidados,
    }
    (PASTA / "resultados.json").write_text(json.dumps(res, ensure_ascii=False, indent=1,
                                                      default=lambda o: o.item() if hasattr(o, "item") else str(o)) + "\n")
    print("OK videos/kmeans/dados/resultados.json")
    print("  somas:", " → ".join(tela["soma_caindo"]["lista"]), f"(sklearn {br(dem['scikit_learn']['inertia'])})")
    print("  cotovelo:", " · ".join(f"k={c['k']} {c['soma_tela']}" for c in cot))
    print("  k=3:", ", ".join(tela["otimo_local"]["k_3_somas"]))
    print("  previsão:", tela["previsao"]["erro_medio"], "LOO", tela["previsao"]["deixar_um_de_fora"])


if __name__ == "__main__":
    main()
