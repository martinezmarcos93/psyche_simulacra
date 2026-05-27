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
    "pradera": "#5a8a3c", "bosque": "#2d6b2d", "desierto": "#c8a55a",
    "tundra": "#8888aa", "montana": "#888888", "montaña": "#888888",
    "montana_alta": "#aaaaaa", "costa": "#3d7aad", "agua": "#1a5280",
    "pantano": "#4a6b4a", "pantano_costero": "#3d5e50",
    "cueva": "#444455", "llanura": "#a0b870",
}
_DEFAULT_BIOME = "#555566"
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
    except Exception:
        return {}


def _extract_agents_data(runner) -> list[dict]:
    """Lee posición y metadata de todos los agentes en vivo para el mapa."""
    try:
        ac  = runner.agents
        mgr = ac.tribe_manager
        out = []
        for agent_id, agent in ac.agents.items():
            tribe = mgr.get_tribe_id(agent_id) or ""
            bs    = agent.behavioral_state
            estado = (
                bs.estado.value if hasattr(bs, "estado") and hasattr(bs.estado, "value")
                else str(bs)
            )
            out.append({
                "id":       agent_id,
                "nombre":   agent.nombre,
                "pos":      agent.posicion,
                "alive":    agent.is_alive,
                "humor":    round(agent.humor, 2),
                "edad":     getattr(agent, "edad", 0),
                "arquetipo": agent.archetypes.dominant(),
                "estado":   estado,
                "tribu":    tribe,
            })
        return out
    except Exception:
        return []


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
            marker=dict(symbol="circle", size=5, color="#14082a", opacity=0.75, line=dict(width=0)),
            hoverinfo="skip", name="Niebla",
            visible=_vis("niebla"),
        ))

    # ── D1b: Terreno explorado ───────────────────────────────────────────────
    if exp_xs:
        traces.append(go.Scattergl(
            x=exp_xs, y=exp_ys, mode="markers",
            marker=dict(symbol="circle", size=9, color=exp_colors, line=dict(width=0)),
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
                marker=dict(symbol="circle", size=11, color=color,
                            line=dict(width=1.5, color="#000000")),
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


def _build_trend_figure(rows: list[dict], fields: list[str], title: str,
                        yrange: list | None = None):
    try:
        import plotly.graph_objects as go
    except ImportError:
        return None
    if not rows:
        return None
    dias = [r["dia"] for r in rows]
    COLORS = ["#00D2B4", "#E040FB", "#FF4B4B", "#F4D03F", "#4a9eff"]
    traces = []
    for i, f in enumerate(fields):
        vals = [r.get(f) for r in rows]
        vals = [v if v is not None else 0 for v in vals]
        traces.append(go.Scatter(x=dias, y=vals, mode="lines", name=f,
                                 line=dict(color=COLORS[i % len(COLORS)], width=2)))
    fig = go.Figure(data=traces)
    yaxis_cfg = dict(color="#aaa", gridcolor="#1f2937")
    if yrange:
        yaxis_cfg["range"] = yrange
    fig.update_layout(
        title=dict(text=title, font=dict(color="#ccc", size=13)),
        paper_bgcolor="#111827", plot_bgcolor="#111827",
        showlegend=True, legend=dict(font=dict(color="#aaa")),
        margin=dict(l=40, r=10, t=40, b=30),
        xaxis=dict(color="#aaa", gridcolor="#1f2937"),
        yaxis=yaxis_cfg,
    )
    return fig


def _build_symbol_figure(symbols: dict):
    try:
        import plotly.graph_objects as go
    except ImportError:
        return None
    if not symbols:
        return None
    items = sorted(symbols.items(), key=lambda x: x[1])
    names  = [k.replace("_", " ").capitalize() for k, _ in items]
    values = [v for _, v in items]
    colors = [_ARCH_COLORS.get(k, "#888") for k, _ in items]
    fig = go.Figure(go.Bar(x=values, y=names, orientation="h",
                           marker=dict(color=colors),
                           text=[f"{v:.2f}" for v in values], textposition="outside"))
    fig.update_layout(
        paper_bgcolor="#111827", plot_bgcolor="#111827",
        margin=dict(l=120, r=50, t=10, b=20),
        xaxis=dict(range=[0, 1.1], color="#aaa", gridcolor="#1f2937"),
        yaxis=dict(color="#aaa"),
        showlegend=False,
    )
    return fig


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


# ── Helper UI ─────────────────────────────────────────────────────────────────

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

            with ui.row().classes("gap-4 w-full"):
                if summ["vivos"] > 0:
                    async def _continue():
                        await _start_sim(app_state, mode="resume",
                                         use_liminal=use_liminal.value,
                                         liminal_server=LIMINAL_SERVER)
                    ui.button("Continuar simulación", on_click=_continue).classes(
                        "flex-1 bg-purple-700 hover:bg-purple-600 text-white"
                    )

                async def _new():
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
        except Exception:
            pass

    def _run():
        try:
            runner.run(n_days=None)
        except Exception:
            pass
        finally:
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
        with ui.row().classes("gap-6 ml-4"):
            refs_hdr["dia"]    = ui.label("Día —").classes("text-purple-200 text-sm")
            refs_hdr["vivos"]  = ui.label("Agentes —").classes("text-green-300 text-sm")
            refs_hdr["tribus"] = ui.label("Tribus —").classes("text-blue-300 text-sm")
            refs_hdr["estado"] = ui.badge("—", color="grey").classes("text-xs")

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
            refs["plot_emoc"]     = ui.plotly({}).classes("w-full h-56 px-2")
            ui.label("Población viva").classes(
                "text-xs text-gray-400 uppercase px-4 pt-2"
            )
            refs["plot_poblacion"] = ui.plotly({}).classes("w-full h-44 px-2")
            ui.label("Temperatura y riesgo climático").classes(
                "text-xs text-gray-400 uppercase px-4 pt-2"
            )
            refs["plot_clima"]    = ui.plotly({}).classes("w-full h-44 px-2")
            ui.label("Presión de recursos / Carrying capacity").classes(
                "text-xs text-gray-400 uppercase px-4 pt-2"
            )
            refs["plot_recursos"] = ui.plotly({}).classes("w-full h-44 px-2")

        # ── Tab ICL ───────────────────────────────────────────────────────────
        with ui.tab_panel(t_icl):
            ui.label("Carga Memética de Símbolos Arquetípicos").classes(
                "text-sm font-semibold px-4 pt-4 text-purple-300"
            )
            refs["plot_symbols"] = ui.plotly({}).classes("w-full h-64 px-2")

            ui.separator().classes("mx-4 my-2")
            ui.label("Mitología emergente").classes("text-xs text-gray-400 uppercase px-4")
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

            refs["plot_social"] = ui.plotly({}).classes("w-full px-2").style("height:58vh")

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
            ).classes("w-full px-4")

        # ── Tab Sueños ────────────────────────────────────────────────────────
        with ui.tab_panel(t_suenos):
            with ui.row().classes("px-4 pt-4 gap-8 w-full"):
                with ui.column().classes("flex-1"):
                    ui.label("Registro de sueños — Por tribu").classes(
                        "text-sm font-semibold text-purple-300 mb-2"
                    )
                    refs["dreams_tribe_html"] = ui.html("").classes("text-sm text-gray-300")
                with ui.column().classes("flex-1"):
                    ui.label("Registro de sueños — Por individuo").classes(
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
            refs["hex_plot"] = ui.plotly({}).classes("w-full").style("height:82vh")

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
    _prev_deaths: list[int]  = [0]
    _map_tick:    list[int]  = [0]
    _slow_tick:   list[int]  = [0]   # para social graph, sueños, civilización
    _charts_tick: list[int]  = [0]

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

                # Inspector de agentes
                rows = []
                for a in alive_list:
                    arch = a.get("archetypes", {})
                    dom  = max(arch, key=lambda k: arch[k]) if arch else "—"
                    rows.append({
                        "nombre":    a.get("nombre", "?"),
                        "edad":      a.get("edad", 0),
                        "tribu":     a2t.get(a.get("id",""), "—")[:14],
                        "arquetipo": dom,
                        "humor":     f"{a.get('humor',0):.2f}",
                        "energia":   f"{a.get('energia',0):.2f}",
                        "ansiedad":  f"{a.get('ansiedad',0):.2f}",
                        "estado":    "vivo",
                    })
                refs["agents_table"].rows = rows
                refs["agents_table"].update()

                # ICL: símbolos
                symbols = cf.get("symbols", {})
                fig_sym = _build_symbol_figure(symbols)
                if fig_sym:
                    refs["plot_symbols"].update_figure(fig_sym)

                # Mitos
                my_data     = agentes_cp.get("mythology_engine", {})
                active_myths = [m for m in my_data.get("active_myths", []) if m.get("active")]
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

            # ── Tendencias (cada 3 ciclos = 6s) ──────────────────────────────
            _charts_tick[0] += 1
            if _charts_tick[0] >= 3:
                _charts_tick[0] = 0
                agent_metrics   = load_agent_metrics()
                climate_metrics = load_climate_metrics()
                scenario_metrics = load_scenario_metrics()

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

                fig_clima = _build_trend_figure(
                    climate_metrics, ["temperatura", "riesgo"],
                    "Temperatura (°C) · Riesgo supervivencia",
                )
                if fig_clima:
                    refs["plot_clima"].update_figure(fig_clima)

                fig_res = _build_trend_figure(
                    scenario_metrics, ["resource_pressure", "carrying_capacity"],
                    "Presión de recursos · Carrying capacity", yrange=[0, None]
                )
                if fig_res:
                    refs["plot_recursos"].update_figure(fig_res)

            # ── Mapa D1/D2/D3 (cada 3 ciclos = 6s) ──────────────────────────
            _map_tick[0] += 1
            if _map_tick[0] >= 3 and snap is not None:
                _map_tick[0] = 0
                runner_now = app_state.get_runner()
                agents_now = _extract_agents_data(runner_now) if runner_now else []
                layer_flags = {
                    "niebla":    refs.get("layer_niebla")    and refs["layer_niebla"].value,
                    "agentes":   refs.get("layer_agentes")   and refs["layer_agentes"].value,
                    "muertos":   refs.get("layer_muertos")   and refs["layer_muertos"].value,
                    "tumbas":    refs.get("layer_tumbas")    and refs["layer_tumbas"].value,
                    "fauna":     refs.get("layer_fauna")     and refs["layer_fauna"].value,
                    "liminales": refs.get("layer_liminales") and refs["layer_liminales"].value,
                    "fuego":     refs.get("layer_fuego")     and refs["layer_fuego"].value,
                }
                new_fig = _build_hex_map(snap, terrain_biomes, agents_now, layer_flags)
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

        except Exception:
            pass

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
