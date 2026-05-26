"""
Interfaz NiceGUI para PSYCHE SIMULACRA.

Fase 5 — stats en tiempo real: día, agentes, tribus, clima, eventos narrativos.
Fase 6 — mapa hex interactivo con Plotly: biomas, recursos, fuego, liminal, tumbas.
Fase 7 — Zona Liminal integrada como tab; campo del multiverso (R5-E2) visible.

Doctrinas respetadas:
  B — la sim existe sin observers; la UI nunca inicia ni detiene la sim.
  C — interfaz solo epistemológica: observar, no controlar.
"""
from __future__ import annotations

import math
import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.runtime.psyche_runtime import PsycheRuntime
    from core.simulation import SimulationRunner

# ── Paleta de colores ─────────────────────────────────────────────────────────

_BIOME_COLORS: dict[str, str] = {
    "pradera":         "#5a8a3c",
    "bosque":          "#2d6b2d",
    "desierto":        "#c8a55a",
    "tundra":          "#8888aa",
    "montana":         "#888888",
    "montaña":         "#888888",
    "montana_alta":    "#aaaaaa",
    "costa":           "#3d7aad",
    "agua":            "#1a5280",
    "pantano":         "#4a6b4a",
    "pantano_costero": "#3d5e50",
    "cueva":           "#444455",
    "llanura":         "#a0b870",
}
_DEFAULT_BIOME_COLOR = "#555566"
_LIMINAL_COLOR       = "#9b59b6"
_FIRE_COLOR          = "#e74c3c"
_GRAVE_COLOR         = "#bdc3c7"
_FAUNA_COLOR         = "#f39c12"
_MULTIVERSE_COLOR    = "#bb88ff"

# ── Hex geometry ──────────────────────────────────────────────────────────────

_HEX_SIZE = 8.0  # unidades Plotly por hex (flat-top)

def _hex_xy(q: int, r: int) -> tuple[float, float]:
    x = _HEX_SIZE * 1.5 * q
    y = _HEX_SIZE * math.sqrt(3) * (r + 0.5 * (q & 1))
    return x, y

# ── Extracción de terreno (una vez) ───────────────────────────────────────────

def _extract_terrain(runner) -> dict[tuple[int, int], str]:
    try:
        cells = runner.world.terrain._cells
        return {coord: cell.biome for coord, cell in cells.items()}
    except Exception:
        return {}

# ── Helpers de construcción de figuras Plotly ─────────────────────────────────

