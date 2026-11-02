# Detector de Conflitos de Separação em Espaço Aéreo

Projeto da disciplina de Projeto e Análise de Algoritmos. Implementa o algoritmo de **Par de Pontos Mais Próximos** (divisão e conquista, O(n log n)) e uma variação que lista **todos** os pares de aeronaves abaixo de uma distância mínima de segurança, aplicados a um cenário de gerenciamento de tráfego aéreo em um plano 2D.

## Objetivo

1. Implementar corretamente o Par de Pontos Mais Próximos por divisão e conquista.
2. Adaptar o algoritmo para detectar todos os pares em violação de separação, e não apenas o mais próximo.
3. Comparar empiricamente as duas abordagens com a força bruta (O(n²)), identificando a partir de qual quantidade de aeronaves a divisão e conquista compensa.
4. Medir o efeito da densidade de aeronaves no custo da variação que coleta todos os pares.

O cenário de aviação é o contexto de aplicação. O foco do projeto é o algoritmo, os testes e a medição de desempenho.

## O problema

Dado um conjunto de `n` aeronaves, cada uma com posição `(x, y)` em milhas náuticas (NM), identificar quais pares estão a **menos de 5 NM** um do outro, valor usado como referência de separação horizontal mínima.

Comparar todos os pares resolve o problema em O(n²). Com muitas aeronaves, esse custo cresce rápido. A divisão e conquista reduz a busca para a ordem de O(n log n).

## Algoritmos

### `par_mais_proximo(pontos)` (`par_mais_proximo.py`)

Divisão e conquista clássica:

1. Ordena os pontos por `x`, uma única vez.
2. Divide o conjunto ao meio e resolve cada metade recursivamente. Cada chamada devolve também seus pontos ordenados por `y`, obtidos por intercalação (merge), sem reordenar a cada nível.
3. Seja `d` o menor valor entre as duas metades. Só pontos a menos de `d` da linha divisória podem formar um par melhor entre as metades. Na faixa (strip), ordenada por `y`, cada ponto é comparado apenas com os seguintes cuja diferença em `y` é menor que `d` (no máximo 7 comparações por ponto).
4. Devolve o par de menor distância.

Recorrência: `T(n) = 2T(n/2) + O(n)`, que resulta em **O(n log n)**.

### `pares_em_risco(pontos, d_seguro)` (`pares_em_risco.py`)

Variação do algoritmo anterior. Em vez de deixar o limiar da faixa encolher conforme a recursão avança, a faixa usa o valor fixo `d_seguro`. Assim, a etapa de combinação coleta **todos** os pares com distância menor que `d_seguro` que cruzam a linha divisória. Pares dentro de uma mesma metade já foram coletados na recursão, então a combinação conta apenas pares com um ponto de cada lado, e cada par é registrado uma única vez.

Custo: O(n log n) mais as comparações feitas dentro da faixa. Com poucos conflitos, fica próximo de O(n log n). Com aeronaves muito amontoadas, a faixa fica cheia e o número de comparações cresce, podendo se aproximar de O(n²). Esse efeito é medido no benchmark.

### `forca_bruta(pontos, d_seguro)` (`forca_bruta.py`)

Compara todos os pares em O(n²). Serve de referência de correção nos testes e de linha de base no benchmark. O módulo também traz `par_mais_proximo_forca_bruta(pontos)`, a versão de referência do par mais próximo.

### Convenções comuns

- `pontos` é uma sequência de tuplas `(x, y)`.
- Os pares são devolvidos como **índices** `(i, j)` da lista original, com `i < j`, o que permite identificar a aeronave mesmo com posições repetidas.
- `par_mais_proximo` devolve `(distancia, (i, j))` e levanta `ValueError` com menos de 2 pontos.
- `pares_em_risco` e `forca_bruta` devolvem uma lista de `(i, j, distancia)` ordenada por `(i, j)`.
- "Abaixo da distância segura" significa distância **estritamente menor** que `d_seguro`. Se `d_seguro <= 0`, o resultado é uma lista vazia.

Exemplo:

```python
from par_mais_proximo import par_mais_proximo
from pares_em_risco import pares_em_risco

aeronaves = [(0, 0), (3, 4), (20, 20), (21, 20)]

par_mais_proximo(aeronaves)     # (1.0, (2, 3))
pares_em_risco(aeronaves, 5.5)  # [(0, 1, 5.0), (2, 3, 1.0)]
```

## Estrutura do repositório

