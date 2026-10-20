"""Confere, na base real de Taiwan, as afirmações TEÓRICAS de teoria.md.

Não substitui calcular.py (que gera os números do roteiro em resultados.json): este script
só testa, com os mesmos dados, o que a teoria diz. Rode da raiz do projeto:
    .venv/bin/python videos/arvore-de-decisao/dados/conferir_teoria.py
Salva conferir_teoria.json nesta pasta.

O que confere:
 A. Interpretação do Gini: rotular sorteando pela proporção erra ~Gini; rotular pela maioria erra min(p).
 B. A pergunta vencedora (PAY_0 >= 2) por três critérios: Gini, entropia (bits) e taxa de erro;
    e a armadilha da média simples (sem ponderar pelo tamanho).
 C. Busca exaustiva na raiz (todas as colunas, todos os limiares) por Gini, entropia e erro.
 D. Um corte que baixa o Gini sem mudar nenhuma previsão.
 E. Viés do ganho com muitos valores (Quinlan 1986): divisão em vários ramos pelo ID do cliente
    e por PAY_0, contra a divisão binária.
 F. Guloso x ótimo: árvore de profundidade 2 gulosa x a de menor Gini nas folhas (e a de maior
    acerto), buscando em todas as perguntas de 11 colunas.
 G. Gini x entropia ao longo da profundidade (mesma divisão treino/teste de calcular.py) e por que
    a árvore sem limite não chega a 100% no treino (clientes idênticos com rótulos diferentes).
"""
from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier, export_text

AQUI = Path(__file__).resolve().parent
ZIP = AQUI / "default_of_credit_card_clients.zip"
XLS = "default of credit card clients.xls"
SAIDA = AQUI / "conferir_teoria.json"
SEMENTE = 42  # a mesma de calcular.py

with zipfile.ZipFile(ZIP) as z:
    df = pd.read_excel(io.BytesIO(z.read(XLS)), header=1)
y = df["default payment next month"].to_numpy().astype(int)
ids = df["ID"].to_numpy()
X = df.drop(columns=["ID", "default payment next month"])
cols = list(X.columns)
Xn = X.to_numpy(dtype=float)
N = len(y)
out: dict = {}


def gini_counts(n, c1):
    """Gini de nós com n exemplos e c1 da classe 1 (vetorizado). Nó vazio -> 0."""
    n = np.asarray(n, dtype=float)
    c1 = np.asarray(c1, dtype=float)
    with np.errstate(invalid="ignore", divide="ignore"):
        p = np.where(n > 0, c1 / n, 0.0)
    return 1.0 - (p ** 2 + (1 - p) ** 2) * (n > 0)


def entropia_counts(n, c1):
    n = np.asarray(n, dtype=float)
    c1 = np.asarray(c1, dtype=float)
    with np.errstate(invalid="ignore", divide="ignore"):
        p = np.where(n > 0, c1 / n, 0.0)
        h = -(np.where(p > 0, p * np.log2(p), 0.0) + np.where(p < 1, (1 - p) * np.log2(1 - p), 0.0))
    return np.where(n > 0, h, 0.0)


def erro_counts(n, c1):
    n = np.asarray(n, dtype=float)
    c1 = np.asarray(c1, dtype=float)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(n > 0, np.minimum(c1, n - c1) / n, 0.0)


CRIT = {"gini": gini_counts, "entropia_bits": entropia_counts, "erro": erro_counts}

# ---------------------------------------------------------------- A. interpretação do Gini
c1 = int(y.sum())
p1 = c1 / N
p = np.array([1 - p1, p1])
g_raiz = float(1 - (p ** 2).sum())
rng = np.random.default_rng(0)
erros = [float((rng.choice(2, size=N, p=p) != y).mean()) for _ in range(20)]
# dois clientes sorteados (com reposição) serem de classes diferentes
pares = rng.integers(0, N, size=(200_000, 2))
dif = float((y[pares[:, 0]] != y[pares[:, 1]]).mean())
out["A_interpretacao_gini"] = {
    "n": N, "calote": c1, "p_calote": p1,
    "gini_1_menos_soma_p2": g_raiz,
    "gini_soma_p_vezes_1_menos_p": float((p * (1 - p)).sum()),
    "gini_2p_1_menos_p": 2 * p1 * (1 - p1),
    "erro_sorteando_rotulo_pela_proporcao_media_20_rodadas": float(np.mean(erros)),
    "erro_sorteando_min_max_20_rodadas": [min(erros), max(erros)],
    "prob_dois_clientes_sorteados_de_classes_diferentes_200mil_pares": dif,
    "erro_rotulando_todo_mundo_pela_maioria": float(min(p)),
    "entropia_raiz_bits": float(entropia_counts(N, c1)),
    "maximo_gini_2_classes": float(gini_counts(2, 1)),
    "maximo_entropia_2_classes_bits": float(entropia_counts(2, 1)),
}

