export const meta = {
  name: 'humanim-designer',
  description: 'humanim: o designer escreve o cenas/comum.py (vocabulário visual do vídeo) e renderiza uma linha de teste',
  whenToUse: 'Skill diretor, passo 4: junto com o humanim-criticos, logo que o roteiro v1 sai. args: { pasta: "videos/<slug>" }',
  phases: [{ title: 'Designer', detail: 'comum.py com o contrato no topo e uma linha de teste' }],
}

const PASTA = args.pasta
phase('Designer')
const designer = await agent(`Projeto humanim: shorts verticais (1080x1920) de 60 a 90 s, cenas Manim por cima de quem apresenta. Rode da raiz do repositório. Pasta do vídeo: ${PASTA}/.

SEU PAPEL: designer das cenas. Leia a skill .claude/skills/cenas/SKILL.md inteira, estilo/estilo.py, ${PASTA}/pauta.md, ${PASTA}/roteiro.md (versão 1: as falas ainda podem mudar depois dos críticos; o vocabulário visual fica) e o bloco para_tela de ${PASTA}/dados/resultados.json (leia o JSON com python, só as chaves que precisa). Exemplos de bons comum.py, com o contrato no topo: .claude/skills/cenas/exemplos/comum-knn.py e comum-kmeans.py (eles importam dados do vídeo deles: leia como exemplo, não rode).

Escreva ${PASTA}/cenas/comum.py com tudo que mais de uma linha usa, com posição, tamanho e cor fixos: os eixos e os pontos reais, os marcadores, os rótulos, os contadores e os gráficos que o roteiro repete. E uma função de estado para cada emenda entre duas linhas [ANIM]/[CANTO] seguidas: a tela inteira nesse ponto (o que fica, com rótulos), para dois animadores diferentes emendarem por ela. Dê às funções o nome da etapa (ex.: estado_rodada(1), tela_soma()), nunca o número da linha: o roteiro ainda pode ganhar ou perder linhas. Legível num celular (letra de ~55 px ou mais). Nas linhas [CANTO], nada abaixo da zona livre acima do canto. Use as peças do estilo (conta, br, lupa, rotulo). No topo, em comentário curto, o contrato de cada função (o que desenha e onde), para os animadores. Arquivo grande sai em partes: o esqueleto num Write, depois uma parte por Edit; se estiver recomeçando, continue do que está no disco.

Teste, com MOLDE: escreva a cena de UMA linha [ANIM] do roteiro (a que mais usa o comum.py), renderize só ela (.venv/bin/humanim animar ${PASTA}/roteiro.md --linha N, com timeout 600000: ele espera a vez na fila da máquina sozinho, e a espera conta no tempo do Bash), olhe os prints de .venv/bin/humanim frames ${PASTA}/cenas/linha_NN.mp4 uma vez e corrija o que estiver ilegível, cortado ou fora da zona. Não renderize outras peças nem faça uma segunda rodada de polimento: os animadores e o fechamento conferem o resto. Nunca abra navegador.

DEVOLVA: o contrato resumido (função → o que desenha, onde), as funções de estado de cada emenda (entre que falas), a linha de teste com o número e a fala dela, e o que você mudou em relação ao que o roteiro descreve (e por quê).`, { label: 'designer', phase: 'Designer' })
return { designer }
