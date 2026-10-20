"""Números do vídeo "árvore de decisão" (como a árvore escolhe a pergunta: impureza de Gini).

Dataset: Default of Credit Card Clients (Yeh & Lien, 2009), UCI id 350, CC BY 4.0.
30 000 clientes reais de cartão de crédito de um banco de Taiwan, abril a setembro de 2005;
alvo = deu calote (não pagou) no mês seguinte.

Rode da raiz do projeto:
    .venv/bin/python videos/arvore-de-decisao/dados/calcular.py

Imprime tudo e salva resultados.json nesta pasta. Cada número é conferido duas vezes:
pela conta à mão (contagens do pandas + fórmula) e por um caminho independente
(numpy vetorizado e/ou o próprio scikit-learn). Se algo não bater, o script para com erro.
"""

from __future__ import annotations

import hashlib
import io
import json
import zipfile
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.tree import DecisionTreeClassifier, export_text

AQUI = Path(__file__).resolve().parent
ZIP = AQUI / "default_of_credit_card_clients.zip"
XLS = "default of credit card clients.xls"
SAIDA = AQUI / "resultados.json"
SEMENTE = 42
TOL = 1e-12

# Nomes legíveis (pt-BR) das colunas, a partir da documentação oficial do UCI.
NOMES = {
    "LIMIT_BAL": "limite do cartão (NT$, inclui cartões adicionais da família)",
    "SEX": "sexo",
    "EDUCATION": "escolaridade",
    "MARRIAGE": "estado civil",
    "AGE": "idade (anos)",
    "PAY_0": "situação da fatura de setembro/2005 (-1 em dia; 1 = 1 mês de atraso; 2 = 2 meses...)",
    "PAY_2": "situação da fatura de agosto/2005",
    "PAY_3": "situação da fatura de julho/2005",
    "PAY_4": "situação da fatura de junho/2005",
    "PAY_5": "situação da fatura de maio/2005",
    "PAY_6": "situação da fatura de abril/2005",
    "BILL_AMT1": "valor da fatura de setembro/2005 (NT$)",
    "BILL_AMT2": "valor da fatura de agosto/2005 (NT$)",
    "BILL_AMT3": "valor da fatura de julho/2005 (NT$)",
    "BILL_AMT4": "valor da fatura de junho/2005 (NT$)",
    "BILL_AMT5": "valor da fatura de maio/2005 (NT$)",
    "BILL_AMT6": "valor da fatura de abril/2005 (NT$)",
    "PAY_AMT1": "valor pago em setembro/2005 (NT$)",
    "PAY_AMT2": "valor pago em agosto/2005 (NT$)",
    "PAY_AMT3": "valor pago em julho/2005 (NT$)",
    "PAY_AMT4": "valor pago em junho/2005 (NT$)",
    "PAY_AMT5": "valor pago em maio/2005 (NT$)",
    "PAY_AMT6": "valor pago em abril/2005 (NT$)",
}

# Perguntas candidatas: legíveis por leigo, limiares redondos. "sim" = condição verdadeira.
PERGUNTAS = [
    {
        "id": "atraso_2_meses",
        "pergunta": "Está com 2 meses ou mais de atraso na fatura de setembro?",
        "coluna": "PAY_0",
        "regra": "PAY_0 >= 2",
        "por_que_o_limiar": "Na documentação, 2 = atraso de dois meses. Para o scikit-learn é o corte PAY_0 <= 1,5.",
        "cond": lambda d: d["PAY_0"] >= 2,
    },
    {
        "id": "qualquer_atraso",
        "pergunta": "Está com algum atraso (1 mês ou mais) na fatura de setembro?",
        "coluna": "PAY_0",
        "regra": "PAY_0 >= 1",
        "por_que_o_limiar": "Mesma coluna, limiar um degrau abaixo: 1 = atraso de um mês. Mostra que o limiar importa.",
        "cond": lambda d: d["PAY_0"] >= 1,
    },
    {
        "id": "limite_baixo",
        "pergunta": "O limite do cartão é de até NT$ 50 mil?",
        "coluna": "LIMIT_BAL",
        "regra": "LIMIT_BAL <= 50000",
        "por_que_o_limiar": "NT$ 50 mil é o quartil de baixo: cerca de 1 em cada 4 clientes tem limite até aí.",
        "cond": lambda d: d["LIMIT_BAL"] <= 50_000,
    },
    {
        "id": "pagou_zero",
        "pergunta": "Pagou zero no mês de setembro?",
        "coluna": "PAY_AMT1",
        "regra": "PAY_AMT1 == 0",
        "por_que_o_limiar": "Zero é o limiar mais simples: pagou alguma coisa ou não pagou nada.",
        "cond": lambda d: d["PAY_AMT1"] == 0,
    },
    {
        "id": "menos_de_30",
        "pergunta": "Tem menos de 30 anos?",
        "coluna": "AGE",
        "regra": "AGE < 30",
        "por_que_o_limiar": "Intuição de senso comum (jovem paga pior?), limiar redondo.",
        "cond": lambda d: d["AGE"] < 30,
    },
    {
        "id": "casado",
        "pergunta": "É casado(a)?",
        "coluna": "MARRIAGE",
        "regra": "MARRIAGE == 1",
        "por_que_o_limiar": "Intuição de senso comum (casado é mais estável?). 1 = casado na documentação.",
        "cond": lambda d: d["MARRIAGE"] == 1,
    },
]


