"""humanim gravar: teleprompter no navegador que grava a webcam e anota o tempo de cada linha.

Um servidor local entrega a página e as falas, recebe a gravação aos pedaços
(um por segundo) e, no fim, os tempos. Bloqueia até a página salvar ou cancelar.
"""
import json
import os
import shutil
import subprocess
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .comum import RAIZ, Erro, duracao, ok, pasta_do_video, rodar, trabalho
from .roteiro import ler_roteiro

PAGINA = Path(__file__).with_name("teleprompter.html")
PERFIL_CHROME = Path.home() / ".cache" / "humanim" / "chrome"
GUARDAR = ["gravacao.webm", "tempos.json", "gravacao-tratada.webm"]
DE_NOVO = "Rode de novo: humanim gravar roteiro.md"


class Sessao:
    """O que a página mandou até agora. O servidor escreve; o main espera `fim`."""

    def __init__(self, pasta, linhas):
        self.pasta, self.linhas = pasta, linhas
        self.bruto = trabalho(pasta) / "gravando.webm"
        self.arquivo = None
        self.trava = threading.Lock()
        self.fim = threading.Event()
        self.resultado = None  # linhas do OK, ou um Erro
        self.fechou_em = None

    def terminar(self, resultado):
        if not self.fim.is_set():
            self.resultado = resultado
            self.fim.set()

    def comecar(self):
        with self.trava:
            if self.arquivo:
                self.arquivo.close()
            self.arquivo = open(self.bruto, "wb")

    def anexar(self, pedaco):
        with self.trava:
            if not self.arquivo:
                raise Erro("chegou pedaço de gravação antes do início.")
            self.arquivo.write(pedaco)

    def fechar(self):
        with self.trava:
            if self.arquivo:
                self.arquivo.close()
                self.arquivo = None
                return True
        return False

    def salvar(self, dados):
        if not self.fechar() or self.bruto.stat().st_size == 0:
            raise Erro(f"a página mandou o fim, mas a gravação não chegou. {DE_NOVO}")
        tempos = conferir(dados.get("tempos") or [], self.linhas)
        regravadas = sorted({int(n) for n in dados.get("regravadas") or []} & {t["linha"] for t in tempos})
        sufixo = guardar_anteriores(self.pasta)

        final = self.pasta / "gravacao.webm"
        arrumado = self.bruto.with_name("arrumado.webm")
        try:  # copia sem recodificar só para o webm ganhar duração e índice (fica pulável)
            rodar(["ffmpeg", "-nostdin", "-y", "-v", "error", "-i", self.bruto, "-c", "copy", arrumado], "ffmpeg")
            os.replace(arrumado, final)
            self.bruto.unlink()
        except Erro:
            os.replace(self.bruto, final)
        provisorio = self.pasta / "tempos.json.tmp"
        provisorio.write_text("[\n" + ",\n".join(json.dumps(t) for t in tempos) + "\n]\n", encoding="utf-8")
        os.replace(provisorio, self.pasta / "tempos.json")
        return resumo(self.pasta, self.linhas, tempos, regravadas, duracao(final), sufixo)


def conferir(tempos, linhas):
    """Tempos como vieram da página, conferidos: linhas em ordem a partir da 1, sem voltar no tempo."""
    if not tempos:
        raise Erro(f"nenhuma linha foi falada: nada foi salvo. {DE_NOVO}")
    certos, anterior = [], 0.0
    for t, linha in zip(tempos, linhas):
        de, ate = float(t["de"]), float(t["ate"])
        if int(t["linha"]) != linha.numero or de < anterior - 0.001 or ate <= de:
            raise Erro(f"os tempos da linha {linha.numero} vieram errados da página ({de:.2f}s a {ate:.2f}s). {DE_NOVO}")
        certos.append({"linha": linha.numero, "de": round(de, 3), "ate": round(ate, 3)})
        anterior = ate
    if len(tempos) > len(linhas):
        raise Erro(f"a página mandou mais linhas que o roteiro tem. {DE_NOVO}")
    return certos


def guardar_anteriores(pasta):
    """Move gravação, tempos e gravação tratada antigos para .trabalho/anteriores/, com o mesmo sufixo."""
    velhos = [pasta / nome for nome in GUARDAR if (pasta / nome).exists()]
    if not velhos:
        return None
    destino = trabalho(pasta) / "anteriores"
    destino.mkdir(exist_ok=True)
    n = 1
    while any((destino / f"{v.stem}-{n}{v.suffix}").exists() for v in velhos):
        n += 1
    for v in velhos:
        os.replace(v, destino / f"{v.stem}-{n}{v.suffix}")
    return n


