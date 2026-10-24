# humanim

O Manim com um humano dentro: shorts verticais de 60 a 90 s no LinkedIn explicando IA para leigos, com a cara e a voz de quem apresenta. A especificação completa está em https://claude.ai/artifact/PefFxxn3cCWEqqqf2EZt1b.

## Como o repositório funciona

```
humanim/
  CLAUDE.md                 # este arquivo
  .claude/skills/diretor/   # tocar um vídeo do começo ao fim, com vários agentes
  .claude/skills/roteiro/   # escrever roteiros: SKILL.md, voz.md, temas.md
  .claude/skills/cenas/     # escrever as cenas Manim de cada linha
  estilo/estilo.py          # cores, fonte, fundo e peças das animações (rotulo, conta, br, lupa)
  humanim/                  # o código do comando humanim
  modelos/                  # remoção de fundo e modelos de fala em whisper/ (baixam sozinhos; fora do Git)
  videos/                   # uma pasta por vídeo, só no computador (fora do Git)
    <slug>/
      teoria.md  fontes.md  dados/  pesquisa/  # a pesquisa: o mecanismo, as fontes, os números e o material bruto
      roteiro.md  cenas/  tempos.json  gravacao.webm  edicao.json  gravacao-tratada.webm  saida.mp4  frames/
      anteriores/           # gravações trocadas por uma nova, e tomadas parciais que não substituíram a completa
```

- O Claude é aberto uma vez, na raiz. Para mexer num vídeo, a pasta é apontada ("ajusta a linha 3 de videos/arvore-de-decisao") e o trabalho fica só ali.
- O comando é `humanim` (o `./instalar.sh` põe um link em `~/.local/bin`; sem ele, use `.venv/bin/humanim`). Rode sempre da raiz, com os caminhos `videos/<slug>/...`. Toda saída começa com `OK` ou `ERRO`, e todo erro diz onde está e o que fazer, com os comandos já prontos para colar.
- Vai para o GitHub: o código, as skills (com os exemplos que os agentes leem em `.claude/skills/*/exemplos/`), os fluxos de agentes e o estilo. Os projetos dos vídeos (`videos/`) ficam só no computador, por decisão de quem apresenta (23/10/2026): nada de commit de vídeo. Dataset, PDF e mídia continuam fora pelo mesmo motivo. Um bom roteiro, pauta ou `comum.py` que valha de exemplo vai para a pasta `exemplos/` da skill, copiado.

## Fazer um vídeo

Quando pedirem "faz um vídeo sobre X", a skill `diretor` toca tudo, com vários agentes; os passos abaixo são o fio. Quem apresenta entra em três pontos: aprovar a prévia, gravar e publicar.

1. `humanim novo <slug>` cria `videos/<slug>/`.
2. Pesquisa (`teoria.md`, `fontes.md` e `dados/`, como diz a skill `diretor`) e roteiro com a skill `roteiro`. `humanim contar videos/<slug>/roteiro.md` dá a duração de cada linha e o segundo de cada gatilho. Mostre o roteiro no chat.
3. Cenas com a skill `cenas`: uma `cenas/linha_NN.py` por linha `[ANIM]`/`[CANTO]`. Renderize com `humanim animar videos/<slug>/roteiro.md` (o vídeo inteiro leva uns 2 a 3 min: em segundo plano ou com timeout maior que os 2 min do Bash) e confira cada cena com `humanim frames videos/<slug>/cenas/linha_NN.mp4`, olhando as imagens. Conserte o que estiver cortado, ilegível ou invadindo o canto.
4. `humanim previa videos/<slug>` abre a prévia no Chrome (na primeira vez; depois, peça para recarregar a aba), com as durações estimadas. Peça a aprovação. Se pedirem mudança, ajuste roteiro ou cenas, rode `animar` e `previa` de novo. Linha listada em "Falta animar" (cena que mudou depois do render, ou o comum.py, o estilo ou o ritmo da fala) aparece com o clipe antigo: anime antes de pedir a aprovação.
5. `humanim gravar videos/<slug>/roteiro.md` **em segundo plano**: abre o teleprompter e só termina quando a gravação é salva (segura a vez na fila: nada pesado começa no meio de uma tomada). Explique as teclas antes: Espaço começa (contagem 3, 2, 1) e passa de linha, R regrava a linha atual, Esc para e salva. Peça para ficar dentro do retângulo amarelo da prévia da câmera (é a largura que o `[CARA]` mostra nos dois planos; a faixa amarelada de baixo só aparece no plano sem zoom, então rosto e mãos acima dela), com a cabeça abaixo da faixa escura de cima (lá fica a interface do app). Diga que travar não é problema: respira e repete a frase inteira, que a edição corta. Espere o `OK` ou `ERRO`. Se a janela fechar ou travar (ou o Chrome não abrir), ele não fica esperando: sai com `ERRO` (10 s depois, se estava gravando) e guarda o que foi gravado como tomada parcial em `anteriores/`, sem mexer na gravação que já existia.
6. `humanim editar videos/<slug>/gravacao.webm` corta da fala o que não é roteiro: silêncio e respiração longos (fica uma pausa curta), muleta (é, hã, hum), repetição, gagueira e começo errado (fica a última tentativa inteira). Transcreve no computador (uns 30 a 50 s para 90 s de fala; na primeira vez baixa o modelo, 1,6 GB) e escreve `edicao.json`, que animar, prévia, montar e frames passam a usar. Leia o relatório: as linhas em que a fala saiu diferente do roteiro (palavra trocada ou faltando) vêm listadas. Antes de listar, ele ouve de novo cada uma dessas linhas com o roteiro como dica: o que era erro da transcrição some da lista (vai para as diferenças pequenas, "ouvida de novo... bate"), e o que continua listado foi dito diferente. Palavra que muda o sentido ou um número é regravação; erro da transcrição (o áudio está certo) segue. Regravar é o roteiro inteiro, da linha 1 (uma tomada parcial não substitui a completa): diga a quem apresenta a linha e o que saiu, para caprichar nela.
7. `humanim animar videos/<slug>/roteiro.md` de novo. Com a duração da fala editada, as cenas são refeitas na medida certa. Os passos 7 a 10 vão numa tacada só, em segundo plano: `humanim animar videos/<slug>/roteiro.md && humanim tratar videos/<slug>/gravacao.webm && humanim montar videos/<slug> && humanim frames videos/<slug>/saida.mp4` (cada um espera a vez na fila, e o `&&` para no primeiro `ERRO`).
8. `humanim tratar videos/<slug>/gravacao.webm` em segundo plano, sozinho: o segundo plano é só para não estourar o tempo limite do Bash; espere o `OK` dele antes do `montar`. Remove o fundo só do que a montagem mostra: o miolo 3:4 da imagem e os trechos `[CARA]` e `[CANTO]` que a edição deixou (uns 2 min para um vídeo de 90 s; por isso vem depois do `editar`, e se a edição mudar, o `montar` pede o tratar de novo). Com ele, o `[CANTO]` mostra só você, cortado no peito e encostado na borda de baixo e na esquerda, e no `[CARA]` fica atrás de você a animação vizinha, parada, desfocada e escurecida (a última antes da linha, ou a primeira depois); sem ele, a imagem da câmera, com o cenário, num retângulo encostado no canto inferior esquerdo.
9. `humanim montar videos/<slug>`, depois do tratar (com o tratar ainda rodando, ele espera a vez na fila), gera `saida.mp4`: cada linha é a soma dos trechos que a edição deixou, vídeo e áudio cortados no mesmo quadro; nos cortes do `[CARA]` o zoom alterna (100% e 112%) para o pulo parecer troca de plano.
10. `humanim frames videos/<slug>/saida.mp4` tira um print por linha. Olhe todos. Ajuste o que estiver errado e monte de novo.
11. Entregue o caminho do `saida.mp4`. Quem publica é quem apresenta.