def br(x: float, casas: int = 4) -> str:
    """Número no formato brasileiro (vírgula decimal)."""
    return f"{x:.{casas}f}".replace(".", ",")


def gini(n_pagou: int, n_calote: int) -> float:
    n = n_pagou + n_calote
    if n == 0:
        return 0.0
    p0, p1 = n_pagou / n, n_calote / n
    return 1.0 - (p0 * p0 + p1 * p1)


def conta_gini(n_pagou: int, n_calote: int) -> dict:
    """A conta do Gini passo a passo, com os números reais."""
    n = n_pagou + n_calote
    p0, p1 = n_pagou / n, n_calote / n
    q0, q1 = p0 * p0, p1 * p1
    g = 1.0 - (q0 + q1)
    g2 = 2.0 * p0 * p1  # forma equivalente para duas classes: conferência
    assert abs(g - g2) < TOL, (g, g2)
    assert abs(g - gini(n_pagou, n_calote)) < TOL
    return {
        "n": n,
        "pagou": n_pagou,
        "calote": n_calote,
        "p_pagou": p0,
        "p_calote": p1,
        "p_pagou_ao_quadrado": q0,
        "p_calote_ao_quadrado": q1,
        "gini": g,
        "conferencia_2p(1-p)": g2,
        "taxa_de_calote_pct": 100 * p1,
        "um_em_cada": (n / n_calote) if n_calote else None,
        "conta": conta_texto(n_pagou, n_calote),
    }


def conta_texto(n_pagou: int, n_calote: int) -> str:
    """Conta passo a passo com 6 casas. Cada número é o valor verdadeiro arredondado;
    por isso o resultado vem com '≈' (somar os números já arredondados pode diferir na última casa).
    A versão que fecha exatamente com os números mostrados está em para_tela (2 casas)."""
    n = n_pagou + n_calote
    p0, p1 = n_pagou / n, n_calote / n
    return (
        f"p(pagou) = {n_pagou} / {n} ≈ {br(p0, 6)}; p(calote) = {n_calote} / {n} ≈ {br(p1, 6)}; "
        f"Gini = 1 − (p(pagou)² + p(calote)²) ≈ 1 − ({br(p0 * p0, 6)} + {br(p1 * p1, 6)}) ≈ {br(gini(n_pagou, n_calote), 6)}"
    )


def _q(x, d: int) -> Decimal:
    """Arredonda como na escola (meio para cima) para d casas."""
    return Decimal(repr(float(x))).quantize(Decimal(1).scaleb(-d), rounding=ROUND_HALF_UP)


def _brd(x: Decimal) -> str:
    return str(x).replace(".", ",")


def gini_tela(n_pagou: int, n_calote: int, d: int) -> dict:
    """A conta do Gini como vai na tela, com d casas, refeita SÓ com os números mostrados
    (o que alguém com calculadora faria). Cada passo é conta exata ou arredondamento dos números mostrados;
    'fecha' = as probabilidades mostradas somam 1 e o resultado final bate com o Gini verdadeiro arredondado."""
    n = n_pagou + n_calote
    p0, p1 = n_pagou / n, n_calote / n
    a, b = _q(p0, d), _q(p1, d)
    a2, b2 = _q(a * a, d), _q(b * b, d)
    soma = a2 + b2
    g = Decimal(1) - soma
    verdadeiro = _q(gini(n_pagou, n_calote), d)
    fecha = (a + b == 1) and (g == verdadeiro)
    return {
        "casas": d,
        "fecha": bool(fecha),
        "gini_tela": float(g),
        "conta": f"1 − ({_brd(a)}² + {_brd(b)}²) = 1 − ({_brd(a2)} + {_brd(b2)}) = 1 − {_brd(soma)} = {_brd(g)}",
        "_g": g,
    }


