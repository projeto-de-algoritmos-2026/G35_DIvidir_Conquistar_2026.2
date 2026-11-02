"""Força bruta O(n^2): referência de correção e linha de base do benchmark.

Convenções (iguais às dos outros módulos do projeto):
- `pontos` é uma sequência de tuplas (x, y).
- Pares são devolvidos como índices (i, j) da lista original, com i < j.
- "Abaixo da distância segura" significa distância estritamente menor
  que `d_seguro`.
"""

from math import sqrt


def par_mais_proximo_forca_bruta(pontos):
    """Devolve (distancia, (i, j)) do par de menor distância.

    Levanta ValueError se houver menos de 2 pontos.
    """
    n = len(pontos)
    if n < 2:
        raise ValueError("São necessários pelo menos 2 pontos.")

    melhor_d2 = float("inf")
    melhor_par = None
    for i in range(n):
        xi, yi = pontos[i]
        for j in range(i + 1, n):
            dx = xi - pontos[j][0]
            dy = yi - pontos[j][1]
            d2 = dx * dx + dy * dy
            if d2 < melhor_d2:
                melhor_d2 = d2
                melhor_par = (i, j)
    return sqrt(melhor_d2), melhor_par


def forca_bruta(pontos, d_seguro):
    """Devolve todos os pares com distância < d_seguro.

    Formato: lista de (i, j, distancia), com i < j, ordenada por (i, j).
    """
    if d_seguro <= 0:
        return []
    d2_seguro = d_seguro * d_seguro
    resultado = []
    n = len(pontos)
    for i in range(n):
        xi, yi = pontos[i]
        for j in range(i + 1, n):
            dx = xi - pontos[j][0]
            dy = yi - pontos[j][1]
            d2 = dx * dx + dy * dy
            if d2 < d2_seguro:
                resultado.append((i, j, sqrt(d2)))
    return resultado
