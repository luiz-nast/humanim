"""Lê roteiro.md, tempos.json e edicao.json: o fio de tudo."""
import hashlib
import json
import re
from dataclasses import dataclass

from .comum import Erro, identidade, relativo
from .fala import fracao_na_fala, ritmo  # noqa: F401 — fracao_na_fala: o estilo e o contar importam daqui
from .formato import FPS

MARCA = re.compile(r"^\[(CARA|ANIM|CANTO)(?::\s*([^\]]*))?\]\s*(.*)$")
DURACAO_MINIMA = 1.5  # segundos: a menor duração estimada de uma fala (fala.ritmo estima o resto)


@dataclass
class Linha:
    numero: int
    marca: str  # CARA, ANIM ou CANTO
    descricao: str  # o que aparece; vazio em CARA
    fala: str

    @property
    def tem_animacao(self):
        return self.marca != "CARA"

    @property
    def cena(self):
        """Nome base dos arquivos da cena desta linha: linha_03."""
        return f"linha_{self.numero:02d}"


@dataclass
class Tempo:
    linha: int
    de: float
    ate: float
    # Pedaços da gravação que ficam, em ordem, em segundos da gravação. Sem edição, um só: [(de, ate)].
    # Com edicao.json, a fala sem pausas, muletas e repetições: de é o início do primeiro, ate o fim do último.
    trechos: list = None

    def __post_init__(self):
        if self.trechos is None:
            self.trechos = [(self.de, self.ate)]

    @property
    def duracao(self):
        """Segundos que a linha ocupa no vídeo final: a soma dos trechos."""
        return sum(b - a for a, b in self.trechos)


def palavras(fala):
    return len(re.findall(r"\w+", fala))


def falado(fala):
    """O que se fala, sem pontuação nem maiúsculas: trocar só uma vírgula não muda a gravação."""
    return re.findall(r"\w+", fala.lower())


def ler_roteiro(pasta):
    texto = (pasta / "roteiro.md").read_text(encoding="utf-8").rstrip("\n")
    if not texto.strip():
        raise Erro("roteiro.md está vazio. Escreva o roteiro com a skill roteiro.")
    linhas = []
    for n, bruta in enumerate(texto.split("\n"), 1):
        m = MARCA.match(bruta.strip())
        if not bruta.strip():
            raise Erro(f"linha {n} do roteiro.md está em branco. Tire a linha: cada linha do arquivo é uma fala.")
        if not m:
            raise Erro(f"linha {n} do roteiro.md não começa com [CARA], [ANIM: …] ou [CANTO: …].")
        marca, descricao, fala = m.group(1), (m.group(2) or "").strip(), m.group(3).strip()
        if marca == "CARA" and m.group(2) is not None:
            raise Erro(f"linha {n}: [CARA] não leva descrição. Use [CARA] fala.")
        if marca != "CARA" and not descricao:
            raise Erro(f"linha {n}: [{marca}] precisa dizer o que aparece: [{marca}: o que aparece] fala.")
        if not fala:
            raise Erro(f"linha {n} não tem fala depois da marca.")
        if "[" in descricao or "]" in fala:
            raise Erro(f"linha {n}: colchete dentro da descrição ou da fala (o primeiro ']' fecha a marca). "
                       f"Troque por parênteses ou aspas.")
        linhas.append(Linha(n, marca, descricao, fala))
    return linhas


