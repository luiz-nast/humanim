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

from .comum import RAIZ, Erro, contar_quadros, memoria_livre, ok, pasta_do_video, relativo, rodar, trabalho
from .formato import ALTURA, FPS, LARGURA
from .roteiro import EDICAO, ler_roteiro, ler_tempos, quadros

ESTILO = RAIZ / "estilo"
# O que toda cena roda além dela e do comum.py: o estilo, o formato (o canto, a faixa de cima) e o ritmo da
# fala (fala.py: quando cada palavra é dita, que o self.momento usa). Mudou, o clipe muda.
DEPENDENCIAS = (ESTILO / "estilo.py", RAIZ / "humanim" / "formato.py", RAIZ / "humanim" / "fala.py")
# Renders ao mesmo tempo: HUMANIM_PARALELO, ou o que a memória livre deixa (cada render de 1080x1920 passa de
# 700 MB; fica 1,5 GB de folga para o resto da máquina), de 1 a 3.
POR_RENDER, FOLGA, MAXIMO = 0.8, 1.5, 3
PARADA = 1.5  # segundos de imagem parada que já pedem aviso ("algo muda a cada segundo")
# Roda o manim com traceback comum do Python (o padrão é uma caixa do rich, difícil de ler).
MANIM = ("import sys, traceback, manim; "
         "manim.error_console.print_exception = lambda *a, **k: traceback.print_exc(); "
         "from manim.__main__ import main; main()")


def paralelo():
    """(quantos renders ao mesmo tempo, por quê): HUMANIM_PARALELO ou pela memória livre."""
    if os.environ.get("HUMANIM_PARALELO"):
        try:
            return max(1, int(os.environ["HUMANIM_PARALELO"])), "HUMANIM_PARALELO"
        except ValueError:
            raise Erro(f"HUMANIM_PARALELO={os.environ['HUMANIM_PARALELO']} não é um número: use 1, 2 ou 3 "
                       f"(ou tire a variável, e o animar escolhe pela memória livre).") from None
    livre = memoria_livre()
    if livre is None:
        return MAXIMO, ""
    n = max(1, min(MAXIMO, int((livre - FOLGA) / POR_RENDER)))
    return n, f"{livre:.1f} GB de memória livre"


def assinatura(cena, linha):
    """Muda quando muda algo que altera o clipe: a cena, cenas/comum.py, as DEPENDENCIAS, a marca ou a fala."""
    h = hashlib.sha256()
    for arq in (*DEPENDENCIAS, cena.parent / "comum.py", cena):
        h.update(arq.read_bytes() if arq.exists() else b"-")
    h.update(f"{linha.marca}|{linha.fala}|{os.environ.get('HUMANIM_DEPURAR', '')}".encode())
    return h.hexdigest()[:16]


def ler_feitas(pasta):
    """O cenas/render.json: o que o último animar fez de cada cena ({cena: {hash, quadros}})."""
    arquivo = pasta / "cenas" / "render.json"
    try:
        return json.loads(arquivo.read_text(encoding="utf-8")) if arquivo.exists() else {}
    except ValueError:
        return {}


def motivo_da_cena(pasta, linha, pede, feitas):
    """'' se cenas/linha_NN.mp4 é o que o último animar fez da cena atual, com os `pede` quadros da fala;
    senão, o motivo. É a mesma pergunta para a prévia (que avisa) e para o montar (que recusa)."""
    cena, clipe = pasta / "cenas" / f"{linha.cena}.py", pasta / "cenas" / f"{linha.cena}.mp4"
    if not clipe.exists():
        falta = "" if cena.exists() else f" e a própria cena cenas/{linha.cena}.py: escreva-a com a skill cenas"
        return f"falta cenas/{linha.cena}.mp4{falta}"
    if abs((tem := contar_quadros(clipe)) - pede) > 1:
        return f"a animação está desatualizada ({tem} quadros, a fala pede {pede})"
    if not cena.exists() or feitas.get(linha.cena) != {"hash": assinatura(cena, linha), "quadros": pede}:
        return ("o clipe não é da cena atual: a cena, o comum.py, o estilo, o formato, o ritmo da fala ou a fala "
                "mudaram depois do último animar, ele falhou nesta linha, ou ela saiu com HUMANIM_DEPURAR")
    return ""