def corte_tela(r: dict, g_raiz_tela: Decimal, d: int) -> dict:
    """Gini ponderado e ganho como vão na tela, com d casas, a partir dos números mostrados."""
    gs = gini_tela(r["sim"]["pagou"], r["sim"]["calote"], d)
    gn = gini_tela(r["nao"]["pagou"], r["nao"]["calote"], d)
    ws, wn = _q(r["peso_sim"], d), _q(r["peso_nao"], d)
    ps, pn = _q(ws * gs["_g"], d), _q(wn * gn["_g"], d)
    pond = ps + pn
    ganho = g_raiz_tela - pond
    fecha = (
        gs["fecha"] and gn["fecha"] and ws + wn == 1
        and pond == _q(r["gini_ponderado"], d) and ganho == _q(r["ganho"], d)
    )
    return {
        "casas": d,
        "fecha": bool(fecha),
        "gini_sim": gs["conta"],
        "gini_nao": gn["conta"],
        "ponderado": f"{_brd(ws)} × {_brd(gs['_g'])} + {_brd(wn)} × {_brd(gn['_g'])} = {_brd(ps)} + {_brd(pn)} = {_brd(pond)}",
        "ganho": f"{_brd(g_raiz_tela)} − {_brd(pond)} = {_brd(ganho)}",
    }


def limpa(t: dict) -> dict:
    return {k: v for k, v in t.items() if not k.startswith("_")}


def avaliar_corte(y: np.ndarray, mascara_sim: np.ndarray, g_raiz: float) -> dict:
    N = len(y)
    sim_calote = int(y[mascara_sim].sum())
    sim_n = int(mascara_sim.sum())
    nao_calote = int(y[~mascara_sim].sum())
    nao_n = N - sim_n
    lado_sim = conta_gini(sim_n - sim_calote, sim_calote)
    lado_nao = conta_gini(nao_n - nao_calote, nao_calote)
    w_sim, w_nao = sim_n / N, nao_n / N
    ponderado = w_sim * lado_sim["gini"] + w_nao * lado_nao["gini"]
    ganho = g_raiz - ponderado
    r = {
        "sim": lado_sim,
        "nao": lado_nao,
        "peso_sim": w_sim,
        "peso_nao": w_nao,
        "gini_ponderado": ponderado,
        "ganho": ganho,
        "ganho_pct_da_raiz": 100 * ganho / g_raiz,
    }
    r["conta_ponderado"] = (
        f"({sim_n}/{N}) × Gini(sim) + ({nao_n}/{N}) × Gini(não) ≈ {br(w_sim, 6)} × {br(lado_sim['gini'], 6)} "
        f"+ {br(w_nao, 6)} × {br(lado_nao['gini'], 6)} ≈ {br(w_sim * lado_sim['gini'], 6)} + {br(w_nao * lado_nao['gini'], 6)} ≈ {br(ponderado, 6)}"
    )
    r["conta_ganho"] = f"Gini(raiz) − ponderado ≈ {br(g_raiz, 6)} − {br(ponderado, 6)} ≈ {br(ganho, 6)}"
    return r


def melhor_corte_numpy(x: np.ndarray, y: np.ndarray) -> tuple[float, float, int]:
    """Busca exaustiva do melhor corte 'x <= t' por Gini ponderado (vetorizado).
    Devolve (limiar no meio entre valores, ganho, nº de limiares testados)."""
    ordem = np.argsort(x, kind="mergesort")
    xs, ys = x[ordem], y[ordem]
    N = len(y)
    cum1 = np.cumsum(ys)
    n_esq = np.arange(1, N + 1)
    # só cortes onde o valor muda
    validos = np.nonzero(xs[:-1] != xs[1:])[0]
    if len(validos) == 0:
        return float("nan"), 0.0, 0
    ne = n_esq[validos].astype(float)
    c1e = cum1[validos].astype(float)
    nd = N - ne
    c1d = cum1[-1] - c1e
    pe, pd_ = c1e / ne, c1d / nd
    ge, gd = 2 * pe * (1 - pe), 2 * pd_ * (1 - pd_)
    pond = (ne * ge + nd * gd) / N
    p = cum1[-1] / N
    g0 = 2 * p * (1 - p)
    k = int(np.argmin(pond))
    i = validos[k]
    limiar = (xs[i] + xs[i + 1]) / 2
    return float(limiar), float(g0 - pond[k]), int(len(validos))


