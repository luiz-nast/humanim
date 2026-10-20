---
name: cenas
description: Escreve, ajusta e confere as cenas Manim do humanim (videos/<slug>/cenas/linha_NN.py), uma por linha [ANIM] ou [CANTO] do roteiro, renderizadas com humanim animar. Use quando pedirem as animações de um vídeo, para animar um roteiro, ou para mudar ou consertar a cena de uma linha.
---

# Cenas

Cada linha `[ANIM: …]` ou `[CANTO: …]` do `roteiro.md` vira uma cena Manim que dura exatamente a fala daquela linha. A descrição entre colchetes é o pedido; a fala diz quando cada coisa acontece.

## Antes de escrever

1. Leia o `roteiro.md` inteiro e marque quais linhas seguidas continuam a mesma cena (ex.: a árvore da linha 2 segue na 3 e na 4). Essas compartilham objetos em `cenas/comum.py`.
2. Leia `estilo/estilo.py`: é a identidade visual. Cor, fonte e tamanho saem só de lá.
3. Se já existe `cenas/comum.py` ou cenas de outras linhas, leia antes de mexer: mudar o `comum.py` muda todas as linhas que o usam.

## O arquivo

`videos/<slug>/cenas/linha_NN.py`, com NN = número da linha no roteiro, com 2 dígitos (`linha_03.py`). Sempre assim:

```python
from estilo import *
from comum import *  # só se a cena usa cenas/comum.py


class Cena(CenaHumanim):
    def construct(self):
        ...
        self.completar()
```

A classe se chama `Cena` e herda de `CenaHumanim`. Não sobrescreva `__init__` nem `setup`. O que a base dá:

| | |
| --- | --- |
| `self.duracao` | segundos da fala desta linha (estimados antes da gravação; depois, os da fala editada) |
| `self.marca`, `self.fala` | `"ANIM"` ou `"CANTO"`, e o texto falado |
| `self.area`, `self.centro` | área livre para desenhar (esq, base, dir, topo) e o centro dela; em [CANTO] já exclui você |
| `self.largura`, `self.altura` | tamanho da área livre |
| `self.ate("palavra")` | espera até a fala chegar nessa palavra (`vez=2` para a segunda vez que ela aparece; aceita fração: `self.ate(0.5)`) |
| `self.momento("palavra")` | o segundo em que a fala chega nela, sem esperar (pelo ritmo estimado: sílabas, números por extenso, pausas da pontuação) |
| `self.restante()` | segundos que ainda faltam |
| `self.completar()` | espera o que falta até `self.duracao`; última linha de todo `construct` |

## O estilo

A tela tem 8 unidades de largura por 14,22 de altura, origem no centro (x de -4 a 4, y de -7,11 a 7,11). 1 unidade = 135 px.

- Cores, cada uma com um papel: `AZUL` estrutura, `AMARELO` o que a fala aponta agora, `VERDE` sim/bom, `VERMELHO` não/ruim, `CINZA` secundário, `APAGADO` fora de foco, `BRANCO` texto. Extras: `LARANJA`, `ROXO`. Fundo preto, sempre.
- Fonte Lato em todo `Text`. Tamanhos (`font_size`): `TITULO` 72, `ROTULO` 48, `PEQUENO` 36. Menor que `PEQUENO` não se lê no celular.
- Traços: `stroke_width=ESPESSURA` em linhas, setas e contornos.
- `rotulo("texto", cor=..., tamanho=...)`: o jeito de pôr texto na tela. Mais de 3 palavras dá erro de propósito.
- Números (`Integer`, `DecimalNumber`, números de eixo) já saem em Lato e no formato brasileiro (`1.234,5`).

## Regras visuais

1. **Ritmo de Reels, não de slide.** Algo muda a cada segundo, mais ou menos. A imagem acompanha a fala: quando a fala diz "aprovado", é ali que "aprovado" acende (`self.ate("aprovado")`).
2. **Texto só como rótulo**, até 3 palavras, num nó, eixo, seta ou destaque. Nunca frase, lista de tópicos ou título de slide: a frase está na fala.
3. **Tudo na zona segura:** x entre -3,5 e 3,5 e y entre -4,7 e 5,6 (`AREA`). Acima e abaixo disso o app cobre com a interface, a legenda e os botões.
4. **Em [CANTO], o canto é seu:** você fica encostado no canto inferior esquerdo da tela, cortado no peito, tocando a borda de baixo e a esquerda: o retângulo x de -4 a -0,44 e y de -7,11 a -2,37 (480 x 640 px). Nada entra nele, em nenhum quadro, nem no primeiro. Desenhe em `self.area`, que nessas linhas é y acima de -2,07. A faixa à direita do canto (x de -0,2 a 3,5, y de -4,7 a -2,4) está livre para um elemento pequeno, se fizer falta.
5. **Cena de [CANTO] é mais simples**: um elemento principal, menos movimento.
6. **Grande e legível:** o assunto ocupa boa parte da área; nada encostado na borda.

