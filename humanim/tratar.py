"""humanim tratar: tira o fundo da gravação com o Robust Video Matting (local, na CPU).

Lê gravacao.webm, passa quadro a quadro no RVM e escreve gravacao-tratada.webm
(VP9 com canal alfa) com o áudio original. A linha do tempo é a mesma da gravação:
o segundo t da tratada é o segundo t da original, como no tempos.json.

Só tira o fundo do que a montagem mostra: o miolo 3:4 da imagem (comum.MIOLO_3X4) e os trechos das
linhas [CARA] e [CANTO] (os da edição, se já tem edicao.json). O resto sai transparente, sem passar
no modelo. A tratada guarda quais quadros tratou, e o montar confere antes de usar.
"""
import json
import os
import shutil
import subprocess
import time
import urllib.request
from pathlib import Path

import numpy as np

from .comum import (MIOLO_3X4, RAIZ, VIDEO_DO_ZERO, Erro, duracao, identidade, miolo_3x4, ok, pasta_do_video,
                    relativo, rodar, trabalho)
from . import fila
from .formato import FPS
from .roteiro import ler_roteiro, ler_tempos

MODELO = RAIZ / "modelos" / "rvm_mobilenetv3_fp32.onnx"
URL = "https://github.com/PeterL1n/RobustVideoMatting/releases/download/v1.0.0/rvm_mobilenetv3_fp32.onnx"
# O RVM reduz o quadro para achar a pessoa e depois refina na resolução cheia.
# O autor recomenda que o lado maior reduzido fique perto de 480 px: 0,375 em 1280x720
# (a tabela dele para retrato/meio-corpo), 0,25 em 1920x1080.
LADO_REDUZIDO = 480
SAIDAS = ["fgr", "pha", "r1o", "r2o", "r3o", "r4o"]
ESPERA_REDE = 30  # segundos sem resposta da rede no download do modelo: aí desiste com ERRO, não fica parado
# Quadros antes e depois de cada trecho na tela: o RVM recomeça a memória em cada trecho e leva alguns quadros
# para firmar a máscara, e sobra folga se a edição mexer um pouco num corte.
MARGEM = 15
JUNTA = 2 * FPS  # trechos mais perto que isto viram um só: tratar o buraco custa menos que recomeçar a memória


def fim(log):
    return "\n".join(log.read_text(errors="replace").strip().splitlines()[-6:])


def assinatura(gravacao):
    """Identidade da gravação original (a mesma do edicao.json: comum.identidade). A tratada a guarda, e o
    montar confere antes de usar."""
    return identidade(gravacao)


def tratar_rodando(pasta):
    """O processo do tratar que está rodando nesta pasta, ou None. O tratar anota o dele em .trabalho/tratar.pid
    enquanto roda; o montar confere, para não montar com fundo nem rodar junto."""
    try:
        pid = int((pasta / ".trabalho" / "tratar.pid").read_text())
        comando = Path(f"/proc/{pid}/cmdline").read_bytes()
    except (OSError, ValueError):
        return None
    # o número pode ter ficado de um tratar morto e voltado em outro programa: confere o subcomando
    return pid if b"\0tratar\0" in comando else None


def etiquetas(tratada):
    saida = rodar(["ffprobe", "-v", "error", "-show_entries", "format_tags", "-of", "json", tratada],
                  f"ffprobe em {tratada.name}")
    tags = json.loads(saida).get("format", {}).get("tags", {})
    return {k.lower(): v for k, v in tags.items()}


def fonte_da_tratada(tratada):
    """A assinatura da original que a tratada guardou ('' se não tem: tratada de outra versão)."""
    return etiquetas(tratada).get("humanim_fonte", "")


def cobertura(tratada):
    """Os quadros da gravação de que a tratada tirou o fundo, [(de, ate)] com o ate de fora, ou None se foram
    todos (a tratada que não diz é de antes do tratar parcial, que tratava tudo)."""
    marcado = etiquetas(tratada).get("humanim_quadros", "")
    if not marcado or marcado == "tudo":
        return None
    return [tuple(int(x) for x in faixa.split("-")) for faixa in marcado.split(",") if faixa]


