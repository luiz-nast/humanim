"""Todo número do roteiro.md, tirado de resultados.json e conferir_teoria.json, com conferência.

Não recalcula nada a partir do dataset: só lê os dois JSON que os outros scripts gravaram,
faz as contas derivadas que o roteiro usa (porcentagens inteiras, arredondamentos de tela,
contagem de cortes por tipo de coluna) e para com erro se alguma frase do roteiro deixar de
valer. Rodar da raiz (menos de 1 s):

    .venv/bin/python videos/arvore-de-decisao/dados/numeros_roteiro.py

Grava dados/numeros_roteiro.json.
"""
import json
from pathlib import Path

AQUI = Path(__file__).resolve().parent
R = json.loads((AQUI / "resultados.json").read_text(encoding="utf-8"))
T = json.loads((AQUI / "conferir_teoria.json").read_text(encoding="utf-8"))


def gini(n, c):
    p = c / n
    return 1 - (p * p + (1 - p) * (1 - p))


def confere(cond, msg):
    if not cond:
        raise SystemExit(f"ERRO: {msg}")


out = {}

# Linha 2: a base
n, cal = R["gini_raiz"]["n"], R["gini_raiz"]["calote"]
pct = 100 * cal / n
confere(n == 30000 and round(pct) == 22, "base: 30 mil clientes e 22% de calote")
out["base"] = {"fala": "30 mil clientes; 22% deram calote no mês seguinte", "n": n, "calote": cal,
               "pct_calote": round(pct, 2),
               "nuvem_300_pontos": {"verdes": 300 - round(300 * cal / n), "vermelhos": round(300 * cal / n)}}

# Linhas 4 a 7: a régua na raiz (contas de 2 casas do para_tela)
g_raiz = R["gini_raiz"]["gini"]
confere(R["gini_raiz"]["contas_de_tela"]["2"]["fecha"], "a conta da raiz com 2 casas tem de fechar")
confere(abs(T["A_interpretacao_gini"]["prob_dois_clientes_sorteados_de_classes_diferentes_200mil_pares"] - g_raiz) < 0.005,
        "dois clientes sorteados diferentes deve bater com o Gini")
out["raiz"] = {"fala": "iguais 0,78 x 0,78 + 0,22 x 0,22 = 0,66; diferentes 0,34",
               "tela": R["para_tela"]["raiz_2_casas"], "gini": round(g_raiz, 4),
               "dois_clientes_diferentes_simulado": T["A_interpretacao_gini"][
                   "prob_dois_clientes_sorteados_de_classes_diferentes_200mil_pares"],
               "maximo_2_classes": 0.5}

# Linhas 8 a 12: a pergunta vencedora
v = R["perguntas_candidatas"][0]
confere(v["regra"] == "PAY_0 >= 2", "a primeira candidata deve ser a vencedora PAY_0 >= 2")
s, nn = v["sim"], v["nao"]
p_sim, p_nao = s["calote"] / s["n"], nn["calote"] / nn["n"]
confere(0.65 < p_sim < 0.70, "'quase 7 em 10' no lado sim")
confere(round(1 / p_nao) == 6, "'1 em 6' no lado não")
confere(s["gini"] > g_raiz > nn["gini"], "o lado sim sobe acima da raiz e o lado não cai abaixo")
confere(abs((1 - p_sim) - 0.30) < 0.01, "'70 a 30' no lado sim")
peso_sim = s["n"] / n
confere(round(100 * peso_sim) == 10, "'os atrasados são só 10%'")
media_simples = (s["gini"] + nn["gini"]) / 2
confere(media_simples > g_raiz, "a média sem peso tem de parecer pior que o começo")
pct_tirado = v["ganho_pct_da_raiz"]
pct_tirado_tela = 100 * 0.05 / 0.34
confere(round(pct_tirado) == round(pct_tirado_tela) == 15,
        "'tirou 15%': tem de fechar com o valor exato e com os números de 2 casas da tela")
