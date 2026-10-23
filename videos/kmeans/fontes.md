# Fontes: k-means no Old Faithful

O material bruto (PDFs, páginas e o CSV, que não tem licença aberta explícita) fica em `pesquisa/`, fora do GitHub; o `dados/calcular.py` diz como baixar o CSV e confere o SHA-256.

## Dados

### Dataset

- **Nome e versão usada:** `faithful`, do pacote `datasets` do R (272 erupções do gêiser Old Faithful, Yellowstone, EUA; colunas `eruptions` = duração da erupção em minutos e `waiting` = espera em minutos).
- **Fonte citada pelo R:** W. Härdle (1991). *Smoothing Techniques with Implementation in S*. New York: Springer.
- **Estudo de referência:** Azzalini, A. e Bowman, A. W. (1990). A look at some data on the Old Faithful geyser. *Applied Statistics* (JRSS C) 39(3): 357–365. doi:10.2307/2347385. O R diz que eles usam "uma versão mais completa". Essa versão é a `MASS::geyser`: 299 erupções, de 1 a 15 de agosto de 1985.
- **Arquivo:** https://vincentarelbundock.github.io/Rdatasets/csv/datasets/faithful.csv, baixado em 2026-10-23 (14:02 UTC), 3.260 bytes, 273 linhas (cabeçalho e 272 erupções).
  SHA-256 `5043db1e2c51c8e8fd67e0868c768ae589770cc76ad0ac0c5b7afd1fca31fc57`.
  Conferido valor a valor com o arquivo de dados do próprio R (`src/library/datasets/data/faithful.R`, espelho https://github.com/wch/r-source): são iguais.
- **Documentação:** https://vincentarelbundock.github.io/Rdatasets/doc/datasets/faithful.html (cópia da página de ajuda do R). A versão do R 0.60 tem o mesmo texto: https://svn.r-project.org/R/branches/R-0-60-patches/src/library/base/data/faithful.doc
- **Licença:** não há licença aberta explícita para os dados. O pacote `datasets` é "Part of R" (GPL-2 | GPL-3), uma licença do software. O README do Rdatasets diz que o autor não conseguiu determinar a licença dos dados. Por isso o CSV fica em `videos/kmeans/pesquisa/faithful.csv` e não vai para o GitHub. O `dados/calcular.py` tem no topo a instrução de download e para com `ERRO` se o SHA-256 mudar. Os números vão para a tela com a citação.

#### A coluna `waiting`: espera até a próxima ou desde a anterior?

- A ajuda do R diz "Waiting time to next eruption", ou seja, a espera até a próxima erupção. Ela diz isso desde o R 0.60.
- Na versão de Azzalini & Bowman (`MASS::geyser`), a mesma descrição estava errada. Foi corrigida para "espera antes desta erupção" no MASS 7.3-30 (https://vincentarelbundock.github.io/Rdatasets/doc/MASS/geyser.html) e no pacote `sm` 2.2-5, que é dos próprios autores (https://search.r-project.org/CRAN/refmans/sm/html/geyser.html).
- As 272 erupções do `faithful` **não** são um pedaço das 299 do `geyser`. Nenhuma sequência de 4 esperas seguidas aparece nas duas, e nenhuma de 3 durações. A correção do `geyser` não se aplica direto ao `faithful`.
- Não consegui ler as fontes primárias: Härdle (1991) e o artigo de 1990 estão atrás de paywall (OUP/JSTOR responderam 403).
- **Evidência interna**, calculada no `calcular.py`:
  - No `faithful`, a duração e a espera da mesma linha têm correlação +0,90.
  - No `geyser`, a duração tem correlação +0,89 com a espera depois dela e −0,64 com a espera antes dela.
  - O `faithful` se comporta, então, como "erupção e a espera depois dela", que é o que a ajuda do R diz.
- **Conclusão:** é provável que seja "até a próxima", mas não está fechado com fonte primária. Na fala e na tela, use frases sem direção no tempo ("erupção curta anda junto com espera curta").
- Arquivo de apoio: `MASS::geyser`, de https://vincentarelbundock.github.io/Rdatasets/csv/MASS/geyser.csv, 3.992 bytes, SHA-256 `691381248e0418ccbfc23cc5093e71220313ddb7ffb70e817e27a6dfb900fbcc`.

#### A regra dos guardas (comparação opcional)

- U.S. National Park Service, "Predict Old Faithful" (atividade para escolas): https://www.nps.gov/common/uploads/teachers/lessonplans/YELL_003-PredictOldFaithful.pdf, baixado em 2026-10-23 e salvo como `nps_predict_old_faithful.pdf` (SHA-256 `a71d2c21…059e`).
- A regra: erupção de menos de 3 min, próxima em 68 min; de mais de 3 min, em 94 min.
- É a regra de hoje. As esperas eram mais curtas nos dados do `faithful`. Use só o corte de 3 min como comparação: o k-means acha um corte em 3,2 min.

### A conta

- Script: `videos/kmeans/dados/calcular.py`, rodado da raiz com `.venv/bin/python videos/kmeans/dados/calcular.py`. Leva uns 15 s e uns 160 MB de memória. Usa numpy 2.5.4, pandas e scikit-learn 1.9.1. Escreve `dados/resultados.json`.
- **k-means de Lloyd, feito à mão:**
  - Regra 1: cada erupção vai para o centro mais perto (distância euclidiana nas duas medidas cruas, em minutos, sem padronizar).
  - Regra 2: cada centro vai para a média do seu grupo.
  - O algoritmo para quando a regra 1 não troca ninguém de grupo.
  - A soma dos quadrados é Σ distância² até o centro do grupo, em min². É a `inertia` do scikit-learn.
- **Demonstração:** k = 2, a partir de duas erupções reais, as duas longas: rownames 74 (4,0 min; 71 min) e 203 (4,133 min; 91 min), que são as linhas 75 e 204 do CSV.
  - Rodadas: 191 × 81, depois 65, 23, 3 e 0 trocas.
  - Somas: 37.347 → 27.203 → 12.821 → 9.057 → 8.902 min².
  - Final: centros (2,1; 54,8) e (4,3; 80,3), com 100 e 172 erupções.
- **Conferências:**
  - `KMeans(2, n_init=10, random_state=0)` dá a mesma divisão, com inertia 8.901,77. Do mesmo começo (`init=` as 2 erupções), o scikit-learn também para com `n_iter_ = 5`.
  - Todos os 36.840 pares de erupções diferentes, usados como começo, chegam na mesma divisão.
  - "Por que a média" foi conferido de dois jeitos: força bruta (deslocar o centro d minutos soma n·d²) e uma grade de 861 centros em volta da média.
  - Cotovelo: `KMeans(k, n_init=10, random_state=0)` para k = 1 a 6.
  - Ótimo local: 100 começos sorteados (`numpy.random.default_rng(0)`), para k = 2 e k = 3.
  - Previsão: deixar-um-de-fora com o k-means refeito nas 271, mais um k-means só na duração.
  - Padronizado: `StandardScaler` (ddof=0) e `KMeans(2, n_init=10, random_state=0)`. Com isso, 4 erupções trocam de grupo.

### Cuidados

1. A direção da espera não está fechada com fonte primária (ver acima). Fale sem direção no tempo.
2. Não diga que as 272 são as medições de agosto de 1985 do artigo de Azzalini & Bowman. A data das 272 não está documentada, só que são anteriores a 1991.
3. As durações foram anotadas em segundos e arredondadas, e múltiplos de 5 s aparecem demais (aviso da ajuda do R). Mostre no máximo 1 casa.
4. Sem padronizar, a espera é 99,3% da soma dos quadrados com k = 1, então o k-means separa quase só pela espera. Padronizando, só 4 das 272 trocam de grupo.
5. A espera entra no agrupamento, então prever a espera pelo grupo é em parte circular. O deixar-um-de-fora (4,8 min) e o k-means só na duração dão o mesmo erro.
6. Cotovelo: em porcentagem, as quedas depois de k = 2 ficam entre 28,1% e 43,3%, e de 3 para 4 cai mais, em %, que de 2 para 3. O cotovelo aparece na curva em min² (41.538 contra 3.713). É uma regra de bolso.
7. Ótimo local: com k = 2 não há nenhum. O exemplo é com k = 3: dos 100 começos, saem 10 finais diferentes, e só 8 chegam na melhor soma (5.189).
8. Empates de distância: nenhum na demonstração. Nas partidas sorteadas, os poucos empates vão para o centro de número menor (fica registrado no JSON).

## Teoria

Seção Teoria, para o diretor juntar no `fontes.md`. Os códigos [T1] a [T8] são os que o `teoria.md` usa. O material bruto está nesta pasta (`pesquisa/`), com o nome indicado em cada obra. Lido em 23/10/2026.

### Obras lidas

**[T1] Lloyd, S. P. (1982).** "Least squares quantization in PCM". *IEEE Transactions on Information Theory* 28(2), 129-137. Rascunho circulado na Bell Labs, registrado em 31/07/1957.
- URL lida: https://www.stat.cmu.edu/~rnugent/PCMI2016/papers/LloydKMeans.pdf (o original da IEEE é pago).
- Arquivos: `lloyd_1982.pdf`, `lloyd_1982_raw.txt`, `lloyd_1982.txt`.
- Lido: resumo, §I-VI (p. 129-132), Method I, nota de rodapé da p. 129 e "Author's Note 1981" (p. 136). O apêndice B (exemplos de mínimos locais), só por cima.

**[T2] MacQueen, J. (1967).** "Some methods for classification and analysis of multivariate observations". *Proceedings of the Fifth Berkeley Symposium on Mathematical Statistics and Probability*, vol. 1, 281-297. University of California Press.
- Página no Project Euclid (bloqueada para download direto): https://projecteuclid.org/euclid.bsmsp/1200512992
- URL lida (cópia do mesmo PDF no Internet Archive): http://web.archive.org/web/2017id_/http://projecteuclid.org/download/pdf_1/euclid.bsmsp/1200512992
- Arquivos: `macqueen_1967.pdf`, `macqueen_1967.txt`.
- Lido: §1 (p. 281-282), §2.1 (p. 282-283), §2.3 (p. 287-288), §3.1 (p. 288-289), §3.6 (p. 294) e a nota acrescentada na prova (p. 296). As demonstrações de §2.2, não.

**[T3] James, G., Witten, D., Hastie, T., Tibshirani, R. e Taylor, J. (2023).** *An Introduction to Statistical Learning with Applications in Python* (*ISLP*). Springer, 1ª impressão, 05/07/2023.
- URL: https://www.statlearning.com/ (PDF grátis). O PDF já estava baixado em `videos/knn/pesquisa/islp.pdf`; o trecho usado foi copiado para `islp_12_4_1.txt`.
- Lido: §12.4.1 "K-Means Clustering" (p. 521-525, com o Algoritmo 12.2 e as eqs. 12.15-12.18) e o começo de §12.4.3 "Practical Issues in Clustering" (p. 532-533).
- Não é o *ISLR* 2ª ed. (2021, versão em R, sem Taylor) que a pauta cita: a seção 12.4.1 é a mesma nos dois, mas não abri o *ISLR*.

**[T4] Hastie, T., Tibshirani, R. e Friedman, J. (2009).** *The Elements of Statistical Learning*, 2ª ed., 12ª impressão corrigida (13/01/2017). Springer.
- URL: https://hastie.su.domains/ElemStatLearn/ (PDF grátis). Já estava em `videos/knn/pesquisa/esl.pdf`; o trecho usado está em `esl_14_3_kmeans.txt`.
- Lido: §14.3.6 "K-means" (p. 509-510, eqs. 14.31-14.34 e Algoritmo 14.1), o exemplo de microarranjos (p. 513) e §14.3.11 "Practical Issues" (p. 518-519).

**[T5] Arthur, D. e Vassilvitskii, S. (2007).** "k-means++: The advantages of careful seeding". *Proceedings of the 18th Annual ACM-SIAM Symposium on Discrete Algorithms (SODA)*, 1027-1035.
- URL lida: https://www.cs.columbia.edu/~verma/classes/uml/ref/clustering_kmean_plusplus_arthur_vassilvitskii.pdf
- O PDF é a versão técnica de 2006 (11 p., criado em 07/06/2006); as páginas citadas são dele, não do SODA. Não conferi a paginação do SODA.
- Arquivos: `kmeanspp_2007.pdf`, `kmeanspp_2007_raw.txt`, `kmeanspp_2007.txt`.
- Lido: resumo, §1 (p. 1), §2 (p. 2-3, com o Lema 2.1), o enunciado do Teorema 3.1 e o Lema 3.2 (p. 3), §6 (experimentos, p. 9-10). As demonstrações de §3-5, não.

**[T6] scikit-learn 1.9.1, documentação.**
- API: https://scikit-learn.org/stable/modules/generated/sklearn.cluster.KMeans.html (`skl_kmeans.html`, `skl_kmeans.txt`).
- Guia do usuário, §2.3.2 "K-means": https://scikit-learn.org/stable/modules/clustering.html#k-means (`skl_clustering.html`, `skl_clustering.txt`).
- Lido: a assinatura e os parâmetros `n_clusters`, `init`, `n_init`, `max_iter`, `tol`, `algorithm`; o atributo `inertia_`; as Notas. No guia, §2.3.2 inteira até "Low-level parallelism".

**[T7] National Park Service, Yellowstone.**
- "Current Geyser Activity": https://www.nps.gov/yell/learn/nature/geyseractivity.htm (página atualizada em 18/04/2025; tabela de comportamento atualizada em novembro de 2020). Arquivos `nps_geyser_activity.*`.
- "Predict Old Faithful" (atividade escolar, 3º ao 5º ano, atualizada em 16/08/2018): https://www.nps.gov/teachers/classrooms/predict-old-faithful.htm e o PDF https://www.nps.gov/common/uploads/teachers/lessonplans/YELL_003-PredictOldFaithful.pdf. Arquivos `nps_predict_old_faithful.html`, `nps_teachers_page.txt`, `nps_yell_003_predict.*`.
- Centro de Visitantes Virtual do Old Faithful, "Predicting Geysers" (sem data): https://home.nps.gov/features/yell/ofvec/exhibits/eruption/prediction/ (índice) e as páginas `predict7.htm` (Old Faithful) e `predict8.htm` (como se prevê). Arquivos `nps_ofvec_*`.
- Lido: as três páginas inteiras, nas partes do Old Faithful.

**[T8] Documentação dos dados.**
- R, `datasets::faithful` (R 4.6.0): https://stat.ethz.ch/R-manual/R-devel/library/datasets/html/faithful.html (`r_faithful.html`, `r_faithful.txt`).
- `MASS::geyser` e `sm::geyser` (a versão de Azzalini e Bowman): `rdatasets_geyser_doc.html` e `sm_geyser_doc.html`, baixados pelo agente de dados nesta pasta.
- Lido: as três páginas inteiras.

### Citadas sem ler

Aparecem no `teoria.md` só como contexto, sem sustentar o mecanismo:

- Azzalini, A. e Bowman, A. W. (1990). "A look at some data on the Old Faithful geyser". *Applied Statistics* 39(3), 357-365. doi:10.2307/2347385. JSTOR e OUP pediram JavaScript ou bloquearam; citado pela doc do R [T8].
- Härdle, W. (1991). *Smoothing Techniques: With Implementation in S*. Springer. Fonte do `faithful` segundo o R [T8].
- Forgy, E. (1965) e Jennrich, R. (comunicação de 1963): a versão em lote, citada por MacQueen [T2 p. 282, 294].
- Arthur, D. e Vassilvitskii, S. (2006). "How slow is the k-means method?" SoCG 2006. Pior caso, citado pelo scikit-learn [T6, Notas].
- Thorndike, R. L. (1953). "Who belongs in the family?" *Psychometrika* 18, 267-276. Atribuição comum do método do cotovelo; não conferi nem a atribuição.
- James, G., Witten, D., Hastie, T. e Tibshirani, R. (2021). *ISLR*, 2ª ed. A pauta cita; usei o *ISLP* [T3].

### Cada afirmação do `teoria.md`

**Em uma frase e passo 1**
- Divisão em k grupos que deixa mínima a variação dentro dos grupos; Algoritmo 12.2: [T3 p. 521-523]. Objetivo φ = soma das distâncias ao quadrado até o centro mais perto: [T5 §2, p. 2]. A `inertia` é "sum of squared distances of samples to their closest cluster center": [T6 KMeans, `inertia_`; Guia §2.3.2, fórmula].
- "Quase Kⁿ jeitos de dividir": [T3 p. 523]. "NP-hard": [T5 §1, p. 1].
- Sem rótulo (aprendizado não supervisionado): [T3 cap. 12, p. 521-522, Fig. 12.7: "cluster labels were not used"].

**Passo 2 (regra 1)**
- O melhor conjunto para cada quantum é o dos valores mais perto dele, com fronteiras no ponto médio entre quanta vizinhos (eqs. 15-17): [T1 §V, p. 131]. Atribuir cada observação à média mais perto (eq. 14.34) e o mosaico de Voronoi: [T4 p. 510]. Guia: "assigns each sample to its nearest centroid": [T6 Guia §2.3.2].
- A regra não sobe a soma: Lloyd, "este passo não aumenta o ruído", N(p⁽²⁾) ≤ N(p⁽¹⁾): [T1 §VI, p. 132]; "Each of steps 1 and 2 reduces the value of the criterion": [T4 p. 510].

**Passo 3 (regra 2)**
- O centro é o vetor das médias de cada medida no grupo; o nome vem daí: [T3 p. 523]. MacQueen: "the k-means are, in fact, the means of the groups they represent (hence the term k-means)": [T2 p. 283].
- Os centros "não são, em geral, pontos de X": [T6 Guia §2.3.2].

**Passo 4 (por que a média)**
- Identidade soma(z) − soma(c(S)) = |S|·|c(S) − z|²: [T5 Lema 2.1, §2.1, p. 2].
- O "momento de inércia" é mínimo quando cada quantum é o centro de massa do seu conjunto (eq. 14): [T1 §IV, p. 130].
- A média é o argmin da soma dos quadrados (eq. 14.32): [T4 p. 510]. "The mean, of course, minimizes the squared error": [T2 p. 282].
- A mediana para a soma das distâncias simples: resultado clássico, não está nas obras lidas; é nota de cuidado, não vai para a tela.

**Passo 5 (por que para)**
- φ decresce sempre, nenhuma configuração se repete, há só kⁿ divisões, "the process will always terminate": [T5 §1, p. 1].
- Empates "may be broken arbitrarily, as long as the method is consistent": [T5 §2.1, p. 2].
- O objetivo "will never increase", até não mudar mais: [T3 p. 523].
- Forgy e Jennrich: variâncias decrescentes, "will converge in a finite number of steps": [T2 §3.6, p. 294].
- Lloyd, Method I: alternar as condições (14) e (17); N(p⁽ᵐ⁾) é decrescente: [T1 §VI, p. 131-132].
- `tol` (diferença entre centros de duas rodadas) e `max_iter=300`; o guia diz que a parada é pelo movimento dos centros, não pela queda do objetivo: [T6 KMeans; Guia §2.3.2].

**Passo 6 (ótimo local)**
- Pontos estacionários podem ser pontos de sela, e pode haver vários mínimos locais: [T1 §V, p. 131].
- "In general, the k-means procedure will not converge to an optimal partition": [T2 p. 282]; exemplo do retângulo: [T2 §2.3, p. 288]; o resultado "will depend on the initial partition": [T2 §3.6, p. 294].
- "Local rather than a global optimum"; 6 partidas, 3 ótimos locais: [T3 p. 523-525, Fig. 12.9].
- A semeadura ao acaso "will inevitably merge clusters together, and the algorithm will never be able to split them apart": [T5 §6.3, p. 9].
- "Given enough time, K-means will always converge, however this may be to a local minimum": [T6 Guia §2.3.2].

**Passo 7 (vários começos e k-means++)**
- Várias partidas e fica-se com a de menor objetivo: [T3 p. 524]; [T4 p. 510]; MacQueen sugere "repeated runs with different initial starting points": [T2 p. 294]. `n_init`: "the best output of n_init consecutive runs in terms of inertia": [T6 KMeans].
- Ponderação D² e Teorema 1.1/3.1, E[φ] ≤ 8(ln k + 2)·φ_ótimo: [T5 §1-3, p. 1-3]. Mais rápido e melhor nos testes: [T5 §6.3, p. 9].
- Padrões do scikit-learn 1.9.1: `init='k-means++'` ("greedy k-means++"), `n_init='auto'` (1 com k-means++ ou centros dados; 10 com `'random'`), mudança na versão 1.4: [T6 KMeans].

**Passo 8 (escolher k)**
- Escolher K "is far from simple": [T3 p. 524]. Decisões com "strong impact", "no single right answer"; "Any time clustering is performed on a data set we will find clusters": [T3 p. 533].
- W_K diminui com K; procura-se a "kink", abordagem "somewhat heuristic"; estatística gap: [T4 p. 518-519]. Exemplo sem dobra clara ("no clear indication"): [T4 p. 513].
- O scikit-learn aponta a análise de silhueta para escolher `n_clusters`: [T6 KMeans, `n_clusters`].

**Passo 9 (peso da espera)**
- "Should the observations or features first be standardized?" está entre as decisões de grande impacto: [T3 p. 533]. Distância euclidiana ponderada = redefinir as medidas: [T4 p. 509].
- Os números (desvios, 99%, 67,5 min, 5 discordâncias): conferências minhas, abaixo.

**Gancho e NPS**
- Regra dos guardas, menos de 3 min dá 68 min e mais de 3 dá 94; duração a meio minuto; "any prediction may not prove to be exactly right": [T7, "Predict Old Faithful"].
- "94 or 68 min (+/- 10 minutes)", 1,5-5 min, 106-184 pés: [T7, "Current Geyser Activity", tabela de nov. 2020].
- 1,5-5 min, 90-184 pés, intervalo de 35 a 120 min, média de 92, cerca de 90% das previsões em ± 10 min; nunca foi de hora em hora; o intervalo cresceu (terremoto de Hebgen Lake, 1959): [T7, `predict7.htm`].
- Relação direta entre duração e espera seguinte; erupção curta gasta menos água e calor; só se prevê uma erupção à frente; como se cronometra: [T7, `predict8.htm`].

**Ressalvas**
- `faithful`: 272 observações, fonte "W. Härdle", "many versions", durações "heavily rounded", Azzalini e Bowman "use a more complete version": [T8, R]. `geyser`: 1 a 15/08/1985, 299 observações, espera corrigida para "antes desta erupção" (MASS 7.3-30): [T8, MASS e sm].
- Objetivo do *ISLP* = 2 × soma até a média (eq. 12.18): [T3 p. 523]. Peso Nₖ na eq. 14.31: [T4 p. 509].
- Lloyd: apresentado em parte em 10-13/09/1957 (rodapé, p. 129); "nearly a verbatim reproduction of a draft manuscript", registro de 31/07/1957 (p. 136); quantização de uma variável (tensão): [T1].
- MacQueen: k-means sequencial [T2 p. 283]; Forgy e Jennrich, comunicado em 1963 [T2 p. 282]; Wallace e Ball usaram o método de forma independente [T2 p. 296].
- "K-means is often referred to as Lloyd's algorithm": [T6 Guia §2.3.2].
- Grupo de massa nula: Lloyd o junta a outro (p. 130-131) e pede "modificações apropriadas" no Method I (p. 131-132): [T1].

### Conferências minhas (não são fonte)

Contas feitas em 23/10/2026 sobre `pesquisa/faithful.csv` (272 linhas, baixado pelo agente de dados), com numpy, só para checar o texto. Quem manda nos números do vídeo é o `dados/resultados.json`.

- Identidade do passo 4: num grupo, com o centro 5 min acima da média na espera, os dois lados deram o mesmo valor.
- Lloyd com k = 2 a partir das duas erupções de menor espera: 5 rodadas até repetir; centros finais (2,09; 54,75) e (4,30; 80,28); soma 8.901,8 min²; grupos de 100 e 172. Pelo melhor de 30 começos ao acaso, a soma mínima para k = 1 a 6: 50.440,2; 8.901,8; 5.188,5; 2.941,7; 2.028,4; 1.473,1 (dobra em k = 2).
- Espalhamento (desvio com ddof = 0): duração 1,139 min, espera 13,57 min; variâncias 1,30 e 184,1 min² (razão de uns 142).
- No resultado final, a parte da espera na soma é 8.855,8 de 8.901,8 (99,5%). A fronteira passa por espera 67,66 (duração 1,6), 67,53 (3,0) e 67,35 min (5,1).
- Contra a regra dos 3 min do NPS: 5 erupções discordam, (3,367; 66), (3,833; 64), (3,5; 66), (3,417; 64) e (2,383; 71).
- Pareamento da espera: correlação duração × espera na mesma linha 0,901; duração(i) × espera(i+1) −0,482. No `geyser` (espera "antes"), mesma linha −0,645 e duração(i) × espera(i+1) 0,888.
- Divisões de 272 pontos em 2 grupos não vazios: S(272, 2) = 2²⁷¹ − 1 ≈ 3,8 × 10⁸¹.