# ---------------------------------------------------------------- B. a vencedora por 3 critérios
j0 = cols.index("PAY_0")
sim = Xn[:, j0] >= 2  # == PAY_0 > 1.5 (valores inteiros)
n_s, c_s = int(sim.sum()), int(y[sim].sum())
n_n, c_n = N - n_s, c1 - c_s
w_s, w_n = n_s / N, n_n / N
B = {"pergunta": "PAY_0 >= 2 (scikit-learn: PAY_0 <= 1.5, lados trocados)",
     "sim": {"n": n_s, "calote": c_s}, "nao": {"n": n_n, "calote": c_n},
     "peso_sim": w_s, "peso_nao": w_n}
for nome, f in CRIT.items():
    pai = float(f(N, c1))
    fs, fn = float(f(n_s, c_s)), float(f(n_n, c_n))
    pond = w_s * fs + w_n * fn
    B[nome] = {"pai": pai, "filho_sim": fs, "filho_nao": fn, "ponderado": pond,
               "ganho": pai - pond, "pct_do_pai_removido": 100 * (pai - pond) / pai,
               "media_simples_errada": (fs + fn) / 2,
               "media_simples_menos_pai": (fs + fn) / 2 - pai}
B["erro_previsoes"] = {
    "antes_todo_mundo_paga_erros": c1,
    "depois_sim_preve_calote_nao_preve_paga_erros": (n_s - c_s) + c_n,
}
out["B_vencedora_tres_criterios"] = B

# ---------------------------------------------------------------- C. busca exaustiva na raiz
codes, uniques = [], []
for j in range(len(cols)):
    u, inv = np.unique(Xn[:, j], return_inverse=True)
    uniques.append(u)
    codes.append(inv)


def cortes_no(mask, colunas=None):
    """Para um nó (máscara), todas as perguntas 'coluna <= limiar' (pontos médios) e o
    valor ponderado de cada critério nos filhos. Devolve lista de dicts por coluna."""
    yy = y[mask]
    n_t, c_t = int(mask.sum()), int(yy.sum())
    res = []
    for j in (range(len(cols)) if colunas is None else colunas):
        cod = codes[j][mask]
        tot = np.bincount(cod, minlength=len(uniques[j]))
        pos = np.bincount(cod, weights=yy, minlength=len(uniques[j]))
        presentes = tot > 0
        u = uniques[j][presentes]
        tot, pos = tot[presentes], pos[presentes]
        if len(u) < 2:
            continue
        nl = np.cumsum(tot)[:-1]
        cl = np.cumsum(pos)[:-1]
        nr, cr = n_t - nl, c_t - cl
        lim = (u[:-1] + u[1:]) / 2
        d = {"coluna": cols[j], "limiares": lim, "nl": nl, "cl": cl}
        for nome, f in CRIT.items():
            d[nome] = (nl * f(nl, cl) + nr * f(nr, cr)) / n_t
        res.append(d)
    return res, n_t, c_t


raiz, _, _ = cortes_no(np.ones(N, bool))
total = int(sum(len(d["limiares"]) for d in raiz))
C = {"perguntas_testadas": total}
for nome, f in CRIT.items():
    pai = float(f(N, c1))
    todas = [(float(pai - v), d["coluna"], float(t)) for d in raiz for v, t in zip(d[nome], d["limiares"])]
    todas.sort(key=lambda r: -r[0])
    ganho_venc = next(g for g, c, t in todas if c == "PAY_0" and t == 1.5)
    C[nome] = {
        "pai": pai,
        "top5": [{"coluna": c, "limiar_sklearn": t, "ganho": g} for g, c, t in todas[:5]],
        "posicao_da_PAY_0_1.5": 1 + sum(1 for g, c, t in todas if g > ganho_venc + 1e-15),
        "perguntas_com_ganho_zero_ou_menos": sum(1 for g, c, t in todas if g <= 1e-15),
    }
out["C_busca_exaustiva_raiz"] = C

# ---------------------------------------------------------------- D. Gini cai, previsão não muda
mask_nao = ~sim
no, n_t, c_t = cortes_no(mask_nao)
melhor = min(((float(v), d["coluna"], float(t), int(nl), int(cl))
              for d in no for v, t, nl, cl in zip(d["gini"], d["limiares"], d["nl"], d["cl"])))
