"""Lê roteiro.md e tempos.json: o fio de tudo."""
import json
import re
from dataclasses import dataclass

from .comum import Erro, relativo
from .formato import FPS

MARCA = re.compile(r"^\[(CARA|ANIM|CANTO)(?::\s*([^\]]*))?\]\s*(.*)$")
PALAVRAS_POR_SEGUNDO = 2.5
DURACAO_MINIMA = 1.5


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

    @property
    def duracao(self):
        return self.ate - self.de


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


def ler_tempos(pasta, linhas):
    """Tempos de cada linha e se são estimados.

    Com tempos.json (depois da gravação), são os reais, em segundos da gravação.
    Sem ele, são estimados pelo tamanho da fala, um atrás do outro a partir do zero.
    """
    arquivo = pasta / "tempos.json"
    gravar = f"humanim gravar {relativo(pasta / 'roteiro.md')}"
    if not arquivo.exists():
        tempos, t = [], 0.0
        for linha in linhas:
            d = max(DURACAO_MINIMA, palavras(linha.fala) / PALAVRAS_POR_SEGUNDO)
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
    return tempos, False


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
