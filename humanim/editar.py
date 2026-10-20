"""humanim editar: tira da fala o que não é roteiro, para a voz sair corrida e sem defeito.

Roda depois do gravar e antes do animar. Transcreve a gravação no computador (faster-whisper, com o
tempo de cada palavra), alinha o que foi dito em cada linha com a fala do roteiro e decide o que fica:
corta silêncio e respiração longos (deixa uma pausa curta), muleta fora do roteiro (é, hã, hum...),
repetição, gagueira e começo errado (fica a última tentativa inteira). Cada corte cai no instante mais
quieto perto dele, para não comer sílaba, e na fronteira de um quadro do vídeo.

Escreve edicao.json: por linha, os trechos [de, ate] da gravação que ficam, o que foi cortado e o que
o falado tem de diferente do roteiro. Daí em diante animar, previa, montar e frames usam esses trechos
(roteiro.ler_tempos). Os trechos dá para ajustar à mão.
"""
import bisect
import difflib
import json
import math
import os
import re
import subprocess
import time
import unicodedata
from dataclasses import dataclass, field

import numpy as np

from .comum import RAIZ, Erro, ok, pasta_do_video, relativo, trabalho
from .formato import FPS
from .roteiro import EDICAO, assinatura_edicao, ler_roteiro, ler_tempos

# Modelo de fala. Medido nesta máquina (8 núcleos, 4 threads, int8) com 89 s de fala, tempo / pico de
# memória / palavras erradas: tiny 3 s / 340 MB / 25% · base 5 s / 390 MB / 37% (pulou um pedaço) ·
# small 14 s / 810 MB / 12% · medium 39 s / 2,2 GB / 12% · large-v3-turbo 26 s / 2,1 GB / 11%
# (com 111 s de gravação, o editar inteiro com o turbo: 34 s e 2,6 GB de pico).
# O padrão é o large-v3-turbo: além de errar menos palavra, transcreve a gagueira ("dez... dez vezes")
# que o small às vezes engole (e aí ela não sai). Com pouca memória livre cai para o small, que cabe
# do lado de outra coisa pesada. HUMANIM_WHISPER escolhe (nome do modelo ou pasta de um modelo CTranslate2).
PADRAO, LEVE, MEMORIA_PADRAO = "large-v3-turbo", "small", 3.0  # GB livres para o padrão (pico de 2,6 GB)
MODELO = os.environ.get("HUMANIM_WHISPER", "")
THREADS = int(os.environ.get("HUMANIM_WHISPER_THREADS", 4))
MODELOS = RAIZ / "modelos" / "whisper"
TAMANHO = {"tiny": "75 MB", "base": "145 MB", "small": "460 MB", "medium": "1,5 GB", "large-v3-turbo": "1,6 GB"}
# Puxa a transcrição literal: sem isto o Whisper "limpa" muleta e repetição, e aí não dá para cortar.
PROMPT = "Hã, é... então, hum, eu, eu acho que... Bom, é isso. Tá, vamos lá."

SR = 16000
PASSO = 0.01  # energia de 10 em 10 ms
PAUSA = {"frase": 0.30, "virgula": 0.20, "palavra": 0.12}  # pausa que fica, pela pontuação do roteiro
FOLGA = 0.10  # pausa até PAUSA + FOLGA fica como está: cortar pouco só faz pulo
INICIO, FIM = 0.06, 0.16  # respiro antes da primeira e depois da última palavra de cada linha
MARGEM = 0.3  # quanto um trecho pode passar do [de, ate] do tempos.json (Espaço apertado em cima da fala)
FRONTEIRA = 0.5  # palavra a até isto da tecla (Espaço antes do fim da fala, R depois de recomeçar) pode ser da vizinha
OCLUSIVA = 0.15  # quase silêncio mais curto que isto dentro da palavra é o p/t/k ("gru-p-os"), não pausa
ILHA = 2.0  # voltar a casar depois de 2+ palavras fora do roteiro no meio: emenda de duas tentativas, evitar
CORTE_MINIMO = 0.1  # corte menor que isto não compensa o pulo
PARECIDO = 0.75  # palavras com essa semelhança contam como a mesma (pra/para, Taiwan/taiuan)
MULETAS = {"e", "eh", "ha", "han", "an", "ah", "ahn", "aham", "hum", "hm", "um", "uh", "uhm", "ne", "tipo",
           "entao", "bom"}
APELIDOS = {"pra": "para", "pro": "para", "ta": "esta", "to": "estou", "ce": "voce", "tava": "estava"}
CURTAS = {"que", "com", "para", "por", "uma", "uns", "das", "dos", "nas", "nos", "ele", "ela", "seu", "sua",
          "isso", "esse", "essa", "este", "esta", "aqui", "ali", "tem", "foi", "vai", "mas", "ou"}
NOMES = {"silencio": ("silêncio", "silêncios"), "respiracao": ("respiração", "respirações"),
         "muleta": ("muleta", "muletas"), "repeticao": ("repetição", "repetições"),
         "comeco_errado": ("começo errado", "começos errados"), "fora_do_roteiro": ("fala fora do roteiro",
                                                                                     "falas fora do roteiro")}


# ---------------------------------------------------------------- palavras e números

UNIDADES = ("zero um dois três quatro cinco seis sete oito nove dez onze doze treze quatorze quinze dezesseis "
            "dezessete dezoito dezenove").split()
DEZENAS = "_ _ vinte trinta quarenta cinquenta sessenta setenta oitenta noventa".split()
CENTENAS = "_ cento duzentos trezentos quatrocentos quinhentos seiscentos setecentos oitocentos novecentos".split()
TOKEN = re.compile(r"\d+(?:[.,]\d+)*(?:\s?%)?|\w+|%")


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
    """'30', '30.000', '2,5', '20%' em palavras."""
    pct = texto.endswith("%")
    t = texto.rstrip("%").strip()
    if re.fullmatch(r"\d{1,3}(\.\d{3})+", t):
        t = t.replace(".", "")
    inteiro, _, decimal = t.replace(".", ",").partition(",")
    palavras = extenso(int(inteiro)) if len(inteiro) < 13 else list(inteiro)
    if decimal.isdigit():
        palavras += ["vírgula"] + (extenso(int(decimal)) if not decimal.startswith("0") else
                                   [UNIDADES[int(c)] for c in decimal])
    return palavras + (["por", "cento"] if pct else [])