out["vencedora"] = {
    "fala": "quase 7 em 10 / 1 em 6 / só 10% / dá 0,29 / tirou 15%",
    "sim": {"n": s["n"], "pct_calote": round(100 * p_sim, 1), "gini": round(s["gini"], 4),
            "nuvem_31_pontos": {"vermelhos": 22, "verdes": 9}},
    "nao": {"n": nn["n"], "pct_calote": round(100 * p_nao, 1), "gini": round(nn["gini"], 4),
            "nuvem_269_pontos": {"vermelhos": 44, "verdes": 225}},
    "tela": R["para_tela"]["vencedora_2_casas"],
    "peso_sim": round(peso_sim, 4), "media_sem_peso": round(media_simples, 4),
    "media_sem_peso_tela": "(0,42 + 0,28) ÷ 2 = 0,35",
    "ponderado": round(v["gini_ponderado"], 4), "pct_da_bagunca_tirada": round(pct_tirado, 1),
    "pct_tela": "0,05 ÷ 0,34 ≈ 15%",
}
confere(round(out["base"]["nuvem_300_pontos"]["vermelhos"]) == 22 + 44, "a nuvem de 300 pontos tem de somar")

# Linha 13: a busca exaustiva
b = R["busca_exaustiva_raiz"]
total = b["total_de_perguntas_testadas"]
por_col = {c["coluna"]: c for c in b["melhor_por_coluna"]}
confere(len(por_col) == 23 and sum(c["limiares_testados"] for c in por_col.values()) == total,
        "as 23 colunas somam os cortes testados")
atraso = sum(por_col[c]["limiares_testados"] for c in ["PAY_0", "PAY_2", "PAY_3", "PAY_4", "PAY_5", "PAY_6"])
dinheiro = sum(c["limiares_testados"] for k, c in por_col.items()
               if k.startswith(("PAY_AMT", "BILL_AMT")) or k == "LIMIT_BAL")
confere(170000 < total < 175000, "'quase 175 mil'")
out["busca"] = {"fala": "quase 175 mil cortes, em toda coluna", "total": total, "colunas": 23,
                "cortes_atraso_6_colunas": atraso, "cortes_valores_em_NT$_13_colunas": dinheiro,
                "cortes_resto": total - atraso - dinheiro}

# Linha 14: idade e estado civil, no melhor corte de cada um
pct_col = {k: 100 * c["ganho"] / g_raiz for k, c in por_col.items()}
for col in ["AGE", "MARRIAGE"]:
    confere(pct_col[col] < 1, f"'nem 1%': o melhor corte de {col} tem de tirar menos de 1% da bagunça")
casado = next(p for p in R["perguntas_candidatas"] if p["id"] == "casado")
confere(100 * casado["ganho"] / g_raiz < 1, "'casado?' (MARRIAGE == 1) também tira menos de 1%")
out["senso_comum"] = {
    "fala": "idade e estado civil: em nenhum corte tiram nem 1%",
    "idade": {"melhor_corte": f'AGE <= {por_col["AGE"]["melhor_limiar"]}', "pct_tirado": round(pct_col["AGE"], 2),
              "tela": "0,2%", "gini_ponderado_2_casas": round(g_raiz - por_col["AGE"]["ganho"], 2)},
    "estado_civil": {"melhor_corte": f'MARRIAGE <= {por_col["MARRIAGE"]["melhor_limiar"]}',
                     "pct_tirado": round(pct_col["MARRIAGE"], 2), "tela": "0,1%",
                     "gini_ponderado_2_casas": round(g_raiz - por_col["MARRIAGE"]["ganho"], 2)},
    "casado_igual_1_pct_tirado": round(100 * casado["ganho"] / g_raiz, 2),
    "melhor_por_coluna_pct_tirado": {k: round(x, 2) for k, x in sorted(pct_col.items(), key=lambda kv: -kv[1])},
}
confere(round(pct_col["AGE"], 1) == 0.2 and round(pct_col["MARRIAGE"], 1) == 0.1, "rótulos 0,2% e 0,1%")

