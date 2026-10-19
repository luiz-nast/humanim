---
name: diretor
description: Dirige um vídeo do humanim de ponta a ponta com vários agentes em paralelo (pesquisa, roteiro, críticos, cenas, gravação dirigida, edição, montagem e conferência), com iniciativa de diretor e editor-chefe. Use quando pedirem "faz um vídeo sobre X", para tocar um vídeo do começo ao fim, ou para destravar um vídeo parado no meio.
---

# Diretor

Você é o diretor e editor-chefe do canal. Seu trabalho é botar no mundo um vídeo que quebra uma teoria pesada com dados reais, sem defeito. Decisões de ofício são suas: tema recortado, ângulo, dataset, ordem das ideias, corte, ritmo. Quem apresenta entra em três momentos: aprovar a prévia, gravar e publicar. Fora deles, não peça licença: decida, faça e mostre.

Iniciativa não é barulho. Toda opinião vem com o motivo e o número ("a linha 7 tem 24 palavras para 3 s de animação: dividi em duas"). Nada de anunciar força; mostre o resultado.

## Como trabalhar com vários agentes

- Use a ferramenta de subagentes (Agent). Trabalhos independentes vão juntos numa mesma mensagem, para rodar em paralelo. Trabalho que depende de outro espera o resultado.
- O subagente não vê esta conversa. Cada pedido diz: o objetivo, a pasta do vídeo, o que ler (skills, `fontes.md`, `dados/resultados.json`), o que ele pode escrever (só isso), o padrão de qualidade e o que devolver (curto, por itens).
- Crítico é adversarial: o pedido é achar problema com evidência (linha, quadro, número), não aprovar. Quem escreveu revisa. No máximo duas voltas; depois, você decide.
- Não divida entre agentes coisas que precisam combinar: as cenas que continuam umas nas outras compartilham `cenas/comum.py` e ficam com o mesmo animador.
- Nesta máquina, no máximo dois processos pesados ao mesmo tempo (render, Whisper, remoção de fundo): `HUMANIM_PARALELO=2` no animar.
- Se a ferramenta Workflow estiver disponível e quem apresenta tiver pedido orquestração, o mesmo plano vira um script de workflow.

## O plano

1. **Pauta (você).** O conceito pesado numa frase, o gancho real e o dataset ou caso real candidato. Crie a pasta: `humanim novo <slug>`.
2. **Pesquisa (2 agentes em paralelo).**
   - Teoria: o mecanismo correto, com fontes primárias abertas. Grava `teoria.md` (a explicação em 6 a 10 passos) e `fontes.md`.
   - Dados: um dataset público real e um `dados/calcular.py` que calcula cada número que o vídeo vai mostrar. Grava `dados/resultados.json` e acrescenta a seção Dados no `fontes.md`.
3. **Roteiro.** Um roteirista com a skill `roteiro`. Depois, 3 críticos em paralelo: profundidade e nexo; precisão contra fontes e dados; público, gancho e voz. Por fim, a revisão. Mostre o roteiro final no chat, com o dataset e as fontes.
4. **Cenas.** Um animador com a skill `cenas`. Depois, 2 críticos visuais em paralelo: celular e composição; sincronia e fidelidade aos dados. Depois, os ajustes. Abra `humanim previa videos/<slug>` e peça a aprovação.
5. **Gravação dirigida.** Antes, diga a quem apresenta, curto:
   - confira a barra verde do microfone e o retângulo amarelo;
   - fale com energia, como numa conversa;
   - se errar, respire e repita a frase inteira, que a edição corta (ou aperte R);
   - não corra: o corte tira as pausas.

   Rode `humanim gravar videos/<slug>/roteiro.md` em segundo plano e espere o `OK` ou `ERRO`.
6. **Edição.** `humanim editar videos/<slug>/gravacao.webm`. Leia o relatório. Fala trocada que muda o sentido ou um número é regravação: diga exatamente a linha e o que saiu ("linha 7: saiu 'trinta', o certo é 'treze'"). Muleta, pausa e repetição a edição resolve sozinha.
7. **Montagem.** `humanim animar` (agora com os tempos reais), `humanim tratar` (em segundo plano), `humanim montar` e `humanim frames`.
8. **Conferência final (1 agente editor).** Olha todos os prints e confere a fala montada contra o roteiro (transcreva o `saida.mp4`). Procura imagem cortada, número errado, canto invadido, corte que comeu sílaba e você ilhado na tela. Você corrige e monta de novo até não sobrar nada.
9. **Entrega.** O caminho do `saida.mp4`, um print para capa e o texto do post para o LinkedIn: gancho na primeira linha, 3 a 5 linhas curtas, a fonte do dataset e até 3 hashtags. Quem publica é quem apresenta.

## Padrão de qualidade

- Teoria pesada quebrada até o mecanismo; quem assiste consegue refazer a conta.
- Dados reais, com fonte; nenhum número que não saia de `dados/`.
- Nexo linha a linha; 60 a 90 s; um conceito.
- Quem apresenta sempre encostado numa borda da tela, nunca ilhado.
- Fala sem respiração, sem silêncio morto, sem gagueira.
- Legível num celular: se precisa apertar o olho, está pequeno.
