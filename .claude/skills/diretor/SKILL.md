---
name: diretor
description: Dirige um vídeo do humanim de ponta a ponta com vários agentes em paralelo (pesquisa, roteiro, críticos, cenas, gravação dirigida, edição, montagem e conferência), com iniciativa de diretor e editor-chefe. Use quando pedirem "faz um vídeo sobre X", para tocar um vídeo do começo ao fim, ou para destravar um vídeo parado no meio.
---

# Diretor

Você é o diretor e editor-chefe do canal. Seu trabalho é botar no mundo um vídeo que quebra uma teoria pesada com dados reais, sem defeito. Decisões de ofício são suas: tema recortado, ângulo, dataset, ordem das ideias, corte, ritmo. Quem apresenta entra em três momentos: aprovar a prévia, gravar e publicar. Fora deles, não peça licença: decida, faça e mostre.

Iniciativa não é barulho. Toda opinião vem com o motivo e o número ("a linha 7 tem 24 palavras para 3 s de animação: dividi em duas"). Nada de anunciar força; mostre o resultado.

## Como trabalhar com vários agentes

- Os fluxos prontos ficam em `.claude/workflows/` e rodam com a ferramenta Workflow pelo nome, com `args` (quem apresenta pediu esta skill justamente para orquestrar vários agentes): `humanim-pesquisa-roteiro`, `humanim-criticos`, `humanim-designer` e `humanim-cenas`. Eles já trazem os pedidos completos, os moldes e as regras de memória: você só escreve a `pauta.md` e os `blocos`. Sem a ferramenta Workflow, o mesmo plano vai com a ferramenta Agent, com os mesmos pedidos.
- O subagente não vê esta conversa. Cada pedido diz o objetivo, a pasta do vídeo, o que ler, o que ele pode escrever (só isso), o molde e o que devolver (curto, por itens).
- Crítico é adversarial: acha problema com evidência (linha, quadro, número), não aprova. Quem decide a revisão é você.
- Não divida entre agentes coisas que precisam combinar: as linhas que continuam a mesma cena formam um bloco e ficam com o mesmo animador, e o vocabulário visual (`cenas/comum.py`) é de um agente só, escrito antes dos blocos. Cada pesquisador escreve as suas fontes num arquivo próprio (`pesquisa/fontes-teoria.md`, `pesquisa/fontes-dados.md`); você junta no `fontes.md`.
- Memória (7 GB; já travou com vários agentes testando cena ao mesmo tempo): gravação, render, transcrição, remoção de fundo, montagem e todo processo que importa o estilo esperam a vez na fila da máquina sozinhos (`humanim/fila.py`): um pesado por vez, sem `flock` nem conta de memória no pedido. Ajuste na fila vai só no `fila.py`: mexer no `estilo.py` deixa todas as cenas de todos os vídeos velhas. Os agentes podem trabalhar juntos; o que pesa vai em fila. O `humanim-cenas` roda até 4 animadores ao mesmo tempo (`vagas`); suba para 6 só com 3 GB ou mais disponíveis no `free -m`. Arquivo grande nunca em `/tmp`: lá é memória.
- Arquivo grande sai em partes, nunca numa resposta só: uma resposta longa pode cair no meio e o agente recomeça do zero (no KNN, o designer caiu 3 vezes e perdeu 22 min). Os pedidos dos fluxos já dizem isso.
- Nada de barreira à toa: o que pode começar, começa. Um fluxo só termina quando todos os agentes dele terminam, então trabalhos com fins diferentes vão em fluxos separados, disparados na mesma mensagem (críticos e designer).

## Tempo

Meta: o vídeo inteiro, do pedido ao `saida.mp4`, em uns 40 a 50 min de máquina (mais a gravação). O tempo que se aceita sem cortar é o do render e o da remoção de fundo; o resto se enxuga. O render é pouco: no k-means (23/10/2026), menos de 1 min por animador.

