export const meta = {
  name: 'humanim-cenas',
  description: 'humanim: um animador por bloco de cenas (até 4 ao mesmo tempo; o render espera a fila da máquina) e o fechamento com a prévia',
  whenToUse: 'Skill diretor, passo 4: depois da revisão do roteiro e do humanim-designer. args: { pasta: "videos/<slug>", blocos: [{ id: "1", linhas: [1, 2], nota: "o que é só deste bloco" }], emendas: "1→2, 4→5", vagas: 4 }',
  phases: [
    { title: 'Blocos', detail: 'um animador por bloco; os mais pesados primeiro' },
    { title: 'Fechamento', detail: 'animar completo, emendas, zona e prévia' },
  ],
}

const PASTA = args.pasta
const BLOCOS = args.blocos
const VAGAS = args.vagas || 4
const ANIMAR = `.venv/bin/humanim animar ${PASTA}/roteiro.md`
const BASE = `Projeto humanim: shorts verticais (1080x1920) de 60 a 90 s no LinkedIn; quem apresenta fala e as cenas Manim entram por cima. Rode tudo da raiz do repositório. Pasta do vídeo: ${PASTA}/.

Leia antes: a skill .claude/skills/cenas/SKILL.md inteira; ${PASTA}/roteiro.md (FINAL: falas e descrições valem como estão); o contrato no topo de ${PASTA}/cenas/comum.py; e, de ${PASTA}/dados/resultados.json, só o que a sua cena usa (leia com python e json, pelas chaves; o arquivo pode ter milhares de pontos). Todo número da tela sai do para_tela ou dos dados; nenhum inventado.

MEMÓRIA: render e teste de cena (tudo que importa o estilo ou o comum.py) esperam a vez na fila da máquina sozinhos; não rode nada com o Manim fora disso (nada de "import manim" direto). A espera conta no tempo do Bash: rode o animar e todo teste de cena com timeout 600000. Nada de arquivo grande em /tmp.

Regras:
- Escreva SÓ as cenas do seu bloco e, se precisar, cenas/bloco_<id>.py. NÃO edite o comum.py, o roteiro nem cenas de outros blocos: faltou algo no comum.py, implemente no seu bloco_<id>.py; erro no comum.py, descreva no retorno.
- Skill cenas: self.ate("palavra") nos gatilhos da descrição, self.completar() no fim, canto livre nas [CANTO], legível num celular, o desenho não engana (escalas, distâncias e fronteiras calculadas, nunca no olho).
- Continuidade: a linha que continua a anterior começa com self.add do estado em que a anterior termina, sem animação. Dentro do bloco, use as suas funções; entre blocos, só as funções de estado do comum.py que a nota do bloco cita (nunca importe o bloco_<id>.py de outro animador: ele pode estar mudando agora). A sua última linha termina exatamente nesse estado do comum.py.
- Arquivo com mais de ~150 linhas sai em partes (esqueleto num Write, depois Edits); se estiver recomeçando, continue do que está no disco.
- MOLDE: escreva, renderize (${ANIMAR} --linha N, pode repetir --linha), olhe os prints de .venv/bin/humanim frames ${PASTA}/cenas/linha_NN.mp4 UMA vez, corrija o que está errado (cortado, ilegível, fora da zona, número ou gatilho errado) e renderize de novo. O que está só fraco, anote no retorno; não faça segunda rodada de polimento.
- Nunca abra navegador nem rode previa sem --nao-abrir, gravar, tratar ou montar.

DEVOLVA (curto): os arquivos, o que conferiu, a função do estado final, o que ficou fraco e o que precisou do comum.py.`

phase('Blocos')
const relatos = new Array(BLOCOS.length).fill(null)
let proximo = 0
await parallel(Array.from({ length: Math.min(VAGAS, BLOCOS.length) }, () => async () => {
  while (proximo < BLOCOS.length) {
    const k = proximo++
    const b = BLOCOS[k]
    const arquivos = b.linhas.map(n => `${PASTA}/cenas/linha_${String(n).padStart(2, '0')}.py`).join(', ')
    const r = await agent(`${BASE}

SEU BLOCO: B${b.id}, linha(s) ${b.linhas.join(' e ')} do roteiro. ${b.nota || ''}
Arquivos que você pode escrever: ${arquivos} e ${PASTA}/cenas/bloco_${b.id}.py.`, { label: `animador:B${b.id}`, phase: 'Blocos' })
    relatos[k] = r ? `B${b.id} (linhas ${b.linhas.join(', ')}): ${r}` : `B${b.id}: sem retorno (o agente caiu)`
    log(`B${b.id} pronto`)
  }
}))

phase('Fechamento')
const fechamento = await agent(`${BASE}

SEU PAPEL: fechamento das cenas (agora você pode mexer no comum.py e em qualquer cena). O que os animadores relataram:
${relatos.join('\n\n')}

MOLDE: conserte o que está errado; o que está só fraco, liste no retorno.
1. Erro apontado no comum.py: conserte. Bloco sem retorno: confira as cenas dele e escreva o que faltar. Rode o animar completo (${ANIMAR}, sem --linha). ERRO numa linha: conserte e rode de novo.
2. Emendas (${args.emendas || 'os pares de linhas seguidas que continuam a mesma cena'}): o último quadro da primeira contra o primeiro da seguinte (ffmpeg -sseof -0.05 e -frames:v 1); conserte o pulo que aparecer.
3. O quadro do meio e o último de cada linha animada: o desenho não engana, nada ilegível, cortado ou no canto das [CANTO]. Conserte e renderize de novo só o que mudou.
4. .venv/bin/humanim previa ${PASTA} --nao-abrir e uma folha com o último quadro de cada linha da prévia (.trabalho/previa.mp4; o segundo do fim de cada linha está no previa.html) em videos/.testes/${PASTA.split('/').pop()}-folha.png, em 2 fileiras.

DEVOLVA: OK ou o que falta, a duração da prévia, o que consertou e o que ficou fraco.`, { label: 'previa:fechar', phase: 'Fechamento' })

return { relatos, fechamento }
