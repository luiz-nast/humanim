"""humanim previa: o animatic. Animação à esquerda, roteiro passando à direita, antes de gravar.

O vídeo sai linha a linha (um ffmpeg por linha, em meio tamanho) e depois as linhas são emendadas sem
recodificar: a memória é a de uma linha só, não cresce com o número de linhas animadas.
"""
import json
import os
import shutil
import subprocess
import textwrap
from pathlib import Path

from .animar import ler_feitas, motivo_da_cena, por_motivo
from .comum import Erro, comandos, contar_quadros, fundo_do_cara, ok, pasta_do_video, relativo, rodar, trabalho
from .formato import CANTO, FPS, LARGURA, lados_soltos
from .roteiro import EDICAO, ler_roteiro, ler_tempos, quadros, vizinha_animada

L, A = 540, 960  # meio tamanho: sai rápido e basta para ver
K = L / LARGURA
MODELO = Path(__file__).with_name("previa.html")
# Iguais em toda linha, para as linhas emendarem sem recodificar (concat com -c copy).
X264 = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "28", "-pix_fmt", "yuv420p", "-r", str(FPS),
        "-g", str(FPS)]


def esc(valor):
    """Escapa um valor para dentro do -filter_complex (nível da opção e do grafo)."""
    v = str(valor)
    for c in "\\':":
        v = v.replace(c, "\\" + c)
    for c in "\\'[],;":
        v = v.replace(c, "\\" + c)
    return v


def conferir(pasta, linha, n, feitas):
    """(usa o clipe?, motivo do aviso ou '') de uma linha ANIM/CANTO. A pergunta é a do montar
    (animar.motivo_da_cena); o clipe que não é da cena atual mas tem os quadros da fala entra, com aviso."""
    try:
        motivo = motivo_da_cena(pasta, linha, n, feitas)
        if not motivo:
            return True, ""
        clipe = pasta / "cenas" / f"{linha.cena}.mp4"
        return clipe.exists() and abs(contar_quadros(clipe) - n) <= 1, motivo
    except Erro as e:  # clipe sem vídeo ou quebrado
        return False, str(e)