Gravou de novo? Rode `editar` de novo antes de animar: o `edicao.json` guarda de que gravação ele é, e os comandos param com `ERRO` se ele ficou velho (uma cópia vai para `anteriores/` com a gravação antiga). Os trechos do `edicao.json` também podem ser ajustados à mão (segundos da gravação, em ordem); rodar o `editar` de novo guarda o ajuste em `edicao-anterior.json`.

## Decisões técnicas

- Webcam de 720p: o `[CARA]` recorta 9:16 e amplia, então fica um pouco mais suave. É limite do hardware.
- Correção de olhar: fora do MVP. O teleprompter cola a frase embaixo da webcam, e o desvio fica dentro do que não se nota.
- Sem LaTeX na máquina: nada de `MathTex`/`Tex` nas cenas (a skill `cenas` lista as alternativas).
- Memória (7 GB, já travou três vezes): um processo pesado por vez. `animar`, `editar`, `tratar`, `montar` e todo processo que importa o estilo (cena, teste de cena) esperam a vez sozinhos na fila da máquina (`humanim/fila.py`, um lock que o sistema solta quando o processo acaba) e avisam quem está na vez; então dá para encadear com `&&` ou disparar vários agentes de cena juntos. O Chrome não entra na fila: com ele aberto, confira 2,5 GB disponíveis no `free -m` (o `editar` quer 3 GB para o modelo melhor; com menos, usa o `small`). O `animar` escolhe quantas cenas renderiza por vez pela memória livre (de 1 a 3, cada uma passa de 700 MB) e diz quantas usou; `HUMANIM_PARALELO=1` força uma por vez. A prévia gera uma linha por vez. `/tmp` fica na memória: arquivo grande vai para o disco.
- Transcrição do `editar`: faster-whisper na CPU, modelo `large-v3-turbo` (uns 30 a 50 s e até 2,6 GB de memória para 90 s de fala nesta máquina), que transcreve gagueira e muleta que modelos menores engolem. Com menos de 3 GB livres ele usa o `small` (15 s, 1 GB) e avisa no relatório, a não ser que a gravação já tenha sido transcrita com o turbo (a transcrição fica em `.trabalho/` e é reaproveitada sem carregar modelo). A transcrição começa no primeiro som (com os 3 s mudos da contagem na frente o Whisper chegou a pular os primeiros 27 s) e trecho com voz e sem palavra é transcrito de novo. Se o modelo falhar, o `ERRO` diz o que fazer. `HUMANIM_WHISPER=<modelo>` escolhe. Os modelos ficam em `modelos/whisper/`.
- O `[CANTO]` fica encostado no canto inferior esquerdo (`formato.CANTO`), nunca solto no meio da tela: você toca a borda de baixo e a esquerda.
