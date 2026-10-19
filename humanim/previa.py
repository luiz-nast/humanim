"""humanim previa: o animatic. Animação à esquerda, roteiro passando à direita, antes de gravar."""
import json
import os
import shlex
import shutil
import subprocess
import textwrap
from pathlib import Path

from .comum import Erro, ok, pasta_do_video, rodar, trabalho
from .formato import CANTO, FPS, LARGURA
from .roteiro import ler_roteiro, ler_tempos, quadros

L, A = 540, 960  # meio tamanho: sai rápido e basta para ver
K = L / LARGURA
MODELO = Path(__file__).with_name("previa.html")


def esc(valor):
    """Escapa um valor para dentro do -filter_complex (nível da opção e do grafo)."""
    v = str(valor)
    for c in "\\':":
        v = v.replace(c, "\\" + c)
    for c in "\\'[],;":
        v = v.replace(c, "\\" + c)
    return v


def contar_quadros(clipe):
    try:
        saida = rodar(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_packets",
                       "-show_entries", "stream=nb_read_packets", "-of", "csv=p=0", clipe], "ffprobe")
        return int(saida.strip().split(",")[0])
    except (Erro, ValueError):
        return -1


def conferir(pasta, linha, n):
    """(usa o clipe?, motivo do aviso ou '') de uma linha ANIM/CANTO."""
    py, mp4 = pasta / "cenas" / f"{linha.cena}.py", pasta / "cenas" / f"{linha.cena}.mp4"
    if not mp4.exists():
        return False, f"falta renderizar cenas/{linha.cena}.py" if py.exists() else f"falta escrever cenas/{linha.cena}.py"
    q = contar_quadros(mp4)
    if q != n:
        return False, f"cenas/{linha.cena}.mp4 tem {q} quadros, a fala pede {n} ({n / FPS:.2f} s)"
    if py.exists() and py.stat().st_mtime > mp4.stat().st_mtime:
        return True, f"cenas/{linha.cena}.py mudou depois do .mp4 (a prévia mostra o clipe antigo)"
    return True, ""


def main(args):
    pasta = pasta_do_video(args.pasta)
    linhas = ler_roteiro(pasta)
    tempos, estimado = ler_tempos(pasta, linhas)
    contagens = quadros(tempos)
    t = trabalho(pasta)
    textos = t / "previa"
    shutil.rmtree(textos, ignore_errors=True)
    textos.mkdir()
    fonte = esc(rodar(["fc-match", "-f", "%{file}", "Lato:bold"], "fc-match (fonte Lato)").strip())

    def escrever(nome, tamanho, cor, y, *linhas_texto, x="(w-text_w)/2"):
        """Um drawtext por linha: o drawtext do ffmpeg 8 desenha o '\\n' como um quadradinho."""
        filtros = []
        for i, conteudo in enumerate(linhas_texto):
            if conteudo:
                arquivo = textos / f"{nome}-{i}.txt"
                arquivo.write_text(conteudo, encoding="utf-8")
                filtros.append(f"drawtext=fontfile={fonte}:textfile={esc(arquivo)}:expansion=none:"
                               f"fontsize={tamanho}:fontcolor={cor}:x={x}:y={y}+{i * round(tamanho * 1.4)}")
        return ",".join(filtros)

    entradas, partes, rotulos, avisos, dados, inicio = [], [], [], [], [], 0
    for linha, n in zip(linhas, contagens):
        motivo, usa = "", False
        if linha.tem_animacao:
            usa, motivo = conferir(pasta, linha, n)
            if motivo:
                avisos.append((linha.numero, motivo))
        dados.append({"n": linha.numero, "marca": linha.marca, "descricao": linha.descricao, "fala": linha.fala,
                      "de": round(inicio / FPS, 3), "ate": round((inicio + n) / FPS, 3),
                      "falta": motivo if not usa and linha.tem_animacao else ""})
        inicio += n
        if n <= 0:
            continue
        cena = linha.cena
        if usa:
            entradas += ["-i", pasta / "cenas" / f"{cena}.mp4"]
            f = f"[{len(entradas) // 2 - 1}:v]trim=end_frame={n},setpts=PTS-STARTPTS,scale={L}:{A},setsar=1"
            if linha.marca == "CANTO":
                x, y, w, h = (round(c * K) for c in CANTO)
                f += (f",drawbox={x}:{y}:{w}:{h}:black@0.45:fill,drawbox={x}:{y}:{w}:{h}:white@0.9:3,"
                      + escrever(cena, 34, "white", f"{y + h // 2}-text_h/2", "você", x=f"{x + w // 2}-text_w/2"))
        elif linha.tem_animacao:
            f = (f"color=c=0x1c1414:s={L}x{A}:r={FPS},trim=end_frame={n},"
                 + escrever(f"{cena}-a", 46, "0xff6b6b", 300, "falta animar") + ","
                 + escrever(f"{cena}-b", 26, "0xb8a8a8", 380, f"linha {linha.numero} · {linha.marca}", "",
                            *textwrap.wrap(linha.descricao, 30)[:8]))
        else:
            f = (f"color=c=black:s={L}x{A}:r={FPS},trim=end_frame={n},"
                 + escrever(cena, 110, "0x5a5a5a", "(h-text_h)/2", "VOCÊ"))
        partes.append(f"{f},format=yuv420p[v{len(rotulos)}]")
        rotulos.append(f"[v{len(rotulos)}]")
    if not rotulos:
        raise Erro("todas as linhas têm 0 quadros: confira o tempos.json.")

    grafo = ";".join(partes) + f";{''.join(rotulos)}concat=n={len(rotulos)}:v=1:a=0[saida]"
    video = t / "previa.mp4"
    rodar(["ffmpeg", "-nostdin", "-y", "-v", "error", *entradas, "-filter_complex", grafo, "-map", "[saida]",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "28", "-pix_fmt", "yuv420p", "-g", str(FPS),
           "-movflags", "+faststart", video], "ffmpeg montando a prévia")

    total = inicio / FPS
    pagina = {"titulo": pasta.name, "estimado": estimado, "duracao": round(total, 3),
              "video": f".trabalho/previa.mp4?v={video.stat().st_mtime_ns}", "linhas": dados}
    html = pasta / "previa.html"
    embutido = json.dumps(pagina, ensure_ascii=False).replace("</", "<\\/")
    html.write_text(MODELO.read_text(encoding="utf-8").replace("__DADOS__", embutido), encoding="utf-8")

    aberto = not args.nao_abrir and abrir(html)
    ok(f"prévia em {os.path.relpath(html)} · {len(linhas)} linhas · {total:.1f} s · "
       f"tempos {'estimados (pelo tamanho das falas)' if estimado else 'reais (tempos.json)'}"
       + (" · aberta no navegador" if aberto else "" if args.nao_abrir else f" · abra no navegador: {html.as_uri()}"))
    if avisos:
        print(f"Falta animar {len(avisos)} linha(s):")
        for numero, motivo in avisos:
            print(f"  linha {numero}: {motivo}")
        so = " ".join(f"--linha {numero}" for numero, _ in avisos)
        antes = "Escreva as cenas que faltam e rode" if any("escrever" in m for _, m in avisos) else "Rode"
        print(f"{antes}: humanim animar {shlex.quote(os.path.relpath(pasta / 'roteiro.md'))} {so}")


def abrir(html):
    for programa in ("google-chrome", "xdg-open"):
        if shutil.which(programa):
            subprocess.Popen([programa, html.as_uri()], stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL, start_new_session=True)
            return True
    return False
