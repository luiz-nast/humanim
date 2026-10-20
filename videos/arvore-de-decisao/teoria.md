# Teoria: como a árvore escolhe a pergunta

Notas para quem escreve o roteiro. As fontes de cada afirmação estão em `fontes.md`, seção Teoria (os números entre colchetes, como [9], são os itens de lá). Os números do exemplo saem de `dados/resultados.json` (os do roteiro) e de `dados/conferir_teoria.json` (os que só conferem a teoria).

**Em uma frase:** a árvore mede a mistura de cada grupo com a impureza de Gini, testa todas as perguntas do tipo "coluna ≤ limiar?", fica com a que deixa os dois grupos menos misturados, na média ponderada pelo tamanho, e repete isso em cada grupo, sem olhar adiante.

## O mecanismo em 10 passos

1. **Todo mundo começa junto.** O topo da árvore (a raiz) tem todos os exemplos de treino. Aqui são 30 000 clientes, 6 636 com calote (22,12%). Se a árvore parasse aqui, diria "paga" para todo mundo (a classe da maioria) e erraria 22,12%. [5, 19]

2. **Medir a mistura: impureza de Gini.**
   Gini = 1 − (p1² + p2²), em que p1 e p2 são as proporções de cada classe no grupo. É o mesmo que somar p × (1 − p) de cada classe; com duas classes, Gini = 2 × p × (1 − p). [1, 2]
   - **Intuição certa:** pegue um cliente do grupo e dê a ele um rótulo sorteado na proporção do grupo (78% "paga", 22% "calote"). O Gini é a chance de esse sorteio errar. Dá no mesmo: a chance de dois clientes sorteados serem de classes diferentes. [4] Conferido: o sorteio erra 0,3440 em média; o Gini é 0,3445.
   - **Escala:** 0 = grupo puro, só uma classe. Com duas classes, o máximo é 0,5 (metade de cada). Não vai até 1. [2, 3]
   - **Na raiz:** 1 − (0,78² + 0,22²) = 1 − (0,61 + 0,05) = 0,34.

3. **Uma pergunta é uma coluna e um limiar.** Sempre de sim ou não: "coluna ≤ limiar?". Os limiares testados são os pontos médios entre valores vizinhos que existem nos dados. A vencedora, "2 meses ou mais de atraso em setembro?", é para o scikit-learn `PAY_0 <= 1.5` (o meio entre os códigos 1 e 2, com os lados trocados). [8, 11]

4. **Cada pergunta parte o grupo em dois, e cada lado tem o seu Gini.**
   - Sim: 3 130 clientes, 69,6% de calote, Gini 1 − (0,30² + 0,70²) = 0,42.
   - Não: 26 870 clientes, 16,6% de calote, Gini 1 − (0,83² + 0,17²) = 0,28.

5. **Os dois lados se juntam numa média ponderada pelo tamanho.**
   Gini dos filhos = (tamanho do sim ÷ total) × Gini do sim + (tamanho do não ÷ total) × Gini do não = 0,10 × 0,42 + 0,90 × 0,28 = 0,29. [9]
   O peso é o que faz a conta funcionar. A média simples, (0,42 + 0,28) ÷ 2 = 0,35, sai maior que os 0,34 da raiz, como se a pergunta piorasse. O lado "sim" é mais misturado, mas tem só 10% dos clientes.

6. **Ganho = Gini do pai − Gini ponderado dos filhos.** 0,34 − 0,29 = 0,05, ou 15,2% da mistura inicial. O nome certo é **redução de impureza**; "ganho de informação" é o nome quando a régua é a entropia (passo extra, abaixo). [10, 34]
   Com o Gini, o ganho nunca é negativo: nenhuma pergunta piora a média ponderada. Das 174 581 perguntas da raiz, todas têm ganho positivo. Até uma pergunta sem sentido sobre o número de cadastro do cliente (que nem está entre as 23 colunas), "cadastro ≤ 18 455?", teria ganho de 0,0003. [7, 21]

