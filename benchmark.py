"""Benchmark: `pares_em_risco` (divisão e conquista) contra `forca_bruta`.

Objetivos:
1. Medir o tempo de execução de `pares_em_risco` (O(n log n)) e `forca_bruta`
   (O(n^2)) para `n` de 10^3 a 10^5 no cenário esparso.
2. Identificar experimentalmente o ponto de cruzamento (menor `n` a partir
   do qual a divisão e conquista supera consistentemente a força bruta).
3. Avaliar o efeito da alta densidade de aeronaves em `n = 10.000`.
4. Gerar o gráfico `saida/benchmark.png`.

Uso:
    python benchmark.py
    python benchmark.py --saida saida/benchmark.png
"""

import argparse
import math
import os
import random
import sys
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from forca_bruta import forca_bruta
from pares_em_risco import pares_em_risco


D_SEGURO = 5.0
TAMANHOS_PRINCIPAIS = (1_000, 2_000, 5_000, 10_000, 20_000, 50_000, 100_000)
TAMANHOS_CRUZAMENTO = (10, 15, 20, 25, 30, 35, 40, 50, 60, 70, 80, 100, 120, 150, 200)


# ---------------------------------------------------------------------------
# Geração de entradas e medição de tempo
# ---------------------------------------------------------------------------

def area_esparsa(n, densidade_base=30.0):
    """Área proporcional a n (lado proporcional a sqrt(n)) para manter densidade constante."""
    return densidade_base * math.sqrt(n)


def gerar_pontos(n, lado, semente):
    rng = random.Random(semente)
    return [(rng.uniform(0.0, lado), rng.uniform(0.0, lado)) for _ in range(n)]


def medir_funcao(func, pontos, d_seguro, repeticoes=1):
    """Executa `func(pontos, d_seguro)` `repeticoes` vezes e devolve (menor_tempo_medio, qtd_pares)."""
    inicio = time.perf_counter()
    resultado = []
    for _ in range(repeticoes):
        resultado = func(pontos, d_seguro)
    decorrido = (time.perf_counter() - inicio) / repeticoes
    return decorrido, len(resultado)


def medir_forca_bruta_grande(pontos, d_seguro, limite_pares=25_000_000):
    """Mede a força bruta em `pontos`.

    Para `n` até ~7.000 (`n*(n-1)/2 <= limite_pares`), executa `forca_bruta`
    integralmente. Para `n` maiores (até 10^5), caso o total de pares exceda
    `limite_pares`, cronometra o laço exato da força bruta sobre os primeiros
    `k` índices (cobrindo `limite_pares` comparações reais na lista de tamanho
    `n`) e extrapola proporcionalmente pelo total `n*(n-1)/2`.
    """
    n = len(pontos)
    total_pares = n * (n - 1) // 2
    if total_pares <= limite_pares:
        return medir_funcao(forca_bruta, pontos, d_seguro, repeticoes=1)[0]

    d2_seguro = d_seguro * d_seguro
    pares_medidos = 0
    acertos = 0
    sqrt = math.sqrt

    inicio = time.perf_counter()
    for i in range(n):
        xi, yi = pontos[i]
        for j in range(i + 1, n):
            dx = xi - pontos[j][0]
            dy = yi - pontos[j][1]
            d2 = dx * dx + dy * dy
            if d2 < d2_seguro:
                acertos += int(sqrt(d2) >= 0)
        pares_medidos += n - 1 - i
        if pares_medidos >= limite_pares:
            break
    tempo_amostra = time.perf_counter() - inicio
    _ = acertos
    return tempo_amostra * (total_pares / pares_medidos)


def encontrar_ponto_cruzamento(
    tamanhos=TAMANHOS_CRUZAMENTO,
    d_seguro=D_SEGURO,
    repeticoes=120,
    semente=100,
):
    """Mede tempos para `n` pequenos e identifica o ponto de cruzamento.

    Devolve `(n_cruzamento, registros)` onde cada item de `registros` é um dict
    com `n`, `tempo_fb` e `tempo_dc` (em segundos).
    """
    rng = random.Random(semente)
    registros = []
    for n in tamanhos:
        lado = area_esparsa(n)
        lotes = [
            [(rng.uniform(0.0, lado), rng.uniform(0.0, lado)) for _ in range(n)]
            for _ in range(repeticoes)
        ]

        t0 = time.perf_counter()
        for pts in lotes:
            forca_bruta(pts, d_seguro)
        tempo_fb = (time.perf_counter() - t0) / repeticoes

        t0 = time.perf_counter()
        for pts in lotes:
            pares_em_risco(pts, d_seguro)
        tempo_dc = (time.perf_counter() - t0) / repeticoes

        registros.append({"n": n, "tempo_fb": tempo_fb, "tempo_dc": tempo_dc})

    # Ponto de cruzamento: primeiro n a partir do qual DC <= FB de forma sustentada
    n_cruzamento = registros[-1]["n"]
    for idx, reg in enumerate(registros):
        if reg["tempo_dc"] <= reg["tempo_fb"]:
            # Verifica se continua menor na maioria dos próximos pontos
            restantes = registros[idx:]
            if sum(1 for r in restantes if r["tempo_dc"] <= r["tempo_fb"]) >= len(restantes) - 1:
                n_cruzamento = reg["n"]
                break

    return n_cruzamento, registros


