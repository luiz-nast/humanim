"""humanim montar: junta gravação, tempos, edição e animações em saida.mp4.

O áudio é sempre a voz da gravação; o roteiro só decide a imagem de cada linha. Com edicao.json, cada
linha é a soma dos seus trechos: vídeo e áudio cortados no mesmo quadro, com um crossfade de 10 ms
na emenda do áudio e, no [CARA], um zoom que alterna a cada pulo para o corte parecer troca de plano.
"""
import subprocess
from dataclasses import dataclass

import numpy as np

from .animar import ler_feitas, motivo_da_cena, por_motivo
from .comum import (AUDIO_DO_ZERO, VIDEO_DO_ZERO, Erro, contar_quadros, duracao, identidade, ok, pasta_do_video,
                    relativo, rodar, trabalho)
from .formato import ALTURA, CANTO, FAIXA_TOPO, FPS, LARGURA, ZOOM, lados_soltos
from .roteiro import EDICAO, ler_roteiro, ler_tempos, quadros
from .tratar import fonte_da_tratada, tratar_rodando

BORDA = 4  # contorno claro nos lados do [CANTO] que não encostam na tela, quando a gravação tem fundo
X264 = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS)]
SR = 48000
CROSSFADE = 480  # amostras (10 ms) de crossfade em cada emenda do áudio: não estala e não muda a duração
SOBRA_AUDIO = 0.5  # segundos de silêncio no fim do wav: o último trecho pode pegar meio crossfade além do fim
# Altura (fração) que fica parada no zoom (formato.ZOOM): a borda de baixo da faixa de cima que a interface do
# app cobre (a que o teleprompter manda deixar a cabeça abaixo). Assim o zoom só cresce para baixo e nada que
# estava fora da faixa entra embaixo dela.
ALTURA_ZOOM = FAIXA_TOPO / ALTURA
FOLGA_CABECA = 0.06  # no [CANTO] sem fundo, folga acima da cabeça (fração da altura da gravação)


@dataclass
class Peca:
    """Um trecho da gravação dentro de uma linha: de que quadro sai, quantos quadros e com que zoom."""
    fonte: int
    quadros: int
    zoom: float = 1.0


def conferir_cenas(pasta, linhas, contagens):
    """Toda linha com animação precisa do clipe que o último animar fez da cena atual, com os quadros da fala."""
    feitas = ler_feitas(pasta)
    problemas = [(linha.numero, motivo) for linha, pede in zip(linhas, contagens)
                 if linha.tem_animacao and (motivo := motivo_da_cena(pasta, linha, pede, feitas))]
    if problemas:
        texto = por_motivo(problemas)
        opcoes = " ".join(f"--linha {n}" for n, _ in problemas)
        raise Erro(f"{texto}\nRode humanim animar {relativo(pasta / 'roteiro.md')} {opcoes}")


def escolher_gravacao(pasta):
    """A gravação tratada (sem fundo) se ela for desta gravacao.webm; senão a original."""
    original, tratada = pasta / "gravacao.webm", pasta / "gravacao-tratada.webm"
    if not original.exists():
        raise Erro(f"falta gravacao.webm em {pasta}. Grave primeiro: humanim gravar {relativo(pasta / 'roteiro.md')}")
    if pid := tratar_rodando(pasta):
        raise Erro(f"o tratar ainda está rodando nesta pasta (processo {pid}): montar agora sairia com o fundo, "
                   f"e são dois processos pesados ao mesmo tempo. Espere o OK dele e rode de novo: "
                   f"humanim montar {relativo(pasta)}")
    if tratada.exists() and fonte_da_tratada(tratada) == identidade(original):
        return tratada, True, ""
    if tratada.exists():
        return original, False, ("\nAtenção: gravacao-tratada.webm não é desta gravacao.webm (é de outra gravação "
                                 "ou de antes dela) e ficou de fora. Para usar sem fundo: "
                                 f"humanim tratar {relativo(original)} e monte de novo.")
    return original, False, ""


