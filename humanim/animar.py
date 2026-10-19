"""humanim animar: renderiza as cenas que a IA escreveu, cada uma na duração da sua fala."""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .comum import RAIZ, Erro, ok, pasta_do_video, rodar, trabalho
from .formato import ALTURA, FPS, LARGURA
from .roteiro import ler_roteiro, ler_tempos, quadros

ESTILO = RAIZ / "estilo"
PARALELO = int(os.environ.get("HUMANIM_PARALELO", 3))
# Roda o manim com traceback comum do Python (o padrão é uma caixa do rich, difícil de ler).
MANIM = ("import sys, traceback, manim; "
         "manim.error_console.print_exception = lambda *a, **k: traceback.print_exc(); "
         "from manim.__main__ import main; main()")


def contar_quadros(video):
    saida = rodar(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_packets",
                   "-show_entries", "stream=nb_read_packets", "-of", "csv=p=0", video], f"ffprobe em {video.name}")
    try:
        return int(saida.strip().split(",")[0])
    except ValueError:
        raise Erro(f"não consegui contar os quadros de {video.name}: {saida.strip()[:100]}")


def assinatura(cena, linha):
    """Muda quando muda algo que altera o clipe: a cena, cenas/comum.py, o estilo, a marca ou a fala."""
    h = hashlib.sha256()
    for arq in (ESTILO / "estilo.py", cena.parent / "comum.py", cena):
        h.update(arq.read_bytes() if arq.exists() else b"-")
    h.update(f"{linha.marca}|{linha.fala}|{os.environ.get('HUMANIM_DEPURAR', '')}".encode())
    return h.hexdigest()[:16]


def explicar_falha(stderr, cena):
    """Última linha do traceback e onde, dentro de cenas/, a cena quebrou."""
    linhas = [t for t in stderr.strip().splitlines() if t.strip()]
    erro = linhas[-1].strip().rstrip(".") if linhas else "o manim saiu sem mensagem"
    locais = [(f, n) for f, n in re.findall(r'File "([^"]+)", line (\d+)', stderr) if Path(f).parent == cena.parent]
    onde = f"cenas/{Path(locais[-1][0]).name}:{locais[-1][1]}" if locais else f"cenas/{cena.name}"
    dica = ""
    if "latex" in stderr.lower():
        dica = " Aqui não tem LaTeX: troque MathTex/Tex (e o que usa LaTeX por baixo) por Text; veja as armadilhas na skill cenas."
    return f"a cena quebrou em {onde}: {erro}.{dica}"


def renderizar(cena, linha, alvo, media):
    shutil.rmtree(media, ignore_errors=True)
    media.mkdir(parents=True)
    caminho = [str(ESTILO), str(cena.parent)] + [p for p in os.environ.get("PYTHONPATH", "").split(os.pathsep) if p]
    env = dict(os.environ, PYTHONPATH=os.pathsep.join(caminho), PYTHONDONTWRITEBYTECODE="1",
               HUMANIM_DURACAO=f"{alvo / FPS:.6f}", HUMANIM_MARCA=linha.marca, HUMANIM_FALA=linha.fala)
    cmd = [sys.executable, "-c", MANIM, "render", "-r", f"{LARGURA},{ALTURA}", "--fps", str(FPS),
           "--disable_caching", "--media_dir", str(media), "--progress_bar", "none", "-v", "WARNING",
           "-o", linha.cena, str(cena), "Cena"]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=media, env=env, stdin=subprocess.DEVNULL)
    if r.returncode != 0:
        raise Erro(explicar_falha(r.stderr, cena))
    videos = list(media.glob(f"videos/*/*/{linha.cena}.mp4"))
    if not videos:
        raise Erro(f"o manim não gerou vídeo de cenas/{cena.name}. Fim da saída dele:\n{(r.stdout + r.stderr).strip()[-500:]}")
    return videos[0]