def normal(palavra):
    """Sem acento, minúscula e com apelido trocado: para comparar, não para mostrar."""
    p = unicodedata.normalize("NFD", palavra.lower())
    p = "".join(c for c in p if unicodedata.category(c) != "Mn")
    return APELIDOS.get(p, p)


def muleta(token):
    return re.sub(r"(.)\1+", r"\1", token) in MULETAS


def tokens(texto):
    """[(normalizado, como está no texto, pontuação depois)]: números viram palavras."""
    saida, achados = [], list(TOKEN.finditer(texto))
    for i, m in enumerate(achados):
        depois = texto[m.end():achados[i + 1].start() if i + 1 < len(achados) else len(texto)]
        pont = "frase" if re.search(r"[.?!:…]", depois) else "virgula" if re.search(r"[,;—–]| - ", depois) else ""
        bruto = m.group()
        partes = numero(bruto) if bruto[0].isdigit() else ["por", "cento"] if bruto == "%" else [bruto]
        for k, parte in enumerate(partes):
            saida.append((normal(parte), bruto, pont if k == len(partes) - 1 else ""))
    return saida


def parecido(a, b):
    if a == b:
        return 1.0
    if min(len(a), len(b)) <= 2:
        return 0.0
    return difflib.SequenceMatcher(None, a, b).ratio()


# ---------------------------------------------------------------- transcrição

@dataclass
class Palavra:
    texto: str
    de: float
    ate: float
    prob: float
    toks: list = field(default_factory=list)
    fica: bool = False
    corte: str = ""  # tipo do corte, se sai


def carregar_audio(gravacao):
    """Áudio a 16 kHz, mono, com t=0 no início do arquivo: a mesma linha do tempo do tempos.json e do montar."""
    r = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", str(gravacao), "-map", "0:a:0",
                        "-af", "aresample=async=1:first_pts=0", "-ar", str(SR), "-ac", "1", "-f", "f32le", "-"],
                       capture_output=True)
    if r.returncode != 0 or not r.stdout:
        fim = r.stderr.decode(errors="replace").strip().splitlines()[-3:]
        raise Erro(f"não consegui ler o áudio de {relativo(gravacao)} (ela tem som?): {' '.join(fim)}")
    return np.frombuffer(r.stdout, np.float32)


def memoria_livre():
    """GB de memória disponível (MemAvailable), ou None fora do Linux."""
    try:
        with open("/proc/meminfo") as f:
            return next(int(x.split()[1]) / 2 ** 20 for x in f if x.startswith("MemAvailable:"))
    except (OSError, StopIteration, ValueError):
        return None


def escolher_modelo(pasta, assinatura):
    """(modelo desta rodada, aviso): HUMANIM_WHISPER, ou o padrão se a memória deixa (ou se esta gravação
    já foi transcrita com ele: aí não carrega modelo nenhum), ou o leve."""
    if MODELO:
        return MODELO, ""
    if guardada(pasta, assinatura, PADRAO) is not None:
        return PADRAO, ""
    livre = memoria_livre()
    if livre is not None and livre < MEMORIA_PADRAO:
        return LEVE, (f"Atenção: só {livre:.1f} GB de memória livre, transcrevi com o {LEVE}, que às vezes engole "
                      f"uma gagueira (e aí ela fica). Com a máquina livre, rode de novo para usar o {PADRAO}.")
    return PADRAO, ""


def caminho_modelo(nome):
    if os.path.isdir(nome):
        return nome
    pasta = MODELOS / nome
    if (pasta / "model.bin").exists():
        return str(pasta)
    try:
        from faster_whisper.utils import available_models, download_model
    except ImportError:
        raise Erro("falta o faster-whisper no ambiente do humanim. Instale: "
                   "uv pip install -p .venv/bin/python -e .") from None
    if nome not in available_models():
        raise Erro(f"HUMANIM_WHISPER={nome} não é um modelo do faster-whisper nem uma pasta. Use um destes: "
                   f"{', '.join(available_models())} (padrão: {PADRAO}).")
    print(f"baixando o modelo de fala {nome} ({TAMANHO.get(nome, '?')}) para modelos/whisper/{nome} ...",
          flush=True)
    try:
        return download_model(nome, output_dir=str(pasta))
    except Exception as e:  # noqa: BLE001 — rede, disco: tudo vira um ERRO legível
        raise Erro(f"não consegui baixar o modelo de fala {nome} ({e}). Confira a internet e rode de novo.") from None


def arquivo_transcricao(pasta, nome):
    return trabalho(pasta) / f"transcricao-{os.path.basename(nome.rstrip('/'))}.json"


def guardada(pasta, assinatura, nome):
    """As palavras da transcrição desta gravação com este modelo, se já foi feita (em .trabalho/), ou None."""
    cache = arquivo_transcricao(pasta, nome)
    if cache.exists():
        try:
            dados = json.loads(cache.read_text(encoding="utf-8"))
            if dados.get("assinatura") == assinatura and dados.get("modelo") == nome:
                return [Palavra(**p) for p in dados["palavras"]]
        except (ValueError, KeyError, TypeError):
            pass
    return None


def transcrever(audio, pasta, assinatura, nome):
    """Palavras com tempo, da gravação inteira. Guarda em .trabalho/ e reaproveita se nada mudou."""
    cache = arquivo_transcricao(pasta, nome)
    palavras = guardada(pasta, assinatura, nome)
    if palavras is not None:
        print(f"transcrição reaproveitada ({cache.name}: mesma gravação, mesmo modelo).", flush=True)
        return colar_numeros(palavras)
    caminho = caminho_modelo(nome)
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        raise Erro("falta o faster-whisper no ambiente do humanim. Instale: "
                   "uv pip install -p .venv/bin/python -e .") from None
    segundos = len(audio) / SR
    print(f"transcrevendo {segundos:.0f}s de fala com o modelo {nome} na CPU ...", flush=True)
    inicio = aviso = time.monotonic()
    palavras = []
    try:
        modelo = WhisperModel(caminho, device="cpu", compute_type="int8", cpu_threads=THREADS)
        trechos, _ = modelo.transcribe(audio, language="pt", word_timestamps=True, initial_prompt=PROMPT,
                                       condition_on_previous_text=False, vad_filter=False, beam_size=5)
        for trecho in trechos:
            for w in trecho.words:
                texto = w.word.strip()
                if re.search(r"[\w%]", texto):  # "%" sozinho é "por cento" dito
                    palavras.append(Palavra(texto, round(float(w.start), 3),
                                            round(max(float(w.end), w.start + 0.02), 3), round(float(w.probability), 3)))
            if time.monotonic() - aviso > 15:
                aviso = time.monotonic()
                print(f"  {trecho.end:.0f}/{segundos:.0f}s", flush=True)
    except Exception as e:  # noqa: BLE001 — modelo quebrado ou pela metade, falta de memória: vira um ERRO legível
        raise Erro(falha_do_modelo(nome, caminho, pasta, e)) from None
    print(f"  transcrito em {time.monotonic() - inicio:.0f}s", flush=True)
    cache.write_text(json.dumps({"assinatura": assinatura, "modelo": nome,
                                 "palavras": [{"texto": p.texto, "de": p.de, "ate": p.ate, "prob": p.prob}
                                              for p in palavras]}, ensure_ascii=False), encoding="utf-8")
    return colar_numeros(palavras)


