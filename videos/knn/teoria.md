# Teoria: como o KNN classifica, e por que a régua muda os vizinhos

Notas para quem escreve o roteiro. As fontes de cada afirmação estão em `fontes.md`, seção Teoria: os números entre colchetes, como [9], são os itens de lá. Os números dos pinguins saem de `dados/resultados.json`, que é de onde o roteiro tira tudo. Quando cito um número de lá, digo o bloco, e quem manda é o JSON.

Convenção do vídeo (pauta): KNN de classificação, distância euclidiana d = √(Δbico² + Δmassa²), k = 5, voto da maioria e, se empatar, decide a espécie do vizinho mais próximo entre as empatadas. Padronizar é z = (x − média) ÷ desvio-padrão, com ddof=0. A nota é por deixar-um-de-fora, acertos ÷ 342.

## Em uma frase

Para classificar um pinguim novo, o KNN mede a distância dele até cada pinguim já conhecido, pega os 5 mais perto e dá a espécie que mais aparece entre eles. Essa distância soma diferenças de medidas em unidades diferentes (milímetros de bico, gramas de massa), então, sem padronizar, quem escolhe os vizinhos é a medida que varia mais na sua própria unidade (a massa), e o bico praticamente não conta.

## O mecanismo em 9 passos

1. **Não tem treino que ajuste números: o KNN guarda os exemplos.** O "treino" é guardar os 342 pinguins, cada um com as suas medidas e a sua espécie. O KNN não monta fórmula nem aprende pesos. Toda a conta acontece na hora de classificar. [1, 21]
   Cada pinguim vira um ponto num plano: o bico (mm) num eixo, a massa (g) no outro.

2. **Medir a distância até cada um.** Para o pinguim novo, calcule a distância até cada um dos conhecidos:
   d = √(Δbico² + Δmassa²), em que Δ é a diferença entre os dois pinguins naquela medida.
   É o Pitágoras no plano (a régua esticada entre os dois pontos), a distância euclidiana. É o padrão do scikit-learn (`metric='minkowski'` com `p=2`). [3, 4]
   - **A distância é uma escolha, desde o começo.** Fix e Hodges (1951) escrevem "especifique uma métrica, por exemplo a distância euclidiana comum". Cover e Hart (1967) definem a regra para qualquer métrica. [5]

3. **Ordenar e ficar com os k mais perto.** Com k = 5, valem só os 5 pinguins de menor distância. Os outros não votam. k = 5 é o padrão do scikit-learn (`n_neighbors=5`), não uma lei. [2, 3]

4. **Os 5 votam, e ganha a maioria.** A previsão é a espécie com mais representantes entre os 5. A fração de cada espécie entre os 5 (3 de 5 = 60%) é a "probabilidade" que o KNN devolve. [2]
   - **Empate.** Com 3 espécies e 5 votos, dá para empatar 2 a 2 (com 1 na terceira). Cada fonte desempata de um jeito: Cover e Hart sugerem a espécie mais popular entre os empatados, o *Elements* sorteia, as notas de Cornell refazem a conta com k menor. O scikit-learn, sem avisar no texto, fica com a espécie que vem primeiro em ordem alfabética: Adelie, depois Chinstrap, depois Gentoo. Testei: com 2 Gentoo mais perto e 2 Adélias mais longe, ele responde Adélia. A pauta usa "decide o vizinho mais próximo entre as empatadas". Se um empate aparecer na tela, a fala diz a regra. [9]
   - Empatar na distância é outra coisa: o 5º e o 6º pinguins ficam à mesma distância. No scikit-learn, quem entra depende da ordem das linhas do arquivo. [10] Com as massas em múltiplos de 25 g, isso acontece aqui (`avaliacao.2_medidas.*.empates_de_distancia_na_5a_vaga` em `resultados.json`).