def descobertos(cobertas, precisa):
    """Os intervalos de `precisa` que não cabem inteiros num dos de `cobertas` (None cobre tudo)."""
    if cobertas is None:
        return []
    return [(a, b) for a, b in precisa if not any(x <= a and b <= y for x, y in cobertas)]


def na_tela(pasta, total):
    """Os quadros da gravação em que você aparece no vídeo: os trechos das linhas [CARA] e [CANTO] (os da
    edição, se já tem edicao.json), com MARGEM de cada lado, juntando os que ficam perto. None: sem roteiro
    ou sem tempos.json desta pasta, trata tudo."""
    if not (pasta / "roteiro.md").exists() or not (pasta / "tempos.json").exists():
        return None
    linhas = ler_roteiro(pasta)
    tempos, estimado = ler_tempos(pasta, linhas)  # edicao.json velho para com ERRO: rode o editar antes
    if estimado:
        return None
    faixas = sorted((max(0, round(a * FPS) - MARGEM), min(total, round(b * FPS) + 1 + MARGEM))
                    for linha, tempo in zip(linhas, tempos) if linha.marca != "ANIM" for a, b in tempo.trechos)
    juntas = []
    for a, b in faixas:
        if juntas and a - juntas[-1][1] <= JUNTA:
            juntas[-1][1] = max(juntas[-1][1], b)
        elif b > a:
            juntas.append([a, b])
    return [(a, b) for a, b in juntas]


def carregar_modelo():
    if not MODELO.exists():
        print(f"baixando o modelo de fundo (RVM mobilenetv3, 15 MB) para {relativo(MODELO)} ...", flush=True)
        MODELO.parent.mkdir(exist_ok=True)
        parcial = MODELO.with_suffix(".parcial")
        try:
            with urllib.request.urlopen(URL, timeout=ESPERA_REDE) as r, open(parcial, "wb") as f:
                shutil.copyfileobj(r, f)
        except OSError as e:  # sem rede, rede parada (timeout), disco cheio
            parcial.unlink(missing_ok=True)
            raise Erro(f"não consegui baixar o modelo ({e}). Confira a internet e rode de novo, ou baixe {URL} "
                       f"para {relativo(MODELO)}.") from None
        parcial.replace(MODELO)
    try:
        import onnxruntime as ort
    except ImportError:
        raise Erro("falta o onnxruntime no ambiente do humanim. Instale: "
                   "uv pip install -p .venv/bin/python -e .") from None
    opcoes = ort.SessionOptions()
    opcoes.log_severity_level = 3
    try:
        return ort.InferenceSession(str(MODELO), opcoes, providers=["CPUExecutionProvider"])
    except Exception as e:  # noqa: BLE001 — arquivo corrompido ou pela metade: vira um ERRO legível
        raise Erro(f"o modelo de fundo {relativo(MODELO)} não abriu ({str(e)[:200]}): deve estar corrompido. Apague-o "
                   f"e rode de novo, que ele baixa sozinho: rm {relativo(MODELO)}") from None


def main(args):
    pasta = pasta_do_video(args.gravacao)
    marca = trabalho(pasta) / "tratar.pid"
    if (pid := tratar_rodando(pasta)) and pid != os.getpid():
        raise Erro(f"já tem um tratar rodando nesta pasta (processo {pid}). Espere o OK dele.")
    marca.write_text(str(os.getpid()))
    try:
        tratar(pasta, args)
    finally:
        marca.unlink(missing_ok=True)


