"""Identidade visual do humanim: toda cena começa com `from estilo import *`.

Reexporta o Manim e fixa tela vertical, cores, fonte e tamanhos, iguais em todo vídeo.
"""
import os
import re

from manim import *  # noqa: F401,F403
from manim import config, np

from humanim.formato import ALTURA, CANTO, FAIXA_TOPO, FPS, LARGURA
from humanim.roteiro import fracao_na_fala

# Tela em pé com 8 unidades de largura: 135 px por unidade, a mesma escala de um
# vídeo 1080p do Manim, então tamanhos de fonte e espessuras ficam com a cara de sempre.
config.frame_width = 8.0
config.frame_height = 8.0 * ALTURA / LARGURA  # 14.22
PX = LARGURA / config.frame_width

# Cores (as do Manim). Papel de cada uma: AZUL estrutura, AMARELO o que a fala aponta agora,
# VERDE sim/bom, VERMELHO não/ruim, CINZA secundário, APAGADO o que saiu de foco.
FUNDO = "#000000"
BRANCO = "#FFFFFF"
AZUL = "#58C4DD"
VERDE = "#83C167"
VERMELHO = "#FC6255"
AMARELO = "#F7D96F"
LARANJA = "#FF862F"
ROXO = "#9A72AC"
CINZA = "#888888"
APAGADO = "#444444"
config.background_color = FUNDO

FONTE = "Lato"
TITULO = 72  # font_size: palavra de destaque
ROTULO = 48  # rótulo num nó, eixo ou seta
PEQUENO = 36  # o menor que ainda se lê no celular
ESPESSURA = 6  # stroke_width de linhas e setas

Text.set_default(font=FONTE)
MarkupText.set_default(font=FONTE)
# Números sem LaTeX: DecimalNumber, Integer e os números de eixos saem em Text.
DecimalNumber.set_default(mob_class=Text)
NumberLine.set_default(label_constructor=Text)
BarChart.set_default(bar_colors=[AZUL, VERDE, AMARELO, LARANJA, ROXO])  # o padrão do Manim some no preto
# E no formato brasileiro: 1.234,5, com o sinal de menos da Lato (o hífen é curto e fica baixo).
MENOS = "−"  # U+2212
_formatar = DecimalNumber._get_num_string
DecimalNumber._get_num_string = lambda self, n: _formatar(self, n).translate(str.maketrans(",.", ".,"))
_peca = DecimalNumber._string_to_mob  # o Manim centra na altura o caractere "-": a string guarda o "-", o desenho é o "−"
DecimalNumber._string_to_mob = lambda self, s, mob_class=None, **kw: _peca(self, MENOS if s == "-" else s, mob_class, **kw)


def br(x, casas=0, sinal=False):
    """Número escrito como o DecimalNumber escreve, para Text e contas: br(1295.2) "1.295", br(-55.18, 1) "−55,2",
    br(0.3445, 2) "0,34". sinal=True põe "+" nos positivos. Nunca "−0"."""
    s = f"{x:,.{casas}f}"
    zero = not any(c in "123456789" for c in s)
    if zero and s.startswith("-"):
        s = s[1:]
    if sinal and not zero and not s.startswith("-"):
        s = "+" + s
    return s.translate(str.maketrans(",.-", ".," + MENOS))


def pixel(x, y):
    """Ponto do vídeo final em pixels (origem no canto superior esquerdo) para coordenadas Manim."""
    return np.array([(x - LARGURA / 2) / PX, (ALTURA / 2 - y) / PX, 0.0])


# Zona segura: fora dela a interface do app (topo, legenda e botões embaixo) cobre a imagem.
LADO = pixel(LARGURA - 64, 0)[0]  # 3.53: x vai de -LADO a LADO
TOPO = pixel(0, FAIXA_TOPO)[1]  # 5.63
BASE = pixel(0, 1600)[1]  # -4.74