def por_motivo(problemas):
    """[(linha, motivo)] em texto, uma linha por motivo: 'linhas 1, 2 e 4: o motivo'."""
    juntos = {}
    for n, motivo in problemas:
        juntos.setdefault(motivo, []).append(str(n))
    return "\n".join(f"linha{'s' if len(ns) > 1 else ''} {', '.join(ns[:-1]) + ' e ' if len(ns) > 1 else ''}{ns[-1]}: "
                     f"{motivo}." for motivo, ns in juntos.items())


def paradas(video):
    """Trechos (de, até) em segundos em que a imagem fica parada PARADA segundos ou mais.
    Limiar baixo (-80 dB): um ponto pequeno andando muda pouco a média do quadro, mas não é parada."""
    r = subprocess.run(["ffmpeg", "-nostdin", "-i", str(video), "-vf", f"freezedetect=n=-80dB:d={PARADA}",
                        "-f", "null", "-"], capture_output=True, text=True)
    inicios = [float(x) for x in re.findall(r"freeze_start: ([\d.]+)", r.stderr)]
    fins = [float(x) for x in re.findall(r"freeze_end: ([\d.]+)", r.stderr)]
    return list(zip(inicios, fins + [None] * (len(inicios) - len(fins))))


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
        parado = paradas(temp)
        temp.replace(clipe)
    except Erro as e:
        return "erro", f"linha {n}: {e}", None
    msg = f"linha {n}: cenas/{nome}.mp4 ({alvo / FPS:.2f}s, {alvo} quadros)"
    if parado:
        trechos = ", ".join(f"{de:.1f}s a {(ate if ate is not None else alvo / FPS):.1f}s" for de, ate in parado)
        msg += (f"; ATENÇÃO imagem parada de {trechos}: faça algo mudar ali "
                f"(a próxima animação mais cedo, ou um destaque na palavra que a fala diz ali)")
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
    cache = ler_feitas(pasta)
    falhas, renderizadas = [], 0
    por_vez, motivo = paralelo()
    ex = ThreadPoolExecutor(por_vez)
    tarefas = {linha.cena: ex.submit(animar_linha, pasta, linha, alvos[linha.numero], cache.get(linha.cena))
               for linha in escolhidas}
    try:
        for linha in escolhidas:
            estado, msg, _ = tarefas[linha.cena].result()
            print(f"{'ERRO' if estado == 'erro' else 'OK'} {msg}", flush=True)
            renderizadas += estado == "feita"
            if estado == "erro":
                falhas.append(linha.numero)
    except KeyboardInterrupt:
        ex.shutdown(wait=False, cancel_futures=True)  # as da fila nem começam
        raise
    finally:
        # Anota as que terminaram, mesmo com Ctrl+C: o próximo animar não refaz essas.
        for cena, tarefa in tarefas.items():
            if tarefa.done() and not tarefa.cancelled() and tarefa.exception() is None:
                estado, _, entrada = tarefa.result()
                if estado == "erro":
                    cache.pop(cena, None)
                else:
                    cache[cena] = entrada
        arquivo.write_text(json.dumps(cache, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    ex.shutdown()

    if estimado:
        origem = "tempos estimados (sem tempos.json; depois de gravar e editar, rode animar de novo)"
    elif (pasta / EDICAO).exists():
        origem = "tempos da fala editada (edicao.json)"
    else:
        origem = (f"tempos reais do tempos.json, fala SEM edição (para cortar pausas e muletas: humanim editar "
                  f"{relativo(pasta / 'gravacao.webm')} e animar de novo)")
    if os.environ.get("HUMANIM_DEPURAR"):
        origem += "; COM a zona segura e a do canto desenhadas: rode sem HUMANIM_DEPURAR antes de montar"
    if renderizadas or falhas:
        origem += f"; {min(por_vez, len(escolhidas))} render(s) por vez" + (f" ({motivo})" if motivo else "")
    if falhas:
        pedir = " ".join(f"--linha {n}" for n in falhas)
        raise Erro(f"{len(falhas)} de {len(escolhidas)} cena(s) falharam, linha(s) {falhas}, com {origem}. "
                   f"Corrija e rode: humanim animar {relativo(pasta / 'roteiro.md')} {pedir}")
    ok(f"{len(escolhidas)} cena(s) pronta(s), {renderizadas} renderizada(s) e {len(escolhidas) - renderizadas} "
       f"sem mudança, com {origem}. Confira com: humanim frames {relativo(pasta / 'cenas')}/linha_NN.mp4")