## Duração

- Some `run_time` e `wait`: o total cabe em `self.duracao`. Termine sempre com `self.completar()`.
- Não escreva segundos fixos que só fecham com a duração estimada: depois da gravação as durações mudam e a cena é renderizada de novo. Dose com frações (`run_time=0.2 * self.duracao`) e sincronize com `self.ate("palavra")`.
- Perto do fim, limite a animação ao que sobra: `run_time=min(0.5, self.restante())`. Uma animação que começa na última palavra e dura mais que o resto estoura a fala.
- Rede de segurança (fala gravada mais rápida que a estimada): todo `self.play(..., run_time=...)` é encurtado para caber no que resta e, sem tempo nenhum, pula direto para o estado final. Não vale para `self.wait(...)` nem para `play` sem `run_time`: escreva sempre o `run_time`.
- Animação mais longa que a fala é ERRO do `animar`. E o `animar` avisa (`ATENÇÃO imagem parada de Xs a Ys`) todo trecho de 1,5 s ou mais em que nada muda, inclusive o fim que o `self.completar()` preenche: ali, adiante a próxima animação ou destaque a palavra que a fala diz.

## Continuidade (`cenas/comum.py`)

- Quando a linha N+1 continua a linha N, a cena N+1 começa redesenhando o estado final da N, sem animação (`self.add(...)`), para o corte não aparecer. Os dois estados saem de funções do `comum.py`, com posições fixas (números no `comum.py`, nunca dependentes de tempo).
- [ANIM] seguida de [CANTO] que continua a cena: a [ANIM] já desenha dentro da área do CANTO (`AREA_CANTO`), senão você aparece por cima no corte. De [CANTO] para [ANIM], a cena pode crescer para a tela toda logo no começo.
- Depois de uma linha [CARA], a cena pode começar do zero.
- Pontos ou posições aleatórias: `rng = np.random.default_rng(7)` no `comum.py`, para todo render e toda linha verem os mesmos pontos.

## Conferir

Rode da raiz do repositório, como no `CLAUDE.md`:

1. `humanim animar videos/<slug>/roteiro.md --linha N` (pode repetir `--linha`). Sai `OK linha N: ...` ou `ERRO linha N: ...` dizendo o que fazer.
2. `humanim frames videos/<slug>/cenas/linha_NN.mp4`: 3 prints em `videos/<slug>/frames/`: `cena_NN_primeiro`, `cena_NN_meio` e `cena_NN_ultimo` (o primeiro e o último quadro de verdade).
3. Olhe cada print com Read. Confira: lê-se tudo? algo cortado na borda ou sobreposto? em [CANTO], o canto inferior esquerdo está vazio, também no `_primeiro`? a imagem bate com a fala naquele momento?
4. Linhas que continuam a cena: o `cena_N_ultimo` e o `cena_(N+1)_primeiro` têm que ser a mesma imagem, senão o corte salta.
5. Ajuste e repita até ficar bom. Para ver as zonas, rode `HUMANIM_DEPURAR=1 humanim animar videos/<slug>/roteiro.md --linha N`: desenha a zona segura (cinza) e, em [CANTO], o seu canto (vermelho tracejado). Antes de montar, rode de novo sem a variável.
6. No fim, `humanim animar videos/<slug>/roteiro.md` sem `--linha`: renderiza todas (até 3 ao mesmo tempo) e pula as que não mudaram (`cenas/render.json`). Mudar o `comum.py` ou o estilo renderiza de novo as linhas que dependem deles.

Depois da gravação e do `humanim editar` (`tempos.json` e `edicao.json` novos), rode `humanim animar videos/<slug>/roteiro.md` de novo: as durações da fala editada (sem pausas, muletas e repetições) entram sozinhas. Elas costumam sair mais curtas que as gravadas: por isso as frações e o `self.ate("palavra")`, nunca segundos fixos.

## Armadilhas

**Não tem LaTeX.** Isto quebra (`No such file or directory: 'latex'`):

