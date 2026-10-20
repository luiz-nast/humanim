# Fontes: árvore de decisão

## Dados

### O dataset

- **Default of Credit Card Clients** (UCI Machine Learning Repository, id 350). 30 000 clientes reais de cartão de crédito em Taiwan, com 6 meses de histórico (abril a setembro de 2005), e o alvo: deu calote ou não no mês seguinte (coluna `default payment next month`). 23 atributos, sem valores faltando.
- Página: https://archive.ics.uci.edu/dataset/350/default+of+credit+card+clients
- Arquivo baixado: https://archive.ics.uci.edu/static/public/350/default+of+credit+card+clients.zip → `dados/default_of_credit_card_clients.zip` (5 539 494 bytes; dentro, `default of credit card clients.xls`, 5 539 328 bytes). SHA-256 do zip: `56c885f84457f6680f8438f02bfcdac9579323d8a94465ee5f26e32baa727602`.
- Acesso e download: 19/10/2026 (23:07 UTC).
- DOI do dataset: 10.24432/C55S3H. Criador: I-Cheng Yeh.
- Licença: Creative Commons Attribution 4.0 International (CC BY 4.0), como diz a página do UCI: https://creativecommons.org/licenses/by/4.0/legalcode. Pede atribuição: citar o dataset (Yeh, UCI) quando os números aparecerem no vídeo ou na legenda do post.
- Artigo de origem: Yeh, I-C. & Lien, C-h. (2009). *The comparisons of data mining techniques for the predictive accuracy of probability of default of credit card clients*. Expert Systems with Applications, 36(2), 2473–2480. https://doi.org/10.1016/j.eswa.2007.12.020
- Dicionário (documentação do UCI): `PAY_0` = situação da fatura de setembro/2005 (-1 = pagou em dia; 1 = um mês de atraso; 2 = dois meses; … 9 = nove ou mais); `PAY_2`…`PAY_6` = agosto a abril; `LIMIT_BAL` = limite de crédito em NT$ (dólar taiwanês novo), incluindo cartões adicionais da família; `PAY_AMT1` = valor pago em setembro/2005; `AGE` = idade; `MARRIAGE` 1 = casado.
- Cuidado: os dados têm os códigos -2 e 0 em `PAY_*`, que a documentação oficial não define (2 759 e 14 737 clientes em `PAY_0`). A pergunta vencedora (`PAY_0 >= 2`) só usa códigos documentados do lado "sim"; -2 e 0 caem todos no lado "não". Não descreva -2 nem 0 no vídeo.
- Rótulo da tela (linhas 15 e 16): a pergunta do lado "sim" da gulosa, `PAY_3 <= -0.5`, aparece como "julho quitado?". Ela junta o -1 (pagou em dia, documentado) e o -2 (não documentado); o 0 fica do outro lado. É uma simplificação de rótulo; a fala não descreve os códigos.

### Contexto real (o gancho)

- FinanceAsia, Lara Wozniak, 28/03/2006, *Taiwan's increasingly dangerous credit-card problem*: https://www.financeasia.com/article/taiwans-increasingly-dangerous-credit-card-problem/36228. Diz que a alta da inadimplência no 3º trimestre de 2005 (o mesmo período do dataset) veio da expansão agressiva dos bancos e de falhas nos seus modelos de pontuação de crédito, e que a taxa anualizada de baixa para prejuízo chegou a 14% no cartão de crédito e 17% no *cash card* em janeiro de 2006.
- Ressalva: não li o texto completo do artigo de Yeh & Lien (é pago). Nome do banco, como a amostra foi tirada e a ligação do artigo com a crise não foram conferidos por mim; no vídeo, diga só "30 mil clientes de cartão em Taiwan, 2005".
- Evitei a página da Seven Pillars Institute sobre a crise: ela traz "US$ 268 bilhões" de dívida em fevereiro de 2006, número que parece confundir NT$ com US$.

### Por que este e não outro

