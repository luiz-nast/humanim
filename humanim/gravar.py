"""humanim gravar: teleprompter no navegador que grava a webcam e anota o tempo de cada linha.

Um servidor local entrega a página e as falas, recebe a gravação aos pedaços (um por segundo), os tempos
a cada Espaço e R e, no fim, os tempos finais. Bloqueia até a página salvar ou cancelar, e vigia a página:
se ela some (aba travada ou morta por falta de memória, janela fechada, Chrome que não abriu), encerra com
ERRO e guarda o que foi gravado como tomada parcial em anteriores/, sem tirar nada do lugar.
"""
import json
import os
import shutil
import signal
import subprocess
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .comum import Erro, duracao, ok, pasta_do_video, relativo, rodar, trabalho
from .formato import ALTURA, FAIXA_TOPO, ZOOM
from .roteiro import EDICAO, ler_roteiro, ler_tempos

PAGINA = Path(__file__).with_name("teleprompter.html")
PERFIL_CHROME = Path.home() / ".cache" / "humanim" / "chrome"
# O que é de uma gravação e vai junto com ela para anteriores/ quando outra a substitui.
GUARDAR = ["gravacao.webm", "tempos.json", "gravacao-tratada.webm", EDICAO]
# O vigia, em segundos. A página manda um pedaço da gravação por segundo e um sinal de vida a cada 5 s.
SEM_PEDACO = 10  # gravando e sem pedaço novo: a aba travou ou morreu (a folga cobre um engasgo da máquina)
SEM_PAGINA = 60  # o Chrome não abriu a página
SEM_SINAL = 120  # aberta, sem gravar e sem sinal (aba escondida tem os timers seguros até 1 por minuto)
FECHOU = 5  # a janela avisou que fechou e não recarregou
CURTA = 1.0  # a linha que tinha acabado de começar quando a gravação parou não entra (como no Esc)