def ler_tempos(pasta, linhas, editado=True):
    """Tempos de cada linha e se são estimados.

    Com tempos.json (depois da gravação), são os reais, em segundos da gravação; com edicao.json
    (depois do editar, e se ele é desta gravação), cada linha vira os trechos que a edição deixou.
    Sem tempos.json, são estimados pelo ritmo da fala (sílabas e pausas, veja ritmo), um atrás do outro.
    `editado=False` ignora o edicao.json (o gravar, para saber se a gravação está completa).
    """
    arquivo = pasta / "tempos.json"
    gravar = f"humanim gravar {relativo(pasta / 'roteiro.md')}"
    if not arquivo.exists():
        tempos, t = [], 0.0
        for linha in linhas:
            d = max(DURACAO_MINIMA, ritmo(linha.fala)[1])
            tempos.append(Tempo(linha.numero, round(t, 3), round(t + d, 3)))
            t += d
        return tempos, True
    try:
        dados = {int(d["linha"]): (float(d["de"]), float(d["ate"]), d.get("fala"))
                 for d in json.loads(arquivo.read_text(encoding="utf-8"))}
    except (ValueError, KeyError, TypeError, AttributeError) as e:
        raise Erro(f"tempos.json não dá para ler ({type(e).__name__}: {e}). O formato é "
                   f'[{{"linha": 1, "de": 0.0, "ate": 3.4}}, ...]: conserte o arquivo ou grave de novo: '
                   f"{gravar}") from None
    faltam = [linha.numero for linha in linhas if linha.numero not in dados]
    if faltam:
        raise Erro(f"tempos.json não tem a(s) linha(s) {faltam}: a gravação parou antes ou o roteiro ganhou linhas "
                   f"depois dela. Grave de novo até o fim: {gravar}")
    sobram = sorted(set(dados) - {linha.numero for linha in linhas})
    if sobram:
        raise Erro(f"tempos.json tem linha(s) {sobram} que o roteiro não tem: o roteiro mudou depois da gravação. "
                   f"Grave de novo: {gravar}")
    # O gravar guarda a fala que estava no teleprompter; tempos.json antigos não têm.
    mudou = [n for n in linhas if dados[n.numero][2] is not None and falado(dados[n.numero][2]) != falado(n.fala)]
    if mudou:
        raise Erro(f"a fala da(s) linha(s) {[n.numero for n in mudou]} mudou no roteiro.md depois da gravação, mas o "
                   f'áudio é o texto antigo (linha {mudou[0].numero} gravada: "{dados[mudou[0].numero][2]}"). '
                   f"Volte o texto ou grave de novo: {gravar}")
    tempos = [Tempo(n.numero, *dados[n.numero][:2]) for n in linhas]
    for t in tempos:
        if t.duracao <= 0:
            raise Erro(f"linha {t.linha} do tempos.json termina antes de começar. Grave de novo.")
    if editado and (pasta / EDICAO).exists():
        tempos = ler_edicao(pasta, tempos)
    return tempos, False


EDICAO = "edicao.json"


def assinatura_edicao(pasta):
    """Identidade do que o editar leu: o tempos.json e a gravacao.webm (tamanho, começo e fim do arquivo).

    O edicao.json guarda isto; se a gravação ou os tempos mudam depois, os trechos não valem mais.
    """
    tempos = hashlib.sha256((pasta / "tempos.json").read_bytes()).hexdigest()[:16]
    gravacao = pasta / "gravacao.webm"
    return {"tempos": tempos, "gravacao": identidade(gravacao) if gravacao.exists() else ""}


def ler_edicao(pasta, tempos):
    """Os tempos com os trechos do edicao.json, conferindo que ele é desta gravação e destes tempos."""
    editar = f"humanim editar {relativo(pasta / 'gravacao.webm')}"
    try:
        dados = json.loads((pasta / EDICAO).read_text(encoding="utf-8"))
        assinatura = {"tempos": dados["tempos"], "gravacao": dados["gravacao"]}
        trechos = {int(d["linha"]): [(float(a), float(b)) for a, b in d["trechos"]] for d in dados["linhas"]}
    except (ValueError, KeyError, TypeError, AttributeError) as e:
        raise Erro(f"edicao.json não dá para ler ({type(e).__name__}: {e}). Rode de novo: {editar}") from None
    if assinatura != assinatura_edicao(pasta):
        raise Erro(f"edicao.json é de outra gravação: gravacao.webm ou tempos.json mudaram depois do último editar, "
                   f"e os cortes não valem mais. Rode de novo: {editar}")
    editados = []
    for t in tempos:
        if t.linha not in trechos:
            raise Erro(f"edicao.json não tem a linha {t.linha}. Rode de novo: {editar}")
        lista, anterior = trechos[t.linha], -1.0
        for a, b in lista:
            if b <= a or a < anterior - 1e-6 or a < 0:
                raise Erro(f"edicao.json, linha {t.linha}: o trecho [{a}, {b}] está fora de ordem, invertido ou "
                           f"encavalado com o anterior. Conserte à mão (trechos em ordem, [de, ate] com de < ate) "
                           f"ou rode de novo: {editar}")
            anterior = b
        if not lista:
            raise Erro(f"edicao.json, linha {t.linha}: nenhum trecho. Conserte à mão ou rode de novo: {editar}")
        editados.append(Tempo(t.linha, lista[0][0], lista[-1][1], lista))
    return editados


def quadros(tempos):
    """Quantos quadros cada linha ocupa no vídeo final, na ordem do roteiro.

    O vídeo final é uma linha atrás da outra, cada uma com a duração da sua fala.
    Arredonda as fronteiras acumuladas, não cada linha, para o vídeo não escorregar do áudio.
    """
    contagens, s = [], 0.0
    for t in tempos:
        inicio = round(s * FPS)
        s += t.duracao
        contagens.append(round(s * FPS) - inicio)
    return contagens
