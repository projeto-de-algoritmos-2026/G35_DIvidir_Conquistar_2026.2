"""Testes da simulação e do log (M3)."""

import re

from forca_bruta import forca_bruta
from simular import avancar, conferem, escrever_log, executar_simulacao

PARAMS = dict(n=60, frames=40, area=100.0, d_seguro=5.0, vel_max=3.0, semente=3)
LINHA_CONFLITO = re.compile(r"^frame=(\d+) \| AC(\d+) - AC(\d+) \| ([\d.]+) NM$")


def rodar(**extra):
    p = {**PARAMS, **extra}
    return executar_simulacao(
        p["n"], p["frames"], p["area"], p["d_seguro"], p["vel_max"], p["semente"]
    )


def test_mesma_semente_gera_o_mesmo_resultado():
    a, _ = rodar()
    b, _ = rodar()
    assert a == b


def test_sementes_diferentes_geram_posicoes_diferentes():
    a, _ = rodar(semente=1)
    b, _ = rodar(semente=2)
    assert a[0]["posicoes"] != b[0]["posicoes"]


def test_aeronaves_permanecem_dentro_da_area():
    frames, _ = rodar(frames=200)
    area = PARAMS["area"]
    for f in frames:
        assert len(f["posicoes"]) == PARAMS["n"]
        for x, y in f["posicoes"]:
            assert 0 <= x <= area and 0 <= y <= area


def test_reflexao_nas_bordas():
    posicoes = [[99.0, 50.0], [1.0, 50.0]]
    velocidades = [[3.0, 0.0], [-3.0, 0.0]]
    avancar(posicoes, velocidades, 100.0)
    assert posicoes == [[98.0, 50.0], [2.0, 50.0]]  # 102 -> 98 e -2 -> 2
    assert velocidades == [[-3.0, 0.0], [3.0, 0.0]]


def test_aeronaves_se_movem_entre_frames():
    frames, _ = rodar(frames=3)
    assert frames[0]["posicoes"] != frames[1]["posicoes"]


def test_conflitos_conferem_com_forca_bruta_em_todos_os_frames():
    frames, divergencias = rodar(frames=100)
    assert divergencias == []
    for f in frames:
        esperado = forca_bruta(f["posicoes"], PARAMS["d_seguro"])
        assert conferem(f["conflitos"], esperado)


def test_log_confere_com_forca_bruta(tmp_path):
    """Relê o arquivo escrito e compara com a força bruta frame a frame."""
    frames, divergencias = rodar(frames=60)
    caminho = tmp_path / "log.txt"
    escrever_log(str(caminho), frames, {"aeronaves": PARAMS["n"]}, not divergencias)

    no_log = {}
    frames_citados = set()
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        if linha.startswith("#") or not linha.strip():
            continue
        frames_citados.add(int(linha.split("|")[0].split("=")[1]))
        m = LINHA_CONFLITO.match(linha)
        if m:
            f, i, j, d = int(m[1]), int(m[2]), int(m[3]), float(m[4])
            no_log.setdefault(f, []).append((i, j, d))

    # Todo frame aparece no log, com ou sem conflito.
    assert frames_citados == set(range(len(frames)))

    for f in frames:
        esperado = forca_bruta(f["posicoes"], PARAMS["d_seguro"])
        lido = no_log.get(f["frame"], [])
        assert [(i, j) for i, j, _ in lido] == [(i, j) for i, j, _ in esperado]
        # O log guarda 3 casas decimais.
        for (_, _, d_log), (_, _, d_ref) in zip(lido, esperado):
            assert abs(d_log - d_ref) <= 5e-4


def test_conferem_detecta_divergencia():
    base = [(0, 1, 2.0), (2, 3, 1.0)]
    assert conferem(base, list(base))
    assert not conferem(base, base[:1])                       # par a menos
    assert not conferem(base, [(0, 1, 2.0), (2, 4, 1.0)])     # par diferente
    assert not conferem(base, [(0, 1, 2.0), (2, 3, 1.5)])     # distância diferente


def test_main_gera_o_log_e_retorna_zero(tmp_path):
    from simular import main

    caminho = tmp_path / "saida" / "log.txt"
    codigo = main(["-n", "40", "-t", "20", "--semente", "5", "--saida", str(caminho)])
    assert codigo == 0
    texto = caminho.read_text(encoding="utf-8")
    assert "todos os frames conferem" in texto