5. **O k é um equilíbrio.** Com k = 1, tudo depende de um único vizinho: um pinguim fora do padrão já vira o voto, e a previsão muda à toa. Com k grande, a resposta fica estável, mas a fronteira entre as espécies borra. Com k igual a todos os outros (341, no deixar-um-de-fora), todo pinguim sairia "Adélia", a espécie mais comum (151 de 342). Não existe um k melhor para todo problema: depende dos dados. [11, 12]
   Fix e Hodges já pediam um k "grande, mas pequeno perto do tamanho das amostras". Cover e Hart explicam por quê: k grande para o voto não ser sorte, k pequeno para os vizinhos estarem perto de verdade. [6, 11]

6. **Onde a régua entra: a soma mistura milímetros e gramas.** Na fórmula, 1 mm de bico pesa o mesmo que 1 g de massa. Entre dois pinguins, a massa costuma diferir em centenas de gramas e o bico em poucos milímetros. Ao quadrado, a diferença aumenta ainda mais: 100 g viram 10 000 na soma, e 0,4 mm viram 0,16 (conta do pinguim misterioso, `para_tela.misterioso.conta_ate_a_barbicha`). [16, 17]
   - O que manda não é ter "número grande", e sim o **espalhamento das diferenças** na unidade da medida. Somar 1 000 g a todos os pinguins não muda nenhuma distância. Trocar gramas por quilos muda: aí a massa varia décimos e o bico passa a mandar. O *ISLP* dá o mesmo exemplo: com o salário em ienes, ou a idade em minutos, as classificações mudam "bastante". **Sem padronizar, a resposta do KNN depende de qual unidade alguém escolheu.** [16]
   - Nos pinguins, sem padronizar, os 5 vizinhos são exatamente os 5 de massa mais parecida, em todos os 342. O bico só desempata entre pinguins de mesma massa (as massas estão em passos de 25 g) (`peso_da_massa` em `resultados.json`). Na conta crua, um desvio de massa entra como 801 e um desvio de bico como 5,45: o bico é medido com uma régua 147 vezes menor (`para_tela.padronizar.conta_razao`: 801 ÷ 5,45 = 147).

7. **Padronizar: medir cada coisa em desvios.** z = (x − média) ÷ desvio-padrão diz "quantos desvios acima ou abaixo da média". O bico passa a ser medido na régua de 5,45 mm e a massa na de 801 g, e as duas ficam sem unidade, as duas em "desvios". Só aí a soma faz sentido. [16, 18]
   - **Para a distância, o que conta é a divisão.** A média some na diferença: Δz = Δx ÷ desvio. Para achar os vizinhos, basta dividir cada Δ pelo desvio da sua medida. Isso deixa a conta da tela mais curta (`para_tela.misterioso.conta_ate_a_barbicha`: 0,4 ÷ 5,45 = 0,07; 100 ÷ 801 = 0,12). [25]
   - Isso equivale a dar a cada medida um peso, 1 ÷ desvio², escolhido por nós e não aprendido. Padronizar iguala o peso das duas. [16, 25]
   - ddof=0 ou ddof=1 não muda nenhum vizinho: o desvio das duas medidas muda pelo mesmo fator, todas as distâncias encolhem juntas e a ordem fica igual. A documentação do scikit-learn diz que a escolha "provavelmente" não afeta o desempenho; no KNN, com as duas medidas contadas nos mesmos 342 pinguins, o efeito é zero. Mudam só os números da tela, a partir da 3ª casa. [18, 25]

