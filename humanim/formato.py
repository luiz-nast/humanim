"""Formato do vídeo final. Tudo que monta ou desenha usa estes números."""

LARGURA = 1080
ALTURA = 1920
FPS = 30

# Onde você fica nas linhas [CANTO], em pixels do vídeo final:
# (x, y do canto superior esquerdo, largura, altura). Encostado no canto
# inferior esquerdo e cortado no peito: você sempre toca uma borda da tela.
CANTO = (0, 1280, 480, 640)

# Faixa de cima que a interface do app cobre, em pixels do vídeo final: a zona segura das cenas começa embaixo
# dela (estilo.TOPO), o teleprompter a escurece no retângulo amarelo e o zoom do [CARA] a deixa parada.
FAIXA_TOPO = 200
ZOOM = 1.12  # jump cut no [CARA]: o plano alterna entre 100% e isto


def lados_soltos(x, y, largura, altura):
    """Lados de um retângulo do vídeo que não encostam na borda da tela: (esquerda, cima, direita, baixo).
    Só esses levam contorno: o lado que encosta na tela continua a imagem até a borda."""
    return x > 0, y > 0, x + largura < LARGURA, y + altura < ALTURA
