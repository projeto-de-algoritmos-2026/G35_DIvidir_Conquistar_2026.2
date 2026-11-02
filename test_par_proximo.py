"""Testes de correção: núcleo (divisão e conquista) contra força bruta."""

import math
import random

import pytest

from forca_bruta import forca_bruta, par_mais_proximo_forca_bruta
from par_mais_proximo import par_mais_proximo
from pares_em_risco import pares_em_risco


# ---------------------------------------------------------------------------
# Auxiliares
# ---------------------------------------------------------------------------

def dist(pontos, i, j):
    return math.hypot(pontos[i][0] - pontos[j][0], pontos[i][1] - pontos[j][1])


def verificar_par_mais_proximo(pontos):
    """O par devolvido deve ser válido e ter a menor distância possível."""
    d, (i, j) = par_mais_proximo(pontos)
    d_ref, _ = par_mais_proximo_forca_bruta(pontos)

    assert 0 <= i < j < len(pontos)
    assert d == pytest.approx(d_ref, abs=1e-12)
    # A distância informada deve ser a do par informado (e não de outro).
    assert dist(pontos, i, j) == pytest.approx(d_ref, abs=1e-12)


def verificar_pares_em_risco(pontos, d_seguro):
    """Mesmos pares da força bruta, sem repetição e com distâncias certas."""
    obtido = pares_em_risco(pontos, d_seguro)
    esperado = forca_bruta(pontos, d_seguro)

    pares_obtidos = [(i, j) for i, j, _ in obtido]
    pares_esperados = [(i, j) for i, j, _ in esperado]

    assert pares_obtidos == pares_esperados  # mesmo conjunto, mesma ordem
    assert len(set(pares_obtidos)) == len(pares_obtidos)  # sem duplicatas
    for i, j, d in obtido:
        assert i < j
        assert d < d_seguro
        assert d == pytest.approx(dist(pontos, i, j), abs=1e-12)


def verificar_tudo(pontos, d_seguro):
    if len(pontos) >= 2:
        verificar_par_mais_proximo(pontos)
    verificar_pares_em_risco(pontos, d_seguro)


# ---------------------------------------------------------------------------
# Entradas aleatórias (milhares de casos)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("semente", range(5))
def test_aleatorios_reais(semente):
    """Coordenadas reais, vários tamanhos, escalas e limiares."""
    rng = random.Random(semente)
    for _ in range(1000):
        n = rng.randint(0, 60)
        escala = rng.choice([1, 5, 50, 1000])
        pontos = [(rng.uniform(0, escala), rng.uniform(0, escala)) for _ in range(n)]
        verificar_tudo(pontos, rng.uniform(0.01, escala / 2))


@pytest.mark.parametrize("semente", range(3))
def test_aleatorios_grade_inteira(semente):
    """Grade pequena: muitos empates, x repetidos e pontos duplicados."""
    rng = random.Random(100 + semente)
    for _ in range(1000):
        n = rng.randint(0, 50)
        lado = rng.choice([3, 6, 10])
        pontos = [(rng.randint(0, lado), rng.randint(0, lado)) for _ in range(n)]
        verificar_tudo(pontos, rng.choice([0.5, 1, 1.5, 2, 3, 5]))


def test_aleatorios_grandes():
    rng = random.Random(7)
    for n in (200, 500, 1000):
        pontos = [(rng.uniform(0, 100), rng.uniform(0, 100)) for _ in range(n)]
        verificar_tudo(pontos, 3.0)


def test_aleatorios_alta_densidade():
    """Aeronaves amontoadas: muitos pares em risco."""
    rng = random.Random(8)
    for _ in range(50):
        pontos = [(rng.uniform(0, 10), rng.uniform(0, 10)) for _ in range(150)]
        verificar_tudo(pontos, 4.0)


# ---------------------------------------------------------------------------
# Casos de borda
# ---------------------------------------------------------------------------

def test_par_menos_de_dois_pontos_levanta_erro():
    for pontos in ([], [(1, 1)]):
        with pytest.raises(ValueError):
            par_mais_proximo(pontos)
        with pytest.raises(ValueError):
            par_mais_proximo_forca_bruta(pontos)


