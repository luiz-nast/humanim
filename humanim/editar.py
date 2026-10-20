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

from .comum import AUDIO_DO_ZERO, RAIZ, Erro, memoria_livre, ok, pasta_do_video, relativo, trabalho
from .fala import PAUSA, numero, pontuacao
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
MEMORIA_MINIMA = 1.5  # GB livres para abrir qualquer modelo (o small chega a 1 GB): abaixo disso, ERRO e não trava
MODELO = os.environ.get("HUMANIM_WHISPER", "")
THREADS = int(os.environ.get("HUMANIM_WHISPER_THREADS", 4))
FANTASMA = 0.2  # palavra com certeza abaixo disto e sem voz embaixo é invenção da transcrição
BURACO, VOLTAS = 0.5, 4  # fala sem palavra a partir disto (s de voz) é transcrita de novo, até VOLTAS vezes
MODELOS = RAIZ / "modelos" / "whisper"
TAMANHO = {"tiny": "75 MB", "base": "145 MB", "small": "460 MB", "medium": "1,5 GB", "large-v3-turbo": "1,6 GB"}
# Puxa a transcrição literal: sem isto o Whisper "limpa" muleta e repetição, e aí não dá para cortar.
PROMPT = "Hã, é... então, hum, eu, eu acho que... Bom, é isso. Tá, vamos lá."

SR = 16000
PASSO = 0.01  # energia de 10 em 10 ms
# PAUSA (fala.py): a pausa que fica depois de cada palavra, pela pontuação do roteiro
FOLGA = 0.10  # pausa até PAUSA + FOLGA fica como está: cortar pouco só faz pulo
INICIO, FIM = 0.06, 0.16  # respiro antes da primeira e depois da última palavra de cada linha
MARGEM = 0.3  # quanto um trecho pode passar do [de, ate] do tempos.json (Espaço apertado em cima da fala)
FRONTEIRA = 0.5  # palavra a até isto da tecla (Espaço antes do fim da fala, R depois de recomeçar) pode ser da vizinha
OCLUSIVA = 0.15  # quase silêncio mais curto que isto dentro da palavra é o p/t/k ("gru-p-os"), não pausa
TAPA_OCLUSIVA, TAPA_ESTALO = 0.04, 0.03  # buraco de som tapado no meio da fala; som solto que não conta (estalo)
SILENCIO_ANTES = 0.20  # silêncio a partir disto no começo de uma palavra: ela começa depois dele (onset)
SILENCIO_DEPOIS, FALA_ANTES = 0.25, 0.05  # silêncio que encerra a palavra (offset), com pelo menos FALA_ANTES de som
VAO_ESTENDER = 0.15  # estender o começo ou o fim sobre o som para num silêncio maior que isto
POR_FALTA = 0.45  # segundos de som que cada palavra do roteiro que faltou pode ter na ponta da fala
CONTINUA = 1.0  # até quanto depois do fim que a transcrição dá a palavra pode seguir, se o som não para
VOZ = 0.12  # cruzamento por zero abaixo disto é voz (vogal, m, n); acima, ruído (respiração, s, f, x)
SIBILO = 0.36  # e acima disto, o chiado do s, x, ch, f (fala); a respiração é um ruído mais grave
# Respiração: som sem voz e sem chiado entre dois vales, de pelo menos RESPIRO. Mais curta que RESPIRO_LONGA,
# também QUIETA dB abaixo da voz: a sílaba final sem voz ("limi-te", "clien-te" com o e mudo) é forte como a fala.
RESPIRO, RESPIRO_LONGA, QUIETA = 0.10, 0.30, 10.0
SOLTURA_TOPO, SOLTURA_SALTO = 6.0, 12.0  # dB: em 20 ms a vogal sem voz após p/t/k está perto do pico e longe do vale
SOLTURA_DURA = 0.17  # s: a vogal sem voz após p/t/k é sílaba átona, mais curta que isto; a respiração dura mais
VALE_RASO, VALE_JANELA = 6.0, 0.15  # muleta grudada: vale (dB) que a separa da palavra, procurado até s antes dela
FUNDO = 3.0  # dB acima do mínimo de um vale que ainda são o fundo dele (o n inteiro de "né", o murmúrio do nasal)
REPETIDA = 0.5  # casar a primeira cópia de uma repetição ("Vai prever. Vai prever calote") custa isto a mais
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

# Os números por extenso (numero, extenso) moram no fala.py: são regras de como o texto é falado.
TOKEN = re.compile(r"(?:R|US)\$\s?\d+(?:[.,]\d+)*|\d+(?:[.,]\d+)*(?:\s?%)?|\w+|%")
MOEDAS = {"R": ("real", "reais"), "US": ("dólar", "dólares")}
GRANDEZAS = {"mil": "", "milhao": "de", "milhoes": "de", "bilhao": "de", "bilhoes": "de", "trilhao": "de",
             "trilhoes": "de"}  # "R$ 30 mil" = trinta mil reais; "R$ 2 bilhões" = dois bilhões de reais


def normal(palavra):
    """Sem acento, minúscula e com apelido trocado: para comparar, não para mostrar."""
    p = unicodedata.normalize("NFD", palavra.lower())
    p = "".join(c for c in p if unicodedata.category(c) != "Mn")
    return APELIDOS.get(p, p)


def muleta(token):
    return re.sub(r"(.)\1+", r"\1", token) in MULETAS


def tokens(texto):
    """[(normalizado, como está no texto, pontuação depois)]: números viram palavras, e valor em dinheiro
    também, com a moeda onde se fala ("R$ 1.500" = mil e quinhentos reais)."""
    saida, achados, moeda = [], list(TOKEN.finditer(texto)), None
    for i, m in enumerate(achados):
        depois = texto[m.end():achados[i + 1].start() if i + 1 < len(achados) else len(texto)]
        pont = pontuacao(depois)
        bruto = m.group()
        if "$" in bruto:
            sigla, valor = bruto.split("$")
            partes, moeda = numero(valor.strip()), MOEDAS[sigla][valor.strip() != "1"]
            if i + 1 == len(achados) or normal(achados[i + 1].group()) not in GRANDEZAS:
                partes, moeda = partes + [moeda], None
        elif moeda and normal(bruto) in GRANDEZAS:  # a moeda do valor de antes vem depois do "bilhões"
            partes, moeda = [bruto] + [GRANDEZAS[normal(bruto)]] * bool(GRANDEZAS[normal(bruto)]) + [moeda], None
        else:
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
                        "-af", AUDIO_DO_ZERO, "-ar", str(SR), "-ac", "1", "-f", "f32le", "-"],
                       capture_output=True)
    if r.returncode != 0 or not r.stdout:
        fim = r.stderr.decode(errors="replace").strip().splitlines()[-3:]
        raise Erro(f"não consegui ler o áudio de {relativo(gravacao)} (ela tem som?): {' '.join(fim)}")
    return np.frombuffer(r.stdout, np.float32)


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


SEM_FASTER_WHISPER = "falta o faster-whisper no ambiente do humanim. Instale: uv pip install -p .venv/bin/python -e ."