8. **Avaliar sem sorteio: deixar-um-de-fora.** Esconda um pinguim. Entre os outros 341, ache os 5 mais perto, deixe-os votar e compare com a espécie real. Repita para os 342. A acurácia é acertos ÷ 342. Não há sorteio: rodando de novo, o resultado é o mesmo. [22]
   - O escondido não pode votar em si mesmo: estaria à distância 0 dele mesmo e acertaria de graça. No scikit-learn, `predict(None)` já tira o próprio ponto. [23]
   - O certo é calcular a média e o desvio da padronização sem o pinguim escondido, porque ele faz o papel de "pinguim novo" (vazamento de dados). Nos pinguins isso não muda nenhuma previsão (`padronizar_por_rodada_vs_de_uma_vez`: 0 diferenças), mas o `calcular.py` faz do jeito certo. [24]
   - Resultado (`para_tela.acuracia_2_medidas`): sem padronizar, 271 ÷ 342 = 79,2%; padronizado, 318 ÷ 342 = 93,0%.

9. **O teorema por trás: com dados infinitos, o vizinho mais próximo erra no máximo o dobro do mínimo.** Cover e Hart (1967) provaram que, quando o número de exemplos vai ao infinito, o erro do 1-NN (k = 1) fica entre o erro de Bayes (o mínimo possível, de quem conhecesse as probabilidades verdadeiras) e o dobro dele. Na forma exata: R* ≤ R ≤ 2R*(1 − R*) com 2 classes. A frase deles: metade da informação de classificação de uma amostra infinita está no vizinho mais próximo. Com k maior, o limite cai na direção do mínimo. [13, 14]
   - **E o detalhe que liga ao vídeo:** nesse limite, o resultado **não depende da métrica**, porque com infinitos pinguins o vizinho mais próximo encosta no pinguim novo em qualquer régua. A régua importa porque os dados são finitos: com 342 pinguins, o vizinho fica longe, e "longe em quê?" decide quem ele é. [15]
   - História: a primeira regra do tipo "vizinho mais próximo" aparece num relatório técnico de Fix e Hodges para a Escola de Medicina de Aviação da Força Aérea dos EUA, em 1951, só publicado em revista em 1989. Eles provaram que a regra funciona com amostras grandes (é "consistente") se k crescer, mas devagar perto do tamanho da amostra. A regra deles tem duas populações e compara frações (M ÷ m com c × N ÷ n); quando as duas amostras têm o mesmo tamanho, é o voto da maioria. [6, 7]

## O caminho que cabe em 60 a 90 s

**O núcleo, que não pode sair:**
1. O pinguim misterioso (real: uma Barbicha, 50,9 mm e 3 550 g). O KNN mede a distância até os outros, pega os 5 mais perto e eles votam.
2. A fórmula na tela, d = √(Δbico² + Δmassa²), e a percepção de que ela soma milímetros com gramas.
3. Sem padronizar: os 5 vizinhos são Adélias com exatamente 3 550 g, e o bico, 8,7 a 11,3 mm mais curto, nem pesou. Errou.
4. A conta de um par, termo a termo, nos dois jeitos: até a Barbicha, 100 g viram 10 000 na soma e 0,4 mm viram 0,16. Em desvios, os 100 g viram 0,12 e os 0,4 mm viram 0,07, e a soma dos quadrados é 0,0144 + 0,0049.
5. Padronizar é medir cada coisa na sua régua ("quantos desvios"): os 5 vizinhos viram Barbichas. Acertou.
6. Em todos os 342, escondendo um de cada vez: 79,2% → 93,0%.

**O que sai primeiro quando falta tempo, nesta ordem:**
1. Cover e Hart e o "no máximo o dobro" (bonito, mas é outro vídeo).
2. Fix e Hodges e 1951 (no máximo meia frase: "a ideia é de 1951").
3. A discussão do k (basta "os 5 mais perto").
4. Empates (só se aparecer um na tela; o misterioso não tem: 5 × 0 nos dois jeitos).
5. As 4 medidas (98,5% padronizado; `avaliacao.4_medidas`): só como número de apoio.
6. A frase "trocar gramas por quilos inverteria quem manda" (forte, mas o `calcular.py` não calcula esse caso; só entra se o agente de dados calcular).

O detalhe de deixar-um-de-fora pode virar meia frase: "escondo um pinguim de cada vez e vejo se os vizinhos acertam".

