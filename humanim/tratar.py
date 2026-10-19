"""humanim tratar: tira o fundo da gravação com o Robust Video Matting (local, na CPU).

Lê gravacao.webm, passa quadro a quadro no RVM e escreve gravacao-tratada.webm
(VP9 com canal alfa) com o áudio original. A linha do tempo é a mesma da gravação:
o segundo t da tratada é o segundo t da original, como no tempos.json.
"""
import json
import subprocess
import time
import urllib.request
from pathlib import Path

import numpy as np

from .comum import RAIZ, Erro, duracao, ok, pasta_do_video, rodar, trabalho
from .formato import FPS

MODELO = RAIZ / "modelos" / "rvm_mobilenetv3_fp32.onnx"
URL = "https://github.com/PeterL1n/RobustVideoMatting/releases/download/v1.0.0/rvm_mobilenetv3_fp32.onnx"
# O RVM reduz o quadro para achar a pessoa e depois refina na resolução cheia.
# O autor recomenda que o lado maior reduzido fique perto de 480 px: 0,375 em 1280x720
# (a tabela dele para retrato/meio-corpo), 0,25 em 1920x1080.
LADO_REDUZIDO = 480
SAIDAS = ["fgr", "pha", "r1o", "r2o", "r3o", "r4o"]


def curto(p):
    try:
        return p.relative_to(RAIZ)
    except ValueError:
        return p


def fim(log):
    return "\n".join(log.read_text(errors="replace").strip().splitlines()[-6:])


def carregar_modelo():
    if not MODELO.exists():
        print(f"baixando o modelo de fundo (RVM mobilenetv3, 15 MB) para {curto(MODELO)} ...", flush=True)
        MODELO.parent.mkdir(exist_ok=True)
        parcial = MODELO.with_suffix(".parcial")
        try:
            urllib.request.urlretrieve(URL, parcial)
        except OSError as e:
            raise Erro(f"não consegui baixar o modelo ({e}). Confira a internet ou baixe {URL} para {MODELO}.")
        parcial.replace(MODELO)
    import onnxruntime as ort
    opcoes = ort.SessionOptions()
    opcoes.log_severity_level = 3
    return ort.InferenceSession(str(MODELO), opcoes, providers=["CPUExecutionProvider"])