def caminho_modelo(nome):
    if os.path.isdir(nome):
        return nome
    pasta = MODELOS / nome
    if (pasta / "model.bin").exists():
        return str(pasta)
    try:
        from faster_whisper.utils import available_models, download_model
    except ImportError:
        raise Erro(SEM_FASTER_WHISPER) from None
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


def transcrever(audio, pasta, assinatura, nome, som):
    """Palavras com tempo, da gravação inteira. Guarda em .trabalho/ e reaproveita se nada mudou.

    O Whisper às vezes dá a janela de 30 s por encerrada depois da primeira frase e pula o resto dela. Com
    os 3 s mudos da contagem antes de um começo errado ("Pra prever… Pra prever calote"), ele escreveu só
    "Quero viver", com o tempo de uma frase 24 s depois, e pulou o resto. Por isso a transcrição começa logo
    antes do primeiro som, e fala com som e sem palavra (buraco) é transcrita de novo, até a primeira frase
    depois dela (que pode ter vindo com o tempo errado), até não sobrar buraco ou não sair palavra nova."""
    cache = arquivo_transcricao(pasta, nome)
    palavras = guardada(pasta, assinatura, nome)
    modelo, mudou, tentados = None, palavras is None, []
    if palavras is not None:
        print(f"transcrição reaproveitada ({cache.name}: mesma gravação, mesmo modelo).", flush=True)
        # buraco que já foi transcrito de novo sem sair palavra (tosse, risada) não abre o modelo outra vez
        tentados = json.loads(cache.read_text(encoding="utf-8")).get("tentados", [])
    else:
        modelo = carregar_whisper(nome, pasta)
        print(f"transcrevendo {len(audio) / SR:.0f}s de fala com o modelo {nome} na CPU ...", flush=True)
        inicio = time.monotonic()
        voz = np.nonzero(som.som)[0]
        palavras = whisper(modelo, audio, pasta, [max(0.0, voz[0] * PASSO - 0.3)] if len(voz) else None)
        print(f"  transcrito em {time.monotonic() - inicio:.0f}s", flush=True)
    for _ in range(VOLTAS):
        lista = [(a, b) for a, b in buracos(som, palavras) if not any(x <= a and b <= y for x, y in tentados)]
        if not lista:
            break
        modelo = modelo or carregar_whisper(nome, pasta)
        print(f"  a transcrição pulou fala com som em {', '.join(f'{a:.1f}s a {b:.1f}s' for a, b in lista)}: "
              f"transcrevendo de novo só ali ...", flush=True)
        novas = whisper(modelo, audio, pasta, [t for par in lista for t in par])
        refeitos = [(a, b) for a, b in lista if any(a <= (w.de + w.ate) / 2 <= b for w in novas)]
        tentados, mudou = tentados + [list(b) for b in lista if b not in refeitos], True
        if not refeitos:
            break

        def dentro(w):
            return any(a <= (w.de + w.ate) / 2 <= b for a, b in refeitos)
        palavras = sorted([p for p in palavras if not dentro(p)] + [w for w in novas if dentro(w)],
                          key=lambda p: p.de)
    if mudou:
        cache.write_text(json.dumps({"assinatura": assinatura, "modelo": nome, "tentados": tentados,
                                     "palavras": [{"texto": p.texto, "de": p.de, "ate": p.ate, "prob": p.prob}
                                                  for p in palavras]}, ensure_ascii=False), encoding="utf-8")
    return colar_numeros(palavras)


_CARREGADOS = {}  # modelo de fala já aberto nesta execução (a segunda escuta usa o mesmo)


def carregar_whisper(nome, pasta):
    if nome in _CARREGADOS:
        return _CARREGADOS[nome]
    livre = memoria_livre()
    if livre is not None and livre < MEMORIA_MINIMA:
        raise Erro(f"só {livre:.1f} GB de memória livre: abrir o modelo de fala agora pode travar a máquina (ele "
                   f"precisa de {MEMORIA_MINIMA:.1f} GB ou mais). Feche o que estiver pesado (render do animar, tratar, "
                   f"abas do Chrome), confira com free -m e rode de novo: humanim editar "
                   f"{relativo(pasta / 'gravacao.webm')}")
    caminho = caminho_modelo(nome)
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        raise Erro(SEM_FASTER_WHISPER) from None
    try:
        modelo = WhisperModel(caminho, device="cpu", compute_type="int8", cpu_threads=THREADS)
    except Exception as e:  # noqa: BLE001 — modelo quebrado ou pela metade, falta de memória: vira um ERRO legível
        raise Erro(falha_do_modelo(nome, caminho, pasta, e)) from None
    modelo.humanim = (nome, caminho)
    _CARREGADOS[nome] = modelo
    return modelo


def whisper(modelo, audio, pasta, trechos_audio=None):
    """Palavras com tempo (segundos da gravação) do áudio inteiro ou só dos trechos [de, ate, de, ate, ...]."""
    segundos, aviso, palavras = len(audio) / SR, time.monotonic(), []
    try:
        trechos, _ = modelo.transcribe(audio, language="pt", word_timestamps=True, initial_prompt=PROMPT,
                                       condition_on_previous_text=False, vad_filter=False, beam_size=5,
                                       clip_timestamps=trechos_audio or "0")
        for trecho in trechos:
            for w in trecho.words:
                texto = w.word.strip()
                if re.search(r"[\w%]", texto):  # "%" sozinho é "por cento" dito
                    palavras.append(Palavra(texto, round(float(w.start), 3),
                                            round(max(float(w.end), w.start + 0.02), 3), round(float(w.probability), 3)))
            if time.monotonic() - aviso > 15:
                aviso = time.monotonic()
                print(f"  {trecho.end:.0f}/{segundos:.0f}s", flush=True)
    except Exception as e:  # noqa: BLE001 — modelo pela metade, falta de memória no meio: vira um ERRO legível
        raise Erro(falha_do_modelo(*modelo.humanim, pasta, e)) from None
    return palavras