def main(args):
    pasta = pasta_do_video(args.pasta)
    linhas = ler_roteiro(pasta)
    tempos, estimado = ler_tempos(pasta, linhas)
    contagens = quadros(tempos)
    feitas = ler_feitas(pasta)
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

    segmentos, avisos, dados, inicio, usadas = [], [], [], 0, {}
    for linha, n in zip(linhas, contagens):
        if linha.tem_animacao:
            usadas[linha.numero] = conferir(pasta, linha, n, feitas)
    for i, (linha, n) in enumerate(zip(linhas, contagens)):
        motivo, usa = "", False
        if linha.tem_animacao:
            usa, motivo = usadas[linha.numero]
            if motivo:
                avisos.append((linha.numero, motivo))
        dados.append({"n": linha.numero, "marca": linha.marca, "descricao": linha.descricao, "fala": linha.fala,
                      "de": round(inicio / FPS, 3), "ate": round((inicio + n) / FPS, 3),
                      "falta": motivo if not usa and linha.tem_animacao else ""})
        inicio += n
        if n <= 0:
            continue
        cena, entrada = linha.cena, []
        if usa:
            entrada = ["-i", pasta / "cenas" / f"{cena}.mp4"]
            f = (f"[0:v]tpad=stop_mode=clone:stop=1,trim=end_frame={n},setpts=PTS-STARTPTS,"
                 f"scale={L}:{A},setsar=1")
            if linha.marca == "CANTO":
                # você no mesmo lugar do montar, encostado na tela: contorno só nos lados soltos
                x, y, w, h = (round(c * K) for c in CANTO)
                esq, cima, dir_, baixo = lados_soltos(*CANTO)
                lados = [(x, y, 3, h)] * esq + [(x, y, w, 3)] * cima + [(x + w - 3, y, 3, h)] * dir_ + \
                        [(x, y + h - 3, w, 3)] * baixo
                f += (f",drawbox={x}:{y}:{w}:{h}:black@0.45:fill,"
                      + "".join(f"drawbox={a}:{b}:{c}:{d}:white@0.9:fill," for a, b, c, d in lados)
                      + escrever(cena, 34, "white", f"{y + h // 2}-text_h/2", "você", x=f"{x + w // 2}-text_w/2"))
        elif linha.tem_animacao:
            f = (f"color=c=0x1c1414:s={L}x{A}:r={FPS},trim=end_frame={n},"
                 + escrever(f"{cena}-a", 46, "0xff6b6b", 300, "falta animar") + ","
                 + escrever(f"{cena}-b", 26, "0xb8a8a8", 380, f"linha {linha.numero} · {linha.marca}", "",
                            *textwrap.wrap(linha.descricao, 30)[:8]))
        else:
            # atrás de você, a animação vizinha parada, como no montar com a gravação sem fundo
            vizinha = vizinha_animada(linhas, i)
            if vizinha and usadas[vizinha[0].numero][0]:
                entrada = [*(["-sseof", "-0.1"] if vizinha[1] == "fim" else []),
                           "-i", pasta / "cenas" / f"{vizinha[0].cena}.mp4"]
                f = (f"[0:v]trim=end_frame=1,scale={L}:{A},setsar=1,{fundo_do_cara(K)},loop=loop=-1:size=1,"
                     f"setpts=N/({FPS}*TB),trim=end_frame={n},")
            else:
                f = f"color=c=black:s={L}x{A}:r={FPS},trim=end_frame={n},"
            f += escrever(cena, 110, "0xb0b0b0", "(h-text_h)/2", "VOCÊ")
        destino = textos / f"seg_{linha.numero:02d}.mp4"
        rodar(["ffmpeg", "-nostdin", "-y", "-v", "error", *entrada, "-filter_complex", f"{f},format=yuv420p[v]",
               "-map", "[v]", "-frames:v", n, *X264, "-an", destino], f"ffmpeg na prévia da linha {linha.numero}")
        segmentos.append(destino)
    if not segmentos:
        raise Erro("todas as linhas têm 0 quadros: confira o tempos.json.")

    lista = textos / "linhas.txt"
    lista.write_text("".join(f"file '{s.name}'\n" for s in segmentos), encoding="utf-8")
    video = t / "previa.mp4"
    rodar(["ffmpeg", "-nostdin", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lista, "-c", "copy",
           "-movflags", "+faststart", video], "ffmpeg emendando as linhas da prévia")

    total = inicio / FPS
    pagina = {"titulo": pasta.name, "estimado": estimado, "duracao": round(total, 3),
              "video": f".trabalho/previa.mp4?v={video.stat().st_mtime_ns}", "linhas": dados}
    html = pasta / "previa.html"
    aberta = t / "previa-aberta"  # existe depois que esta prévia foi aberta no navegador
    primeira = not html.exists() or not aberta.exists()
    embutido = json.dumps(pagina, ensure_ascii=False).replace("</", "<\\/")
    html.write_text(MODELO.read_text(encoding="utf-8").replace("__DADOS__", embutido), encoding="utf-8")

    # Abre só na primeira vez: depois a aba já está no navegador, e abrir de novo empilha abas iguais.
    if args.nao_abrir:
        onde = ""
    elif primeira and abrir(html):
        aberta.touch()
        onde = " · aberta no navegador"
    elif primeira:
        onde = f" · abra no navegador: {html.as_uri()}"
    else:
        onde = f" · recarregue a aba da prévia (F5); se ela foi fechada, abra: {html.as_uri()}"
    origem = ("estimados (pelo tamanho das falas)" if estimado else
              "da fala editada (edicao.json)" if (pasta / EDICAO).exists() else "reais (tempos.json)")
    ok(f"prévia em {os.path.relpath(html)} · {len(linhas)} linhas · {total:.1f} s · tempos {origem}{onde}")
    if avisos:
        print(f"Falta animar {len(avisos)} linha(s) (a prévia mostra o clipe que existe, se tem a duração certa; "
              f"o montar recusa):")
        print(por_motivo(avisos))
        so = " ".join(f"--linha {numero}" for numero, _ in avisos)
        antes = "Escreva as cenas que faltam e rode" if any("skill cenas" in m for _, m in avisos) else "Rode"
        print(comandos(f"{antes}: humanim animar {relativo(pasta / 'roteiro.md')} {so}"), flush=True)


def abrir(html):
    for programa in ("google-chrome", "xdg-open"):
        if shutil.which(programa):
            subprocess.Popen([programa, html.as_uri()], stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL, start_new_session=True)
            return True
    return False