def normalizar(pasta, gravacao, com_alfa):
    """Vídeo em 30 fps fixos (recortado 3:4 no centro) e áudio em wav, ambos com t=0 no início do arquivo.

    O webm do navegador tem quadros irregulares e pode não começar no zero; daqui em diante
    o quadro k da gravação é exatamente o instante k/30 do tempos.json.
    """
    t = trabalho(pasta)
    video, audio = t / "gravacao-30fps.mkv", t / "gravacao.wav"
    decodificador = ["-c:v", "libvpx-vp9"] if com_alfa else []  # sem isso o alfa do VP9 some
    rodar(["ffmpeg", "-nostdin", "-y", "-v", "error", *decodificador, "-i", gravacao, "-map", "0:v:0",
           "-vf", f"{VIDEO_DO_ZERO},crop='trunc(min(iw,ih*3/4)/2)*2':'trunc(min(ih,iw*4/3)/2)*2'",
           "-c:v", "ffv1", "-pix_fmt", "yuva420p" if com_alfa else "yuv420p", video],
          f"normalizar o vídeo de {gravacao.name}")
    rodar(["ffmpeg", "-nostdin", "-y", "-v", "error", "-i", pasta / "gravacao.webm", "-map", "0:a:0",
           "-af", f"{AUDIO_DO_ZERO},apad=pad_dur={SOBRA_AUDIO}", "-ar", str(SR), audio],
          "extrair o áudio de gravacao.webm (ela tem áudio?)")
    return video, audio


def planejar(linhas, tempos, contagens):
    """As peças de cada linha. Os quadros de cada trecho saem das fronteiras acumuladas dentro da linha
    (como em quadros()), e a última peça fecha a conta: a linha tem sempre os quadros que quadros() deu.

    Zoom: no [CARA], cada vez que a gravação pula (corte da edição dentro da linha, ou de uma linha
    [CARA] para a seguinte com fala cortada entre elas) o zoom troca entre 100% e ZOOM.
    """
    plano, zoom, anterior, pulos = [], 1.0, None, 0
    for linha, tempo, n in zip(linhas, tempos, contagens):
        pecas, acumulado, usados = [], 0.0, 0
        for k, (a, b) in enumerate(tempo.trechos):
            acumulado += b - a
            q = n - usados if k == len(tempo.trechos) - 1 else round(acumulado * FPS) - usados
            q = max(0, q)
            usados += q
            if linha.marca == "CARA":
                if anterior and anterior[0] == "CARA" and abs(a - anterior[1]) > 0.5 / FPS:
                    zoom, pulos = (1.0 if zoom != 1.0 else ZOOM), pulos + 1
                elif not anterior or anterior[0] != "CARA":
                    zoom = 1.0
            anterior = (linha.marca, b)
            if q:
                pecas.append(Peca(round(a * FPS), q, zoom if linha.marca == "CARA" else 1.0))
        plano.append(pecas)
    return plano, pulos


def dimensoes(video):
    saida = rodar(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                   "-of", "csv=p=0", video], f"ffprobe em {video}")
    w, h = saida.strip().split(",")[:2]
    return int(w), int(h)