7. **A árvore testa todas e fica com o maior ganho: é a busca gulosa.** Na raiz ela calcula o ganho de 174 581 perguntas (23 colunas × todos os limiares) e escolhe a melhor naquele momento. Não olha adiante e não testa árvores inteiras. Por isso não há garantia de que o resultado seja a melhor árvore possível: achar a ótima é um problema NP-completo (não se conhece jeito rápido de garantir a ótima em geral), e por isso os algoritmos usados na prática são gulosos. [11–13]
   Exemplo real: buscando em 11 colunas, a melhor árvore de 2 níveis (menor Gini nas folhas: 0,28082 contra 0,28101 da gulosa) começa por outra pergunta, "algum atraso em setembro?". A diferença é mínima, mas existe.

8. **Recursão: o mesmo passo, em cada lado.** Cada grupo novo vira um "pai" e passa pelos passos 2 a 7, só com os clientes que caíram nele. A mesma coluna pode voltar, com outro limiar. Na árvore de 2 níveis do scikit-learn, o lado "não" pergunta sobre agosto (`PAY_2 <= 1.5`) e o lado "sim" sobre julho (`PAY_3 <= -0.5`). [14]

9. **Quando parar, e como a árvore responde.** Um nó vira folha quando está puro, quando tem exemplos de menos (`min_samples_split`, padrão 2; `min_samples_leaf`, padrão 1), quando chega à profundidade máxima (`max_depth`, padrão sem limite) ou quando o ganho fica abaixo de um mínimo (`min_impurity_decrease`, padrão 0). Com os padrões do scikit-learn, a árvore só para quando as folhas estão puras ou não há mais como separar. [15, 16]
   Para um cliente novo, a árvore desce pergunta por pergunta até uma folha e responde a classe da maioria ali, com a proporção da folha como probabilidade. [19]

10. **Por que a árvore funda decora (overfitting).** No treino, toda pergunta a mais baixa um pouco o Gini, inclusive as que só pegam coincidências daquela amostra. Quanto menor o grupo, mais fácil a coincidência: com poucos clientes, quase qualquer corte "separa" alguma coisa. [20, 21]
    - Sem limite: 3 251 folhas, uns 6,5 clientes de treino por folha, profundidade 40. Acerta 99,95% no treino e só 72,3% no teste, menos que o chute "todo mundo paga" (77,9%).
    - Os 11 erros que sobram no treino são clientes com ficha idêntica à de outro e rótulo diferente: nenhuma pergunta separa os dois. [16]
    - Com profundidade 2 (4 folhas): 82,1% no treino e 81,8% no teste, quase igual.
    - O remédio é limitar o tamanho (`max_depth`, `min_samples_leaf`) ou fazer como o CART: crescer grande e depois **podar**, escolhendo o tamanho pela validação cruzada (poda de custo-complexidade, `ccp_alpha` no scikit-learn). Só "parar quando o ganho ficar pequeno" é míope, porque uma pergunta fraca pode abrir caminho para uma ótima logo abaixo. [17, 18]

## A outra régua: entropia e ganho de informação (ID3 e C4.5, Quinlan)

- Entropia = −(p1 × log2 p1 + p2 × log2 p2), em bits. Vale 0 num grupo puro e 1 bit em meio a meio (com duas classes). Na raiz: 0,76 bits. [24]
- Ganho de informação = entropia do pai − média ponderada das entropias dos filhos. É a mesma receita do Gini, só com outra régua. É o critério do ID3, no artigo de Quinlan de 1986. [25]
- Na prática quase não muda nada: aqui a entropia escolhe a mesma primeira pergunta (ganho de 0,089 bits), e as 5 melhores perguntas da raiz são as mesmas, na mesma ordem. As árvores de 3 níveis já diferem um pouco, e o acerto no teste fica a no máximo 0,12 ponto até a profundidade 6. [29]
- A diferença que importa é de estrutura. O ID3 abre um ramo para cada valor de um atributo categórico, e aí o ganho de informação favorece atributos com muitos valores. No extremo, um ramo por cliente (o número de cadastro) zera a mistura e teria o ganho máximo, sendo inútil. A correção de Quinlan é a **razão de ganho** (ganho ÷ a informação da própria divisão), que o C4.5 usa. O CART e o scikit-learn sempre dividem em dois. [26, 27]
- O padrão do scikit-learn e do `rpart` (a versão do CART no R) é o Gini. [33]

## Armadilhas: pode simplificar assim, mas não errar assim

**Simplificação aceitável**