## Armadilhas

### Simplificação aceitável

- **"A distância soma as diferenças"**, desde que a tela mostre a fórmula com os quadrados e a raiz.
- **"Quantos desvios da média"** para z, e **"a régua de cada medida"** para o desvio-padrão: é a definição, não uma aproximação.
- **"Sem padronizar, a massa manda sozinha"**: vale aqui, porque os 5 vizinhos crus são os 5 de massa mais parecida em todos os 342 (`peso_da_massa`). A versão exata é "o bico só desempata entre pinguins de mesmo peso".
- **"O KNN não aprende nada, só guarda os exemplos e faz a conta na hora"**: o scikit-learn chama isso de aprendizado "baseado em instâncias" ou "não generalizante", e o *Elements*, de "baseado em memória, sem modelo para ajustar". [1]
- **"Os 5 mais perto votam"** para o voto de maioria com k = 5.
- **"Esconder um pinguim e ver se os vizinhos acertam"** para deixar-um-de-fora.
- **"93% de acerto"** para 318 ÷ 342, desde que fique claro que é nestes pinguins, um escondido de cada vez.
- **"Barbicha"** para *chinstrap* (pinguim-de-barbicha), como na pauta.

### ERRADO, não diga

1. **"O KNN aprende pesos" ou "descobre qual medida é mais importante".** Ele não ajusta nada. O peso de cada medida na distância vem da unidade escolhida ou da padronização, quer dizer, de nós. O *ISLP* diz com todas as letras que o KNN não diz quais variáveis importam. [1, 21]
2. **"Padronizar muda os dados" ou "distorce os pinguins".** Padronizar é trocar a unidade, e dá para desfazer. Dentro de cada medida, a ordem dos pinguins não muda (o maior bico continua o maior). O que muda é quanto cada medida pesa na distância, e por isso os vizinhos mudam. [18, 25]
3. **"Padronizar é normalizar" ou "deixa os dados com cara de sino".** No scikit-learn, "normalizar" (`Normalizer`) é outra coisa: deixa cada linha com comprimento 1. E a padronização não muda a forma da distribuição, só a média (0) e o desvio (1). Diga "padronizar". [20]
4. **"A medida de números maiores manda."** O que manda é o tamanho das diferenças na unidade da medida, não o tamanho dos valores. Somar uma constante a todos não muda nada. Pode dizer: "a diferença em gramas dá um número muito maior que a diferença em milímetros". [16, 25]
5. **"Tirar a média é o que resolve."** Na distância, a média se cancela. Quem muda os vizinhos é a divisão pelo desvio. [25]
6. **"A distância é a soma das diferenças"** (sem quadrado nem raiz) ou **"a distância crua é em milímetros"** (ou em gramas). É a raiz da soma dos quadrados, e a crua mistura mm com g: não tem unidade. A padronizada está em desvios. [4]
7. **"Os outros 341 votam."** Os 341 são medidos; só os 5 mais perto votam. A frase da pauta ("os outros 341 votam") e a de `para_tela.acuracia_2_medidas.como` precisam virar algo como "os outros 341 ficam na turma, e os 5 mais perto votam". [2]
8. **"Padronizar sempre melhora o KNN."** Padronizar iguala o peso das medidas, e isso é uma escolha. Se a medida mais espalhada fosse justamente a que separa as espécies, poderia piorar. Aqui melhorou, mas não para todos: 51 pinguins passam a acertar e 4 passam a errar (`para_tela.acuracia_2_medidas.mudam`). [16, 19]
9. **"k = 5 é o certo" ou "k maior é sempre melhor".** k depende dos dados. k = 1 vai atrás de qualquer pinguim fora do padrão; k = 341 (todos os outros) responde "Adélia" para todos. [11, 12]
10. **"O KNN acerta 93% dos pinguins" (ponto final).** É a acurácia de deixar-um-de-fora nestes 342 pinguins, de 3 ilhas, entre 2007 e 2009. É uma estimativa para pinguins parecidos, não uma garantia. [22]
11. **"Cover e Hart provaram que o KNN erra no máximo o dobro do mínimo."** Só no limite de infinitos exemplos, e para o vizinho mais próximo (k = 1). Não vale para os 342 pinguins. E esse limite não depende da régua: o problema da escala é justamente dos dados finitos. [13, 15]
12. **"Fix e Hodges inventaram o KNN com voto da maioria em 1951" ou "publicaram em 1951".** Foi um relatório técnico da Força Aérea dos EUA, só publicado em revista em 1989, e a regra deles compara frações de duas amostras. Diga: "a ideia aparece num relatório de 1951". [6, 7]
13. **"Desempata pelo mais próximo, como o scikit-learn."** O scikit-learn desempata pela ordem alfabética (Adelie, Chinstrap, Gentoo). O `calcular.py` implementa a regra da pauta à mão e mostra quantas previsões mudam em relação ao scikit-learn (`sklearn` em `resultados.json`). [9]
14. **"Testei com os mesmos pinguins e acertou 100%."** Se o pinguim participa da própria votação, ele é o próprio vizinho, à distância 0. Por isso a nota é por deixar-um-de-fora. [23]
15. **Na tela, "√(−8,7² + 0²)".** Pela regra das contas, −8,7² é −(8,7²) = −75,69, e a raiz ficaria de um número negativo. Escreva (−8,7)² ou use a diferença sem sinal, 8,7². O sinal não importa, porque o quadrado o apaga. O `resultados.json` atual já escreve sem sinal ("√(8,7² + 0²)"); mantenha assim nas cenas.

