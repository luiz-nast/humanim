
## Dados

### O dataset

- **Palmer Penguins**: 344 pinguins adultos medidos perto da estação Palmer, no arquipélago de Palmer (Antártida), de 2007 a 2009, nas ilhas Biscoe, Dream e Torgersen. São 3 espécies: Adélia (*Pygoscelis adeliae*, pinguim-de-adélia), Gentoo (*P. papua*) e Barbicha (*P. antarcticus*, chinstrap, pinguim-de-barbicha). Colunas: espécie, ilha, comprimento e altura do bico (mm), comprimento da nadadeira (mm), massa corporal (g), sexo e ano.
- Estudo original: Gorman, K. B., Williams, T. D. & Fraser, W. R. (2014). *Ecological Sexual Dimorphism and Environmental Variability within a Community of Antarctic Penguins (Genus Pygoscelis)*. PLoS ONE 9(3): e90081. https://doi.org/10.1371/journal.pone.0090081
- Dados brutos (Environmental Data Initiative, Palmer Station Antarctica LTER e K. Gorman, 2020): Adélia ver. 5, https://doi.org/10.6073/pasta/98b16d7d563f265cb52372c8ca99e60f · Gentoo ver. 5, https://doi.org/10.6073/pasta/7fca67fb28d56ee2ffa3d9370ebda689 · Barbicha ver. 6, https://doi.org/10.6073/pasta/c14dfcfada8ea13a17536e73eb6fbe9e
- Pacote que organiza a tabela: Horst, A. M., Hill, A. P. & Gorman, K. B. (2020). *palmerpenguins: Palmer Archipelago (Antarctica) penguin data*. R package. https://doi.org/10.5281/zenodo.3960218 · https://allisonhorst.github.io/palmerpenguins/
- Arquivo baixado: https://raw.githubusercontent.com/allisonhorst/palmerpenguins/main/inst/extdata/penguins.csv → `dados/penguins.csv` (15.241 bytes, 344 linhas + cabeçalho). SHA-256: `f204db2c753b0937caac3cb35258562c14f073e4bbc76be24b4c51ce22767a93`. Branch `main` no commit `8957207b78d6ccd1b4654a9dd9c9041b657478ab`; a última mudança no arquivo é o commit `156daa4` (15/07/2020, "Adding year to penguins").
- Licença: **CC0 1.0** (domínio público). Texto em https://raw.githubusercontent.com/allisonhorst/palmerpenguins/main/LICENSE.md → `dados/LICENSE.md` (6.966 bytes, SHA-256 `8e2c443dd9aea6fcd6c293dbf66935bd5ef502fc0ca9b466c773cf9316d5e04c`). O README do pacote diz que os dados são CC-0 "in accordance with" a política de dados da Palmer Station LTER e a política de acesso do LTER para dados Tipo I. Pode publicar e redistribuir; o pacote pede para citar os autores (citação curta para a tela ou o post: "Gorman, Williams & Fraser (2014), via palmerpenguins").
- Lidos para conferir: o README e `R/penguins.R` do repositório (descrição das colunas, unidades e as fontes acima). Acesso e download: 20/10/2026, 21:35 UTC.
- Filtro: tirados os 2 pinguins sem nenhuma medida (linhas 5, Adélia de Torgersen, e 273, Gentoo de Biscoe). Ficam **342**: 151 Adélias, 123 Gentoos e 68 Barbichas. O sexo falta em mais 9, mas ele não entra na conta.

### O modelo e a conta (`dados/calcular.py` → `dados/resultados.json`)