def falha_do_modelo(nome, caminho, pasta, e):
    """O ERRO de quando o modelo de fala não abre ou para no meio, com o que fazer."""
    editar = f"humanim editar {relativo(pasta / 'gravacao.webm')}"
    linhas = str(e).strip().splitlines()
    motivo = type(e).__name__ + (f": {linhas[0][:200]}" if linhas else "")
    texto = f"o modelo de fala {nome} não rodou ({motivo})."
    if isinstance(e, MemoryError) or re.search(r"memory|alloc", str(e), re.I):
        texto += " Faltou memória: feche o que estiver pesado (render do animar, tratar, Chrome) e rode de novo."
    elif os.path.realpath(caminho).startswith(os.path.realpath(MODELOS) + os.sep):
        texto += (f" O modelo deve ter baixado pela metade ou estar corrompido: apague a pasta {relativo(caminho)} "
                  f"e rode de novo, que ele baixa outra vez: {editar}")
    else:
        texto += (f" Confira a pasta do HUMANIM_WHISPER ({caminho}: tem que ser um modelo CTranslate2 do "
                  f"faster-whisper) ou rode sem ele: {editar}")
    return texto + f"\nCom pouca memória livre, use o modelo leve: HUMANIM_WHISPER={LEVE} {editar}"


def colar_numeros(palavras):
    """O faster-whisper parte número em palavras sem espaço entre elas ("22" ",1%.", "1" ".500.", "20" "%"):
    cola de volta, para comparar com o roteiro pelo número inteiro."""
    saida = []
    for p in palavras:
        a = saida[-1] if saida else None
        if a and re.match(r"[.,]\d|%", p.texto) and a.texto[-1:].isdigit() and p.de - a.ate < 0.5:
            saida[-1] = Palavra(a.texto + p.texto, a.de, max(a.ate, p.ate), min(a.prob, p.prob))
        else:
            saida.append(p)
    return saida


# ---------------------------------------------------------------- energia