def _build_hex_figure(snap: dict, terrain_biomes: dict[tuple[int, int], str]):
    try:
        import plotly.graph_objects as go
    except ImportError:
        return None

    # ── Terreno base ──────────────────────────────────────────────────────────
    if terrain_biomes:
        coords = list(terrain_biomes.keys())
    else:
        rph = snap.get("recursos_por_hex") or {}
        coords = list(rph.keys())

    xs, ys, colors, texts = [], [], [], []
    for coord in coords:
        if isinstance(coord, str):
            try:
                parts = coord.strip("()[] ").split(",")
                coord = (int(parts[0]), int(parts[1]))
            except Exception:
                continue
        q, r = coord
        x, y = _hex_xy(q, r)
        biome = terrain_biomes.get((q, r), "")
        color = _BIOME_COLORS.get(biome, _DEFAULT_BIOME_COLOR)
        xs.append(x); ys.append(y); colors.append(color)
        texts.append(f"({q},{r})<br>{biome}")

    traces: list = [go.Scatter(
        x=xs, y=ys, mode="markers",
        marker=dict(symbol="hexagon", size=10, color=colors, line=dict(width=0)),
        text=texts, hoverinfo="text", name="Terreno",
    )]

    # ── Hexes liminales ───────────────────────────────────────────────────────
    lhexes = snap.get("liminal_hexes") or []
    if lhexes:
        lx, ly, lt = [], [], []
        for lh in lhexes:
            q, r = lh["coord"]
            x, y = _hex_xy(q, r)
            lx.append(x); ly.append(y)
            sym = ", ".join(lh.get("symbol_pool", []))
            lt.append(f"Liminal ({q},{r})<br>Misterio: {lh.get('misterio', 0):.2f}<br>{sym}")
        traces.append(go.Scatter(
            x=lx, y=ly, mode="markers",
            marker=dict(symbol="hexagon-open", size=16, color=_LIMINAL_COLOR, line=dict(width=2)),
            text=lt, hoverinfo="text", name="Liminal",
        ))

    # ── Tumbas activas ────────────────────────────────────────────────────────
    graves = snap.get("graves_activos") or []
    if graves:
        gx, gy = [], []
        for g in graves:
            coord_g = g[0] if isinstance(g, (list, tuple)) and len(g) > 0 else None
            if coord_g is None:
                continue
            q, r = coord_g
            x, y = _hex_xy(q, r)
            gx.append(x); gy.append(y)
        if gx:
            traces.append(go.Scatter(
                x=gx, y=gy, mode="markers",
                marker=dict(symbol="star", size=12, color=_GRAVE_COLOR),
                name="Tumbas", hoverinfo="skip",
            ))

    # ── Fauna simbólica ───────────────────────────────────────────────────────
    fauna = snap.get("fauna_simbolica") or []
    if fauna:
        fx, fy, ft = [], [], []
        for f in fauna:
            coord_f = f.get("coord")
            if coord_f is None:
                continue
            q, r = coord_f
            x, y = _hex_xy(q, r)
            fx.append(x); fy.append(y)
            ft.append(f.get("nombre", "bestia"))
        traces.append(go.Scatter(
            x=fx, y=fy, mode="markers",
            marker=dict(symbol="triangle-up", size=14, color=_FAUNA_COLOR),
            text=ft, hoverinfo="text", name="Fauna simbólica",
        ))

    # ── Fuego ─────────────────────────────────────────────────────────────────
    if snap.get("fuego_activo") and snap.get("fuego_coord"):
        q, r = snap["fuego_coord"]
        x, y = _hex_xy(q, r)
        traces.append(go.Scatter(
            x=[x], y=[y], mode="markers+text",
            marker=dict(symbol="circle", size=20, color=_FIRE_COLOR, opacity=0.9),
            text=["🔥"], textposition="middle center",
            name="Fuego", hoverinfo="skip",
        ))

    fig = go.Figure(data=traces)
    fig.update_layout(
        paper_bgcolor="#1a0a2e",
        plot_bgcolor ="#1a0a2e",
        showlegend   =True,
        legend=dict(font=dict(color="#cccccc"), bgcolor="rgba(0,0,0,0.5)"),
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False,
                   scaleanchor="y", scaleratio=1),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        hovermode="closest",
    )
    return fig


def _build_liminal_figure(snap: dict):
    """Mapa pequeño mostrando solo los hexes liminales del mundo."""
    try:
        import plotly.graph_objects as go
    except ImportError:
        return None

    lhexes = snap.get("liminal_hexes") or []
    if not lhexes:
        return None

    SIZE = 40.0
    xs, ys, colors, texts = [], [], [], []
    for lh in lhexes:
        q, r = lh["coord"]
        x = SIZE * 1.5 * q
        y = SIZE * math.sqrt(3) * (r + 0.5 * (q & 1))
        es_portal = lh.get("es_portal", False)
        misterio  = lh.get("misterio", 0.5)
        sym = ", ".join(lh.get("symbol_pool", []))
        xs.append(x); ys.append(y)
        colors.append("#dd44ff" if es_portal else "#6c3483")
        texts.append(
            f"({'PORTAL' if es_portal else 'liminal'}) ({q},{r})<br>"
            f"Misterio: {misterio:.2f}<br>Símbolos: {sym}"
        )

    fig = go.Figure(go.Scatter(
        x=xs, y=ys, mode="markers",
        marker=dict(symbol="hexagon", size=50, color=colors,
                    line=dict(width=2, color="#bb88ff")),
        text=texts, hoverinfo="text",
    ))
    fig.update_layout(
        paper_bgcolor="#0d001a",
        plot_bgcolor ="#0d001a",
        showlegend=False,
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
    )
    return fig


# ── Construcción de la página principal ──────────────────────────────────────