def buracos(som, palavras):
    """Trechos [de, ate] para transcrever de novo: onde há fala (som de voz, não respiração) longe de toda
    palavra transcrita, pelo menos BURACO s de voz, juntando corridas a menos de 1 s uma da outra. Começam
    0,3 s antes do som (sem pegar a palavra de antes) e vão até o fim da primeira frase transcrita depois
    (a palavra com . ? ou !, até 10 s depois): as palavras dessa frase podem ser as da fala pulada, com o
    tempo errado."""
    ordem = sorted(palavras, key=lambda p: p.de)
    coberto = np.zeros(som.n, bool)
    for p in ordem:
        coberto[som.q(p.de - 0.25):som.q(p.ate + 0.25) + 1] = True
    grupos = []
    for k in np.nonzero(som.som & ~coberto)[0]:
        if grupos and k - grupos[-1][1] <= round(1.0 / PASSO):
            grupos[-1][1], grupos[-1][2] = k, grupos[-1][2] + 1
        else:
            grupos.append([k, k, 1])
    saida, fim_audio = [], som.n * PASSO
    for a, b, n in grupos:
        if n * PASSO < BURACO:
            continue
        ta, tb = a * PASSO, (b + 1) * PASSO
        antes = max([p.ate for p in ordem if p.ate <= ta] + [0.0])
        fim = tb + 0.3
        for p in ordem:
            if p.de >= tb - 0.25 and p.ate <= tb + 10:
                fim = max(fim, p.ate + 0.1)
                if re.search(r"[.?!…]$", p.texto):
                    break
        de, ate = round(float(max(antes, ta - 0.3, 0.0)), 2), round(float(min(fim, fim_audio)), 2)
        if saida and de <= saida[-1][1]:
            saida[-1] = (saida[-1][0], max(ate, saida[-1][1]))
        else:
            saida.append((de, ate))
    return saida


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
    """O faster-whisper parte número em palavras sem espaço entre elas ("22" ",1%.", "1" ".500.", "20" "%"),
    e escreve "mil e quinhentos reais" como "R" "1" ".500." (sem o "$" e sem "reais"): cola de volta, para
    comparar com o roteiro pelo número inteiro e com a moeda ("R$1.500.")."""
    saida = []
    for p in palavras:
        a = saida[-1] if saida else None
        if a and p.de - a.ate < 0.5 and (re.match(r"[.,]\d|%", p.texto) and a.texto[-1:].isdigit()
                                         or re.fullmatch(r"(R|US)\$?", a.texto) and p.texto[:1].isdigit()):
            junto = a.texto + ("$" if a.texto[-1] != "$" and p.texto[:1].isdigit() else "") + p.texto
            saida[-1] = Palavra(junto, a.de, max(a.ate, p.ate), min(a.prob, p.prob))
        else:
            saida.append(p)
    return saida


# ---------------------------------------------------------------- energia

def quadros(segundos):
    """Segundos em quadros de energia (de PASSO em PASSO)."""
    return round(segundos / PASSO)


