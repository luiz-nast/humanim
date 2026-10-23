# Teoria: como o k-means acha os dois tipos de erupção do Old Faithful

Notas para o roteiro. As fontes estão em `pesquisa/fontes-teoria.md` ([T1] a [T8], com página). Os números do vídeo saem de `dados/resultados.json`, que manda. Os números daqui que não vêm das fontes são conferências minhas no `faithful`, marcadas "(conferi)".

Convenção (pauta): k-means de Lloyd, distância euclidiana nas medidas cruas em minutos (duração e espera). Soma dos quadrados: em todos os pontos, a distância ao quadrado até o centro do seu grupo, somada, em min² (a `inertia` do scikit-learn).

## Em uma frase

Sem ninguém dizer o que é erupção curta ou longa, o k-means põe k centros no gráfico e alterna duas regras até nada mudar: cada erupção vai para o centro mais perto, e cada centro vai para a média do seu grupo. Nenhuma das duas sobe a soma dos quadrados, e os jeitos de dividir são finitos, então ele sempre para; mas para num vale que depende do começo, e o k é você que escolhe.

## O mecanismo em 9 passos

1. **Dividir sem rótulo.** Cada erupção é um ponto: duração num eixo, espera no outro. O k-means busca k centros e uma divisão que deixem mínima a soma dos quadrados. O mínimo exato é difícil (quase kⁿ divisões possíveis; NP-difícil), então ele melhora a divisão aos poucos. [T3 p. 521-523; T5 §1-2; T6 Guia]

2. **Regra 1: cada ponto vai para o centro mais perto.** A fronteira entre dois centros é a reta que corta ao meio, em ângulo reto, o segmento entre eles. Não sobe a soma: a parcela de cada ponto é a distância ao quadrado até o seu centro, e trocar para um centro mais perto só a diminui. [T1 §V p. 131; T4 p. 510]

3. **Regra 2: cada centro vai para a média do seu grupo** (a duração média e a espera média). Daí o nome, k médias. Depois da primeira média, o centro em geral não é uma erupção de verdade. [T3 p. 523; T2 p. 283; T6 Guia]

4. **Por que a média.** Para um grupo de n pontos com média m e um centro c qualquer:
   soma(c) = soma(m) + n·|c − m|²
   Afastar o centro d minutos da média acrescenta exatamente n·d² (100 erupções, centro 1 min fora: +100 min²). O mínimo é d = 0: a média. É o Lema 2.1 do k-means++; Lloyd diz o mesmo em física: a soma é um "momento de inércia", mínimo no centro de massa. [T5 Lema 2.1, p. 2; T1 §IV p. 130; T4 eq. 14.32; T2 p. 282]
   - Para refazer: x − c = (x − m) + (m − c). Ao quadrado e somado, o termo cruzado é zero porque as sobras em volta da média somam zero (a média é o ponto de equilíbrio). No `faithful`, os dois lados dão o mesmo número (conferi).
   - Vale para os **quadrados**. Para a soma das distâncias simples, o melhor ponto é outro (em uma dimensão, a mediana).

5. **Alternar até nada mudar, e por que ele para.** A soma nunca sobe: nem na regra 1 (passo 2) nem na 2 (passo 4). Quando um ponto troca de grupo, ela cai de verdade, então nenhuma divisão se repete; e as divisões são finitas (272 erupções em 2 grupos: 2²⁷¹ − 1 jeitos, conta minha). Logo chega a rodada em que nada muda. [T5 §1 p. 1; T3 p. 523; T2 §3.6 p. 294; T1 §VI p. 131-132]
   - Detalhe: o empate na distância tem de ser resolvido sempre do mesmo jeito ("de forma consistente"). [T5 §2.1]
   - O scikit-learn para quando os centros se mexem menos que `tol`, com teto de 300 rodadas. [T6]

6. **Parar não é acertar: ótimo local.** "Nada muda" quer dizer que nenhuma regra melhora mais, não que a divisão é a melhor. Lloyd já via vários mínimos locais; MacQueen escreve que o resultado depende da divisão inicial; o *ISLP* roda o mesmo dado 6 vezes e obtém 3 resultados. O erro típico: o começo junta dois grupos de verdade debaixo de um centro só (e outro grupo fica com dois centros), e o k-means "nunca consegue separá-los" depois. [T1 p. 131; T2 p. 282, 294; T3 p. 523-525; T5 §6.3]
   - No `faithful` com k = 2, os grupos são tão separados que o começo ruim da pauta é consertado. Com dados menos separados, ficaria preso num vale pior.