def _stat_card(title: str, value: str):
    from nicegui import ui
    with ui.card().classes("p-4 bg-gray-800 text-white rounded-xl"):
        ui.label(title).classes("text-xs text-gray-400 uppercase tracking-wider mb-1")
        val = ui.label(value).classes("text-2xl font-bold text-purple-300")
    return val


def _build_main_page(runtime, runner, terrain_biomes: dict) -> None:
    from nicegui import ui

    # ── Header ────────────────────────────────────────────────────────────────
    with ui.header().classes("bg-purple-950 text-white shadow-lg"):
        with ui.row().classes("items-center gap-4 px-4"):
            ui.label("PSYCHE SIMULACRA").classes("text-xl font-bold tracking-widest")
            ui.label("observación continua").classes("text-xs text-purple-300")

    # ── Tabs ──────────────────────────────────────────────────────────────────
    with ui.tabs().classes("bg-purple-900 text-white w-full") as tabs:
        t_estado  = ui.tab("Estado")
        t_mapa    = ui.tab("Mapa")
        t_liminal = ui.tab("Zona Liminal")

    refs: dict = {}

    with ui.tab_panels(tabs, value=t_estado).classes("w-full bg-gray-900 flex-1"):

        # ── Tab: Estado ───────────────────────────────────────────────────────
        with ui.tab_panel(t_estado):
            with ui.grid(columns=3).classes("w-full gap-4 p-4"):
                refs["dia"]    = _stat_card("Día simulado", "—")
                refs["vivos"]  = _stat_card("Agentes vivos", "—")
                refs["tribus"] = _stat_card("Tribus activas", "—")

            with ui.grid(columns=3).classes("w-full gap-4 p-4"):
                refs["temp"]   = _stat_card("Temperatura", "—")
                refs["estac"]  = _stat_card("Estación", "—")
                refs["cc"]     = _stat_card("Carrying capacity", "—")

            with ui.card().classes("mx-4 mb-4 bg-gray-800"):
                with ui.row().classes("items-center gap-2 p-3"):
                    ui.label("Sim").classes("text-xs text-gray-400")
                    refs["sim_state"] = ui.badge("—", color="grey").classes("text-xs")
                    ui.label("Ollama").classes("text-xs text-gray-400 ml-4")
                    refs["ollama_state"] = ui.badge("—", color="grey").classes("text-xs")

            ui.separator().classes("mx-4")
            ui.label("Eventos narrativos").classes("text-sm font-semibold px-4 pt-4 text-gray-300")
            refs["log"] = ui.log(max_lines=30).classes("h-48 mx-4 mb-4 bg-gray-950 text-green-300")

        # ── Tab: Mapa ─────────────────────────────────────────────────────────
        with ui.tab_panel(t_mapa):
            ui.label(
                "Mapa del mundo — solo observacional. "
                "Click en un hex para ver detalles."
            ).classes("text-xs text-gray-400 px-4 py-2")

            initial_snap = runtime.get_current_snapshot() or {}
            initial_fig  = _build_hex_figure(initial_snap, terrain_biomes)
            if initial_fig is not None:
                refs["hex_plot"] = ui.plotly(initial_fig).classes("w-full").style("height:75vh")
            else:
                refs["hex_plot"] = None
                ui.label("Esperando datos del mapa...").classes("p-4 text-gray-400")

        # ── Tab: Zona Liminal ─────────────────────────────────────────────────
        with ui.tab_panel(t_liminal):
            ui.label("Hexágonos liminales del mundo").classes(
                "text-sm font-semibold px-4 pt-4 text-purple-300"
            )
            ui.label(
                "Umbrales entre lo manifiesto y el inconsciente. "
                "Los agentes que los visitan experimentan símbolos sin origen conocido."
            ).classes("text-xs text-purple-400 px-4 pb-2")

            initial_lim_fig = _build_liminal_figure(initial_snap)
            if initial_lim_fig is not None:
                refs["lim_plot"] = ui.plotly(initial_lim_fig).classes("w-full h-64")
            else:
                refs["lim_plot"] = None
                ui.label("Sin hexes liminales detectados.").classes("p-4 text-gray-400")

            ui.separator().classes("mx-4 my-4")
            ui.label("Campo del Multiverso (R5-E2)").classes(
                "text-sm font-semibold px-4 text-purple-200"
            )
            ui.label(
                "Cuando varias tribus convergen en el mismo símbolo, "
                "ese arquetipo resuena en toda la Zona Liminal como eco del inconsciente colectivo."
            ).classes("text-xs text-purple-400 px-4 pb-2")
            refs["multiverse"] = ui.label("Sin datos de convergencia simbólica.").classes(
                "px-4 py-2 text-purple-100 text-sm font-mono"
            )

    # ── Timer: refrescar stats y mapa ─────────────────────────────────────────
    _prev_dia: list[int] = [-1]
    _map_tick: list[int] = [0]

    _SIM_COLORS  = {"running": "green", "stopped": "red", "paused": "orange", "error": "red"}
    _SVC_COLORS  = {"running": "green", "stopped": "grey", "starting": "yellow", "error": "red"}

    def refresh() -> None:
        try:
            state = runtime.get_state()
            snap  = runtime.get_current_snapshot() or {}

            # ── Stats ──────────────────────────────────────────────────────────
            refs["dia"].set_text(str(state.dia_simulado))
            refs["vivos"].set_text(str(state.agentes_vivos))
            refs["tribus"].set_text(str(state.tribus_activas))

            temp = snap.get("temperatura")
            refs["temp"].set_text(f"{temp:.1f}°" if isinstance(temp, float) else "—")
            refs["estac"].set_text(snap.get("estacion") or "—")
            cc = snap.get("carrying_capacity")
            refs["cc"].set_text(str(cc) if cc is not None else "—")

            # Badges de estado
            sim_s = state.simulation
            refs["sim_state"].set_text(sim_s)
            refs["sim_state"].props(f'color="{_SIM_COLORS.get(sim_s, "grey")}"')
            oll_s = state.ollama
            refs["ollama_state"].set_text(oll_s)
            refs["ollama_state"].props(f'color="{_SVC_COLORS.get(oll_s, "grey")}"')

            # ── Log de eventos ─────────────────────────────────────────────────
            if state.dia_simulado != _prev_dia[0]:
                _prev_dia[0] = state.dia_simulado
                if state.ultimo_evento:
                    refs["log"].push(
                        f"[Día {state.dia_simulado}] {state.ultimo_evento}"
                    )

            # ── Mapa (refrescar cada 10s para no saturar) ─────────────────────
            _map_tick[0] += 1
            if _map_tick[0] >= 5 and refs.get("hex_plot") is not None:
                _map_tick[0] = 0
                new_fig = _build_hex_figure(snap, terrain_biomes)
                if new_fig is not None:
                    refs["hex_plot"].update_figure(new_fig)

            # ── Liminal ────────────────────────────────────────────────────────
            if refs.get("lim_plot") is not None:
                new_lim = _build_liminal_figure(snap)
                if new_lim is not None:
                    refs["lim_plot"].update_figure(new_lim)

            # ── R5-E2: campo del multiverso ────────────────────────────────────
            mv = snap.get("multiverse_echo")
            if mv and mv.get("symbol"):
                n     = mv.get("tribe_count", 0)
                sym   = mv["symbol"]
                level = mv.get("level", 0.0)
                refs["multiverse"].set_text(
                    f"Símbolo convergente: «{sym}»  ·  {n} tribus  ·  intensidad {level:.2f}"
                )

        except Exception:
            pass

    ui.timer(2.0, refresh)


# ── Lanzamiento ───────────────────────────────────────────────────────────────

def launch_ui(runtime, runner) -> None:
    """
    Lanza la interfaz NiceGUI en el hilo actual (bloqueante).
    La simulación debe correr en un hilo separado antes de llamar a esto.
    """
    try:
        from nicegui import ui
    except ImportError:
        raise RuntimeError("nicegui no instalado: pip install nicegui")

    terrain_biomes = _extract_terrain(runner)

    @ui.page("/")
    def index():
        _build_main_page(runtime, runner, terrain_biomes)

    ui.run(
        title             = "PSYCHE SIMULACRA",
        port              = 8080,
        dark              = True,
        show              = True,
        favicon           = "🧠",
        reload            = False,
        log_level         = "warning",
        reconnect_timeout = 5,      # termina el proceso 5s después de cerrar el browser
    )