- "Mistura" ou "bagunça" no lugar de impureza, desde que o nome certo venha depois ("isso tem nome: impureza de Gini").
- "A chance de errar se você chutar o rótulo na proporção do grupo": é a definição exata, não uma aproximação.
- "Ela testa todas as perguntas": vale para o scikit-learn com o padrão `splitter='best'`, desde que fique claro que são as perguntas do tipo "coluna ≤ limiar", não qualquer pergunta imaginável.
- "2 meses ou mais de atraso" para `PAY_0 <= 1.5`: os códigos são inteiros, então é a mesma pergunta.
- Mostrar os pesos como 0,10 e 0,90 e a conta com 2 casas: ela fecha (bloco `para_tela` de `resultados.json`).

**ERRADO, não diga**

1. **"O Gini é a chance de a árvore errar."** A árvore rotula pela maioria: na raiz ela erraria 22,1%, e o Gini é 0,34. São medidas diferentes. [5]
2. **"O Gini vai de 0 a 1."** Com duas classes, o máximo é 0,5. Em geral, o máximo é 1 − 1/(número de classes). [2]
3. **"É o mesmo Gini da desigualdade de renda."** Tem o mesmo sobrenome, mas é outra medida: aquele usa a curva de Lorenz e vai de 0 a 100. [6]
4. **"A árvore escolhe a pergunta que mais acerta."** Ela escolhe a que mais reduz a impureza. Uma pergunta pode baixar o Gini sem mudar nenhuma previsão: no lado "não" da raiz, `PAY_2 <= 1.5` separa grupos com 14,3% e 41,6% de calote, os dois continuam com maioria "paga", os acertos ficam iguais (22 411) e mesmo assim o Gini cai de 0,277 para 0,265. Se a régua fosse a taxa de acerto, 174 533 das 174 581 perguntas da raiz teriam ganho zero, e a árvore não teria como comparar quase nenhuma. [30, 31]
5. **"Faz a média dos dois lados."** Sem pesos, a conta dá errado (0,35, acima do pai). A média é ponderada pelo número de clientes de cada lado. [9]
6. **"A árvore acha a melhor árvore" ou "testa todas as árvores possíveis".** Ela é gulosa: a melhor pergunta em cada nó, um nó por vez. A ótima é NP-completa. [12, 13]
7. **"Ela descobre qual é a coluna mais importante."** Ela escolhe um par coluna e limiar. A mesma coluna com o limiar um degrau abaixo ("algum atraso?") perde: ganho de 0,0467 contra 0,0524. [8]
8. **"O CART usa entropia" ou "o ID3 usa Gini".** É o contrário: o ID3 usa ganho de informação (entropia), e o CART e o scikit-learn usam Gini por padrão. Também não chame a redução de Gini de "ganho de informação", mesmo que a documentação do scikit-learn escorregue nisso. [25, 33, 34]
9. **"Quanto mais funda, melhor" ou "acertou 100% no treino, então é ótima".** Sem limite: 99,95% no treino e 72,3% no teste, abaixo do chute. [20]
10. **"Ela para quando a pergunta piora as coisas."** Com o Gini, nenhuma pergunta piora a média ponderada. A parada vem de limites (profundidade, tamanho mínimo, ganho mínimo) ou da poda. [7, 15]
11. **"Cada coluna só pode ser usada uma vez."** No CART e no scikit-learn a mesma coluna volta com outro limiar. A regra de "uma vez por caminho" é do ID3, para atributos categóricos. [36]
12. **"A árvore encontrou a verdade sobre quem dá calote."** A árvore é instável: outra amostra, ou até outra semente em caso de empate, dá outras perguntas. A árvore sem limite vai de 71,8% a 72,3% no teste só trocando o `random_state` (6 sementes testadas). [23]
13. **"O ID3 foi inventado em 1986."** O artigo de 1986 é a descrição de referência; o próprio texto põe o ID3 em 1979. Diga "Quinlan, nos anos 1980". [32]

## Ressalvas de fonte

- Não li o livro do CART (Breiman et al., 1984, pago). O que se diz dele aqui vem do scikit-learn, do *Elements of Statistical Learning*, da vinheta do `rpart` e da revisão de Loh (2014), que o descrevem.
- O NP-completo vem da documentação do scikit-learn e das notas de Cornell. O artigo original (Hyafil e Rivest, 1976) só teve os metadados conferidos.
