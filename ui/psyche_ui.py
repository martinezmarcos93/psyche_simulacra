"""
Interfaz NiceGUI de PSYCHE SIMULACRA.

Página /        — Launcher: estado del checkpoint + botones de inicio.
Página /monitor — Monitoreo en tiempo real: mapa, stats, gráficos, agentes,
                  red social cuántica, sueños, civilización.

Doctrinas:
  B — la sim existe sin observers. La UI nunca modifica el mundo.
  C — interfaz epistemológica: observar, no controlar.
"""
from __future__ import annotations

import math
import subprocess
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).parent.parent

# ── Paleta ────────────────────────────────────────────────────────────────────

_BIOME_COLORS: dict[str, str] = {
    # Nombres reales de terrain.py / hexagon.py
    "bosque_templado":  "#1f6b1f",
    "pradera_humeda":   "#5a8a3c",
    "rio_lago":         "#2471a3",
    "montana_alta":     "#9e9e9e",
    "sabana_abierta":   "#c8a040",
    "pantano_costero":  "#3d6b5a",
    "cueva":            "#3a3a4a",
    "valle_fertil":     "#27ae60",
    "costa_abierta":    "#3d7aad",
    "desierto_borde":   "#d4a040",
    "colinas_suaves":   "#7a9050",
    "lago_interior":    "#1a5280",
}
_DEFAULT_BIOME = "#4a3a6a"  # púrpura oscuro para biomas no reconocidos
_HEX_SIZE      = 8.0

_ARCH_COLORS: dict[str, str] = {
    "self_":        "#ffffff",
    "persona":      "#88aaff",
    "sombra":       "#FF4B4B",
    "anima_animus": "#E040FB",
    "heroe":        "#00D2B4",
    "sabio":        "#F4D03F",
    "trickster":    "#FF9F43",
    "madre":        "#ff69b4",
    "padre":        "#4a9eff",
    "nino_divino":  "#2ecc71",
    "gobernante":   "#8e44ad",
    "rebelde":      "#e74c3c",
}

_PROCESO_COLORS: dict[str, str] = {
    "integracion_parcial": "#00D2B4",
    "amplificacion": "#F4D03F",
    "compensacion": "#E040FB",
    "proyeccion": "#FF9F43",
}

_TECH_LABELS: dict[str, str] = {
    "conservacion_agua":  "Conservación del agua",
    "fuego_ritual":       "Fuego ritual",
    "curacion":           "Curación",
    "tecnica_constructiva": "Técnica constructiva",
    "caza_avanzada":      "Caza avanzada",
    "navegacion":         "Navegación",
    "alquimia_vegetal":   "Alquimia vegetal",
}

_STRUCT_COLORS: dict[str, str] = {
    "activo": "#2ecc71", "abandonado": "#f39c12", "ruina": "#e74c3c",
}


# ── Helpers geométricos ───────────────────────────────────────────────────────

def _hex_xy(q: int, r: int) -> tuple[float, float]:
    return _HEX_SIZE * 1.5 * q, _HEX_SIZE * math.sqrt(3) * (r + 0.5 * (q & 1))


def _extract_terrain(runner) -> dict[tuple[int, int], str]:
    try:
        return {coord: cell.biome for coord, cell in runner.world.terrain._cells.items()}
    except Exception as e:
        import sys
        print(f"[UI] _extract_terrain: {e}", file=sys.stderr)
        return {}


def _extract_agents_data(runner) -> list[dict]:
    """Lee posición y metadata de todos los agentes en vivo para el mapa."""
    import sys
    try:
        ac  = runner.agents
        mgr = ac.tribe_manager
    except Exception as e:
        print(f"[UI] _extract_agents_data setup: {e}", file=sys.stderr)
        return []
    out = []
    for agent_id, agent in list(ac.agents.items()):
        try:
            bs    = agent.behavioral_state
            estado = (
                bs.estado.value if hasattr(bs, "estado") and hasattr(bs.estado, "value")
                else str(bs)
            )
            arch = agent.archetypes.dominant()
            pos  = agent.posicion
            if not isinstance(pos, (tuple, list)) or len(pos) != 2:
                continue
            out.append({
                "id":        agent_id,
                "nombre":    agent.nombre,
                "pos":       tuple(pos),
                "alive":     agent.is_alive,
                "humor":     round(agent.humor, 2),
                "edad":      getattr(agent, "edad", 0),
                "arquetipo": arch,
                "estado":    estado,
                "tribu":     mgr.get_tribe_id(agent_id) or "",
            })
        except Exception as e:
            print(f"[UI] agent {agent_id}: {e}", file=sys.stderr)
    return out


# ── Spring layout (Fruchterman-Reingold) ─────────────────────────────────────

def _fruchterman_reingold(
    positions: dict[str, list[float]],
    adjacency: dict[str, dict[str, float]],
    iterations: int = 60,
    area: float = 4.0,
) -> dict[str, tuple[float, float]]:
    """
    Layout spring para la red social. O(n²) por iteración — OK con ~100 nodos.
    adjacency[u][v] = peso del lazo (bond_strength absoluto).
    """
    pos   = {n: list(p) for n, p in positions.items()}
    nodes = list(pos.keys())
    n     = len(nodes)
    if n < 2:
        return {nd: tuple(pos[nd]) for nd in nodes}

    k = math.sqrt(area / max(n, 1))

    for step in range(iterations):
        disp = {nd: [0.0, 0.0] for nd in nodes}

        # Fuerzas repulsivas (todos contra todos)
        for i in range(n):
            for j in range(i + 1, n):
                u, v = nodes[i], nodes[j]
                dx = pos[u][0] - pos[v][0]
                dy = pos[u][1] - pos[v][1]
                d  = math.sqrt(dx * dx + dy * dy) + 1e-6
                f  = k * k / d
                ux, uy = (dx / d) * f, (dy / d) * f
                disp[u][0] += ux; disp[u][1] += uy
                disp[v][0] -= ux; disp[v][1] -= uy

        # Fuerzas atractivas (solo aristas)
        for u, neighbors in adjacency.items():
            for v, w in neighbors.items():
                if u not in pos or v not in pos:
                    continue
                dx = pos[u][0] - pos[v][0]
                dy = pos[u][1] - pos[v][1]
                d  = math.sqrt(dx * dx + dy * dy) + 1e-6
                f  = (d * d / k) * max(abs(w), 0.1)
                fx, fy = (dx / d) * f, (dy / d) * f
                disp[u][0] -= fx; disp[u][1] -= fy
                disp[v][0] += fx; disp[v][1] += fy

        # Actualizar con temperatura decreciente
        t = area * (1.0 - step / iterations)
        for nd in nodes:
            d0, d1 = disp[nd]
            dist   = math.sqrt(d0 * d0 + d1 * d1) + 1e-6
            move   = min(dist, t)
            pos[nd][0] += (d0 / dist) * move
            pos[nd][1] += (d1 / dist) * move

    return {nd: (pos[nd][0], pos[nd][1]) for nd in nodes}


def _social_stats(alive: dict, live_edges: list[dict]) -> dict:
    """
    Calcula estadísticas de red (C3):
    clusters, hub, grado máximo, pares entrelazados.
    """
    import collections

    degree: dict[str, int] = collections.Counter()
    adj: dict[str, set] = {aid: set() for aid in alive}
    n_ent = 0

    for e in live_edges:
        u, v = e.get("u", ""), e.get("v", "")
        if u not in alive or v not in alive:
            continue
        bs = e.get("bond_strength", 0.0)
        if abs(bs) > 0.1:
            degree[u] += 1
            degree[v] += 1
            adj[u].add(v)
            adj[v].add(u)
        if e.get("entangled"):
            n_ent += 1

    # BFS para componentes conectados
    visited: set = set()
    n_clusters = 0
    for start in alive:
        if start in visited:
            continue
        n_clusters += 1
        queue = [start]
        while queue:
            cur = queue.pop()
            if cur in visited:
                continue
            visited.add(cur)
            for nb in adj.get(cur, []):
                if nb not in visited:
                    queue.append(nb)

    hub_id  = degree.most_common(1)[0][0] if degree else None
    hub_deg = degree[hub_id] if hub_id else 0
    hub_nom = alive[hub_id].get("nombre", hub_id) if hub_id and hub_id in alive else "—"

    n_active_edges = sum(1 for e in live_edges
                         if abs(e.get("bond_strength", 0.0)) > 0.1
                         and e.get("u", "") in alive and e.get("v", "") in alive)

    return {
        "n_nodos":       len(alive),
        "n_aristas":     n_active_edges,
        "n_clusters":    n_clusters,
        "hub":           hub_nom,
        "hub_grado":     hub_deg,
        "n_entrelazados": n_ent,
    }


def _render_edge_table_html(
    alive: dict,           # {id: agent_dict}
    edges: list[dict],
    a2t: dict[str, str],   # agent_id → tribe_id
    tribe_filter: str = "",
    top_n: int = 20,
) -> str:
    """
    Tabla HTML de las top_n aristas más fuertes (C2).
    tribe_filter: si no vacío, solo muestra aristas donde al menos un agente es de esa tribu.
    """
    live = []
    for e in edges:
        u, v = e.get("u", ""), e.get("v", "")
        if u not in alive or v not in alive:
            continue
        if tribe_filter and a2t.get(u) != tribe_filter and a2t.get(v) != tribe_filter:
            continue
        live.append(e)

    live.sort(key=lambda e: -abs(e.get("bond_strength", 0.0)))
    live = live[:top_n]

    if not live:
        return "<span style='color:#666'>Sin aristas para este filtro.</span>"

    rows = []
    for e in live:
        u, v   = e["u"], e["v"]
        an, bn = alive[u].get("nombre","?"), alive[v].get("nombre","?")
        bs     = e.get("bond_strength", 0.0)
        intim  = e.get("intimacy", 0.0)
        res    = e.get("resonance", 0.0)
        ent    = "⚛" if e.get("entangled") else "·"
        bs_col = "#FF4B4B" if bs < 0 else "#00D2B4"
        rows.append(
            f"<tr>"
            f"<td style='color:#ddd;padding:3px 8px'>{an}</td>"
            f"<td style='color:#ddd;padding:3px 8px'>{bn}</td>"
            f"<td style='color:{bs_col};padding:3px 8px;text-align:right'>{bs:+.3f}</td>"
            f"<td style='color:#aaa;padding:3px 8px;text-align:right'>{intim:.2f}</td>"
            f"<td style='color:#aaa;padding:3px 8px;text-align:right'>{res:.2f}</td>"
            f"<td style='color:#E040FB;padding:3px 8px;text-align:center'>{ent}</td>"
            f"</tr>"
        )

    header = (
        "<table style='width:100%;border-collapse:collapse;font-size:11px'>"
        "<thead><tr style='border-bottom:1px solid #333'>"
        "<th style='color:#888;text-align:left;padding:4px 8px'>Agente A</th>"
        "<th style='color:#888;text-align:left;padding:4px 8px'>Agente B</th>"
        "<th style='color:#888;text-align:right;padding:4px 8px'>Bond</th>"
        "<th style='color:#888;text-align:right;padding:4px 8px'>Intimidad</th>"
        "<th style='color:#888;text-align:right;padding:4px 8px'>Resonancia</th>"
        "<th style='color:#888;text-align:center;padding:4px 8px'>Ent.</th>"
        "</tr></thead><tbody>"
    )
    return header + "".join(rows) + "</tbody></table>"


# ── Figuras Plotly ────────────────────────────────────────────────────────────

