"""Peças que todos os comandos usam: saída OK/ERRO, pastas e ffmpeg."""
import re
import subprocess
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


class Erro(Exception):
    """Vira uma linha 'ERRO ...' na saída. A mensagem diz onde está e o que fazer."""


def ok(mensagem):
    print(f"OK {mensagem}", flush=True)


def pasta_do_video(caminho=None):
    """A pasta do vídeo: a do arquivo passado, a pasta passada, ou a pasta atual."""
    p = Path(caminho) if caminho else Path.cwd()
    if p.suffix:
        p = p.parent
    p = p.resolve()
    if not (p / "roteiro.md").exists():
        raise Erro(f"{p} não tem roteiro.md. Rode o comando dentro de videos/<slug>/ ou passe um arquivo de lá.")
    return p


def trabalho(pasta):
    """Pasta de arquivos intermediários do vídeo; pode ser apagada a qualquer hora."""
    t = pasta / ".trabalho"
    t.mkdir(exist_ok=True)
    return t


def rodar(cmd, o_que):
    """Roda um comando externo; se falhar, vira Erro com o fim do stderr."""
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True)
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
