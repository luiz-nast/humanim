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
- `rotulo("texto", cor=..., tamanho=...)`: o jeito de pôr texto na tela. Mais de 3 palavras dá erro de propósito (um número conta como uma).
- `conta("0", " − ", "10", " × ", "(−55,2)", " = ", "552")`: conta ou fórmula num `Text` só (mesma linha de base), com cada parte animável (`[2]` é o "10"). É assim que se monta termo a termo; a regra das 3 palavras não vale aqui. `cores={2: AMARELO}` pinta uma parte.
- Números (`Integer`, `DecimalNumber`, eixos) já saem em Lato, no formato brasileiro e com o menos certo: `−1.234,5`. Número escrito à mão: `br(1295.2)` dá "1.295" e `br(-55.18, 1)` dá "−55,2", igual ao `DecimalNumber`.
- `lupa(ponto, centro)`: círculo no detalhe, ligado a uma lente maior (fundo preto) onde a cena desenha o detalhe ampliado.

## Regras visuais

1. **Ritmo de Reels, não de slide.** Algo muda a cada segundo, mais ou menos. A imagem acompanha a fala: quando a fala diz "aprovado", é ali que "aprovado" acende (`self.ate("aprovado")`).
2. **Texto só como rótulo**, até 3 palavras, num nó, eixo, seta ou destaque. Nunca frase, lista de tópicos ou título de slide: a frase está na fala.
3. **Tudo na zona segura:** x entre -3,5 e 3,5 e y entre -4,7 e 5,6 (`AREA`). Acima e abaixo disso o app cobre com a interface, a legenda e os botões.
4. **Em [CANTO], o canto é seu:** você fica encostado no canto inferior esquerdo, cortado no peito: x de -4 a -0,44 e y de -7,11 a -2,37 (480 x 640 px). Nada entra nele, em nenhum quadro, nem no primeiro. Desenhe em `self.area` (y acima de -2,07). Na faixa à direita do canto (x de -0,2 a 3,5, y de -4,7 a -2,4) cabe um elemento pequeno.
5. **Cena de [CANTO] é mais simples**: um elemento principal, menos movimento.
6. **Grande e legível:** o assunto ocupa boa parte da área; nada encostado na borda. No eixo, números só nos valores que a fala usa ou em 2 ou 3 de referência (`numbers_to_include=[...]`), marcas sem número no resto, nunca números em duas alturas.
7. **O desenho não engana.**
   - Ampliar só com `lupa()` ou com uma moldura que sai do pedaço ampliado e cresce até o gráfico novo (outro `Axes`, com o intervalo novo). Não há câmera para dar zoom, e escalar o gráfico por cima dos números do eixo mente a escala.
   - Se a fala diz que algo não é zero, o desenho mostra a distância até o zero.
   - Número muda de valor no pouso, sem rolar por valores que não existiram; contador só rola quando conta coisas (vendas, passos).
   - O número ao lado de uma curva é o da grandeza dessa curva. Comparação que a fala pede tem de se ver: se o dado dá 3° de diferença, ponha os dois números lado a lado.
   - Posição pedida na descrição é indicação: mude para caber, sem mudar o sentido.

## Duração

- Some `run_time` e `wait`: o total cabe em `self.duracao`. Termine sempre com `self.completar()`.
- Não escreva segundos fixos que só fecham com a duração estimada: depois da gravação as durações mudam e a cena é renderizada de novo. Dose com frações (`run_time=0.2 * self.duracao`) e sincronize com `self.ate("palavra")`.
- Perto do fim, limite a animação ao que sobra: `run_time=min(0.5, self.restante())`. Uma animação que começa na última palavra e dura mais que o resto estoura a fala.
- Rede de segurança (fala gravada mais rápida que a estimada): todo `self.play(..., run_time=...)` é encurtado para caber no que resta e, sem tempo nenhum, pula direto para o estado final. Não vale para `self.wait(...)` nem para `play` sem `run_time`: escreva sempre o `run_time`.
- Animação mais longa que a fala é ERRO do `animar`, e 1,5 s ou mais sem nada mudar (inclusive o fim que o `completar()` preenche) vira `ATENÇÃO imagem parada`: adiante a próxima animação ou destaque a palavra que a fala diz ali.