# Onde você fica nas linhas [CANTO], em unidades Manim (formato.CANTO convertido).
CANTO_ESQ, CANTO_TOPO = pixel(CANTO[0], CANTO[1])[:2]  # -4.0, -2.37
CANTO_DIR, CANTO_BASE = pixel(CANTO[0] + CANTO[2], CANTO[1] + CANTO[3])[:2]  # -0.44, -7.11

# Área para desenhar (esq, base, dir, topo). Em [CANTO], só acima de você (y > -2.07).
AREA = (-LADO, BASE, LADO, TOPO)
AREA_CANTO = (-LADO, CANTO_TOPO + 0.3, LADO, TOPO)


def zona_canto():
    """Retângulo de depuração: onde você aparece nas linhas [CANTO]."""
    return DashedVMobject(Rectangle(width=CANTO_DIR - CANTO_ESQ, height=CANTO_TOPO - CANTO_BASE,
                                    color=VERMELHO, stroke_width=4), num_dashes=40).move_to(
        [(CANTO_ESQ + CANTO_DIR) / 2, (CANTO_TOPO + CANTO_BASE) / 2, 0])


def rotulo(texto, cor=BRANCO, tamanho=ROTULO, **kwargs):
    """Texto curto na fonte do estilo. Mais de 3 palavras vira erro: na tela, só rótulo. Número ("1.295") é uma."""
    if len(re.findall(r"\d+(?:[.,]\d+)*|\w+", texto)) > 3:
        raise ValueError(f'rótulo "{texto}" tem mais de 3 palavras: na tela vai só rótulo curto, a frase fica na fala '
                         f'(conta ou fórmula: conta(...)).')
    return Text(texto, color=cor, font_size=tamanho, **kwargs)


FINO = " "  # espaço fino: entre um "²" e um ")" de uma conta, para o expoente não encostar


def conta(*partes, tamanho=ROTULO, cor=BRANCO, cores=None):
    """Conta ou fórmula num Text só, com cada parte acessível para animar sozinha:
    conta("0", " − ", "10", " × ", "(−55,2)", " = ", "552")[2] é o "10". Tudo fica na mesma linha de base (Text
    separados com arrange desalinham), os espaços vão dentro das partes, e a regra das 3 palavras não vale aqui.
    O hífen antes de número ou sozinho vira o menos (−); "²" e "³" saem 25% maiores, para se ler no celular (antes
    de um ")", ponha FINO). cores: {índice da parte: cor}."""
    partes = [re.sub(r"(?<!\w)-(?=[\d\s(]|$)", MENOS, p) for p in partes]
    s = "".join(partes)
    t = Text(s, font_size=tamanho, color=cor, disable_ligatures=True)
    if len(t.submobjects) != len(s):
        raise ValueError(f"conta {s!r}: {len(t.submobjects)} glifos para {len(s)} caracteres (quebra de linha?)")
    for i, c in enumerate(s):
        if c in "²³":
            t.submobjects[i].scale(1.25, about_edge=DL)
    grupos, i = VGroup(), 0
    for k, p in enumerate(partes):
        g = VGroup(*(m for m in t.submobjects[i:i + len(p)] if m.has_points()))  # sem os espaços: o Write quebra neles
        if cores and k in cores:
            g.set_color(cores[k])
        grupos.add(g)
        i += len(p)
    return grupos


def lupa(ponto, centro, raio=1.1, raio_alvo=0.25, cor=CINZA):
    """Ampliar um detalhe sem enganar: um círculo no detalhe, ligado por duas linhas a um círculo maior (a lente,
    com fundo preto, cobre o que fica atrás). O detalhe ampliado a cena desenha dentro da lente (centro, raio).
    Devolve VGroup(alvo, linha, linha, lente). Se uma linha cair em cima de algo, mude o centro da lente."""
    p, c = np.array(ponto, dtype=float), np.array(centro, dtype=float)
    d = np.linalg.norm(c - p)
    if d <= raio + raio_alvo:
        raise ValueError("lupa: a lente encosta no detalhe; afaste o centro ou diminua o raio.")
    u, angulo = (c - p) / d, np.arccos((raio_alvo - raio) / d)  # tangentes externas aos dois círculos
    linhas = [Line(p + raio_alvo * n, c + raio * n, color=cor, stroke_width=3)
              for n in (rotate_vector(u, angulo), rotate_vector(u, -angulo))]
    alvo = Circle(radius=raio_alvo, color=cor, stroke_width=3).move_to(p)
    lente = Circle(radius=raio, color=cor, stroke_width=4).move_to(c).set_fill(FUNDO, opacity=1)
    return VGroup(alvo, *linhas, lente)


