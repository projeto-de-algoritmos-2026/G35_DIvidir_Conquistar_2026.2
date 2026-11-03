"""Testes do módulo de benchmark."""

from benchmark import encontrar_ponto_cruzamento, executar_benchmark, main


def test_ponto_cruzamento_identificado():
    n_cruz, registros = encontrar_ponto_cruzamento(
        tamanhos=(10, 25, 50, 100, 200),
        repeticoes=20,
        semente=7,
    )
    assert len(registros) == 5
    assert n_cruz in (10, 25, 50, 100, 200)
    # Em n = 200, divisão e conquista já deve ser mais rápida que força bruta
    assert registros[-1]["tempo_dc"] < registros[-1]["tempo_fb"]


def test_executar_benchmark_e_gerar_grafico(tmp_path):
    caminho_png = tmp_path / "saida" / "benchmark.png"
    codigo = main(["--rapido", "--saida", str(caminho_png)])
    assert codigo == 0
    assert caminho_png.exists()
    assert caminho_png.stat().st_size > 10_000


def test_cenario_denso_tem_mais_pares_que_esparso():
    esparsos, denso = executar_benchmark(
        tamanhos=(1_000,),
        semente=42,
        limite_pares_fb=1_000_000,
    )
    assert len(esparsos) == 1
    assert denso["pares"] > esparsos[0]["pares"]