class Som:
    """Energia do áudio em dB de 10 em 10 ms, onde há som e se o som é voz (vogal) ou ruído (respiração)."""

    def __init__(self, audio):
        passo, janela = int(SR * PASSO), int(SR * 0.025)
        n = len(audio) // passo + 1
        pad = np.pad(audio, (janela // 2, janela))
        blocos = pad[np.arange(n)[:, None] * passo + np.arange(janela)[None, :]]
        self.db = 10 * np.log10(np.mean(blocos.astype(np.float64) ** 2, axis=1) + 1e-12)
        sinais = np.signbit(blocos)
        self.zcr = np.mean(sinais[:, 1:] != sinais[:, :-1], axis=1)
        piso, voz = np.percentile(self.db, 10), np.percentile(self.db, 97)
        self.limiar = min(piso + max(8.0, 0.3 * (voz - piso)), voz - 15)
        som = self.db > self.limiar
        som = self._tapar(som, True, 4)  # oclusiva (p, t, k) no meio da palavra não é silêncio
        self.som = self._tapar(som, False, 3)  # estalo de 20 ms não é som
        # Som fraco: acima do ruído de fundo mas abaixo do limiar (vogal final átona, "ris-c-o", numa sala
        # com ruído). Só serve para não cortar o fim de uma palavra (Som.cauda).
        fraco = self._tapar(self.db > piso + 0.4 * (self.limiar - piso), False, 3)
        self.fraco = fraco | self.som
        self.n = n
        self.inicios = []  # onde cada palavra da transcrição começa (main preenche), em ordem

    @staticmethod
    def _tapar(mascara, valor, maximo):
        """Troca corridas de `not valor` com até `maximo` quadros, entre corridas de `valor`."""
        m = mascara.copy()
        k, n = 0, len(m)
        while k < n:
            if m[k] != valor:
                j = k
                while j < n and m[j] != valor:
                    j += 1
                if 0 < k and j < n and j - k <= maximo:
                    m[k:j] = valor
                k = j
            else:
                k += 1
        return m

    def q(self, t):
        return min(self.n - 1, max(0, int(round(t / PASSO))))

    def onset(self, w, limite):
        """Onde a palavra começa de verdade: a whisper erra o começo em até uns 200 ms."""
        k, lim = self.q(w.de), self.q(max(limite, w.de - 0.2))
        if self.som[k]:
            while k - 1 >= lim and self.som[k - 1]:
                k -= 1
        else:
            fim = self.q(max(w.de, w.ate - 0.03))
            j = k
            while j < fim and not self.som[j]:
                j += 1
            k = j if self.som[j] else k
        # A transcrição às vezes começa a palavra na respiração (ou muleta) de antes: a palavra começa depois
        # do último silêncio de 200 ms, ou de OCLUSIVA se o som antes dele é ruído (respiração, sem voz; um
        # silêncio mais curto pode ser o p/t/k depois de um "s": "es-t-á"). O som depois do silêncio tem que
        # ser desta palavra: som que só começa onde a palavra seguinte começa é dela (a transcrição esticou
        # esta por cima da pausa), e pular para ele inverteria o trecho.
        fim = self.q(min(w.ate + 0.05, self.seguinte(w)))
        j, ultimo, ini, curto = k, None, k, round(OCLUSIVA / PASSO)
        while j < fim:
            if not self.som[j]:
                s = j
                while j < fim and not self.som[j]:
                    j += 1
                if j < fim and self.som[j] and (j - s >= 20 or (j - s >= curto and self.ruido(ini, s))):
                    ultimo, ini = j, j
            else:
                j += 1
        return (ultimo if ultimo is not None else k) * PASSO

    def seguinte(self, w):
        """Onde começa a palavra da transcrição depois de w (infinito se não tem)."""
        k = bisect.bisect_right(self.inicios, w.de + 1e-6)
        return self.inicios[k] if k < len(self.inicios) else math.inf

    def ruido(self, a, b):
        """Se o som entre os quadros a e b é ruído sem voz (respiração), pelo cruzamento por zero."""
        som = np.nonzero(self.som[a:b])[0] + a
        return len(som) > 0 and float(np.median(self.zcr[som])) >= 0.12

    def offset(self, w, limite):
        """Onde a palavra termina de verdade."""
        k, lim = self.q(w.ate), self.q(min(limite, w.ate + 0.25))
        if self.som[k]:
            while k + 1 <= lim and self.som[k + 1]:
                k += 1
        else:
            ini = self.q(min(w.ate, w.de + 0.03))
            j = k
            while j > ini and not self.som[j]:
                j -= 1
            k = j if self.som[j] else k
        # O fim que a transcrição dá cai às vezes no silêncio do p/t/k antes da última sílaba ("gru-p-os"):
        # som que volta em menos de OCLUSIVA ainda é a palavra, até um pouco antes da palavra seguinte (som
        # dela, uma muleta logo depois, não: a pausa entre as duas é o que decide se a muleta sai).
        antes_de = min(limite, self.seguinte(w))
        k = self.cauda(k, self.q(min(antes_de - 0.05, w.ate + 0.25)), self.q(min(antes_de, w.ate + 0.5)))
        # depois da palavra veio silêncio de 250 ms e outro som (respiração): termina antes do silêncio.
        # Procura a partir de onde a palavra começa de verdade (a transcrição às vezes começa a palavra
        # na respiração de antes, e aí o silêncio entre as duas não é o fim dela).
        j, falou, curto = self.q(self.onset(w, w.de - 0.2)), 0, round(OCLUSIVA / PASSO)
        while j < k:
            if not self.som[j]:
                s = j
                while j < k and not self.som[j]:
                    j += 1
                if falou >= 5 and self.som[j] and (j - s >= 25 or (j - s >= curto and self.ruido(j, k + 1))):
                    return s * PASSO
            else:
                falou += 1
                j += 1
        return (k + 1) * PASSO

    def cauda(self, k, volta, fim):
        """Último quadro da palavra cujo som vai até k: o som (mesmo fraco) que volta depois de um quase
        silêncio de menos de OCLUSIVA, começando até o quadro `volta`, ainda é dela (vai no máximo até `fim`)."""
        curto = round(OCLUSIVA / PASSO)
        while True:
            j = k + 1
            while j <= volta and j - k <= curto and not self.fraco[j]:
                j += 1
            if j > volta or j - k > curto or not self.fraco[j]:
                return k
            while j + 1 <= fim and self.fraco[j + 1]:
                j += 1
            k = j

    def quieto(self, a, b, alvo):
        """O instante mais quieto entre a e b (entre os até 3 dB do mínimo, o mais perto de alvo)."""
        ka, kb = self.q(a), self.q(b)
        if kb <= ka:
            return min(max(alvo, a), b) if b >= a else (a + b) / 2
        trecho = self.db[ka:kb + 1]
        cand = np.nonzero(trecho <= trecho.min() + 3)[0] + ka
        return float(cand[np.argmin(np.abs(cand * PASSO - alvo))] * PASSO)

    def conteudo(self, a, b):
        """O que tem entre a e b, sem palavra: 'respiracao' (ruído), 'muleta' (voz) ou 'silencio'."""
        ka, kb = self.q(a), self.q(b)
        som = np.nonzero(self.som[ka:kb])[0] + ka
        if len(som) * PASSO < 0.08:
            return "silencio"
        return "respiracao" if self.ruido(ka, kb) else "muleta"


# ---------------------------------------------------------------- alinhamento

def junta(alvo, a, b):
    """Se os pedaços a + b são a palavra alvo partida em dois."""
    inteiro = parecido(alvo, a + b)
    return inteiro >= 0.85 and inteiro > max(parecido(alvo, a), parecido(alvo, b))


def alinhar(S, W, vizinhas=frozenset()):
    """Melhor casamento entre os tokens do roteiro (S) e os falados (W), em ordem.

    Passos: igual/trocada (fica), sobra (token falado que sai), falta (do roteiro, não foi dito) e
    junta (dois falados = um do roteiro, ou o contrário). Empate vai para o falado mais tarde: numa
    repetição ou começo errado, fica a última tentativa. E voltar a casar depois de 2 ou mais palavras
    fora do roteiro (sem contar muleta), no meio, custa ILHA: é emendar o começo de uma tentativa com o
    fim da outra, que só vale se a última tentativa tem bem mais palavras erradas (pela transcrição) que a
    anterior. Palavra trocada não conta como volta ao roteiro (senão trocar em vez de sobrar pularia a
    regra). `vizinhas`: tokens de palavras da linha vizinha, que só vêm para esta se casarem (no empate,
    fica a palavra da própria linha).
    """
    m, n = len(S), len(W)
    inf = float("inf")
    # estado: 0 = nada casado ainda; 1 = casou igual; 2 = casou e depois 1 palavra fora; 3 = 2 ou mais
    custo = [[[inf] * 4 for _ in range(n + 1)] for _ in range(m + 1)]
    volta = [[[None] * 4 for _ in range(n + 1)] for _ in range(m + 1)]
    custo[0][0][0] = 0.0
    eps = 1e-5

    def relaxar(i, j, e, ni, nj, ne, c, passo):
        if c < custo[ni][nj][ne] - 1e-12:
            custo[ni][nj][ne], volta[ni][nj][ne] = c, (i, j, e, passo)

    for i in range(m + 1):
        for j in range(n + 1):
            for e in range(4):
                c = custo[i][j][e]
                if c == inf:
                    continue
                casar = c + eps * (n - j) + (0.05 if j in vizinhas else 0)
                volta_ao_roteiro = casar + (ILHA if e == 3 else 0)
                if i < m and j < n:
                    if parecido(S[i][0], W[j][0]) >= PARECIDO:
                        relaxar(i, j, e, i + 1, j + 1, 1, volta_ao_roteiro, "igual")
                    else:
                        relaxar(i, j, e, i + 1, j + 1, max(e, 1), casar + 1.0 + 0.3 * muleta(W[j][0]), "trocada")
                if j < n:
                    fora = muleta(W[j][0])
                    relaxar(i, j, e, i, j + 1, e if e == 0 or fora else min(e + 1, 3), c + (0.4 if fora else 1.0),
                            "sobra")
                if i < m:
                    relaxar(i, j, e, i + 1, j, e, c + 1.1, "falta")
                # junta: a transcrição partiu ou colou palavras ("atas ou" = "atrasou", "a prova" = "aprova").
                # Muleta não entra ("hã" + "uma" parece "uma", mas o "hã" sai) e grudado precisa dar mais
                # certo que cada pedaço sozinho ("o" + "banco" não vira "banco": o "o" é outra palavra).
                if (i < m and j + 1 < n and W[j][2] and not muleta(W[j][0]) and not muleta(W[j + 1][0])
                        and junta(S[i][0], W[j][0], W[j + 1][0])):
                    relaxar(i, j, e, i + 1, j + 2, 1, volta_ao_roteiro + 0.1, "junta")
                if i + 1 < m and j < n and not muleta(W[j][0]) and junta(W[j][0], S[i][0], S[i + 1][0]):
                    relaxar(i, j, e, i + 2, j + 1, 1, volta_ao_roteiro + 0.1, "junta")
    e = min(range(4), key=lambda x: custo[m][n][x])
    passos, i, j = [], m, n
    while (i, j, e) != (0, 0, 0):
        pi, pj, pe, passo = volta[i][j][e]
        passos.append((passo, pi, i, pj, j))
        i, j, e = pi, pj, pe
    return passos[::-1]


# ---------------------------------------------------------------- edição de uma linha

@dataclass
class Linha:
    numero: int
    marca: str
    fala: str
    de: float
    ate: float
    palavras: list
    trechos: list = field(default_factory=list)
    cortes: list = field(default_factory=list)
    diferencas: list = field(default_factory=list)


def falados(ps):
    """Os tokens falados das palavras ps, [(token, texto, gruda)], e o índice da palavra de cada um."""
    W, dono = [], []
    for k, w in enumerate(ps):
        w.toks = [t[0] for t in tokens(w.texto)]
        # o último token da palavra só junta com o da próxima se não tem pausa entre as duas
        gruda = k + 1 < len(ps) and ps[k + 1].de - w.ate < 0.12
        W += [(t, w.texto, gruda or n + 1 < len(w.toks)) for n, t in enumerate(w.toks)]
        dono += [k] * len(w.toks)
    return W, dono


def casadas(fala, ps, vizinhas=()):
    """Índices das palavras de ps que o alinhamento com a fala casa (igual ou junta)."""
    W, dono = falados(ps)
    tv = frozenset(j for j, k in enumerate(dono) if k in vizinhas)
    return {dono[j] for passo, _, _, j0, j1 in alinhar(tokens(fala), W, tv) if passo in ("igual", "junta")
            for j in range(j0, j1)}


def redistribuir(linhas, palavras):
    """Palavra dita em cima da tecla vai para a linha a que ela pertence.

    Cada palavra é da linha em que cai o meio dela. Mas o Espaço apertado antes do fim da fala põe a
    última palavra na linha seguinte, e o R apertado depois de recomeçar deixa a primeira entre as linhas
    (em nenhuma). Palavra a até FRONTEIRA da tecla que não casa com o roteiro da linha dela (ou que não é
    de linha nenhuma) é oferecida à vizinha, e fica com ela se lá casa (o alinhamento decide).
    """
    meio = [(w.de + w.ate) / 2 for w in palavras]
    indice = {id(w): k for k, w in enumerate(palavras)}
    presas = {id(x.palavras[k]) for x in linhas for k in casadas(x.fala, x.palavras)}
    dona = {}  # id da palavra que muda -> linha nova
    for n, x in enumerate(linhas):
        ant = linhas[n - 1].ate if n else -math.inf
        prox = linhas[n + 1].de if n + 1 < len(linhas) else math.inf

        def livre(k):
            return id(palavras[k]) not in presas and id(palavras[k]) not in dona

        # antes: da linha anterior ou de entre as duas (aí, se está mais perto desta tecla que da anterior),
        # tocando os FRONTEIRA s antes da tecla (a transcrição às vezes estica a palavra para trás na pausa)
        antes = [k for k, w in enumerate(palavras) if meio[k] < x.de and w.ate > x.de - FRONTEIRA and livre(k)
                 and (meio[k] < ant or x.de - meio[k] <= meio[k] - ant)]
        depois = [k for k, w in enumerate(palavras) if meio[k] >= x.ate and w.de < x.ate + FRONTEIRA and livre(k)
                  and (meio[k] >= prox or meio[k] - x.ate < prox - meio[k])]
        if not antes and not depois:
            continue
        proprias = [indice[id(w)] for w in x.palavras if id(w) not in dona]
        ks = sorted(set(antes + proprias + depois))
        ps = [palavras[k] for k in ks]
        vizinhas = {i for i, k in enumerate(ks) if k in antes or k in depois}
        for i in casadas(x.fala, ps, vizinhas) & vizinhas:
            dona[id(ps[i])] = n
    if dona:
        for n, x in enumerate(linhas):
            minhas = {id(w) for w in x.palavras}
            x.palavras = [w for w in palavras if dona.get(id(w), n if id(w) in minhas else None) == n]


def decidir(linha, som):
    """Marca quais palavras ficam (w.fica) e o tipo de corte das que saem; devolve as diferenças e as faltas."""
    S = tokens(linha.fala)
    W, dono = falados(linha.palavras)
    passos = alinhar(S, W)
    pontuacao = {}  # palavra -> pontuação do roteiro depois dela
    faltas = [0] * (len(linha.palavras) + 1)  # tokens do roteiro que faltam antes da palavra k
    diferencas = []
    for passo, i0, i1, j0, j1 in passos:
        if passo in ("igual", "trocada", "junta"):
            for j in range(j0, j1):
                linha.palavras[dono[j]].fica = True
                pontuacao[dono[j]] = S[i1 - 1][2] or pontuacao.get(dono[j], "")
            if passo == "trocada":
                diferencas.append({"tipo": "trocada", "roteiro": S[i0][1], "falado": W[j0][1],
                                   "parecido": round(parecido(S[i0][0], W[j0][0]), 2), "token": S[i0][0],
                                   "certeza": linha.palavras[dono[j0]].prob})
        elif passo == "falta":
            faltas[dono[j0] if j0 < len(dono) else len(linha.palavras)] += 1
            diferencas.append({"tipo": "faltando", "roteiro": S[i0][1], "token": S[i0][0]})

    # As que sobraram, em corridas: sai o que é muleta, repetição, começo errado ou fala fora do roteiro
    # com pausa em volta. O resto fica (é fala que a transcrição errou): nunca cortar fala na dúvida.
    ps, k = linha.palavras, 0
    while k < len(ps):
        if ps[k].fica:
            k += 1
            continue
        j = k
        while j < len(ps) and not ps[j].fica:
            j += 1
        corrida = ps[k:j]
        ant = ps[k - 1] if k > 0 else None
        prox = ps[j] if j < len(ps) else None
        tipo = classificar(corrida, ant, prox, sum(faltas[k:j + 1]) if prox else sum(faltas[k:]), som)
        for w in corrida:
            if tipo:
                w.corte = tipo
            else:
                w.fica = True
                diferencas.append({"tipo": "a_mais", "falado": w.texto, "token": w.toks[0]})
        k = j
    return diferencas, faltas, pontuacao


def classificar(corrida, ant, prox, faltam, som):
    """Tipo do corte de uma corrida de palavras fora do alinhamento, ou '' se ela fica.

    `faltam`: tokens do roteiro que não foram ditos ali perto (aí a corrida pode ser a fala que a
    transcrição errou, e só sai se tem pausa em volta)."""
    nucleo = [t for w in corrida for t in w.toks if not muleta(t)]
    antes = som.onset(corrida[0], 0) - som.offset(ant, 1e9) if ant else 9.0
    depois = som.onset(prox, 0) - som.offset(corrida[-1], 1e9) if prox else 9.0
    if not nucleo:
        # "e"/"é" curto grudado na fala dos dois lados costuma ser invenção da transcrição (ou o fim de
        # uma palavra): fica. Muleta de verdade tem pausa em volta ou é arrastada ("ééé").
        if max(antes, depois) < 0.06 and corrida[-1].ate - corrida[0].de < 0.3:
            return ""
        return "muleta"
    if prox is not None:
        p0 = prox.toks[0]
        if any(parecido(t, p0) >= PARECIDO for t in nucleo) or (len(nucleo[0]) >= 2 and p0.startswith(nucleo[0])):
            return "repeticao" if len(nucleo) == 1 else "comeco_errado"
    if ant is not None and parecido(nucleo[-1], ant.toks[-1]) >= PARECIDO:
        return "repeticao"
    # Na ponta da linha: sai se tem pausa entre ela e a fala que fica (grudada, pode ser a primeira ou a
    # última palavra do roteiro mal transcrita: "Quando a renda" no lugar de "Com renda").
    if ant is None or prox is None:
        return "fora_do_roteiro" if (depois if ant is None else antes) >= 0.15 else ""
    # No meio, com o roteiro inteiro casado em volta: é fala a mais (repetição mal transcrita, um "pera").
    # Sai se tem uma pausa de pelo menos um lado; grudada nos dois, pode ser pedaço de palavra partida.
    if faltam == 0 and len(corrida) <= 2 and max(antes, depois) >= 0.08:
        vizinhos = ant.toks[-1:] + prox.toks[:1]
        return "repeticao" if any(parecido(t, v) >= 0.5 for t in nucleo for v in vizinhos) else "fora_do_roteiro"
    # Faltando palavra do roteiro ali, a corrida pode ser ela mal transcrita: só sai bem separada.
    if min(antes, depois) >= 0.3:
        return "fora_do_roteiro"
    return ""


def editar_linha(linha, som, obstaculos, faltas, pontuacao):
    """Os trechos que ficam da linha, em quadros [a, b) do vídeo.

    `obstaculos`: palavras que nenhum trecho desta linha pode pegar (as que saem e as das outras linhas).
    """
    ps = linha.palavras
    ficam = [k for k, w in enumerate(ps) if w.fica]
    if not ficam:
        a, b = math.ceil(linha.de * FPS), math.floor(linha.ate * FPS)
        linha.diferencas.append({"tipo": "sem_fala", "token": ""})
        return [(a, max(b, a + 1))]
    # Até onde o som da linha pode ir, além das palavras das outras (obstáculos): a tecla com folga, ou a
    # fala, se ela passa da tecla (Espaço apertado antes do fim dela, R depois de recomeçar).
    lo = min(linha.de, ps[ficam[0]].de - 0.2) - MARGEM
    hi = min(max(linha.ate, ps[ficam[-1]].ate + 0.5) + MARGEM, (som.n - 3) * PASSO)  # não passa do fim da gravação

    def limite_esq(t):
        return max([lo] + [o.ate for o in obstaculos if o.ate <= t + 0.05 and o.de < t])

    def limite_dir(t):
        return min([hi] + [o.de for o in obstaculos if o.de >= t - 0.05 and o.ate > t])

    pedacos = []  # ((corte, onde a fala começa), (corte, onde a fala termina)) em segundos
    k0 = ficam[0]
    lim = limite_esq(ps[k0].de)
    on = som.onset(ps[k0], lim)
    if sum(faltas[:k0 + 1]):  # falta palavra do roteiro antes da primeira: o som logo antes fica
        on = estender_esq(som, on, max(lim, on - 0.45 * sum(faltas[:k0 + 1]) - 0.2))
    inicio = (som.quieto(max(lim, on - INICIO - 0.04), on - 0.02, on - INICIO), on)
    for ia, ib in zip(ficam, ficam[1:]):
        A, B, meio = ps[ia], ps[ib], ps[ia + 1:ib]  # meio: as que saem entre A e B
        alvo = PAUSA[pontuacao.get(ia) or "palavra"]
        if meio:
            off_a = som.offset(A, limite_dir(A.ate))
            on_b = som.onset(B, limite_esq(B.de))
            on_meio, off_meio = som.onset(meio[0], off_a), som.offset(meio[-1], on_b)
            fim_a = som.quieto(off_a + 0.02, max(off_a + 0.02, min(off_a + alvo / 2 + 0.04, on_meio - 0.02)),
                               off_a + alvo / 2)
            ini_b = som.quieto(min(on_b - 0.02, max(on_b - alvo / 2 - 0.04, off_meio + 0.02)), on_b - 0.02,
                               on_b - alvo / 2)
            pedacos.append((inicio, (fim_a, off_a)))
            inicio = (ini_b, on_b)
            continue
        # palavras vizinhas que ficam: o fim de A vai até onde B começa de verdade (a fronteira da
        # transcrição entre as duas erra para os dois lados)
        on_b = som.onset(B, A.de + 0.05)
        off_a = som.offset(A, on_b)
        if sum(faltas[ia + 1:ib + 1]):
            # falta palavra do roteiro aqui: o som do meio pode ser ela. Só encurta silêncio puro.
            for s0, s1 in silencios(som, off_a, on_b, alvo + FOLGA):
                pedacos.append((inicio, (s0 + alvo / 2, s0)))
                inicio = (s1 - alvo / 2, s1)
            continue
        if on_b - off_a > alvo + FOLGA:
            fim_a = som.quieto(off_a + 0.02, off_a + alvo / 2 + 0.04, off_a + alvo / 2)
            ini_b = som.quieto(on_b - alvo / 2 - 0.04, on_b - 0.02, on_b - alvo / 2)
            if ini_b - fim_a >= CORTE_MINIMO:
                pedacos.append((inicio, (fim_a, off_a)))
                inicio = (ini_b, on_b)
    kz = ficam[-1]
    lim = limite_dir(ps[kz].ate)
    off = som.offset(ps[kz], lim)
    if sum(faltas[kz + 1:]):
        off = estender_dir(som, off, min(lim, off + 0.45 * sum(faltas[kz + 1:]) + 0.2))
    pedacos.append((inicio, (som.quieto(off + 0.02, max(off + 0.02, min(lim, off + FIM + 0.04)), off + FIM), off)))
    # Pedaço em que a fala acaba antes de começar não tem palavra que fica (o começo e o fim vieram de
    # palavras diferentes, com a transcrição errando o tempo): sai, e os dois cortes em volta viram um.
    certos = [p for p in pedacos if p[1][1] - p[0][1] > 0.02]
    pedacos = certos or pedacos

    # Na grade de quadros: o início arredonda para trás e o fim para a frente se o arredondado comeria fala.
    trechos = []
    for (a, fala_a), (b, fala_b) in pedacos:
        qa = round(a * FPS)
        if qa / FPS > fala_a - 0.01:
            qa = math.floor((fala_a - 0.01) * FPS)
        qb = round(b * FPS)
        if qb / FPS < fala_b + 0.01:
            qb = math.ceil((fala_b + 0.01) * FPS)
        qa, qb = max(qa, 0), max(qb, qa + 1)
        if trechos and qa - trechos[-1][1] < CORTE_MINIMO * FPS:
            trechos[-1] = (trechos[-1][0], max(qb, trechos[-1][1]))
        else:
            trechos.append((qa, qb))
    return trechos


def estender_esq(som, t, limite):
    """Volta o começo sobre o som contínuo (pausas < 150 ms) até `limite`."""
    k, lim, quieto = som.q(t), som.q(limite), 0
    melhor = k
    while k > lim:
        k -= 1
        quieto = 0 if som.som[k] else quieto + 1
        if quieto > 15:
            break
        if som.som[k]:
            melhor = k
    return melhor * PASSO


def estender_dir(som, t, limite):
    k, lim, quieto = som.q(t), som.q(limite), 0
    melhor = k
    while k < lim:
        k += 1
        quieto = 0 if som.som[k] else quieto + 1
        if quieto > 15:
            break
        if som.som[k]:
            melhor = k + 1
    return melhor * PASSO


def silencios(som, a, b, minimo):
    """Corridas sem som entre a e b com pelo menos `minimo` segundos."""
    saida, k, kb = [], som.q(a), som.q(b)
    while k < kb:
        if not som.som[k]:
            s = k
            while k < kb and not som.som[k]:
                k += 1
            if (k - s) * PASSO >= minimo:
                saida.append((s * PASSO, k * PASSO))
        else:
            k += 1
    return saida


def descrever_cortes(linha, trechos, som):
    """O que saiu da janela da linha, pedaço por pedaço, com o tipo."""
    ini, fim = min(linha.de, trechos[0][0] / FPS), max(linha.ate, trechos[-1][1] / FPS)
    buracos, t = [], ini
    for a, b in trechos:
        if a / FPS > t + 1e-6:
            buracos.append((t, a / FPS))
        t = b / FPS
    if fim > t + 1e-6:
        buracos.append((t, fim))
    cortes = []
    for a, b in buracos:
        dentro = [w for w in linha.palavras if a - 0.02 <= (w.de + w.ate) / 2 <= b + 0.02 and not w.fica]
        if dentro:
            tipos = sorted({w.corte for w in dentro}, key=list(NOMES).index)
            cortes.append({"de": round(a, 3), "ate": round(b, 3), "tipo": tipos[-1],
                           "texto": " ".join(w.texto for w in dentro)})
            continue
        tipo = som.conteudo(a, b)
        if tipo != "silencio" or b - a >= 0.15:
            cortes.append({"de": round(a, 3), "ate": round(b, 3), "tipo": tipo,
                           "texto": "(som sem palavra)" if tipo == "muleta" else ""})
    return cortes


def importante(d):
    """Diferença que muda o que se diz: número, palavra de conteúdo, 'não'."""
    if d["tipo"] == "sem_fala":
        return True
    t = d.get("token", "")
    if d["tipo"] == "trocada" and d.get("parecido", 0) >= 0.6:
        return False
    if d["tipo"] == "a_mais":
        return t not in CURTAS and len(t) >= 4
    numerico = any(c.isdigit() for c in d.get("roteiro", "") + d.get("falado", ""))
    return numerico or t in {"nao", "sim", "sem", "mais", "menos", "nunca"} or (len(t) >= 3 and t not in CURTAS)


def frase(d):
    if d["tipo"] == "trocada":
        duvida = " (a transcrição não tem certeza)" if d.get("certeza", 1) < 0.5 else ""
        return f'"{d["falado"].strip(".,?!:;")}" no lugar de "{d["roteiro"]}"{duvida}'
    if d["tipo"] == "faltando":
        return f'faltou "{d["roteiro"]}"'
    if d["tipo"] == "a_mais":
        return f'"{d["falado"].strip(".,?!:;")}" a mais'
    return "não ouvi fala nenhuma"


def agrupar(diferencas):
    """Junta as diferenças que vêm do mesmo trecho do texto (um número vira várias palavras)."""
    saida = []
    for d in diferencas:
        if saida and saida[-1]["tipo"] == d["tipo"] and d["tipo"] != "sem_fala" and (
                d.get("roteiro") is not None and saida[-1].get("roteiro") == d.get("roteiro")
                and saida[-1].get("falado") == d.get("falado")):
            continue
        saida.append(dict(d))
    return saida


# ---------------------------------------------------------------- comando

def main(args):
    pasta = pasta_do_video(args.gravacao)
    gravacao = pasta / "gravacao.webm"
    if args.gravacao and args.gravacao.endswith(".webm") and os.path.basename(args.gravacao) != "gravacao.webm":
        raise Erro(f"o editar trabalha sobre a gravacao.webm da pasta (é dela que o tempos.json fala). "
                   f"Rode: humanim editar {relativo(gravacao)}")
    roteiro = relativo(pasta / "roteiro.md")
    if not gravacao.exists() or not (pasta / "tempos.json").exists():
        raise Erro(f"falta gravacao.webm ou tempos.json em {relativo(pasta)}. Grave primeiro: humanim gravar {roteiro}")
    linhas_roteiro = ler_roteiro(pasta)
    tempos, _ = ler_tempos(pasta, linhas_roteiro, editado=False)
    assinatura = assinatura_edicao(pasta)

    audio = carregar_audio(gravacao)
    som = Som(audio)
    modelo, aviso = escolher_modelo(pasta, assinatura["gravacao"])
    palavras = transcrever(audio, pasta, assinatura["gravacao"], modelo)
    som.inicios = sorted(p.de for p in palavras)

    linhas = []
    for lr, t in zip(linhas_roteiro, tempos):
        dentro = [w for w in palavras if t.de <= (w.de + w.ate) / 2 < t.ate]
        linhas.append(Linha(lr.numero, lr.marca, lr.fala, t.de, t.ate, dentro))
    redistribuir(linhas, palavras)
    decisoes = []
    for linha in linhas:
        diferencas, faltas, pontuacao = decidir(linha, som)
        linha.diferencas = diferencas
        decisoes.append((faltas, pontuacao))
    for linha, (faltas, pontuacao) in zip(linhas, decisoes):
        minhas = {id(w) for w in linha.palavras if w.fica}
        obstaculos = [w for w in palavras if id(w) not in minhas]
        linha.trechos = editar_linha(linha, som, obstaculos, faltas, pontuacao)
    # Duas linhas não dividem gravação: se uma passa por cima da outra, corta no mais quieto entre elas.
    for x, y in zip(linhas, linhas[1:]):
        if x.trechos[-1][1] > y.trechos[0][0]:
            meio = round(som.quieto(y.trechos[0][0] / FPS, x.trechos[-1][1] / FPS,
                                    (x.trechos[-1][1] + y.trechos[0][0]) / 2 / FPS) * FPS)
            x.trechos[-1] = (x.trechos[-1][0], max(meio, x.trechos[-1][0] + 1))
            y.trechos[0] = (min(max(meio, x.trechos[-1][1]), y.trechos[0][1] - 1), y.trechos[0][1])
    for linha in linhas:
        linha.cortes = descrever_cortes(linha, linha.trechos, som)
        linha.diferencas = agrupar(linha.diferencas)

    dados = {"versao": 1, **assinatura, "modelo": modelo, "fps": FPS, "linhas": []}
    for linha in linhas:
        dados["linhas"].append({
            "linha": linha.numero, "marca": linha.marca, "de": linha.de, "ate": linha.ate,
            "trechos": [[round(a / FPS, 4), round(b / FPS, 4)] for a, b in linha.trechos],
            "roteiro": linha.fala,
            "falado": " ".join(w.texto for w in linha.palavras),
            "fica": " ".join(w.texto for w in linha.palavras if w.fica),
            "diferencas": [{k: v for k, v in d.items() if k != "token"} | {"importante": importante(d)}
                           for d in linha.diferencas],
            "cortes": linha.cortes,
        })
    destino = pasta / EDICAO
    provisorio = destino.with_name(EDICAO + ".tmp")
    provisorio.write_text(json.dumps(dados, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    os.replace(provisorio, destino)
    ok("\n".join(resumo(pasta, linhas) + ([aviso] if aviso else [])))


def resumo(pasta, linhas):
    antes = sum(x.ate - x.de for x in linhas)
    depois = sum((b - a) / FPS for x in linhas for a, b in x.trechos)
    contagem = {}
    for x in linhas:
        for c in x.cortes:
            contagem[c["tipo"]] = contagem.get(c["tipo"], 0) + 1
    cortes = ", ".join(f"{n} {NOMES[t][n > 1]}" for t, n in sorted(contagem.items(), key=lambda i: list(NOMES).index(i[0])))
    texto = [f"{relativo(pasta / EDICAO)}: fala de {antes:.1f}s para {depois:.1f}s ({depois - antes:+.1f}s), "
             f"{len(linhas)} linhas. Cortes: {cortes or 'nenhum'}."]
    regravar, pequenas = [], []
    for x in linhas:
        dif = x.diferencas
        if any(importante(d) for d in dif):
            regravar.append(f"  linha {x.numero}: {'; '.join(frase(d) for d in dif if importante(d))}")
        elif dif:
            pequenas.append(f"{x.numero} ({'; '.join(frase(d) for d in dif)})")
    if regravar:
        texto.append("A fala difere do roteiro (palavra trocada ou faltando; confira e decida se regrava):")
        texto += regravar
        texto.append(f"Para regravar: humanim gravar {relativo(pasta / 'roteiro.md')} e depois este editar de novo. "
                     f"Se a diferença é erro da transcrição (o áudio está certo), siga.")
    else:
        texto.append("A fala bate com o roteiro.")
    if pequenas:
        texto.append(f"Diferenças pequenas, provavelmente da transcrição: linha {', '.join(pequenas)}.")
    texto.append(f"O que saiu e o que ficou, por linha: {relativo(pasta / EDICAO)} (cortes, diferencas).")
    texto.append(f"Próximo: humanim animar {relativo(pasta / 'roteiro.md')} (cenas na duração da fala editada), "
                 f"humanim tratar {relativo(pasta / 'gravacao.webm')} (em segundo plano), "
                 f"humanim montar {relativo(pasta)}")
    return texto