- **Statlog German Credit (UCI 144)**: só 1 000 linhas, de 1973 a 1975, com os maus pagadores "heavily oversampled" (300 de 1 000 não é a taxa real), e o próprio UCI publicou uma correção porque a codificação da versão Statlog tinha erros graves (South German Credit, UCI 522 e 573: https://archive.ics.uci.edu/dataset/573/south+german+credit+update). Atributos em códigos (A11, A14…) e em marcos alemães.
- **Dados brasileiros de crédito**: não há base aberta por cliente (sigilo bancário, Lei Complementar 105/2001); o Banco Central publica só agregados. Saúde (SRAG/OpenDataSUS) é real e brasileira, mas pesada (milhões de linhas) e sensível demais para um vídeo sobre como a árvore escolhe a pergunta.
- **Fraude (cartões europeus, Kaggle/ULB)**: os atributos são V1…V28 (PCA), ilegíveis para leigo. **Churn de telecom da IBM**: dados fictícios.
- O de Taiwan junta tudo: dado real de banco, 30 mil pessoas, licença aberta, atributos que qualquer um entende (atraso, limite, quanto pagou, idade) e uma pergunta vencedora óbvia depois de vista, mas que derruba as intuições de senso comum (idade e estado civil quase não separam nada).

### Como os números foram calculados

- Script: `dados/calcular.py` (rodar da raiz: `.venv/bin/python videos/arvore-de-decisao/dados/calcular.py`). Saída: `dados/resultados.json`. Versões: scikit-learn 1.9.1, pandas e numpy do `.venv`.
- Cada número sai duas vezes: contagens com pandas + fórmula, conferidas pelo `crosstab`, por um toco do scikit-learn com só aquela pergunta e por uma busca exaustiva em numpy de todos os 174 581 cortes possíveis na raiz. Conferência extra, à parte: o .xls lido com `xlrd` puro e as contas refeitas com frações exatas (biblioteca padrão), batendo em todas as 6 perguntas.
- Overfitting: `train_test_split(test_size=0.3, stratify=y, random_state=42)` (21 000 treino, 9 000 teste), confirmado com 10 sementes (0 a 9): a árvore sem limite fica abaixo do chute "todo mundo paga" em todas.
- Conta na tela: com 2 casas, a conta da raiz e a da pergunta vencedora fecham exatamente (bloco `para_tela` do JSON). Não misture 2 e 3 casas no Gini da raiz (0,34454: 0,34 com 2 casas, 0,345 com 3).

### Números-chave (todos de `resultados.json`)

| Número | O que é |
| --- | --- |
| 30 000 clientes; 6 636 calotes = 22,12% | a base: mais de 1 em cada 5 não pagou no mês seguinte |
| Gini da raiz 0,34 (0,3445) | a "bagunça" inicial: 1 − (0,78² + 0,22²) = 0,34; o máximo para 2 classes é 0,5 |
| 174 581 | perguntas (coluna + limiar) que a árvore testa só para escolher a primeira |
| "2 meses ou mais de atraso em setembro?" | a pergunta vencedora (no scikit-learn: `PAY_0 <= 1.5`, a mesma) |
| Sim: 3 130 clientes, 2 177 calotes = 69,6% (Gini 0,42) | do lado "sim", cerca de 7 em cada 10 não pagaram |
| Não: 26 870 clientes, 4 459 calotes = 16,6% (Gini 0,28) | do lado "não", cerca de 1 em cada 6 |
| Gini ponderado 0,29; ganho 0,05 (0,0524) = 15,2% da bagunça | 0,10 × 0,42 + 0,90 × 0,28 = 0,29; 0,34 − 0,29 = 0,05 |
| "Algum atraso (1+ mês)?" ganho 0,0467 | mesma coluna, limiar um degrau abaixo: perde; o limiar importa |
| Idade (< 30): 22,8% × 21,8% de calote, ganho 0,00005 (0,0%); casado: 23,5% × 21,0%, ganho 0,0003 | o senso comum quase não separa nada |
| 6,5 vezes | o ganho da vencedora sobre a melhor pergunta de outra coluna ("pagou zero em setembro?", 0,0081) |
| Profundidade 2: 82,1% treino, 81,8% teste | árvore pequena, 4 folhas: acerta igual no que viu e no que não viu |
| Sem limite: 99,95% treino, 72,3% teste, 3 251 folhas (6,5 clientes por folha), profundidade 40 | decorou: perde até do chute "todo mundo paga" (77,9%); quando diz "calote", acerta 38% (a de profundidade 2 acerta 70%) |

## Teoria

Como a árvore de classificação (CART, como no scikit-learn) escolhe a pergunta de cada nó. As notas para o roteiro estão em `teoria.md`; aqui fica de onde sai cada afirmação. Tudo lido em 19/10/2026. As páginas são as do PDF de cada obra.

### Fontes lidas (texto aberto)

| # | Fonte | O que foi lido | URL |
| --- | --- | --- | --- |
| T1 | scikit-learn 1.9.1, Guia do Usuário, *1.10. Decision Trees* (documentação oficial) | desvantagens; 1.10.5 dicas; 1.10.6 ID3, C4.5, C5.0 e CART; 1.10.7 formulação matemática; 1.10.9 poda de custo-complexidade | https://scikit-learn.org/stable/modules/tree.html |
| T2 | scikit-learn 1.9.1, referência de `DecisionTreeClassifier` | parâmetros `criterion`, `splitter`, `max_depth`, `min_samples_split`, `min_samples_leaf`, `random_state`, `min_impurity_decrease` | https://scikit-learn.org/stable/modules/generated/sklearn.tree.DecisionTreeClassifier.html |
| T3 | Código-fonte do scikit-learn 1.9.1 (a mesma versão do `.venv`) | classe `Gini` e `Entropy` (`_criterion.pyx`), regras de parada (`_tree.pyx`), logaritmo na base 2 (`_utils.pyx`) | https://github.com/scikit-learn/scikit-learn/blob/1.9.1/sklearn/tree/_criterion.pyx#L532-L620 · https://github.com/scikit-learn/scikit-learn/blob/1.9.1/sklearn/tree/_tree.pyx#L227-L252 · https://github.com/scikit-learn/scikit-learn/blob/1.9.1/sklearn/tree/_utils.pyx#L64-L65 |
| T4 | Quinlan, J. R. (1986). *Induction of Decision Trees*. Machine Learning 1(1), 81–106 (o artigo do ID3) | seções 2 a 5 e 7 (pp. 84–102) | DOI: https://doi.org/10.1007/BF00116251 · PDF lido: https://hunch.net/~coms-4771/quinlan.pdf |
| T5 | Hastie, Tibshirani & Friedman, *The Elements of Statistical Learning*, 2ª ed., 12ª impressão corrigida (2017), PDF gratuito dos autores | seção 9.2, pp. 305–313 | https://hastie.su.domains/ElemStatLearn/ (download: https://hastie.su.domains/ElemStatLearn/download.html) |
| T6 | James, Witten, Hastie, Tibshirani & Taylor, *An Introduction to Statistical Learning with Applications in Python* (ISLP, 2023), PDF gratuito dos autores | seção 8.1, pp. 331–341 | https://www.statlearning.com/ |
| T7 | Therneau & Atkinson (Mayo Foundation), *An Introduction to Recursive Partitioning Using the RPART Routines*, vinheta do pacote `rpart` do R (versão de 26/03/2026). O `rpart` implementa as ideias do livro do CART | seções 1 e 3 (pp. 2–7) | https://cran.r-project.org/web/packages/rpart/vignettes/longintro.pdf |
| T8 | Loh, W.-Y. (2014). *Fifty Years of Classification and Regression Trees*. International Statistical Review 82(3), 329–348 (revisão histórica) | seções 1 e 2 (pp. 329–332) | DOI: https://doi.org/10.1111/insr.12016 · PDF do autor: https://pages.stat.wisc.edu/~loh/treeprogs/guide/LohISI14.pdf |
| T9 | Cornell University, CS4780 (K. Weinberger, 2018), notas da aula 17: *Decision Trees* | inteira | https://www.cs.cornell.edu/courses/cs4780/2018fa/lectures/lecturenote17.html |
| T10 | Banco Mundial, indicador *Gini index* (SI.POV.GINI): a definição oficial do coeficiente de Gini de desigualdade | definição | https://data.worldbank.org/indicator/SI.POV.GINI (texto da definição pela API oficial: https://api.worldbank.org/v2/indicator/SI.POV.GINI?format=json) |

### Citadas, mas não lidas (só os metadados foram conferidos no Crossref)

- **Breiman, Friedman, Olshen & Stone (1984). *Classification and Regression Trees*.** Wadsworth, Belmont (CA), segundo a referência [BRE] da T1; reedição Routledge/CRC, DOI https://doi.org/10.1201/9781315139470. O livro é pago e eu não o li. O que estas notas dizem do CART vem de T1, T5, T7 e T8, que o descrevem e citam.
- **Hyafil & Rivest (1976). *Constructing optimal binary decision trees is NP-complete*.** Information Processing Letters 5(1), 15–17. https://doi.org/10.1016/0020-0190(76)90095-8. Não li o artigo. A afirmação de que achar a árvore ótima é NP-completo vem da T1 (desvantagens) e da T9 ("NP-Hard").
- **Quinlan (1993). *C4.5: Programs for Machine Learning*.** Morgan Kaufmann. Não li. O que digo do C4.5 vem da T8 (seção 2.3) e da T1 (1.10.6).

### Cada afirmação e a sua fonte

**Medir a bagunça (impureza de Gini)**

1. Proporção da classe k no nó m: p_mk = (exemplos da classe k no nó) / (exemplos no nó). Gini do nó = soma de p_mk × (1 − p_mk), que é igual a 1 − soma de p_mk². T1 (1.10.7.1); T5 eq. 9.17, p. 309; T6 eq. 8.6, p. 338; T3 (docstring da classe `Gini`, que traz as duas formas).
2. Com duas classes e proporção p, Gini = 2p(1 − p), máximo de 0,5 quando p = 0,5. T5 p. 309 (e a Figura 9.3); T9 ("reaches its maximum at p=0.5").
3. Gini pequeno = nó quase todo de uma classe; por isso o Gini é chamado de medida de "pureza do nó". T6 p. 339.
4. Leitura exata do Gini: em vez de dar a todos o rótulo da maioria, dê a cada exemplo um rótulo sorteado com as proporções do nó; a taxa de erro esperada dessa regra é o Gini. T5 p. 310; T7 seção 3.2.1, p. 7 (sorteia o objeto e sorteia a classe pela mesma distribuição: a chance de errar é 1 − soma de p_i²). Outra leitura dada pela T5: é a soma das variâncias da resposta 0/1 de cada classe; T6 p. 338 chama de "medida de variância total".
5. Não é a taxa de erro da árvore. A árvore rotula o nó pela classe da maioria (T5 p. 309; T6 p. 338), e a taxa de erro do nó é 1 − (maior proporção) (T5 eq. 9.17; T6 eq. 8.5), outra medida.
6. "Gini" aqui não é o coeficiente de Gini da desigualdade de renda: aquele mede a área entre a curva de Lorenz e a linha de igualdade, de 0 a 100 (T10). A T9 avisa: "This is different from Gini coefficient". A T8 (p. 330) conta que Messenger & Mandell (1972), no THAID, atribuíram o índice de Gini usado em árvores a Light & Margolin (1971).
7. A função de impureza precisa valer 0 num nó puro e ser côncava (T7 seção 3.1, p. 6). Consequência: dividir um nó nunca aumenta a impureza ponderada (o ganho é sempre maior ou igual a zero). Conferido nos dados: na raiz, nenhuma das 174 581 perguntas tem ganho de Gini menor ou igual a zero (`dados/conferir_teoria.json`, bloco C).

**Como uma pergunta é avaliada**

8. Uma pergunta candidata é um par (coluna j, limiar t): à esquerda vai quem tem x_j ≤ t, à direita o resto. A divisão é sempre em dois (binária). T1 (1.10.7); T5 eq. 9.12, p. 307 (CART: "recursive binary splitting", Figura 9.2).
9. Qualidade da pergunta = impureza dos dois filhos ponderada pelo tamanho: G = (n_esq / n) × H(esq) + (n_dir / n) × H(dir). A árvore escolhe a pergunta de menor G. T1 (1.10.7, fórmula de G e argmin); T5 p. 309 ("weight the node impurity measures by the number N_mL and N_mR"); T4 p. 90 (E(A), "the weighted average").
10. Escolher o menor G é o mesmo que escolher a maior redução de impureza, ΔI = I(pai) − [p(esq) × I(esq) + p(dir) × I(dir)]. T7 seção 3.1, p. 6 ("maximal impurity reduction"); T4 nota 3, p. 90 (como I(pai) é igual para todas as perguntas, maximizar o ganho é minimizar E(A)). O scikit-learn chama de "impurity decrease" e, no parâmetro `min_impurity_decrease`, ainda multiplica por N_t / N (fração das amostras que chegam ao nó; na raiz é 1). T2.
11. Limiares testados: os pontos médios entre valores distintos vizinhos, já ordenados. Com `splitter='best'` (o padrão), é uma "busca exaustiva gulosa" em todas as colunas e todos os limiares. T1 (1.10.7). O ID3 faz o mesmo com atributos contínuos: ordena os valores e testa cada ponto entre dois vizinhos (T4 p. 101). Por isso o limiar do scikit-learn na vencedora é 1,5 (entre os códigos 1 e 2 de `PAY_0`).

**Busca gulosa, recursão e parada**

12. É guloso: escolhe a melhor pergunta naquele passo, sem olhar adiante para ver se outra levaria a uma árvore melhor. T6 p. 334 ("top-down, greedy ... recursive binary splitting"); T5 p. 307 (achar a melhor partição é inviável, "Hence we proceed with a greedy algorithm").
13. Por isso não há garantia de achar a melhor árvore. Achar a árvore ótima é NP-completo, e os algoritmos práticos usam heurísticas gulosas, com decisões ótimas só localmente. T1 (desvantagens); T9 ("Finding a minimum size tree is NP-Hard"); T4 p. 88 (o ID3 "cannot guarantee that better trees have not been overlooked"). Conferido nos dados: entre 11 colunas, a árvore de 2 níveis com menor Gini nas folhas começa por outra pergunta (`PAY_0 <= 0.5`), não pela gulosa (`dados/conferir_teoria.json`, bloco F).
14. Recursão: depois de escolher a pergunta, o mesmo procedimento é aplicado a cada filho, até um critério de parada. T1 (1.10.7); T5 p. 307; T4 p. 90 ("the same process recursively").
15. Critérios de parada do scikit-learn: profundidade máxima (`max_depth`), poucas amostras no nó (`min_samples_split`), ganho abaixo de `min_impurity_decrease`; e o nó vira folha se a impureza é zero. T1 (1.10.7); T3 (`_tree.pyx`, linhas 230–252). Com o padrão `max_depth=None`, os nós são expandidos até todas as folhas ficarem puras ou com menos de `min_samples_split` (padrão 2) amostras. T2.
16. Só existe árvore que acerta 100% do treino se não houver dois exemplos com atributos idênticos e rótulos diferentes. T9. Conferido nos dados: no treino há 11 grupos assim, e a árvore sem limite erra exatamente 11 clientes do treino (`conferir_teoria.json`, bloco G).
17. Parar quando o ganho fica pequeno é míope: uma divisão que parece inútil pode abrir caminho para uma ótima logo abaixo. A estratégia preferida é crescer uma árvore grande e podar. T5 p. 308; T9 (exemplo do XOR: a primeira pergunta não melhora a impureza; "Decision trees are myopic").
18. O CART trocou as regras de parada por "crescer grande e podar" até o tamanho com menor erro na validação cruzada, numa poda pelo elo mais fraco (*weakest link*) indexada pelo parâmetro de custo-complexidade. T8 seção 2.1, p. 331; T7 seção 1, p. 3; T5 pp. 308 (custo-complexidade C_α(T) = erro + α × número de folhas); T1 (1.10.9: `ccp_alpha`, "described in Chapter 3 of [BRE]").
19. A folha prevê a classe da maioria e devolve a proporção de cada classe como probabilidade (`predict_proba`). T1 (1.10.7.1); T5 p. 309.

**Por que a árvore funda decora**

20. Árvores complexas demais não generalizam ("overfitting"); poda, mínimo de amostras por folha e profundidade máxima são "necessários" para evitar isso. T1 (desvantagens); T1 1.10.5 (use `max_depth` para controlar o tamanho; `min_samples_leaf` pequeno "will usually mean the tree will overfit"). "A very large tree might overfit the data" (T5 p. 307).
21. Mecanismo: um atributo de valores aleatórios dá um ganho aparente, a não ser que as proporções nos filhos fiquem exatamente iguais às do pai. T4 p. 93. Erros nos rótulos ("ruído") forçam a árvore a "explicar" casos especiais: no exemplo do artigo, um rótulo corrompido faz a menor árvore correta passar de 8 para 12 nós, "spurious complexity". T4 p. 92. Conferido nos dados: até o número de ID do cliente, sem sentido nenhum, tem ganho positivo na melhor pergunta binária (0,0003) (bloco E).
22. Entre árvores que acertam o treino, a mais simples deve generalizar melhor (navalha de Occam, com limites de erro que crescem com a complexidade). T4 p. 87 e nota 2.
23. Árvores são instáveis (alta variância): uma pequena mudança nos dados pode dar uma sequência de perguntas bem diferente, porque um erro no topo se propaga para tudo abaixo. T5 p. 312; T1 (desvantagens). No scikit-learn, as colunas são embaralhadas a cada nó e, em empate exato de ganho, a escolhida muda com `random_state`. T2.

**Entropia e ganho de informação (ID3, C4.5)**

24. Entropia do nó = −soma de p_k × log(p_k). T1 (1.10.7.1); T5 eq. 9.17; T6 eq. 8.7, p. 339. No scikit-learn o log é na base 2 (bits): `log(x) = ln(x) / ln(2)`. T3 (`_utils.pyx`). Usar entropia equivale a minimizar a log loss da árvore no treino. T1 (1.10.7.1).
25. No ID3: I(p, n) = −(p/(p+n)) log2(p/(p+n)) − (n/(p+n)) log2(n/(p+n)); E(A) = média ponderada de I nos ramos; gain(A) = I(p, n) − E(A). Exemplo do artigo, 14 sábados: 0,940 bits; gain(outlook) = 0,246 bits, o maior, e outlook vira a raiz. T4 pp. 89–91.
26. O ID3 abre um ramo por valor do atributo categórico (árvore multi-ramos) e escolhe o de maior ganho de informação. T1 (1.10.6); T4 p. 90. O CART sempre faz divisões binárias; o C4.5 abre vários ramos para atributos categóricos e faz "X < c" para os ordenados. T8 seções 2.3 e 2.5, pp. 331–332.
27. O ganho de informação favorece atributos com muitos valores. No extremo, um atributo aleatório com um valor diferente para cada exemplo teria ganho máximo e seria escolhido para a raiz, "a singularly poor choice". A correção de Quinlan é a razão de ganho: gain(A) / IV(A), em que IV(A) é a informação da própria resposta "qual é o valor de A?". T4 seção 7, pp. 100–102. O C4.5 usa a razão de ganho. T8 seção 2.3, p. 331. Conferido nos dados: dividir pelo ID do cliente (30 000 ramos) zera a impureza, com ganho máximo em Gini e em entropia, e a razão de ganho derruba esse ID (bloco E).
28. Mesmo com divisões binárias, sobra um viés: uma coluna com mais valores distintos oferece mais limiares e tem mais chance de ser escolhida, mesmo sem relação com o alvo. Breiman et al. (1984, p. 42) já apontavam isso no CART. T8 p. 332.
29. Gini e entropia são parecidos: para duas classes "differ only slightly, and will nearly always choose the same split point" (T7 seção 3.1, p. 6); "quite similar numerically" (T6 p. 339). Conferido nos dados: as 5 melhores perguntas da raiz são as mesmas e na mesma ordem pelos dois critérios (bloco C).
30. A taxa de erro de classificação não é sensível o bastante para crescer a árvore; Gini e entropia são. Exemplo da T5: com (400, 400), as divisões (300, 100)/(100, 300) e (200, 400)/(200, 0) erram as duas 25%, mas a segunda cria um nó puro e tem Gini e entropia menores. T5 pp. 309–310; T6 p. 338; T7 seção 3.1, p. 5 (com 80% de uma classe, uma divisão em 54% e 100% tem redução de risco zero, embora seja "very informative"). Conferido nos dados: pela taxa de erro, 174 533 das 174 581 perguntas da raiz teriam ganho zero (bloco C).
31. Uma divisão pode baixar o Gini sem mudar nenhuma previsão (os dois filhos com a mesma classe de maioria). Ela é feita porque aumenta a pureza, e a confiança da previsão muda. T6 pp. 340–341. Conferido nos dados no lado "não" da raiz (bloco D).
32. "ID3 (Iterative Dichotomiser 3) was developed in 1986 by Ross Quinlan", diz a T1 (1.10.6). Cuidado: o próprio artigo de 1986 (T4, pp. 84–85) põe o ID3 em 1979 ("ID3 (Quinlan, 1979, 1983a)", um dos programas derivados do CLS); o artigo de 1986 é a descrição de referência, não o nascimento. No vídeo, diga "Quinlan, anos 1980", não "inventado em 1986".
33. O scikit-learn usa "uma versão otimizada do CART" e não aceita variáveis categóricas por enquanto (é preciso codificá-las em números). T1 (1.10.6). Escolhe Gini por padrão (`criterion='gini'`); "entropy" e "log_loss" dão o ganho de informação de Shannon. T2. No `rpart`, sem parâmetros, a regra de divisão também é a de Gini; a alternativa é "information". T7 pp. 11 e 23.
34. A T1 (1.10.6) diz que o CART escolhe o par "que dá o maior ganho de informação". É frouxo: no CART e no scikit-learn o padrão é o Gini (T2, T7). Use "redução de impureza" para Gini e "ganho de informação" só para entropia.

**História, para contexto (T8, seção 1–2, pp. 329–331)**

35. AID (Morgan & Sonquist, 1963) é o primeiro algoritmo de árvore de regressão publicado; THAID (Messenger & Mandell, 1972) leva a ideia para classificação (Loh apresenta entropia e Gini como as funções de impureza alternativas nesse ponto); o CART (Breiman et al., 1984) "foi instrumental" para reacender o interesse, com a mesma busca gulosa e a poda por validação cruzada.

**Detalhe de estrutura**

36. No ID3, cada nó calcula o ganho só dos atributos "ainda não testados" naquele caminho (T4 p. 91: "the gain of each untested attribute A"). Com divisões binárias, a mesma coluna pode voltar mais abaixo: Quinlan aponta, nas árvores binárias, "multiple tests on the same attribute" (T4 p. 101). Conferido nos dados: a árvore de 2 níveis de menor Gini usa `PAY_0` na raiz e de novo num filho (`conferir_teoria.json`, bloco F).

### Conferência da teoria nos dados reais

- Script: `dados/conferir_teoria.py` (rodar da raiz: `.venv/bin/python videos/arvore-de-decisao/dados/conferir_teoria.py`, uns 10 s). Saída: `dados/conferir_teoria.json`. Usa o mesmo zip e a mesma divisão treino/teste de `calcular.py` (`test_size=0.3, stratify=y, random_state=42`). Ele não gera os números do roteiro: só confere a teoria. Os números do roteiro continuam em `resultados.json`.
- O que ele mostra (os blocos do JSON):
  - **A.** Sortear o rótulo pela proporção (78/22) erra em média 0,3440 em 20 rodadas (de 0,3402 a 0,3498); o Gini da raiz é 0,3445. Dois clientes sorteados são de classes diferentes em 0,3464 de 200 mil pares. Rotular todos pela maioria erra 0,2212. Entropia da raiz: 0,762 bits.
  - **B.** Na vencedora (`PAY_0 >= 2`), a média simples dos dois Gini dá 0,3502, acima do 0,3445 da raiz (pareceria piorar); a ponderada dá 0,2921 (ganho de 0,0524). Em entropia: 0,762 → 0,673 bits, ganho de 0,0891 bits. Em taxa de erro: 22,12% → 18,04% (6 636 → 5 412 erros).
  - **C.** Busca exaustiva na raiz pelos três critérios (174 581 perguntas): Gini, entropia e erro escolhem a mesma vencedora (`PAY_0 <= 1.5`); Gini e entropia têm o mesmo top 5, na mesma ordem. Nenhuma pergunta tem ganho de Gini ≤ 0. Pela taxa de erro, 174 533 têm ganho zero: só 48 mudam alguma previsão.
  - **D.** No lado "não" da raiz (26 870 clientes, 16,6% de calote), a melhor pergunta por Gini (`PAY_2 <= 1.5`) separa 14,3% de 41,6% de calote. Os dois lados continuam com maioria "paga", e os acertos ficam iguais (22 411 antes e depois), mas o Gini cai de 0,2768 para 0,2653.
  - **E.** Divisão em vários ramos pelo ID do cliente: 30 000 ramos, ganho de Gini 0,3445 e de entropia 0,762 bits, os dois máximos (zera a impureza). A razão de ganho cai para 0,051 (IV = 14,87 bits); a da vencedora binária é 0,185. A melhor pergunta binária sobre o ID tem ganho de Gini de 0,0003. `PAY_0` com um ramo por valor (11 ramos) tem ganho de 0,0616, acima do 0,0524 da binária: refinar um atributo nunca diminui o ganho (T4 p. 100: gain(A') ≥ gain(A)).
  - **F.** Profundidade 2, buscando em todas as 203 perguntas de 11 colunas (`PAY_0`…`PAY_6`, `SEX`, `EDUCATION`, `MARRIAGE`, `AGE`, `LIMIT_BAL`) em cada nó. A gulosa (a mesma do scikit-learn) é `PAY_0 <= 1.5`, depois `PAY_2 <= 1.5` e `PAY_3 <= -0.5`, com Gini nas folhas de 0,28101 e 82,01% de acerto. A de menor Gini nas folhas começa por `PAY_0 <= 0.5` e chega a 0,28082. A de maior acerto (82,06%) tem a mesma raiz da gulosa e outro limiar num filho (`PAY_2 <= 2.5`). As diferenças são pequenas, mas mostram que guloso não é ótimo.
  - **G.** Gini contra entropia, por profundidade (teste): idênticos até a profundidade 2, com diferença de no máximo 0,12 ponto até a 6. Sem limite: Gini 72,32% e entropia 73,71% no teste, 99,95% no treino nos dois. A raiz é a mesma; as árvores de profundidade 3 já diferem. A árvore sem limite muda com `random_state` (teste de 71,84% a 72,07% nas sementes 0 a 4; 72,32% na 42). No treino, os 11 erros da árvore sem limite são os 11 clientes com ficha idêntica à de outro e rótulo diferente.

## Roteiro

De onde sai cada número e afirmação do `roteiro.md` (17 linhas). Os números de linha abaixo são os do roteiro.

- Script: `dados/numeros_roteiro.py` (rodar da raiz: `.venv/bin/python videos/arvore-de-decisao/dados/numeros_roteiro.py`, menos de 1 s). Não lê o dataset: lê `resultados.json` e `conferir_teoria.json`, faz as contas derivadas que o roteiro usa (porcentagens inteiras, arredondamentos de tela, cortes por tipo de coluna, a bagunça que o melhor corte de idade e de estado civil tira) e para com erro se alguma frase do roteiro deixar de valer. Saída: `dados/numeros_roteiro.json`.
- Linha 2: 30 000 clientes, 22,12% de calote no mês seguinte (Dados, acima). Na tela, "dados: Yeh, UCI" cumpre a atribuição da CC BY 4.0.
- Linhas 4 a 6: "bagunça é a chance de dois clientes sorteados serem diferentes" é a leitura do item 4 da Teoria (T5 p. 310; T7 seção 3.2.1), conferida no bloco A de `conferir_teoria.json` (0,3464 em 200 mil pares, contra Gini 0,3445). Contas de tela com 2 casas: `para_tela` de `resultados.json`.
- Linhas 8 a 11: lados da vencedora, média sem peso (0,35), ponderada (0,29) e "tirou 15%" (15,2% exato; 0,05 ÷ 0,34 = 14,7% com os números da tela; os dois arredondam para 15%). Nome "redução de impureza": item 10 da Teoria.
- Linha 12: 174 581 cortes na raiz (busca exaustiva de `resultados.json`): 58 nas 6 colunas de atraso, 174 458 nas 13 colunas de valores em NT$, 65 nas outras 4.
- Linha 13: o melhor corte de idade (`AGE <= 25,5`) tira 0,18% da bagunça; o de estado civil (`MARRIAGE <= 1,5`), 0,08%; "casado?" (`MARRIAGE == 1`, que não é um corte), 0,09%. Todos abaixo de 1%.
- Linha 14: "algum atraso" (`PAY_0 >= 1`) deixa 6 818 clientes no lado "sim", com 50,3% de calote (Gini 0,50), e perde no Gini ponderado: 0,2979 contra 0,2921 (`varredura_PAY_0`).
- Linhas 15 e 16: "busca gulosa, não garante a melhor árvore" são os itens 12 e 13 da Teoria. O exemplo "começar por um mês dava um tiquinho menos bagunça" é a exceção desta lista: vem do bloco F de `conferir_teoria.json`, não de `resultados.json`. Vale só como está dito: menos bagunça nas folhas (0,2808 contra 0,2810 da gulosa), não mais acerto (a árvore de 2 andares com mais acerto, 82,06%, tem a mesma raiz da gulosa), numa busca em 11 colunas. A gulosa dessas 11 colunas é a mesma árvore que o scikit-learn faz com as 23.
- O gancho da crise de 2005 (FinanceAsia, acima) saiu do roteiro; se for usado, que seja na legenda do post, longe do "22%", que é a taxa desta amostra, não a de Taiwan.