def nos_da_arvore(arv: DecisionTreeClassifier, colunas: list[str]) -> list[dict]:
    t = arv.tree_
    nos = []
    for i in range(t.node_count):
        n = int(t.n_node_samples[i])
        # sklearn >= 1.4 guarda proporções em tree_.value; volta para contagens
        frac = t.value[i][0] / t.value[i][0].sum()
        cont = np.rint(frac * n).astype(int)
        no = {
            "no": i,
            "n": n,
            "pagou": int(cont[0]),
            "calote": int(cont[1]),
            "taxa_de_calote_pct": 100 * cont[1] / n,
            "gini_sklearn": float(t.impurity[i]),
            "gini_conferido": gini(int(cont[0]), int(cont[1])),
        }
        assert abs(no["gini_sklearn"] - no["gini_conferido"]) < 1e-9, no
        if t.children_left[i] != -1:
            no["pergunta"] = f"{colunas[t.feature[i]]} <= {t.threshold[i]:g}"
            no["coluna"] = colunas[t.feature[i]]
            no["limiar"] = float(t.threshold[i])
            no["filho_sim_<=limiar"] = int(t.children_left[i])
            no["filho_nao_>limiar"] = int(t.children_right[i])
        else:
            no["folha"] = True
            no["preve"] = "calote" if cont[1] > cont[0] else "pagou"
        nos.append(no)
    return nos