class Sessao:
    """O que a página mandou até agora. O servidor escreve; o main espera `fim` e vigia a página."""

    def __init__(self, pasta, linhas):
        self.pasta, self.linhas = pasta, linhas
        self.bruto = trabalho(pasta) / "gravando.webm"
        self.url = ""
        self.arquivo = None
        self.trava = threading.RLock()  # a tomada, as marcas e o fim: o servidor e o vigia mexem
        self.fim = threading.Event()
        self.resultado = None  # linhas do OK, ou um Erro
        self.encerrando = False  # a tomada final está sendo guardada (fim normal ou não): nada mais entra
        self.marcas = {}  # o último {"tempos", "regravadas"} que a página mandou (a cada Espaço e R)
        self.sinal = self.pedaco = self.fechou_em = None  # time.monotonic do último pedido, pedaço e /fechou
        self.avisos = []  # tomadas guardadas à parte no caminho, para o relatório do fim

    def terminar(self, resultado):
        if not self.fim.is_set():
            self.resultado = resultado
            self.fim.set()

    def comecar(self):
        """/inicio: abre a tomada. Uma tomada ainda aberta (a página recomeçou sem salvar) vai para anteriores/."""
        with self.trava:
            if self.encerrando or self.fim.is_set():
                raise Erro("o humanim já encerrou esta gravação (veja a saída dele).")
            if self.arquivo:
                onde = self.interromper()
                if onde:
                    self.avisos.append(f"A página recomeçou no meio de uma tomada: {minuscula(onde)}")
            if sobra := self.guardar_sobra():  # nunca zera uma tomada
                self.avisos.append(f"Uma tomada bruta que estava em .trabalho/ ficou em {relativo(sobra)} (sem os "
                                   f"tempos das linhas).")
            self.arquivo = open(self.bruto, "wb")
            self.pedaco, self.marcas = time.monotonic(), {}

    def anexar(self, pedaco):
        with self.trava:
            if not self.arquivo:
                if self.encerrando or self.fim.is_set():
                    return  # chegou atrasado: a tomada já foi guardada
                raise Erro("chegou pedaço de gravação antes do início.")
            self.arquivo.write(pedaco)
            self.pedaco = time.monotonic()

    def marcar(self, corpo):
        """/marca: os tempos de agora (a cada Espaço e R). Se a página cair, a tomada é guardada com eles."""
        try:
            dados = json.loads(corpo)
        except ValueError:
            return  # marca estragada não derruba a gravação: vale a anterior
        with self.trava:
            if self.arquivo and isinstance(dados, dict):
                self.marcas = dados

    def fechar(self):
        with self.trava:
            if self.arquivo:
                self.arquivo.close()
                self.arquivo = None

    def tem_tomada(self):
        return self.bruto.exists() and self.bruto.stat().st_size > 0

    def carregou(self):
        """/falas: a página (re)carregou. Se uma tomada estava aberta e a página dela fechou (ou parou de mandar
        pedaços), ela caiu no meio: a tomada vai para anteriores/. Outra aba aberta de olho não mexe em nada."""
        with self.trava:
            caiu = self.fechou_em is not None or (self.pedaco and time.monotonic() - self.pedaco > 2)
            self.fechou_em = None
            if self.arquivo and caiu and not self.encerrando:
                onde = self.interromper()
                if onde:
                    self.avisos.append(f"A página recarregou no meio de uma tomada: {minuscula(onde)}")

    def guardar_sobra(self):
        """O que ficou da tomada em .trabalho/ (de um gravar morto, ou de um fim que falhou) vai para
        anteriores/gravando-N.webm, sem os tempos das linhas, em vez de ser zerado pela próxima tomada.
        Devolve onde ficou, ou None se não havia nada."""
        with self.trava:
            self.fechar()
            if not self.tem_tomada():
                return None
            destino = self.pasta / "anteriores" / f"gravando-{numero_livre(self.pasta)}.webm"
            os.replace(self.bruto, destino)
            return destino

    def sem_som(self):
        """Se a tomada saiu muda, ela vai para anteriores/ e volta a explicação; senão ''."""
        if not audio_mudo(self.bruto):
            return ""
        destino = self.pasta / "anteriores" / f"gravacao-sem-audio-{numero_livre(self.pasta)}.webm"
        os.replace(self.bruto, destino)
        return (f"a gravação saiu sem som: o microfone está no mudo ou é a entrada errada (guardei em "
                f"{relativo(destino)}, nada mais mudou). Tire o mudo em Configurações > Som > Entrada "
                f"(ou pactl set-source-mute @DEFAULT_SOURCE@ 0), confira a barra verde do microfone no "
                f"teleprompter e grave de novo.")

    def arrumar(self):
        """Copia a tomada sem recodificar, só para o webm ganhar duração e índice (fica pulável). Devolve
        (arquivo, segundos); se a cópia falha, o bruto mesmo."""
        arrumado = self.bruto.with_name("arrumado.webm")
        try:
            rodar(["ffmpeg", "-nostdin", "-y", "-v", "error", "-i", self.bruto, "-c", "copy", arrumado], "ffmpeg")
            return arrumado, duracao(arrumado)
        except Erro:
            arrumado.unlink(missing_ok=True)
            return self.bruto, duracao(self.bruto)

    def por_no_lugar(self, fonte, tempos, final, destino_tempos):
        """Escreve os tempos e põe a tomada no lugar. O que pode falhar (disco cheio) vem antes de tirar a
        gravação anterior do lugar; dali em diante são só renomeações. Devolve o sufixo da anterior, se saiu."""
        provisorio = destino_tempos.with_name(destino_tempos.name + ".tmp")
        corpo = ",\n".join(json.dumps(t, ensure_ascii=False) for t in tempos)
        try:
            provisorio.write_text(f"[\n{corpo}\n]\n", encoding="utf-8")
        except OSError:
            provisorio.unlink(missing_ok=True)
            raise
        sufixo = guardar_anteriores(self.pasta) if final.parent == self.pasta else None
        os.replace(fonte, final)
        os.replace(provisorio, destino_tempos)
        self.bruto.unlink(missing_ok=True)
        return sufixo

    def salvar(self, dados):
        """/fim, o fim normal (Esc, ou Espaço na última linha): a tomada vira gravacao.webm e tempos.json. Parcial,
        numa pasta que já tem uma completa, vai para anteriores/ e a completa continua valendo."""
        self.fechar()
        if not self.tem_tomada():
            raise Erro(f"a página mandou o fim, mas a gravação não chegou. {de_novo(self.pasta)}")
        if mudo := self.sem_som():
            raise Erro(f"{mudo} {de_novo(self.pasta)}")
        fonte, segundos = self.arrumar()
        try:
            tempos = conferir(dados.get("tempos"), self.linhas, self.pasta, segundos)
        except Erro:
            if fonte != self.bruto:
                fonte.unlink(missing_ok=True)
            raise
        regravadas = sorted({int(n) for n in dados.get("regravadas") or []} & {t["linha"] for t in tempos})
        if len(tempos) < len(self.linhas) and completa(self.pasta, self.linhas):
            # Parcial (Esc sem querer, tentativa abandonada) não tira do lugar uma gravação completa.
            sufixo = numero_livre(self.pasta)
            final = self.pasta / "anteriores" / f"gravacao-{sufixo}.webm"
            destino_tempos, guardada = final.with_name(f"tempos-{sufixo}.json"), True
        else:
            final, destino_tempos, guardada = self.pasta / "gravacao.webm", self.pasta / "tempos.json", False
        anterior = self.por_no_lugar(fonte, tempos, final, destino_tempos)
        return resumo(self.pasta, self.linhas, tempos, regravadas, segundos, sufixo if guardada else anterior,
                      guardada)

    def interromper(self):
        """Fim fora do normal: a tomada aberta vai para anteriores/ como parcial, com os tempos que a página mandou
        no último Espaço ou R (a linha em que parou termina no fim do arquivo), sem tirar nada do lugar. Devolve a
        frase que diz onde ela ficou ('' se nada foi gravado)."""
        with self.trava:
            self.fechar()
            dados, self.marcas = self.marcas, {}
            if not self.tem_tomada():
                return ""
            try:
                if mudo := self.sem_som():
                    return mudo
                if not dados.get("tempos"):
                    return f"Parou antes da primeira linha: a tomada bruta ficou em {relativo(self.guardar_sobra())}."
                fonte, segundos = self.arrumar()
                tempos = conferir(dados["tempos"], self.linhas, self.pasta, segundos)
                n = numero_livre(self.pasta)
                final = self.pasta / "anteriores" / f"gravacao-{n}.webm"
                destino_tempos = final.with_name(f"tempos-{n}.json")
                self.por_no_lugar(fonte, tempos, final, destino_tempos)
                return (f"Guardei o que foi gravado como tomada parcial, sem mexer em gravacao.webm e tempos.json: "
                        f"{relativo(final)} e {relativo(destino_tempos)} ({segundos:.1f}s, linhas 1 a {len(tempos)} "
                        f"de {len(self.linhas)}).")
            except (Erro, OSError) as e:  # sem conseguir arrumar ou escrever os tempos: a tomada bruta não se perde
                self.bruto.with_name("arrumado.webm").unlink(missing_ok=True)
                sobra = self.guardar_sobra()
                return (f"Não consegui guardar a tomada com os tempos ({e}); ela ficou bruta, sem os tempos das "
                        f"linhas, em {relativo(sobra)}." if sobra else
                        f"Não consegui guardar a tomada ({e}): confira {relativo(self.pasta / 'anteriores')}/.")

    def abortar(self, motivo):
        """Encerra o gravar com ERRO por um fim fora do normal, guardando a tomada aberta."""
        with self.trava:
            if self.encerrando or self.fim.is_set():
                return
            self.encerrando = True
            onde = self.interromper()
            self.terminar(Erro(" ".join([f"{motivo}.", onde or "Nada foi gravado.", *self.avisos,
                                         de_novo(self.pasta)])))

    def fim_da_pagina(self, dados):
        """/fim. Com "parou", o navegador parou a gravação sozinho (câmera ou microfone desligou, erro do
        gravador): é um fim fora do normal, e a tomada vai para anteriores/ como parcial."""
        with self.trava:
            if self.encerrando or self.fim.is_set():
                raise Erro("o humanim já tinha encerrado esta gravação (veja a saída dele).")
            tempos = dados.get("tempos")
            ultima = tempos[-1] if isinstance(tempos, list) and tempos else None
            sem_fim = isinstance(ultima, dict) and ultima.get("ate") is None  # parou no meio dela
            if dados.get("parou") or sem_fim:
                self.marcas = {"tempos": tempos, "regravadas": dados.get("regravadas")}
                linha = len(tempos or [])
                self.abortar(f"a gravação parou sozinha{f' na linha {linha}' if linha else ''} "
                             f"({dados.get('parou') or 'a página mandou a última linha sem fim'})")
                raise self.resultado
            self.encerrando = True
            try:
                return self.salvar(dados) + self.avisos
            except (Erro, OSError) as e:
                if sobra := self.guardar_sobra():  # o fim falhou: a tomada não fica em .trabalho/
                    self.avisos.append(f"O que foi gravado ficou em {relativo(sobra)} (sem os tempos das linhas).")
                texto = (f"não consegui salvar a gravação ({e}): o disco está cheio? Libere espaço (df -h .)."
                         if isinstance(e, OSError) else str(e))
                raise Erro(" ".join([texto, *self.avisos] + ([] if isinstance(e, Erro) else [de_novo(self.pasta)])))

    def cancelar(self):
        """/cancelar: Esc antes da primeira linha. O que foi gravado é só a contagem."""
        with self.trava:
            self.encerrando = True
            self.fechar()
            self.bruto.unlink(missing_ok=True)
            return Erro(" ".join(["cancelado antes de começar: nada foi gravado (arquivos anteriores ficaram como "
                                  "estavam).", *self.avisos]))

    def vigiar(self, agora, inicio, esperar_pagina):
        """O main chama a cada meio segundo: se a página sumiu, encerra com ERRO e guarda a tomada."""
        with self.trava:
            if self.encerrando or self.fim.is_set():
                return
            motivo = ""
            if self.arquivo and agora - self.pedaco > SEM_PEDACO:
                motivo = (f"a gravação parou de chegar ({SEM_PEDACO} s sem nenhum pedaço): a aba do teleprompter "
                          f"travou, ou o sistema a fechou por falta de memória (feche o que estiver pesado)")
            elif self.fechou_em and agora - self.fechou_em > FECHOU:
                motivo = "a janela do teleprompter fechou antes de salvar"
            elif self.sinal is None and esperar_pagina and agora - inicio > SEM_PAGINA:
                motivo = (f"o teleprompter não abriu em {SEM_PAGINA} s: o Chrome não abriu ou não chegou em "
                          f"{self.url}")
            elif self.sinal is not None and agora - self.sinal > SEM_SINAL:
                motivo = f"o teleprompter parou de responder ({SEM_SINAL} s sem sinal): a janela travou ou fechou"
            if motivo:
                self.abortar(motivo)


