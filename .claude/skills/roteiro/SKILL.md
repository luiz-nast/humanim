---
name: roteiro
description: Escreve e ajusta roteiros dos shorts do humanim (vídeos verticais de 60 s explicando IA para leigos), linha por linha, com as marcas [CARA], [ANIM: …] e [CANTO: …]. Use quando pedirem um roteiro, um vídeo novo sobre um tema, ideias de vídeo, ou ajustes num videos/<slug>/roteiro.md.
---

# Roteiro

Escreve o roteiro de um short do humanim: o que quem apresenta fala e o que aparece na tela, linha por linha. Não é para inventar uma voz do zero: é para escrever na direção de quem apresenta, seguindo `voz.md`.

## Antes de escrever

1. Leia `voz.md` e `temas.md`, nesta pasta.
2. Se `voz.md` ainda não tem frases de exemplo, siga só o Tom e os fechamentos que estão lá, e avise na entrega.
3. Feche o tema numa frase: a única ideia que o vídeo passa. Tema largo demais ("redes neurais") vira um recorte ("o que um neurônio artificial faz"). Num tema de técnica, a ideia inclui o que a máquina aprende; sem isso, vira explicação de fluxograma.

## O arquivo

Salve em `videos/<slug>/roteiro.md`. O slug é o tema curto em minúsculas, sem acento, com hífens: `arvore-de-decisao`. Crie a pasta se não existir.

O arquivo tem só as linhas do roteiro: uma fala por linha, sem título, sem comentário, sem linha em branco no meio, terminando com uma quebra de linha. A linha N do arquivo é a `"linha": N` do `tempos.json` que o teleprompter vai gerar, então nada além das falas entra ali. Observações vão no chat.

Cada linha começa com uma das três marcas, escritas exatamente assim:

| Marca | Na tela |
| --- | --- |
| `[CARA] fala` | quem apresenta grande, sem animação |
| `[ANIM: o que aparece] fala` | só a animação |
| `[CANTO: o que aparece] fala` | a animação, com quem apresenta pequeno num canto |

As marcas são escritas sempre, mesmo enquanto a gravação for só com a cara: são elas que guiam as animações e a montagem depois.

Exemplo (um trecho; o vídeo inteiro tem 8 a 14 linhas):

```
[CARA] Sabe como o banco decide se te dá crédito?
[ANIM: árvore de perguntas sim/não] Muitas vezes, com uma árvore de decisão.
[CANTO: a primeira pergunta se divide em sim e não] É tipo jogo de adivinhação: uma pergunta por vez.
[ANIM: o caminho até "aprovado" acende] Tem renda fixa? Sim. Paga em dia? Sim. Aprovado.
[CARA] Segue pra mais IA sem complicação.
```

## Regras do canal

1. **Público leigo.** Todo termo técnico vem explicado com algo do dia a dia, na mesma linha ou na seguinte.
2. **Teoria sempre com exemplo.** Cada conceito ganha um caso concreto logo em seguida. Nunca duas linhas seguidas sem nenhum caso concreto.
3. **60 segundos, uma ideia por vídeo.** Alvo de 120 a 140 palavras faladas; 150 é o teto, porque a leitura no teleprompter, com pausas, sai mais lenta que a conta. Isso dá 8 a 14 linhas. Conta como palavra tudo que tem letra ou número, sem contar as marcas.
4. **A primeira linha é um gancho:** uma pergunta ou um fato curioso. Nada de "Olá, hoje vamos falar de…".
5. **Frases curtas, para ler em voz alta.** Uma ideia por linha, 5 a 20 palavras. Leia mentalmente em voz alta: se tropeça, reescreva.
6. **Toda linha começa com uma marca.**
7. **As marcas se alternam.** Nunca três linhas seguidas com a mesma marca. Quem apresenta não fica muito tempo sumido (`[ANIM]`) nem muito tempo parado na tela (`[CARA]`). Entre a primeira e as duas últimas linhas, `[CARA]` aparece em uma linha por vez.
8. **Termina com uma linha `[CARA]` de fechamento**, tirada de `voz.md`. A conclusão do vídeo pode vir logo antes, também em `[CARA]`.
9. **Fala do jeito de quem apresenta**, seguindo `voz.md`. Na dúvida entre uma palavra bonita e uma comum, fica a comum.
10. **Fatos certos.** Nome, data e número só entram com certeza. Assunto disputado (ex.: "pai do deep learning" tem mais de um candidato) vira parte da história, em vez de escolher um lado. Exemplo inventado é dito como possibilidade ("um banco pode…"), não como fato ("os bancos fazem…").