- Rodar da raiz: `.venv/bin/python videos/knn/dados/calcular.py` (leve: uns 170 MB e 4 s).
- KNN de classificação com k = 5 e distância euclidiana **d = √(Δbico² + Δmassa²)**, com o bico em mm e a massa em g. Voto da maioria. Empate 2 a 2: entre as espécies empatadas, ganha a do vizinho mais próximo. Empate de distância na 5ª vaga: entra quem vem antes no arquivo; o script testa todas as escolhas possíveis e nenhuma muda a previsão.
- Padronização: **z = (x − média) ÷ desvio**, com o desvio populacional (ddof=0, o do StandardScaler). Nos 342: bico 43,9 mm ± 5,45 mm; massa 4.202 g ± 801 g. Na diferença entre dois pinguins a média se cancela: Δz = Δx ÷ desvio.
- Avaliação deixar-um-de-fora: esconde um pinguim, os outros 341 votam, repete para os 342; acurácia = acertos ÷ 342. No padronizado, a média e o desvio são refeitos a cada rodada só com os 341 que votam (sem vazar). Padronizar os 342 de uma vez dá exatamente as mesmas previsões (0 diferenças, nas 2 e nas 4 medidas).
- Resultados, 2 medidas: sem padronizar 271 ÷ 342 = 79,2% (71 erros); padronizado 318 ÷ 342 = 93,0% (24 erros). Mudam de previsão 57 pinguins: 51 passam a acertar, 4 passam a errar, 2 trocam um erro por outro (271 + 51 − 4 = 318). A Barbicha, que pesa igual à Adélia (3.733 g contra 3.701 g de média), é a que mais ganha: 30 de 68 certas sem padronizar (33 chamadas de Adélia), 60 de 68 padronizado.
- Apoio, 4 medidas (bico, altura do bico, nadadeira e massa): sem padronizar 274 ÷ 342 = 80,1%; padronizado 337 ÷ 342 = 98,5%.
- Quanto a massa manda sem padronizar: entre todos os pares de pinguins, 99,995% da soma das diferenças ao quadrado vem da massa (é exatamente var_massa ÷ (var_bico + var_massa) = 801² ÷ (5,45² + 801²)). Em todos os 342 pinguins, os 5 vizinhos crus são os 5 de peso mais parecido, e o bico só desempata (71% dos vizinhos crus têm exatamente o mesmo peso; as massas vêm em múltiplos de 25 g). Um desvio de massa vale 801 ÷ 5,45 = 147 desvios de bico na conta crua.
- Pinguim misterioso: linha 320 do `penguins.csv` (o 319º dos 344), um Barbicha macho da ilha Dream, 2008: bico 50,9 mm, massa 3.550 g. Sem padronizar, os 5 vizinhos são 5 Adélias com os mesmos 3.550 g e bico 8,7 a 11,3 mm mais curto (voto 5 a 0, erra); padronizado, 5 Barbichas com bico até 1,2 mm diferente e peso até 150 g (voto 5 a 0, acerta). Nenhum vizinho em comum. Conta até a Adélia (42,2 mm, 3.550 g): √(8,7² + 0²) = 8,7 crua; √(1,60² + 0²) = 1,60 padronizada. Até a Barbicha (51,3 mm, 3.650 g): √(0,4² + 100²) = √(0,16 + 10.000) = 100,0 crua; √(0,07² + 0,12²) = √(0,0049 + 0,0144) = √0,0193 = 0,14 padronizada. Escolha: dos 51 que o KNN erra sem padronizar e acerta padronizado, só 2 têm voto 5 a 0 nos dois jeitos (linhas 320 e 341); o 320 tem medidas típicas de Barbicha, o 341 tem um dos maiores bicos do arquivo (55,8 mm).
- Conferência: (1) scikit-learn 1.9.1, `KNeighborsClassifier(n_neighbors=5)` e `make_pipeline(StandardScaler(), KNeighborsClassifier(n_neighbors=5))` com `LeaveOneOut`: com o mesmo desempate do scikit-learn (alfabético), a conta à mão dá as mesmas previsões nos 342, nos 4 casos (2 e 4 medidas, cru e padronizado); (2) um segundo script, só com pandas e `NearestNeighbors`, refez a contagem, a média, o desvio e os vizinhos do pinguim misterioso, com as mesmas distâncias. As contas encadeadas da tela fecham com a distância exata arredondada (o script para com erro se não fecharem).

### Cuidados