## Continuidade (`cenas/comum.py`)

- Quando a linha N+1 continua a linha N, a cena N+1 começa redesenhando o estado final da N, sem animação (`self.add(...)`), para o corte não aparecer. Os dois estados saem de funções do `comum.py`, com posições fixas (números no `comum.py`, nunca dependentes de tempo). O que mudou com animação (um `DecimalNumber` depois de `set_value` fica 1 a 2 px fora) termina com `.become(...)` do mesmo objeto criado pelo `comum.py`.
- [ANIM] seguida de [CANTO] que continua a cena: a [ANIM] já desenha dentro da área do CANTO (`AREA_CANTO`), senão você aparece por cima no corte. De [CANTO] para [ANIM], a cena pode crescer para a tela toda logo no começo.
- Depois de uma linha [CARA], a cena pode começar do zero.
- Pontos ou posições aleatórias: `rng = np.random.default_rng(7)` no `comum.py`, para todo render e toda linha verem os mesmos pontos.

## Conferir

Rode da raiz do repositório, como no `CLAUDE.md`:

1. `humanim animar videos/<slug>/roteiro.md --linha N` (pode repetir `--linha`; para iterar, só as linhas que mudaram). Sai `OK linha N: ...` ou `ERRO linha N: ...` dizendo o que fazer.
2. `humanim frames videos/<slug>/cenas/linha_NN.mp4`: 3 prints em `videos/<slug>/frames/`: `cena_NN_primeiro`, `cena_NN_meio` e `cena_NN_ultimo` (o primeiro e o último quadro de verdade). Cena com vários eventos pede a folha, um quadro a cada 0,5 s com o tempo escrito: `ffmpeg -v error -y -i videos/<slug>/cenas/linha_NN.mp4 -vf "fps=2,scale=270:480,drawtext=text='%{pts\:hms}':x=6:y=6:fontsize=20:fontcolor=yellow,tile=6x3" -frames:v 1 videos/<slug>/frames/folha_NN.png`.
3. Olhe cada imagem com Read. Confira: lê-se tudo? algo cortado na borda, sobreposto ou entrando de fora da zona segura? tela vazia em algum momento? em [CANTO], o canto inferior esquerdo está vazio, também no `_primeiro`? a imagem bate com a fala naquele momento? o desenho engana (regra 7)?
4. Linhas que continuam a cena: o `cena_N_ultimo` e o `cena_(N+1)_primeiro` têm que ser a mesma imagem, senão o corte salta.
5. Ajuste e repita até ficar bom. Para ver as zonas, rode `HUMANIM_DEPURAR=1 humanim animar videos/<slug>/roteiro.md --linha N`: desenha a zona segura (cinza) e, em [CANTO], o seu canto (vermelho tracejado). Antes de montar, rode de novo sem a variável.
6. No fim, `humanim animar videos/<slug>/roteiro.md` sem `--linha`: renderiza todas (quantas por vez a memória livre deixa, de 1 a 3; `HUMANIM_PARALELO=1` força uma) e pula as que não mudaram (`cenas/render.json`). O vídeo inteiro leva uns 2 a 3 min: rode em segundo plano ou com timeout maior que os 2 min do Bash, e nada pesado junto. Mudar o `comum.py`, o estilo, o `humanim/formato.py` ou o ritmo da fala (`humanim/fala.py`) renderiza de novo as linhas que dependem deles; a prévia lista em "Falta animar" a linha cujo clipe ficou velho. Depois da gravação e do `editar`, rode de novo: as durações da fala editada entram sozinhas.

## Armadilhas

**Não tem LaTeX.** Isto quebra (`No such file or directory: 'latex'`):