def test_risco_menos_de_dois_pontos_devolve_vazio():
    assert pares_em_risco([], 5) == []
    assert pares_em_risco([(1, 1)], 5) == []


def test_n_igual_2():
    pontos = [(0, 0), (3, 4)]
    assert par_mais_proximo(pontos) == (5.0, (0, 1))
    verificar_tudo(pontos, 6)
    verificar_tudo(pontos, 4)


def test_n_igual_3():
    pontos = [(0, 0), (10, 0), (10, 1)]
    d, par = par_mais_proximo(pontos)
    assert d == pytest.approx(1.0)
    assert par == (1, 2)
    verificar_tudo(pontos, 2)
    verificar_tudo(pontos, 20)


def test_pontos_duplicados():
    pontos = [(2, 2)] * 6
    d, par = par_mais_proximo(pontos)
    assert d == 0.0
    assert par[0] < par[1]
    # Todos os C(6,2) = 15 pares têm distância 0 < d_seguro.
    assert len(pares_em_risco(pontos, 1)) == 15
    verificar_tudo(pontos, 1)


def test_duplicados_misturados_com_outros_pontos():
    pontos = [(0, 0), (5, 5), (0, 0), (9, 1), (5, 5), (7, 7)]
    verificar_tudo(pontos, 0.5)
    verificar_tudo(pontos, 3)


def test_mesma_coordenada_x():
    pontos = [(4, y) for y in (0, 7, 2, 9, 3, 15, 11)]
    d, _ = par_mais_proximo(pontos)
    assert d == pytest.approx(1.0)  # y = 2 e y = 3
    verificar_tudo(pontos, 3)
    verificar_tudo(pontos, 0.5)


def test_colineares_horizontal():
    pontos = [(x, 0) for x in (0, 10, 3, 4, 20, 21.5, 40)]
    d, _ = par_mais_proximo(pontos)
    assert d == pytest.approx(1.0)  # x = 3 e x = 4
    verificar_tudo(pontos, 2.5)


def test_colineares_vertical():
    pontos = [(0, y) for y in range(0, 60, 2)]
    verificar_tudo(pontos, 2.5)
    verificar_tudo(pontos, 4.5)


def test_colineares_diagonal():
    pontos = [(i, i) for i in range(30)]
    d, _ = par_mais_proximo(pontos)
    assert d == pytest.approx(math.sqrt(2))
    verificar_tudo(pontos, 3)


# ---------------------------------------------------------------------------
# Limiar
# ---------------------------------------------------------------------------

def test_nenhum_par_abaixo_do_limiar():
    pontos = [(0, 0), (100, 0), (0, 100), (100, 100)]
    assert pares_em_risco(pontos, 5) == []
    verificar_tudo(pontos, 5)


def test_todos_os_pares_abaixo_do_limiar():
    pontos = [(0, 0), (1, 0), (0, 1), (1, 1), (0.5, 0.5)]
    # C(5,2) = 10 pares, todos a menos de 2 unidades.
    assert len(pares_em_risco(pontos, 2)) == 10
    verificar_tudo(pontos, 2)


def test_distancia_exatamente_igual_ao_limiar_nao_alerta():
    pontos = [(0, 0), (3, 4)]  # distância exata 5
    assert pares_em_risco(pontos, 5) == []
    assert forca_bruta(pontos, 5) == []
    assert len(pares_em_risco(pontos, 5.0001)) == 1


@pytest.mark.parametrize("d_seguro", [0, -1, -5.5])
def test_limiar_nao_positivo(d_seguro):
    pontos = [(0, 0), (0, 0), (1, 1)]
    assert pares_em_risco(pontos, d_seguro) == []
    assert forca_bruta(pontos, d_seguro) == []


def test_ordem_dos_pontos_nao_altera_o_resultado():
    rng = random.Random(9)
    pontos = [(rng.uniform(0, 30), rng.uniform(0, 30)) for _ in range(80)]
    esperado = {(i, j) for i, j, _ in forca_bruta(pontos, 4)}

    permutacao = list(range(len(pontos)))
    rng.shuffle(permutacao)
    embaralhados = [pontos[k] for k in permutacao]
    obtido = {
        tuple(sorted((permutacao[i], permutacao[j])))
        for i, j, _ in pares_em_risco(embaralhados, 4)
    }
    assert obtido == esperado