def _build_hex_map(
    snap,
    terrain_biomes: dict,
    agents_data: list | None = None,
    layer_flags: dict | None = None,
    explored_coords: frozenset | None = None,
) -> "go.Figure | None":
    """
    Mapa hexagonal completo (D1/D2/D3):
      D1 — todo el terreno 80×60: niebla de guerra para inexplorados, bioma completo para explorados
      D2 — capa de agentes coloreados por arquetipo dominante
      D3 — visibilidad de capas controlada por layer_flags
    """
    try:
        import plotly.graph_objects as go
    except ImportError:
        return None

    if snap is None or not terrain_biomes:
        return None

    flags = layer_flags or {}
    def _vis(key: str, default: bool = True) -> bool:
        return bool(flags.get(key, default))

    # Usar terrain._explored_set si se proporcionó (más completo que recursos_por_hex)
    if explored_coords is not None:
        explored = explored_coords
    else:
        explored = set((snap.recursos_por_hex or {}).keys())

    # ── D1a: Niebla de guerra (hexes no explorados) ─────────────────────────
    fog_xs, fog_ys = [], []
    exp_xs, exp_ys, exp_colors, exp_texts = [], [], [], []

    for coord, biome in terrain_biomes.items():
        x, y = _hex_xy(*coord)
        if coord in explored:
            exp_xs.append(x); exp_ys.append(y)
            exp_colors.append(_BIOME_COLORS.get(biome, _DEFAULT_BIOME))
            exp_texts.append(f"({coord[0]},{coord[1]}) {biome}")
        else:
            fog_xs.append(x); fog_ys.append(y)

    traces: list = []

    if fog_xs:
        traces.append(go.Scattergl(
            x=fog_xs, y=fog_ys, mode="markers",
            marker=dict(symbol="circle", size=13, color="#0d0520", opacity=0.90,
                        line=dict(width=0)),
            hoverinfo="skip", name="Niebla",
            visible=_vis("niebla"),
        ))

    # ── D1b: Terreno explorado ───────────────────────────────────────────────
    if exp_xs:
        traces.append(go.Scattergl(
            x=exp_xs, y=exp_ys, mode="markers",
            marker=dict(symbol="circle", size=17, color=exp_colors, line=dict(width=0)),
            text=exp_texts, hoverinfo="text", name="Terreno explorado",
            visible=True,
        ))

    # ── Hexes liminales ──────────────────────────────────────────────────────
    lim_xs, lim_ys, lim_t = [], [], []
    for lh in (getattr(snap, "liminal_hexes", None) or []):
        q, r = lh["coord"]
        x, y = _hex_xy(q, r)
        lim_xs.append(x); lim_ys.append(y)
        lim_t.append(f"Liminal ({q},{r})<br>{', '.join(lh.get('symbol_pool', []))}")
    if lim_xs:
        traces.append(go.Scattergl(
            x=lim_xs, y=lim_ys, mode="markers",
            marker=dict(symbol="circle-open", size=16, color="#9b59b6", line=dict(width=2)),
            text=lim_t, hoverinfo="text", name="Liminal",
            visible=_vis("liminales"),
        ))

    # ── Tumbas ───────────────────────────────────────────────────────────────
    gx, gy = [], []
    for g in (getattr(snap, "graves_activos", None) or []):
        coord_g = g[0] if isinstance(g, (list, tuple)) else None
        if coord_g:
            x, y = _hex_xy(*coord_g); gx.append(x); gy.append(y)
    if gx:
        traces.append(go.Scattergl(
            x=gx, y=gy, mode="markers",
            marker=dict(symbol="star", size=12, color="#bdc3c7"),
            name="Tumbas", hoverinfo="skip",
            visible=_vis("tumbas"),
        ))

    # ── Fauna simbólica ──────────────────────────────────────────────────────
    fx, fy, ft = [], [], []
    for f in (getattr(snap, "fauna_simbolica", None) or []):
        coord_f = f.get("coord")
        if coord_f:
            x, y = _hex_xy(*coord_f); fx.append(x); fy.append(y)
            ft.append(f.get("nombre", "bestia"))
    if fx:
        traces.append(go.Scattergl(
            x=fx, y=fy, mode="markers",
            marker=dict(symbol="triangle-up", size=14, color="#f39c12"),
            text=ft, hoverinfo="text", name="Fauna",
            visible=_vis("fauna"),
        ))

    # ── Fuego ────────────────────────────────────────────────────────────────
    if getattr(snap, "fuego_activo", False) and getattr(snap, "fuego_coord", None):
        x, y = _hex_xy(*snap.fuego_coord)
        traces.append(go.Scattergl(
            x=[x], y=[y], mode="markers",
            marker=dict(symbol="circle", size=22, color="#e74c3c", opacity=0.9),
            name="Fuego", hoverinfo="skip",
            visible=_vis("fuego"),
        ))

    # ── D2: Agentes vivos ────────────────────────────────────────────────────
    if agents_data and _vis("agentes"):
        # Agrupa por arquetipo para una sola leyenda por arquetipo
        by_arch: dict[str, list] = {}
        dead_ax, dead_ay, dead_at = [], [], []
        for a in agents_data:
            if not a["alive"]:
                if _vis("muertos"):
                    x, y = _hex_xy(*a["pos"])
                    dead_ax.append(x); dead_ay.append(y)
                    dead_at.append(f"✝ {a['nombre']} ({a['tribu']})")
                continue
            arch  = a["arquetipo"]
            entry = by_arch.setdefault(arch, {"xs": [], "ys": [], "texts": []})
            x, y  = _hex_xy(*a["pos"])
            entry["xs"].append(x); entry["ys"].append(y)
            entry["texts"].append(
                f"<b>{a['nombre']}</b><br>Tribu: {a['tribu']}<br>"
                f"Arquetipo: {arch}<br>Humor: {a['humor']}<br>"
                f"Edad: {a['edad']}  Estado: {a['estado']}"
            )

        for arch, data in by_arch.items():
            color = _ARCH_COLORS.get(arch, "#cccccc")
            traces.append(go.Scattergl(
                x=data["xs"], y=data["ys"], mode="markers",
                marker=dict(symbol="circle", size=14, color=color,
                            line=dict(width=2.0, color="#000000")),
                text=data["texts"], hoverinfo="text",
                name=f"↑ {arch}", legendgroup="agentes",
                visible=True,
            ))

        if dead_ax:
            traces.append(go.Scattergl(
                x=dead_ax, y=dead_ay, mode="markers",
                marker=dict(symbol="x-thin-open", size=8, color="#666677",
                            line=dict(width=1.5)),
                text=dead_at, hoverinfo="text",
                name="Muertos", legendgroup="agentes",
                visible=_vis("muertos"),
            ))

    n_exp = len(explored)
    n_tot = len(terrain_biomes)
    fig = go.Figure(data=traces)
    fig.update_layout(
        paper_bgcolor="#1a0a2e", plot_bgcolor="#1a0a2e",
        showlegend=True,
        legend=dict(font=dict(color="#ccc", size=10), bgcolor="rgba(0,0,0,0.5)",
                    itemsizing="constant"),
        margin=dict(l=0, r=0, t=24, b=0),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False,
                   scaleanchor="y", scaleratio=1),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        title=dict(
            text=f"{n_exp}/{n_tot} hexes explorados ({100*n_exp//max(n_tot,1)}%)",
            font=dict(color="#888", size=11),
        ),
        dragmode="pan",
        uirevision="map",
    )
    return fig


_TREND_COLORS = ["#00D2B4", "#E040FB", "#FF4B4B", "#F4D03F", "#4a9eff"]

_EVENT_COLORS: dict[str, str] = {
    "tormenta":    "rgba(74,158,255,0.25)",
    "helada":      "rgba(174,214,241,0.25)",
    "sequia":      "rgba(241,196,15,0.25)",
    "granizo":     "rgba(174,214,241,0.20)",
    "ola_calor":   "rgba(231,76,60,0.25)",
    "inundacion":  "rgba(41,128,185,0.25)",
}
_EVENT_DEFAULT_COLOR = "rgba(155,89,182,0.20)"


def _build_trend_figure(
    rows: list[dict],
    fields: list[str],
    title: str,
    yrange: list | None = None,
    events: list[dict] | None = None,
):
    """
    Gráfico de líneas temporales.
    A1: events=[{dia, evento}] → bandas verticales coloreadas por tipo de evento.
    """
    try:
        import plotly.graph_objects as go
    except ImportError:
        return None
    if not rows:
        return None

    dias = [r["dia"] for r in rows]
    traces = []
    for i, f in enumerate(fields):
        vals = [r.get(f) for r in rows]
        vals = [v if v is not None else 0 for v in vals]
        traces.append(go.Scatter(
            x=dias, y=vals, mode="lines", name=f,
            line=dict(color=_TREND_COLORS[i % len(_TREND_COLORS)], width=2),
        ))

    fig = go.Figure(data=traces)
    yaxis_cfg = dict(color="#aaa", gridcolor="#1f2937")
    if yrange:
        yaxis_cfg["range"] = yrange

    # A1 — Bandas de eventos climáticos
    shapes = []
    event_annotations = []
    if events:
        for ev in events:
            d    = ev.get("dia", 0)
            evnm = (ev.get("evento") or "").lower()
            col  = _EVENT_COLORS.get(evnm, _EVENT_DEFAULT_COLOR)
            shapes.append(dict(
                type="rect", xref="x", yref="paper",
                x0=d - 0.4, x1=d + 0.4, y0=0, y1=1,
                fillcolor=col, line=dict(width=0), layer="below",
            ))
            event_annotations.append(dict(
                x=d, y=1.02, xref="x", yref="paper",
                text=evnm[:3], showarrow=False,
                font=dict(size=7, color="#aaa"), textangle=-45,
            ))

    fig.update_layout(
        title=dict(text=title, font=dict(color="#ccc", size=13)),
        paper_bgcolor="#111827", plot_bgcolor="#111827",
        showlegend=True, legend=dict(font=dict(color="#aaa")),
        margin=dict(l=40, r=10, t=40, b=30),
        xaxis=dict(color="#aaa", gridcolor="#1f2937"),
        yaxis=yaxis_cfg,
        shapes=shapes,
        annotations=event_annotations,
    )
    return fig


def _build_emergence_figure(rows: list[dict]) -> "go.Figure | None":
    """
    A2 — Métricas de emergencia cultural (KL, VFE, IMI) desde emergence_series.csv.
    """
    try:
        import plotly.graph_objects as go
    except ImportError:
        return None
    if not rows:
        return None

    dias     = [r["dia"] for r in rows]
    kl_mean  = [r.get("kl_mean", 0.0)  for r in rows]
    vfe      = [r.get("vfe_global", 0.0) for r in rows]
    imi      = [r.get("imi", 0.0)       for r in rows]

    traces = [
        go.Scatter(x=dias, y=kl_mean, mode="lines", name="KL (div. psicológica)",
                   line=dict(color="#E040FB", width=1.8)),
        go.Scatter(x=dias, y=vfe, mode="lines", name="VFE (entropía colectiva)",
                   line=dict(color="#F4D03F", width=1.8)),
        go.Scatter(x=dias, y=imi, mode="lines", name="IMI (varianza arquetípica)",
                   line=dict(color="#00D2B4", width=1.8)),
    ]

    fig = go.Figure(data=traces)
    fig.update_layout(
        title=dict(text="Métricas de emergencia cultural", font=dict(color="#ccc", size=13)),
        paper_bgcolor="#111827", plot_bgcolor="#111827",
        showlegend=True,
        legend=dict(font=dict(color="#aaa", size=10), orientation="h",
                    yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(l=40, r=10, t=50, b=30),
        xaxis=dict(color="#aaa", gridcolor="#1f2937", title="Día simulado"),
        yaxis=dict(color="#aaa", gridcolor="#1f2937"),
    )
    return fig


_ARCH_DESCRIPTIONS: dict[str, str] = {
    "self_":        "El Sí-mismo — integración psíquica total",
    "persona":      "La Máscara — rol social adoptado",
    "sombra":       "La Sombra — contenido inconsciente reprimido",
    "anima_animus": "Ánima/Ánimus — principio contrasexual",
    "heroe":        "El Héroe — voluntad de superar obstáculos",
    "sabio":        "El Sabio — búsqueda de significado",
    "trickster":    "El Embaucador — caos creativo, transgresión",
    "madre":        "La Gran Madre — nutrición, protección",
    "padre":        "El Padre — autoridad, orden",
    "nino_divino":  "El Niño Divino — potencial, nueva vida",
    "gobernante":   "El Gobernante — control, estabilidad",
    "rebelde":      "El Rebelde — ruptura, revolución",
    "muerte":       "La Muerte — transformación, fin",
    "fuego":        "El Fuego — purificación, energía",
    "agua":         "El Agua — inconsciente, flujo",
}


def _build_icl_gauges(
    emotional_pressure: float,
    myth_pressure: float,
    confusion: float,
) -> "go.Figure | None":
    """B1 — Tres gauges para el estado del campo colectivo."""
    try:
        import plotly.graph_objects as go
    except ImportError:
        return None

    def _gauge_color(v: float) -> str:
        return "#e74c3c" if v > 0.7 else "#f39c12" if v > 0.4 else "#2ecc71"

    fig = go.Figure()
    positions = [
        ("Presión emocional", emotional_pressure, 0.15),
        ("Presión mítica",    myth_pressure,       0.50),
        ("Confusión",         confusion,           0.85),
    ]
    for title, val, x in positions:
        col = _gauge_color(val)
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=round(val, 3),
            domain=dict(x=[x - 0.14, x + 0.14], y=[0, 1]),
            title=dict(text=title, font=dict(color="#ccc", size=11)),
            gauge=dict(
                axis=dict(range=[0, 1], tickcolor="#555", tickfont=dict(size=8, color="#666")),
                bar=dict(color=col),
                bgcolor="#1f2937",
                borderwidth=0,
                steps=[
                    dict(range=[0, 0.4], color="#0f2027"),
                    dict(range=[0.4, 0.7], color="#12263a"),
                    dict(range=[0.7, 1.0], color="#1a1015"),
                ],
                threshold=dict(line=dict(color="#e74c3c", width=2), thickness=0.75, value=0.7),
            ),
            number=dict(font=dict(color=col, size=20)),
        ))

    fig.update_layout(
        paper_bgcolor="#111827",
        height=180,
        margin=dict(l=10, r=10, t=20, b=10),
        annotations=[dict(
            x=0.5, y=-0.08, xref="paper", yref="paper",
            text="Ψ(t) = ∑ Sᵢ(t) × Wᵢ",
            showarrow=False, font=dict(color="#666", size=10),
        )],
    )
    return fig


