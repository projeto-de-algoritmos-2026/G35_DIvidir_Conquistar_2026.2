"""Par de Pontos Mais Próximos por divisão e conquista, O(n log n).

Estratégia:
1. Ordena os pontos por x uma única vez.
2. Divide ao meio e resolve cada metade recursivamente. Cada chamada
   também devolve seus pontos ordenados por y, obtidos por intercalação
   (merge), então não há reordenação a cada nível.
3. Seja d o menor valor entre as metades. Só pontos a menos de d da
   linha divisória podem formar um par melhor entre as metades. Na faixa
   (strip), ordenada por y, cada ponto é comparado apenas com os
   seguintes cuja diferença em y é menor que d (no máximo 7).

Recorrência: T(n) = 2T(n/2) + O(n)  =>  O(n log n).

Convenções:
- `pontos` é uma sequência de tuplas (x, y).
- O par é devolvido como índices (i, j) da lista original, com i < j.
"""

from math import inf, sqrt


def par_mais_proximo(pontos):
    """Devolve (distancia, (i, j)) do par de menor distância.

    Levanta ValueError se houver menos de 2 pontos.
    """
    if len(pontos) < 2:
        raise ValueError("São necessários pelo menos 2 pontos.")

    # Cada ponto vira (x, y, indice_original); ordena por x (depois y, índice).
    por_x = sorted((x, y, i) for i, (x, y) in enumerate(pontos))

    _, melhor_d2, (a, b) = _resolver(por_x)
    return sqrt(melhor_d2), (min(a, b), max(a, b))


def _resolver(P):
    """P está ordenada por x e tem pelo menos 2 pontos.

    Devolve (P ordenada por y, menor distância ao quadrado, (idx_a, idx_b)).
    """
    n = len(P)

    # Caso base: força bruta em até 3 pontos.
    if n <= 3:
        melhor_d2, melhor_par = inf, None
        for a in range(n):
            for b in range(a + 1, n):
                d2 = _dist2(P[a], P[b])
                if d2 < melhor_d2:
                    melhor_d2, melhor_par = d2, (P[a][2], P[b][2])
        return sorted(P, key=_chave_y), melhor_d2, melhor_par

    meio = n // 2
    x_divisoria = P[meio][0]

    # Divisão: com n >= 4, cada metade tem pelo menos 2 pontos.
    esq_y, d2_esq, par_esq = _resolver(P[:meio])
    dir_y, d2_dir, par_dir = _resolver(P[meio:])

    if d2_esq <= d2_dir:
        melhor_d2, melhor_par = d2_esq, par_esq
    else:
        melhor_d2, melhor_par = d2_dir, par_dir

    # Combinação: ordena por y por intercalação, em O(n).
    por_y = _intercalar_por_y(esq_y, dir_y)

    # Faixa: pontos a menos de d da linha divisória (comparação ao quadrado).
    faixa = [p for p in por_y if (p[0] - x_divisoria) ** 2 < melhor_d2]

    for i in range(len(faixa)):
        p = faixa[i]
        for j in range(i + 1, len(faixa)):
            q = faixa[j]
            if (q[1] - p[1]) ** 2 >= melhor_d2:
                break
            d2 = _dist2(p, q)
            if d2 < melhor_d2:
                melhor_d2, melhor_par = d2, (p[2], q[2])

    return por_y, melhor_d2, melhor_par


def _dist2(p, q):
    dx = p[0] - q[0]
    dy = p[1] - q[1]
    return dx * dx + dy * dy


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