| Quebra | Use |
| --- | --- |
| `MathTex`, `Tex`, `SingleStringMathTex` | `Text` (`"x²"` com caractere Unicode) |
| `Title`, `BulletedList` | `rotulo(...)`; lista de tópicos nunca |
| `Matrix`, `IntegerMatrix`, `DecimalMatrix`, `MathTable` | `Table` ou `IntegerTable`, ou quadrados com `Text` num `VGroup(...).arrange_in_grid()` |
| `Variable` | `rotulo("nome")` ao lado de um `DecimalNumber` com updater |
| `Brace(...).get_text/get_tex`, `BraceLabel` padrão | `BraceText(obj, "texto")` ou `BraceLabel(obj, "texto", label_constructor=Text)` |
| `LabeledDot("a")`, `LabeledLine("a", ...)` | `LabeledDot(Text("a", color=FUNDO))` (o ponto é branco: texto branco some); `Line` + `rotulo` ao lado |
| `Graph(..., labels=True)` | `labels={v: Text(str(v), color=FUNDO, font_size=PEQUENO)}`; para vértices coloridos, `vertex_config={"fill_color": AZUL}` |
| `BarChart(..., bar_names=[...])` | `BarChart` sem nomes + `rotulo` embaixo de cada barra (`chart.bars[i]`) |
| `DecimalNumber(..., unit="%")` ou `show_ellipsis=True` | `rotulo("%")` com `.next_to(numero, RIGHT)` |

Funcionam (o estilo troca o LaTeX por Text): `Integer`, `DecimalNumber`, `ChangeDecimalToValue`, `NumberLine` e `Axes` com `include_numbers`, `add_coordinates`, `get_axis_labels`, `BarChart` sem nomes (já sai nas cores do estilo), `Table`, `IntegerTable`, `DecimalTable`, `BraceText`, `LabeledArrow(Text(...))`, `Code`, `MarkupText`.

Outras:

- `set_opacity` numa forma sem preenchimento (retângulo, círculo) enche ela de cor. Para apagar: `set_stroke(opacity=...)` ou `fade(0.7)`; para voltar, `save_state()` antes e `Restore(obj)` depois.
- `Transform` numa parte e `.animate` no grupo que a contém, no mesmo `play`, brigam. Anime as partes, cada uma para o seu alvo.
- `Indicate`, `Flash`, `Wiggle`, `Circumscribe` voltam ao estado de antes: bons para destacar sem mudar o estado final.
- `self.wait()` sem número espera 1 s.
- Largura: a área útil tem 7 unidades. Em `ROTULO`, cada letra ocupa uns 0,27; em `PEQUENO`, uns 0,2. `Axes` com `x_length` até 6,5.
- Sem `self.camera.frame` (a cena não é `MovingCamera`): para "aproximar", escale e mova os objetos.

## Exemplo

`[CANTO: da caixinha do topo saem duas setas, "sim" e "não"]` com a fala "É tipo jogo de adivinhação: uma pergunta por vez, e cada resposta abre um caminho.":

```python
from estilo import *
from comum import *  # arvore(), titulo() e respostas() desenham a árvore na AREA_CANTO


class Cena(CenaHumanim):
    def construct(self):
        caixas, setas = arvore()
        nome = titulo()
        self.add(*caixas.values(), *setas.values(), nome)  # emenda com o fim da linha 2

        self.play(FadeOut(nome, shift=UP * 0.3), run_time=0.4)
        self.ate("adivinhação")
        self.play(Wiggle(caixas["raiz"]), run_time=0.6)
        self.ate("pergunta")
        self.play(caixas["raiz"][0].animate.set_color(AMARELO), run_time=0.3)
        rotulos, cores = respostas(setas, "raiz")
        self.ate("resposta")
        self.play(*(setas[k].animate.set_color(c) for k, c in cores.items()),
                  *(Write(r) for r in rotulos), run_time=0.6)
        self.ate("abre")
        self.play(caixas["raiz"][0].animate.set_color(AZUL),
                  Indicate(caixas["a"], color=VERDE), Indicate(caixas["b"], color=VERMELHO), run_time=0.7)
        self.completar()
```

## Entrega

- [ ] Uma cena por linha [ANIM] e [CANTO], `class Cena(CenaHumanim)`, terminando em `self.completar()`
- [ ] `humanim animar roteiro.md` deu OK em todas, sem `HUMANIM_DEPURAR`
- [ ] Olhou os prints de cada cena
- [ ] Só rótulos de até 3 palavras; nenhuma frase na tela
- [ ] Nada fora da zona segura; canto livre nas linhas [CANTO]
- [ ] Linhas que continuam a cena emendam (o fim de uma é o começo da outra)

No chat: uma linha por cena dizendo o que ela mostra, e o que vale quem apresenta conferir (uma escolha visual duvidosa, uma simplificação).
