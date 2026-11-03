"""Simulação de aeronaves em um plano 2D, log e visualização HTML/SVG.

Fluxo:
1. Cria N aeronaves com posição e velocidade aleatórias em um quadrado
   de lado `area` (em NM).
2. Avança T frames. A cada frame as aeronaves se movem e batem nas
   bordas (reflexão).
3. Em cada frame, `pares_em_risco` detecta os pares a menos de
   `d_seguro` e, por padrão, o resultado é conferido contra a força bruta.
4. Escreve o log em `saida/log.txt` e a visualização em `saida/relatorio.html`.

Unidades: posições em NM, velocidades em NM por frame. A simulação é um
cenário sintético, sem física de voo.

Uso:
    python simular.py
    python simular.py --aeronaves 200 --frames 300 --semente 7
"""

import argparse
import json
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
# Visualização HTML/SVG
# ---------------------------------------------------------------------------

def _montar_svg_estatico(frame_dados, area, d_seguro, rotulos):
    """Gera o conteúdo interno inicial do SVG (eixos em NM, pontos e conflitos)."""
    margem_esq = 65.0
    margem_topo = 30.0
    tamanho_plot = 600.0
    base_y = margem_topo + tamanho_plot

    def sx(x):
        return margem_esq + (x / area) * tamanho_plot

    def sy(y):
        return base_y - (y / area) * tamanho_plot

    linhas = []
    # Fundo da área do plano
    linhas.append(
        f'<rect x="{margem_esq:.1f}" y="{margem_topo:.1f}" '
        f'width="{tamanho_plot:.1f}" height="{tamanho_plot:.1f}" '
        f'fill="#0f172a" stroke="#334155" stroke-width="1.5" />'
    )

    # Grade e marcações dos eixos em NM (5 divisões)
    passos = 5
    for k in range(passos + 1):
        frac = k / passos
        valor_nm = frac * area
        px = sx(valor_nm)
        py = sy(valor_nm)
        rotulo_nm = f"{valor_nm:g} NM"

        # Linhas de grade internas
        if 0 < k < passos:
            linhas.append(
                f'<line x1="{px:.1f}" y1="{margem_topo:.1f}" x2="{px:.1f}" y2="{base_y:.1f}" '
                f'stroke="#1e293b" stroke-width="1" stroke-dasharray="4 4" />'
            )
            linhas.append(
                f'<line x1="{margem_esq:.1f}" y1="{py:.1f}" x2="{margem_esq + tamanho_plot:.1f}" y2="{py:.1f}" '
                f'stroke="#1e293b" stroke-width="1" stroke-dasharray="4 4" />'
            )

        # Ticks e valores do eixo X (em NM)
        linhas.append(
            f'<line x1="{px:.1f}" y1="{base_y:.1f}" x2="{px:.1f}" y2="{base_y + 6:.1f}" '
            f'stroke="#94a3b8" stroke-width="1.2" />'
        )
        linhas.append(
            f'<text x="{px:.1f}" y="{base_y + 22:.1f}" fill="#cbd5e1" '
            f'font-size="11" text-anchor="middle">{rotulo_nm}</text>'
        )

        # Ticks e valores do eixo Y (em NM)
        linhas.append(
            f'<line x1="{margem_esq - 6:.1f}" y1="{py:.1f}" x2="{margem_esq:.1f}" y2="{py:.1f}" '
            f'stroke="#94a3b8" stroke-width="1.2" />'
        )
        linhas.append(
            f'<text x="{margem_esq - 10:.1f}" y="{py + 4:.1f}" fill="#cbd5e1" '
            f'font-size="11" text-anchor="end">{rotulo_nm}</text>'
        )

    # Títulos dos eixos
    meio_x = margem_esq + tamanho_plot / 2
    meio_y = margem_topo + tamanho_plot / 2
    linhas.append(
        f'<text x="{meio_x:.1f}" y="{base_y + 45:.1f}" fill="#e2e8f0" '
        f'font-size="13" font-weight="600" text-anchor="middle">Posição X (NM)</text>'
    )
    linhas.append(
        f'<text x="18" y="{meio_y:.1f}" fill="#e2e8f0" font-size="13" font-weight="600" '
        f'text-anchor="middle" transform="rotate(-90 18 {meio_y:.1f})">Posição Y (NM)</text>'
    )

    posicoes = frame_dados["posicoes"]
    conflitos = frame_dados["conflitos"]
    em_risco = set()
    for i, j, _ in conflitos:
        em_risco.add(i)
        em_risco.add(j)

    # Camada de linhas vermelhas nos pares em conflito
    linhas.append('<g id="camada-conflitos">')
    for i, j, d in conflitos:
        x1, y1 = sx(posicoes[i][0]), sy(posicoes[i][1])
        x2, y2 = sx(posicoes[j][0]), sy(posicoes[j][1])
        linhas.append(
            f'<line class="conflito-linha" data-par="{rotulos[i]}-{rotulos[j]}" '
            f'x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
            f'stroke="#ef4444" stroke-width="2.4" stroke-linecap="round">'
            f'<title>{rotulos[i]} - {rotulos[j]}: {d:.3f} NM (&lt; {d_seguro:g} NM)</title>'
            f'</line>'
        )
    linhas.append('</g>')

    # Camada de pontos das aeronaves
    linhas.append('<g id="camada-aeronaves">')
    for idx, (x, y) in enumerate(posicoes):
        cx, cy = sx(x), sy(y)
        conflito = idx in em_risco
        cor = "#ef4444" if conflito else "#38bdf8"
        raio = "5.0" if conflito else "3.8"
        classe = "aeronave em-conflito" if conflito else "aeronave segura"
        linhas.append(
            f'<circle class="{classe}" data-id="{rotulos[idx]}" '
            f'cx="{cx:.2f}" cy="{cy:.2f}" r="{raio}" fill="{cor}" '
            f'stroke="#0f172a" stroke-width="1.2">'
            f'<title>{rotulos[idx]} ({x:.2f} NM, {y:.2f} NM)</title>'
            f'</circle>'
        )
        if conflito:
            linhas.append(
                f'<text class="rotulo-aeronave" x="{cx + 7:.2f}" y="{cy - 6:.2f}" '
                f'fill="#fca5a5" font-size="10" font-weight="600">{rotulos[idx]}</text>'
            )
    linhas.append('</g>')

    return "\n".join(linhas)