def audio_mudo(arquivo):
    """Sem trilha de áudio ou com silêncio digital (microfone no mudo no sistema)."""
    r = subprocess.run(["ffmpeg", "-nostdin", "-i", str(arquivo), "-vn", "-af", "volumedetect", "-f", "null", "-"],
                       capture_output=True, text=True)
    pico = [linha.split("max_volume:")[1].split()[0] for linha in r.stderr.splitlines() if "max_volume:" in linha]
    return not pico or pico[0] == "-inf" or float(pico[0]) <= -90


def minuscula(frase):
    return frase[:1].lower() + frase[1:]


def de_novo(pasta):
    return f"Rode de novo: humanim gravar {relativo(pasta / 'roteiro.md')}"


def conferir(tempos, linhas, pasta, fim):
    """Tempos como vieram da página, conferidos: linhas em ordem a partir da 1, sem voltar no tempo. A última
    pode vir sem fim (a gravação parou no meio dela): termina em `fim`, o fim do arquivo, e sai se tinha
    acabado de começar."""
    if not isinstance(tempos, list) or not tempos:
        raise Erro(f"nenhuma linha foi falada: nada foi salvo. {de_novo(pasta)}")
    if len(tempos) > len(linhas):
        raise Erro(f"a página mandou mais linhas que o roteiro tem. {de_novo(pasta)}")
    certos, anterior = [], 0.0
    for i, (t, linha) in enumerate(zip(tempos, linhas)):
        try:
            sem_fim = t.get("ate") is None and i == len(tempos) - 1
            de, ate, numero = float(t["de"]), float(fim if sem_fim else t["ate"]), int(t["linha"])
        except (KeyError, TypeError, ValueError, AttributeError):
            raise Erro(f"os tempos da linha {linha.numero} vieram incompletos da página ({json.dumps(t)[:80]}). "
                       f"{de_novo(pasta)}") from None
        if sem_fim and certos and ate - de < CURTA:
            break  # tinha acabado de passar para ela: nem começou
        if numero != linha.numero or de < anterior - 0.001 or ate <= de:
            raise Erro(f"os tempos da linha {linha.numero} vieram errados da página ({de:.2f}s a {ate:.2f}s). "
                       f"{de_novo(pasta)}")
        # A fala vai junto: se o roteiro mudar depois, ler_tempos avisa que o áudio é o texto antigo.
        certos.append({"linha": linha.numero, "de": round(de, 3), "ate": round(ate, 3), "fala": linha.fala})
        anterior = ate
    return certos