- **O número cru depende do desempate.** Sem padronizar há 13 empates 2 a 2 no voto (2 medidas): 271 acertos com o desempate da pauta, 269 se o 1º vizinho decidisse sempre, 274 no scikit-learn (que desempata pela ordem alfabética do nome). Fale "uns 80%" ou mostre 79,2% com a regra da pauta; não compare com um número do scikit-learn. Padronizado dá 318 em qualquer desempate.
- **A distância crua não tem unidade**: ela soma mm² com g². Na tela, "8,7" e "100,0" sem "mm" nem "g". A padronizada é em desvios.
- **Padronizar não acerta todos**: 4 pinguins que o KNN acertava passam a errar. Não diga "padronizar sempre melhora cada caso"; diga que o total sobe de 271 para 318.
- **Os 93,0% são dos próprios 342 pinguins**, contados com o deixar-um-de-fora: não é garantia para pinguins de outro lugar ou outro ano.
- **O KNN não treina pesos**: ele guarda os exemplos e mede distâncias na hora. A única coisa "aprendida" na padronização é a média e o desvio.
- Para a tela, o z do pinguim misterioso usa a média e o desvio dos 342 ((50,9 − 43,9) ÷ 5,45 = +1,28; (3.550 − 4.202) ÷ 801 = −0,81). Com os 341 da rodada dá +1,28 e −0,82; os vizinhos e as distâncias de 2 casas são os mesmos.
- O 3º e o 4º vizinho padronizado do pinguim misterioso estão exatamente empatados (Δbico ±0,4 mm, Δmassa ±150 g, d = 0,20); a ordem entre eles não muda nada.
- `resultados.json` traz também os 342 pontos (`pontos_2_medidas`: linha, espécie, bico, massa) para o gráfico das cenas, com as faixas: bico de 32,1 a 59,6 mm, massa de 2.700 a 6.300 g.

## Teoria

Como o KNN de classificação escolhe a resposta, e por que padronizar muda os vizinhos. As notas para o roteiro estão em `teoria.md`; aqui fica de onde sai cada afirmação (os números [n] de `teoria.md` são os itens abaixo). Tudo lido em 20/10/2026. Páginas: as impressas na obra (no relatório de Fix e Hodges, a numeração do relatório). Cópias locais em `pesquisa/`.

### Fontes lidas (texto aberto)

| # | Fonte | O que foi lido | URL |
| --- | --- | --- | --- |
| T1 | Fix, E. & Hodges, J. L., Jr. (fev. 1951). *Discriminatory Analysis. Nonparametric Discrimination: Consistency Properties*. USAF School of Aviation Medicine, Randolph Field (Texas), Project 21-49-004, Report 4, contrato AF41(128)-31 (Universidade da Califórnia, Berkeley). Relatório técnico | capa, introdução, pp. 13 e 20 (lidas como imagem; o OCR é ruim) | DTIC ADA800276: https://apps.dtic.mil/sti/pdfs/ADA800276.pdf (bloqueia download automático) · cópia lida: https://web.archive.org/web/2023id_/https://apps.dtic.mil/sti/pdfs/ADA800276.pdf → `pesquisa/fix_hodges_1951.pdf` |
| T2 | Cover, T. M. & Hart, P. E. (1967). *Nearest Neighbor Pattern Classification*. IEEE Transactions on Information Theory 13(1), 21–27 | inteiro, pp. 21–27 | DOI: https://doi.org/10.1109/TIT.1967.1053964 · PDF lido (página de Cover em Stanford): https://isl.stanford.edu/~cover/papers/transIT/0021cove.pdf → `pesquisa/cover_hart_1967.pdf` |
| T3 | scikit-learn 1.9.1, referência de `KNeighborsClassifier` (documentação oficial) | parâmetros `n_neighbors`, `weights`, `p`, `metric`; aviso sobre empates de distância; `predict` e `predict_proba` | https://scikit-learn.org/stable/modules/generated/sklearn.neighbors.KNeighborsClassifier.html |
| T4 | scikit-learn 1.9.1, Guia do Usuário, *1.6. Nearest Neighbors* | introdução de 1.6 e 1.6.2 (Nearest Neighbors Classification) | https://scikit-learn.org/stable/modules/neighbors.html |
| T5 | scikit-learn 1.9.1, referência de `StandardScaler` | descrição, fórmula, Notes | https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html |
| T6 | scikit-learn 1.9.1, Guia do Usuário, *8.3. Preprocessing data* | 8.3.1 (padronização) e 8.3.3 (Normalization) | https://scikit-learn.org/stable/modules/preprocessing.html |
| T7 | scikit-learn 1.9.1, exemplo *Importance of Feature Scaling* | inteiro | https://scikit-learn.org/stable/auto_examples/preprocessing/plot_scaling_importance.html |
| T8 | scikit-learn 1.9.1, *12. Common pitfalls and recommended practices* | 12.2 Data leakage | https://scikit-learn.org/stable/common_pitfalls.html |
| T9 | Código-fonte do scikit-learn 1.9.1 (o instalado no `.venv`), `sklearn/neighbors/_classification.py`, método `predict` (linhas 245–312) | inteiro, e um teste meu (abaixo, item 9) | https://github.com/scikit-learn/scikit-learn/blob/1.9.1/sklearn/neighbors/_classification.py |
| T10 | James, Witten, Hastie, Tibshirani & Taylor (2023). *An Introduction to Statistical Learning with Applications in Python* (ISLP), PDF gratuito dos autores | 2.2.3 (pp. 36–37), 4.5 (p. 164), 4.7.6 (p. 185), 5.1.2 (pp. 204–205), 5.1.5 (p. 209) | https://www.statlearning.com/ → `pesquisa/islp.pdf` |
| T11 | Hastie, Tibshirani & Friedman, *The Elements of Statistical Learning*, 2ª ed., 12ª impressão (2017), PDF gratuito dos autores | 13.3, pp. 463–465 | https://hastie.su.domains/ElemStatLearn/ → `pesquisa/esl.pdf` |
| T12 | Cornell University, CS4780 (K. Weinberger, 2018), notas da aula 2: *k-nearest neighbors / Curse of Dimensionality* | inteira | https://www.cs.cornell.edu/courses/cs4780/2018fa/lectures/lecturenote02_kNN.html |

