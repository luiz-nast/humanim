"""Como o texto do roteiro é falado: números por extenso, sílabas, pausas da pontuação e o ritmo da fala.

O editar usa estas regras para comparar o falado com o roteiro e decidir a pausa que fica; o roteiro e as
cenas (CenaHumanim.momento, via fracao_na_fala), para estimar quando cada palavra é dita. Mudar este
arquivo muda o tempo das animações: por isso ele entra na assinatura das cenas (animar.assinatura).
"""
import re
import unicodedata

# Antes da gravação, a duração de cada fala é estimada pelas sílabas, com os números por extenso
# ("0,78" são 11 sílabas, não 2 palavras), mais as pausas que o editar deixa na pontuação (PAUSA).
SILABAS_POR_SEGUNDO = 5.5
PAUSA = {"frase": 0.30, "virgula": 0.20, "palavra": 0.12}  # pausa que fica depois da palavra, pela pontuação
_NUMERO = re.compile(r"\d+(?:[.,]\d+)*%?")
_DITO = re.compile(_NUMERO.pattern + r"(?!\w)|\w+")


def pontuacao(depois):
    """'frase', 'virgula' ou '' pelo que vem depois da palavra no texto (até a próxima)."""
    return "frase" if re.search(r"[.?!:…]", depois) else "virgula" if re.search(r"[,;—–]| - ", depois) else ""


# ---------------------------------------------------------------- números por extenso

UNIDADES = ("zero um dois três quatro cinco seis sete oito nove dez onze doze treze quatorze quinze dezesseis "
            "dezessete dezoito dezenove").split()
DEZENAS = "_ _ vinte trinta quarenta cinquenta sessenta setenta oitenta noventa".split()
CENTENAS = "_ cento duzentos trezentos quatrocentos quinhentos seiscentos setecentos oitocentos novecentos".split()


def extenso(n):
    """Número inteiro por extenso, em palavras: 2005 -> dois mil e cinco."""
    if n < 20:
        return [UNIDADES[n]]
    if n < 100:
        d, u = divmod(n, 10)
        return [DEZENAS[d]] + (["e", UNIDADES[u]] if u else [])
    if n < 1000:
        if n == 100:
            return ["cem"]
        c, r = divmod(n, 100)
        return [CENTENAS[c]] + (["e"] + extenso(r) if r else [])
    for base, um, varios in ((10 ** 9, "bilhão", "bilhões"), (10 ** 6, "milhão", "milhões"), (1000, "mil", "mil")):
        if n >= base:
            q, r = divmod(n, base)
            if q >= 1000:
                return list(str(n))
            antes = ([] if q == 1 and base == 1000 else extenso(q)) + [um if q == 1 else varios]
            return antes + (((["e"] if r < 100 or r % 100 == 0 else []) + extenso(r)) if r else [])
    return list(str(n))


def numero(texto):
    """'30', '30.000', '2,5', '1.234,5', '20%' em palavras. Centavos zerados ('1.500,00') não se falam."""
    pct = texto.endswith("%")
    t = texto.rstrip("%").strip()
    if re.fullmatch(r"\d{1,3}(\.\d{3})+(,\d+)?", t):  # ponto de milhar (e vírgula decimal)
        t = t.replace(".", "")
    inteiro, _, decimal = t.replace(".", ",").partition(",")
    if decimal and not decimal.strip("0"):
        decimal = ""
    palavras = extenso(int(inteiro)) if len(inteiro) < 13 else list(inteiro)
    if decimal.isdigit():
        palavras += ["vírgula"] + (extenso(int(decimal)) if not decimal.startswith("0") else
                                   [UNIDADES[int(c)] for c in decimal])
    return palavras + (["por", "cento"] if pct else [])


# ---------------------------------------------------------------- ritmo

# Sigla soletrada: sílabas do nome de cada letra ("efe", "eme", "dáblio"); as outras letras dão 1.
_LETRA = {"F": 2, "H": 2, "J": 2, "L": 2, "M": 2, "N": 2, "R": 2, "S": 2, "W": 3, "Y": 3}


def silabas(palavra):
    """Sílabas de uma palavra, contando os grupos de vogais (aproximado: "saída" dá 2).
    Sigla em maiúsculas sem vogal ou de 2 letras se soletra: "GPT" dá 3 (gê-pê-tê), "IA" dá 2, "LLM" dá 6."""
    if palavra.isalpha() and palavra.isupper() and (len(palavra) == 2 or not re.search(r"[AEIOUY]", palavra)):
        return sum(_LETRA.get(c, 1) for c in palavra)
    p = unicodedata.normalize("NFD", palavra.lower())
    p = "".join(c for c in p if unicodedata.category(c) != "Mn")
    return max(1, len(re.findall(r"[aeiouy]+", p)))


def ritmo(fala):
    """Estimativa de quando cada palavra da fala começa: (inícios, total), em segundos.

    `inícios` tem um valor por palavra de re.findall(r"\\w+", fala), a mesma divisão que
    CenaHumanim.momento usa; `total` é a duração estimada da fala (sem a pausa depois da última palavra).
    """
    achados = list(_DITO.finditer(fala))
    pesos = []  # (sílabas de cada palavra \w+ deste trecho, pausa depois dele)
    for i, m in enumerate(achados):
        bruto, partes = m.group(), re.findall(r"\w+", m.group())
        if _NUMERO.fullmatch(bruto):
            total = sum(silabas(p) for p in numero(bruto))
            inteiro = sum(silabas(p) for p in numero(bruto.split(",")[0].rstrip("%")))
            if "," in bruto:  # "zero vírgula" | "setenta e oito": a vírgula vai com a parte inteira
                inteiro += silabas("vírgula")
            cada = [min(inteiro, total)] + [0] * (len(partes) - 1)
            cada[-1] += total - cada[0]
        else:
            cada = [silabas(p) for p in partes]
        depois = fala[m.end():achados[i + 1].start() if i + 1 < len(achados) else len(fala)]
        pausa = PAUSA.get(pontuacao(depois), 0.0) if i + 1 < len(achados) else 0.0
        pesos.append((cada, pausa))
    inicios, t = [], 0.0
    for cada, pausa in pesos:
        for s in cada:
            inicios.append(t)
            t += s / SILABAS_POR_SEGUNDO
        t += pausa
    if len(inicios) != len(re.findall(r"\w+", fala)):  # divisão diferente da do momento: volta ao uniforme
        n = len(re.findall(r"\w+", fala))
        inicios = [t * k / max(n, 1) for k in range(n)]
    return inicios, t


def fracao_na_fala(fala, busca, vez=1):
    """Em que fração da fala (0 a 1) ela chega em `busca` (uma ou mais palavras), pelo ritmo; None se não chega.
    É o que CenaHumanim.momento e o humanim contar usam."""
    todas = re.findall(r"\w+", fala.lower())
    alvo = re.findall(r"\w+", busca.lower())
    achou = [i for i in range(len(todas)) if alvo and todas[i:i + len(alvo)] == alvo]
    if len(achou) < vez:
        return None
    inicios, total = ritmo(fala)
    return inicios[achou[vez - 1]] / total if total > 0 else achou[vez - 1] / len(todas)
