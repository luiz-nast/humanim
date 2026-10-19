"""Formato do vídeo final. Tudo que monta ou desenha usa estes números."""

LARGURA = 1080
ALTURA = 1920
FPS = 30

# Onde você fica nas linhas [CANTO], em pixels do vídeo final:
# (x, y do canto superior esquerdo, largura, altura). Encostado no canto
# inferior esquerdo e cortado no peito: você sempre toca uma borda da tela.
CANTO = (0, 1280, 480, 640)