class Som:
    """Energia do áudio em dB de 10 em 10 ms, onde há som e se o som é voz (vogal) ou ruído (respiração).

    Respiração não conta como som (som, fraco): para o corte ela é pausa, e sai com a pausa em volta."""

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
        self.n = n
        self.alto = self.db > self.limiar  # sem tapar nada: aqui aparece o vale entre dois sons encostados
        fraco = self.db > piso + 0.4 * (self.limiar - piso)
        self.resp = self._respiracoes(fraco, voz)
        som = self._tapar(self.alto & ~self.resp, True, quadros(TAPA_OCLUSIVA))  # oclusiva (p, t, k) no meio da
        self.som = self._tapar(som, False, quadros(TAPA_ESTALO))  # palavra não é silêncio; estalo não é som
        # Som fraco: acima do ruído de fundo mas abaixo do limiar (vogal final átona, "ris-c-o", numa sala
        # com ruído). Só serve para não cortar o fim de uma palavra (Som.cauda).
        self.fraco = self._tapar(fraco & ~self.resp, False, quadros(TAPA_ESTALO)) | self.som
        self.inicios = []  # onde cada palavra da transcrição começa (preparar), em ordem
        self.reais = []  # onde começa de verdade (pela energia) a primeira palavra a partir de cada uma delas
        self._inicio, self._fim = {}, {}  # id da palavra -> onde ela começa / termina de verdade

    def preparar(self, palavras):
        """Guarda as palavras da transcrição e onde cada uma começa de verdade. A transcrição (o modelo leve
        mais ainda) estica a palavra para trás por cima da pausa: o fim da palavra de antes não pode parar
        ali, e sim onde o som da seguinte começa."""
        ordem = sorted(palavras, key=lambda p: p.de)
        self.inicios = [p.de for p in ordem]
        self.reais = [math.inf] * (len(ordem) + 1)
        for i in range(len(ordem) - 1, -1, -1):  # de trás para a frente: o onset de uma olha a seguinte
            self.reais[i] = min(self.reais[i + 1], self.inicio(ordem[i]))

    def inicio(self, w):
        """Onde o som da palavra w começa, nunca antes do que a transcrição diz (em cima de outra fala, a
        fronteira da transcrição é o melhor que se tem)."""
        if id(w) not in self._inicio:
            self._inicio[id(w)] = max(w.de, self.onset(w, w.de))
        return self._inicio[id(w)]

    def fim(self, w):
        """Onde o som da palavra w termina, nunca depois do que a transcrição diz."""
        if id(w) not in self._fim:
            self._fim[id(w)] = min(w.ate, self.offset(w, w.ate))
        return self._fim[id(w)]

    def _respiracoes(self, fraco, voz):
        """Quadros de respiração. Cada som entre dois vales (corrida acima do limiar, sem tapar: a respiração
        encostada na palavra fica separada dela pelo vale) é respiração se é ruído (quase nenhum quadro de
        voz), sem o chiado do s/x/ch ("tóra-x", "gru-p-s" depois do p/t/k são fala), de pelo menos RESPIRO e,
        se mais curto que RESPIRO_LONGA, QUIETA dB abaixo da voz. E que não é a vogal sem voz depois do p/t/k
        (a soltura da oclusiva, "cin-c(u)" no fim da frase), que tem o mesmo ruído grave da respiração: ela
        nasce de uma vez do fechamento, que é curto (fala a menos de OCLUSIVA antes), e dura menos que
        SOLTURA_DURA. Nascer de uma vez sozinho não basta: a respiração também pode começar rápido. Vai até o
        fundo dos vales em volta."""
        resp, k, n = np.zeros(self.n, bool), 0, self.n
        while k < n:
            if not self.alto[k]:
                k += 1
                continue
            a = k
            while k < n and self.alto[k]:
                k += 1
            db, zcr = self.db[a:k], self.zcr[a:k]
            comeco = db[:2].max()
            if (k - a < round(RESPIRO / PASSO) or np.mean(zcr < VOZ) >= 0.15
                    or np.median(zcr[db >= db.max() - 10]) >= SIBILO
                    or (k - a < round(RESPIRO_LONGA / PASSO) and db.max() > voz - QUIETA)
                    or (a > 0 and db.max() - comeco < SOLTURA_TOPO
                        and comeco - self.db[max(0, a - 4):a].min() >= SOLTURA_SALTO
                        and k - a < quadros(SOLTURA_DURA) and self.alto[max(0, a - quadros(OCLUSIVA)):a].any())):
                continue
            i, j = a, k
            while i > 0 and fraco[i - 1] and self.db[i - 1] < self.db[i]:
                i -= 1
            while j < n and fraco[j] and self.db[j] < self.db[j - 1]:
                j += 1
            resp[i:j] = True
        return resp

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
        # do último silêncio de 200 ms, ou de OCLUSIVA se o som antes dele é ruído (sem voz; um silêncio mais
        # curto pode ser o p/t/k depois de um "s": "es-t-á"). A respiração que Som achou já é silêncio. O som
        # depois do silêncio tem que ser desta palavra: som que só começa onde a palavra seguinte começa é
        # dela (a transcrição esticou esta por cima da pausa), e pular para ele inverteria o trecho.
        fim = self.q(min(w.ate + 0.05, self.seguinte(w)))
        j, ultimo, ini, curto = k, None, k, round(OCLUSIVA / PASSO)
        while j < fim:
            if not self.som[j]:
                s = j
                while j < fim and not self.som[j]:
                    j += 1
                if j < fim and self.som[j] and (j - s >= quadros(SILENCIO_ANTES)
                                                or (j - s >= curto and self.ruido(ini, s))):
                    ultimo, ini = j, j
            else:
                j += 1
        return (ultimo if ultimo is not None else k) * PASSO

    def seguinte(self, w):
        """Onde começa de verdade a palavra da transcrição depois de w (infinito se não tem)."""
        k = bisect.bisect_right(self.inicios, w.de + 1e-6)
        return self.reais[k] if k < len(self.reais) else math.inf

    def ruido(self, a, b):
        """Se o som entre os quadros a e b é ruído sem voz (respiração), pelo cruzamento por zero."""
        som = np.nonzero(self.som[a:b])[0] + a
        return len(som) > 0 and float(np.median(self.zcr[som])) >= VOZ

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
        # A transcrição às vezes dá o fim bem antes, no fim da frase ("sessenta e seis" terminando 0,6 s antes
        # do "s" final, que saía): som que continua sem vale nenhum ainda é a palavra, até antes da seguinte.
        fim = self.q(min(antes_de - 0.05, w.ate + CONTINUA))
        while k + 1 <= fim and self.som[k + 1]:
            k += 1
        # depois da palavra veio silêncio de 250 ms e outro som (ou de OCLUSIVA e ruído): termina antes do
        # silêncio. Procura a partir de onde a palavra começa de verdade (a transcrição às vezes começa a
        # palavra na respiração de antes, e aí o silêncio entre as duas não é o fim dela).
        j, falou, curto = self.q(self.onset(w, w.de - 0.2)), 0, round(OCLUSIVA / PASSO)
        while j < k:
            if not self.som[j]:
                s = j
                while j < k and not self.som[j]:
                    j += 1
                if falou >= quadros(FALA_ANTES) and self.som[j] and (
                        j - s >= quadros(SILENCIO_DEPOIS) or (j - s >= curto and self.ruido(j, k + 1))):
                    return s * PASSO
            else:
                falou += 1
                j += 1
        return (k + 1) * PASSO

    def cauda(self, k, volta, fim):
        """Último quadro da palavra cujo som vai até k: o som (mesmo fraco) que volta depois de um quase
        silêncio de menos de OCLUSIVA, começando até o quadro `volta`, ainda é dela (vai no máximo até `fim`).
        Respiração encostada na palavra não é som (Som._respiracoes): não volta."""
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

    def proprio(self, ws, esq=None, dir=None):
        """Segundos de som só das palavras ws: das corridas de som (sem tapar, sem respiração) que tocam o
        intervalo delas na transcrição, as que não começam antes do meio da palavra `esq` (a de antes) nem
        terminam depois do meio da `dir` (a de depois): essas são o som da vizinha, sem vale até ws."""
        sons = self.alto & ~self.resp
        a, b = self.q(ws[0].de), max(self.q(ws[-1].ate), self.q(ws[0].de) + 1)
        lo = self.q((esq.de + esq.ate) / 2) if esq else -1
        hi = self.q((dir.de + dir.ate) / 2) if dir else self.n
        while a > 0 and sons[a] and sons[a - 1]:
            a -= 1
        total, k = 0, a
        while k < b:
            if not sons[k]:
                k += 1
                continue
            s = k
            while k < self.n and sons[k]:
                k += 1
            if s > lo and k <= hi:
                total += k - s
        return total * PASSO

    def pausa(self, w, sentido):
        """Segundos sem fala de w até o som mais perto, depois dela (sentido 1) ou antes (-1)."""
        k = self.q(self.offset(w, 1e9)) if sentido > 0 else self.q(self.onset(w, 0)) - 1
        j = k
        while 0 <= j < self.n and not self.som[j]:
            j += sentido
        return abs(j - k) * PASSO if 0 <= j < self.n else math.inf

    def vao(self, a, b):
        """Segundos sem fala entre a palavra a e a seguinte b, pela energia: do fim de verdade de a ao começo
        de verdade de b, sem outro limite além dos de onset e offset (0 e 1e9: nenhum)."""
        return self.onset(b, 0) - self.offset(a, 1e9)

    def vale(self, w):
        """Onde começa a muleta w dita no embalo da palavra de antes, sem silêncio entre as duas ("dado-s|é",
        "guarda|né"): o fundo do vale raso (VALE_RASO dB abaixo do som dos dois lados, a até 100 ms, mesmo
        acima do limiar) mais perto do fim do som dela, até VALE_JANELA antes do começo que a transcrição dá.
        Procura do fim (a pausa depois da muleta, ou a palavra seguinte) para trás, e não do tempo que a
        transcrição dá à muleta: ele erra para os dois lados, e cedo cai na palavra de antes, que aí perderia
        a última sílaba. Vale no meio do chiado ("clien-te-s|é": o s, acima do limiar e sem voz) vai até onde a
        voz da muleta começa, que o s é da palavra; vale com voz ("simples|né": o n) volta até o começo do
        fundo dele, que o n é da muleta. None se não tem: não há onde separar as duas sem comer uma."""
        de = self.q(w.de)
        fim = self.q(min(w.ate + VALE_JANELA, self.seguinte(w)))
        while fim > de and not self.som[fim - 1]:
            fim -= 1
        if fim == de:  # nada de som da muleta até a pausa ou a palavra seguinte
            return None
        a, lado = self.q(w.de - VALE_JANELA), quadros(0.1)
        for k in range(fim - 1, a - 1, -1):
            if (0 < k < self.n - 1 and self.db[k] <= min(self.db[k - 1], self.db[k + 1])
                    and self.db[max(0, k - lado):k].max() - self.db[k] >= VALE_RASO
                    and self.db[k + 1:k + 1 + lado].max() - self.db[k] >= VALE_RASO):
                fundo = self.db[k]
                if self.zcr[k] < VOZ:  # fundo com voz (o n de "né", que é da muleta): até onde ele começa
                    while k - 1 > a and self.zcr[k - 1] < VOZ and self.db[k - 1] <= fundo + FUNDO:
                        k -= 1
                elif self.alto[k]:  # no meio do chiado (o s, que é da palavra): até o último quadro sem voz
                    while k + 1 < fim and self.zcr[k + 1] >= VOZ:
                        k += 1
                return k * PASSO
        return None

    def conteudo(self, a, b):
        """O que tem entre a e b, sem palavra: 'respiracao' (ruído), 'muleta' (voz) ou 'silencio'."""
        ka, kb = self.q(a), self.q(b)
        som, resp = np.count_nonzero(self.som[ka:kb]), np.count_nonzero(self.resp[ka:kb])
        if (som + resp) * PASSO < 0.08:
            return "silencio"
        return "respiracao" if resp >= som or self.ruido(ka, kb) else "muleta"