| Quebra | Use |
| --- | --- |
| `MathTex`, `Tex`, `SingleStringMathTex` | `conta(...)` ou `rotulo(...)`, com caractere Unicode (`"x²"`) |
| `Title`, `BulletedList` | `rotulo(...)`; lista de tópicos nunca |
| `Matrix`, `IntegerMatrix`, `DecimalMatrix`, `MathTable` | `Table` ou `IntegerTable`, ou quadrados com `Text` num `VGroup(...).arrange_in_grid()` |
| `Brace(...).get_text/get_tex`, `BraceLabel` padrão | `BraceText(obj, "texto")` ou `BraceLabel(obj, "texto", label_constructor=Text)` |
| `LabeledDot("a")`, `LabeledLine("a", ...)` | `LabeledDot(Text("a", color=FUNDO))` (o ponto é branco: texto branco some); `Line` + `rotulo` ao lado |
| `Graph(..., labels=True)` | `labels={v: Text(str(v), color=FUNDO, font_size=PEQUENO)}`; para vértices coloridos, `vertex_config={"fill_color": AZUL}` |
| `BarChart(..., bar_names=[...])` | `BarChart` sem nomes + `rotulo` embaixo de cada barra (`chart.bars[i]`) |
| `DecimalNumber(..., unit="%")` ou `show_ellipsis=True` | `rotulo("%")` com `.next_to(numero, RIGHT)` |

Funcionam (o estilo troca o LaTeX por Text): `Integer`, `DecimalNumber`, `NumberLine` e `Axes` com números, `BarChart` sem nomes, `Table`, `IntegerTable`, `DecimalTable`, `BraceText`, `LabeledArrow(Text(...))`.

Símbolos que a Lato tem: × − ÷ ± ≈ ≠ ≤ ≥ → √ ∑ ∫ ∂ ∞ Δ θ λ ε η α σ μ π ½ ² ³, os dígitos sobrescritos e subscritos (w₀, 10⁻⁴), ŷ e x̄. Não tem ∇, ∈, ⋅ nem a maioria das letras subscritas (ₖ ₙ ₘ ₜ ⱼ): saem em outra fonte ou como caixa. Escreva "gradiente", "w novo", "·".

Outras:

- `set_opacity` numa forma sem preenchimento (retângulo, círculo) enche ela de cor. Para apagar: `set_stroke(opacity=...)` ou `fade(0.7)`; para voltar, `save_state()` antes e `Restore(obj)` depois.
- `Transform` numa parte e `.animate` no grupo que a contém, no mesmo `play`, brigam. Anime as partes, cada uma para o seu alvo.
- `Indicate`, `Flash`, `Wiggle`, `Circumscribe` voltam ao estado de antes: bons para destacar sem mudar o estado final.
- `self.wait()` sem número espera 1 s.
- `numero.animate.set_value(v)` quebra (`zip() argument 2 is longer than argument 1`) quando o número muda de tamanho ("−55,2" para "12,5"). Troque com `numero.set_value(v)` no pouso; `ChangeDecimalToValue(numero, v)` rola pelos valores do meio, então só para contador (regra 7).
- Medidas: a área útil tem 7 de largura e `Axes` vai até `x_length` 6,5. Meça antes de posicionar (`Text("1.000", font_size=PEQUENO).width` dá 1,22). De cabeça, letra, dígito e altura de "Ég": `PEQUENO` 0,22, 0,29 e 0,55; `ROTULO` 0,3, 0,38 e 0,74; `TITULO` 0,45, 0,57 e 1,1.
- `Axes` cruza os eixos no zero: com x de −1.000 a 3.600, o eixo y fica no meio do gráfico. Para ele ficar à esquerda, desloque os dados para x começar no 0 e escreva os números com `br()`.
- `FadeOut` de tudo e depois `Create`/`FadeIn` do novo deixa a tela preta no meio: ponha os dois no mesmo `play`. E `FadeIn(..., shift=...)` começa deslocado: perto da borda, entra de fora da zona segura.
- Seta curva com `Create` desenha a ponta por último, só o contorno. Separe: `ponta = arco.add_tip().pop_tips()[0]`, `Create(arco)` e, no fim, `FadeIn(ponta)`.
- Gatilho num número: a fala "1.295" são as palavras "1" e "295", e `self.ate("295")` espera o fim do número falado.

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
- [ ] Só rótulos de até 3 palavras e contas montadas com `conta()`; nenhuma frase na tela
- [ ] Nada fora da zona segura; canto livre nas linhas [CANTO]; o desenho não engana
- [ ] Linhas que continuam a cena emendam (o fim de uma é o começo da outra)

No chat: uma linha por cena dizendo o que ela mostra, e o que vale quem apresenta conferir (uma escolha visual duvidosa, uma simplificação).
