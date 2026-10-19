# humanim

O Manim com um humano dentro: shorts verticais de 60 s no LinkedIn explicando IA para leigos, com a cara e a voz de quem apresenta. A especificação completa está em https://claude.ai/artifact/PefFxxn3cCWEqqqf2EZt1b.

## Como o repositório funciona

```
humanim/
  CLAUDE.md                 # este arquivo
  .claude/skills/roteiro/   # escrever roteiros: SKILL.md, voz.md, temas.md
  .claude/skills/cenas/     # escrever as cenas Manim de cada linha
  estilo/estilo.py          # cores, fonte e fundo das animações
  humanim/                  # o código do comando humanim
  modelos/                  # modelo de remoção de fundo (baixa sozinho; fora do Git)
  videos/                   # uma pasta por vídeo (fora do Git)
    <slug>/
      roteiro.md  cenas/  tempos.json  gravacao.webm  gravacao-tratada.webm  saida.mp4  frames/
      anteriores/           # gravações trocadas por uma nova, e tomadas parciais que não substituíram a completa
```

- O Claude é aberto uma vez, na raiz. Para mexer num vídeo, a pasta é apontada ("ajusta a linha 3 de videos/arvore-de-decisao") e o trabalho fica só ali.
- O comando é `humanim` (o `./instalar.sh` põe um link em `~/.local/bin`; sem ele, use `.venv/bin/humanim`). Rode sempre da raiz, com os caminhos `videos/<slug>/...`. Toda saída começa com `OK` ou `ERRO`, e todo erro diz onde está e o que fazer, com os comandos já prontos para colar.
- Commits levam só código, skills e estilo; `videos/` e `modelos/` ficam fora.

## Fazer um vídeo

Quando pedirem "faz um vídeo sobre X", siga na ordem. Quem apresenta entra em três pontos: aprovar a prévia, gravar e publicar.

1. `humanim novo <slug>` cria `videos/<slug>/`.
2. Roteiro com a skill `roteiro`. Mostre o roteiro no chat.
3. Cenas com a skill `cenas`: uma `cenas/linha_NN.py` por linha `[ANIM]`/`[CANTO]`. Renderize com `humanim animar videos/<slug>/roteiro.md` e confira cada cena com `humanim frames videos/<slug>/cenas/linha_NN.mp4`, olhando as imagens. Conserte o que estiver cortado, ilegível ou invadindo o canto.
4. `humanim previa videos/<slug>` abre a prévia no Chrome, com as durações estimadas. Peça a aprovação. Se pedirem mudança, ajuste roteiro ou cenas, rode `animar` e `previa` de novo.
5. `humanim gravar videos/<slug>/roteiro.md` **em segundo plano**: abre o teleprompter e só termina quando a gravação é salva. Explique as teclas antes: Espaço começa (contagem 3, 2, 1) e passa de linha, R regrava a linha atual, Esc para e salva. Peça para ficar dentro do retângulo amarelo da prévia da câmera (é o que o `[CARA]` usa), com a cabeça abaixo da faixa escura de cima (lá fica a interface do app). Espere o `OK` ou `ERRO`.
6. `humanim animar videos/<slug>/roteiro.md` de novo. Com os tempos reais, as cenas são refeitas na duração certa.
7. `humanim tratar videos/<slug>/gravacao.webm` em segundo plano. Remove o fundo (3 a 6 min para 60 s). Sem ele, o `[CANTO]` mostra você num retângulo.
8. `humanim montar videos/<slug>` gera `saida.mp4`.
9. `humanim frames videos/<slug>/saida.mp4` tira um print por linha. Olhe todos. Ajuste o que estiver errado e monte de novo.
10. Entregue o caminho do `saida.mp4`. Quem publica é quem apresenta.

## Decisões técnicas

- Webcam de 720p: o `[CARA]` recorta 9:16 e amplia, então fica um pouco mais suave. É limite do hardware.
- Correção de olhar: fora do MVP. O teleprompter cola a frase embaixo da webcam, e o desvio fica dentro do que não se nota.
- Sem LaTeX na máquina: nada de `MathTex`/`Tex` nas cenas (a skill `cenas` lista as alternativas).
- Pouca memória livre: `HUMANIM_PARALELO=2 humanim animar ...` renderiza menos cenas ao mesmo tempo.