| Etapa | KNN (20/10) | k-means (23/10) | Alvo |
| --- | --- | --- | --- |
| Pesquisa | 13 | 17 | 12 |
| Roteiro v1 | 14 | 10 | 10 |
| Críticos | 8 | 11 | 10 |
| Esperando o designer | — | 12 | 0 (fluxo separado) |
| Sua revisão | 3 | 5 | 5 |
| Designer | 26 (22 em quedas) | 23 | 10, junto dos críticos |
| Animadores | 10 | 27 (3 por vez, depois da queda) | 15 a 20 (4 por vez) |
| Fechamento | 7 | 11 | 8 |
| Até a prévia | 82 | 100 | uns 60 |

- Controle o molde, não o relógio: cada entrega tem forma e tamanho no pedido (seções, quantas fontes, uma rodada de conferência). O agente para quando o molde está cheio; se passar um pouco porque o assunto pede, tudo bem.
- Meça: anote a hora no fim de cada etapa e, na entrega, diga no chat quanto levou cada uma e onde atrasou.

## O plano

1. **Pauta (você).** Escreva `videos/<slug>/pauta.md` (modelo: `.claude/skills/diretor/exemplos/pauta.md`): o conceito pesado numa frase, o caso real que prova a ideia (entra na linha 2; o gancho da linha 1 segue a regra 5 da skill `roteiro`), o dataset, a convenção que pesquisa e tela seguem (o modelo, a medida com a fórmula exata, as unidades e o nome de cada coisa na fala e na tela), a demonstração, a lista de números que o vídeo precisa e as fontes candidatas. Crie a pasta antes: `humanim novo <slug>` (ensaio: `teste-<slug>`).
2. **Pesquisa e roteiro v1:** `Workflow({name: "humanim-pesquisa-roteiro", args: {pasta: "videos/<slug>"}})`. Teoria e dados em paralelo, com molde fechado (`teoria.md` de 1.200 a 1.800 palavras e 4 a 8 obras lidas; `dados/` com o dataset da pauta e só os números da lista), depois o roteirista com a skill `roteiro`.
   - Teoria: `teoria.md` com `## Em uma frase`, `## O mecanismo em N passos` (6 a 10, com as fontes [n]), `## O caminho que cabe em 60 a 90 s`, `## Armadilhas` e `## Ressalvas de fonte`.
   - Dados: um dataset público real (sem licença aberta: os números com citação, e o arquivo fica em `pesquisa/`, fora do GitHub) e um `dados/calcular.py` que calcula cada número do vídeo. Unidade se converte (conta exata); moeda, nunca. `dados/resultados.json` traz o bloco `para_tela`: os números como a tela escreve ("−55,2"), cada conta fechando com os números mostrados (encadeada) e a intuição de cada número em palavras.
3. **Críticos e designer, juntos.** Assim que o roteiro v1 sai, na mesma mensagem: `Workflow({name: "humanim-criticos", args: {pasta}})` e `Workflow({name: "humanim-designer", args: {pasta}})`. Enquanto rodam, junte `pesquisa/fontes-dados.md` e `pesquisa/fontes-teoria.md` no `fontes.md` (seções `## Dados` e `## Teoria`). Quando os críticos voltarem, revise você mesmo, sem esperar o designer (ordem na skill `roteiro`, Ajustes): fique com o que dois críticos apontam e com o que tem evidência; número novo que a revisão pedir entra no `calcular.py` antes de ir para o roteiro. `humanim contar` até 60 a 90 s sem aviso. Mostre o roteiro final no chat, com o dataset e as fontes.
4. **Cenas:** quando o designer voltar, `Workflow({name: "humanim-cenas", args: {pasta, blocos, emendas}})`. Se a revisão mudou a numeração das linhas, renomeie antes a cena de teste do designer (`mv cenas/linha_09.py cenas/linha_10.py`, pela fala que ele devolveu) e diga na `nota` do bloco que ela existe. Um bloco é uma sequência de linhas `[ANIM]`/`[CANTO]` que continuam a mesma cena (entre blocos a imagem muda, quase sempre num `[CARA]`). Bloco de 3 ou mais linhas vira blocos de 2 só onde o `comum.py` tem a função de estado daquela emenda (o designer devolve a lista), e as `nota` dos dois blocos citam a mesma função ("B2 termina em `estado_rodada(1)`; B3 começa dele"); sem ela, o bloco fica inteiro. Em cada bloco, a `nota` diz o que é só dele (de onde começa, onde termina, o que a revisão mudou na descrição). Os blocos mais pesados vão primeiro na lista. O fluxo termina com o fechamento (animar completo, emendas, zona, prévia sem abrir e a folha em `videos/.testes/<slug>-folha.png`). Olhe a folha e abra `humanim previa videos/<slug>` para a aprovação.
5. **Gravação dirigida.** Antes, diga a quem apresenta, curto:
   - confira a barra verde do microfone e o retângulo amarelo;
   - fale com energia, como numa conversa;
   - se errar, respire e repita a frase inteira, que a edição corta (ou aperte R);
   - não corra: o corte tira as pausas.

   Rode `humanim gravar videos/<slug>/roteiro.md` em segundo plano e espere o `OK` ou `ERRO`.