## O que vai dentro de `[ANIM: …]` e `[CANTO: …]`

A descrição é o pedido para a cena Manim daquela linha, então ela diz o que se vê, não o que se explica.

- Só o que o Manim desenha bem sobre fundo preto: formas, setas, números, gráficos, linhas do tempo.
- Ritmo de Reels, não de slide: texto na tela só como rótulo curto (até 3 palavras, num nó, eixo ou destaque). Frase ou lista de tópicos, nunca.
- A imagem acompanha a fala daquela linha. Se a fala diz "aprovado", é ali que "aprovado" acende.
- Sem colchetes dentro da descrição nem da fala: o primeiro `]` fecha a marca. Use parênteses ou aspas (`[ANIM: o vetor (0, 1, 0) acende]`).
- Linhas seguidas podem continuar a mesma cena ("o caminho até 'aprovado' acende" continua a árvore de antes).
- Em `[CANTO]`, a cena é mais simples e deixa um canto livre para quem apresenta.
- Precisa de foto (ex.: o rosto de um pesquisador)? Escreva `foto: …` na descrição e avise no chat. Quem apresenta decide.

## Entrega

Antes de entregar, confira cada item:

- [ ] Uma ideia só, e o gancho na linha 1
- [ ] 120 a 140 palavras faladas, nunca mais que 150
- [ ] Toda linha com marca, nenhuma marca três vezes seguidas
- [ ] Todo termo técnico explicado e todo conceito com exemplo
- [ ] Última linha `[CARA]` de fechamento
- [ ] Arquivo só com as linhas, sem linha em branco no meio

Depois de salvar, marque o tema em `temas.md`: troque `- [ ]` por `- [x]`. Tema que não está lá, ou está em Sugestões, entra em Ideias já marcado, com o slug.

No chat, nesta ordem:

1. Se `voz.md` não tinha frases de exemplo: o aviso, pedindo 3 a 5 frases do jeito que quem apresenta fala.
2. A ideia do vídeo, numa frase.
3. O caminho do arquivo, o número de linhas, a contagem de palavras e a duração estimada (palavras ÷ 2,5 = segundos).
4. O que vale conferir antes de gravar, se houver: afirmações, simplificações, pedidos de foto.
5. Se o comando `humanim gravar` ainda não existe: as falas sem as marcas, num único bloco de código, uma fala por linha, prontas para colar no app de teleprompter do celular.

## Ajustes

- "Ajusta a linha 3 de videos/arvore-de-decisao": mude só a linha 3 daquela pasta e mostre como ficou.
- Se a pasta já tem `tempos.json` ou `gravacao.webm`, avise antes de incluir, tirar ou trocar linhas de lugar, ou de mudar o texto de uma fala: os tempos gravados deixam de bater (ou o áudio fica com o texto antigo) e a gravação precisa ser refeita. Mudar só a descrição de [ANIM] ou [CANTO] não pede gravação nova.
- Quando quem apresenta reescrever uma fala com as próprias palavras, ofereça guardar a frase em `voz.md`. É assim que a skill fica mais parecida com quem apresenta a cada vídeo.

## Ideias de vídeo

Quando pedirem ideias, proponha 5, uma por linha, no formato de `temas.md`: a pergunta que o vídeo responde e o slug. Cada uma tem que caber em 60 s e ter um caso do dia a dia. Só grave em `temas.md` as que forem aprovadas, na seção Ideias.