```
.
├── par_mais_proximo.py     # par mais próximo, O(n log n)
├── pares_em_risco.py       # todos os pares abaixo de d_seguro
├── forca_bruta.py          # referência O(n^2)
├── simular.py              # gera aeronaves, move por T frames, produz log e HTML
├── benchmark.py            # medição de tempo contra força bruta
├── test_par_proximo.py     # testes de correção
├── saida/
│   ├── log.txt             # pares em conflito por frame
│   ├── relatorio.html      # visualização
│   └── benchmark.png       # gráfico de desempenho
└── README.md
```

## Como executar

Requisitos: Python 3.10 ou superior. O gráfico do benchmark usa `matplotlib` e os testes usam `pytest`.

```bash
pip install matplotlib pytest

# 1. testes de correção
python -m pytest test_par_proximo.py

# 2. simulação, log e visualização
python simular.py

# 3. benchmark
python benchmark.py
```

Depois da simulação, abra `saida/relatorio.html` diretamente no navegador.

## Testes

Os testes comparam `par_mais_proximo` e `pares_em_risco` com a força bruta em milhares de entradas aleatórias. Casos de borda cobertos:

- `n = 0`, `n = 1`, `n = 2` e `n = 3`
- pontos duplicados
- pontos com a mesma coordenada `x`
- pontos colineares
- grades de coordenadas inteiras (muitos empates de distância)
- nenhum par abaixo do limiar
- todos os pares abaixo do limiar
- distância exatamente igual ao limiar (não deve alertar, pois a comparação é estrita)
- `d_seguro` zero ou negativo

## Simulação e visualização

`simular.py` cria `N` aeronaves com posição e velocidade aleatórias e as movimenta por `T` frames, com reflexão nas bordas do plano. A cada frame, `pares_em_risco` é executada e os conflitos são registrados em `saida/log.txt` com frame, aeronaves envolvidas e distância.

`saida/relatorio.html` anima as aeronaves em um plano com eixos em NM. Uma linha vermelha liga cada par em conflito.

## Resultados do benchmark

Ambiente de medição: _preencher (processador, memória, versão do Python)_.

Dois cenários, ambos com `d_seguro = 5` NM:

- **Esparso:** aeronaves distribuídas uniformemente em uma área grande, poucos conflitos.
- **Denso:** o mesmo número de aeronaves concentrado em uma área pequena, muitos conflitos.

| n | Cenário | Força bruta (s) | Divisão e conquista (s) | Pares em risco |
|---|---------|-----------------|-------------------------|----------------|
| 1.000 | esparso | _preencher_ | _preencher_ | _preencher_ |
| 10.000 | esparso | _preencher_ | _preencher_ | _preencher_ |
| 100.000 | esparso | _preencher_ | _preencher_ | _preencher_ |
| 10.000 | denso | _preencher_ | _preencher_ | _preencher_ |

Ponto de cruzamento observado (cenário esparso): _preencher_.

![Benchmark](saida/benchmark.png)

Análise: _preencher com a discussão dos resultados, comparando o cenário esparso com o denso._

## Limitações

- **Fotografia instantânea.** O detector olha apenas a distância no instante atual. Sistemas reais de controle de tráfego preveem trajetórias para antecipar conflitos. Este projeto não faz previsão.
- **Altitude ignorada.** Todas as aeronaves são tratadas como se estivessem na mesma altitude. Aeronaves próximas no plano, mas separadas verticalmente, seriam seguras na prática e aqui são marcadas como conflito (falsos positivos). Nenhum conflito horizontal deixa de ser detectado.
- **Plano cartesiano.** As posições estão em um plano 2D em NM, sem projeção geográfica nem curvatura da Terra.
- **Dados sintéticos.** As aeronaves são geradas aleatoriamente, sem tráfego real.
- **Alta densidade.** Com aeronaves muito concentradas, `pares_em_risco` perde a vantagem assintótica sobre a força bruta, porque o número de comparações na faixa e de pares reportados cresce.
- **Escala do cenário.** Em um setor de controle com dezenas de aeronaves, a força bruta já é suficiente. A vantagem da divisão e conquista aparece em varreduras com milhares de aeronaves.

## Referências

- Cormen, Leiserson, Rivest, Stein. *Introduction to Algorithms*. Capítulo sobre o problema do par de pontos mais próximos.
- Kleinberg, Tardos. *Algorithm Design*. Capítulo sobre divisão e conquista.
- _Adicionar material da disciplina._

## Autor

Carlos, Engenharia de Software, Universidade de Brasília (UnB).