def animar_linha(pasta, linha, alvo, antes):
    """Devolve (estado, mensagem, entrada do render.json); estado é "feita", "igual" ou "erro"."""
    n, nome = linha.numero, linha.cena
    cena, clipe = pasta / "cenas" / f"{nome}.py", pasta / "cenas" / f"{nome}.mp4"
    if not cena.exists():
        return "erro", f"linha {n}: falta cenas/{nome}.py. Escreva a cena com a skill cenas (o que aparece: {linha.descricao}).", None
    entrada = {"hash": assinatura(cena, linha), "quadros": alvo}
    if antes == entrada and clipe.exists():
        return "igual", f"linha {n}: sem mudança, cenas/{nome}.mp4", entrada
    try:
        if not re.search(r"^class Cena\(", cena.read_text(encoding="utf-8"), re.M):
            raise Erro(f"cenas/{nome}.py tem que definir class Cena(CenaHumanim) (veja a skill cenas).")
        media = trabalho(pasta) / "manim" / nome
        bruto = renderizar(cena, linha, alvo, media)
        tem = contar_quadros(bruto)
        if tem > alvo + 1:
            return "erro", (f"linha {n}: a animação tem {tem / FPS:.2f}s, mas a fala tem {alvo / FPS:.2f}s. "
                           f"Sugestão: encurte os run_time/wait de cenas/{nome}.py (tudo tem que caber em self.duracao, "
                           f"que já vale {alvo / FPS:.2f}) ou divida a fala em duas linhas."), None
        # Mais curto: completa com o último quadro parado. Sempre sai com exatamente `alvo` quadros.
        filtro = ["-vf", f"tpad=stop_mode=clone:stop={alvo - tem}"] if tem < alvo else []
        temp = media / f"{nome}.mp4"
        rodar(["ffmpeg", "-nostdin", "-y", "-v", "error", "-i", bruto, *filtro, "-frames:v", alvo, "-an",
               "-c:v", "libx264", "-preset", "fast", "-crf", "16", "-pix_fmt", "yuv420p", "-r", FPS, temp],
              f"ffmpeg ao gravar cenas/{nome}.mp4")
        if contar_quadros(temp) != alvo:
            raise Erro(f"cenas/{nome}.mp4 não saiu com {alvo} quadros. Rode de novo; se repetir, é bug do animar.")
        temp.replace(clipe)
    except Erro as e:
        return "erro", f"linha {n}: {e}", None
    msg = f"linha {n}: cenas/{nome}.mp4 ({alvo / FPS:.2f}s, {alvo} quadros)"
    if alvo - tem > FPS // 2:
        msg += (f"; a cena acabou em {tem / FPS:.2f}s e o resto ficou parado. "
                f"Termine com self.completar() ou alongue as animações")
    return "feita", msg, entrada


def main(args):
    pasta = pasta_do_video(args.roteiro)
    linhas = ler_roteiro(pasta)
    tempos, estimado = ler_tempos(pasta, linhas)
    alvos = dict(zip((linha.numero for linha in linhas), quadros(tempos)))
    escolhidas = [linha for linha in linhas if linha.tem_animacao]
    if args.linha:
        marcas = {linha.numero: linha.marca for linha in linhas}
        for n in args.linha:
            if n not in marcas:
                raise Erro(f"o roteiro não tem linha {n}: vai de 1 a {len(linhas)}.")
            if marcas[n] == "CARA":
                raise Erro(f"linha {n} é [CARA]: não tem cena para animar.")
        escolhidas = [linha for linha in escolhidas if linha.numero in args.linha]
    if not escolhidas:
        raise Erro("o roteiro não tem linhas [ANIM] nem [CANTO]: não há o que animar.")

    (pasta / "cenas").mkdir(exist_ok=True)
    arquivo = pasta / "cenas" / "render.json"
    cache = json.loads(arquivo.read_text(encoding="utf-8")) if arquivo.exists() else {}
    falhas, renderizadas = [], 0
    with ThreadPoolExecutor(PARALELO) as ex:
        tarefas = [ex.submit(animar_linha, pasta, linha, alvos[linha.numero], cache.get(linha.cena))
                   for linha in escolhidas]
        for linha, tarefa in zip(escolhidas, tarefas):
            estado, msg, entrada = tarefa.result()
            print(f"{'ERRO' if estado == 'erro' else 'OK'} {msg}", flush=True)
            if estado != "erro":
                renderizadas += estado == "feita"
                cache[linha.cena] = entrada
            else:
                falhas.append(linha.numero)
                cache.pop(linha.cena, None)
    arquivo.write_text(json.dumps(cache, indent=1, sort_keys=True) + "\n", encoding="utf-8")

    origem = ("tempos estimados (sem tempos.json; depois de gravar, rode animar de novo)" if estimado
              else "tempos reais do tempos.json")
    if os.environ.get("HUMANIM_DEPURAR"):
        origem += "; COM a zona segura e a do canto desenhadas: rode sem HUMANIM_DEPURAR antes de montar"
    if falhas:
        pedir = " ".join(f"--linha {n}" for n in falhas)
        raise Erro(f"{len(falhas)} de {len(escolhidas)} cena(s) falharam, linha(s) {falhas}, com {origem}. "
                   f"Corrija e rode: humanim animar roteiro.md {pedir}")
    ok(f"{len(escolhidas)} cena(s) pronta(s), {renderizadas} renderizada(s) e {len(escolhidas) - renderizadas} "
       f"sem mudança, com {origem}. Confira com: humanim frames cenas/linha_NN.mp4")
