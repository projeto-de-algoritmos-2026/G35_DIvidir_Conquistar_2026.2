"""Simulação de aeronaves em um plano 2D e log de conflitos de separação.

Fluxo:
1. Cria N aeronaves com posição e velocidade aleatórias em um quadrado
   de lado `area` (em NM).
2. Avança T frames. A cada frame as aeronaves se movem e batem nas
   bordas (reflexão).
3. Em cada frame, `pares_em_risco` detecta os pares a menos de
   `d_seguro` e, por padrão, o resultado é conferido contra a força bruta.
4. Escreve o log em `saida/log.txt`.

Unidades: posições em NM, velocidades em NM por frame. A simulação é um
cenário sintético, sem física de voo.

Uso:
    python simular.py
    python simular.py --aeronaves 200 --frames 300 --semente 7
"""

import argparse
import math
import os
import random
import sys

from forca_bruta import forca_bruta
from pares_em_risco import pares_em_risco


# ---------------------------------------------------------------------------
# Simulação
# ---------------------------------------------------------------------------

def criar_aeronaves(n, area, vel_max, rng):
    """Devolve (posicoes, velocidades) como listas de [x, y] mutáveis."""
    posicoes = [[rng.uniform(0, area), rng.uniform(0, area)] for _ in range(n)]
    velocidades = []
    for _ in range(n):
        modulo = rng.uniform(0.3 * vel_max, vel_max)
        angulo = rng.uniform(0, 2 * math.pi)
        velocidades.append([modulo * math.cos(angulo), modulo * math.sin(angulo)])
    return posicoes, velocidades


def avancar(posicoes, velocidades, area):
    """Move cada aeronave um frame, refletindo nas bordas do quadrado."""
    for p, v in zip(posicoes, velocidades):
        for eixo in (0, 1):
            p[eixo] += v[eixo]
            if p[eixo] < 0:
                p[eixo] = -p[eixo]
                v[eixo] = -v[eixo]
            elif p[eixo] > area:
                p[eixo] = 2 * area - p[eixo]
                v[eixo] = -v[eixo]


def conferem(obtido, esperado, tolerancia=1e-9):
    """Mesmos pares, na mesma ordem, e distâncias praticamente iguais."""
    if [(i, j) for i, j, _ in obtido] != [(i, j) for i, j, _ in esperado]:
        return False
    return all(abs(a[2] - b[2]) <= tolerancia for a, b in zip(obtido, esperado))


def executar_simulacao(n, frames, area, d_seguro, vel_max, semente, verificar=True):
    """Roda a simulação.

    Devolve (lista_de_frames, divergencias). Cada frame é um dict com:
    - "frame": número do frame (0 é a posição inicial);
    - "posicoes": lista de (x, y) de todas as aeronaves;
    - "conflitos": lista de (i, j, distancia) vinda de `pares_em_risco`.

    `divergencias` lista os números dos frames em que o resultado diferiu
    da força bruta (vazia se tudo conferiu, ou se `verificar` é falso).
    """
    rng = random.Random(semente)
    posicoes, velocidades = criar_aeronaves(n, area, vel_max, rng)

    resultado = []
    divergencias = []
    for frame in range(frames):
        if frame > 0:
            avancar(posicoes, velocidades, area)
        pontos = [(x, y) for x, y in posicoes]
        conflitos = pares_em_risco(pontos, d_seguro)

        if verificar and not conferem(conflitos, forca_bruta(pontos, d_seguro)):
            divergencias.append(frame)

        resultado.append({"frame": frame, "posicoes": pontos, "conflitos": conflitos})
    return resultado, divergencias


# ---------------------------------------------------------------------------
# Log
# ---------------------------------------------------------------------------

def rotulo(indice, largura):
    return f"AC{indice:0{largura}d}"