def tratar(pasta, args):
    dada = Path(args.gravacao) if args.gravacao else None
    entrada = dada.resolve() if dada and dada.suffix else pasta / "gravacao.webm"
    if not entrada.exists():
        raise Erro(f"{relativo(entrada)} não existe. Grave primeiro: humanim gravar {relativo(pasta / 'roteiro.md')}")
    if entrada.stem.endswith("-tratada"):
        raise Erro(f"{entrada.name} já é a tratada. Passe a gravação original: humanim tratar "
                   f"{relativo(pasta / 'gravacao.webm')}")
    saida = entrada.with_name(f"{entrada.stem}-tratada.webm")
    antes = entrada.stat()
    fonte = assinatura(entrada)
    total = round(duracao(entrada) * FPS)
    faixas = na_tela(pasta, total)
    if saida.exists() and fonte_da_tratada(saida) == fonte and (
            cobertura(saida) is None or (faixas is not None and not descobertos(cobertura(saida), faixas))):
        ok(f"{relativo(saida)} já está tratada (é desta {entrada.name} e tem todos os trechos em que você "
           f"aparece). Para refazer, apague-a.")
        return
    if faixas == []:
        ok(f"nada para tratar: o roteiro não tem [CARA] nem [CANTO], então você não aparece no vídeo. "
           f"Próximo: humanim montar {relativo(pasta)}")
        return

    fluxos = json.loads(rodar(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height",
                               "-of", "json", entrada], f"ffprobe em {entrada.name}"))["streams"]
    video = next((f for f in fluxos if f["codec_type"] == "video"), None)
    if not video:
        raise Erro(f"{relativo(entrada)} não tem vídeo. Grave de novo: humanim gravar {relativo(pasta / 'roteiro.md')}")
    tem_audio = any(f["codec_type"] == "audio" for f in fluxos)
    w, h = video["width"], video["height"]
    mw, mh = miolo_3x4(w, h)
    sessao = carregar_modelo()

    t = trabalho(pasta)
    parcial = t / f"{saida.stem}.parcial.webm"
    log_dec, log_enc = t / "tratar-decodifica.log", t / "tratar-codifica.log"
    marcado = "tudo" if faixas is None else ",".join(f"{a}-{b}" for a, b in faixas)
    tratar_n = total if faixas is None else sum(b - a for a, b in faixas)
    # Quadros RGB planares float (ordem G,B,R) a 30 fps constantes. Sem -copyts, o ffmpeg conta o
    # tempo a partir do início do arquivo (o zero do tempos.json); start_time=0 repete o primeiro
    # quadro se o vídeo começa depois do áudio, o fps tapa os buracos do VFR e o scale segura
    # mudança de resolução no meio da gravação.
    dec = subprocess.Popen(["ffmpeg", "-nostdin", "-v", "error", "-i", entrada, "-map", "0:v:0",
                            "-vf", f"{VIDEO_DO_ZERO},scale={w}:{h},{MIOLO_3X4}",
                            "-f", "rawvideo", "-pix_fmt", "gbrpf32le", "pipe:1"],
                           stdout=subprocess.PIPE, stderr=log_dec.open("w"), pass_fds=fila.vez())
    enc = subprocess.Popen(["ffmpeg", "-nostdin", "-v", "error", "-y",
                            "-f", "rawvideo", "-pix_fmt", "gbrap", "-s", f"{mw}x{mh}", "-r", str(FPS), "-i", "pipe:0",
                            "-i", entrada, "-map", "0:v", "-map", "1:a?",
                            "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-crf", "30", "-b:v", "0",
                            "-deadline", "realtime", "-cpu-used", "8", "-row-mt", "1",
                            "-c:a", "copy", "-metadata", f"humanim_fonte={fonte}", "-metadata", f"humanim_quadros={marcado}",
                            "-f", "webm", parcial],
                           stdin=subprocess.PIPE, stderr=log_enc.open("w"), pass_fds=fila.vez())
    tamanho = 3 * mw * mh * 4
    zerado = {f"r{i}i": np.zeros((1, 1, 1, 1), np.float32) for i in range(1, 5)}
    estado = zerado
    vazio = bytes(4 * mw * mh)  # quadro fora da tela: transparente, sem passar no modelo
    # A razão vem do quadro inteiro: a pessoa fica do mesmo tamanho na passada reduzida que o autor recomenda.
    razao = np.array([min(1.0, LADO_REDUZIDO / max(w, h))], np.float32)
    n, feitos, k, inicio, aviso = 0, 0, 0, time.monotonic(), time.monotonic()
    try:
        try:
            while len(buf := dec.stdout.read(tamanho)) == tamanho:
                while faixas and k < len(faixas) and n >= faixas[k][1]:
                    k += 1
                if faixas is not None and not (k < len(faixas) and faixas[k][0] <= n):
                    enc.stdin.write(vazio)
                    n += 1
                    continue
                if faixas is not None and n == faixas[k][0]:
                    estado = zerado  # trecho novo: a memória do RVM é do quadro anterior a ele
                src = np.frombuffer(buf, np.float32).reshape(3, mh, mw)[[2, 0, 1]][None]
                fgr, pha, *rec = sessao.run(SAIDAS, {"src": src, "downsample_ratio": razao, **estado})
                estado = dict(zip(estado, rec))
                # Cor = fgr: a da pessoa sem o fundo misturado nas bordas (é o que o RVM usa no PNG com alfa).
                gbra = np.concatenate([fgr[0, [1, 2, 0]], pha[0]])
                enc.stdin.write((gbra * 255 + 0.5).astype(np.uint8).tobytes())
                n += 1
                feitos += 1
                if time.monotonic() - aviso > 15:
                    aviso = time.monotonic()
                    q = feitos / (aviso - inicio)
                    print(f"  {feitos}/{tratar_n} quadros, {q:.1f} q/s, faltam ~{max(0, tratar_n - feitos) / q:.0f}s",
                          flush=True)
            enc.stdin.close()
        except BrokenPipeError:
            dec.kill()  # o codificador morreu; o log dele diz por quê
        erro_dec, erro_enc = dec.wait(), enc.wait()
        if n == 0:
            raise Erro(f"nenhum quadro saiu de {relativo(entrada)}. Grave de novo. ffmpeg:\n{fim(log_dec)}")
        if erro_enc:
            raise Erro(f"o ffmpeg não conseguiu escrever {saida.name}:\n{fim(log_enc)}")
        if erro_dec:
            raise Erro(f"o ffmpeg parou no meio de {relativo(entrada)} (quadro {n} de ~{total}):\n{fim(log_dec)}")
    except BaseException:
        dec.kill()
        enc.kill()
        parcial.unlink(missing_ok=True)
        raise
    segundos = time.monotonic() - inicio
    # Gravaram de novo enquanto o tratar rodava: esta tratada é da gravação velha, que já saiu do lugar.
    agora = entrada.stat() if entrada.exists() else None
    if not agora or (agora.st_ino, agora.st_size, agora.st_mtime_ns) != (antes.st_ino, antes.st_size, antes.st_mtime_ns):
        parcial.unlink(missing_ok=True)
        raise Erro(f"{relativo(entrada)} mudou enquanto o tratar rodava (gravaram de novo?): nada foi salvo. "
                   f"Rode de novo: humanim tratar {relativo(entrada)}")
    parcial.replace(saida)
    sem_audio = "" if tem_audio else " ATENÇÃO: a gravação não tem áudio."
    so = "" if faixas is None else (f" só de {feitos / FPS:.1f}s, os trechos [CARA] e [CANTO] em que você "
                                    f"aparece,")
    ok(f"{relativo(saida)}: {n / FPS:.1f}s, {n} quadros a {FPS} fps, {mw}x{mh} (o miolo que a montagem usa), "
       f"com transparência. Fundo tirado{so} a {feitos / segundos:.1f} quadros/s ({segundos:.0f}s).{sem_audio} "
       f"Próximo: humanim montar {relativo(pasta)}")