def _build_symbol_figure(symbols: dict, local_fields: dict | None = None):
    """
    B2 — Carga memética de símbolos.
    Ordenado por carga descendente. Tooltip incluye descripción del arquetipo
    y qué tribu tiene mayor carga si local_fields disponible.
    """
    try:
        import plotly.graph_objects as go
    except ImportError:
        return None
    if not symbols:
        return None

    # Ordenar descendente
    items = sorted(symbols.items(), key=lambda x: -x[1])
    keys   = [k for k, _ in items]
    names  = [k.replace("_", " ").capitalize() for k in keys]
    values = [v for _, v in items]
    colors = [_ARCH_COLORS.get(k, "#888") for k in keys]

    # B2 — Tribu con mayor carga por símbolo
    tooltips = []
    for k, v in items:
        desc = _ARCH_DESCRIPTIONS.get(k, "")
        tip  = f"<b>{k}</b>: {v:.3f}<br>{desc}"
        if local_fields:
            max_tribe = max(
                local_fields.items(),
                key=lambda kv: kv[1].get("symbols", {}).get(k, 0.0),
                default=(None, {}),
            )
            if max_tribe[0]:
                tribe_val = max_tribe[1].get("symbols", {}).get(k, 0.0)
                tip += f"<br>Tribu dominante: {max_tribe[0]} ({tribe_val:.3f})"
        tooltips.append(tip)

    fig = go.Figure(go.Bar(
        x=values, y=names, orientation="h",
        marker=dict(color=colors),
        text=[f"{v:.2f}" for v in values], textposition="outside",
        hovertext=tooltips, hoverinfo="text",
    ))
    fig.update_layout(
        paper_bgcolor="#111827", plot_bgcolor="#111827",
        margin=dict(l=130, r=60, t=10, b=20),
        xaxis=dict(range=[0, 1.15], color="#aaa", gridcolor="#1f2937"),
        yaxis=dict(color="#aaa"),
        showlegend=False,
    )
    return fig


def _render_proto_myths_html(proto_myths: list, active_myths: list) -> str:
    """B3 — Proto-mitos en gestación + mitos activos."""
    parts = []

    if active_myths:
        parts.append("<b style='color:#E040FB'>Mitos activos</b><br>")
        for m in active_myths:
            dia_c = m.get("day_crystallized", m.get("dia_origen", "?"))
            par   = " vs ".join(m.get("par", []))
            coh   = m.get("coherencia", 0.0)
            parts.append(
                f"<div style='margin:4px 0;padding:6px 10px;"
                f"background:rgba(155,89,182,0.15);border-left:3px solid #9b59b6;border-radius:3px'>"
                f"<span style='color:#E040FB'>{m.get('tipo','?')}</span> — "
                f"{par} · coherencia {coh:.2f} · día {dia_c}</div>"
            )
        parts.append("<br>")

    if proto_myths:
        parts.append("<b style='color:#aaa'>Proto-mitos en gestación</b>")
        parts.append(
            "<table style='width:100%;font-size:11px;border-collapse:collapse;margin-top:6px'>"
            "<thead><tr style='border-bottom:1px solid #333'>"
            "<th style='color:#666;text-align:left;padding:3px 8px'>Tipo</th>"
            "<th style='color:#666;text-align:left;padding:3px 8px'>Par</th>"
            "<th style='color:#666;text-align:right;padding:3px 8px'>Coherencia</th>"
            "<th style='color:#666;text-align:right;padding:3px 8px'>Intensidad</th>"
            "<th style='color:#666;text-align:right;padding:3px 8px'>Día</th>"
            "</tr></thead><tbody>"
        )
        for pm in sorted(proto_myths, key=lambda x: -x.get("coherencia", 0)):
            par  = " + ".join(pm.get("par", []))
            coh  = pm.get("coherencia", 0.0)
            intens = pm.get("intensidad_contexto", 0.0)
            dia  = pm.get("dia_origen", "?")
            coh_col = "#E040FB" if coh > 0.5 else "#aaa"
            parts.append(
                f"<tr><td style='color:#ccc;padding:3px 8px'>{pm.get('tipo','?')}</td>"
                f"<td style='color:#aaa;padding:3px 8px'>{par}</td>"
                f"<td style='color:{coh_col};text-align:right;padding:3px 8px'>{coh:.3f}</td>"
                f"<td style='color:#666;text-align:right;padding:3px 8px'>{intens:.2f}</td>"
                f"<td style='color:#555;text-align:right;padding:3px 8px'>{dia}</td></tr>"
            )
        parts.append("</tbody></table>")
    elif not active_myths:
        parts.append("<span style='color:#555'>Sin mitos activos ni proto-mitos registrados.</span>")

    return "".join(parts)


def _build_social_graph(cp: dict) -> "go.Figure | None":
    """
    Red social cuántica (C1):
      - Spring layout Fruchterman-Reingold agrupado por tribu
      - Aristas: verdes (lazo+), rojas (lazo−), púrpura (entrelazado)
      - Nodos vivos coloreados por humor; nodos muertos como X gris
    """
    try:
        import plotly.graph_objects as go
    except ImportError:
        return None

    agents_list = cp.get("agentes", {}).get("agents", [])
    if not agents_list:
        return None

    alive = {a["id"]: a for a in agents_list if a.get("is_alive", False)}
    dead  = {a["id"]: a for a in agents_list if not a.get("is_alive", True)}

    social = cp.get("agentes", {}).get("social_network", {})
    edges  = social.get("edges", [])
    t_data = cp.get("agentes", {}).get("tribe_manager", {})
    a2t    = t_data.get("agent_to_tribe", {})

    if not alive:
        return None

    # ── C1a: Posiciones iniciales agrupadas por tribu ────────────────────────
    tribes: dict[str, list[str]] = {}
    for aid in alive:
        tid = a2t.get(aid, "_sin_tribu")
        tribes.setdefault(tid, []).append(aid)

    tribe_list  = sorted(tribes.keys())
    n_tribes    = max(len(tribe_list), 1)
    tribe_angle = {tid: 2 * math.pi * i / n_tribes for i, tid in enumerate(tribe_list)}

    init_pos: dict[str, list[float]] = {}
    for tid, members in tribes.items():
        cx = 2.5 * math.cos(tribe_angle[tid])
        cy = 2.5 * math.sin(tribe_angle[tid])
        for i, aid in enumerate(members):
            angle = 2 * math.pi * i / max(len(members), 1)
            init_pos[aid] = [cx + 0.5 * math.cos(angle), cy + 0.5 * math.sin(angle)]

    # Construir adjacency para FR (solo aristas entre vivos con bs significativo)
    adjacency: dict[str, dict[str, float]] = {aid: {} for aid in alive}
    for e in edges:
        u, v = e.get("u", ""), e.get("v", "")
        if u not in alive or v not in alive:
            continue
        bs = abs(e.get("bond_strength", 0.0))
        if bs > 0.1:
            adjacency[u][v] = bs
            adjacency[v][u] = bs

    positions = _fruchterman_reingold(init_pos, adjacency, iterations=60)

    # ── Aristas ──────────────────────────────────────────────────────────────
    ex_pos, ey_pos = [], []
    ex_neg, ey_neg = [], []
    ex_ent, ey_ent = [], []

    for e in edges:
        u, v = e.get("u", ""), e.get("v", "")
        if u not in alive or v not in alive:
            continue
        x0, y0 = positions.get(u, (0.0, 0.0))
        x1, y1 = positions.get(v, (0.0, 0.0))
        bs = e.get("bond_strength", 0.0)

        if e.get("entangled"):
            ex_ent.extend([x0, x1, None])
            ey_ent.extend([y0, y1, None])
        elif bs > 0.3:
            ex_pos.extend([x0, x1, None])
            ey_pos.extend([y0, y1, None])
        elif bs < -0.15:
            ex_neg.extend([x0, x1, None])
            ey_neg.extend([y0, y1, None])

    traces = []
    if ex_ent:
        traces.append(go.Scatter(x=ex_ent, y=ey_ent, mode="lines",
            line=dict(color="#E040FB", width=1.5), hoverinfo="skip", name="⚛ Entrelazado"))
    if ex_pos:
        traces.append(go.Scatter(x=ex_pos, y=ey_pos, mode="lines",
            line=dict(color="#00D2B4", width=0.5, dash="solid"),
            hoverinfo="skip", name="Lazo ＋"))
    if ex_neg:
        traces.append(go.Scatter(x=ex_neg, y=ey_neg, mode="lines",
            line=dict(color="#FF4B4B", width=0.5),
            hoverinfo="skip", name="Lazo −"))

    # ── Nodos muertos como X pequeña ─────────────────────────────────────────
    dx_list, dy_list, dead_t = [], [], []
    for aid, ag in dead.items():
        pos = positions.get(aid)
        if pos:
            dx_list.append(pos[0]); dy_list.append(pos[1])
            dead_t.append(f"✝ {ag['nombre']}")
    if dx_list:
        traces.append(go.Scatter(
            x=dx_list, y=dy_list, mode="markers",
            marker=dict(symbol="x-thin-open", size=7, color="#555566",
                        line=dict(width=1.2)),
            text=dead_t, hoverinfo="text", name="Muertos",
        ))

    # ── Nodos vivos coloreados por humor + tribu en tooltip ──────────────────
    # Un trace por tribu para color de borde diferenciado
    tribe_node_x: dict[str, list] = {}
    tribe_node_y: dict[str, list] = {}
    tribe_node_c: dict[str, list] = {}
    tribe_node_t: dict[str, list] = {}
    tribe_labels: dict[str, list] = {}

    _TRIBE_BORDER = ["#4a9eff","#ff9f43","#2ecc71","#e040fb","#ff4b4b",
                     "#f4d03f","#00d2b4","#e74c3c","#8e44ad","#16a085",
                     "#d35400","#1abc9c","#2980b9"]

    for aid, ag in alive.items():
        tid = a2t.get(aid, "_sin_tribu")
        pos = positions.get(aid, (0.0, 0.0))
        h   = ag.get("humor", 0.5)
        tribe_node_x.setdefault(tid, []).append(pos[0])
        tribe_node_y.setdefault(tid, []).append(pos[1])
        tribe_node_c.setdefault(tid, []).append(
            "#FF4B4B" if h < 0.35 else "#F4D03F" if h < 0.65 else "#00D2B4"
        )
        tribe_node_t.setdefault(tid, []).append(
            f"<b>{ag['nombre']}</b><br>Tribu: {tid[:12]}<br>"
            f"Humor: {h:.2f} · Edad: {ag.get('edad',0)}<br>"
            f"Arquetipo: {ag.get('arquetipo_dominante','?')}"
        )
        tribe_labels.setdefault(tid, []).append(ag["nombre"][:6])

    for i, tid in enumerate(sorted(tribe_node_x)):
        border = _TRIBE_BORDER[i % len(_TRIBE_BORDER)]
        traces.append(go.Scatter(
            x=tribe_node_x[tid], y=tribe_node_y[tid],
            mode="markers+text",
            marker=dict(size=12, color=tribe_node_c[tid],
                        line=dict(color=border, width=2)),
            text=tribe_labels[tid],
            textfont=dict(size=7, color="#ddd"),
            textposition="top center",
            hovertext=tribe_node_t[tid], hoverinfo="text",
            name=tid[:14],
        ))

    stats_text = (
        f"{len(alive)} vivos · {len(dead)} muertos · "
        f"{len(ex_ent)//3} entrelazados · {len(ex_pos)//3} lazos+"
    )
    fig = go.Figure(data=traces)
    fig.update_layout(
        title=dict(text=stats_text, font=dict(color="#aaa", size=11)),
        paper_bgcolor="#0a0014", plot_bgcolor="#0a0014",
        showlegend=True,
        legend=dict(font=dict(color="#ccc", size=9), bgcolor="rgba(0,0,0,0.4)",
                    x=0.01, y=0.99),
        margin=dict(l=0, r=0, t=30, b=0),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False,
                   scaleanchor="x"),
        dragmode="pan",
        uirevision="social",
    )
    return fig


# ── Renders HTML ──────────────────────────────────────────────────────────────

def _render_myths_html(active_myths: list, agent_names: dict) -> str:
    if not active_myths:
        return "<span style='color:#666'>Sin mitos activos actualmente.</span>"
    parts = []
    for m in active_myths:
        hero    = agent_names.get(m.get("hero_id", ""), m.get("hero_id", "?"))
        monster = agent_names.get(m.get("monster_id", ""), m.get("monster_id", "?"))
        dia_c   = m.get("day_crystallized", "?")
        parts.append(
            f"<div style='border-left:3px solid #9b59b6;padding:8px 12px;margin-bottom:8px;"
            f"background:rgba(155,89,182,0.1);border-radius:4px'>"
            f"<b style='color:#E040FB'>Héroe vs Monstruo</b> — día {dia_c}<br>"
            f"🌟 <b style='color:#00D2B4'>{hero}</b>&nbsp;vs&nbsp;"
            f"👹 <b style='color:#FF4B4B'>{monster}</b></div>"
        )
    return "".join(parts)


