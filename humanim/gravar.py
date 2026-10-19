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

from .comum import RAIZ, Erro, duracao, ok, pasta_do_video, relativo, rodar, trabalho
from .roteiro import ler_roteiro, ler_tempos

PAGINA = Path(__file__).with_name("teleprompter.html")
PERFIL_CHROME = Path.home() / ".cache" / "humanim" / "chrome"
GUARDAR = ["gravacao.webm", "tempos.json", "gravacao-tratada.webm"]


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
        self.salvando = False  # a janela pode fechar enquanto salva: aí o que vale é o salvar

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
        self.salvando = True
        if not self.fechar() or self.bruto.stat().st_size == 0:
            raise Erro(f"a página mandou o fim, mas a gravação não chegou. {de_novo(self.pasta)}")
        if audio_mudo(self.bruto):
            destino = self.pasta / "anteriores" / f"gravacao-sem-audio-{numero_livre(self.pasta)}.webm"
            os.replace(self.bruto, destino)
            raise Erro(f"a gravação saiu sem som: o microfone está no mudo ou é a entrada errada (guardei em "
                       f"{relativo(destino)}, nada mais mudou). Tire o mudo em Configurações > Som > Entrada "
                       f"(ou pactl set-source-mute @DEFAULT_SOURCE@ 0), confira a barra verde do microfone no "
                       f"teleprompter e grave de novo. {de_novo(self.pasta)}")
        tempos = conferir(dados.get("tempos") or [], self.linhas, self.pasta)
        regravadas = sorted({int(n) for n in dados.get("regravadas") or []} & {t["linha"] for t in tempos})
        if len(tempos) < len(self.linhas) and completa(self.pasta, self.linhas):
            # Parcial (Esc sem querer, tentativa abandonada) não tira do lugar uma gravação completa.
            sufixo = numero_livre(self.pasta)
            final = self.pasta / "anteriores" / f"gravacao-{sufixo}.webm"
            destino_tempos, guardada = final.with_name(f"tempos-{sufixo}.json"), True
        else:
            sufixo, guardada = guardar_anteriores(self.pasta), False
            final, destino_tempos = self.pasta / "gravacao.webm", self.pasta / "tempos.json"

        arrumado = self.bruto.with_name("arrumado.webm")
        try:  # copia sem recodificar só para o webm ganhar duração e índice (fica pulável)
            rodar(["ffmpeg", "-nostdin", "-y", "-v", "error", "-i", self.bruto, "-c", "copy", arrumado], "ffmpeg")
            os.replace(arrumado, final)
            self.bruto.unlink()
        except Erro:
            os.replace(self.bruto, final)
        provisorio = destino_tempos.with_name(destino_tempos.name + ".tmp")
        corpo = ",\n".join(json.dumps(t, ensure_ascii=False) for t in tempos)
        provisorio.write_text(f"[\n{corpo}\n]\n", encoding="utf-8")
        os.replace(provisorio, destino_tempos)
        return resumo(self.pasta, self.linhas, tempos, regravadas, duracao(final), sufixo, guardada)


def audio_mudo(arquivo):
    """Sem trilha de áudio ou com silêncio digital (microfone no mudo no sistema)."""
    r = subprocess.run(["ffmpeg", "-nostdin", "-i", str(arquivo), "-vn", "-af", "volumedetect", "-f", "null", "-"],
                       capture_output=True, text=True)
    pico = [linha.split("max_volume:")[1].split()[0] for linha in r.stderr.splitlines() if "max_volume:" in linha]
    return not pico or pico[0] == "-inf" or float(pico[0]) <= -90


def de_novo(pasta):
    return f"Rode de novo: humanim gravar {relativo(pasta / 'roteiro.md')}"


def conferir(tempos, linhas, pasta):
    """Tempos como vieram da página, conferidos: linhas em ordem a partir da 1, sem voltar no tempo."""
    if not tempos:
        raise Erro(f"nenhuma linha foi falada: nada foi salvo. {de_novo(pasta)}")
    certos, anterior = [], 0.0
    for t, linha in zip(tempos, linhas):
        de, ate = float(t["de"]), float(t["ate"])
        if int(t["linha"]) != linha.numero or de < anterior - 0.001 or ate <= de:
            raise Erro(f"os tempos da linha {linha.numero} vieram errados da página ({de:.2f}s a {ate:.2f}s). "
                       f"{de_novo(pasta)}")
        # A fala vai junto: se o roteiro mudar depois, ler_tempos avisa que o áudio é o texto antigo.
        certos.append({"linha": linha.numero, "de": round(de, 3), "ate": round(ate, 3), "fala": linha.fala})
        anterior = ate
    if len(tempos) > len(linhas):
        raise Erro(f"a página mandou mais linhas que o roteiro tem. {de_novo(pasta)}")
    return certos