def gerar_html(frames, parametros):
    """Devolve o conteúdo completo de `relatorio.html` com JSON embutido (sem fetch)."""
    n = parametros["aeronaves"]
    area = float(parametros["area"])
    d_seguro = float(parametros["d_seguro"])
    largura = max(3, len(str(max(0, n - 1))))
    rotulos = [rotulo(i, largura) for i in range(n)]

    # Seleciona o primeiro frame com conflito para exibição imediata ao abrir do disco
    frame_inicial = next(( idx for idx, f in enumerate(frames) if f["conflitos"] ), 0)

    dados_json = {
        "parametros": parametros,
        "rotulos": rotulos,
        "frame_inicial": frame_inicial,
        "frames": [
            {
                "frame": f["frame"],
                "posicoes": [[round(x, 4), round(y, 4)] for x, y in f["posicoes"]],
                "conflitos": [[i, j, round(d, 4)] for i, j, d in f["conflitos"]],
            }
            for f in frames
        ],
    }

    json_embutido = json.dumps(dados_json, ensure_ascii=False, separators=(",", ":"))
    svg_inicial = _montar_svg_estatico(frames[frame_inicial], area, d_seguro, rotulos)

    total_eventos = sum(len(f["conflitos"]) for f in frames)
    frames_com_conflito = sum(1 for f in frames if f["conflitos"])
    distancias = [d for f in frames for _, _, d in f["conflitos"]]
    menor_dist_str = f"{min(distancias):.3f} NM" if distancias else "—"

    linhas_tabela_inicial = []
    for i, j, d in frames[frame_inicial]["conflitos"]:
        linhas_tabela_inicial.append(
            f"<tr><td><code>{rotulos[i]}</code> — <code>{rotulos[j]}</code></td>"
            f"<td class=\"num perigo\">{d:.3f} NM</td></tr>"
        )
    if not linhas_tabela_inicial:
        linhas_tabela_inicial.append(
            '<tr><td colspan="2" class="vazio">Nenhum conflito neste frame.</td></tr>'
        )
    tabela_inicial_html = "\n".join(linhas_tabela_inicial)

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Relatório de Conflitos de Separação (NM)</title>
<style>
  :root {{
    color-scheme: dark;
    --bg: #0b1120;
    --panel: #111827;
    --border: #1f2937;
    --text: #e5e7eb;
    --muted: #9ca3af;
    --accent: #38bdf8;
    --danger: #ef4444;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    padding: 20px;
    font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
    background: var(--bg);
    color: var(--text);
  }}
  header {{
    max-width: 1200px;
    margin: 0 auto 16px auto;
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    align-items: baseline;
    gap: 12px;
    border-bottom: 1px solid var(--border);
    padding-bottom: 12px;
  }}
  header h1 {{
    margin: 0;
    font-size: 1.35rem;
  }}
  .meta {{
    font-size: 0.9rem;
    color: var(--muted);
  }}
  .layout {{
    max-width: 1200px;
    margin: 0 auto;
    display: grid;
    grid-template-columns: minmax(340px, 690px) minmax(280px, 1fr);
    gap: 20px;
    align-items: start;
  }}
  @media (max-width: 900px) {{
    .layout {{ grid-template-columns: 1fr; }}
  }}
  .card {{
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 16px;
  }}
  .svg-wrap {{
    width: 100%;
    aspect-ratio: 1 / 1;
    max-width: 685px;
    margin: 0 auto;
  }}
  svg {{
    width: 100%;
    height: 100%;
    display: block;
    user-select: none;
  }}
  .controles {{
    margin-top: 12px;
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px;
  }}
  button, select {{
    background: #1e293b;
    color: var(--text);
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 6px 11px;
    font-size: 0.88rem;
    cursor: pointer;
  }}
  button:hover {{ background: #334155; }}
  input[type="range"] {{
    flex: 1;
    min-width: 140px;
    accent-color: var(--accent);
  }}
  .legenda {{
    margin-top: 10px;
    display: flex;
    flex-wrap: wrap;
    gap: 16px;
    font-size: 0.85rem;
    color: var(--muted);
  }}
  .legenda span {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
  }}
  .bolinha {{
    width: 10px;
    height: 10px;
    border-radius: 50%;
    display: inline-block;
  }}
  .traco-vermelho {{
    width: 18px;
    height: 3px;
    background: var(--danger);
    display: inline-block;
  }}
  .resumo-grid {{
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
    margin-bottom: 14px;
  }}
  .kpi {{
    background: #0f172a;
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 10px 12px;
  }}
  .kpi .rotulo {{
    font-size: 0.78rem;
    color: var(--muted);
  }}
  .kpi .valor {{
    font-size: 1.15rem;
    font-weight: 700;
    margin-top: 2px;
  }}
  .perigo {{ color: #f87171; font-weight: 600; }}
  h2 {{
    margin: 10px 0 8px 0;
    font-size: 1rem;
  }}
  .tabela-container {{
    max-height: 360px;
    overflow-y: auto;
    border: 1px solid var(--border);
    border-radius: 8px;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 0.88rem;
  }}
  th, td {{
    padding: 7px 10px;
    text-align: left;
    border-bottom: 1px solid var(--border);
  }}
  th {{
    background: #0f172a;
    color: var(--muted);
    position: sticky;
    top: 0;
  }}
  td.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
  td.vazio {{ text-align: center; color: var(--muted); padding: 16px; }}
</style>
</head>
<body>
<header>
  <h1>Detector de Conflitos de Separação em Espaço Aéreo</h1>
  <div class="meta">
    Aeronaves: <strong>{n}</strong> |
    Área: <strong>{area:g} × {area:g} NM</strong> |
    Separação mínima (d_seguro): <strong>{d_seguro:g} NM</strong> |
    Frames: <strong>{len(frames)}</strong>
  </div>
</header>

<main class="layout">
  <section class="card">
    <div class="svg-wrap">
      <svg id="plano-svg" viewBox="0 0 695 690" aria-label="Plano de espaço aéreo em milhas náuticas (NM)">
{svg_inicial}
      </svg>
    </div>

    <div class="controles">
      <button type="button" id="btn-play">▶ Reproduzir</button>
      <button type="button" id="btn-prev" title="Frame anterior">⏮</button>
      <button type="button" id="btn-next" title="Próximo frame">⏭</button>
      <button type="button" id="btn-conflito" title="Ir para o próximo frame com conflito">⚠ Próx. conflito</button>
      <input type="range" id="slider-frame" min="0" max="{max(0, len(frames) - 1)}" value="{frame_inicial}" />
      <label for="sel-fps" class="meta">Velocidade:</label>
      <select id="sel-fps">
        <option value="2">2 fps</option>
        <option value="6" selected>6 fps</option>
        <option value="12">12 fps</option>
        <option value="24">24 fps</option>
      </select>
    </div>

    <div class="legenda">
      <span><i class="bolinha" style="background:#38bdf8"></i> Aeronave segura (&ge; {d_seguro:g} NM)</span>
      <span><i class="bolinha" style="background:#ef4444"></i> Aeronave em conflito (&lt; {d_seguro:g} NM)</span>
      <span><i class="traco-vermelho"></i> Linha vermelha: par em violação de separação</span>
    </div>
  </section>

  <aside class="card">
    <div class="resumo-grid">
      <div class="kpi">
        <div class="rotulo">Frame exibido</div>
        <div class="valor" id="kpi-frame">{frame_inicial} / {max(0, len(frames) - 1)}</div>
      </div>
      <div class="kpi">
        <div class="rotulo">Pares em conflito no frame</div>
        <div class="valor perigo" id="kpi-conflitos-frame">{len(frames[frame_inicial]["conflitos"])}</div>
      </div>
      <div class="kpi">
        <div class="rotulo">Frames com conflito (total)</div>
        <div class="valor">{frames_com_conflito} de {len(frames)}</div>
      </div>
      <div class="kpi">
        <div class="rotulo">Menor distância global</div>
        <div class="valor">{menor_dist_str}</div>
      </div>
    </div>

    <h2>Pares em conflito neste frame (&lt; {d_seguro:g} NM)</h2>
    <div class="tabela-container">
      <table>
        <thead>
          <tr>
            <th>Par de aeronaves</th>
            <th style="text-align:right">Distância (NM)</th>
          </tr>
        </thead>
        <tbody id="corpo-conflitos">
{tabela_inicial_html}
        </tbody>
      </table>
    </div>
    <p class="meta" style="margin-top:12px">
      Total acumulado na simulação: <strong>{total_eventos}</strong> ocorrências de conflito.
      Dados JSON embutidos diretamente no arquivo (abre direto do disco).
    </p>
  </aside>
</main>

<script id="dados-json" type="application/json">{json_embutido}</script>
<script>
const DADOS = {json_embutido};

(function() {{
  const area = DADOS.parametros.area;
  const dSeguro = DADOS.parametros.d_seguro;
  const rotulos = DADOS.rotulos;
  const frames = DADOS.frames;
  const margemEsq = 65.0;
  const margemTopo = 30.0;
  const tamanhoPlot = 600.0;
  const baseY = margemTopo + tamanhoPlot;

  const camadaConflitos = document.getElementById("camada-conflitos");
  const camadaAeronaves = document.getElementById("camada-aeronaves");
  const kpiFrame = document.getElementById("kpi-frame");
  const kpiConflitos = document.getElementById("kpi-conflitos-frame");
  const corpoConflitos = document.getElementById("corpo-conflitos");
  const slider = document.getElementById("slider-frame");
  const btnPlay = document.getElementById("btn-play");
  const btnPrev = document.getElementById("btn-prev");
  const btnNext = document.getElementById("btn-next");
  const btnConflito = document.getElementById("btn-conflito");
  const selFps = document.getElementById("sel-fps");

  let indiceAtual = DADOS.frame_inicial || 0;
  let timer = null;

  function sx(x) {{ return margemEsq + (x / area) * tamanhoPlot; }}
  function sy(y) {{ return baseY - (y / area) * tamanhoPlot; }}

  function renderizarFrame(idx) {{
    indiceAtual = (idx + frames.length) % frames.length;
    slider.value = String(indiceAtual);

    const f = frames[indiceAtual];
    const posicoes = f.posicoes;
    const conflitos = f.conflitos;
    const emRisco = new Set();

    let htmlLinhas = "";
    let htmlTabela = "";

    for (let k = 0; k < conflitos.length; k++) {{
      const i = conflitos[k][0];
      const j = conflitos[k][1];
      const d = conflitos[k][2];
      emRisco.add(i);
      emRisco.add(j);

      const x1 = sx(posicoes[i][0]).toFixed(2);
      const y1 = sy(posicoes[i][1]).toFixed(2);
      const x2 = sx(posicoes[j][0]).toFixed(2);
      const y2 = sy(posicoes[j][1]).toFixed(2);
      const dFmt = d.toFixed(3);

      htmlLinhas += `<line class="conflito-linha" data-par="${{rotulos[i]}}-${{rotulos[j]}}" `
        + `x1="${{x1}}" y1="${{y1}}" x2="${{x2}}" y2="${{y2}}" `
        + `stroke="#ef4444" stroke-width="2.4" stroke-linecap="round">`
        + `<title>${{rotulos[i]}} - ${{rotulos[j]}}: ${{dFmt}} NM (&lt; ${{dSeguro}} NM)</title></line>`;

      htmlTabela += `<tr><td><code>${{rotulos[i]}}</code> — <code>${{rotulos[j]}}</code></td>`
        + `<td class="num perigo">${{dFmt}} NM</td></tr>`;
    }}

    if (!htmlTabela) {{
      htmlTabela = '<tr><td colspan="2" class="vazio">Nenhum conflito neste frame.</td></tr>';
    }}

    let htmlPontos = "";
    for (let idxP = 0; idxP < posicoes.length; idxP++) {{
      const x = posicoes[idxP][0];
      const y = posicoes[idxP][1];
      const cx = sx(x).toFixed(2);
      const cy = sy(y).toFixed(2);
      const conflito = emRisco.has(idxP);
      const cor = conflito ? "#ef4444" : "#38bdf8";
      const raio = conflito ? "5.0" : "3.8";
      const classe = conflito ? "aeronave em-conflito" : "aeronave segura";

      htmlPontos += `<circle class="${{classe}}" data-id="${{rotulos[idxP]}}" `
        + `cx="${{cx}}" cy="${{cy}}" r="${{raio}}" fill="${{cor}}" stroke="#0f172a" stroke-width="1.2">`
        + `<title>${{rotulos[idxP]}} (${{x.toFixed(2)}} NM, ${{y.toFixed(2)}} NM)</title></circle>`;

      if (conflito) {{
        htmlPontos += `<text class="rotulo-aeronave" x="${{(parseFloat(cx) + 7).toFixed(2)}}" `
          + `y="${{(parseFloat(cy) - 6).toFixed(2)}}" fill="#fca5a5" font-size="10" font-weight="600">${{rotulos[idxP]}}</text>`;
      }}
    }}

    camadaConflitos.innerHTML = htmlLinhas;
    camadaAeronaves.innerHTML = htmlPontos;
    kpiFrame.textContent = `${{f.frame}} / ${{frames.length - 1}}`;
    kpiConflitos.textContent = String(conflitos.length);
    corpoConflitos.innerHTML = htmlTabela;
  }}

  function pausar() {{
    if (timer !== null) {{
      clearInterval(timer);
      timer = null;
      btnPlay.textContent = "▶ Reproduzir";
    }}
  }}

  function reproduzir() {{
    pausar();
    const fps = parseInt(selFps.value, 10) || 6;
    btnPlay.textContent = "⏸ Pausar";
    timer = setInterval(function() {{
      renderizarFrame(indiceAtual + 1);
    }}, Math.round(1000 / fps));
  }}

  btnPlay.addEventListener("click", function() {{
    if (timer !== null) pausar(); else reproduzir();
  }});
  btnPrev.addEventListener("click", function() {{
    pausar();
    renderizarFrame(indiceAtual - 1);
  }});
  btnNext.addEventListener("click", function() {{
    pausar();
    renderizarFrame(indiceAtual + 1);
  }});
  btnConflito.addEventListener("click", function() {{
    pausar();
    for (let passo = 1; passo <= frames.length; passo++) {{
      const candidato = (indiceAtual + passo) % frames.length;
      if (frames[candidato].conflitos.length > 0) {{
        renderizarFrame(candidato);
        return;
      }}
    }}
  }});
  slider.addEventListener("input", function() {{
    pausar();
    renderizarFrame(parseInt(slider.value, 10) || 0);
  }});
  selFps.addEventListener("change", function() {{
    if (timer !== null) reproduzir();
  }});

  renderizarFrame(indiceAtual);
}})();
</script>
</body>
</html>
"""


def escrever_html(caminho, frames, parametros):
    """Escreve o arquivo HTML autossuficiente com visualização SVG e JSON embutido."""
    pasta = os.path.dirname(caminho)
    if pasta:
        os.makedirs(pasta, exist_ok=True)
    conteudo = gerar_html(frames, parametros)
    with open(caminho, "w", encoding="utf-8") as arq:
        arq.write(conteudo)


# ---------------------------------------------------------------------------
# Linha de comando
# ---------------------------------------------------------------------------

def ler_argumentos(argv=None):
    p = argparse.ArgumentParser(description="Simulação de aeronaves, log e visualização HTML/SVG.")
    p.add_argument("-n", "--aeronaves", type=int, default=80, help="número de aeronaves (padrão: 80)")
    p.add_argument("-t", "--frames", type=int, default=120, help="número de frames (padrão: 120)")
    p.add_argument("--area", type=float, default=200.0, help="lado do quadrado em NM (padrão: 200)")
    p.add_argument("--d-seguro", type=float, default=5.0, help="separação mínima em NM (padrão: 5)")
    p.add_argument("--vel-max", type=float, default=3.0, help="velocidade máxima em NM/frame (padrão: 3)")
    p.add_argument("--semente", type=int, default=42, help="semente aleatória (padrão: 42)")
    p.add_argument("--saida", default=os.path.join("saida", "log.txt"), help="caminho do log")
    p.add_argument("--html", default=None, help="caminho do relatório HTML (padrão: saida/relatorio.html)")
    p.add_argument("--sem-verificacao", action="store_true",
                   help="não conferir com a força bruta (útil para n muito grande)")
    args = p.parse_args(argv)

    if args.html is None:
        pasta_saida = os.path.dirname(args.saida)
        args.html = os.path.join(pasta_saida, "relatorio.html") if pasta_saida else "relatorio.html"

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
    escrever_html(args.html, frames, parametros)

    eventos = sum(len(f["conflitos"]) for f in frames)
    com_conflito = sum(1 for f in frames if f["conflitos"])
    print(f"Log escrito em {args.saida}")
    print(f"Relatório HTML escrito em {args.html}")
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