def executar_benchmark(
    tamanhos=TAMANHOS_PRINCIPAIS,
    d_seguro=D_SEGURO,
    semente=42,
    limite_pares_fb=50_000_000,
):
    """Executa o benchmark de 10^3 a 10^5 (esparso) e em 10^4 (denso)."""
    resultados_esparsos = []
    for indice, n in enumerate(tamanhos):
        lado = area_esparsa(n)
        pontos = gerar_pontos(n, lado, semente + indice)

        tempo_dc, qtd_pares = medir_funcao(pares_em_risco, pontos, d_seguro, repeticoes=1)
        tempo_fb = medir_forca_bruta_grande(pontos, d_seguro, limite_pares=limite_pares_fb)

        resultados_esparsos.append({
            "n": n,
            "cenario": "esparso",
            "area": lado,
            "tempo_fb": tempo_fb,
            "tempo_dc": tempo_dc,
            "pares": qtd_pares,
            "extrapolado_fb": (n * (n - 1) // 2) > limite_pares_fb,
        })

    # Cenário denso em n = 10.000 (mesmo número de aeronaves em área 50x50 NM)
    n_denso = 10_000
    lado_denso = 50.0
    pontos_densos = gerar_pontos(n_denso, lado_denso, semente + 999)
    tempo_dc_denso, pares_densos = medir_funcao(pares_em_risco, pontos_densos, d_seguro, repeticoes=1)
    tempo_fb_denso = medir_forca_bruta_grande(pontos_densos, d_seguro, limite_pares=limite_pares_fb)

    resultado_denso = {
        "n": n_denso,
        "cenario": "denso",
        "area": lado_denso,
        "tempo_fb": tempo_fb_denso,
        "tempo_dc": tempo_dc_denso,
        "pares": pares_densos,
        "extrapolado_fb": False,
    }

    return resultados_esparsos, resultado_denso


# ---------------------------------------------------------------------------
# Geração do gráfico
# ---------------------------------------------------------------------------

def gerar_grafico(caminho, resultados_esparsos, resultado_denso, n_cruzamento, dados_cruzamento):
    """Salva `benchmark.png` com dois painéis: (1) 10^3 a 10^5 e (2) ponto de cruzamento."""
    pasta = os.path.dirname(caminho)
    if pasta:
        os.makedirs(pasta, exist_ok=True)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.5, 5.6), dpi=150)
    fig.suptitle(
        "Desempenho: Força Bruta O(n²) vs. Divisão e Conquista O(n log n)",
        fontsize=13,
        fontweight="bold",
    )

    # Painel 1: Escala de 10^3 a 10^5 (log-log)
    ns = [r["n"] for r in resultados_esparsos]
    tempos_fb = [r["tempo_fb"] for r in resultados_esparsos]
    tempos_dc = [r["tempo_dc"] for r in resultados_esparsos]

    ax1.loglog(
        ns, tempos_fb, "o--", color="#dc2626", linewidth=2.2, markersize=6,
        label="Força bruta O(n²) — esparso",
    )
    ax1.loglog(
        ns, tempos_dc, "s-", color="#0284c7", linewidth=2.2, markersize=6,
        label="pares_em_risco O(n log n) — esparso",
    )

    if resultado_denso:
        ax1.loglog(
            [resultado_denso["n"]], [resultado_denso["tempo_dc"]],
            "^", color="#d97706", markersize=9,
            label=f"pares_em_risco — denso (n={resultado_denso['n']:,})",
        )
        ax1.annotate(
            f"Denso ({resultado_denso['pares']:,} pares)\n{resultado_denso['tempo_dc']:.2f}s",
            xy=(resultado_denso["n"], resultado_denso["tempo_dc"]),
            xytext=(resultado_denso["n"] * 0.42, resultado_denso["tempo_dc"] * 2.3),
            arrowprops=dict(arrowstyle="->", color="#b45309", lw=1.1),
            fontsize=8.5,
            color="#92400e",
            fontweight="bold",
        )

    # Anota ganho em n = 10^4 e n = 10^5
    for r in resultados_esparsos:
        if r["n"] in (1_000, 10_000, 100_000):
            ganho = r["tempo_fb"] / max(r["tempo_dc"], 1e-9)
            ax1.annotate(
                f"{ganho:.0f}× mais rápido",
                xy=(r["n"], r["tempo_dc"]),
                xytext=(r["n"] * 0.65, r["tempo_dc"] * 0.38),
                fontsize=8,
                color="#0369a1",
                fontweight="bold",
            )

    ax1.set_title("Escala de 10³ a 10⁵ aeronaves (log-log)", fontsize=11)
    ax1.set_xlabel("Número de aeronaves (n)")
    ax1.set_ylabel("Tempo de execução (segundos)")
    ax1.grid(True, which="both", linestyle=":", alpha=0.6)
    ax1.legend(loc="upper left", fontsize=8.8)

    # Painel 2: Ponto de cruzamento em n pequenos (escala linear em ms)
    ns_cruz = [r["n"] for r in dados_cruzamento]
    fb_ms = [r["tempo_fb"] * 1000.0 for r in dados_cruzamento]
    dc_ms = [r["tempo_dc"] * 1000.0 for r in dados_cruzamento]

    ax2.plot(ns_cruz, fb_ms, "o--", color="#dc2626", linewidth=2.0, markersize=5, label="Força bruta O(n²)")
    ax2.plot(ns_cruz, dc_ms, "s-", color="#0284c7", linewidth=2.0, markersize=5, label="pares_em_risco O(n log n)")
    ax2.axvline(
        n_cruzamento, color="#16a34a", linestyle="-.", linewidth=1.8,
        label=f"Ponto de cruzamento (n ≈ {n_cruzamento})",
    )

    reg_cruz = next((r for r in dados_cruzamento if r["n"] == n_cruzamento), dados_cruzamento[0])
    y_cruz = reg_cruz["tempo_dc"] * 1000.0
    ax2.annotate(
        f"Cruzamento: n ≈ {n_cruzamento}\n({y_cruz:.3f} ms)",
        xy=(n_cruzamento, y_cruz),
        xytext=(n_cruzamento + 25, max(fb_ms) * 0.55),
        arrowprops=dict(arrowstyle="->", color="#15803d", lw=1.2),
        fontsize=9,
        color="#166534",
        fontweight="bold",
    )

    ax2.set_title("Identificação do Ponto de Cruzamento (n pequeno)", fontsize=11)
    ax2.set_xlabel("Número de aeronaves (n)")
    ax2.set_ylabel("Tempo médio por chamada (ms)")
    ax2.grid(True, linestyle=":", alpha=0.6)
    ax2.legend(loc="upper left", fontsize=8.8)

    fig.tight_layout()
    fig.savefig(caminho, dpi=150)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Linha de comando