# ---------------------------------------------------------------- alinhamento

def fonetico(p):
    """O fim da palavra como se fala: e e o finais átonos soam i e u ("mede a" se ouve "média")."""
    return re.sub(r"o$", "u", re.sub(r"e$", "i", p))


def junta(alvo, a, b):
    """Se os pedaços a + b são a palavra alvo partida em dois (ou duas palavras ditas como uma)."""
    inteiro = max(parecido(alvo, a + b), parecido(fonetico(alvo), fonetico(a) + fonetico(b)))
    return inteiro >= 0.85 and inteiro > max(parecido(alvo, a), parecido(alvo, b))


def primeira_copia(W):
    """Índices dos tokens falados que se repetem logo em seguida (1 a 4 palavras, sem contar muleta):
    "Vai prever. Vai prever calote" -> os do primeiro "Vai prever". É a tentativa que o recomeço desfaz."""
    ks = [j for j, t in enumerate(W) if not muleta(t[0])]
    saida, usados = set(), set()
    for k in range(4, 0, -1):  # a repetição mais longa primeiro, sem sobrepor ("A máquina. A máquina. A
        for p in range(len(ks) - 2 * k + 1):  # prender": é "A máquina" duas vezes, não "máquina. A")
            if (not usados & set(range(p, p + 2 * k))
                    and all(parecido(W[ks[p + d]][0], W[ks[p + k + d]][0]) >= PARECIDO for d in range(k))):
                saida.update(ks[p:p + k])
                usados.update(range(p, p + 2 * k))
    return saida


def alinhar(S, W, vizinhas=frozenset()):
    """Melhor casamento entre os tokens do roteiro (S) e os falados (W), em ordem.

    Passos: igual/trocada (fica), sobra (token falado que sai), falta (do roteiro, não foi dito) e
    junta (dois falados = um do roteiro, ou o contrário). Empate vai para o falado mais tarde: numa
    repetição ou começo errado, fica a última tentativa. E voltar a casar depois de 2 ou mais palavras
    fora do roteiro (sem contar muleta), no meio, custa ILHA: é emendar o começo de uma tentativa com o
    fim da outra, que só vale se a última tentativa tem bem mais palavras erradas (pela transcrição) que a
    anterior. Palavra trocada não conta como volta ao roteiro (senão trocar em vez de sobrar pularia a
    regra). `vizinhas`: tokens de palavras da linha vizinha (ou da borda da janela, em trocadas_na_linha),
    que só vêm para esta se casarem (no empate, fica a palavra da própria linha, ou a de dentro).
    """
    m, n = len(S), len(W)
    inf = float("inf")
    repetidas = primeira_copia(W)
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
                casar = c + eps * (n - j) + (0.05 if j in vizinhas else 0) + (REPETIDA if j in repetidas else 0)
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


def casadas(fala, ps, vizinhas=(), som=None, alheias=()):
    """Índices das palavras de ps que o alinhamento com a fala casa (igual ou junta).

    Com `som`, também a vizinha que não casa (fora muleta) mas está grudada (sem pausa, pela energia) numa
    palavra desta linha: é a mesma frase, dita em cima da tecla ("quase não erra" com o Espaço antes do
    "erra"), ou fala desta linha que a transcrição errou ("A" no lugar de "Pra", com o R apertado depois de
    recomeçar). Menos as `alheias`, que a própria linha delas troca por uma palavra do roteiro dela: com as
    linhas ditas emendadas, grudada não diz de qual é ("grupos. Segue" com o "Segue" ouvido "Sede"). E a que
    o alinhamento troca por uma palavra do roteiro que faltaria aqui, se a pausa entre ela e esta linha é
    menor que a do outro lado ("aprende? Regras." no lugar de "Padrões.", com o Espaço apertado na pausa da
    pergunta)."""
    W, dono = falados(ps)
    tv = frozenset(j for j, k in enumerate(dono) if k in vizinhas)
    passos = alinhar(tokens(fala), W, tv)
    casa = {dono[j] for passo, _, _, j0, j1 in passos if passo in ("igual", "junta") for j in range(j0, j1)}
    if som is None:
        return casa
    trocadas = {dono[j0] for passo, _, _, j0, _ in passos if passo == "trocada"}
    soltas = {i for i in vizinhas if not all(muleta(t) for t in ps[i].toks)}
    mudou = True
    while mudou:  # de dentro para fora: cada uma tem que encostar numa que já é desta linha
        mudou = False
        for i in sorted(soltas - casa):
            for v in (i - 1, i + 1):
                if not 0 <= v < len(ps) or (v in vizinhas and v not in casa):
                    continue
                a, b = ps[min(i, v)], ps[max(i, v)]
                dentro = som.vao(a, b)
                if ((dentro < OCLUSIVA and i not in alheias)
                        or (i in trocadas and dentro < som.pausa(ps[i], 1 if v < i else -1))):
                    casa.add(i)
                    mudou = True
                    break
    return casa


def trocadas_na_linha(x):
    """Índices das palavras da linha x que o alinhamento com a fala dela troca por uma palavra do roteiro. No
    empate, a troca fica com a palavra de dentro da janela, não com a que começa a até FRONTEIRA do fim dela
    (ou termina a até FRONTEIRA do começo), que pode ser da vizinha: "os loops. Segue" com o Espaço apertado
    depois do "Segue" troca "grupos" por "loops", e não por "Segue" (que é da linha seguinte)."""
    W, dono = falados(x.palavras)
    borda = frozenset(j for j, k in enumerate(dono)
                      if x.palavras[k].de > x.ate - FRONTEIRA or x.palavras[k].ate < x.de + FRONTEIRA)
    return {dono[j0] for passo, _, _, j0, _ in alinhar(tokens(x.fala), W, borda) if passo == "trocada"}