def escrever_log(caminho, frames, parametros, verificacao):
    """Escreve o log. `verificacao` é True, False ou None (não verificado)."""
    n = parametros["aeronaves"]
    largura = max(3, len(str(n - 1)))
    pasta = os.path.dirname(caminho)
    if pasta:
        os.makedirs(pasta, exist_ok=True)

    total_eventos = sum(len(f["conflitos"]) for f in frames)
    frames_com_conflito = sum(1 for f in frames if f["conflitos"])
    distancias = [d for f in frames for _, _, d in f["conflitos"]]

    with open(caminho, "w", encoding="utf-8") as arq:
        arq.write("# Log de conflitos de separação\n")
        arq.write("# Formato: frame=<n> | <aeronave A> - <aeronave B> | <distância> NM\n")
        arq.write("# Parâmetros: " + ", ".join(f"{k}={v}" for k, v in parametros.items()) + "\n")
        arq.write("# Distâncias em NM; um conflito é um par a menos de d_seguro.\n")
        arq.write("\n")

        for f in frames:
            numero = f["frame"]
            if not f["conflitos"]:
                arq.write(f"frame={numero:04d} | sem conflitos\n")
                continue
            for i, j, d in f["conflitos"]:
                arq.write(
                    f"frame={numero:04d} | {rotulo(i, largura)} - {rotulo(j, largura)} | {d:.3f} NM\n"
                )

        arq.write("\n")
        arq.write(f"# Frames simulados: {len(frames)}\n")
        arq.write(f"# Frames com conflito: {frames_com_conflito}\n")
        arq.write(f"# Total de pares em conflito (soma dos frames): {total_eventos}\n")
        if distancias:
            arq.write(f"# Menor distância registrada: {min(distancias):.3f} NM\n")
        if verificacao is None:
            arq.write("# Verificação contra força bruta: não executada\n")
        else:
            estado = "todos os frames conferem" if verificacao else "DIVERGÊNCIAS ENCONTRADAS"
            arq.write(f"# Verificação contra força bruta: {estado}\n")


# ---------------------------------------------------------------------------
# Linha de comando
# ---------------------------------------------------------------------------

def ler_argumentos(argv=None):
    p = argparse.ArgumentParser(description="Simulação de aeronaves e log de conflitos.")
    p.add_argument("-n", "--aeronaves", type=int, default=80, help="número de aeronaves (padrão: 80)")
    p.add_argument("-t", "--frames", type=int, default=120, help="número de frames (padrão: 120)")
    p.add_argument("--area", type=float, default=200.0, help="lado do quadrado em NM (padrão: 200)")
    p.add_argument("--d-seguro", type=float, default=5.0, help="separação mínima em NM (padrão: 5)")
    p.add_argument("--vel-max", type=float, default=3.0, help="velocidade máxima em NM/frame (padrão: 3)")
    p.add_argument("--semente", type=int, default=42, help="semente aleatória (padrão: 42)")
    p.add_argument("--saida", default=os.path.join("saida", "log.txt"), help="caminho do log")
    p.add_argument("--sem-verificacao", action="store_true",
                   help="não conferir com a força bruta (útil para n muito grande)")
    args = p.parse_args(argv)

    if args.aeronaves < 2:
        p.error("--aeronaves deve ser pelo menos 2")
    if args.frames < 1:
        p.error("--frames deve ser pelo menos 1")
    if args.area <= 0 or args.d_seguro <= 0 or args.vel_max <= 0:
        p.error("--area, --d-seguro e --vel-max devem ser positivos")
    if args.vel_max >= args.area:
        p.error("--vel-max deve ser menor que --area")
    return args


def main(argv=None):
    args = ler_argumentos(argv)
    verificar = not args.sem_verificacao

    frames, divergencias = executar_simulacao(
        args.aeronaves, args.frames, args.area, args.d_seguro,
        args.vel_max, args.semente, verificar,
    )

    parametros = {
        "aeronaves": args.aeronaves,
        "frames": args.frames,
        "area": args.area,
        "d_seguro": args.d_seguro,
        "vel_max": args.vel_max,
        "semente": args.semente,
    }
    verificacao = None if not verificar else (len(divergencias) == 0)
    escrever_log(args.saida, frames, parametros, verificacao)

    eventos = sum(len(f["conflitos"]) for f in frames)
    com_conflito = sum(1 for f in frames if f["conflitos"])
    print(f"Log escrito em {args.saida}")
    print(f"{args.frames} frames, {com_conflito} com conflito, {eventos} pares em conflito no total")
    if not verificar:
        print("Verificação contra força bruta: não executada")
    elif divergencias:
        print(f"ERRO: divergência da força bruta nos frames {divergencias[:10]}")
        return 1
    else:
        print("Verificação contra força bruta: todos os frames conferem")
    return 0


if __name__ == "__main__":
    sys.exit(main())