def _render_lexicon_html(lex_data: dict) -> str:
    if not lex_data:
        return "<span style='color:#555'>Sin léxico generado aún.</span>"
    lines = []
    for tribe_id, ld in lex_data.items():
        words = ld.get("words", {}) if isinstance(ld, dict) else {}
        if words:
            word_str = "  ".join(f"<b>{arch}</b>→{w}" for arch, w in words.items())
            lines.append(
                f"<span style='color:#9b59b6'>{tribe_id[:14]}</span>: {word_str}"
            )
    return "<br>".join(lines) if lines else "<span style='color:#555'>Sin palabras emergentes aún.</span>"


def _render_dreams_html(cp: dict) -> str:
    agents   = cp.get("agentes", {}).get("agents", [])
    alive    = [a for a in agents if a.get("is_alive", False)]
    t_data   = cp.get("agentes", {}).get("tribe_manager", {})
    a2t      = t_data.get("agent_to_tribe", {})

    all_dreams = []
    for a in alive:
        for d in a.get("dreams", []):
            all_dreams.append({
                "nombre":       a.get("nombre", "?"),
                "tribu":        a2t.get(a.get("id", ""), "?")[:12],
                "dia":          d.get("dia", 0),
                "simbolo":      d.get("simbolo", "?"),
                "insight":      d.get("insight", ""),
                "procesamiento": d.get("procesamiento", "?"),
                "arquetipo":    d.get("arquetipo", ""),
            })

    if not all_dreams:
        return "<span style='color:#555'>Sin sueños registrados en este checkpoint.</span>"

    all_dreams.sort(key=lambda x: -x["dia"])
    html = ""
    for d in all_dreams[:25]:
        pc = _PROCESO_COLORS.get(d["procesamiento"], "#888")
        html += (
            f"<div style='border-left:3px solid {pc};padding:6px 12px;margin-bottom:5px;"
            f"background:rgba(155,89,182,0.06);border-radius:3px'>"
            f"<span style='color:{pc};font-size:0.72em'>"
            f"{d['procesamiento'].replace('_',' ').upper()}</span>"
            f"<span style='color:#555;font-size:0.72em'> · día {d['dia']}</span><br>"
            f"<b style='color:#E040FB'>{d['nombre']}</b>"
            f"<span style='color:#888;font-size:0.8em'> ({d['tribu']})</span>"
            f" sueña con <b style='color:#F4D03F'>«{d['simbolo']}»</b><br>"
            f"<span style='color:#aaa;font-size:0.83em;font-style:italic'>"
            f"{d['insight'][:130]}{'…' if len(d['insight'])>130 else ''}</span></div>"
        )
    total = len(all_dreams)
    if total > 25:
        html += f"<span style='color:#444;font-size:0.75em'>… y {total-25} sueños más</span>"
    return html


def _render_dreams_by_tribe_html(cp: dict) -> str:
    agents   = cp.get("agentes", {}).get("agents", [])
    t_data   = cp.get("agentes", {}).get("tribe_manager", {})
    a2t      = t_data.get("agent_to_tribe", {})

    tribe_symbols: dict[str, dict[str, int]] = {}
    for a in agents:
        tid = a2t.get(a.get("id", ""), "sin_tribu")
        for d in a.get("dreams", []):
            sym = d.get("simbolo", "?")
            tribe_symbols.setdefault(tid, {})
            tribe_symbols[tid][sym] = tribe_symbols[tid].get(sym, 0) + 1

    if not tribe_symbols:
        return "<span style='color:#555'>Sin datos de sueños por tribu.</span>"

    html = ""
    for tid in sorted(tribe_symbols):
        syms = sorted(tribe_symbols[tid].items(), key=lambda x: -x[1])
        sym_str = " · ".join(f"<b style='color:#F4D03F'>{s}</b>×{n}" for s, n in syms[:6])
        html += (
            f"<div style='margin-bottom:8px;padding:6px 10px;"
            f"background:rgba(155,89,182,0.08);border-radius:3px'>"
            f"<span style='color:#9b59b6;font-weight:bold'>{tid[:16]}</span>: {sym_str}"
            f"</div>"
        )
    return html


def _render_structures_html(cp: dict) -> str:
    world = cp.get("world", {})
    structures_raw = world.get("persistent_structures", {})
    if not structures_raw:
        return "<span style='color:#555'>Sin estructuras construidas todavía.</span>"

    all_s = []
    for key, slist in structures_raw.items():
        for s in (slist if isinstance(slist, list) else [slist]):
            all_s.append(s)

    all_s.sort(key=lambda s: s.get("dia_construccion", 0), reverse=True)

    html = ""
    for s in all_s[:40]:
        color = _STRUCT_COLORS.get(s.get("estado", ""), "#888")
        coord = s.get("coord", [0, 0])
        cq, cr = (coord[0], coord[1]) if isinstance(coord, (list, tuple)) else (0, 0)
        html += (
            f"<div style='border-left:3px solid {color};padding:4px 10px;margin-bottom:4px;"
            f"background:rgba(0,0,0,0.2);border-radius:2px'>"
            f"<b style='color:{color}'>{s.get('tipo','?').upper()}</b> "
            f"<span style='color:#aaa'>— {s.get('tribu_origen','?')[:14]}</span> "
            f"<span style='color:#666;font-size:0.8em'>"
            f"· Día {s.get('dia_construccion','?')} · ({cq},{cr}) · {s.get('n_usos',0)} usos"
            f"</span></div>"
        )
    total = len(all_s)
    if total > 40:
        html += f"<span style='color:#444;font-size:0.75em'>… y {total-40} más</span>"
    return html


def _render_technologies_html(cp: dict) -> str:
    knowledge     = cp.get("agentes", {}).get("knowledge", {})
    agent_know    = knowledge.get("agent_knowledge", {})
    agent_linajes = knowledge.get("agent_lineages", {})

    if not agent_know:
        return "<span style='color:#555'>Sin tecnologías materializadas aún.</span>"

    type_count: dict[str, int] = {}
    for aid, types in agent_know.items():
        for t in (types if isinstance(types, list) else []):
            type_count[t] = type_count.get(t, 0) + 1

    max_c = max(type_count.values()) if type_count else 1
    html = ""
    for tech, count in sorted(type_count.items(), key=lambda x: -x[1]):
        label = _TECH_LABELS.get(tech, tech.replace("_", " ").capitalize())
        bar_w = int(count / max_c * 100)
        html += (
            f"<div style='margin-bottom:8px'>"
            f"<span style='color:#F4D03F'>{label}</span> "
            f"<span style='color:#666;font-size:0.82em'>({count} portadores)</span><br>"
            f"<div style='background:#1f2937;border-radius:3px;height:6px;width:100%;margin-top:3px'>"
            f"<div style='background:#F4D03F;width:{bar_w}%;height:6px;border-radius:3px'></div>"
            f"</div></div>"
        )

    # Linajes notables (baja fidelidad → superstición)
    low_fidelity = []
    for aid, linajes in agent_linajes.items():
        for lin in (linajes if isinstance(linajes, list) else []):
            if isinstance(lin, dict) and lin.get("fidelidad", 1.0) < 0.35:
                low_fidelity.append(lin)
    if low_fidelity:
        html += "<hr style='border-color:#333;margin:10px 0'>"
        html += "<span style='color:#f39c12;font-size:0.8em'>SUPERSTICIÓN (fidelidad < 35%):</span><br>"
        for lin in low_fidelity[:8]:
            html += (
                f"<span style='color:#888;font-size:0.8em'>"
                f"«{lin.get('nombre_original','?')}» → «{lin.get('nombre_actual','?')}» "
                f"(fidelidad {lin.get('fidelidad',0):.0%} · {lin.get('n_transmisiones',0)} transmisiones)"
                f"</span><br>"
            )
    return html


# ── E1: Frecuencia simbólica en sueños ───────────────────────────────────────

def _build_dream_frequency_figure(cp: dict) -> "go.Figure | None":
    """
    E1 — Barras de frecuencia de arquetipos en sueños, comparado con carga del ICL.
    """
    try:
        import plotly.graph_objects as go
    except ImportError:
        return None

    agents = cp.get("agentes", {}).get("agents", [])
    cf     = cp.get("agentes", {}).get("collective_field", {})
    icl_symbols = cf.get("symbols", {})

    dream_arch: dict[str, int] = {}
    for a in agents:
        for d in a.get("dreams", []):
            arch = d.get("arquetipo", "?")
            dream_arch[arch] = dream_arch.get(arch, 0) + 1

    if not dream_arch:
        return None

    archs   = sorted(dream_arch, key=lambda k: -dream_arch[k])
    freq    = [dream_arch[a] for a in archs]
    labels  = [a.replace("_", " ").capitalize() for a in archs]
    colors  = [_ARCH_COLORS.get(a, "#888") for a in archs]
    icl_vals = [icl_symbols.get(a, 0.0) for a in archs]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Frecuencia en sueños", x=labels, y=freq,
        marker=dict(color=colors), opacity=0.85,
        hovertemplate="%{x}: %{y} sueños<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        name="Carga ICL (×10)", x=labels, y=[v * 10 for v in icl_vals],
        mode="lines+markers", yaxis="y2",
        line=dict(color="#ffffff", width=1.5, dash="dot"),
        marker=dict(size=5, color="#ffffff"),
        hovertemplate="%{x} ICL: %{customdata:.3f}<extra></extra>",
        customdata=icl_vals,
    ))

    fig.update_layout(
        title=dict(text="Frecuencia arquetipos en sueños vs carga ICL",
                   font=dict(color="#ccc", size=12)),
        paper_bgcolor="#111827", plot_bgcolor="#111827",
        showlegend=True, legend=dict(font=dict(color="#aaa", size=9),
                                     orientation="h", y=1.12),
        margin=dict(l=40, r=40, t=55, b=50),
        xaxis=dict(color="#aaa", tickfont=dict(size=9)),
        yaxis=dict(color="#aaa", gridcolor="#1f2937", title="# sueños"),
        yaxis2=dict(overlaying="y", side="right", color="#555",
                    title="ICL ×10", showgrid=False),
        barmode="group",
    )
    return fig


# ── E2: Sueños compartidos (entrelazamiento onírico) ─────────────────────────

def _render_shared_dreams_html(cp: dict) -> str:
    """E2 — Pares de agentes con sueños entrelazados."""
    agents  = cp.get("agentes", {}).get("agents", [])
    id2name = {a["id"]: a["nombre"] for a in agents}

    pairs = []
    for a in agents:
        for d in a.get("dreams", []):
            sw = d.get("shared_with", [])
            if sw:
                for partner_id in (sw if isinstance(sw, list) else [sw]):
                    pairs.append({
                        "a1":      a["nombre"],
                        "a2":      id2name.get(partner_id, partner_id),
                        "dia":     d.get("dia", 0),
                        "simbolo": d.get("simbolo", "?"),
                        "arch":    d.get("arquetipo", "?"),
                    })

    if not pairs:
        return (
            "<span style='color:#555'>Sin sueños entrelazados registrados.<br>"
            "Los sueños compartidos emergen cuando dos agentes sueñan el mismo símbolo "
            "en circunstancias análogas.</span>"
        )

    pairs.sort(key=lambda x: -x["dia"])
    _row_parts = []
    for p in pairs[:30]:
        ac = _ARCH_COLORS.get(p["arch"], "#888")
        _row_parts.append(
            f"<tr>"
            f"<td style='color:#E040FB;padding:3px 8px'>{p['a1']}</td>"
            f"<td style='color:#E040FB;padding:3px 8px'>{p['a2']}</td>"
            f"<td style='color:#F4D03F;padding:3px 8px'>«{p['simbolo']}»</td>"
            f"<td style='color:{ac};padding:3px 8px'>{p['arch']}</td>"
            f"<td style='color:#555;padding:3px 8px;text-align:right'>Día {p['dia']}</td>"
            f"</tr>"
        )
    rows = "".join(_row_parts)
    return (
        "<table style='width:100%;font-size:11px;border-collapse:collapse'>"
        "<thead><tr style='border-bottom:1px solid #333'>"
        "<th style='color:#888;text-align:left;padding:4px 8px'>Agente A</th>"
        "<th style='color:#888;text-align:left;padding:4px 8px'>Agente B</th>"
        "<th style='color:#888;text-align:left;padding:4px 8px'>Símbolo</th>"
        "<th style='color:#888;text-align:left;padding:4px 8px'>Arquetipo</th>"
        "<th style='color:#888;text-align:right;padding:4px 8px'>Día</th>"
        f"</tr></thead><tbody>{rows}</tbody></table>"
    )


# ── F2: Memoria cultural y linaje de transmisión ──────────────────────────────