def redistribuir(linhas, palavras, som):
    """Palavra dita em cima da tecla vai para a linha a que ela pertence.

    Cada palavra é da linha em que cai o meio dela. Mas o Espaço apertado antes do fim da fala põe a
    última palavra na linha seguinte, e o R apertado depois de recomeçar deixa a primeira entre as linhas
    (em nenhuma). Palavra a até FRONTEIRA da tecla que não casa com o roteiro da linha dela (ou que não é
    de linha nenhuma), e a fala emendada nela, é oferecida à vizinha, e fica com ela se lá casa (o
    alinhamento decide), ou se é a mesma frase da vizinha (casadas).
    """
    meio = [(w.de + w.ate) / 2 for w in palavras]
    indice = {id(w): k for k, w in enumerate(palavras)}
    presas = {id(x.palavras[k]) for x in linhas for k in casadas(x.fala, x.palavras)}
    trocas = {id(x.palavras[k]) for x in linhas for k in trocadas_na_linha(x)}
    dona = {}  # id da palavra que muda -> linha nova
    for n, x in enumerate(linhas):
        ant = linhas[n - 1].ate if n else -math.inf
        prox = linhas[n + 1].de if n + 1 < len(linhas) else math.inf

        def livre(k):
            return id(palavras[k]) not in presas and id(palavras[k]) not in dona

        def antes_ok(k):  # da linha anterior ou de entre as duas (aí, mais perto desta tecla que da anterior)
            return meio[k] < x.de and livre(k) and (meio[k] < ant or x.de - meio[k] <= meio[k] - ant)

        def depois_ok(k):
            return meio[k] >= x.ate and livre(k) and (meio[k] >= prox or meio[k] - x.ate < prox - meio[k])

        def emendadas(a, b):  # palavras[a] e palavras[b] sem pausa entre elas, pela energia
            return som.vao(palavras[a], palavras[b]) < OCLUSIVA

        # tocando os FRONTEIRA s antes da tecla (a transcrição às vezes estica a palavra para trás na pausa),
        # e a fala emendada nelas do lado de fora: com o R apertado 0,8 s depois de recomeçar ou o Espaço 1 s
        # antes do fim, a frase inteira fica do outro lado da tecla, não só a palavra da ponta
        antes = [k for k, w in enumerate(palavras) if w.ate > x.de - FRONTEIRA and antes_ok(k)]
        while antes and antes[0] > 0 and antes_ok(antes[0] - 1) and emendadas(antes[0] - 1, antes[0]):
            antes.insert(0, antes[0] - 1)
        depois = [k for k, w in enumerate(palavras) if w.de < x.ate + FRONTEIRA and depois_ok(k)]
        while (depois and depois[-1] + 1 < len(palavras) and depois_ok(depois[-1] + 1)
               and emendadas(depois[-1], depois[-1] + 1)):
            depois.append(depois[-1] + 1)
        if not antes and not depois:
            continue
        proprias = [indice[id(w)] for w in x.palavras if id(w) not in dona]
        ks = sorted(set(antes + proprias + depois))
        ps = [palavras[k] for k in ks]
        vizinhas = {i for i, k in enumerate(ks) if k in antes or k in depois}
        alheias = {i for i in vizinhas if id(ps[i]) in trocas}
        for i in casadas(x.fala, ps, vizinhas, som, alheias) & vizinhas:
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
    diferencas, trocadas = [], set()
    for passo, i0, i1, j0, j1 in passos:
        if passo in ("igual", "trocada", "junta"):
            for j in range(j0, j1):
                linha.palavras[dono[j]].fica = True
                pontuacao[dono[j]] = S[i1 - 1][2] or pontuacao.get(dono[j], "")
            if passo == "trocada":
                trocadas.update(dono[j] for j in range(j0, j1))
                diferencas.append({"tipo": "trocada", "roteiro": S[i0][1], "falado": W[j0][1],
                                   "parecido": round(parecido(S[i0][0], W[j0][0]), 2), "token": S[i0][0],
                                   "certeza": linha.palavras[dono[j0]].prob, "indices": [i0]})
        elif passo == "falta":
            faltas[dono[j0] if j0 < len(dono) else len(linha.palavras)] += 1
            diferencas.append({"tipo": "faltando", "roteiro": S[i0][1], "token": S[i0][0], "indices": [i0]})
    for k, w in enumerate(linha.palavras):
        if "$" in w.texto:  # "R$ 1.500" transcrito: o tempo é o do número, e o "reais" é dito depois dele
            faltas[k + 1] += 1

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
        tipo = classificar(corrida, ant, prox, sum(faltas[k:j + 1]) if prox else sum(faltas[k:]), som,
                           duvida=k - 1 in trocadas or j in trocadas)
        for w in corrida:
            if tipo:
                w.corte = tipo
            else:
                w.fica = True
                diferencas.append({"tipo": "a_mais", "falado": w.texto, "token": w.toks[0]})
        k = j
    return diferencas, faltas, pontuacao


def classificar(corrida, ant, prox, faltam, som, duvida=False):
    """Tipo do corte de uma corrida de palavras fora do alinhamento, ou '' se ela fica.

    `faltam`: tokens do roteiro que não foram ditos ali perto (aí a corrida pode ser a fala que a
    transcrição errou, e só sai se tem pausa em volta). `duvida`: uma vizinha é palavra trocada (a
    transcrição errou ali, e a corrida pode ser pedaço da fala certa: "sem truque" ouvido "Sinto o que")."""
    nucleo = [t for w in corrida for t in w.toks if not muleta(t)]
    antes = som.vao(ant, corrida[0]) if ant else 9.0
    depois = som.vao(corrida[-1], prox) if prox else 9.0
    if not nucleo:
        # "e"/"é" curto grudado na fala dos dois lados costuma ser invenção da transcrição (ou o fim de
        # uma palavra): fica. Muleta de verdade tem pausa em volta ou é arrastada ("ééé").
        if max(antes, depois) < 0.06 and corrida[-1].ate - corrida[0].de < 0.3:
            return ""
        # Grudada de um lado só, quase sem som próprio: é o fim (ou o começo) da palavra em que gruda que a
        # transcrição chamou de "e" ("árvo-re" + "e" na pausa da vírgula, "cli-entes" ouvido "e antes": o
        # som não para entre as duas). Também fica. Grudada só na de antes, fica se a palavra termina com o que
        # foi ouvido, ou se não tem nem um vale raso entre as duas (Som.vale) onde cortar: a muleta dita no
        # embalo da palavra ("Os dados é... mostram", "guarda né... a chance") também não tem silêncio antes,
        # e tem a pausa depois; ela sai, cortada nesse vale (editar_linha).
        if (som.proprio(corrida, ant, prox) < 0.15
                and (depois < 0.06 or (antes < 0.06 and (fim_da_palavra(ant, corrida)
                                                         or som.vale(corrida[0]) is None)))):
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
    if faltam == 0 and not duvida and len(corrida) <= 2 and max(antes, depois) >= 0.08:
        vizinhos = ant.toks[-1:] + prox.toks[:1]
        return "repeticao" if any(parecido(t, v) >= 0.5 for t in nucleo for v in vizinhos) else "fora_do_roteiro"
    # Faltando palavra do roteiro ali, a corrida pode ser ela mal transcrita: só sai bem separada.
    if min(antes, depois) >= 0.3:
        return "fora_do_roteiro"
    return ""