def main(args):
    pasta = pasta_do_video(args.gravacao)
    dada = Path(args.gravacao) if args.gravacao else None
    entrada = dada.resolve() if dada and dada.suffix else pasta / "gravacao.webm"
    if not entrada.exists():
        raise Erro(f"{curto(entrada)} não existe. Grave primeiro: humanim gravar {curto(pasta)}/roteiro.md")
    if entrada.stem.endswith("-tratada"):
        raise Erro(f"{entrada.name} já é a tratada. Passe a gravação original: humanim tratar {curto(pasta)}/gravacao.webm")
    saida = entrada.with_name(f"{entrada.stem}-tratada.webm")
    if saida.exists() and saida.stat().st_mtime >= entrada.stat().st_mtime:
        ok(f"{curto(saida)} já está tratada (é mais nova que {entrada.name}). Para refazer, apague-a.")
        return

    fluxos = json.loads(rodar(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height",
                               "-of", "json", entrada], f"ffprobe em {entrada.name}"))["streams"]
    video = next((f for f in fluxos if f["codec_type"] == "video"), None)
    if not video:
        raise Erro(f"{curto(entrada)} não tem vídeo. Grave de novo: humanim gravar {curto(pasta)}/roteiro.md")
    tem_audio = any(f["codec_type"] == "audio" for f in fluxos)
    w, h = video["width"], video["height"]
    total = round(duracao(entrada) * FPS)
    sessao = carregar_modelo()

    t = trabalho(pasta)
    parcial = t / f"{saida.stem}.parcial.webm"
    log_dec, log_enc = t / "tratar-decodifica.log", t / "tratar-codifica.log"
    # Quadros RGB planares float (ordem G,B,R) a 30 fps constantes. Sem -copyts, o ffmpeg conta o
    # tempo a partir do início do arquivo (o zero do tempos.json); start_time=0 repete o primeiro
    # quadro se o vídeo começa depois do áudio, o fps tapa os buracos do VFR e o scale segura
    # mudança de resolução no meio da gravação.
    dec = subprocess.Popen(["ffmpeg", "-nostdin", "-v", "error", "-i", entrada, "-map", "0:v:0",
                            "-vf", f"fps={FPS}:start_time=0,scale={w}:{h}",
                            "-f", "rawvideo", "-pix_fmt", "gbrpf32le", "pipe:1"],
                           stdout=subprocess.PIPE, stderr=log_dec.open("w"))
    enc = subprocess.Popen(["ffmpeg", "-nostdin", "-v", "error", "-y",
                            "-f", "rawvideo", "-pix_fmt", "gbrap", "-s", f"{w}x{h}", "-r", str(FPS), "-i", "pipe:0",
                            "-i", entrada, "-map", "0:v", "-map", "1:a?",
                            "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-crf", "30", "-b:v", "0",
                            "-deadline", "realtime", "-cpu-used", "8", "-row-mt", "1",
                            "-c:a", "copy", "-f", "webm", parcial],
                           stdin=subprocess.PIPE, stderr=log_enc.open("w"))
    tamanho = 3 * w * h * 4
    estado = {f"r{i}i": np.zeros((1, 1, 1, 1), np.float32) for i in range(1, 5)}
    razao = np.array([min(1.0, LADO_REDUZIDO / max(w, h))], np.float32)
    n, inicio, aviso = 0, time.monotonic(), time.monotonic()
    try:
        try:
            while len(buf := dec.stdout.read(tamanho)) == tamanho:
                src = np.frombuffer(buf, np.float32).reshape(3, h, w)[[2, 0, 1]][None]
                fgr, pha, *rec = sessao.run(SAIDAS, {"src": src, "downsample_ratio": razao, **estado})
                estado = dict(zip(estado, rec))
                # Cor = fgr: a da pessoa sem o fundo misturado nas bordas (é o que o RVM usa no PNG com alfa).
                gbra = np.concatenate([fgr[0, [1, 2, 0]], pha[0]])
                enc.stdin.write((gbra * 255 + 0.5).astype(np.uint8).tobytes())
                n += 1
                if time.monotonic() - aviso > 15:
                    aviso = time.monotonic()
                    q = n / (aviso - inicio)
                    print(f"  {n}/{total} quadros, {q:.1f} q/s, faltam ~{max(0, total - n) / q:.0f}s", flush=True)
            enc.stdin.close()
        except BrokenPipeError:
            dec.kill()  # o codificador morreu; o log dele diz por quê
        erro_dec, erro_enc = dec.wait(), enc.wait()
        if n == 0:
            raise Erro(f"nenhum quadro saiu de {curto(entrada)}. Grave de novo. ffmpeg:\n{fim(log_dec)}")
        if erro_enc:
            raise Erro(f"o ffmpeg não conseguiu escrever {saida.name}:\n{fim(log_enc)}")
        if erro_dec:
            raise Erro(f"o ffmpeg parou no meio de {curto(entrada)} (quadro {n} de ~{total}):\n{fim(log_dec)}")
    except BaseException:
        dec.kill()
        enc.kill()
        parcial.unlink(missing_ok=True)
        raise
    segundos = time.monotonic() - inicio
    parcial.replace(saida)
    sem_audio = "" if tem_audio else " ATENÇÃO: a gravação não tem áudio."
    ok(f"{curto(saida)}: {n / FPS:.1f}s, {n} quadros a {FPS} fps, com transparência. "
       f"Fundo tirado a {n / segundos:.1f} quadros/s ({segundos:.0f}s).{sem_audio}")