## Ressalvas de fonte

- **Fix e Hodges (1951):** li uma cópia escaneada do relatório (DTIC ADA800276, pelo Wayback Machine, porque o DTIC bloqueia o download direto). O texto extraído por OCR é ruim, então li as páginas do relatório como imagem (pp. 13 e 20). Na cópia, o sinal da desigualdade da regra (M ÷ m contra c × N ÷ n) está ilegível; não cite a direção. Não li a reimpressão de 1989 (*International Statistical Review*, JSTOR, paga) nem o comentário de Silverman e Jones na mesma edição: conferi só os metadados no Crossref.
- **Cover e Hart (1967):** li o artigo inteiro (6 páginas), num PDF escaneado da página de Cover em Stanford. As fórmulas saem embaralhadas no OCR; os limites (2R*(1 − R*) e R*(2 − MR*/(M − 1))) batem com o *Elements* (p. 465) e com as notas de Cornell.
- **Desempate do scikit-learn:** a documentação não diz em texto como desempata o voto; diz só que as classes ficam em ordem lexicográfica no `predict_proba` e que empates de distância na k-ésima vaga dependem da ordem dos dados. A regra "a primeira em ordem alfabética" vem do código-fonte da versão 1.9.1 (a do `.venv`) e de um teste que rodei.
- **Exemplos das fontes não são dados reais:** o salário e a idade do *ISLP* são um exemplo imaginado. Os 35,19% e 96,30% da página "Importance of Feature Scaling" do scikit-learn são de PCA com regressão logística, não de KNN; não use como número de KNN.
- **Contas minhas, sem fonte direta:** "a média se cancela na diferença" e "ddof não muda nenhum vizinho" (item [25] de `fontes.md`) são álgebra de uma linha, não citação.
- **Conferência com `resultados.json` (versão de 20/10/2026, 18h45):** o z do pinguim misterioso na tela usa a média e o desvio dos 342 (massa −0,81); com os 341 da rodada dá −0,82, e os vizinhos são os mesmos (nota em `para_tela.misterioso.z`). A tela deve mostrar um só dos dois, com a conta que fecha com ele.