def fim_da_palavra(w, corrida):
    """Se o que a transcrição ouviu na corrida pode ser o fim da palavra w partida ("árvo-re" + "e")."""
    ouvido = "".join(re.sub(r"(.)\1+", r"\1", t) for x in corrida for t in x.toks)
    return fonetico(w.toks[-1]).endswith(fonetico(ouvido)) if w.toks and ouvido else False


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

    # O obstáculo vai de onde o som dele começa até onde termina (a transcrição estica a palavra por cima
    # da pausa, e aí ela cortaria o fim ou o começo da fala que fica), nunca além do que a transcrição diz.
    def limite_esq(t):
        return max([lo] + [som.fim(o) for o in obstaculos if o.ate <= t + 0.05 and o.de < t])

    def limite_dir(t):
        return min([hi] + [som.inicio(o) for o in obstaculos if o.de >= t - 0.05 and o.ate > t])

    def embalo(w, seguinte):  # o vale raso entre w e a seguinte, se ela é muleta dita no embalo de w (classificar)
        if seguinte.fica or seguinte.corte != "muleta" or som.vao(w, seguinte) >= 0.06:
            return None
        return som.vale(seguinte)

    pedacos = []  # ((corte, onde a fala começa), (corte, onde a fala termina)) em segundos
    k0 = ficam[0]
    lim = limite_esq(ps[k0].de)
    on = som.onset(ps[k0], lim)
    if sum(faltas[:k0 + 1]):  # falta palavra do roteiro antes da primeira: o som logo antes fica
        on = estender_esq(som, on, max(lim, on - POR_FALTA * sum(faltas[:k0 + 1]) - 0.2))
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
            raso = embalo(A, meio[0])
            if raso is not None and raso - 0.02 > inicio[1]:  # sem silêncio entre A e a muleta: corta no vale
                fim_a, off_a = raso, raso - 0.02
            pedacos.append((inicio, (fim_a, off_a)))
            inicio = (ini_b, on_b)
            continue
        # palavras vizinhas que ficam: o fim de A vai até onde B começa de verdade (a fronteira da
        # transcrição entre as duas erra para os dois lados)
        on_b = som.onset(B, A.de + 0.05)
        off_a = som.offset(A, on_b)
        if sum(faltas[ia + 1:ib + 1]):
            # falta palavra do roteiro aqui: o som do meio pode ser ela. Só encurta silêncio (e respiração).
            for s0, s1 in silencios(som, off_a, on_b, alvo + FOLGA):
                pedacos.append((inicio, (som.quieto(s0 + 0.02, s0 + alvo / 2 + 0.04, s0 + alvo / 2), s0)))
                inicio = (som.quieto(s1 - alvo / 2 - 0.04, s1 - 0.02, s1 - alvo / 2), s1)
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
        off = estender_dir(som, off, min(lim, off + POR_FALTA * sum(faltas[kz + 1:]) + 0.2))
    fim = som.quieto(off + 0.02, max(off + 0.02, min(lim, off + FIM + 0.04)), off + FIM)
    raso = embalo(ps[kz], ps[kz + 1]) if kz + 1 < len(ps) and not sum(faltas[kz + 1:]) else None
    if raso is not None and raso - 0.02 > inicio[1]:  # muleta no embalo da última palavra: corta no vale
        fim, off = raso, raso - 0.02
    pedacos.append((inicio, (fim, off)))
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
        if quieto > quadros(VAO_ESTENDER):
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
        if quieto > quadros(VAO_ESTENDER):
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


