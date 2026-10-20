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
  modelos/                  # remoção de fundo e modelos de fala em whisper/ (baixam sozinhos; fora do Git)
  videos/                   # uma pasta por vídeo (fora do Git)
    <slug>/
      roteiro.md  cenas/  tempos.json  gravacao.webm  edicao.json  gravacao-tratada.webm  saida.mp4  frames/
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
5. `humanim gravar videos/<slug>/roteiro.md` **em segundo plano**: abre o teleprompter e só termina quando a gravação é salva. Explique as teclas antes: Espaço começa (contagem 3, 2, 1) e passa de linha, R regrava a linha atual, Esc para e salva. Peça para ficar dentro do retângulo amarelo da prévia da câmera (é o que o `[CARA]` mostra nos dois planos, com e sem zoom), com a cabeça abaixo da faixa escura de cima (lá fica a interface do app). Diga que travar não é problema: respira e repete a frase inteira, que a edição corta. Espere o `OK` ou `ERRO`.
6. `humanim editar videos/<slug>/gravacao.webm` corta da fala o que não é roteiro: silêncio e respiração longos (fica uma pausa curta), muleta (é, hã, hum), repetição, gagueira e começo errado (fica a última tentativa inteira). Transcreve no computador (uns 30 s para 90 s de fala; na primeira vez baixa o modelo, 1,6 GB) e escreve `edicao.json`, que animar, prévia, montar e frames passam a usar. Leia o relatório: as linhas em que a fala saiu diferente do roteiro (palavra trocada ou faltando) vêm listadas. Palavra que muda o sentido ou um número é regravação; erro da transcrição (o áudio está certo) segue.
7. `humanim animar videos/<slug>/roteiro.md` de novo. Com a duração da fala editada, as cenas são refeitas na medida certa.
8. `humanim tratar videos/<slug>/gravacao.webm` em segundo plano. Remove o fundo (3 a 6 min para 60 s). Com ele, o `[CANTO]` mostra só você, cortado no peito e encostado na borda de baixo e na esquerda; sem ele, a imagem da câmera num retângulo encostado no canto inferior esquerdo.
9. `humanim montar videos/<slug>` gera `saida.mp4`: cada linha é a soma dos trechos que a edição deixou, vídeo e áudio cortados no mesmo quadro; nos cortes do `[CARA]` o zoom alterna (100% e 112%) para o pulo parecer troca de plano.
10. `humanim frames videos/<slug>/saida.mp4` tira um print por linha. Olhe todos. Ajuste o que estiver errado e monte de novo.
11. Entregue o caminho do `saida.mp4`. Quem publica é quem apresenta.

Gravou de novo? Rode `editar` de novo antes de animar: o `edicao.json` guarda de que gravação ele é, e os comandos param com `ERRO` se ele ficou velho. Os trechos do `edicao.json` também podem ser ajustados à mão (segundos da gravação, em ordem).

## Decisões técnicas

- Webcam de 720p: o `[CARA]` recorta 9:16 e amplia, então fica um pouco mais suave. É limite do hardware.
- Correção de olhar: fora do MVP. O teleprompter cola a frase embaixo da webcam, e o desvio fica dentro do que não se nota.
- Sem LaTeX na máquina: nada de `MathTex`/`Tex` nas cenas (a skill `cenas` lista as alternativas).
- Pouca memória livre: `HUMANIM_PARALELO=2 humanim animar ...` renderiza menos cenas ao mesmo tempo.
- Transcrição do `editar`: faster-whisper na CPU, modelo `large-v3-turbo` (uns 30 s e até 2,6 GB de memória para 90 s de fala nesta máquina), que transcreve gagueira e muleta que modelos menores engolem. Com menos de 3 GB livres ele usa o `small` (15 s, 1 GB) e avisa no relatório, a não ser que a gravação já tenha sido transcrita com o turbo (a transcrição fica em `.trabalho/` e é reaproveitada sem carregar modelo). Se o modelo falhar, o `ERRO` diz o que fazer. `HUMANIM_WHISPER=<modelo>` escolhe. Os modelos ficam em `modelos/whisper/`.
- O `[CANTO]` fica encostado no canto inferior esquerdo (`formato.CANTO`), nunca solto no meio da tela: você toca a borda de baixo e a esquerda.