### Citadas, mas não lidas (só os metadados, conferidos no Crossref)

- **Fix & Hodges (1989), reimpressão do relatório de 1951.** International Statistical Review 57(3), 238–247. https://doi.org/10.2307/1403797 (JSTOR, pago).
- **Silverman, B. W. & Jones, M. C. (1989).** *E. Fix and J.L. Hodges (1951): An Important Contribution to Nonparametric Discriminant Analysis and Density Estimation: Commentary on Fix and Hodges (1951)*. International Statistical Review 57(3), 233–238. https://doi.org/10.2307/1403796.

### Cada afirmação e a sua fonte

**O que o KNN é**

1. Não constrói modelo: guarda os exemplos de treino. "Neighbors-based classification is a type of instance-based learning or non-generalizing learning: it does not attempt to construct a general internal model, but simply stores instances of the training data." T4 (1.6.2); T4 (1.6: métodos "non-generalizing", que só "lembram" os dados, talvez num índice como Ball Tree ou KD Tree). "These classifiers are memory-based, and require no model to be fit." T11 p. 463.
2. A regra: achar os k exemplos mais perto e ficar com a classe que mais aparece entre eles ("a simple majority vote of the nearest neighbors", T4 1.6.2; "majority vote among the k neighbors", T11 p. 463; "the most common label amongst its k most similar training inputs", T12). A probabilidade de cada classe é a fração dos k vizinhos com aquela classe, e a previsão é a de maior fração. T10 p. 37, eq. 2.12.
3. Padrões do scikit-learn: `n_neighbors=5`, `weights='uniform'` (todos os vizinhos com o mesmo peso), `metric='minkowski'` com `p=2`, "which results in the standard Euclidean distance". T3. Conferido no `.venv` (`get_params()`).
4. Distância euclidiana: d(i) = ‖x(i) − x0‖ (T11 eq. 13.1, p. 465). É a distância de Minkowski com p = 2 (T12; T3). Em duas medidas, √(Δx² + Δy²) (T12, parte "Distances to hyperplanes").
5. A métrica é uma escolha de quem usa. Fix e Hodges: "Specify a metric in the sample space, for example ordinary Euclidean distance" (T1 p. 20). Cover e Hart definem a regra num espaço métrico qualquer, "upon which is defined a metric d" (T2 p. 22). "The distance can, in general, be any metric measure: standard Euclidean distance is the most common choice" (T4 1.6). "The k-nearest neighbor classifier fundamentally relies on a distance metric. The better that metric reflects label similarity, the better the classified will be" (T12).

**De onde vem (história)**

6. A regra de Fix e Hodges (T1 p. 20): escolher k "large but small compared to the sample sizes"; juntar as duas amostras (m exemplos da população F e n da G); entre os k mais perto do caso novo, contar M que vêm de F e N = k − M que vêm de G; usar M/m e N/n no lugar das densidades f(z) e g(z) na regra da razão de verossimilhança, com uma constante c. A ideia de fundo (T1 p. 13): a fração da amostra que cai numa vizinhança pequena estima a probabilidade ali, e a vizinhança deve encolher devagar conforme a amostra cresce. Leitura minha: com m = n e c = 1, a regra é o voto da maioria.
7. "The first formulation of a rule of the nearest neighbor type and primary previous contribution to the analysis of its properties, appears to have been made by Fix and Hodges", que provaram a consistência para k_n → ∞ com k_n/n → 0. T2 p. 22. O relatório é de fevereiro de 1951 (capa de T1) e só saiu em revista em 1989 (metadados acima).
8. A regra 1-NN em Cover e Hart: o vizinho mais próximo x′ é o que minimiza d(x_i, x) (eq. 1); a regra dá a x a categoria dele e ignora as outras n − 1. T2 p. 22.