def main() -> None:
    # ---------- dados ----------
    bruto = ZIP.read_bytes()
    with zipfile.ZipFile(io.BytesIO(bruto)) as z:
        df = pd.read_excel(io.BytesIO(z.read(XLS)), header=1)
    df = df.rename(columns={"default payment next month": "calote"})
    colunas = [c for c in df.columns if c not in ("ID", "calote")]
    assert len(colunas) == 23
    X = df[colunas].to_numpy()
    y = df["calote"].to_numpy().astype(int)
    N = len(df)
    assert N == 30_000, N  # nº de instâncias declarado no UCI
    assert set(np.unique(y)) == {0, 1}

    n_calote = int(y.sum())
    n_pagou = N - n_calote
    assert (n_pagou, n_calote) == tuple(df["calote"].value_counts().sort_index().tolist())

    R: dict = {}
    R["dataset"] = {
        "nome": "Default of Credit Card Clients (UCI id 350)",
        "arquivo": ZIP.name,
        "sha256_zip": hashlib.sha256(bruto).hexdigest(),
        "linhas": N,
        "atributos": len(colunas),
        "alvo": "calote = 1 se o cliente deu calote no mês seguinte (coluna 'default payment next month'; documentação: default payment Yes = 1, No = 0)",
        "codigos_nao_documentados": {
            "nota": "A documentação do UCI define -1 (em dia) e 1..9 (meses de atraso) para PAY_*, mas os dados também têm -2 e 0, sem definição oficial. A pergunta vencedora (PAY_0 >= 2) usa só códigos documentados do lado 'sim'; -2 e 0 caem todos no lado 'não'.",
            "PAY_0_igual_-2": int((df["PAY_0"] == -2).sum()),
            "PAY_0_igual_0": int((df["PAY_0"] == 0).sum()),
        },
        "versoes": {"scikit-learn": sklearn.__version__, "pandas": pd.__version__, "numpy": np.__version__},
    }
    R["classes"] = {
        "pagou": n_pagou,
        "calote": n_calote,
        "pct_pagou": 100 * n_pagou / N,
        "pct_calote": 100 * n_calote / N,
    }

    # ---------- raiz ----------
    raiz = conta_gini(n_pagou, n_calote)
    g_raiz = raiz["gini"]
    R["gini_raiz"] = raiz
    R["gini_raiz"]["maximo_possivel_2_classes"] = 0.5
    raiz_tela = {d: gini_tela(n_pagou, n_calote, d) for d in (2, 3, 4)}
    R["gini_raiz"]["contas_de_tela"] = {str(d): limpa(t) for d, t in raiz_tela.items()}

    # ---------- perguntas candidatas ----------
    cand = []
    for q in PERGUNTAS:
        m = q["cond"](df).to_numpy()
        r = avaliar_corte(y, m, g_raiz)
        # conferência 1: contagens pelo pandas (crosstab), caminho independente
        ct = pd.crosstab(m, y)
        assert int(ct.loc[True, 1]) == r["sim"]["calote"] and int(ct.loc[True, 0]) == r["sim"]["pagou"]
        assert int(ct.loc[False, 1]) == r["nao"]["calote"] and int(ct.loc[False, 0]) == r["nao"]["pagou"]
        # conferência 2: o scikit-learn com só essa pergunta (toco de profundidade 1)
        toco = DecisionTreeClassifier(criterion="gini", max_depth=1, random_state=0)
        toco.fit(m.reshape(-1, 1).astype(int), y)
        t = toco.tree_
        l, rr = t.children_left[0], t.children_right[0]
        pond_sk = (t.n_node_samples[l] * t.impurity[l] + t.n_node_samples[rr] * t.impurity[rr]) / N
        assert abs(pond_sk - r["gini_ponderado"]) < 1e-9, (q["id"], pond_sk, r["gini_ponderado"])
        telas = {str(d): corte_tela(r, raiz_tela[d]["_g"], d) for d in (2, 3, 4)}
        r["contas_de_tela"] = telas
        r["casas_que_fecham_na_tela"] = [int(d) for d, t in telas.items() if t["fecha"] and raiz_tela[int(d)]["fecha"]]
        cand.append({k: v for k, v in q.items() if k != "cond"} | r | {"conferido_sklearn": True})

    cand.sort(key=lambda c: c["ganho"], reverse=True)
    for i, c in enumerate(cand, 1):
        c["posicao"] = i
    R["perguntas_candidatas"] = cand
    v, s = cand[0], cand[1]
    outra = next(c for c in cand[1:] if c["coluna"] != v["coluna"])
    R["vencedora"] = {
        "id": v["id"],
        "pergunta": v["pergunta"],
        "regra": v["regra"],
        "ganho": v["ganho"],
        "segunda": s["id"],
        "ganho_segunda": s["ganho"],
        "diferenca_para_segunda": v["ganho"] - s["ganho"],
        "vezes_a_segunda": v["ganho"] / s["ganho"],
        "melhor_de_outra_coluna": outra["id"],
        "ganho_melhor_de_outra_coluna": outra["ganho"],
        "vezes_a_melhor_de_outra_coluna": v["ganho"] / outra["ganho"],
        "pior": cand[-1]["id"],
        "ganho_pior": cand[-1]["ganho"],
        "vezes_a_pior": v["ganho"] / cand[-1]["ganho"],
        "gini_cai_de_para": [g_raiz, v["gini_ponderado"]],
        "pct_da_impureza_da_raiz_removida": v["ganho_pct_da_raiz"],
    }

    # ---------- versão para a tela: números que fecham entre si ----------
    t2 = v["contas_de_tela"]["2"]
    assert raiz_tela[2]["fecha"] and t2["fecha"], "a conta de 2 casas deixou de fechar: revise para_tela"
    R["para_tela"] = {
        "regra": (
            "Conta passo a passo com 2 casas (ela fecha: cada passo é conta dos números mostrados e o final bate "
            "com o valor verdadeiro arredondado). Para comparar perguntas, mostre o Gini ponderado (o menor vence) "
            "com 2 ou 4 casas, ou a bagunça removida em %; não mostre o ganho das outras perguntas com 2 casas "
            "(0,34 − 0,30 daria 0,04, mas o ganho real da 2ª pergunta arredonda para 0,05). "
            "Não mostre o Gini da raiz com 3 casas junto com 2 casas: 0,34454 vira 0,345 com 3 casas, "
            "que parece arredondar para 0,35, mas com 2 casas o certo é 0,34."
        ),
        "raiz_2_casas": raiz_tela[2]["conta"],
        "vencedora_2_casas": {k: t2[k] for k in ("gini_sim", "gini_nao", "ponderado", "ganho")},
        "raiz_4_casas": float(_q(g_raiz, 4)),
        "ranking": [
            {
                "pergunta": c["pergunta"],
                "regra": c["regra"],
                "calote_sim_pct_1_casa": float(_q(c["sim"]["taxa_de_calote_pct"], 1)),
                "calote_nao_pct_1_casa": float(_q(c["nao"]["taxa_de_calote_pct"], 1)),
                "gini_ponderado_2_casas": float(_q(c["gini_ponderado"], 2)),
                "gini_ponderado_4_casas": float(_q(c["gini_ponderado"], 4)),
                "ganho_4_casas": float(_q(c["ganho"], 4)),
                "bagunca_removida_pct_1_casa": float(_q(c["ganho_pct_da_raiz"], 1)),
            }
            for c in cand
        ],
        "em_palavras": {
            "raiz": f"{n_calote} de {N} deram calote: {br(100 * n_calote / N, 2)}%, mais de 1 em cada 5",
            "vencedora_sim": f"{v['sim']['calote']} de {v['sim']['n']} deram calote: {br(v['sim']['taxa_de_calote_pct'], 1)}%, cerca de 7 em cada 10",
            "vencedora_nao": f"{v['nao']['calote']} de {v['nao']['n']} deram calote: {br(v['nao']['taxa_de_calote_pct'], 1)}%, cerca de 1 em cada 6",
        },
    }
    assert round(v["sim"]["taxa_de_calote_pct"] / 10) == 7 and round(100 / v["nao"]["taxa_de_calote_pct"]) == 6
    assert 20 < 100 * n_calote / N < 25

    # ---------- todos os cortes possíveis na raiz (o que o algoritmo realmente faz) ----------
    por_coluna = []
    total_testados = 0
    for j, c in enumerate(colunas):
        lim, ganho, nt = melhor_corte_numpy(X[:, j].astype(float), y)
        total_testados += nt
        por_coluna.append({"coluna": c, "nome": NOMES[c], "melhor_limiar": lim, "ganho": ganho, "limiares_testados": nt})
    por_coluna.sort(key=lambda d: d["ganho"], reverse=True)
    R["busca_exaustiva_raiz"] = {
        "explicacao": "Para cada uma das 23 colunas, testa todo corte 'coluna <= limiar' entre dois valores vizinhos e guarda o de menor Gini ponderado.",
        "total_de_perguntas_testadas": total_testados,
        "melhor_por_coluna": por_coluna,
    }

    # varredura dos limiares da coluna vencedora (para animar "testa um limiar de cada vez")
    vals = np.sort(df["PAY_0"].unique())
    varredura = []
    for a, b in zip(vals[:-1], vals[1:]):
        r = avaliar_corte(y, (df["PAY_0"] > a).to_numpy(), g_raiz)
        varredura.append({
            "pergunta": f"PAY_0 >= {b}",
            "limiar_sklearn": f"PAY_0 <= {(a + b) / 2:g}",
            "n_sim": r["sim"]["n"],
            "taxa_calote_sim_pct": r["sim"]["taxa_de_calote_pct"],
            "taxa_calote_nao_pct": r["nao"]["taxa_de_calote_pct"],
            "gini_ponderado": r["gini_ponderado"],
            "ganho": r["ganho"],
        })
    R["varredura_PAY_0"] = varredura

    # ---------- árvore de profundidade 2 do scikit-learn (todos os dados) ----------
    arv2 = DecisionTreeClassifier(criterion="gini", max_depth=2, random_state=0).fit(X, y)
    nos2 = nos_da_arvore(arv2, colunas)
    raiz_sk = nos2[0]
    filho_e, filho_d = nos2[raiz_sk["filho_sim_<=limiar"]], nos2[raiz_sk["filho_nao_>limiar"]]
    # A pergunta vencedora "PAY_0 >= 2" é o lado ">" de "PAY_0 <= 1,5"
    bate = (
        raiz_sk["coluna"] == "PAY_0"
        and abs(raiz_sk["limiar"] - 1.5) < 1e-9
        and v["id"] == "atraso_2_meses"
        and filho_d["calote"] == v["sim"]["calote"]
        and filho_d["pagou"] == v["sim"]["pagou"]
        and filho_e["calote"] == v["nao"]["calote"]
    )
    melhor_exaustivo = por_coluna[0]
    R["arvore_profundidade_2_sklearn"] = {
        "parametros": "DecisionTreeClassifier(criterion='gini', max_depth=2, random_state=0), 30 000 linhas",
        "texto": export_text(arv2, feature_names=colunas, show_weights=True),
        "nos": nos2,
        "raiz_bate_com_a_conta": bool(bate),
        "explicacao": (
            f"A raiz do scikit-learn é {raiz_sk['pergunta']}. NÃO bate com a conta à mão: confira limiar e coluna."
        ) if not bate else (
            "A raiz do scikit-learn é PAY_0 <= 1,5, que com valores inteiros é a mesma pergunta "
            "'atraso de 2 meses ou mais?' (o lado 'não' do sklearn é o 'sim' da nossa pergunta). "
            "As contagens e o Gini de cada lado são idênticos aos da conta à mão, e a busca exaustiva "
            f"em numpy chega ao mesmo corte ({melhor_exaustivo['coluna']} <= {melhor_exaustivo['melhor_limiar']:g})."
        ),
        "ganho_raiz_sklearn": float(raiz_sk["gini_sklearn"] - (filho_e["n"] * filho_e["gini_sklearn"] + filho_d["n"] * filho_d["gini_sklearn"]) / N),
    }
    assert melhor_exaustivo["coluna"] == raiz_sk["coluna"] and abs(melhor_exaustivo["melhor_limiar"] - raiz_sk["limiar"]) < 1e-9
    assert abs(R["arvore_profundidade_2_sklearn"]["ganho_raiz_sklearn"] - melhor_exaustivo["ganho"]) < 1e-9
    assert abs(melhor_exaustivo["ganho"] - v["ganho"]) < 1e-9 if bate else True
    folhas2 = [n for n in nos2 if n.get("folha")]
    R["arvore_profundidade_2_sklearn"]["leitura"] = {
        "PAY_2 <= 1.5": "lado de quem NÃO está 2+ meses atrasado em setembro: a próxima pergunta é 'estava 2+ meses atrasado em agosto?'",
        "PAY_3 <= -0.5": "lado de quem está 2+ meses atrasado em setembro: a próxima pergunta é 'julho estava em dia?' (-1 = em dia; -2 não tem definição oficial)",
        "so_uma_folha_preve_calote": sum(1 for n in folhas2 if n["preve"] == "calote") == 1,
    }
    R["arvore_profundidade_2_sklearn"]["acuracia_nos_30000"] = float(arv2.score(X, y))

    # ---------- limite: overfitting (treino x teste) ----------
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.3, random_state=SEMENTE, stratify=y)
    chute = max(np.mean(yte == 0), np.mean(yte == 1))  # "diz que todo mundo paga"

    def avalia(prof):
        a = DecisionTreeClassifier(criterion="gini", max_depth=prof, random_state=SEMENTE).fit(Xtr, ytr)
        pred = a.predict(Xte)
        return {
            "profundidade_max": prof if prof is not None else "sem limite",
            "profundidade_real": int(a.get_depth()),
            "folhas": int(a.get_n_leaves()),
            "acuracia_treino_pct": 100 * a.score(Xtr, ytr),
            "acuracia_teste_pct": 100 * a.score(Xte, yte),
            "calotes_do_teste_detectados_pct": 100 * float(((pred == 1) & (yte == 1)).sum() / (yte == 1).sum()),
            "alarmes_certos_pct": 100 * float(((pred == 1) & (yte == 1)).sum() / max((pred == 1).sum(), 1)),
            "clientes_de_treino_por_folha": len(ytr) / a.get_n_leaves(),
        }

    p2, plivre = avalia(2), avalia(None)
    curva = [avalia(p) for p in list(range(1, 21))] + [plivre]

    # profundidade escolhida do jeito certo: validação cruzada só no treino
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEMENTE)
    cv_res = []
    for p in range(1, 16):
        sc = cross_val_score(DecisionTreeClassifier(criterion="gini", max_depth=p, random_state=SEMENTE), Xtr, ytr, cv=cv)
        cv_res.append({"profundidade": p, "acuracia_cv_pct": 100 * sc.mean()})
    melhor_cv = max(cv_res, key=lambda d: d["acuracia_cv_pct"])

    # robustez: 10 sementes de divisão treino/teste
    sementes = []
    for sd in range(10):
        a_tr, a_te, b_tr, b_te = train_test_split(X, y, test_size=0.3, random_state=sd, stratify=y)
        r2 = DecisionTreeClassifier(criterion="gini", max_depth=2, random_state=sd).fit(a_tr, b_tr)
        rl = DecisionTreeClassifier(criterion="gini", max_depth=None, random_state=sd).fit(a_tr, b_tr)
        sementes.append({
            "semente": sd,
            "prof2_treino": 100 * r2.score(a_tr, b_tr), "prof2_teste": 100 * r2.score(a_te, b_te),
            "livre_treino": 100 * rl.score(a_tr, b_tr), "livre_teste": 100 * rl.score(a_te, b_te),
            "livre_folhas": int(rl.get_n_leaves()),
            "chute_teste": 100 * max(np.mean(b_te == 0), np.mean(b_te == 1)),
        })
    sm = pd.DataFrame(sementes)

    R["overfitting"] = {
        "divisao": f"train_test_split(test_size=0.3, stratify=y, random_state={SEMENTE}): {len(ytr)} treino, {len(yte)} teste",
        "chute_todo_mundo_paga_teste_pct": 100 * chute,
        "profundidade_2": p2,
        "sem_limite": plivre,
        "sem_limite_perde_do_chute_por_pontos": 100 * chute - plivre["acuracia_teste_pct"],
        "queda_treino_para_teste_sem_limite_pontos": plivre["acuracia_treino_pct"] - plivre["acuracia_teste_pct"],
        "curva_por_profundidade": curva,
        "validacao_cruzada_5_dobras_no_treino": cv_res,
        "melhor_profundidade_cv": melhor_cv,
        "teste_na_profundidade_cv": avalia(melhor_cv["profundidade"]),
        "duplicatas_de_atributos_no_dataset": int(df[colunas].duplicated().sum()),
        "sementes_0_a_9": {
            "linhas": sementes,
            "media": sm.drop(columns="semente").mean().to_dict(),
            "min": sm.drop(columns="semente").min().to_dict(),
            "max": sm.drop(columns="semente").max().to_dict(),
            "sem_limite_abaixo_do_chute_em_todas": bool((sm["livre_teste"] < sm["chute_teste"]).all()),
        },
    }

    SAIDA.write_text(json.dumps(R, ensure_ascii=False, indent=2, default=float) + "\n", encoding="utf-8")

    # ---------- impressão ----------
    print(f"Dataset: {R['dataset']['nome']} — {N} clientes, {len(colunas)} atributos")
    print(f"Pagou: {n_pagou} ({br(R['classes']['pct_pagou'], 2)}%)  Calote: {n_calote} ({br(R['classes']['pct_calote'], 2)}%)")
    print(f"\nGini da raiz: {raiz['conta']}")
    print("\nPerguntas candidatas (ordenadas pelo ganho):")
    for c in cand:
        print(f"\n{c['posicao']}. {c['pergunta']}  [{c['regra']}]")
        for lado in ("sim", "nao"):
            L = c[lado]
            print(f"   {lado:>3}: {L['n']:>6} clientes = {L['pagou']:>6} pagou + {L['calote']:>5} calote "
                  f"-> calote {br(L['taxa_de_calote_pct'], 1)}% | Gini {br(L['gini'])}")
        print(f"   ponderado: {c['conta_ponderado']}")
        print(f"   ganho: {c['conta_ganho']}  ({br(c['ganho_pct_da_raiz'], 1)}% da impureza da raiz)")
    vv = R["vencedora"]
    print(f"\nVence: {vv['pergunta']} ganho {br(vv['ganho'])}; {br(vv['vezes_a_segunda'], 2)}x a 2ª ({vv['segunda']}), "
          f"{br(vv['vezes_a_pior'], 0)}x a pior ({vv['pior']})")
    print(f"   melhor pergunta de outra coluna: {vv['melhor_de_outra_coluna']} -> vencedora tem {br(vv['vezes_a_melhor_de_outra_coluna'], 1)}x o ganho")
    print("\nContas de tela que fecham (casas):", {c["id"]: c["casas_que_fecham_na_tela"] for c in cand},
          "| raiz:", [d for d, t in raiz_tela.items() if t["fecha"]])
    for d in (2, 3, 4):
        print(f"   raiz {d} casas: {raiz_tela[d]['conta']}  fecha={raiz_tela[d]['fecha']}")
        t = v["contas_de_tela"][str(d)]
        print(f"   vencedora {d} casas: sim {t['gini_sim']} | não {t['gini_nao']} | {t['ponderado']} | ganho {t['ganho']}  fecha={t['fecha']}")
    print(f"\nBusca exaustiva: {total_testados} perguntas testadas na raiz. Top 5:")
    for d in por_coluna[:5]:
        print(f"   {d['coluna']:>9} <= {d['melhor_limiar']:<10g} ganho {br(d['ganho'])}")
    print("\nVarredura de limiares em PAY_0:")
    for d in varredura:
        print(f"   {d['pergunta']:>12}: sim={d['n_sim']:>6} calote sim {br(d['taxa_calote_sim_pct'], 1):>5}% | ganho {br(d['ganho'])}")
    print("\nÁrvore de profundidade 2 (scikit-learn, todos os dados):")
    print(R["arvore_profundidade_2_sklearn"]["texto"])
    print(f"Raiz bate com a conta: {bate}")
    for n in folhas2:
        print(f"   folha {n['no']}: {n['n']} clientes, calote {br(n['taxa_de_calote_pct'], 1)}% -> {n['preve']}")
    o = R["overfitting"]
    print(f"\nOverfitting ({o['divisao']}):")
    print(f"   chute 'todo mundo paga' no teste: {br(o['chute_todo_mundo_paga_teste_pct'], 2)}%")
    for nome, a in (("profundidade 2", p2), ("sem limite", plivre)):
        print(f"   {nome}: treino {br(a['acuracia_treino_pct'], 2)}% | teste {br(a['acuracia_teste_pct'], 2)}% | "
              f"{a['folhas']} folhas, profundidade {a['profundidade_real']}, {br(a['clientes_de_treino_por_folha'], 1)} clientes/folha | "
              f"pega {br(a['calotes_do_teste_detectados_pct'], 1)}% dos calotes")
    print("   curva (profundidade: folhas, treino%, teste%):",
          "; ".join(f"{c['profundidade_max']}: {c['folhas']}, {c['acuracia_treino_pct']:.1f}, {c['acuracia_teste_pct']:.1f}" for c in curva))
    print(f"   quando diz 'calote', acerta: prof2 {br(p2['alarmes_certos_pct'], 1)}% | sem limite {br(plivre['alarmes_certos_pct'], 1)}%")
    print(f"   melhor profundidade (validação cruzada no treino): {melhor_cv['profundidade']} "
          f"-> teste {br(o['teste_na_profundidade_cv']['acuracia_teste_pct'], 2)}%")
    print("   10 sementes (média): prof2 teste {:.2f}% | sem limite treino {:.2f}% teste {:.2f}% | chute {:.2f}% | sem limite < chute em todas: {}".format(
        o["sementes_0_a_9"]["media"]["prof2_teste"], o["sementes_0_a_9"]["media"]["livre_treino"],
        o["sementes_0_a_9"]["media"]["livre_teste"], o["sementes_0_a_9"]["media"]["chute_teste"],
        o["sementes_0_a_9"]["sem_limite_abaixo_do_chute_em_todas"]))
    print(f"\nOK salvo {SAIDA}")


if __name__ == "__main__":
    main()