def _render_cultural_memory_html(cp: dict) -> str:
    """F2 — Árbol de transmisión cultural: eventos que viajaron entre agentes."""
    tm = cp.get("agentes", {}).get("tribe_manager", {})
    cm = tm.get("cultural_memories", {})

    all_records = []
    for tribe_id, mem in cm.items():
        for rec in mem.get("records", []):
            all_records.append({**rec, "tribe": tribe_id})

    if not all_records:
        return "<span style='color:#555'>Sin registros de memoria cultural.</span>"

    all_records.sort(key=lambda r: -r.get("n_transmisiones", 0))

    html = []
    for rec in all_records[:25]:
        n_trans = rec.get("n_transmisiones", 0)
        trans   = rec.get("transmisores", [])
        orig    = rec.get("agente_origen", "?")
        dia_o   = rec.get("dia_origen", "?")
        tipo    = rec.get("tipo_evento", "?").replace("_", " ")
        desc_a  = rec.get("descripcion_actual", rec.get("descripcion_original", ""))[:100]
        intens  = rec.get("intensidad_emocional", 0.0)
        tribe_s = rec.get("tribe", "")[:12]

        # Color de intensidad
        ic = "#e74c3c" if intens > 0.7 else "#f39c12" if intens > 0.4 else "#2ecc71"
        chain = " → ".join(trans[:5]) if trans else orig
        if len(trans) > 5:
            chain += f" … (+{len(trans)-5})"

        html.append(
            f"<div style='border-left:3px solid {ic};padding:6px 10px;margin-bottom:5px;"
            f"background:rgba(0,0,0,0.15);border-radius:3px'>"
            f"<div style='display:flex;justify-content:space-between;align-items:center'>"
            f"<span style='color:{ic};font-size:0.72em;text-transform:uppercase'>{tipo}</span>"
            f"<span style='color:#444;font-size:0.7em'>{tribe_s} · Día {dia_o} · "
            f"{n_trans}✦ transmisión{'es' if n_trans!=1 else ''}</span></div>"
            f"<div style='color:#aaa;font-size:0.8em;margin:2px 0;font-style:italic'>"
            f"{desc_a}{'…' if len(rec.get('descripcion_actual',''))>100 else ''}</div>"
            f"<div style='color:#555;font-size:0.72em'>Cadena: "
            f"<span style='color:#9b59b6'>{chain}</span></div>"
            f"</div>"
        )

    total = len(all_records)
    if total > 25:
        html.append(f"<span style='color:#444;font-size:0.75em'>… y {total-25} registros más</span>")
    return "".join(html)


# ── G1: Radar arquetípico por agente ─────────────────────────────────────────

def _build_agent_radar(agent_data: dict) -> "go.Figure | None":
    """G1 — Radar chart de 12 arquetipos para un agente seleccionado."""
    try:
        import plotly.graph_objects as go
    except ImportError:
        return None

    archs = agent_data.get("archetypes", {})
    if not archs:
        return None

    _RADAR_LABELS = [
        "self", "persona", "sombra", "anima_animus", "heroe", "sabio",
        "trickster", "madre", "padre", "nino_divino", "gobernante", "rebelde",
    ]
    # Mapear self → self_ para el dict del agente
    values = []
    for lbl in _RADAR_LABELS:
        key = "self_" if lbl == "self" else lbl
        values.append(archs.get(key, 0.0))
    values_closed = values + [values[0]]
    labels_closed = _RADAR_LABELS + [_RADAR_LABELS[0]]

    dominant = max(archs, key=archs.get) if archs else "—"
    dom_color = _ARCH_COLORS.get(dominant, "#00D2B4")

    fig = go.Figure(go.Scatterpolar(
        r=values_closed, theta=labels_closed,
        fill="toself", fillcolor=dom_color.replace("#", "rgba(") + ",0.15)",
        line=dict(color=dom_color, width=2),
        name=agent_data.get("nombre", "?"),
    ))
    fig.update_layout(
        polar=dict(
            bgcolor="#0a0020",
            radialaxis=dict(range=[0, 1], color="#555", gridcolor="#222", tickfont=dict(size=8)),
            angularaxis=dict(color="#888", gridcolor="#222", tickfont=dict(size=9)),
        ),
        paper_bgcolor="#111827",
        showlegend=False,
        margin=dict(l=40, r=40, t=50, b=40),
        title=dict(
            text=f"{agent_data.get('nombre','?')} — {dominant}",
            font=dict(color=dom_color, size=13),
        ),
    )
    return fig


# ── Helper UI ─────────────────────────────────────────────────────────────────

def _dark_placeholder() -> dict:
    """Figura Plotly vacía con tema oscuro para inicializar ui.plotly()."""
    return {
        "data": [],
        "layout": {
            "paper_bgcolor": "#111827",
            "plot_bgcolor":  "#111827",
            "xaxis": {"color": "#333", "gridcolor": "#1a1a2e", "showgrid": True,
                      "showticklabels": False},
            "yaxis": {"color": "#333", "gridcolor": "#1a1a2e",
                      "showticklabels": False},
            "margin": {"l": 10, "r": 10, "t": 10, "b": 10},
        },
    }


def _mini_stat(title: str, value: str):
    from nicegui import ui
    with ui.card().classes("p-4 bg-gray-800 text-white rounded-xl"):
        ui.label(title).classes("text-xs text-gray-400 uppercase tracking-wider mb-1")
        val = ui.label(value).classes("text-xl font-bold text-purple-300")
    return val


def _tension_bar(label: str, value: float, color_fn=None):
    """Barra horizontal de presión 0–1 con color dinámico."""
    from nicegui import ui
    if color_fn is None:
        color_fn = lambda v: "#e74c3c" if v > 0.7 else "#f39c12" if v > 0.4 else "#2ecc71"
    color = color_fn(value)
    w = int(value * 100)
    with ui.card().classes("p-3 bg-gray-800 text-white rounded-xl"):
        ui.label(label).classes("text-xs text-gray-400 uppercase tracking-wider mb-1")
        val = ui.label(f"{value:.1%}").classes("text-lg font-bold").style(f"color:{color}")
        bar_ref = ui.html(
            f"<div style='background:#1f2937;border-radius:4px;height:8px;width:100%;margin-top:4px'>"
            f"<div style='background:{color};width:{w}%;height:8px;border-radius:4px'></div></div>"
        )
    return val, bar_ref


# ── Página de lanzamiento ─────────────────────────────────────────────────────

def build_launcher_page(app_state, DB_PATH, CP_DIR, SEEDS_DIR, LIMINAL_SERVER) -> None:
    import os
    from nicegui import ui
    from ui.db_reader import load_checkpoint, checkpoint_summary

    cp   = load_checkpoint()
    summ = checkpoint_summary(cp)

    with ui.column().classes("w-full min-h-screen bg-gray-950 items-center justify-center p-8"):
        ui.label("PSYCHE SIMULACRA").classes(
            "text-4xl font-bold text-purple-300 tracking-widest mb-2"
        )
        ui.label("Simulación ABM de inconsciente colectivo").classes(
            "text-sm text-gray-500 mb-10"
        )

        # ── Panel estado actual ───────────────────────────────────────────────
        with ui.card().classes("w-full max-w-xl bg-gray-800 mb-8"):
            if summ["dia"] > 0:
                ui.label("Estado actual").classes("text-xs text-gray-400 uppercase px-4 pt-4")
                with ui.row().classes("px-4 pb-4 gap-8"):
                    with ui.column().classes("items-center"):
                        ui.label(str(summ["dia"])).classes("text-3xl font-bold text-purple-300")
                        ui.label("Día simulado").classes("text-xs text-gray-400")
                    with ui.column().classes("items-center"):
                        ui.label(f"{summ['vivos']} / {summ['total']}").classes(
                            "text-3xl font-bold text-green-400"
                        )
                        ui.label("Agentes vivos").classes("text-xs text-gray-400")
                    with ui.column().classes("items-center"):
                        ui.label(summ["timestamp"] or "—").classes("text-sm text-gray-400")
                        ui.label("Último checkpoint").classes("text-xs text-gray-400")
            else:
                ui.label("Sin simulación activa").classes("p-4 text-yellow-400")

        # ── Opciones de inicio ────────────────────────────────────────────────
        with ui.card().classes("w-full max-w-xl bg-gray-800 p-6"):
            ui.label("Iniciar").classes("text-sm text-gray-400 uppercase mb-4")

            seeds_files = sorted(Path(SEEDS_DIR).glob("*.yaml")) if Path(SEEDS_DIR).exists() else []

            seed_select = ui.select(
                {str(f): f.name for f in seeds_files},
                value=str(seeds_files[0]) if seeds_files else None,
                label="Archivo de semillas (nueva sim)",
            ).classes("w-full mb-2")

            seed_input = ui.number("Seed aleatoria", value=42, min=0).classes("w-full mb-4")
            use_liminal = ui.checkbox("Levantar servidor Zona Liminal", value=False).classes("mb-4")

            # H3 — Configuración avanzada
            with ui.expansion("Configuración avanzada", icon="settings").classes(
                "w-full mb-4 text-gray-300"
            ):
                with ui.grid(columns=2).classes("w-full gap-3"):
                    cfg_narrative = ui.select(
                        {True: "Activada", False: "Desactivada"},
                        value=os.environ.get("NARRATIVE_ENABLED", "true").lower() != "false",
                        label="Narrativa (NARRATIVE_ENABLED)",
                    ).classes("w-full")
                    cfg_model = ui.input(
                        label="Modelo Ollama (OLLAMA_MODEL)",
                        value=os.environ.get("OLLAMA_MODEL", "llama3"),
                        placeholder="llama3",
                    ).classes("w-full")
                    cfg_cp_interval = ui.number(
                        label="Días entre checkpoints",
                        value=int(os.environ.get("CHECKPOINT_INTERVAL", "50")),
                        min=1, max=500,
                    ).classes("w-full")
                    cfg_clustering = ui.number(
                        label="Días hasta clustering",
                        value=int(os.environ.get("DAYS_UNTIL_CLUSTERING", "365")),
                        min=1, max=9999,
                    ).classes("w-full")
                ui.label(
                    "Los cambios se aplican al iniciar la simulación (no requieren reiniciar el servidor)."
                ).classes("text-xs text-gray-500 mt-1")

            def _apply_config() -> None:
                os.environ["NARRATIVE_ENABLED"]    = str(cfg_narrative.value).lower()
                os.environ["OLLAMA_MODEL"]          = str(cfg_model.value).strip() or "llama3"
                os.environ["CHECKPOINT_INTERVAL"]  = str(int(cfg_cp_interval.value or 50))
                os.environ["DAYS_UNTIL_CLUSTERING"] = str(int(cfg_clustering.value or 365))

            with ui.row().classes("gap-4 w-full"):
                if summ["vivos"] > 0:
                    async def _continue():
                        _apply_config()
                        await _start_sim(app_state, mode="resume",
                                         use_liminal=use_liminal.value,
                                         liminal_server=LIMINAL_SERVER)
                    ui.button("Continuar simulación", on_click=_continue).classes(
                        "flex-1 bg-purple-700 hover:bg-purple-600 text-white"
                    )

                async def _new():
                    _apply_config()
                    await _start_sim(app_state, mode="new",
                                     seeds_path=seed_select.value,
                                     seed=int(seed_input.value or 42),
                                     use_liminal=use_liminal.value,
                                     liminal_server=LIMINAL_SERVER)
                ui.button("Nueva simulación", on_click=_new).classes(
                    "flex-1 bg-indigo-700 hover:bg-indigo-600 text-white"
                )


async def _start_sim(app_state, mode: str, seeds_path: str = None,
                     seed: int = 42, use_liminal: bool = False,
                     liminal_server: Path = None) -> None:
    from nicegui import ui
    from core.simulation import SimulationRunner
    from core.runtime.psyche_runtime import PsycheRuntime

    DB_PATH = ROOT / "data" / "db" / "simulation.db"
    CP_DIR  = ROOT / "data" / "checkpoints"

    try:
        if mode == "resume":
            runner = SimulationRunner.resume(
                db_path=str(DB_PATH),
                checkpoint_dir=str(CP_DIR),
            )
        else:
            runner = SimulationRunner.new_session(
                seed_file=seeds_path,
                seed=seed,
                db_path=str(DB_PATH),
                checkpoint_dir=str(CP_DIR),
            )
    except Exception as e:
        ui.notify(f"Error iniciando simulación: {e}", type="negative")
        return

    runtime = PsycheRuntime()
    runtime.attach_runner(runner)
    runtime.state.simulation = "running"

    app_state.set_runner(runner, runtime)
    app_state.use_liminal = use_liminal

    if use_liminal and liminal_server and liminal_server.exists():
        try:
            if sys.platform == "win32":
                proc = subprocess.Popen(
                    [sys.executable, str(liminal_server), "--host", "0.0.0.0",
                     "--port", str(app_state.liminal_port), "--seed", "0"],
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                )
            else:
                proc = subprocess.Popen(
                    [sys.executable, str(liminal_server), "--host", "0.0.0.0",
                     "--port", str(app_state.liminal_port), "--seed", "0"],
                    start_new_session=True,
                )
            app_state._liminal_proc = proc
            runtime.state.liminal = "starting"
        except Exception as e:
            import sys
            print(f"[UI] liminal start: {e}", file=sys.stderr)

    # Limpiar evento de pausa anterior y registrar gate en el reloj
    app_state._pause_event.clear()

    def _pause_gate(tp) -> None:
        import time as _t
        while app_state._pause_event.is_set():
            _t.sleep(0.05)

    runner.clock.on_day(_pause_gate, priority=98)  # justo antes del stopper (99)

    def _run():
        try:
            runner.run(n_days=None)
        except Exception as e:
            import sys
            print(f"[UI] sim thread: {e}", file=sys.stderr)
        finally:
            app_state._pause_event.clear()
            runtime.state.simulation = "stopped"

    t = threading.Thread(target=_run, daemon=True, name="sim_worker")
    t.start()
    app_state.sim_thread = t

    ui.navigate.to("/monitor")