def completa(pasta, linhas):
    """Se a pasta já tem uma gravação com todas as linhas do roteiro (a que animar e montar aceitam)."""
    if not (pasta / "gravacao.webm").exists() or not (pasta / "tempos.json").exists():
        return False
    try:
        ler_tempos(pasta, linhas)
    except Erro:
        return False
    return True


def numero_livre(pasta):
    """Primeiro sufixo N sem nenhum arquivo em anteriores/ (fora de .trabalho, que pode ser apagada)."""
    destino = pasta / "anteriores"
    destino.mkdir(exist_ok=True)
    n = 1
    while any((destino / f"{Path(nome).stem}-{n}{Path(nome).suffix}").exists() for nome in GUARDAR):
        n += 1
    return n


def guardar_anteriores(pasta):
    """Move gravação, tempos e gravação tratada antigos para anteriores/, com o mesmo sufixo."""
    velhos = [pasta / nome for nome in GUARDAR if (pasta / nome).exists()]
    if not velhos:
        return None
    n = numero_livre(pasta)
    for v in velhos:
        os.replace(v, pasta / "anteriores" / f"{v.stem}-{n}{v.suffix}")
    return n


def resumo(pasta, linhas, tempos, regravadas, segundos, sufixo, guardada=False):
    try:
        nome = pasta.relative_to(RAIZ)
    except ValueError:
        nome = pasta
    feitas, total = len(tempos), len(linhas)
    arquivos = (f"anteriores/gravacao-{sufixo}.webm e anteriores/tempos-{sufixo}.json" if guardada
                else "gravacao.webm e tempos.json")
    texto = [f"{arquivos} ({segundos:.1f}s) em {nome}/: linhas 1 a {feitas} de {total}"
             + (f", regravadas: {', '.join(map(str, regravadas))}" if regravadas else ", nenhuma regravada")
             + f". Fala de {tempos[0]['de']:.1f}s a {tempos[-1]['ate']:.1f}s."]
    if sufixo and not guardada:
        texto.append(f"A gravação anterior foi para anteriores/ (sufixo -{sufixo}).")
    if segundos + 0.5 < tempos[-1]["ate"]:
        texto.append(f"ATENÇÃO o vídeo tem {segundos:.1f}s, mas a última fala termina em {tempos[-1]['ate']:.1f}s: "
                     f"algum pedaço se perdeu. Confira com humanim frames ou grave de novo.")
    roteiro = relativo(pasta / "roteiro.md")
    if guardada:
        texto[0] = "gravação PARCIAL guardada à parte: " + texto[0]
        texto.append("A gravação completa de antes continua valendo: gravacao.webm e tempos.json não mudaram. "
                     f"Para trocar por uma nova, grave de novo até o fim: humanim gravar {roteiro}")
    elif feitas < total:
        texto[0] = "gravação PARCIAL salva: " + texto[0]
        texto.append(f"Faltam as linhas {feitas + 1} a {total}: animar e montar precisam de todas. "
                     f"Grave de novo até o fim: humanim gravar {roteiro} (esta parcial vai para anteriores/).")
    else:
        texto[0] = "gravação salva: " + texto[0]
        texto.append(f"Próximo: humanim animar {roteiro} (refaz as cenas com os tempos reais), depois "
                     f"humanim tratar {relativo(pasta / 'gravacao.webm')} (em segundo plano), depois "
                     f"humanim montar {relativo(pasta)}")
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
        fim, codigo, texto = None, 200, "ok"
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
                fim = Erro(f"o teleprompter avisou: {corpo.decode(errors='replace')} {de_novo(s.pasta)}")
            elif self.path == "/fechou":
                s.fechou_em = time.monotonic()
            else:
                codigo, texto = 404, "não existe"
        except Erro as e:
            codigo, texto, fim = 500, str(e), e
        except Exception as e:  # noqa: BLE001 — qualquer falha aqui tem de virar ERRO, não travar o CLI
            codigo, texto = 500, repr(e)
            fim = Erro(f"falha no servidor do teleprompter ao tratar {self.path}: {e!r}. {de_novo(s.pasta)}")
        try:
            self.responder(codigo, texto)
        except (BrokenPipeError, ConnectionResetError):
            pass  # a janela fechou antes da resposta: o que foi salvo vale do mesmo jeito
        finally:
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
            if sessao.fechou_em and not sessao.salvando and time.monotonic() - sessao.fechou_em > 5:
                sessao.terminar(Erro(f"a janela do teleprompter fechou antes de salvar: nada foi gravado. "
                                     f"{de_novo(pasta)}"))
    except KeyboardInterrupt:
        raise Erro(f"interrompido (Ctrl+C) antes de salvar: nada foi gravado. {de_novo(pasta)}") from None
    finally:
        servidor.shutdown()
        servidor.server_close()
        sessao.fechar()
    if isinstance(sessao.resultado, Erro):
        raise sessao.resultado
    ok("\n".join(sessao.resultado))