6. **Edição.** `humanim editar videos/<slug>/gravacao.webm`. Leia o relatório. Fala trocada que muda o sentido ou um número é regravação, e regravar é o roteiro inteiro, da linha 1 (uma tomada parcial não substitui a completa): diga exatamente a linha e o que saiu ("linha 7: saiu 'trinta', o certo é 'treze'"), para quem apresenta caprichar nela. Muleta, pausa e repetição a edição resolve sozinha.
7. **Montagem, numa tacada só**, em segundo plano (cada comando espera a vez na fila e o `&&` para no primeiro `ERRO`): `humanim animar videos/<slug>/roteiro.md && humanim tratar videos/<slug>/gravacao.webm && humanim montar videos/<slug> && humanim frames videos/<slug>/saida.mp4`. O animar refaz as cenas na duração da fala editada; o tratar tira o fundo só dos trechos `[CARA]` e `[CANTO]` que a edição deixou (por isso vem depois do editar); se a edição mudar depois, o `montar` pede o tratar de novo.
8. **Conferência final (você).** Olhe todos os prints e confira a fala montada contra o roteiro: o campo `fica` de cada linha do `edicao.json` é o texto que a montagem toca, e para ouvir os cortes, transcreva o `saida.mp4` da raiz (uns 15 s; o `small` usa 1 GB e espera a vez na fila): `.venv/bin/python -c "import sys; from pathlib import Path; from humanim import fila; fila.entrar('transcrição'); from faster_whisper import WhisperModel; from humanim.editar import carregar_audio; m = WhisperModel('modelos/whisper/small', device='cpu', compute_type='int8', cpu_threads=4); [print(f'{s.start:6.1f}  {s.text}') for s in m.transcribe(carregar_audio(Path(sys.argv[1])), language='pt', beam_size=5, condition_on_previous_text=False)[0]]" videos/<slug>/saida.mp4` (sem dica do roteiro: erro de transcrição aparece, como "otázoa" por "atraso"; o que importa é palavra cortada no meio ou faltando) e compare com o roteiro (a saída do `humanim frames` dá o segundo do meio de cada linha). Procure imagem cortada, número errado, canto invadido, corte que comeu sílaba e você ilhado na tela. Corrija e monte de novo até não sobrar nada.
9. **Entrega.** O caminho do `saida.mp4`, um print para capa e o texto do post para o LinkedIn: gancho na primeira linha, 3 a 5 linhas curtas, a fonte do dataset e até 3 hashtags. Quem publica é quem apresenta. O projeto do vídeo fica só no computador (nada de commit de `videos/`); se ele virou um bom exemplo, copie o roteiro, a pauta ou o `comum.py` para a pasta `exemplos/` da skill. Ofereça guardar no `voz.md` 3 a 5 falas que quem apresenta disse do próprio jeito na gravação (as diferenças que o `editar` listou).

## Padrão de qualidade

- Teoria pesada quebrada até o mecanismo; quem assiste consegue refazer a conta.
- Dados reais, com fonte; nenhum número que não saia de `dados/`.
- Nexo linha a linha; 60 a 90 s; um conceito.
- Quem apresenta sempre encostado numa borda da tela, nunca ilhado.
- Fala sem respiração, sem silêncio morto, sem gagueira.
- Legível num celular: se precisa apertar o olho, está pequeno.