def descrever_cortes(linha, trechos, som, outros=()):
    """O que saiu da janela da linha, pedaço por pedaço, com o tipo. `outros`: os trechos das outras linhas
    (a fala dita em cima da tecla que foi para a vizinha não saiu)."""
    ini, fim = min(linha.de, trechos[0][0] / FPS), max(linha.ate, trechos[-1][1] / FPS)
    buracos, t = [], ini
    for a, b in sorted(list(trechos) + [o for o in outros if o[1] / FPS > ini and o[0] / FPS < fim]):
        if a / FPS > t + 1e-6:
            buracos.append((t, a / FPS))
        t = max(t, b / FPS)
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
    """Diferença que muda o que se diz: número, palavra de conteúdo, 'não'. A que a segunda escuta desfez
    (era erro da transcrição) não conta."""
    if d.get("conferida"):
        return False
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
            saida[-1]["indices"] = saida[-1].get("indices", []) + d.get("indices", [])
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
    palavras = transcrever(audio, pasta, assinatura["gravacao"], modelo, som)
    # Palavra inventada em cima de respiração ou silêncio (o small repete a palavra de antes com certeza
    # baixa: "diferentes." sobre a respiração que abre a linha seguinte): sem voz embaixo, não é fala. Só
    # com tempo para julgar: palavra de 20 ms ("30" grudado no "mil") é tempo que a transcrição espremeu.
    palavras = [w for w in palavras if w.prob >= FANTASMA or w.ate - w.de < 0.2
                or np.count_nonzero(som.som[som.q(w.de):som.q(w.ate) + 1]) * PASSO >= 0.05]
    som.preparar(palavras)

    linhas = []
    for lr, t in zip(linhas_roteiro, tempos):
        dentro = [w for w in palavras if t.de <= (w.de + w.ate) / 2 < t.ate]
        linhas.append(Linha(lr.numero, lr.marca, lr.fala, t.de, t.ate, dentro))
    redistribuir(linhas, palavras, som)
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
        outros = [t for x in linhas if x is not linha for t in x.trechos]
        linha.cortes = descrever_cortes(linha, linha.trechos, som, outros)
        linha.diferencas = agrupar(linha.diferencas)
    ouvidas = segunda_escuta(linhas, audio, pasta, assinatura["gravacao"], modelo)

    dados = {"versao": 1, **assinatura, "modelo": modelo, "fps": FPS, "linhas": []}
    for linha in linhas:
        dados["linhas"].append({
            "linha": linha.numero, "marca": linha.marca, "de": linha.de, "ate": linha.ate,
            "trechos": [[round(a / FPS, 4), round(b / FPS, 4)] for a, b in linha.trechos],
            "roteiro": linha.fala,
            "falado": " ".join(w.texto for w in linha.palavras),
            "fica": " ".join(w.texto for w in linha.palavras if w.fica),
            "diferencas": [{k: v for k, v in d.items() if k not in ("token", "indices")}
                           | {"importante": importante(d)}
                           for d in linha.diferencas],
            "cortes": linha.cortes,
        } | ({"segunda_escuta": {"ouvido": ouvidas[linha.numero][0], "bate": ouvidas[linha.numero][1]}}
             if linha.numero in ouvidas else {}))
    destino = pasta / EDICAO
    provisorio = destino.with_name(EDICAO + ".tmp")
    provisorio.write_text(json.dumps(dados, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    guardado = guardar_ajuste(destino, dados)
    os.replace(provisorio, destino)
    ok("\n".join(resumo(pasta, linhas, ouvidas) + ([guardado] if guardado else []) + ([aviso] if aviso else [])))


def guardar_ajuste(destino, dados):
    """O edicao.json de antes vai para edicao-anterior.json se os trechos dele são outros (um ajuste à mão
    não se perde ao rodar o editar de novo). Devolve o aviso para o relatório, ou ''."""
    try:
        velho = json.loads(destino.read_text(encoding="utf-8"))
        iguais = [(x["linha"], x["trechos"]) for x in velho["linhas"]] == [(x["linha"], x["trechos"])
                                                                           for x in dados["linhas"]]
    except FileNotFoundError:
        return ""
    except (ValueError, KeyError, TypeError):
        iguais = False
    if iguais:
        return ""
    anterior = destino.with_name("edicao-anterior.json")
    os.replace(destino, anterior)
    return (f"O {EDICAO} de antes tinha outros trechos (ajuste à mão, ou de outra gravação ou modelo): ficou em "
            f"{relativo(anterior)}. Para voltar a ele: mv {relativo(anterior)} {relativo(destino)}")


def segunda_escuta(linhas, audio, pasta, assinatura, nome):
    """Linha com diferença importante é ouvida de novo: só a fala que fica, com a fala do roteiro como dica.
    A dica desfaz o erro da transcrição ("Aula" por "Olha", "nenhum porcento" por "nem 1%", "otazo" por
    "atraso") e não esconde erro de verdade: dito "três meses", "seis em dez", "16%", "0,28", "50%", "do
    Japão", "150 mil", "menos bagunça" ou sem o "não", com o roteiro certo como dica, o small e o turbo
    escreveram o que foi dito. Marca como conferida a diferença que ela desfez. Devolve {linha: (o que
    ouviu, se bate com o roteiro)}; guarda em .trabalho/."""
    duvidosas = [x for x in linhas if any(importante(d) for d in x.diferencas)
                 and not any(d["tipo"] == "sem_fala" for d in x.diferencas)]
    if not duvidosas or os.environ.get("HUMANIM_SEGUNDA_ESCUTA") == "0":  # 0: os testes do corte não precisam
        return {}
    livre = memoria_livre()
    if nome not in _CARREGADOS and nome == PADRAO and livre is not None and livre < MEMORIA_PADRAO:
        nome = LEVE  # transcrição guardada e pouca memória: o leve também acerta com a dica
    arquivo = trabalho(pasta) / f"segunda-escuta-{os.path.basename(nome.rstrip('/'))}.json"
    try:
        guardado = json.loads(arquivo.read_text(encoding="utf-8"))
        guardado = guardado["linhas"] if guardado.get("assinatura") == assinatura else {}
    except (OSError, ValueError, KeyError, AttributeError):
        guardado = {}

    def chave(x):
        return json.dumps([x.fala, x.trechos])

    faltam = [x for x in duvidosas if chave(x) not in guardado]
    if faltam:
        modelo = carregar_whisper(nome, pasta)
        print(f"ouvindo de novo, com o roteiro como dica, a(s) linha(s) {', '.join(str(x.numero) for x in faltam)} ...",
              flush=True)
        pausa = np.zeros(int(0.15 * SR), np.float32)
        for x in faltam:
            fala = np.concatenate([np.concatenate([audio[int(a / FPS * SR):int(b / FPS * SR)], pausa])
                                   for a, b in x.trechos])
            try:
                trechos, _ = modelo.transcribe(fala, language="pt", initial_prompt=x.fala, beam_size=5,
                                               condition_on_previous_text=False, without_timestamps=True)
                guardado[chave(x)] = " ".join(t.text.strip() for t in trechos)
            except Exception as e:  # noqa: BLE001 — falta de memória no meio: vira um ERRO legível
                raise Erro(falha_do_modelo(*modelo.humanim, pasta, e)) from None
        arquivo.write_text(json.dumps({"assinatura": assinatura, "linhas": guardado}, ensure_ascii=False),
                           encoding="utf-8")
    saida = {}
    for x in duvidosas:
        ouvido = guardado[chave(x)]
        S, W = tokens(x.fala), [(t, bruto, True) for t, bruto, _ in tokens(ouvido)]
        restam, certas = [], set()
        for passo, i0, i1, j0, j1 in alinhar(S, W):
            if passo in ("igual", "junta"):
                certas.update(range(i0, i1))
            elif passo == "trocada":
                restam.append({"tipo": "trocada", "roteiro": S[i0][1], "falado": W[j0][1], "token": S[i0][0],
                               "parecido": parecido(S[i0][0], W[j0][0])})
            elif passo == "falta":
                restam.append({"tipo": "faltando", "roteiro": S[i0][1], "token": S[i0][0]})
            elif passo == "sobra" and not muleta(W[j0][0]):
                restam.append({"tipo": "a_mais", "falado": W[j0][1], "token": W[j0][0]})
        bate = not any(importante(d) for d in restam)
        # A diferença da primeira escuta que a segunda desfez é da transcrição: com a linha batendo, todas; e,
        # uma a uma, a palavra do roteiro que a segunda ouviu certa. A que só a segunda erra também não pede
        # regravar (ela às vezes pula um pedaço da fala: "busca gulosa", que a primeira ouviu).
        for d in x.diferencas:
            if bate or (d.get("indices") and set(d["indices"]) <= certas):
                d["conferida"] = True
        saida[x.numero] = (ouvido, bate)
    return saida


def resumo(pasta, linhas, ouvidas=None):
    antes = sum(x.ate - x.de for x in linhas)
    depois = sum((b - a) / FPS for x in linhas for a, b in x.trechos)
    contagem = {}
    for x in linhas:
        for c in x.cortes:
            contagem[c["tipo"]] = contagem.get(c["tipo"], 0) + 1
    cortes = ", ".join(f"{n} {NOMES[t][n > 1]}" for t, n in sorted(contagem.items(), key=lambda i: list(NOMES).index(i[0])))
    texto = [f"{relativo(pasta / EDICAO)}: fala de {antes:.1f}s para {depois:.1f}s ({depois - antes:+.1f}s), "
             f"{len(linhas)} linhas. Cortes: {cortes or 'nenhum'}."]
    regravar, pequenas, ouvidas = [], [], ouvidas or {}
    for x in linhas:
        dif = x.diferencas
        if any(importante(d) for d in dif):
            regravar.append(f"  linha {x.numero}: {'; '.join(frase(d) for d in dif if importante(d))}"
                            + (f' (ouvida de novo, com o roteiro como dica: "{ouvidas[x.numero][0]}")'
                               if x.numero in ouvidas else ""))
        elif x.numero in ouvidas:
            pequenas.append(f"{x.numero} ({'; '.join(frase(d) for d in dif)}: ouvida de novo, com o roteiro como "
                            f"dica, {'bate' if ouvidas[x.numero][1] else 'as palavras em dúvida batem'})")
        elif dif:
            pequenas.append(f"{x.numero} ({'; '.join(frase(d) for d in dif)})")
    if regravar:
        texto.append("A fala difere do roteiro (palavra trocada ou faltando; confira e decida se regrava):")
        texto += regravar
        texto.append(f"Para regravar: humanim gravar {relativo(pasta / 'roteiro.md')} (o roteiro inteiro, da linha 1: "
                     f"uma tomada parcial não substitui a completa) e depois este editar de novo. Se a diferença é "
                     f"erro da transcrição (o áudio está certo), siga.")
    else:
        texto.append("A fala bate com o roteiro.")
    if pequenas:
        texto.append(f"Diferenças pequenas, provavelmente da transcrição: linha {', '.join(pequenas)}.")
    texto.append(f"O que saiu e o que ficou, por linha: {relativo(pasta / EDICAO)} (cortes, diferencas).")
    texto.append(f"Próximo, um de cada vez (cada um é pesado): humanim animar {relativo(pasta / 'roteiro.md')} "
                 f"(cenas na duração da fala editada); depois humanim tratar {relativo(pasta / 'gravacao.webm')} "
                 f"(minutos: em segundo plano só para não estourar o tempo limite, sozinho, e espere o OK dele); "
                 f"só então humanim montar {relativo(pasta)}")
    return texto
