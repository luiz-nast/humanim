export const meta = {
  name: 'humanim-criticos',
  description: 'humanim: os 3 críticos adversariais do roteiro v1, em paralelo (só leem, devolvem as correções prontas)',
  whenToUse: 'Skill diretor, passo 3: junto com o humanim-designer, logo que o roteiro v1 sai. args: { pasta: "videos/<slug>" }',
  phases: [{ title: 'Críticos', detail: 'profundidade, precisão e público, em paralelo' }],
}

const PASTA = args.pasta
const LEITURA = `Projeto humanim (shorts de 60 a 90 s que quebram uma teoria pesada de IA com dados reais). Rode da raiz do repositório. Leia: ${PASTA}/pauta.md, .claude/skills/roteiro/SKILL.md e voz.md, ${PASTA}/roteiro.md, ${PASTA}/teoria.md, ${PASTA}/pesquisa/fontes-teoria.md, ${PASTA}/pesquisa/fontes-dados.md e o bloco para_tela e os cuidados de ${PASTA}/dados/resultados.json. Rode .venv/bin/humanim contar ${PASTA}/roteiro.md se precisar de tempos. Você NÃO escreve nenhum arquivo. Você é adversarial: ache problema com evidência (linha, número, fonte), não aprove. Devolva no máximo 8 problemas, do mais grave ao menos, cada um com: linha, o problema, a evidência e a correção concreta (o texto novo da fala ou da descrição, pronto para colar). Diga quanto cada correção muda a duração. Linha boa, não comente.`
const CRITICOS = [
  { id: 'profundidade', foco: 'PROFUNDIDADE E NEXO: a teoria está quebrada até o mecanismo (quem assiste sai sabendo refazer a conta e entende o porquê de cada passo)? O roteiro diz o que o algoritmo quer e quando ele para? Cada linha puxa a seguinte, nenhuma sobra? Falta um passo que deixa a conta mágica? Um conceito só?' },
  { id: 'precisao', foco: 'PRECISÃO: cada número bate com o para_tela (rode o dados/calcular.py se precisar)? Cada afirmação tem fonte e diz o que a fonte diz? Alguma armadilha do teoria.md foi pisada? A descrição das cenas desenha algo que engana (escala, eixo, distância, ponto que não existe)?' },
  { id: 'publico', foco: 'PÚBLICO, GANCHO E VOZ: o gancho segura nos 2 primeiros segundos de quem rola o feed? Leigo entende cada termo quando ele aparece? A fala soa como o voz.md (gente falando, não texto lido)? O fechamento volta ao gancho? Tem frase longa demais para falar de uma vez (mais de 20 palavras)?' },
]
phase('Críticos')
const criticas = await parallel(CRITICOS.map(c => () =>
  agent(`SEU PAPEL: crítico de roteiro. ${c.foco}\n\n${LEITURA}`, { label: `critica:${c.id}`, phase: 'Críticos' })
    .then(r => ({ critico: c.id, r }))))
return { criticas }