**Empates**

9. Empate no voto: cada fonte resolve de um jeito.
   - Cover e Hart, para empate na distância do vizinho mais próximo: "the rule may be modified to decide the most popular category among the ties". T2 p. 22, nota 1.
   - "Ties are broken at random." T11 p. 465.
   - "In case of a draw, a good solution is to return the result of k-NN with smaller k." T12.
   - scikit-learn: a documentação não diz em texto. No `predict_proba`, "Classes are ordered by lexicographic order" (T3). O `predict` pega o `argmax` das probabilidades ou a moda do `scipy`, e os dois ficam com a primeira classe em caso de empate (T9, linhas 261–275 e 297–307). Teste meu (`.venv`, 1.9.1): 5 pontos numa reta, com 2 Gentoo como os mais perto, depois 2 Adelie e 1 Chinstrap. Probabilidades [0,4; 0,2; 0,4] e previsão "Adelie", com `algorithm='brute'` e com `'kd_tree'`. Logo, o scikit-learn desempata pela ordem alfabética, não pelo vizinho mais próximo.
10. Empate de distância na k-ésima vaga: "if two neighbors k+1 and k have identical distances but different labels, the result will depend on the ordering of the training data." T3; T4 (1.6.1).

**O k**

11. "The optimal choice of the value k is highly data-dependent: in general a larger k suppresses the effects of noise, but makes the classification boundaries less distinct." T4 1.6.2. No ISLP, com dados simulados: K = 1 dá uma fronteira "overly flexible", com viés baixo e variância muito alta (erro de treino 0); K = 100 dá uma fronteira quase reta; os erros de teste são 0,1695 e 0,1925, contra 0,1363 com K = 10 e 0,1304 do erro de Bayes. T10 p. 37. Cover e Hart: k grande para diminuir a chance de uma decisão que não é a de Bayes, mas k pequeno, em proporção ao número de exemplos, "in order that the points be close enough to x". T2 p. 22. Fix e Hodges: k "large but small compared to the sample sizes". T1 p. 20.
12. Com k = n, o KNN devolve a classe mais comum do conjunto. T12 (Quiz #1 e "Best constant predictor"). Não existe k melhor para todo problema: para qualquer n, há distribuições em que o 1-NN erra menos que qualquer k ≠ 1 (o 1-NN é "admissible"). T2 pp. 22–23 e p. 27.

**O teorema de Cover e Hart**

13. Com amostra grande (n → ∞) e 2 classes: R* ≤ R ≤ 2R*(1 − R*), em que R é o erro do 1-NN e R* o de Bayes, e esses limites são os mais apertados possíveis (eq. 13, p. 24). Com M classes: R* ≤ R ≤ R*(2 − MR*/(M − 1)) (resumo, p. 21; p. 25; conclusões, p. 27). "Thus for any number of categories, the probability of error of the nearest neighbor rule is bounded above by twice the Bayes probability of error. In this sense, it may be said that half the classification information in an infinite sample set is contained in the nearest neighbor." (p. 21). Para o k-NN (2 classes, k ímpar), os limites caem com k na direção de R* (seção VIII, p. 26). T2. O mesmo resultado, "asymptotically", em T11 p. 465 e em T12 ("As n → ∞").
14. O erro de Bayes é a referência impossível de bater: "the limit of excellence beyond which it is not possible to go" (T2 p. 23); "an unattainable gold standard" (T10 p. 36). O 1-NN não precisa de nenhuma hipótese sobre as distribuições ("nonparametric, or distribution free", T2 p. 23).
15. Nesse limite, a métrica não importa: "Since the convergence of the nearest neighbor to x is independent of the metric, the bounds on the risks of the NN rule will be independent of the metric on X." T2 p. 23. O *Elements* explica a hipótese: vale "asymptotically if the dimension of the feature space is fixed and the training data fills up the space in a dense fashion". T11 p. 465. Leitura minha: a escala importa porque a amostra é finita.

**Escala e padronização**

16. A escala muda os vizinhos. "Because the KNN classifier predicts the class of a given test observation by identifying the observations that are nearest to it, the scale of the variables matters." Variáveis em escala grande pesam muito mais na distância. Exemplo imaginado: salário em dólares e idade em anos, em que 1 000 dólares pesam mais que 50 anos. Medir o salário em ienes ou a idade em minutos daria classificações "quite different". O remédio é padronizar: média 0 e desvio 1, com `StandardScaler()`. T10 p. 185. "Typically we first standardize each of the features to have mean zero and variance 1, since it is possible that they are measured in different units." T11 p. 465. No exemplo do scikit-learn (vinho, k = 20), as fronteiras com e sem padronização são "completely different models": a prolina vai de 0 a 1 000 e o matiz de 1 a 10, as distâncias são "mostly impacted by differences in values of proline" e o matiz é "comparatively ignored". Padronizadas, as duas ficam mais ou menos entre −3 e 3 e pesam de forma parecida nos vizinhos. Árvores de decisão "(almost) not affected by scaling". T7.
17. Regra geral do scikit-learn: "If a feature has a variance that is orders of magnitude larger than others, it might dominate the objective function and make the estimator unable to learn from other features correctly as expected." T5; T6 (8.3.1).
18. z = (x − u) / s, em que u é a média e s o desvio-padrão dos exemplos de treino. "We use a biased estimator for the standard deviation, equivalent to numpy.std(x, ddof=0). Note that the choice of ddof is unlikely to affect model performance." T5. Conferido no `.venv`: `scale_` é igual a `np.std(x, ddof=0)`.
19. Padronizar é uma escolha, não uma lei: as fontes dizem "typically" (T11 p. 465) e "a good way to handle this problem" (T10 p. 185). O `StandardScaler` é sensível a valores extremos: "the features may scale differently from each other in the presence of outliers". T5.
20. "Normalization is the process of scaling individual samples to have unit norm" (o `Normalizer` do scikit-learn), que é outra transformação. T6 (8.3.3). Padronizar não muda a forma da distribuição: "In practice we often ignore the shape of the distribution and just transform the data to center it by removing the mean value of each feature, then scale it by dividing non-constant features by their standard deviation." T6 (8.3.1).
21. "Unlike logistic regression, KNN does not tell us which predictors are important: we don't get a table of coefficients." KNN é "completely non-parametric: no assumptions are made about the shape of the decision boundary". T10 p. 164.

**Avaliação**

22. Deixar-um-de-fora (LOOCV): um exemplo fica de fora para validar, o método roda com os outros n − 1, prevê o de fora e repete n vezes (T10 pp. 204–205). Na classificação, CV(n) = (1/n) Σ Err_i, com Err_i = 1 se errou (T10 p. 209, eq. 5.4); acurácia = 1 − CV(n) = acertos ÷ n. Não há sorteio: "performing LOOCV multiple times will always yield the same results: there is no randomness in the training/validation set splits." T10 p. 205.
23. `predict(None)` no scikit-learn: "predictions for all indexed points are returned; in this case, points are not considered their own neighbors." T3.
24. Vazamento: "Data leakage occurs when information that would not be available at prediction time is used when building the model", e o resultado são estimativas otimistas demais, por exemplo na validação cruzada. "The general rule is to never call fit on the test data", inclusive no pré-processamento; use um `Pipeline`. T8 (12.2). No deixar-um-de-fora, o escondido é o dado de teste: a média e o desvio deveriam sair dos outros 341. O `calcular.py` faz assim, e isso não muda nenhuma previsão (`padronizar_por_rodada_vs_de_uma_vez` em `resultados.json`).

**Contas minhas (álgebra, sem fonte)**

25. A média se cancela na distância: z_a − z_b = (x_a − u)/s − (x_b − u)/s = (x_a − x_b)/s. Então a distância padronizada é d = √((Δbico/s_bico)² + (Δmassa/s_massa)²), igual à crua com os pesos 1/s² em cada termo. Somar uma constante a uma medida não muda distância nenhuma; mudar a unidade multiplica os Δ daquela medida e muda os pesos. Com ddof=1, s1 = s0 × √(n/(n − 1)) para as duas medidas (mesmo n): todas as distâncias padronizadas são divididas pelo mesmo número, e os vizinhos e o voto não mudam. Dentro de cada medida, z preserva a ordem dos pinguins (s > 0).

**Para não usar errado**

26. Os 35,19% e 96,30% de acerto em T7 são de PCA com `LogisticRegressionCV` (sem e com padronização), não de KNN. T7.
