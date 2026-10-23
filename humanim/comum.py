"""Peças que todos os comandos usam: saída OK/ERRO, pastas, memória e ffmpeg."""
import hashlib
import os
import re
import shlex
import shutil
import subprocess
from pathlib import Path

from . import fila
from .formato import FPS

RAIZ = Path(__file__).resolve().parent.parent

# A linha do tempo de tudo: t=0 é o início do arquivo da gravação (o zero do tempos.json). O webm do navegador
# pode começar o áudio ou o vídeo depois do zero e tem quadros irregulares; estes filtros do ffmpeg trazem os
# dois para essa linha do tempo (o áudio com silêncio no começo, o vídeo repetindo o primeiro quadro).
AUDIO_DO_ZERO = "aresample=async=1:first_pts=0"
VIDEO_DO_ZERO = f"fps={FPS}:start_time=0"
# A parte da gravação que a montagem usa: o miolo 3:4 (540x720 numa webcam de 1280x720). O [CARA] e o [CANTO]
# recortam dele; o tratar só tira o fundo dele.
MIOLO_3X4 = "crop='trunc(min(iw,ih*3/4)/2)*2':'trunc(min(ih,iw*4/3)/2)*2'"


def fundo_do_cara(escala=1.0):
    """Filtro do ffmpeg para o que fica atrás de você no [CARA] sem fundo: o quadro da animação vizinha,
    desfocado e escurecido, para o vídeo não virar um buraco preto e o rosto continuar na frente.
    `escala`: o tamanho do quadro em relação ao vídeo final (a prévia sai em meio tamanho)."""
    return f"gblur=sigma={24 * escala:g},eq=brightness=-0.06:saturation=0.85"


def miolo_3x4(w, h):
    """Largura e altura do MIOLO_3X4 numa gravação w x h (a mesma conta do filtro)."""
    return int(min(w, h * 3 / 4) / 2) * 2, int(min(h, w * 4 / 3) / 2) * 2


class Erro(Exception):
    """Vira uma linha 'ERRO ...' na saída. A mensagem diz onde está e o que fazer."""


_SUBCOMANDO = re.compile(r"(?<![\w./-])humanim (?=(?:novo|contar|animar|previa|gravar|editar|tratar|montar|frames)\b)")
_EXECUTAVEL = []


def comandos(texto):
    """Os comandos 'humanim ...' da mensagem prontos para colar: sem o link do humanim no PATH (o
    ./instalar.sh põe em ~/.local/bin), viram o caminho do .venv/bin/humanim."""
    if not _EXECUTAVEL:
        no_path = shutil.which("humanim")
        _EXECUTAVEL.append("humanim" if no_path else shlex.quote(os.path.relpath(RAIZ / ".venv" / "bin" / "humanim")))
    if _EXECUTAVEL[0] == "humanim":
        return texto
    return _SUBCOMANDO.sub(_EXECUTAVEL[0] + " ", texto)


def ok(mensagem):
    print(f"OK {comandos(mensagem)}", flush=True)


def pasta_do_video(caminho=None):
    """A pasta do vídeo: a do arquivo passado, a pasta passada, ou a pasta atual."""
    p = Path(caminho) if caminho else Path.cwd()
    if p.suffix and not p.is_dir():
        p = p.parent
    p = p.resolve()
    if not (p / "roteiro.md").exists():
        onde = "a pasta atual" if p == Path.cwd().resolve() else relativo(p)
        raise Erro(f"{onde} não tem roteiro.md. Passe a pasta do vídeo ou um arquivo dela, rodando da raiz "
                   f"do humanim (ex.: videos/<slug> ou videos/<slug>/roteiro.md).")
    return p


def relativo(arquivo):
    """Caminho para as dicas da saída: relativo à pasta onde o comando rodou, pronto para colar."""
    return shlex.quote(os.path.relpath(arquivo))


def trabalho(pasta):
    """Pasta de arquivos intermediários do vídeo; pode ser apagada a qualquer hora."""
    t = pasta / ".trabalho"
    t.mkdir(exist_ok=True)
    return t


def rodar(cmd, o_que):
    """Roda um comando externo; se falhar, vira Erro com o fim do stderr."""
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True, pass_fds=fila.vez())
    if r.returncode != 0:
        fim = "\n".join(r.stderr.strip().splitlines()[-6:])
        raise Erro(f"{o_que} falhou:\n{fim}")
    return r.stdout


def duracao(arquivo):
    """Duração em segundos. Webm do navegador às vezes não tem duração no cabeçalho: aí decodifica."""
    saida = rodar(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                   "-of", "default=nw=1:nk=1", arquivo], f"ffprobe em {arquivo}").strip()
    try:
        return float(saida)
    except ValueError:
        r = subprocess.run(["ffmpeg", "-nostdin", "-i", str(arquivo), "-f", "null", "-"],
                           capture_output=True, text=True)
        tempos = re.findall(r"time=(\d+):(\d+):([\d.]+)", r.stderr)
        if not tempos:
            raise Erro(f"não consegui ler a duração de {arquivo}.")
        h, m, s = tempos[-1]
        return int(h) * 3600 + int(m) * 60 + float(s)


def contar_quadros(video):
    """Quantos quadros de vídeo o arquivo tem (contando os pacotes, não pelo cabeçalho)."""
    video = Path(video)
    saida = rodar(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_packets",
                   "-show_entries", "stream=nb_read_packets", "-of", "csv=p=0", video], f"ffprobe em {video.name}")
    try:
        return int(saida.strip().split(",")[0])
    except ValueError:
        raise Erro(f"não consegui contar os quadros de {relativo(video)} (ele tem vídeo?): "
                   f"{saida.strip()[:100] or 'nenhuma trilha de vídeo'}") from None


def identidade(arquivo):
    """Identidade do conteúdo de um arquivo grande: tamanho, 1 MB do começo e 1 MB do fim. Não muda com cópia
    nem com a data; muda se a gravação é outra. É como edicao.json e a gravação tratada sabem de quem são."""
    tamanho, bloco = arquivo.stat().st_size, 1 << 20
    with open(arquivo, "rb") as f:
        inicio = f.read(bloco)
        f.seek(max(0, tamanho - bloco))
        fim = f.read(bloco)
    return hashlib.sha256(str(tamanho).encode() + inicio + fim).hexdigest()[:16]


def memoria_livre():
    """GB de memória disponível (MemAvailable, o 'disponível' do free), ou None fora do Linux."""
    try:
        with open("/proc/meminfo") as f:
            return next(int(x.split()[1]) / 2 ** 20 for x in f if x.startswith("MemAvailable:"))
    except (OSError, StopIteration, ValueError):
        return None
