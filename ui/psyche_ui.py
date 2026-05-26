"""
Interfaz NiceGUI de PSYCHE SIMULACRA.

Página /        — Launcher: estado del checkpoint + botones de inicio.
Página /monitor — Monitoreo en tiempo real: mapa, stats, gráficos, agentes.

Doctrinas respetadas:
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
    "heroe": "#00D2B4", "sombra": "#FF4B4B", "madre": "#E040FB",
    "padre": "#4a9eff", "sabio": "#F4D03F", "trickster": "#FF9F43",
    "rebelde": "#e74c3c", "gobernante": "#8e44ad", "nino_divino": "#2ecc71",
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _hex_xy(q: int, r: int) -> tuple[float, float]:
    return _HEX_SIZE * 1.5 * q, _HEX_SIZE * math.sqrt(3) * (r + 0.5 * (q & 1))


def _extract_terrain(runner) -> dict[tuple[int, int], str]:
    try:
        return {coord: cell.biome for coord, cell in runner.world.terrain._cells.items()}
    except Exception:
        return {}


# ── Figuras Plotly ────────────────────────────────────────────────────────────

def _build_hex_map(snap, terrain_biomes: dict) -> "go.Figure | None":
    try:
        import plotly.graph_objects as go
    except ImportError:
        return None
    if snap is None and not terrain_biomes:
        return None

    xs, ys, colors, texts = [], [], [], []
    coords = list(terrain_biomes.keys()) if terrain_biomes else []

    # Si no hay terreno precargado, usar los hexes del snapshot
    if not coords and snap is not None:
        rph = getattr(snap, "recursos_por_hex", {}) or {}
        coords = list(rph.keys())

    for coord in coords:
        q, r = coord
        x, y = _hex_xy(q, r)
        biome = terrain_biomes.get(coord, "")
        xs.append(x); ys.append(y)
        colors.append(_BIOME_COLORS.get(biome, _DEFAULT_BIOME))
        texts.append(f"({q},{r}) {biome}")

    traces: list = [go.Scatter(
        x=xs, y=ys, mode="markers",
        marker=dict(symbol="hexagon", size=10, color=colors, line=dict(width=0)),
        text=texts, hoverinfo="text", name="Terreno",
    )]

    if snap is not None:
        # Hexes liminales
        for lh in (getattr(snap, "liminal_hexes", None) or []):
            q, r = lh["coord"]
            x, y = _hex_xy(q, r)
            sym  = ", ".join(lh.get("symbol_pool", []))
            traces.append(go.Scatter(
                x=[x], y=[y], mode="markers",
                marker=dict(symbol="hexagon-open", size=18, color="#9b59b6", line=dict(width=2)),
                text=[f"Liminal ({q},{r})<br>{sym}"], hoverinfo="text", name="Liminal",
                showlegend=len(traces) == 1,
            ))

        # Tumbas
        gx, gy = [], []
        for g in (getattr(snap, "graves_activos", None) or []):
            coord_g = g[0] if isinstance(g, (list, tuple)) else None
            if coord_g:
                x, y = _hex_xy(*coord_g); gx.append(x); gy.append(y)
        if gx:
            traces.append(go.Scatter(x=gx, y=gy, mode="markers",
                marker=dict(symbol="star", size=12, color="#bdc3c7"),
                name="Tumbas", hoverinfo="skip"))

        # Fauna simbólica
        fx, fy, ft = [], [], []
        for f in (getattr(snap, "fauna_simbolica", None) or []):
            coord_f = f.get("coord")
            if coord_f:
                x, y = _hex_xy(*coord_f); fx.append(x); fy.append(y)
                ft.append(f.get("nombre", "bestia"))
        if fx:
            traces.append(go.Scatter(x=fx, y=fy, mode="markers",
                marker=dict(symbol="triangle-up", size=14, color="#f39c12"),
                text=ft, hoverinfo="text", name="Fauna"))

        # Fuego
        if getattr(snap, "fuego_activo", False) and getattr(snap, "fuego_coord", None):
            x, y = _hex_xy(*snap.fuego_coord)
            traces.append(go.Scatter(x=[x], y=[y], mode="markers",
                marker=dict(symbol="circle", size=22, color="#e74c3c", opacity=0.9),
                name="Fuego", hoverinfo="skip"))

    fig = go.Figure(data=traces)
    fig.update_layout(
        paper_bgcolor="#1a0a2e", plot_bgcolor="#1a0a2e",
        showlegend=True,
        legend=dict(font=dict(color="#ccc"), bgcolor="rgba(0,0,0,0.4)"),
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False,
                   scaleanchor="y", scaleratio=1),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
    )
    return fig


def _build_trend_figure(rows: list[dict], fields: list[str], title: str):
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
        vals = [r.get(f, 0) for r in rows]
        traces.append(go.Scatter(x=dias, y=vals, mode="lines", name=f,
                                 line=dict(color=COLORS[i % len(COLORS)], width=2)))
    fig = go.Figure(data=traces)
    fig.update_layout(
        title=dict(text=title, font=dict(color="#ccc", size=13)),
        paper_bgcolor="#111827", plot_bgcolor="#111827",
        showlegend=True, legend=dict(font=dict(color="#aaa")),
        margin=dict(l=40, r=10, t=40, b=30),
        xaxis=dict(color="#aaa", gridcolor="#1f2937"),
        yaxis=dict(color="#aaa", gridcolor="#1f2937", range=[0, 1.05]),
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
    names  = [k.capitalize() for k, _ in items]
    values = [v for _, v in items]
    colors = [_ARCH_COLORS.get(k, "#888") for k, _ in items]
    fig = go.Figure(go.Bar(x=values, y=names, orientation="h",
                           marker=dict(color=colors),
                           text=[f"{v:.2f}" for v in values], textposition="outside"))
    fig.update_layout(
        paper_bgcolor="#111827", plot_bgcolor="#111827",
        margin=dict(l=80, r=40, t=10, b=20),
        xaxis=dict(range=[0, 1.1], color="#aaa", gridcolor="#1f2937"),
        yaxis=dict(color="#aaa"),
        showlegend=False,
    )
    return fig


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

            # Semillas para nueva simulación
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

    # Lanzar servidor liminal si se pidió
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

    # Simulación en hilo background
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
        load_climate_metrics, load_deaths_log,
    )

    runner   = app_state.get_runner()
    if runner is None:
        ui.label("Sin simulación activa.").classes("p-8 text-yellow-400")
        ui.button("Volver", on_click=lambda: ui.navigate.to("/")).classes("m-4")
        return

    # Extraer terreno estático (una sola vez por conexión)
    terrain_biomes = _extract_terrain(runner)

    # ── Header ────────────────────────────────────────────────────────────────
    with ui.header().classes("bg-purple-950 text-white px-6 py-2 flex items-center gap-6"):
        ui.label("PSYCHE SIMULACRA").classes("text-lg font-bold tracking-widest")
        refs_header: dict = {}
        with ui.row().classes("gap-6 ml-4"):
            refs_header["dia"]    = ui.label("Día —").classes("text-purple-200 text-sm")
            refs_header["vivos"]  = ui.label("Agentes —").classes("text-green-300 text-sm")
            refs_header["estado"] = ui.badge("—", color="grey").classes("text-xs")

    # ── Tabs ──────────────────────────────────────────────────────────────────
    with ui.tabs().classes("bg-purple-900 text-white w-full") as tabs:
        t_resumen   = ui.tab("Resumen")
        t_tendencias = ui.tab("Tendencias")
        t_icl       = ui.tab("ICL")
        t_agentes   = ui.tab("Agentes")
        t_mapa      = ui.tab("Mapa")
        if app_state.use_liminal:
            t_liminal = ui.tab("Zona Liminal")

    refs: dict = {}

    with ui.tab_panels(tabs, value=t_resumen).classes("w-full bg-gray-900"):

        # ── Tab Resumen ───────────────────────────────────────────────────────
        with ui.tab_panel(t_resumen):
            with ui.grid(columns=4).classes("w-full gap-4 p-4"):
                refs["temp"]   = _mini_stat("Temperatura", "—")
                refs["estac"]  = _mini_stat("Estación", "—")
                refs["cc"]     = _mini_stat("Carrying capacity", "—")
                refs["presion"]= _mini_stat("Presión recursos", "—")
            with ui.grid(columns=3).classes("w-full gap-4 px-4 pb-4"):
                refs["humor"]    = _mini_stat("Humor promedio", "—")
                refs["energia"]  = _mini_stat("Energía promedio", "—")
                refs["ansiedad"] = _mini_stat("Ansiedad promedio", "—")

            ui.separator().classes("mx-4")
            ui.label("Clima activo").classes("text-xs text-gray-400 uppercase px-4 pt-3")
            refs["evento_clima"] = ui.label("—").classes("px-4 pb-2 text-yellow-300 text-sm")
            refs["fuego"]        = ui.label("").classes("px-4 text-red-400 text-sm")

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
            refs["plot_emoc"] = ui.plotly({}).classes("w-full h-64 px-2")
            ui.label("Registro climático").classes(
                "text-xs text-gray-400 uppercase px-4 pt-2"
            )
            refs["plot_clima"] = ui.plotly({}).classes("w-full h-56 px-2")

        # ── Tab ICL ───────────────────────────────────────────────────────────
        with ui.tab_panel(t_icl):
            ui.label("Inconsciente Colectivo").classes(
                "text-sm font-semibold px-4 pt-4 text-purple-300"
            )
            refs["plot_symbols"] = ui.plotly({}).classes("w-full h-64 px-2")

            ui.separator().classes("mx-4 my-2")
            ui.label("Mitología emergente").classes(
                "text-xs text-gray-400 uppercase px-4"
            )
            refs["myths_html"] = ui.html("").classes("px-4 pb-4 text-sm text-gray-300")

            ui.separator().classes("mx-4 my-2")
            ui.label("Léxico tribal").classes("text-xs text-gray-400 uppercase px-4")
            refs["lexicon_html"] = ui.html("").classes("px-4 pb-4 text-xs font-mono text-purple-200")

        # ── Tab Agentes ───────────────────────────────────────────────────────
        with ui.tab_panel(t_agentes):
            ui.label("Inspector de agentes").classes(
                "text-sm font-semibold px-4 pt-4 text-purple-300"
            )
            refs["agents_table"] = ui.table(
                columns=[
                    {"name": "nombre",   "label": "Nombre",    "field": "nombre",   "align": "left"},
                    {"name": "edad",     "label": "Edad",      "field": "edad",     "align": "right"},
                    {"name": "tribu",    "label": "Tribu",     "field": "tribu",    "align": "left"},
                    {"name": "arquetipo","label": "Arquetipo", "field": "arquetipo","align": "left"},
                    {"name": "humor",    "label": "Humor",     "field": "humor",    "align": "right"},
                    {"name": "ansiedad", "label": "Ansiedad",  "field": "ansiedad", "align": "right"},
                    {"name": "estado",   "label": "Estado",    "field": "estado",   "align": "left"},
                ],
                rows=[],
                row_key="nombre",
                pagination=20,
            ).classes("w-full px-4")

        # ── Tab Mapa ──────────────────────────────────────────────────────────
        with ui.tab_panel(t_mapa):
            ui.label(
                "Mapa del mundo — observacional. "
                "Solo hexes explorados por los agentes."
            ).classes("text-xs text-gray-400 px-4 py-2")
            snap0 = app_state.get_snapshot()
            fig0  = _build_hex_map(snap0, terrain_biomes)
            if fig0:
                refs["hex_plot"] = ui.plotly(fig0).classes("w-full").style("height:80vh")
            else:
                refs["hex_plot"] = None
                refs["hex_placeholder"] = ui.label(
                    "Esperando exploración del mundo..."
                ).classes("p-8 text-gray-400")

        # ── Tab Liminal ───────────────────────────────────────────────────────
        if app_state.use_liminal:
            with ui.tab_panel(t_liminal):
                ui.label("Zona Liminal").classes(
                    "text-sm font-semibold px-4 pt-4 text-purple-300"
                )
                ui.label(
                    "Hexes liminales del mundo principal. "
                    "El servidor Zona Liminal gestiona el espacio compartido cross-sim."
                ).classes("text-xs text-purple-400 px-4 pb-2")
                refs["lim_hexes"] = ui.html("").classes("px-4 pb-2 text-xs font-mono text-purple-200")
                ui.separator().classes("mx-4 my-2")
                ui.label("Campo del Multiverso (R5-E2)").classes(
                    "text-xs text-gray-400 uppercase px-4"
                )
                refs["multiverse"] = ui.label("Sin datos de convergencia.").classes(
                    "px-4 py-2 text-purple-100 text-sm"
                )

    # ── Timer de actualización ────────────────────────────────────────────────
    _prev_deaths: list[int] = [0]
    _map_tick:    list[int] = [0]

    _SIM_COLORS = {"running": "green", "stopped": "red", "paused": "orange", "error": "red"}

    def _refresh() -> None:
        try:
            # ── Snapshot directo ──────────────────────────────────────────────
            snap    = app_state.get_snapshot()
            runtime = app_state.get_runtime()
            state   = runtime.get_state() if runtime else None

            # Header
            refs_header["dia"].set_text(f"Día {app_state.dia_simulado}")
            refs_header["vivos"].set_text(f"{app_state.agentes_vivos} vivos")
            if state:
                sim_s = state.simulation
                refs_header["estado"].set_text(sim_s)
                refs_header["estado"].props(f'color="{_SIM_COLORS.get(sim_s,"grey")}"')

            if snap is not None:
                # ── Resumen ───────────────────────────────────────────────────
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

                # ── Liminal ───────────────────────────────────────────────────
                if app_state.use_liminal and "lim_hexes" in refs:
                    lh_lines = []
                    for lh in (snap.liminal_hexes or []):
                        portal = "PORTAL " if lh.get("es_portal") else ""
                        sym    = ", ".join(lh.get("symbol_pool", []))
                        lh_lines.append(
                            f"<span style='color:#bb88ff'>{portal}({lh['coord'][0]},{lh['coord'][1]})"
                            f" misterio={lh.get('misterio',0):.2f}</span> — {sym}"
                        )
                    refs["lim_hexes"].set_content("<br>".join(lh_lines) or "Sin hexes liminales.")

            # ── Checkpoint (cada ciclo) ────────────────────────────────────────
            cp = load_checkpoint()
            if cp:
                agents_list = cp.get("agentes", {}).get("agents", [])
                alive = [a for a in agents_list if a.get("is_alive", False)]
                if alive:
                    avg_h = sum(a.get("humor", 0.5) for a in alive) / len(alive)
                    avg_e = sum(a.get("energia", 0.5) for a in alive) / len(alive)
                    avg_a = sum(a.get("ansiedad", 0.5) for a in alive) / len(alive)
                    refs["humor"].set_text(f"{avg_h:.2f}")
                    refs["energia"].set_text(f"{avg_e:.2f}")
                    refs["ansiedad"].set_text(f"{avg_a:.2f}")

                # Agentes
                tribe_mgr = getattr(runner, "agents", None)
                tribe_mgr = getattr(tribe_mgr, "tribe_manager", None)
                rows = []
                for a in alive:
                    tid = None
                    if tribe_mgr:
                        tid = tribe_mgr.get_tribe_id(a.get("id", ""))
                    arch  = a.get("archetypes", {})
                    dom   = max(arch, key=lambda k: arch[k]) if arch else "—"
                    rows.append({
                        "nombre":    a.get("nombre", "?"),
                        "edad":      a.get("edad", 0),
                        "tribu":     tid or "—",
                        "arquetipo": dom,
                        "humor":     f"{a.get('humor', 0):.2f}",
                        "ansiedad":  f"{a.get('ansiedad', 0):.2f}",
                        "estado":    "vivo" if a.get("is_alive") else "fallecido",
                    })
                refs["agents_table"].rows = rows
                refs["agents_table"].update()

                # ICL
                cf = cp.get("agentes", {}).get("collective_field", {})
                symbols = cf.get("symbols", {})
                fig_sym = _build_symbol_figure(symbols)
                if fig_sym:
                    refs["plot_symbols"].update_figure(fig_sym)

                # Mitos
                my_data = cp.get("agentes", {}).get("mythology_engine", {})
                active_myths = [m for m in my_data.get("active_myths", []) if m.get("active")]
                myth_html = _render_myths_html(active_myths, {a["id"]: a["nombre"] for a in agents_list})
                refs["myths_html"].set_content(myth_html)

                # Léxico tribal
                lex_data = cp.get("agentes", {}).get("emergent_lexicon", {})
                refs["lexicon_html"].set_content(_render_lexicon_html(lex_data))

                # R5-E2 multiverse echo
                if "multiverse" in refs and state:
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
                    refs["deaths_log"].push(
                        f"Día {d['dia']} — {d['nombre']} ({d['causa']})"
                    )

            # ── Tendencias (cada ciclo, datos de DB) ───────────────────────────
            agent_metrics  = load_agent_metrics()
            climate_metrics = load_climate_metrics()
            fig_emoc  = _build_trend_figure(
                agent_metrics, ["humor", "energia", "ansiedad"],
                "Humor / Energía / Ansiedad promedio"
            )
            if fig_emoc:
                refs["plot_emoc"].update_figure(fig_emoc)
            fig_clima = _build_trend_figure(
                climate_metrics, ["temperatura"],
                "Temperatura promedio (°C)"
            )
            if fig_clima:
                refs["plot_clima"].update_figure(fig_clima)

            # ── Mapa (cada 5 ciclos = cada 10s) ───────────────────────────────
            _map_tick[0] += 1
            if _map_tick[0] >= 5 and snap is not None:
                _map_tick[0] = 0
                new_fig = _build_hex_map(snap, terrain_biomes)
                if new_fig:
                    if refs.get("hex_plot"):
                        refs["hex_plot"].update_figure(new_fig)
                    else:
                        # Primera vez que hay datos
                        if "hex_placeholder" in refs:
                            refs["hex_placeholder"].delete()
                        refs["hex_plot"] = ui.plotly(new_fig).classes("w-full").style("height:80vh")

        except Exception:
            pass

    ui.timer(2.0, _refresh)


# ── Helpers de renderizado ────────────────────────────────────────────────────

def _mini_stat(title: str, value: str):
    from nicegui import ui
    with ui.card().classes("p-4 bg-gray-800 text-white rounded-xl"):
        ui.label(title).classes("text-xs text-gray-400 uppercase tracking-wider mb-1")
        val = ui.label(value).classes("text-xl font-bold text-purple-300")
    return val


def _render_myths_html(active_myths: list, agent_names: dict) -> str:
    if not active_myths:
        return "<span class='text-gray-400'>Sin mitos activos actualmente.</span>"
    parts = []
    for m in active_myths:
        hero    = agent_names.get(m.get("hero_id", ""), m.get("hero_id", "?"))
        monster = agent_names.get(m.get("monster_id", ""), m.get("monster_id", "?"))
        dia_c   = m.get("day_crystallized", "?")
        parts.append(
            f"<div style='border-left:3px solid #9b59b6;padding:8px 12px;margin-bottom:8px;"
            f"background:rgba(155,89,182,0.1);border-radius:4px'>"
            f"<b style='color:#E040FB'>Héroe vs Monstruo</b> — cristalizado día {dia_c}<br>"
            f"🌟 <b style='color:#00D2B4'>{hero}</b> &nbsp;vs&nbsp; "
            f"👹 <b style='color:#FF4B4B'>{monster}</b></div>"
        )
    return "".join(parts)


def _render_lexicon_html(lex_data: dict) -> str:
    if not lex_data:
        return "<span class='text-gray-500'>Sin léxico generado aún.</span>"
    lines = []
    for tribe_id, ld in lex_data.items():
        words = ld.get("words", {})
        if words:
            word_str = "  ".join(f"<b>{arch}</b>→{w}" for arch, w in words.items())
            lines.append(f"<span style='color:#9b59b6'>{tribe_id[:12]}</span>: {word_str}")
    return "<br>".join(lines) if lines else "<span class='text-gray-500'>Sin palabras nombradas aún.</span>"


# ── Lanzamiento ───────────────────────────────────────────────────────────────

def launch_ui(app_state,
              DB_PATH=None, CP_DIR=None, SEEDS_DIR=None,
              LIMINAL_SERVER=None) -> None:
    from nicegui import ui

    DB_PATH       = DB_PATH       or ROOT / "data" / "db" / "simulation.db"
    CP_DIR        = CP_DIR        or ROOT / "data" / "checkpoints"
    SEEDS_DIR     = SEEDS_DIR     or ROOT / "data" / "seeds"
    LIMINAL_SERVER= LIMINAL_SERVER or ROOT / "liminal_server" / "main.py"

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
