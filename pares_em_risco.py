"""Todos os pares a menos de `d_seguro`, por divisão e conquista.

Diferença para `par_mais_proximo`: o limiar da faixa (strip) é FIXO em
`d_seguro`, em vez de encolher conforme a recursão acha pares melhores.
Assim, a etapa de combinação coleta todos os pares com distância menor
que `d_seguro` que cruzam a linha divisória. Pares dentro de uma mesma
metade já foram coletados na recursão, então a combinação conta apenas
pares com um ponto de cada lado (cada par é registrado uma única vez).

Custo: O(n log n) mais as comparações feitas dentro da faixa. Com poucos
conflitos, fica perto de O(n log n). Com aeronaves muito amontoadas, a
faixa fica cheia e o número de comparações cresce, podendo se aproximar
de O(n^2). Esse efeito é o que o benchmark deve medir.

Convenções:
- `pontos` é uma sequência de tuplas (x, y).
- "Abaixo da distância segura" significa distância estritamente menor
  que `d_seguro`.
- Resultado: lista de (i, j, distancia), com i < j sobre a lista
  original, ordenada por (i, j).
"""

from math import sqrt


def pares_em_risco(pontos, d_seguro):
    """Devolve todos os pares com distância < d_seguro."""
    if len(pontos) < 2 or d_seguro <= 0:
        return []

    d2_seguro = d_seguro * d_seguro

    # Cada ponto vira (x, y, indice_original, posicao_na_ordem_por_x).
    ordenados = sorted((x, y, i) for i, (x, y) in enumerate(pontos))
    P = [(x, y, i, rank) for rank, (x, y, i) in enumerate(ordenados)]

    resultado = []

    def resolver(trecho):
        """`trecho` está ordenado por x e tem pelo menos 2 pontos.

        Devolve o trecho ordenado por y e acumula os pares em `resultado`.
        """
        n = len(trecho)

        # Caso base: força bruta em até 3 pontos.
        if n <= 3:
            for a in range(n):
                for b in range(a + 1, n):
                    _registrar(trecho[a], trecho[b], d2_seguro, resultado)
            return sorted(trecho, key=_chave_y)

        meio = n // 2
        x_divisoria = trecho[meio][0]
        rank_corte = trecho[meio][3]  # ranks < rank_corte estão à esquerda

        esq_y = resolver(trecho[:meio])
        dir_y = resolver(trecho[meio:])
        por_y = _intercalar_por_y(esq_y, dir_y)

        # Faixa de largura fixa: um par que cruza a divisória com
        # distância < d_seguro tem os dois pontos a menos de d_seguro dela.
        faixa = [p for p in por_y if (p[0] - x_divisoria) ** 2 < d2_seguro]

        for i in range(len(faixa)):
            p = faixa[i]
            p_esquerda = p[3] < rank_corte
            for j in range(i + 1, len(faixa)):
                q = faixa[j]
                if (q[1] - p[1]) ** 2 >= d2_seguro:
                    break
                # Só pares que cruzam a divisória (lados diferentes).
                if p_esquerda != (q[3] < rank_corte):
                    _registrar(p, q, d2_seguro, resultado)

        return por_y

    resolver(P)
    resultado.sort()
    return resultado


def _registrar(p, q, d2_seguro, resultado):
    dx = p[0] - q[0]
    dy = p[1] - q[1]
    d2 = dx * dx + dy * dy
    if d2 < d2_seguro:
        i, j = (p[2], q[2]) if p[2] < q[2] else (q[2], p[2])
        resultado.append((i, j, sqrt(d2)))


def _chave_y(p):
    return p[1]


def _intercalar_por_y(A, B):
    """Intercala duas listas já ordenadas por y."""
    resultado = []
    i = j = 0
    while i < len(A) and j < len(B):
        if A[i][1] <= B[j][1]:
            resultado.append(A[i])
            i += 1
        else:
            resultado.append(B[j])
            j += 1
    resultado.extend(A[i:])
    resultado.extend(B[j:])
    return resultado