def completa(pasta, linhas):
    """Se a pasta já tem uma gravação com todas as linhas do roteiro (a que animar e montar aceitam)."""
    if not (pasta / "gravacao.webm").exists() or not (pasta / "tempos.json").exists():
        return False
    try:
        ler_tempos(pasta, linhas, editado=False)  # um edicao.json velho não torna a gravação incompleta
    except Erro:
        return False
    return True


def numero_livre(pasta):
    """Primeiro sufixo N que nenhum arquivo de anteriores/ usa (gravacao-N, tempos-N, gravando-N, ...)."""
    destino = pasta / "anteriores"
    destino.mkdir(exist_ok=True)
    n = 1
    while any(destino.glob(f"*-{n}.*")):
        n += 1
    return n


def guardar_anteriores(pasta):
    """Gravação, tempos e gravação tratada antigos vão para anteriores/, com o mesmo sufixo. O edicao.json vai em
    cópia e fica: ele é da gravação antiga, então animar, prévia e montar param com ERRO até o editar rodar de
    novo (sem ele, usariam a fala nova sem edição, sem dizer nada)."""
    velhos = [pasta / nome for nome in GUARDAR if (pasta / nome).exists()]
    if not velhos:
        return None
    n = numero_livre(pasta)
    for v in velhos:
        destino = pasta / "anteriores" / f"{v.stem}-{n}{v.suffix}"
        if v.name == EDICAO:
            shutil.copy2(v, destino)
        else:
            os.replace(v, destino)
    return n