def enquadrar_canto(video, indices):
    """Recorte (x, y, largura, altura) da gravação sem fundo para o [CANTO], ou None se não achou você.

    Do peito para cima e ancorado embaixo: o recorte termina na borda de baixo da gravação, então o
    corpo continua até a borda da tela. Em cima, a cabeça com uma folga pequena (na posição mais alta
    que ela chega). Na horizontal, o ombro esquerdo passa um pouco da borda esquerda (corte, não
    encostadinho), sem a cabeça ir para menos de 35% da largura. Quem senta à direita do centro deixa o
    recorte sair da gravação pela direita (lá fica transparente: o segmento estende a imagem antes de
    recortar), para o ombro ainda chegar na borda. Mede a máscara (alfa) em alguns quadros das linhas
    [CANTO].
    """
    w, h = dimensoes(video)
    lw, lh = max(8, w // 4), max(8, h // 4)
    unicos = sorted(set(indices))
    selecao = "+".join(f"eq(n\\,{i})" for i in unicos)
    r = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-c:v", "ffv1", "-i", str(video), "-vf",
                        f"select={selecao},alphaextract,scale={lw}:{lh}", "-fps_mode", "passthrough",
                        "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True)
    if r.returncode != 0 or len(r.stdout) < lw * lh:
        return None
    mascaras = np.frombuffer(r.stdout, np.uint8)[:len(r.stdout) // (lw * lh) * lw * lh].reshape(-1, lh, lw) > 128
    presenca = mascaras.mean(axis=0)
    if not 0.02 < presenca.mean() < 0.95:
        return None  # o tratar não achou ninguém (ou achou tudo): melhor o quadro inteiro
    linhas = np.nonzero(presenca.max(axis=1) >= 0.2)[0]
    if not len(linhas):
        return None
    topo = linhas[0] / lh
    cabeca = presenca[linhas[0]:linhas[0] + max(1, int(lh * 0.15))]
    centro = float((cabeca.sum(axis=0) * np.arange(lw)).sum() / max(cabeca.sum(), 1e-9) / lw)
    embaixo = np.nonzero(presenca[int(lh * 0.92):].mean(axis=0) >= 0.5)[0]
    ombro = embaixo[0] / lw if len(embaixo) else centro
    alt = min(1.0, max(0.5, 1 - topo + FOLGA_CABECA))  # zoom de no máximo 2x
    larg = min(1.0, alt * h * 3 / 4 / w)
    alt = min(1.0, larg * w * 4 / 3 / h)
    x0 = min(max(ombro + 0.05 * larg, centro - 0.5 * larg), centro - 0.35 * larg)  # o ombro passa da borda
    x0 = max(0.0, x0)  # x0 + larg pode passar de 1: o recorte sai pela direita, transparente
    cw, ch = int(larg * w) // 2 * 2, int(alt * h) // 2 * 2
    return int(x0 * w) // 2 * 2, h - ch, cw, ch


def segmento(linha, pecas, clipe, video, com_alfa, recorte, destino):
    """A imagem de uma linha: exatamente sum(quadros) quadros, peça a peça da gravação."""
    n = sum(p.quadros for p in pecas)
    cmd = ["ffmpeg", "-nostdin", "-y", "-v", "error"]
    if linha.marca == "CARA":
        filtros = [f"color=c=black:s={LARGURA}x{ALTURA}:r={FPS}[base]"]
    else:
        cmd += ["-i", clipe]
        filtros = [f"[0:v]setpts=N/({FPS}*TB),scale={LARGURA}:{ALTURA},setsar=1,tpad=stop_mode=clone:stop=2[base]"]
    saida = "[base]"
    if linha.marca != "ANIM":
        primeira = 0 if linha.marca == "CARA" else 1
        if linha.marca == "CARA":
            x, y = 0, 0
        else:
            x, y, largura, altura = CANTO
            esq, cima, dir_, baixo = lados_soltos(*CANTO)
            if com_alfa:
                rx, ry, rw, rh = recorte or (0, 0, 0, 0)
                corte = (f"pad=w='max(iw,{rx + rw})':h=ih:x=0:y=0:color=black@0,crop={rw}:{rh}:{rx}:{ry},"
                         if recorte else "")
                canto = f"{corte}scale={largura}:{altura}"
            else:  # retângulo encostado na tela; contorno só nos lados que ficam soltos
                canto = (f"scale={largura}:{altura},pad=iw+{BORDA * (esq + dir_)}:ih+{BORDA * (cima + baixo)}:"
                         f"{BORDA * esq}:{BORDA * cima}:color=0xEEEEEE")
                x, y = x - BORDA * esq, y - BORDA * cima
        rotulos = []
        for k, p in enumerate(pecas):
            if linha.marca == "CARA":
                z = f"/{p.zoom:g}" if p.zoom != 1.0 else ""
                pessoa = (f"crop=w='min(iw,ih*9/16){z}':h='min(ih,iw*16/9){z}':x='(iw-ow)/2':"
                          f"y='(ih-oh)*{ALTURA_ZOOM}',scale={LARGURA}:{ALTURA}")
            else:
                pessoa = canto
            cmd += ["-ss", f"{max(0, p.fonte - 0.5) / FPS:.6f}", "-i", video]
            filtros.append(f"[{primeira + k}:v]setpts=N/({FPS}*TB),tpad=stop_mode=clone:stop={p.quadros},"
                           f"trim=end_frame={p.quadros},{pessoa},setsar=1[p{k}]")
            rotulos.append(f"[p{k}]")
        if len(rotulos) > 1:
            filtros.append("".join(rotulos) + f"concat=n={len(rotulos)}:v=1:a=0[p]")
        else:
            filtros[-1] = filtros[-1][:-len("[p0]")] + "[p]"
        filtros.append(f"[base][p]overlay={x}:{y}[v]")
        saida = "[v]"
    rodar([*cmd, "-filter_complex", ";".join(filtros), "-map", saida, "-frames:v", n, *X264, "-an", destino],
          f"montar a imagem da linha {linha.numero}")


def filtro_audio(tempos, entrada):
    """Os trechos da gravação, na ordem, emendados com crossfade, e com volume normalizado.

    Cada emenda pega CROSSFADE/2 amostras de cada lado além do trecho e cruza as duas: a duração
    total é exatamente a soma dos trechos (o vídeo não escorrega) e o corte não estala.
    """
    trechos = [(round(a * SR), round(b * SR)) for t in tempos for a, b in t.trechos]
    n, meio = len(trechos), CROSSFADE // 2
    partes = [f"[{entrada}:a]asplit={n}" + "".join(f"[s{i}]" for i in range(n))]
    for i, (a, b) in enumerate(trechos):
        a, b = a - (meio if i > 0 else 0), b + (meio if i < n - 1 else 0)
        partes.append(f"[s{i}]atrim=start_sample={a}:end_sample={b},asetpts=PTS-STARTPTS[t{i}]")
    atual = "[t0]"
    for i in range(1, n):
        partes.append(f"{atual}[t{i}]acrossfade=ns={CROSSFADE}:c1=tri:c2=tri[x{i}]")
        atual = f"[x{i}]"
    total = sum(b - a for a, b in trechos)
    partes.append(f"{atual}afade=t=in:ns={meio},afade=t=out:ss={total - meio}:ns={meio},"
                  f"loudnorm=I=-16:TP=-1.5,aresample={SR}[a]")
    return ";".join(partes)


def main(args):
    pasta = pasta_do_video(args.pasta)
    linhas = ler_roteiro(pasta)
    if not (pasta / "tempos.json").exists():
        raise Erro(f"falta tempos.json em {pasta}. Grave primeiro: humanim gravar {relativo(pasta / 'roteiro.md')}")
    tempos, _ = ler_tempos(pasta, linhas)
    contagens = quadros(tempos)
    curtas = [t.linha for t, n in zip(tempos, contagens) if n < 1]
    if curtas:
        raise Erro(f"linha(s) {curtas} duram menos de um quadro no tempos.json. Grave de novo essas linhas.")
    gravacao, com_alfa, aviso = escolher_gravacao(pasta)
    conferir_cenas(pasta, linhas, contagens)

    video, audio = normalizar(pasta, gravacao, com_alfa)
    fim_video, fim_audio = contar_quadros(video) / FPS, duracao(audio) - SOBRA_AUDIO
    for t in tempos:
        if t.ate > min(fim_video, fim_audio) + 0.25:
            raise Erro(f"linha {t.linha} termina em {t.ate:.2f}s no tempos.json, mas a gravação tem "
                       f"{min(fim_video, fim_audio):.2f}s. tempos.json não é desta gravação: grave de novo.")

    t = trabalho(pasta)
    plano, pulos = planejar(linhas, tempos, contagens)
    no_canto = [p.fonte + k for linha, pecas in zip(linhas, plano) if linha.marca == "CANTO"
                for p in pecas for k in range(0, p.quadros, max(1, p.quadros // 4))]
    recorte = enquadrar_canto(video, no_canto[::max(1, len(no_canto) // 24)]) if com_alfa and no_canto else None
    segmentos = []
    for linha, pecas in zip(linhas, plano):
        destino = t / f"seg_{linha.numero:02d}.mp4"
        segmento(linha, pecas, pasta / "cenas" / f"{linha.cena}.mp4", video, com_alfa, recorte, destino)
        segmentos.append(destino)
    lista = t / "segmentos.txt"
    lista.write_text("".join(f"file '{s}'\n" for s in segmentos), encoding="utf-8")

    provisorio, saida = t / "saida.mp4", pasta / "saida.mp4"
    rodar(["ffmpeg", "-nostdin", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lista, "-i", audio,
           "-filter_complex", filtro_audio(tempos, 1), "-map", "0:v", "-map", "[a]", "-c:v", "copy",
           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", provisorio], "juntar as linhas com o áudio")
    total, feito = sum(contagens), contar_quadros(provisorio)
    if abs(feito - total) > 1:
        raise Erro(f"saida.mp4 saiu com {feito} quadros, esperava {total}. Veja {t}/seg_*.mp4.")
    provisorio.replace(saida)

    por_marca = ", ".join(f"{m} {sum(1 for x in linhas if x.marca == m)}" for m in ("CARA", "ANIM", "CANTO"))
    fundo = "sem fundo (gravacao-tratada.webm)" if com_alfa else "com fundo (gravacao.webm)"
    if com_alfa and recorte is None and any(x.marca == "CANTO" for x in linhas):
        aviso += ("\nAtenção: não achei você na gravação tratada para recortar o [CANTO]; ela entrou inteira. "
                  "Confira nos frames.")
    if (pasta / EDICAO).exists():
        cortes = sum(len(x.trechos) - 1 for x in tempos)
        fala = f"fala editada (edicao.json: {cortes} corte(s) dentro das linhas, {pulos} pulo(s) com zoom no [CARA])"
    else:
        fala = "fala SEM edição"
        aviso += (f"\nAtenção: sem edicao.json, a fala entra como foi gravada (pausas, muletas e repetições "
                  f"junto). Para cortar: humanim editar {relativo(pasta / 'gravacao.webm')} e monte de novo.")
    ok(f"{relativo(saida)} montado: {total / FPS:.2f}s, {len(linhas)} linhas ({por_marca}), gravação {fundo}, "
       f"{fala}.{aviso}\nPróximo: humanim frames {relativo(saida)} e olhe as imagens em frames/.")