# ── Página de monitoreo ───────────────────────────────────────────────────────

def build_monitor_page(app_state) -> None:
    from nicegui import ui
    from ui.db_reader import (
        load_checkpoint, load_agent_metrics,
        load_climate_metrics, load_scenario_metrics, load_deaths_log,
        load_climate_events, load_emergence_metrics,
    )

    runner = app_state.get_runner()
    if runner is None:
        ui.label("Sin simulación activa.").classes("p-8 text-yellow-400")
        ui.button("Volver al inicio", on_click=lambda: ui.navigate.to("/")).classes("m-4")
        return

    terrain_biomes = _extract_terrain(runner)

    # ── Header ────────────────────────────────────────────────────────────────
    with ui.header().classes("bg-purple-950 text-white px-6 py-2 flex items-center gap-6"):
        ui.label("PSYCHE SIMULACRA").classes("text-lg font-bold tracking-widest")
        refs_hdr: dict = {}
        with ui.row().classes("gap-6 ml-4 flex-1 items-center"):
            refs_hdr["dia"]    = ui.label("Día —").classes("text-purple-200 text-sm")
            refs_hdr["vivos"]  = ui.label("Agentes —").classes("text-green-300 text-sm")
            refs_hdr["tribus"] = ui.label("Tribus —").classes("text-blue-300 text-sm")
            refs_hdr["estado"] = ui.badge("—", color="grey").classes("text-xs")

        # Control de velocidad de simulación
        _SPEED_LABELS = ["MAX", "×20", "×5", "×1", "Paso"]
        _SPEED_VALUES = {
            "MAX":  None,    # velocidad máxima (sin límite)
            "×20":  0.05,    # 20 ticks/s → 1 día ≈ 1.2s
            "×5":   0.2,     # 5 ticks/s  → 1 día ≈ 4.8s
            "×1":   1.0,     # 1 tick/s   → 1 día ≈ 24s (observable)
            "Paso": 5.0,     # 0.2 ticks/s → muy lento
        }

        speed_select = ui.select(
            options=_SPEED_LABELS,
            value="MAX",
            label="Vel.",
        ).classes("text-xs w-24 ml-4").props("dense dark")

        def _on_speed_change():
            rv = app_state.get_runner()
            if rv:
                try:
                    rv.clock.set_speed(_SPEED_VALUES.get(speed_select.value))
                except Exception:
                    pass

        speed_select.on("update:modelValue", lambda _: _on_speed_change())

        # Botón Pausar / Reanudar
        def _toggle_pause() -> None:
            if app_state.is_paused:
                app_state._pause_event.clear()
                pause_btn.set_text("⏸ Pausar")
                pause_btn.props('color="purple-700"')
                rt = app_state.get_runtime()
                if rt:
                    rt.state.simulation = "running"
            else:
                app_state._pause_event.set()
                pause_btn.set_text("▶ Reanudar")
                pause_btn.props('color="orange-600"')
                rt = app_state.get_runtime()
                if rt:
                    rt.state.simulation = "paused"

        pause_btn = ui.button("⏸ Pausar", on_click=_toggle_pause).classes(
            "text-xs bg-purple-700 hover:bg-purple-600 text-white px-3 py-1 rounded"
        )

        # Botón Cerrar simulación
        def _cerrar_simulacion() -> None:
            rv = app_state.get_runner()
            if rv:
                try:
                    rv.shutdown()
                except Exception as e:
                    print(f"[UI] shutdown error: {e}", file=sys.stderr)
            proc = app_state._liminal_proc
            if proc is not None:
                try:
                    proc.terminate()
                except Exception:
                    pass
                app_state._liminal_proc = None
            app_state.set_runner(None, None)
            ui.navigate.to("/")

        ui.button("✕ Cerrar", on_click=_cerrar_simulacion).classes(
            "text-xs bg-red-800 hover:bg-red-700 text-white px-3 py-1 rounded ml-2"
        )

    # ── Tabs ──────────────────────────────────────────────────────────────────
    with ui.tabs().classes("bg-purple-900 text-white w-full") as tabs:
        t_resumen    = ui.tab("Resumen")
        t_tendencias = ui.tab("Tendencias")
        t_icl        = ui.tab("ICL")
        t_redsocial  = ui.tab("Red Social")
        t_agentes    = ui.tab("Agentes")
        t_suenos     = ui.tab("Sueños")
        t_civiliz    = ui.tab("Civilización")
        t_mapa       = ui.tab("Mapa")
        if app_state.use_liminal:
            t_liminal = ui.tab("Zona Liminal")

    refs: dict = {}

    with ui.tab_panels(tabs, value=t_resumen).classes("w-full bg-gray-900 flex-1"):

        # ── Tab Resumen ───────────────────────────────────────────────────────
        with ui.tab_panel(t_resumen):
            with ui.grid(columns=4).classes("w-full gap-4 p-4"):
                refs["temp"]    = _mini_stat("Temperatura", "—")
                refs["estac"]   = _mini_stat("Estación", "—")
                refs["cc"]      = _mini_stat("Carrying capacity", "—")
                refs["presion"] = _mini_stat("Presión recursos", "—")
            with ui.grid(columns=3).classes("w-full gap-4 px-4 pb-4"):
                refs["humor"]    = _mini_stat("Humor promedio", "—")
                refs["energia"]  = _mini_stat("Energía promedio", "—")
                refs["ansiedad"] = _mini_stat("Ansiedad promedio", "—")

            ui.separator().classes("mx-4")
            ui.label("Tensión colectiva global").classes(
                "text-xs text-gray-400 uppercase px-4 pt-3"
            )
            with ui.grid(columns=3).classes("w-full gap-4 px-4 pb-3"):
                refs["tension_emoc"], refs["tension_emoc_bar"] = _tension_bar("Presión emocional", 0.0)
                refs["tension_mito"], refs["tension_mito_bar"] = _tension_bar("Presión mítica", 0.0)
                refs["confusion"],    refs["confusion_bar"]    = _tension_bar("Confusión", 0.0)

            refs["histeria"] = ui.label("").classes("px-4 pb-2 text-red-400 text-sm font-bold")

            ui.separator().classes("mx-4 mt-2")
            ui.label("Clima activo").classes("text-xs text-gray-400 uppercase px-4 pt-3")
            refs["evento_clima"] = ui.label("—").classes("px-4 pb-2 text-yellow-300 text-sm")
            refs["fuego"]        = ui.label("").classes("px-4 text-red-400 text-sm")
            refs["catastrofe"]   = ui.label("").classes("px-4 text-orange-400 text-sm font-bold")

            ui.separator().classes("mx-4 mt-2")
            ui.label("Muertes recientes").classes("text-xs text-gray-400 uppercase px-4 pt-3")
            refs["deaths_log"] = ui.log(max_lines=20).classes(
                "h-48 mx-4 mb-4 bg-gray-950 text-red-300 text-xs"
            )

        # ── Tab Tendencias ────────────────────────────────────────────────────
        with ui.tab_panel(t_tendencias):
            ui.label("Estado emocional poblacional").classes(
                "text-xs text-gray-400 uppercase px-4 pt-4"
            )
            refs["plot_emoc"]      = ui.plotly(_dark_placeholder()).classes("w-full h-52 px-2")
            ui.label("Población viva").classes(
                "text-xs text-gray-400 uppercase px-4 pt-2"
            )
            refs["plot_poblacion"] = ui.plotly(_dark_placeholder()).classes("w-full h-40 px-2")
            ui.label("Temperatura y riesgo climático · Bandas = eventos extremos").classes(
                "text-xs text-gray-400 uppercase px-4 pt-2"
            )
            refs["plot_clima"]     = ui.plotly(_dark_placeholder()).classes("w-full h-44 px-2")
            ui.label("Presión de recursos / Carrying capacity").classes(
                "text-xs text-gray-400 uppercase px-4 pt-2"
            )
            refs["plot_recursos"]  = ui.plotly(_dark_placeholder()).classes("w-full h-40 px-2")
            ui.separator().classes("mx-4 mt-3")
            ui.label("Métricas de emergencia cultural — KL · VFE · IMI").classes(
                "text-xs text-gray-400 uppercase px-4 pt-2"
            )
            refs["plot_emergence"] = ui.plotly(_dark_placeholder()).classes("w-full h-52 px-2")

        # ── Tab ICL ───────────────────────────────────────────────────────────
        with ui.tab_panel(t_icl):
            # B1 — Gauges del campo colectivo
            ui.label("Estado del campo colectivo · Ψ(t) = ∑ Sᵢ(t) × Wᵢ").classes(
                "text-xs text-gray-400 uppercase px-4 pt-4"
            )
            refs["plot_gauges"] = ui.plotly(_dark_placeholder()).classes("w-full px-2").style("height:200px")

            ui.separator().classes("mx-4 mt-1 mb-2")

            # B2 — Símbolos con tooltips arquetípicos
            ui.label("Carga Memética de Símbolos Arquetípicos").classes(
                "text-sm font-semibold px-4 text-purple-300"
            )
            refs["plot_symbols"] = ui.plotly(_dark_placeholder()).classes("w-full h-72 px-2")

            ui.separator().classes("mx-4 my-2")

            # B3 — Proto-mitos y mitos activos
            ui.label("Mitos activos y proto-mitos en gestación").classes(
                "text-xs text-gray-400 uppercase px-4"
            )
            refs["proto_myths_html"] = ui.html("").classes("px-4 pb-2 text-sm text-gray-300")

            ui.separator().classes("mx-4 my-2")
            ui.label("Mitología emergente (crystallized)").classes("text-xs text-gray-400 uppercase px-4")
            refs["myths_html"] = ui.html("").classes("px-4 pb-4 text-sm text-gray-300")

            ui.separator().classes("mx-4 my-2")
            ui.label("Léxico tribal emergente").classes("text-xs text-gray-400 uppercase px-4")
            refs["lexicon_html"] = ui.html("").classes("px-4 pb-4 text-xs font-mono text-purple-200")

        # ── Tab Red Social ────────────────────────────────────────────────────
        with ui.tab_panel(t_redsocial):
            ui.label("Red Social Cuántica").classes(
                "text-sm font-semibold px-4 pt-4 text-purple-300"
            )
            ui.label(
                "Nodos coloreados por humor (verde=alto · amarillo=medio · rojo=bajo). "
                "Borde de nodo = tribu. Verde = lazo+ · Rojo = lazo− · Púrpura = entrelazado."
            ).classes("text-xs text-gray-500 px-4 pb-2")

            # C3 — Stats de red
            with ui.row().classes("px-4 pb-2 gap-6 flex-wrap"):
                refs["soc_nodos"]   = ui.label("Nodos: —").classes("text-xs text-gray-300")
                refs["soc_aristas"] = ui.label("Aristas: —").classes("text-xs text-gray-300")
                refs["soc_cluster"] = ui.label("Clusters: —").classes("text-xs text-blue-300")
                refs["soc_hub"]     = ui.label("Hub: —").classes("text-xs text-yellow-300")
                refs["soc_ent"]     = ui.label("Entrelazados: —").classes("text-xs text-purple-300")

            refs["plot_social"] = ui.plotly(_dark_placeholder()).classes("w-full px-2").style("height:58vh")

            ui.separator().classes("mx-4 mt-2 mb-1")

            # C2 — Tabla de aristas con filtro por tribu
            with ui.row().classes("px-4 pb-1 gap-4 items-center"):
                ui.label("Aristas más fuertes").classes("text-xs text-gray-400 uppercase font-semibold")
                refs["soc_tribe_filter"] = ui.select(
                    options=["(todas)"],
                    value="(todas)",
                    label="Tribu",
                ).classes("text-xs w-40")
            refs["soc_edge_table"] = ui.html("").classes("px-4 pb-4 overflow-x-auto")

        # ── Tab Agentes ───────────────────────────────────────────────────────
        with ui.tab_panel(t_agentes):
            ui.label("Inspector de agentes").classes(
                "text-sm font-semibold px-4 pt-4 text-purple-300"
            )
            # G2 — Filtros
            with ui.row().classes("px-4 pb-2 gap-4 flex-wrap items-end"):
                refs["filter_tribu"]    = ui.select(
                    options=["(todas)"], value="(todas)", label="Tribu"
                ).classes("w-36 text-xs")
                refs["filter_arquetipo"] = ui.select(
                    options=["(todos)"] + list(_ARCH_COLORS.keys()),
                    value="(todos)", label="Arquetipo"
                ).classes("w-36 text-xs")
                refs["filter_estado"]   = ui.select(
                    options=["(todos)", "cooperacion", "competencia",
                             "aislamiento", "manipulacion"],
                    value="(todos)", label="Estado"
                ).classes("w-36 text-xs")
                ui.label("(click en fila → radar arquetípico)").classes(
                    "text-xs text-gray-500 self-end pb-1"
                )

            refs["agents_table"] = ui.table(
                columns=[
                    {"name": "nombre",    "label": "Nombre",    "field": "nombre",    "align": "left"},
                    {"name": "edad",      "label": "Edad",      "field": "edad",      "align": "right"},
                    {"name": "tribu",     "label": "Tribu",     "field": "tribu",     "align": "left"},
                    {"name": "arquetipo", "label": "Arquetipo", "field": "arquetipo", "align": "left"},
                    {"name": "humor",     "label": "Humor",     "field": "humor",     "align": "right"},
                    {"name": "energia",   "label": "Energía",   "field": "energia",   "align": "right"},
                    {"name": "ansiedad",  "label": "Ansiedad",  "field": "ansiedad",  "align": "right"},
                    {"name": "estado",    "label": "Estado",    "field": "estado",    "align": "left"},
                ],
                rows=[],
                row_key="nombre",
                pagination={"rowsPerPage": 25},
                selection="single",
            ).classes("w-full px-4")

            # G1 — Dialog con radar arquetípico al hacer click en fila
            with ui.dialog() as radar_dialog, ui.card().classes(
                "bg-gray-900 border border-purple-800"
            ).style("min-width:420px"):
                refs["radar_plot"]  = ui.plotly(_dark_placeholder()).style("width:380px;height:340px")
                refs["radar_stats"] = ui.html("").classes("px-2 pb-2 text-xs text-gray-300")
                ui.button("Cerrar", on_click=radar_dialog.close).classes(
                    "mt-1 text-xs text-gray-400"
                ).props("flat")
            refs["radar_dialog"] = radar_dialog

            def _on_agent_select(e) -> None:
                # NiceGUI pasa GenericEventArguments; Quasar QTable envía {added, rows, keys}
                args = e.args if hasattr(e, "args") else {}
                if isinstance(args, dict):
                    selected = args.get("rows", args.get("selection", []))
                elif isinstance(args, list):
                    selected = args
                else:
                    return
                if not selected:
                    return
                row = selected[0]
                agent_id = row.get("id", "")
                runner_now = app_state.get_runner()
                if runner_now and agent_id:
                    agent = runner_now.agents.agents.get(agent_id)
                    if agent:
                        ad = {
                            "nombre":     agent.nombre,
                            "archetypes": {
                                k: getattr(agent.archetypes, k, 0.0)
                                for k in ["self_","persona","sombra","anima_animus",
                                          "heroe","sabio","trickster","madre","padre",
                                          "nino_divino","gobernante","rebelde"]
                            },
                        }
                        fig = _build_agent_radar(ad)
                        if fig:
                            refs["radar_plot"].update_figure(fig)
                        top3 = agent.archetypes.top_n(3)
                        stats_html = (
                            f"<b style='color:#ccc'>{agent.nombre}</b>"
                            f"<span style='color:#555'> · Tribu: {row.get('tribu','?')}"
                            f" · Edad: {agent.edad}</span><br>"
                            + " ".join(
                                f"<span style='color:{_ARCH_COLORS.get(a,'#888')}'>"
                                f"{a}: {v:.2f}</span>"
                                for a, v in top3
                            )
                        )
                        refs["radar_stats"].set_content(stats_html)
                        radar_dialog.open()

            refs["agents_table"].on("selection", _on_agent_select)

        # ── Tab Sueños ────────────────────────────────────────────────────────
        with ui.tab_panel(t_suenos):
            # E1 — Frecuencia simbólica
            ui.label("Frecuencia de arquetipos en sueños vs carga ICL").classes(
                "text-xs text-gray-400 uppercase px-4 pt-4"
            )
            refs["plot_dream_freq"] = ui.plotly(_dark_placeholder()).classes("w-full h-56 px-2")

            ui.separator().classes("mx-4 my-2")

            # E2 — Sueños compartidos / entrelazados
            ui.label("Sueños entrelazados (shared_with)").classes(
                "text-xs text-gray-400 uppercase px-4"
            )
            refs["shared_dreams_html"] = ui.html("").classes("px-4 pb-2 text-sm text-gray-300")

            ui.separator().classes("mx-4 my-2")

            with ui.row().classes("px-4 pt-2 gap-8 w-full"):
                with ui.column().classes("flex-1"):
                    ui.label("Registro por tribu").classes(
                        "text-sm font-semibold text-purple-300 mb-2"
                    )
                    refs["dreams_tribe_html"] = ui.html("").classes("text-sm text-gray-300")
                with ui.column().classes("flex-1"):
                    ui.label("Registro por individuo").classes(
                        "text-sm font-semibold text-purple-300 mb-2"
                    )
                    refs["dreams_html"] = ui.html("").classes("text-sm text-gray-300")

        # ── Tab Civilización ──────────────────────────────────────────────────
        with ui.tab_panel(t_civiliz):
            with ui.row().classes("px-4 pt-4 gap-8 w-full"):
                with ui.column().classes("flex-1"):
                    ui.label("Estructuras — Altares, refugios, depósitos").classes(
                        "text-sm font-semibold text-purple-300 mb-2"
                    )
                    refs["structures_html"] = ui.html("").classes("text-sm text-gray-300")
                with ui.column().classes("flex-1"):
                    ui.label("Tecnologías desarrolladas").classes(
                        "text-sm font-semibold text-purple-300 mb-2"
                    )
                    refs["technologies_html"] = ui.html("").classes("text-sm text-gray-300")

            ui.separator().classes("mx-4 mt-3 mb-2")

            # F2 — Memoria cultural y árbol de transmisión
            ui.label("Memoria cultural — Linaje de transmisión").classes(
                "text-xs text-gray-400 uppercase px-4"
            )
            refs["cultural_memory_html"] = ui.html("").classes(
                "px-4 pb-4 text-sm text-gray-300"
            )

        # ── Tab Mapa ──────────────────────────────────────────────────────────
        with ui.tab_panel(t_mapa):
            # D3 — Panel de control de capas
            with ui.row().classes("px-4 py-2 gap-6 flex-wrap items-center"):
                ui.label("Capas:").classes("text-xs text-gray-400 font-semibold")
                refs["layer_niebla"]    = ui.checkbox("Niebla de guerra", value=True).classes("text-xs text-gray-300")
                refs["layer_agentes"]   = ui.checkbox("Agentes",          value=True).classes("text-xs text-green-300")
                refs["layer_muertos"]   = ui.checkbox("Muertos",          value=True).classes("text-xs text-gray-500")
                refs["layer_tumbas"]    = ui.checkbox("Tumbas",           value=True).classes("text-xs text-gray-300")
                refs["layer_fauna"]     = ui.checkbox("Fauna simbólica",  value=True).classes("text-xs text-yellow-300")
                refs["layer_liminales"] = ui.checkbox("Hexes liminales",  value=True).classes("text-xs text-purple-300")
                refs["layer_fuego"]     = ui.checkbox("Fuego",            value=True).classes("text-xs text-red-400")
            refs["hex_plot"] = ui.plotly(_dark_placeholder()).classes("w-full").style("height:82vh")

        # ── Tab Liminal ───────────────────────────────────────────────────────
        if app_state.use_liminal:
            with ui.tab_panel(t_liminal):
                ui.label("Zona Liminal").classes(
                    "text-sm font-semibold px-4 pt-4 text-purple-300"
                )
                refs["lim_hexes"]  = ui.html("").classes("px-4 pb-2 text-xs font-mono text-purple-200")
                ui.separator().classes("mx-4 my-2")
                ui.label("Campo del Multiverso (R5-E2)").classes(
                    "text-xs text-gray-400 uppercase px-4"
                )
                refs["multiverse"] = ui.label("Sin datos de convergencia.").classes(
                    "px-4 py-2 text-purple-100 text-sm"
                )

    # ── Timers de actualización ───────────────────────────────────────────────
    _prev_deaths:     list[int]  = [0]
    _map_tick:        list[int]  = [99]
    _slow_tick:       list[int]  = [99]
    _charts_tick:     list[int]  = [99]
    _prev_n_myths:    list[int]  = [0]    # H2 — detección de nuevos mitos
    _prev_hysteria:   list[bool] = [False]  # H2 — detección histeria
    _notified_deaths: set        = set()   # H2 — agentes destacados ya notificados

    _SIM_COLORS = {"running": "green", "stopped": "red", "paused": "orange", "error": "red"}

    def _refresh() -> None:
        try:
            snap    = app_state.get_snapshot()
            runtime = app_state.get_runtime()
            state_r = runtime.get_state() if runtime else None

            # ── Header ────────────────────────────────────────────────────────
            refs_hdr["dia"].set_text(f"Día {app_state.dia_simulado}")
            refs_hdr["vivos"].set_text(f"{app_state.agentes_vivos} vivos")
            if state_r:
                sim_s = state_r.simulation
                refs_hdr["estado"].set_text(sim_s)
                refs_hdr["estado"].props(f'color="{_SIM_COLORS.get(sim_s,"grey")}"')

            if snap is not None:
                # ── Resumen: clima ─────────────────────────────────────────────
                refs["temp"].set_text(f"{snap.temperatura:.1f}°C")
                refs["estac"].set_text(snap.estacion)
                refs["cc"].set_text(str(snap.carrying_capacity))
                refs["presion"].set_text(f"{snap.resource_pressure:.1%}")
                ec = snap.evento_climatico
                refs["evento_clima"].set_text(ec if ec else "Sin evento climático")
                fuego_txt = (
                    f"🔥 Fuego activo en {snap.fuego_coord} (int. {snap.fuego_intensidad:.2f})"
                    if snap.fuego_activo else ""
                )
                refs["fuego"].set_text(fuego_txt)
                cat = getattr(snap, "catastrofe_activa", None)
                refs["catastrofe"].set_text(
                    f"⚠ CATÁSTROFE: {cat.get('tipo','?')}" if cat else ""
                )

                # ── Liminal ────────────────────────────────────────────────────
                if app_state.use_liminal and "lim_hexes" in refs:
                    lh_lines = []
                    for lh in (snap.liminal_hexes or []):
                        portal = "PORTAL " if lh.get("es_portal") else ""
                        sym    = ", ".join(lh.get("symbol_pool", []))
                        lh_lines.append(
                            f"<span style='color:#bb88ff'>{portal}"
                            f"({lh['coord'][0]},{lh['coord'][1]}) "
                            f"misterio={lh.get('misterio',0):.2f}</span> — {sym}"
                        )
                    refs["lim_hexes"].set_content("<br>".join(lh_lines) or "Sin hexes liminales.")

            # ── Checkpoint (cada ciclo) ────────────────────────────────────────
            cp = load_checkpoint()
            if cp:
                agentes_cp = cp.get("agentes", {})
                agents_list = agentes_cp.get("agents", [])
                alive_list  = [a for a in agents_list if a.get("is_alive", False)]
                t_data      = agentes_cp.get("tribe_manager", {})
                a2t         = t_data.get("agent_to_tribe", {})

                # Tribus activas
                tribes_active = len(set(a2t.get(a.get("id",""),"") for a in alive_list) - {""})
                refs_hdr["tribus"].set_text(f"{tribes_active} tribus")

                # Promedios emocionales
                if alive_list:
                    avg_h = sum(a.get("humor",0.5)    for a in alive_list) / len(alive_list)
                    avg_e = sum(a.get("energia",0.5)  for a in alive_list) / len(alive_list)
                    avg_a = sum(a.get("ansiedad",0.5) for a in alive_list) / len(alive_list)
                    refs["humor"].set_text(f"{avg_h:.2f}")
                    refs["energia"].set_text(f"{avg_e:.2f}")
                    refs["ansiedad"].set_text(f"{avg_a:.2f}")

                # Tensión colectiva
                cf = agentes_cp.get("collective_field", {})
                ep  = cf.get("emotional_pressure", 0.0)
                mp  = cf.get("myth_pressure", 0.0)
                con = cf.get("confusion", 0.0)
                refs["tension_emoc"].set_text(f"{ep:.1%}")
                refs["tension_mito"].set_text(f"{mp:.1%}")
                refs["confusion"].set_text(f"{con:.1%}")
                hyst = cf.get("hysteria_active", False)
                refs["histeria"].set_text(
                    f"⚡ HISTERIA COLECTIVA (int. {cf.get('hysteria_intensity',0):.2f})" if hyst else ""
                )
                # Actualizar colores de barras
                for key, val in [("tension_emoc_bar", ep), ("tension_mito_bar", mp), ("confusion_bar", con)]:
                    color = "#e74c3c" if val > 0.7 else "#f39c12" if val > 0.4 else "#2ecc71"
                    w = int(val * 100)
                    refs[key].set_content(
                        f"<div style='background:#1f2937;border-radius:4px;height:8px;width:100%;margin-top:4px'>"
                        f"<div style='background:{color};width:{w}%;height:8px;border-radius:4px'></div></div>"
                    )

                # G2+G1 — Inspector de agentes con filtros y id para radar
                tf_tribu = refs.get("filter_tribu") and refs["filter_tribu"].value
                tf_arch  = refs.get("filter_arquetipo") and refs["filter_arquetipo"].value
                tf_est   = refs.get("filter_estado") and refs["filter_estado"].value

                # Actualizar opciones de tribu en filtro
                tribe_opts = sorted({a2t.get(a.get("id",""), "—") for a in alive_list})
                if refs.get("filter_tribu"):
                    refs["filter_tribu"].options = ["(todas)"] + tribe_opts
                    refs["filter_tribu"].update()

                rows = []
                for a in alive_list:
                    arch    = a.get("archetypes", {})
                    dom     = max(arch, key=lambda k: arch[k]) if arch else "—"
                    tribu   = a2t.get(a.get("id",""), "—")[:14]
                    estado  = a.get("estado_conductual", "vivo")

                    # G2 — aplicar filtros
                    if tf_tribu and tf_tribu != "(todas)" and tribu[:len(tf_tribu)] != tf_tribu:
                        continue
                    if tf_arch and tf_arch != "(todos)" and dom != tf_arch:
                        continue
                    if tf_est and tf_est != "(todos)" and tf_est not in estado.lower():
                        continue

                    rows.append({
                        "id":        a.get("id", ""),
                        "nombre":    a.get("nombre", "?"),
                        "edad":      a.get("edad", 0),
                        "tribu":     tribu,
                        "arquetipo": dom,
                        "humor":     f"{a.get('humor',0):.2f}",
                        "energia":   f"{a.get('energia',0):.2f}",
                        "ansiedad":  f"{a.get('ansiedad',0):.2f}",
                        "estado":    estado,
                    })
                refs["agents_table"].rows = rows
                refs["agents_table"].update()

                # ICL B1 — Gauges del campo colectivo
                ep  = cf.get("emotional_pressure", 0.0)
                mp  = cf.get("myth_pressure", 0.0)
                con = cf.get("confusion", 0.0)
                fig_gauges = _build_icl_gauges(ep, mp, con)
                if fig_gauges:
                    refs["plot_gauges"].update_figure(fig_gauges)

                # ICL B2 — Símbolos con tooltips y tribu dominante
                symbols    = cf.get("symbols", {})
                lf_data    = t_data.get("local_fields", {})
                fig_sym    = _build_symbol_figure(symbols, lf_data)
                if fig_sym:
                    refs["plot_symbols"].update_figure(fig_sym)

                # ICL B3 — Proto-mitos + mitos activos
                my_data      = agentes_cp.get("mythology_engine", {})
                proto_myths  = my_data.get("proto_myths", [])
                active_myths = my_data.get("active_myths", [])
                refs["proto_myths_html"].set_content(
                    _render_proto_myths_html(proto_myths, active_myths)
                )

                # Mitos cristalizados
                agent_names  = {a["id"]: a["nombre"] for a in agents_list}
                refs["myths_html"].set_content(_render_myths_html(active_myths, agent_names))

                # Léxico
                lex = agentes_cp.get("emergent_lexicon", {})
                refs["lexicon_html"].set_content(_render_lexicon_html(lex))

                # R5-E2 multiverse echo
                if "multiverse" in refs:
                    echo = getattr(
                        getattr(app_state.get_runner(), "agents", None),
                        "_last_multiverse_echo", None
                    )
                    if echo:
                        refs["multiverse"].set_text(
                            f"Símbolo convergente: «{echo.symbol}»  ·  "
                            f"{echo.tribe_count} tribus  ·  intensidad {echo.level:.2f}"
                        )

            # ── Muertes recientes ──────────────────────────────────────────────
            deaths = load_deaths_log(limit=50)
            if len(deaths) != _prev_deaths[0]:
                _prev_deaths[0] = len(deaths)
                refs["deaths_log"].clear()
                for d in deaths[:20]:
                    refs["deaths_log"].push(f"Día {d['dia']} — {d['nombre']} ({d['causa']})")

            # ── Tendencias A1+A2 (cada 3 ciclos = 6s) ────────────────────────
            _charts_tick[0] += 1
            if _charts_tick[0] >= 3:
                _charts_tick[0] = 0
                agent_metrics    = load_agent_metrics()
                climate_metrics  = load_climate_metrics()
                scenario_metrics = load_scenario_metrics()
                clim_events      = load_climate_events()

                fig_emoc = _build_trend_figure(
                    agent_metrics, ["humor", "energia", "ansiedad"],
                    "Humor / Energía / Ansiedad promedio", yrange=[0, 1.05]
                )
                if fig_emoc:
                    refs["plot_emoc"].update_figure(fig_emoc)

                fig_pop = _build_trend_figure(
                    agent_metrics, ["vivos"], "Población viva",
                )
                if fig_pop:
                    refs["plot_poblacion"].update_figure(fig_pop)

                # A1 — Temperatura con bandas de eventos climáticos
                fig_clima = _build_trend_figure(
                    climate_metrics, ["temperatura", "riesgo"],
                    "Temperatura (°C) · Riesgo supervivencia",
                    events=clim_events,
                )
                if fig_clima:
                    refs["plot_clima"].update_figure(fig_clima)

                fig_res = _build_trend_figure(
                    scenario_metrics, ["resource_pressure", "carrying_capacity"],
                    "Presión de recursos · Carrying capacity", yrange=[0, None]
                )
                if fig_res:
                    refs["plot_recursos"].update_figure(fig_res)

                # A2 — Métricas de emergencia cultural
                emerg_data = load_emergence_metrics(last_n_days=300)
                fig_emerg  = _build_emergence_figure(emerg_data)
                if fig_emerg:
                    refs["plot_emergence"].update_figure(fig_emerg)

            # ── Mapa D1/D2/D3 (cada 3 ciclos = 6s) ──────────────────────────
            _map_tick[0] += 1
            if _map_tick[0] >= 3 and snap is not None:
                _map_tick[0] = 0
                runner_now = app_state.get_runner()
                agents_now = _extract_agents_data(runner_now) if runner_now else []
                # terrain._explored_set es más completo que snap.recursos_por_hex
                try:
                    exp_coords = frozenset(runner_now.world.terrain._explored_set) if runner_now else None
                except Exception as e:
                    import sys
                    print(f"[UI] _explored_set: {e}", file=sys.stderr)
                    exp_coords = None
                layer_flags = {
                    "niebla":    refs.get("layer_niebla")    and refs["layer_niebla"].value,
                    "agentes":   refs.get("layer_agentes")   and refs["layer_agentes"].value,
                    "muertos":   refs.get("layer_muertos")   and refs["layer_muertos"].value,
                    "tumbas":    refs.get("layer_tumbas")    and refs["layer_tumbas"].value,
                    "fauna":     refs.get("layer_fauna")     and refs["layer_fauna"].value,
                    "liminales": refs.get("layer_liminales") and refs["layer_liminales"].value,
                    "fuego":     refs.get("layer_fuego")     and refs["layer_fuego"].value,
                }
                new_fig = _build_hex_map(snap, terrain_biomes, agents_now, layer_flags, exp_coords)
                if new_fig:
                    refs["hex_plot"].update_figure(new_fig)

            # ── Lento: Red Social + Sueños + Civilización (cada 15 ciclos = 30s)
            _slow_tick[0] += 1
            if _slow_tick[0] >= 15:
                _slow_tick[0] = 0
                cp_slow = load_checkpoint()
                if cp_slow:
                    # C1 — Red social (spring layout)
                    fig_social = _build_social_graph(cp_slow)
                    if fig_social:
                        refs["plot_social"].update_figure(fig_social)

                    # C2 + C3 — Stats de red y tabla de aristas
                    _agents_sl  = cp_slow.get("agentes", {}).get("agents", [])
                    _alive_sl   = {a["id"]: a for a in _agents_sl if a.get("is_alive", False)}
                    _t_data_sl  = cp_slow.get("agentes", {}).get("tribe_manager", {})
                    _a2t_sl     = _t_data_sl.get("agent_to_tribe", {})
                    _edges_sl   = cp_slow.get("agentes", {}).get("social_network", {}).get("edges", [])

                    # C3 — Stats
                    st = _social_stats(_alive_sl, _edges_sl)
                    refs["soc_nodos"].set_text(f"Nodos vivos: {st['n_nodos']}")
                    refs["soc_aristas"].set_text(f"Aristas activas: {st['n_aristas']}")
                    refs["soc_cluster"].set_text(f"Clusters: {st['n_clusters']}")
                    refs["soc_hub"].set_text(f"Hub: {st['hub']} ({st['hub_grado']})")
                    refs["soc_ent"].set_text(f"Entrelazados: {st['n_entrelazados']}")

                    # Actualizar opciones del filtro de tribu
                    tribe_ids = sorted({_a2t_sl.get(aid,"?") for aid in _alive_sl})
                    refs["soc_tribe_filter"].options = ["(todas)"] + tribe_ids
                    refs["soc_tribe_filter"].update()

                    # C2 — Tabla de aristas
                    tribe_sel = refs["soc_tribe_filter"].value
                    tf = "" if tribe_sel == "(todas)" else tribe_sel
                    refs["soc_edge_table"].set_content(
                        _render_edge_table_html(_alive_sl, _edges_sl, _a2t_sl, tf)
                    )

                    # Sueños
                    refs["dreams_html"].set_content(_render_dreams_html(cp_slow))
                    refs["dreams_tribe_html"].set_content(_render_dreams_by_tribe_html(cp_slow))

                    # Civilización
                    refs["structures_html"].set_content(_render_structures_html(cp_slow))
                    refs["technologies_html"].set_content(_render_technologies_html(cp_slow))

                    # E1 — Frecuencia simbólica en sueños vs carga ICL
                    fig_dream_freq = _build_dream_frequency_figure(cp_slow)
                    if fig_dream_freq:
                        refs["plot_dream_freq"].update_figure(fig_dream_freq)

                    # E2 — Sueños entrelazados
                    refs["shared_dreams_html"].set_content(
                        _render_shared_dreams_html(cp_slow)
                    )

                    # F2 — Memoria cultural y linaje de transmisión
                    refs["cultural_memory_html"].set_content(
                        _render_cultural_memory_html(cp_slow)
                    )

                    # H2 — Notificación: nuevo mito cristalizado
                    _my_data_sl = cp_slow.get("agentes", {}).get("mythology_engine", {})
                    _active_sl  = _my_data_sl.get("active_myths", [])
                    n_myths_now = len(_active_sl)
                    if n_myths_now > _prev_n_myths[0] and _prev_n_myths[0] > 0:
                        new_m = _active_sl[-1] if _active_sl else {}
                        par   = " vs ".join(new_m.get("par", []))
                        ui.notify(
                            f"Nuevo mito: {new_m.get('tipo','?')} — {par}",
                            type="positive", timeout=8000,
                        )
                    _prev_n_myths[0] = n_myths_now

                    # H2 — Notificación: histeria colectiva activada
                    _cf_sl   = cp_slow.get("agentes", {}).get("collective_field", {})
                    hyst_now = _cf_sl.get("hysteria_active", False)
                    if hyst_now and not _prev_hysteria[0]:
                        ui.notify(
                            f"⚡ HISTERIA COLECTIVA "
                            f"(intensidad {_cf_sl.get('hysteria_intensity', 0):.2f})",
                            type="warning", timeout=0,
                        )
                    _prev_hysteria[0] = hyst_now

                    # H2 — Notificación: muerte de agente arquetípicamente destacado
                    for ag in cp_slow.get("agentes", {}).get("agents", []):
                        if ag.get("is_alive", True):
                            continue
                        aid = ag.get("id", "")
                        if not aid or aid in _notified_deaths:
                            continue
                        arch    = ag.get("archetypes", {})
                        dom_val = max(arch.values()) if arch else 0.0
                        if dom_val >= 0.70:
                            dom_name = max(arch, key=arch.get) if arch else "—"
                            _notified_deaths.add(aid)
                            ui.notify(
                                f"✝ {ag.get('nombre','?')} — {dom_name} {dom_val:.2f}",
                                type="info", timeout=10000,
                            )

        except Exception as e:
            import sys, traceback
            print(f"[UI] _refresh: {e}\n{traceback.format_exc()}", file=sys.stderr)

    ui.timer(2.0, _refresh)


# ── Lanzamiento ───────────────────────────────────────────────────────────────

def launch_ui(app_state,
              DB_PATH=None, CP_DIR=None, SEEDS_DIR=None,
              LIMINAL_SERVER=None) -> None:
    from nicegui import ui

    DB_PATH        = DB_PATH        or ROOT / "data" / "db" / "simulation.db"
    CP_DIR         = CP_DIR         or ROOT / "data" / "checkpoints"
    SEEDS_DIR      = SEEDS_DIR      or ROOT / "data" / "seeds"
    LIMINAL_SERVER = LIMINAL_SERVER or ROOT / "liminal_server" / "main.py"

    @ui.page("/")
    def launcher():
        build_launcher_page(app_state, DB_PATH, CP_DIR, SEEDS_DIR, LIMINAL_SERVER)

    @ui.page("/monitor")
    def monitor():
        build_monitor_page(app_state)

    ui.run(
        title             = "PSYCHE SIMULACRA",
        port              = 8080,
        dark              = True,
        show              = True,
        favicon           = "🧠",
        reload            = False,
        reconnect_timeout = 10,
    )