# Linha 15: o corte importa (1 mês contra 2 meses, mesma coluna)
var = {x["limiar_sklearn"]: x for x in R["varredura_PAY_0"]}
um, dois = var["PAY_0 <= 0.5"], var["PAY_0 <= 1.5"]
cal_um = round(um["n_sim"] * um["taxa_calote_sim_pct"] / 100)
g_um_sim = gini(um["n_sim"], cal_um)
confere(round(um["taxa_calote_sim_pct"]) == 50 and round(g_um_sim, 2) == 0.50, "'meio a meio' no lado sim de 1 mês")
confere(round(dois["gini_ponderado"], 2) == 0.29 and round(um["gini_ponderado"], 2) == 0.30, "0,29 contra 0,30")
confere(dois["gini_ponderado"] < um["gini_ponderado"], "dois meses vence um mês")
out["corte"] = {"fala": "cortar em um mês perde: os atrasados ficam meio a meio",
                "um_mes": {"n_sim": um["n_sim"], "pct_calote_sim": round(um["taxa_calote_sim_pct"], 1),
                           "gini_sim": round(g_um_sim, 4), "gini_ponderado": round(um["gini_ponderado"], 4)},
                "dois_meses": {"gini_ponderado": round(dois["gini_ponderado"], 4)}}

# Linhas 16 e 17: guloso não garante a melhor árvore (conferir_teoria.json, bloco F, 11 colunas)
F = T["F_guloso_vs_otimo_prof2"]
g_arv, o_arv = F["guloso"]["arvore"], F["otimo_por_gini_nas_folhas"]["arvore"]
confere(g_arv == ["PAY_0 <= 1.5", "PAY_2 <= 1.5", "PAY_3 <= -0.5"], "árvore gulosa: raiz 2+ meses, agosto 2+, julho")
confere(o_arv == ["PAY_0 <= 0.5", "PAY_3 <= 1.0", "PAY_0 <= 1.5"], "a outra árvore começa por 1+ mês")
gg, go = F["guloso"]["gini_nas_folhas"], F["otimo_por_gini_nas_folhas"]["gini_nas_folhas"]
confere(go < gg and gg - go < 0.001, "'um tiquinho menos bagunça'")
arv_sk = R["arvore_profundidade_2_sklearn"]["nos"]
confere([arv_sk[0]["pergunta"], arv_sk[1]["pergunta"], arv_sk[4]["pergunta"]] == g_arv,
        "a gulosa de 11 colunas é a mesma árvore do scikit-learn com as 23")
out["gulosa"] = {
    "fala": "começar por um mês dava um tiquinho menos bagunça",
    "gulosa": {"raiz": "2+ meses? (PAY_0 <= 1.5)", "lado_nao": "agosto 2+? (PAY_2 <= 1.5)",
               "lado_sim": "julho? (PAY_3 <= -0.5; não descrever os códigos -2 e 0)",
               "gini_nas_folhas": round(gg, 4), "acuracia_pct": round(F["guloso"]["acuracia_pct"], 2)},
    "comeca_por_1_mes": {"raiz": "1+ mês? (PAY_0 <= 0.5)", "lado_nao": "julho 2+? (PAY_3 <= 1.0)",
                         "lado_sim": "2+ meses? (PAY_0 <= 1.5)", "gini_nas_folhas": round(go, 4)},
    "ressalvas": ["menos bagunça nas folhas, não mais acerto: a de maior acerto (82,06%) tem a mesma raiz da gulosa",
                  "busca em 11 colunas (as 6 de atraso, sexo, escolaridade, estado civil, idade, limite)",
                  "diferença de 0,0002: dizer 'um tiquinho'"],
}

destino = AQUI / "numeros_roteiro.json"
destino.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print(f"OK {destino.relative_to(AQUI.parents[2])}: todas as frases do roteiro conferem")
