export const meta = {
  name: 'humanim-pesquisa-roteiro',
  description: 'humanim: pesquisa (teoria e dados em paralelo) e o roteiro v1, a partir da pauta.md do vídeo',
  whenToUse: 'Skill diretor, passos 2 e 3: depois que o diretor escreveu videos/<slug>/pauta.md. args: { pasta: "videos/<slug>" }',
  phases: [
    { title: 'Pesquisa', detail: 'teoria e dados, em paralelo' },
    { title: 'Roteiro', detail: 'roteirista com a skill roteiro' },
  ],
}

const PASTA = args.pasta
const BASE = `Projeto humanim (shorts verticais de 60 a 90 s no LinkedIn que quebram uma teoria pesada de IA com dados reais; quem apresenta fala, cenas Manim por cima). Rode tudo da raiz do repositório. Comando: .venv/bin/humanim. Pasta do vídeo: ${PASTA}/. A PAUTA está em ${PASTA}/pauta.md: leia antes de tudo; ela fixa o conceito, o gancho, o dataset, a convenção (modelo, fórmula, unidades, nomes na fala e na tela), a demonstração e a lista de números que o vídeo precisa. Não mexa em outros vídeos nem no código. Nada de arquivo grande em /tmp (é memória). Nunca abra navegador. Arquivo com mais de ~150 linhas sai em partes (esqueleto num Write, depois Edits); se estiver recomeçando, continue do que está no disco.`

phase('Pesquisa')
const [teoria, dados] = await parallel([
  () => agent(`${BASE}

SEU PAPEL: pesquisador de teoria (skill diretor, item 2). Escreva ${PASTA}/teoria.md com estas seções, nesta ordem: "## Em uma frase"; "## O mecanismo em N passos" (6 a 10, cada um com as fontes [n]); "## O caminho que cabe em 60 a 90 s" (o núcleo que o vídeo não pode perder e o que sai primeiro quando falta tempo); "## Armadilhas" ("simplificação aceitável" e "ERRADO, não diga"); "## Ressalvas de fonte".
MOLDE: 1.200 a 1.800 palavras e 4 a 8 obras lidas de verdade (as primárias abertas, um livro-texto e a documentação oficial; as candidatas estão na pauta). Pare quando o molde estiver cheio. O WebFetch não lê PDF: curl + pdftotext; material bruto em ${PASTA}/pesquisa/.
Fontes só em ${PASTA}/pesquisa/fontes-teoria.md: obras lidas numeradas [T1]... com URL e o que foi lido; cada afirmação do teoria.md com obra e página ou seção; "lidas" separadas de "citadas sem ler".
Escreva só teoria.md, pesquisa/fontes-teoria.md e o material em pesquisa/.
DEVOLVA (curto, por itens): as 3 a 5 ideias centrais para o roteiro, as armadilhas mais perigosas e as dúvidas de fonte.`, { label: 'pesquisa:teoria', phase: 'Pesquisa' }),
  () => agent(`${BASE}

SEU PAPEL: pesquisador de dados (skill diretor, item 2). Exemplo do nível esperado: .claude/skills/diretor/exemplos/calcular-knn.py e .claude/skills/diretor/exemplos/para_tela-knn.json.
1. Baixe o dataset da pauta de uma fonte estável; registre URL, data, tamanho e SHA-256 e descubra a licença. Sem licença aberta explícita: o arquivo fica em ${PASTA}/pesquisa/ (fora do GitHub) e o calcular.py lê de lá, com o comando de download no topo; com licença aberta, vai em ${PASTA}/dados/ com o texto da licença.
2. ${PASTA}/dados/calcular.py calcula cada número da lista da pauta e grava ${PASTA}/dados/resultados.json, com o bloco "para_tela" (cada número como a tela escreve, vírgula decimal e ponto de milhar; cada conta fechando com os números mostrados, encadeada; a intuição de cada número em palavras) e "cuidados". Se a cena vai desenhar pontos, grave também os pontos com o grupo ou a classe de cada etapa.
MOLDE: os números da lista da pauta, conferidos com uma biblioteca de referência quando houver. Conferência extra só se ela pode mudar o que o vídeo diz; anote nos cuidados o que ficou aberto, sem investigar a fundo.
Fontes só em ${PASTA}/pesquisa/fontes-dados.md: o dataset (estudo original, versão, URL, SHA-256, licença), a conta e os cuidados.
Escreva só dados/, pesquisa/ e pesquisa/fontes-dados.md.
DEVOLVA (curto, por itens): licença e onde ficou o arquivo; os números da lista com o valor; os 8 a 12 números mais fortes do para_tela; os cuidados.`, { label: 'pesquisa:dados', phase: 'Pesquisa' }),
])

phase('Roteiro')
const roteiro = await agent(`${BASE}

SEU PAPEL: roteirista. Leia a skill .claude/skills/roteiro/ inteira (SKILL.md, voz.md, temas.md), ${PASTA}/teoria.md e ${PASTA}/dados/resultados.json (o bloco para_tela e os cuidados; não leia a lista de pontos). Como referência do nível, leia .claude/skills/roteiro/exemplos/knn.md e kmeans.md (copie a profundidade e o nexo, não a forma).

Resumo dos pesquisadores:
TEORIA: ${teoria}
DADOS: ${dados}

Escreva ${PASTA}/roteiro.md seguindo a skill roteiro: 60 a 90 s medidos com ".venv/bin/humanim contar ${PASTA}/roteiro.md" (rode até dar 60 a 90 s e nenhum aviso), 15 a 18 linhas, gancho na linha 1, a teoria quebrada até a conta, todo número do para_tela, a descrição de cada [ANIM]/[CANTO] concreta (o que aparece, onde, e o gatilho em "palavra"), o checklist de entrega da skill cumprido (as fontes estão em ${PASTA}/pesquisa/fontes-teoria.md e pesquisa/fontes-dados.md; o fontes.md o diretor junta depois, não o escreva). Diga, logo depois do gancho, o que o algoritmo quer (o objetivo) e, quando houver, a regra de parada. Escreva só roteiro.md.
DEVOLVA: o roteiro inteiro, a duração do contar e as escolhas (curto).`, { label: 'roteiro:v1', phase: 'Roteiro' })

return { teoria, dados, roteiro }