7. **O remédio: vários começos.** Roda-se de vários começos e fica-se com o de **menor** soma, não com a média (`n_init`). O k-means++ espalha o começo: cada novo centro inicial é sorteado com chance proporcional à distância ao quadrado até o centro mais próximo já escolhido. Garante, em média, no máximo 8(ln k + 2) vezes a soma ótima; não garante o ótimo. No scikit-learn 1.9.1 o padrão é k-means++ com uma partida só (`n_init='auto'`); com `init='random'`, 10. [T5 §2.2, Teor. 1.1; T6 KMeans]

8. **O k é você que escolhe; o cotovelo é palpite.** A melhor soma nunca sobe quando k cresce (com um centro em cada erupção, é zero), então não dá para escolher k pela menor soma. O cotovelo procura o k depois do qual a queda fica pequena; o *Elements* chama de "dobra", diz que é "um tanto heurístico" e mostra um exemplo sem dobra clara. E o k-means devolve k grupos até em dado sem grupo nenhum: quem confirma o grupo é o mundo (aqui, a física do gêiser). [T4 p. 513, 518-519; T3 p. 524, 533]
   - No `faithful`, a dobra é clara em k = 2 (conferi; números no `dados/`).

9. **Mesma unidade não é mesmo peso.** As duas medidas estão em minutos, mas a espera se espalha muito mais (desvio de uns 13,6 min contra 1,1; ao quadrado, uns 140 vezes). No resultado final, mais de 99% da soma é diferença de espera, e a fronteira fica quase horizontal, numa espera de uns 67,5 min (conferi). Os grupos saem certos porque as duas medidas separam as erupções juntas. Padronizar mudaria os pesos; o *ISLP* põe essa escolha entre as de "grande impacto". [T3 p. 532-533; T8]

## O caminho que cabe em 60 a 90 s

**Núcleo, nesta ordem:**

1. **Gancho.** O Old Faithful tem erupção curta e longa, e a espera até a próxima anda junto. Os guardas preveem a próxima pela duração: menos de 3 min, 68 min; mais de 3, 94 min [T7]. É uma regra de dois grupos, e o k-means acha os dois grupos sem ninguém contar.
2. **As duas regras, na demonstração.** Começo ruim; cada erupção vai para o centro mais perto (a divisão sai errada); cada centro vai para a média; repete até nada mudar. A soma dos quadrados caindo na tela.
3. **Por que a média:** afastar o centro d minutos da média soma n·d².
4. **Por que para:** nenhuma regra sobe a soma, e os jeitos de dividir são finitos.
5. **O limite:** para num vale que depende do começo (por isso vários começos), e o k é você que escolhe.

**Sai primeiro:** a história (Lloyd, MacQueen); o k-means++ por dentro; a conta 2²⁷¹ − 1; o gráfico do cotovelo (fica a frase do k); o peso da espera na fala (mas a tela não pode contradizê-lo); os outros números do NPS.

## Armadilhas

### Simplificação aceitável

- "Centro" por centróide; "média do grupo" = duração média e espera média.
- "Para quando nada muda" (o scikit-learn usa uma tolerância).
- "Nunca sobe, e os jeitos são finitos, então para" (omite o empate consistente).
- "Para num vale que pode não ser o mais fundo" por ótimo local.
- "Roda de vários começos e fica com o melhor" por `n_init` e k-means++.
- Chamar os grupos de "curtas" e "longas": o nome é nosso; ele devolve grupo 1 e grupo 2.

### ERRADO, não diga