v, col, t, nl, cl = melhor
nr, cr = n_t - nl, c_t - cl
maj = lambda n, c: int(c > n - c)
D = {"no": "lado 'não' da raiz (PAY_0 <= 1.5)", "n": n_t, "calote": c_t,
     "melhor_pergunta_por_gini": f"{col} <= {t}",
     "gini_no": float(gini_counts(n_t, c_t)), "gini_ponderado_filhos": v,
     "ganho_gini": float(gini_counts(n_t, c_t)) - v,
     "filho_sim": {"n": nl, "calote": cl, "taxa_calote_pct": 100 * cl / nl, "maioria": maj(nl, cl)},
     "filho_nao": {"n": nr, "calote": cr, "taxa_calote_pct": 100 * cr / nr, "maioria": maj(nr, cr)},
     "maioria_no": maj(n_t, c_t)}
D["acertos_antes"] = max(c_t, n_t - c_t)
D["acertos_depois"] = max(cl, nl - cl) + max(cr, nr - cr)
D["melhor_ganho_por_taxa_de_erro_neste_no"] = max(
    float(erro_counts(n_t, c_t) - x) for d in no for x in d["erro"])
out["D_gini_cai_previsao_igual"] = D

# ---------------------------------------------------------------- E. viés com muitos valores
def multiway(codigos):
    tot = np.bincount(codigos)
    pos = np.bincount(codigos, weights=y)
    ok = tot > 0
    tot, pos = tot[ok], pos[ok]
    r = {"ramos": int(ok.sum())}
    for nome, f in (("gini", gini_counts), ("entropia_bits", entropia_counts)):
        pai = float(f(N, c1))
        r["ganho_" + nome] = pai - float((tot * f(tot, pos)).sum() / N)
    pr = tot / N
    r["IV_bits"] = float(-(pr * np.log2(pr)).sum())
    r["razao_de_ganho"] = r["ganho_entropia_bits"] / r["IV_bits"]
    return r


_, id_codes = np.unique(ids, return_inverse=True)
E = {"multiway_ID_do_cliente": multiway(id_codes),
     "multiway_PAY_0_um_ramo_por_valor": multiway(codes[j0]),
     "binaria_PAY_0_ge_2": {"ganho_gini": B["gini"]["ganho"], "ganho_entropia_bits": B["entropia_bits"]["ganho"]}}
# melhor pergunta binária sobre o ID (CART)
u, inv = np.unique(ids, return_inverse=True)
tot = np.bincount(inv); pos = np.bincount(inv, weights=y)
nl = np.cumsum(tot)[:-1]; cl = np.cumsum(pos)[:-1]
pond = (nl * gini_counts(nl, cl) + (N - nl) * gini_counts(N - nl, c1 - cl)) / N
E["binaria_melhor_corte_no_ID"] = {"limiar": float((u[:-1] + u[1:])[pond.argmin()] / 2),
                                   "ganho_gini": g_raiz - float(pond.min())}
iv_bin = float(entropia_counts(N, n_s))
E["binaria_PAY_0_ge_2"]["IV_bits"] = iv_bin
E["binaria_PAY_0_ge_2"]["razao_de_ganho"] = B["entropia_bits"]["ganho"] / iv_bin
out["E_vies_muitos_valores"] = E

# ---------------------------------------------------------------- F. guloso x ótimo (profundidade 2)
poucas = ["PAY_0", "PAY_2", "PAY_3", "PAY_4", "PAY_5", "PAY_6", "SEX", "EDUCATION", "MARRIAGE", "AGE", "LIMIT_BAL"]
idx = [cols.index(c) for c in poucas]


def melhor_filho(mask):
    """Melhor corte de um nó entre as colunas 'poucas'. Devolve (gini ponderado do melhor por
    Gini, a pergunta, acertos dessa pergunta, maior número de acertos possível, a pergunta, n)."""
    res, n_t, c_t = cortes_no(mask, idx)
    g0 = float(gini_counts(n_t, c_t)); a0 = max(c_t, n_t - c_t)
    bg, qg, ag = g0, None, a0
    ba, qa = a0, None
    for d in res:
        nl, cl = d["nl"], d["cl"]
        nr, cr = n_t - nl, c_t - cl
        ac = np.maximum(cl, nl - cl) + np.maximum(cr, nr - cr)
        k = int(np.argmin(d["gini"]))
        if d["gini"][k] < bg - 1e-15:
            bg, qg, ag = float(d["gini"][k]), f'{d["coluna"]} <= {float(d["limiares"][k])}', int(ac[k])
        k = int(np.argmax(ac))
        if ac[k] > ba:
            ba, qa = int(ac[k]), f'{d["coluna"]} <= {float(d["limiares"][k])}'
    return bg, qg, ag, ba, qa, n_t


