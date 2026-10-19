"""humanim montar: junta gravação, tempos e animações em saida.mp4.

O áudio é sempre a voz da gravação; o roteiro só decide a imagem de cada linha.
"""
import json

from .animar import assinatura
from .comum import Erro, duracao, ok, pasta_do_video, relativo, rodar, trabalho
from .formato import ALTURA, CANTO, FPS, LARGURA
from .roteiro import ler_roteiro, ler_tempos, quadros
from .tratar import assinatura as assinatura_gravacao, fonte_da_tratada

BORDA = 4  # borda clara em volta de você no [CANTO], quando a gravação tem fundo
X264 = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS)]
FADE = 0.005  # micro fade nas pontas de cada trecho de áudio, para não estalar


def contar_quadros(arquivo):
    saida = rodar(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_packets",
                   "-show_entries", "stream=nb_read_packets", "-of", "csv=p=0", arquivo],
                  f"contar quadros de {arquivo}")
    return int(saida.strip().split(",")[0])


def conferir_cenas(pasta, linhas, contagens):
    """Toda linha com animação precisa do clipe que o último animar fez da cena atual, com os quadros da fala."""
    arquivo = pasta / "cenas" / "render.json"
    feitas = json.loads(arquivo.read_text(encoding="utf-8")) if arquivo.exists() else {}
    problemas = []
    for linha, pede in zip(linhas, contagens):
        if not linha.tem_animacao:
            continue
        cena, clipe = pasta / "cenas" / f"{linha.cena}.py", pasta / "cenas" / f"{linha.cena}.mp4"
        if not clipe.exists():
            problemas.append((linha.numero, f"falta cenas/{linha.cena}.mp4" + ("" if cena.exists() else
                              f" e a própria cena cenas/{linha.cena}.py: escreva-a com a skill cenas")))
        elif abs((tem := contar_quadros(clipe)) - pede) > 1:
            problemas.append((linha.numero, f"a animação está desatualizada ({tem} quadros, a fala pede {pede})"))
        elif not cena.exists() or feitas.get(linha.cena) != {"hash": assinatura(cena, linha), "quadros": pede}:
            problemas.append((linha.numero, f"cenas/{linha.cena}.mp4 não é da cena atual: a cena, o comum.py, o estilo "
                                            f"ou a fala mudaram depois do último animar, ele falhou nesta linha, "
                                            f"ou ela saiu com HUMANIM_DEPURAR"))
    if problemas:
        texto = "\n".join(f"linha {n}: {p}." for n, p in problemas)
        opcoes = " ".join(f"--linha {n}" for n, _ in problemas)
        raise Erro(f"{texto}\nRode humanim animar {relativo(pasta / 'roteiro.md')} {opcoes}")


def escolher_gravacao(pasta):
    """A gravação tratada (sem fundo) se ela for desta gravacao.webm; senão a original."""
    original, tratada = pasta / "gravacao.webm", pasta / "gravacao-tratada.webm"
    if not original.exists():
        raise Erro(f"falta gravacao.webm em {pasta}. Grave primeiro: humanim gravar {relativo(pasta / 'roteiro.md')}")
    if tratada.exists() and fonte_da_tratada(tratada) == assinatura_gravacao(original):
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
           "-vf", f"fps={FPS}:start_time=0,crop='trunc(min(iw,ih*3/4)/2)*2':'trunc(min(ih,iw*4/3)/2)*2'",
           "-c:v", "ffv1", "-pix_fmt", "yuva420p" if com_alfa else "yuv420p", video],
          f"normalizar o vídeo de {gravacao.name}")
    rodar(["ffmpeg", "-nostdin", "-y", "-v", "error", "-i", pasta / "gravacao.webm", "-map", "0:a:0",
           "-af", "aresample=async=1:first_pts=0,apad=pad_dur=0.5", "-ar", "48000", audio],
          "extrair o áudio de gravacao.webm (ela tem áudio?)")
    return video, audio


def segmento(linha, n, inicio, clipe, video, com_alfa, destino):
    """A imagem de uma linha: exatamente n quadros, a partir do quadro `inicio` da gravação."""
    cmd = ["ffmpeg", "-nostdin", "-y", "-v", "error"]
    if linha.marca == "CARA":
        filtros = [f"color=c=black:s={LARGURA}x{ALTURA}:r={FPS}[base]"]
    else:
        cmd += ["-i", clipe]
        filtros = [f"[0:v]setpts=N/({FPS}*TB),scale={LARGURA}:{ALTURA},setsar=1,tpad=stop_mode=clone:stop=2[base]"]
    saida = "[base]"
    if linha.marca != "ANIM":
        entrada = 0 if linha.marca == "CARA" else 1
        cmd += ["-ss", f"{max(0, inicio - 0.5) / FPS:.6f}", "-i", video]
        if linha.marca == "CARA":
            x, y = 0, 0
            pessoa = f"crop='min(iw,ih*9/16)':'min(ih,iw*16/9)',scale={LARGURA}:{ALTURA}"
        else:
            x, y, largura, altura = CANTO
            pessoa = f"scale={largura}:{altura}"
            if not com_alfa:
                pessoa += f",pad=iw+{2 * BORDA}:ih+{2 * BORDA}:{BORDA}:{BORDA}:color=0xEEEEEE"
                x, y = x - BORDA, y - BORDA
        filtros.append(f"[{entrada}:v]setpts=N/({FPS}*TB),{pessoa},setsar=1,tpad=stop_mode=clone:stop={n}[p]")
        filtros.append(f"[base][p]overlay={x}:{y}[v]")
        saida = "[v]"
    rodar([*cmd, "-filter_complex", ";".join(filtros), "-map", saida, "-frames:v", n, *X264, "-an", destino],
          f"montar a imagem da linha {linha.numero}")


def filtro_audio(tempos, entrada):
    """Os trechos [de, ate] da gravação, na ordem, com micro fades, juntos e com volume normalizado."""
    n = len(tempos)
    partes = [f"[{entrada}:a]asplit={n}" + "".join(f"[s{i}]" for i in range(n))]
    for i, t in enumerate(tempos):
        partes.append(f"[s{i}]atrim=start={t.de:.6f}:end={t.ate:.6f},asetpts=PTS-STARTPTS,"
                      f"afade=t=in:d={FADE},afade=t=out:st={t.duracao - FADE:.6f}:d={FADE}[a{i}]")
    partes.append("".join(f"[a{i}]" for i in range(n))
                  + f"concat=n={n}:v=0:a=1,loudnorm=I=-16:TP=-1.5,aresample=48000[a]")
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
    fim_video, fim_audio = contar_quadros(video) / FPS, duracao(audio) - 0.5
    for t in tempos:
        if t.ate > min(fim_video, fim_audio) + 0.25:
            raise Erro(f"linha {t.linha} termina em {t.ate:.2f}s no tempos.json, mas a gravação tem "
                       f"{min(fim_video, fim_audio):.2f}s. tempos.json não é desta gravação: grave de novo.")

    t = trabalho(pasta)
    segmentos = []
    for linha, tempo, n in zip(linhas, tempos, contagens):
        destino = t / f"seg_{linha.numero:02d}.mp4"
        segmento(linha, n, round(tempo.de * FPS), pasta / "cenas" / f"{linha.cena}.mp4", video, com_alfa, destino)
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
    ok(f"{saida} montado: {total / FPS:.2f}s, {len(linhas)} linhas ({por_marca}), gravação {fundo}.{aviso}\n"
       f"Próximo: humanim frames {relativo(saida)} e olhe as imagens em frames/.")