def resumo(pasta, linhas, tempos, regravadas, segundos, sufixo, guardada=False):
    feitas, total = len(tempos), len(linhas)
    arquivos = (f"anteriores/gravacao-{sufixo}.webm e anteriores/tempos-{sufixo}.json" if guardada
                else "gravacao.webm e tempos.json")
    texto = [f"{arquivos} ({segundos:.1f}s) em {relativo(pasta)}/: linhas 1 a {feitas} de {total}"
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
        texto.append(f"Próximo: humanim editar {relativo(pasta / 'gravacao.webm')} (corta pausas, muletas e "
                     f"repetições, e diz se alguma fala saiu diferente do roteiro); ele diz o resto.")
    return texto


def pagina():
    """O teleprompter, com os números do formato.py que ele desenha no retângulo amarelo."""
    formato = json.dumps({"faixa": FAIXA_TOPO / ALTURA, "zoom": ZOOM})
    return PAGINA.read_text(encoding="utf-8").replace("__FORMATO__", formato).encode()


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
        s.sinal = time.monotonic()
        if self.path == "/":
            self.responder(200, pagina(), "text/html; charset=utf-8")
        elif self.path == "/falas":
            s.carregou()
            falas = [{"linha": n.numero, "fala": n.fala} for n in s.linhas]
            self.responder(200, json.dumps(falas, ensure_ascii=False), "application/json; charset=utf-8")
        else:
            self.responder(404, "não existe")

    def do_POST(self):
        s = self.server.sessao
        s.sinal = time.monotonic()
        corpo = self.rfile.read(int(self.headers.get("Content-Length") or 0))
        fim, codigo, texto = None, 200, "ok"
        try:
            if self.path == "/inicio":
                s.comecar()
            elif self.path == "/pedaco":
                s.anexar(corpo)
            elif self.path == "/marca":
                s.marcar(corpo)
            elif self.path == "/vivo":
                pass
            elif self.path == "/fim":
                fim = s.fim_da_pagina(json.loads(corpo))
            elif self.path == "/cancelar":
                fim = s.cancelar()
            elif self.path == "/erro":
                s.abortar(f"o teleprompter avisou: {corpo.decode(errors='replace')}")
            elif self.path == "/fechou":
                s.fechou_em = time.monotonic()
            else:
                codigo, texto = 404, "não existe"
        except Erro as e:
            codigo, texto, fim = 500, str(e), e
        except Exception as e:  # noqa: BLE001 — qualquer falha aqui tem de virar ERRO, não travar o CLI
            codigo, texto = 500, repr(e)
            if sobra := s.guardar_sobra():
                s.avisos.append(f"O que foi gravado ficou em {relativo(sobra)} (sem os tempos das linhas).")
            fim = Erro(" ".join([f"falha no servidor do teleprompter ao tratar {self.path}: {e!r}.", *s.avisos,
                                 de_novo(s.pasta)]))
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


def _encerrado(*_):
    raise KeyboardInterrupt  # SIGTERM (kill, timeout) faz o mesmo que o Ctrl+C: guarda a tomada aberta


def main(args):
    pasta = pasta_do_video(args.roteiro)
    sessao = Sessao(pasta, ler_roteiro(pasta))
    try:
        servidor = ThreadingHTTPServer(("127.0.0.1", args.porta), Pagina)
    except OSError:
        raise Erro(f"a porta {args.porta} está ocupada (outro humanim gravar aberto?). "
                   f"Feche-o ou use --porta {args.porta + 1}.") from None
    # Depois da porta: um gravar ainda aberto nesta pasta teria parado acima, e a tomada dele é dele.
    if sobra := sessao.guardar_sobra():
        sessao.avisos.append(f"Uma tomada de um gravar que não terminou estava em .trabalho/: ficou em "
                             f"{relativo(sobra)} (sem os tempos das linhas, que só a página tinha).")
    servidor.daemon_threads = True
    servidor.sessao = sessao
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    sessao.url = url = f"http://127.0.0.1:{args.porta}/"
    print(f"teleprompter em {url} esperando a gravação (Esc na página salva; Ctrl+C cancela).", flush=True)
    if not args.nao_abrir:
        abrir(url)
    inicio = time.monotonic()
    signal.signal(signal.SIGTERM, _encerrado)
    try:
        while not sessao.fim.wait(0.5):
            sessao.vigiar(time.monotonic(), inicio, not args.nao_abrir)
    except KeyboardInterrupt:
        sessao.abortar("interrompido (Ctrl+C ou o processo foi encerrado) antes de salvar")
    finally:
        servidor.shutdown()
        servidor.server_close()
        sessao.fechar()
    sessao.fim.wait(5)  # o /fim que estava salvando quando o Ctrl+C chegou
    if sessao.resultado is None:
        raise Erro(f"interrompido no meio do salvar: confira gravacao.webm, tempos.json e anteriores/ em "
                   f"{relativo(pasta)}. {de_novo(pasta)}")
    if isinstance(sessao.resultado, Erro):
        raise sessao.resultado
    ok("\n".join(sessao.resultado))