def resumo(pasta, linhas, tempos, regravadas, segundos, sufixo):
    try:
        nome = pasta.relative_to(RAIZ)
    except ValueError:
        nome = pasta
    feitas, total = len(tempos), len(linhas)
    texto = [f"gravacao.webm ({segundos:.1f}s) e tempos.json em {nome}/: linhas 1 a {feitas} de {total}"
             + (f", regravadas: {', '.join(map(str, regravadas))}" if regravadas else ", nenhuma regravada")
             + f". Fala de {tempos[0]['de']:.1f}s a {tempos[-1]['ate']:.1f}s."]
    if sufixo:
        texto.append(f"A gravação anterior foi para .trabalho/anteriores/ (sufixo -{sufixo}).")
    if segundos + 0.5 < tempos[-1]["ate"]:
        texto.append(f"ATENÇÃO o vídeo tem {segundos:.1f}s, mas a última fala termina em {tempos[-1]['ate']:.1f}s: "
                     f"algum pedaço se perdeu. Confira com humanim frames ou grave de novo.")
    if feitas < total:
        texto[0] = "gravação PARCIAL salva: " + texto[0]
        texto.append(f"Faltam as linhas {feitas + 1} a {total}: animar e montar precisam de todas. "
                     "Grave de novo até o fim: humanim gravar roteiro.md (esta parcial vai para .trabalho/anteriores/).")
    else:
        texto[0] = "gravação salva: " + texto[0]
        texto.append("Próximo: humanim animar roteiro.md (refaz as cenas com os tempos reais), depois humanim montar.")
    return texto


class Pagina(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def responder(self, codigo, corpo, tipo="text/plain; charset=utf-8"):
        dados = corpo if isinstance(corpo, bytes) else corpo.encode()
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(dados)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(dados)

    def do_GET(self):
        s = self.server.sessao
        if self.path == "/":
            self.responder(200, PAGINA.read_bytes(), "text/html; charset=utf-8")
        elif self.path == "/falas":
            s.fechou_em = None  # página (re)carregada
            falas = [{"linha": n.numero, "fala": n.fala} for n in s.linhas]
            self.responder(200, json.dumps(falas, ensure_ascii=False), "application/json; charset=utf-8")
        else:
            self.responder(404, "não existe")

    def do_POST(self):
        s = self.server.sessao
        corpo = self.rfile.read(int(self.headers.get("Content-Length") or 0))
        fim = None
        try:
            if self.path == "/inicio":
                s.comecar()
            elif self.path == "/pedaco":
                s.anexar(corpo)
            elif self.path == "/fim":
                fim = s.salvar(json.loads(corpo))
            elif self.path == "/cancelar":
                fim = Erro("cancelado antes de começar: nada foi gravado (arquivos anteriores ficaram como estavam).")
            elif self.path == "/erro":
                fim = Erro(f"o teleprompter avisou: {corpo.decode(errors='replace')} {DE_NOVO}")
            elif self.path == "/fechou":
                s.fechou_em = time.monotonic()
            else:
                return self.responder(404, "não existe")
            self.responder(200, "ok")
        except Erro as e:
            self.responder(500, str(e))
            fim = e
        except Exception as e:  # noqa: BLE001 — qualquer falha aqui tem de virar ERRO, não travar o CLI
            self.responder(500, repr(e))
            fim = Erro(f"falha no servidor do teleprompter ao tratar {self.path}: {e!r}. {DE_NOVO}")
        if fim is not None:
            s.terminar(fim)


def abrir(url):
    """Janela limpa do Chrome (perfil próprio, para lembrar a permissão da câmera); senão o navegador padrão."""
    chrome = shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chromium-browser")
    if not chrome:
        webbrowser.open(url)
        return
    PERFIL_CHROME.mkdir(parents=True, exist_ok=True)
    subprocess.Popen([chrome, f"--user-data-dir={PERFIL_CHROME}", "--no-first-run", "--no-default-browser-check",
                      "--start-maximized", f"--app={url}"],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)


def main(args):
    pasta = pasta_do_video(args.roteiro)
    sessao = Sessao(pasta, ler_roteiro(pasta))
    try:
        servidor = ThreadingHTTPServer(("127.0.0.1", args.porta), Pagina)
    except OSError:
        raise Erro(f"a porta {args.porta} está ocupada (outro humanim gravar aberto?). "
                   f"Feche-o ou use --porta {args.porta + 1}.") from None
    servidor.daemon_threads = True
    servidor.sessao = sessao
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{args.porta}/"
    print(f"teleprompter em {url} esperando a gravação (Esc na página salva; Ctrl+C cancela).", flush=True)
    if not args.nao_abrir:
        abrir(url)
    try:
        while not sessao.fim.wait(0.5):
            if sessao.fechou_em and time.monotonic() - sessao.fechou_em > 5:
                sessao.terminar(Erro(f"a janela do teleprompter fechou antes de salvar: nada foi gravado. {DE_NOVO}"))
    except KeyboardInterrupt:
        raise Erro(f"interrompido (Ctrl+C) antes de salvar: nada foi gravado. {DE_NOVO}") from None
    finally:
        servidor.shutdown()
        servidor.server_close()
        sessao.fechar()
    if isinstance(sessao.resultado, Erro):
        raise sessao.resultado
    ok("\n".join(sessao.resultado))