# ---------------------------------------------------------------------------

def ler_argumentos(argv=None):
    p = argparse.ArgumentParser(description="Benchmark entre pares_em_risco e força bruta.")
    p.add_argument(
        "--saida",
        default=os.path.join("saida", "benchmark.png"),
        help="caminho do gráfico gerado (padrão: saida/benchmark.png)",
    )
    p.add_argument(
        "--semente",
        type=int,
        default=42,
        help="semente aleatória (padrão: 42)",
    )
    p.add_argument(
        "--rapido",
        action="store_true",
        help="usa tamanhos reduzidos para execução rápida em testes",
    )
    return p.parse_args(argv)


def main(argv=None):
    args = ler_argumentos(argv)
    if args.rapido:
        tamanhos = (200, 500, 1_000)
        tamanhos_cruz = (10, 20, 30, 40, 60, 80, 100)
        repeticoes_cruz = 25
        limite_fb = 2_000_000
    else:
        tamanhos = TAMANHOS_PRINCIPAIS
        tamanhos_cruz = TAMANHOS_CRUZAMENTO
        repeticoes_cruz = 120
        limite_fb = 50_000_000

    n_cruzamento, dados_cruz = encontrar_ponto_cruzamento(
        tamanhos=tamanhos_cruz,
        repeticoes=repeticoes_cruz,
        semente=args.semente + 100,
    )
    resultados_esparsos, resultado_denso = executar_benchmark(
        tamanhos=tamanhos,
        semente=args.semente,
        limite_pares_fb=limite_fb,
    )

    gerar_grafico(args.saida, resultados_esparsos, resultado_denso, n_cruzamento, dados_cruz)

    print("=== Benchmark: Força Bruta O(n^2) vs Divisão e Conquista O(n log n) ===")
    print(f"Ponto de cruzamento identificado (cenário esparso): n ~ {n_cruzamento}")
    print()
    print(f"{'n':>10} | {'Cenário':<8} | {'Força bruta (s)':>16} | {'Div. e Conq. (s)':>16} | {'Speedup':>9} | {'Pares em risco':>14}")
    print("-" * 86)
    for r in resultados_esparsos:
        sufixo = "*" if r["extrapolado_fb"] else " "
        ganho = r["tempo_fb"] / max(r["tempo_dc"], 1e-9)
        print(
            f"{r['n']:>10,} | {r['cenario']:<8} | {r['tempo_fb']:>15.4f}{sufixo} | "
            f"{r['tempo_dc']:>16.4f} | {ganho:>8.1f}x | {r['pares']:>14,}"
        )
    if not args.rapido:
        ganho_d = resultado_denso["tempo_fb"] / max(resultado_denso["tempo_dc"], 1e-9)
        print(
            f"{resultado_denso['n']:>10,} | {resultado_denso['cenario']:<8} | "
            f"{resultado_denso['tempo_fb']:>15.4f}  | {resultado_denso['tempo_dc']:>16.4f} | "
            f"{ganho_d:>8.1f}x | {resultado_denso['pares']:>14,}"
        )
    print()
    print(f"Gráfico salvo em {args.saida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

