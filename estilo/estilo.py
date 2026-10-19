"""Identidade visual do humanim: toda cena começa com `from estilo import *`.

Reexporta o Manim e fixa tela vertical, cores, fonte e tamanhos, iguais em todo vídeo.
"""
import os
import re

from manim import *  # noqa: F401,F403
from manim import config, np

from humanim.formato import ALTURA, CANTO, FPS, LARGURA

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
# E no formato brasileiro: 1.234,5.
_formatar = DecimalNumber._get_num_string
DecimalNumber._get_num_string = lambda self, n: _formatar(self, n).translate(str.maketrans(",.", ".,"))


def pixel(x, y):
    """Ponto do vídeo final em pixels (origem no canto superior esquerdo) para coordenadas Manim."""
    return np.array([(x - LARGURA / 2) / PX, (ALTURA / 2 - y) / PX, 0.0])


# Zona segura: fora dela a interface do app (topo, legenda e botões embaixo) cobre a imagem.
LADO = pixel(LARGURA - 64, 0)[0]  # 3.53: x vai de -LADO a LADO
TOPO = pixel(0, 200)[1]  # 5.63
BASE = pixel(0, 1600)[1]  # -4.74

# Onde você fica nas linhas [CANTO], em unidades Manim (formato.CANTO convertido).
CANTO_ESQ, CANTO_TOPO = pixel(CANTO[0], CANTO[1])[:2]  # -3.64, -1.19
CANTO_DIR, CANTO_BASE = pixel(CANTO[0] + CANTO[2], CANTO[1] + CANTO[3])[:2]  # -0.98, -4.74

# Área para desenhar (esq, base, dir, topo). Em [CANTO], só acima de você.
AREA = (-LADO, BASE, LADO, TOPO)
AREA_CANTO = (-LADO, CANTO_TOPO + 0.3, LADO, TOPO)


def zona_canto():
    """Retângulo de depuração: onde você aparece nas linhas [CANTO]."""
    return DashedVMobject(Rectangle(width=CANTO_DIR - CANTO_ESQ, height=CANTO_TOPO - CANTO_BASE,
                                    color=VERMELHO, stroke_width=4), num_dashes=40).move_to(
        [(CANTO_ESQ + CANTO_DIR) / 2, (CANTO_TOPO + CANTO_BASE) / 2, 0])


def rotulo(texto, cor=BRANCO, tamanho=ROTULO, **kwargs):
    """Texto curto na fonte do estilo. Mais de 3 palavras vira erro: na tela, só rótulo."""
    if len(re.findall(r"\w+", texto)) > 3:
        raise ValueError(f'rótulo "{texto}" tem mais de 3 palavras: na tela vai só rótulo curto, a frase fica na fala.')
    return Text(texto, color=cor, font_size=tamanho, **kwargs)


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
        """Segundo da cena em que a fala chega em `quando`: fração (0.5) ou palavra(s) da fala ("aprovado")."""
        if isinstance(quando, str):
            todas = re.findall(r"\w+", self.fala.lower())
            busca = re.findall(r"\w+", quando.lower())
            achou = [i for i in range(len(todas)) if todas[i:i + len(busca)] == busca]
            if len(achou) < vez:
                raise ValueError(f'"{quando}" (vez {vez}) não está na fala: "{self.fala}"')
            quando = achou[vez - 1] / len(todas)
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