- "Acha a melhor divisão." Acha um ótimo local. [T1, T2, T3, T5]
- "A soma cai a cada rodada." Na última fica igual, e é assim que se sabe que acabou. Diga "nunca sobe".
- "A média minimiza a soma das distâncias." Das distâncias **ao quadrado**.
- "O centro é uma das erupções." Só no começo da demonstração. [T6]
- "Descobre quantos grupos existem" ou "o cotovelo prova que são 2." [T3 p. 533; T4 p. 519]
- "Roda várias vezes e tira a média." Fica com a menor soma. [T6]
- "O k-means++ garante o ótimo." [T5]
- "Os guardas usam k-means" ou "o k-means achou o corte dos 3 minutos." A regra do NPS corta a duração; o k-means em minutos crus corta quase só a espera, e discorda da regra dos 3 min em 5 das 272 erupções (conferi).
- "Estão as duas em minutos, então pesam igual." (passo 9)
- "68 e 94 min" como se fossem os grupos do `faithful`. São do NPS de hoje; o intervalo do gêiser cresceu com o tempo, diz o NPS [T7], e o `faithful` é antigo. Não ponha os dois na mesma régua sem avisar.
- "Erupção de hora em hora." O NPS diz que isso nunca aconteceu. [T7]
- Soma dos quadrados "em minutos": é min².
- "MacQueen inventou estas duas regras." (Ressalvas)

**Para as cenas (o desenho não engana):** com escalas diferentes nos eixos (uns 4 min de duração contra uns 55 de espera), "perto na tela" não é "perto em minutos": a fronteira de verdade não sai em ângulo reto com o segmento entre os centros, sai quase horizontal, e uma erupção de 3,4 min com 66 min de espera (conferi) parece do grupo longo e vai para o curto. Desenhe a fronteira calculada com os números do `dados/`, ou nenhuma; nunca uma mediatriz feita no olho.

## Ressalvas de fonte

- **NPS: três páginas, números que não batem por inteiro** [T7]. "Current Geyser Activity" (tabela de novembro de 2020): intervalo "94 ou 68 min (± 10 minutos)", duração de 1,5 a 5 min, altura de 106 a 184 pés. Atividade escolar "Predict Old Faithful" (2018): a "fórmula dos guardas", menos de 3 min dá 68 min, mais de 3 dá 94, duração medida a meio minuto. Centro de Visitantes Virtual (sem data): 1,5 a 5 min, 90 a 184 pés, intervalo de 35 a 120 min com média de 92, "cerca de 90%" das previsões certas em ± 10 min; erupção curta gasta menos água e calor, que se repõem mais rápido; só se prevê uma erupção à frente; o intervalo cresceu com o tempo (terremoto de 1959 e outros). Nenhuma diz de onde saem 68 e 94 nem desde quando valem.
- **O `faithful` não tem data nem protocolo.** O R dá como fonte só "W. Härdle", diz que há "muitas versões" e que as durações estão muito arredondadas [T8]. Na versão de Azzalini e Bowman do pacote MASS (`geyser`, agosto de 1985), a espera foi corrigida para "antes desta erupção". No `faithful`, a duração anda com a espera da mesma linha (correlação 0,90), não com a da linha seguinte (−0,48): bate com "espera até a próxima" (conferi). Não li o artigo de 1990 (bloqueado): ano e protocolo ficam sem confirmação.
- **Livro-texto: *ISLP* (2023), não *ISLR* 2ª ed.** A pauta põe Taylor no *ISLR*; ele é coautor do *ISLP*. A seção 12.4.1 é a mesma; as páginas são do *ISLP*. O objetivo do *ISLP* (eq. 12.17) é o **dobro** da nossa soma, e o *Elements* (eq. 14.31) põe um peso Nₖ por grupo: nos números, só a soma da pauta. [T3; T4; T6]
- **Quem inventou.** Lloyd escreveu em 1957 (rascunho da Bell Labs registrado em 31/07/1957), para uma dimensão (sinal de PCM), e publicou "quase literalmente" em 1982. MacQueen deu o nome em 1967, mas o k-means dele é sequencial (cada ponto novo ajusta só a sua média); a versão em lote ele atribui a Forgy e Jennrich (comunicada em 1963). "Algoritmo de Lloyd" é como o scikit-learn chama. [T1 p. 129, 136; T2 p. 281-283, 294; T6]
- **k-means++:** li a versão técnica de 2006; a paginação do SODA 2007 é outra. [T5]
- **scikit-learn 1.9.1**, lido em 23/10/2026; o padrão de `n_init` mudou na 1.4. "Sempre para" não é "para rápido": o pior caso é enorme (Arthur e Vassilvitskii 2006, citado pelo scikit-learn, não lido). [T6]
- **Grupo vazio:** se um centro fica sem ponto, a regra 2 não tem média. Lloyd trata à parte; o `dados/calcular.py` deve conferir. [T1 p. 130-132]
- **Cotovelo:** o nome costuma ser atribuído a Thorndike (1953); não conferi. [T4 p. 519]
