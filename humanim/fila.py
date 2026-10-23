"""A fila da máquina: um processo pesado por vez (render do Manim, transcrição, remoção de fundo, montagem).

Nesta máquina (7 GB) pesados juntos já travaram tudo, inclusive vários agentes testando cena ao mesmo tempo.
Quem entra espera a vez num lock de arquivo, que o sistema solta sozinho quando o processo termina (até se
ele morrer). Os filhos herdam a vez por HUMANIM_NA_FILA: o animar renderiza várias cenas de uma vez dentro
da própria vez. Entram: animar, editar, tratar e montar (cli.py) e toda cena ou teste que importa o estilo.
"""
import fcntl
import os
import sys
import time

TRAVA = "/tmp/humanim-fila.lock"  # vazio: /tmp é memória, mas o arquivo não guarda nada
QUEM = "/tmp/humanim-fila.quem"  # o processo que está na vez, para a mensagem de quem espera
_vez = None


def quem_esta():
    try:
        pid = int(open(QUEM).read().split()[0])
        partes = open(f"/proc/{pid}/cmdline", "rb").read().decode(errors="replace").split("\0")
        comando = " ".join(os.path.basename(x) if x.startswith("/") else x for x in partes if x)
        return f"processo {pid}: {comando[:100]}"
    except (OSError, ValueError, IndexError):
        return "outro processo pesado"


def vez():
    """Para o pass_fds dos subprocessos pesados: o filho segura a vez junto, e ela só solta quando o último
    acaba (se o pai morrer no meio, os renders órfãos não deixam outro pesado entrar)."""
    return (_vez.fileno(),) if _vez else ()


def entrar(o_que):
    """Espera a vez e a segura até o processo acabar. Não faz nada se este processo (ou o pai) já está na vez."""
    global _vez
    if _vez or os.environ.get("HUMANIM_NA_FILA"):
        return
    f = open(TRAVA, "a")
    try:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print(f"fila: {o_que} espera a vez ({quem_esta()}). Um pesado por vez nesta máquina; começa sozinho "
              f"quando ele terminar.", file=sys.stderr, flush=True)
        inicio = time.monotonic()
        fcntl.flock(f, fcntl.LOCK_EX)
        print(f"fila: {o_que} na vez, depois de {time.monotonic() - inicio:.0f}s de espera.", file=sys.stderr,
              flush=True)
    _vez = f
    with open(QUEM, "w") as q:
        q.write(f"{os.getpid()}\n")
    os.environ["HUMANIM_NA_FILA"] = str(os.getpid())