class CenaHumanim(Scene):
    """Base de toda cena. O humanim animar passa a duração, a marca e a fala da linha."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.duracao = float(os.environ.get("HUMANIM_DURACAO", 5))
        self.marca = os.environ.get("HUMANIM_MARCA", "ANIM")
        self.fala = os.environ.get("HUMANIM_FALA", "")
        self.area = AREA_CANTO if self.marca == "CANTO" else AREA
        esq, base, dir_, topo = self.area
        self.centro = np.array([(esq + dir_) / 2, (base + topo) / 2, 0.0])
        self.largura, self.altura = dir_ - esq, topo - base

    def setup(self):
        if os.environ.get("HUMANIM_DEPURAR"):
            esq, base, dir_, topo = self.area
            self.add_foreground_mobjects(Rectangle(width=dir_ - esq, height=topo - base, color=CINZA,
                                                   stroke_width=2).move_to(self.centro))
            if self.marca == "CANTO":
                self.add_foreground_mobjects(zona_canto())

    def play(self, *animacoes, **kwargs):
        """O play do Manim, mas sem passar do fim da fala (fala gravada mais rápida que a estimada):
        um run_time maior que o que resta é encurtado e, sem tempo nenhum, vai direto ao estado final.
        Sobra sempre o último quadro: o Manim não desenha o instante final de um play, e é esse
        estado final que a linha seguinte redesenha para emendar."""
        if "run_time" in kwargs:
            kwargs["run_time"] = min(kwargs["run_time"], self.restante() - 1 / FPS)
            if kwargs["run_time"] < 1 / FPS:
                lista = self.compile_animations(*animacoes)
                self.add_mobjects_from_animations(lista)
                for a in lista:
                    a._setup_scene(self)
                    a.begin()
                    a.finish()
                    a.clean_up_from_scene(self)
                return
        super().play(*animacoes, **kwargs)

    def restante(self):
        """Segundos que ainda faltam até self.duracao."""
        return max(0.0, self.duracao - self.time)

    def momento(self, quando, vez=1):
        """Segundo da cena em que a fala chega em `quando`: fração (0.5) ou palavra(s) da fala ("aprovado").
        A posição da palavra sai do ritmo estimado da fala (sílabas, números por extenso e pausas da
        pontuação), esticado ou encolhido para a duração da linha."""
        if isinstance(quando, str):
            fracao = fracao_na_fala(self.fala, quando, vez)
            if fracao is None:
                raise ValueError(f'"{quando}" (vez {vez}) não está na fala: "{self.fala}"')
            quando = fracao
        return quando * self.duracao

    def ate(self, quando, vez=1):
        """Espera até a fala chegar em `quando` (veja momento). Se já passou, segue."""
        falta = self.momento(quando, vez) - self.time
        if falta >= 1 / FPS:
            self.wait(falta)

    def completar(self):
        """Espera o que falta até self.duracao. Última linha de todo construct."""
        n = round(self.restante() * FPS)
        if n > 0:
            # Quadro parado conta int(t*fps) quadros; com updaters, conta ceil(t*fps).
            parado = not (self.always_update_mobjects or self.updaters or any(
                m.has_time_based_updater() for m in self.get_mobject_family_members()))
            self.wait((n + (0.5 if parado else -0.5)) / FPS, frozen_frame=parado)