cand = [(j, float(t)) for j in idx for t in (uniques[j][:-1] + uniques[j][1:]) / 2]
melhor_g = (np.inf, None)
melhor_a = (-1, None)
guloso = None
g_root_min = np.inf
for j, t in cand:
    m = Xn[:, j] <= t
    gl, ql, agl, al, qal, nl_ = melhor_filho(m)
    gr, qr, agr, ar, qar, nr_ = melhor_filho(~m)
    folhas_g = (nl_ * gl + nr_ * gr) / N
    if folhas_g < melhor_g[0] - 1e-15:
        melhor_g = (folhas_g, (f"{cols[j]} <= {t}", ql, qr))
    if al + ar > melhor_a[0]:
        melhor_a = (al + ar, (f"{cols[j]} <= {t}", qal, qar))
    yl = y[m]
    g_root = (m.sum() * gini_counts(m.sum(), yl.sum()) + (~m).sum() * gini_counts((~m).sum(), y[~m].sum())) / N
    if g_root < g_root_min - 1e-15:
        g_root_min = float(g_root)
        guloso = (folhas_g, (f"{cols[j]} <= {t}", ql, qr), agl + agr)
arv = DecisionTreeClassifier(criterion="gini", max_depth=2, random_state=0).fit(X[poucas], y)
folhas = arv.apply(X[poucas])
g_folhas_sk = 0.0
for f_ in np.unique(folhas):
    mm = folhas == f_
    g_folhas_sk += mm.sum() * float(gini_counts(mm.sum(), y[mm].sum()))
g_folhas_sk /= N
out["F_guloso_vs_otimo_prof2"] = {
    "colunas": poucas, "perguntas_por_no": len(cand),
    "guloso": {"arvore": guloso[1], "gini_nas_folhas": float(guloso[0]), "acuracia_pct": 100 * guloso[2] / N},
    "guloso_sklearn_confere": {"texto": export_text(arv, feature_names=poucas),
                               "gini_nas_folhas": g_folhas_sk, "acuracia_pct": 100 * arv.score(X[poucas], y)},
    "otimo_por_gini_nas_folhas": {"arvore": melhor_g[1], "gini_nas_folhas": float(melhor_g[0])},
    "otimo_por_acuracia": {"arvore": melhor_a[1], "acuracia_pct": 100 * melhor_a[0] / N},
}

# ---------------------------------------------------------------- G. Gini x entropia; teto do treino
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.3, random_state=SEMENTE, stratify=y)
curva = []
for d in [1, 2, 3, 4, 5, 6, 8, 10, 15, None]:
    lin = {"max_depth": d}
    for crit in ["gini", "entropy"]:
        t_ = DecisionTreeClassifier(criterion=crit, max_depth=d, random_state=SEMENTE).fit(Xtr, ytr)
        lin[crit + "_treino_pct"] = round(100 * t_.score(Xtr, ytr), 2)
        lin[crit + "_teste_pct"] = round(100 * t_.score(Xte, yte), 2)
        lin[crit + "_folhas"] = int(t_.get_n_leaves())
    curva.append(lin)
t3 = {c: export_text(DecisionTreeClassifier(criterion=c, max_depth=3, random_state=0).fit(X, y), feature_names=cols)
      for c in ["gini", "entropy"]}
livre_sementes = []
for rs in range(5):
    t_ = DecisionTreeClassifier(criterion="gini", random_state=rs).fit(Xtr, ytr)
    livre_sementes.append({"random_state": rs, "teste_pct": round(100 * t_.score(Xte, yte), 2),
                           "folhas": int(t_.get_n_leaves())})
# clientes de treino com atributos idênticos e rótulos diferentes: nenhuma árvore separa
tr = Xtr.copy(); tr["_y"] = ytr
grp = tr.groupby(cols)["_y"].agg(["size", "sum"])
conflito = grp[(grp["sum"] > 0) & (grp["sum"] < grp["size"])]
erros_inevitaveis = int(np.minimum(conflito["sum"], conflito["size"] - conflito["sum"]).sum())
livre = DecisionTreeClassifier(criterion="gini", random_state=SEMENTE).fit(Xtr, ytr)
out["G_gini_vs_entropia_e_teto"] = {
    "divisao": "train_test_split(test_size=0.3, stratify=y, random_state=42), como calcular.py",
    "curva": curva,
    "raiz_igual_gini_entropia_base_inteira": t3["gini"].splitlines()[0] == t3["entropy"].splitlines()[0],
    "raiz": t3["gini"].splitlines()[0].strip(),
    "profundidade3_identica": t3["gini"] == t3["entropy"],
    "sem_limite_gini_por_random_state": livre_sementes,
    "treino_grupos_identicos_com_rotulos_diferentes": int(len(conflito)),
    "treino_erros_inevitaveis": erros_inevitaveis,
    "treino_erros_da_arvore_sem_limite": int((livre.predict(Xtr) != ytr).sum()),
    "treino_n": int(len(ytr)),
}

texto = json.dumps(out, ensure_ascii=False, indent=1, default=float)
SAIDA.write_text(texto + "\n", encoding="utf-8")
print(texto)
print("OK conferir_teoria.json salvo")
