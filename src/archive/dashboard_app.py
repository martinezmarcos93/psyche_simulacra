from __future__ import annotations

import streamlit as st
import pandas as pd
import sqlite3
import json
import os
import time
from pathlib import Path

# Configuración inicial de Streamlit
st.set_page_config(
    page_title="PSYCHE SIMULACRA — Jungian ABM Dashboard",
    page_icon="⚛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Componentes locales
from components.network_graph import draw_quantum_network
from components.collective_field import render_collective_field_section
from components.agent_inspector import render_agent_inspector_section

# ── Estilos CSS Premium (Glassmorphism & Neon) ──────────────────────────────
st.markdown(
    """
    <style>
    /* Tema oscuro unificado */
    .stApp {
        background-color: #0E1117;
        color: #E2E8F0;
    }
    
    /* Contenedores Glassmorphism */
    div[data-testid="stMetricContainer"] {
        background-color: rgba(26, 29, 36, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 8px;
        padding: 15px 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        backdrop-filter: blur(10px);
    }
    
    div[data-testid="stMetricContainer"] label {
        color: #A0AEC0 !important;
        font-weight: 500 !important;
        font-size: 13px !important;
    }
    
    div[data-testid="stMetricContainer"] div[data-testid="stMetricValue"] {
        color: #FFF !important;
        font-family: 'Outfit', 'Inter', sans-serif !important;
        font-weight: bold !important;
    }
    
    /* Separadores decorativos */
    hr {
        border-color: rgba(255, 255, 255, 0.05) !important;
    }
    
    /* Tabs personalizados */
    button[data-baseweb="tab"] {
        font-size: 15px !important;
        font-weight: 600 !important;
        color: #A0AEC0 !important;
        border-bottom-width: 2px !important;
    }
    
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #E040FB !important;
        border-bottom-color: #E040FB !important;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #0B0D13 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    /* Scrollbars */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-track {
        background: #0E1117;
    }
    ::-webkit-scrollbar-thumb {
        background: #2D3139;
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #4A5568;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ── Funciones de carga de datos no bloqueantes ──────────────────────────────

def get_db_connection(db_path: str) -> sqlite3.Connection:
    """Crea una conexión de solo lectura a la base de datos para no bloquear la simulación."""
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn

@st.cache_data(ttl=2)
def load_historical_agent_metrics(db_path: str) -> pd.DataFrame:
    """Carga históricos diarios de humor, energía y ansiedad promedio de agentes."""
    try:
        with get_db_connection(db_path) as conn:
            query = """
            SELECT dia, 
                   AVG(humor) as "Humor Promedio", 
                   AVG(energia) as "Energía Promedio", 
                   AVG(ansiedad) as "Ansiedad Promedio",
                   SUM(is_alive) as "Agentes Vivos"
            FROM agent_snapshots
            GROUP BY dia
            ORDER BY dia;
            """
            return pd.read_sql_query(query, conn)
    except Exception as e:
        # Retornar DataFrame vacío en caso de que la tabla no tenga datos todavía
        return pd.DataFrame(columns=["dia", "Humor Promedio", "Energía Promedio", "Ansiedad Promedio", "Agentes Vivos"])

@st.cache_data(ttl=2)
def load_climate_metrics(db_path: str) -> pd.DataFrame:
    """Carga históricos agregados de clima por día."""
    try:
        with get_db_connection(db_path) as conn:
            query = """
            SELECT dia, 
                   AVG(temperatura) as "Temperatura Promedio (°C)", 
                   AVG(survival_risk) as "Riesgo de Supervivencia Promedio",
                   AVG(precipitacion) as "Precipitación Promedio"
            FROM climate_log
            GROUP BY dia
            ORDER BY dia;
            """
            return pd.read_sql_query(query, conn)
    except Exception as e:
        return pd.DataFrame(columns=["dia", "Temperatura Promedio (°C)", "Riesgo de Supervivencia Promedio", "Precipitación Promedio"])

@st.cache_data(ttl=2)
def load_deaths_log(db_path: str) -> pd.DataFrame:
    """Carga el historial de decesos."""
    try:
        with get_db_connection(db_path) as conn:
            query = """
            SELECT dia as "Día", 
                   tick as "Tick", 
                   nombre as "Agente", 
                   causa as "Causa de Muerte"
            FROM deaths_log
            ORDER BY dia DESC, tick DESC;
            """
            return pd.read_sql_query(query, conn)
    except Exception as e:
        return pd.DataFrame(columns=["Día", "Tick", "Agente", "Causa de Muerte"])

def load_latest_checkpoint(checkpoints_dir: str) -> dict | None:
    """Carga de forma atómica y segura el último checkpoint guardado."""
    dir_path = Path(checkpoints_dir)
    if not dir_path.exists():
        return None
    candidates = sorted(dir_path.glob("checkpoint_*.json"), reverse=True)
    if not candidates:
        return None
    
    path = candidates[0]
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        # En caso de race condition, intentar cargar el segundo más nuevo
        if len(candidates) > 1:
            try:
                with open(candidates[1], encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return None

# ── Sidebar y configuración ──────────────────────────────────────────────────

st.sidebar.markdown(
    """
    <div style="text-align: center; margin-bottom: 20px;">
        <h2 style="margin: 0; color: #E040FB; font-size: 26px; font-weight: bold; text-shadow: 0 0 10px rgba(224, 64, 251, 0.4);">
            PSYCHE SIMULACRA
        </h2>
        <span style="color: #A0AEC0; font-size: 12px; font-family: monospace;">
            ⚛️ Jungian ABM Dashboard v1.0
        </span>
    </div>
    <hr style="margin-top: 0; margin-bottom: 20px;">
    """,
    unsafe_allow_html=True
)

st.sidebar.markdown("### ⚙️ Configuración de Datos")

checkpoints_dir = st.sidebar.text_input(
    "Directorio de Checkpoints",
    value="data/checkpoints"
)

db_path = st.sidebar.text_input(
    "Base de Datos SQLite",
    value="data/db/simulation.db"
)

st.sidebar.markdown("---")
st.sidebar.markdown("### ⏱️ Control de Refresco")

auto_refresh = st.sidebar.checkbox("Auto-refrescar en tiempo real", value=False)
refresh_interval = st.sidebar.slider("Intervalo de refresco (segundos)", min_value=2, max_value=30, value=5)

st.sidebar.markdown("---")

# Botón de refresco manual
if st.sidebar.button("🔄 Forzar Recarga de Datos", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

# ── Inicialización y verificación de datos ──────────────────────────────────

checkpoint = load_latest_checkpoint(checkpoints_dir)

if checkpoint is None:
    st.markdown(
        """
        <div style="background-color: rgba(255, 75, 75, 0.08); border-left: 4px solid #FF4B4B; padding: 25px; border-radius: 8px; margin: 40px auto; max-width: 800px;">
            <h3 style="margin: 0 0 10px 0; color: #FF4B4B;">⚠️ No se encontraron Checkpoints activos</h3>
            <p style="margin: 0; color: #E2E8F0; font-size: 15px;">
                El motor del simulador no ha generado ningún archivo de estado todavía en el directorio <code>data/checkpoints/</code>.<br>
                Por favor, asegúrate de correr al menos un día en el simulador mediante:
            </p>
            <pre style="margin-top: 12px; background-color: #11141A; padding: 10px; border-radius: 4px; border: 1px solid #2D3139; color: #FEB2B2;">python scripts/run_simulation.py --days 2</pre>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.stop()

# Desglosar datos del checkpoint
reloj = checkpoint.get("reloj", {})
dia_simulado = checkpoint.get("dia_simulado", 0)
hora_simulada = checkpoint.get("hora_simulada", 0)

agentes_core = checkpoint.get("agentes", {})
agents_list = agentes_core.get("agents", [])
social_network = agentes_core.get("social_network", {})
collective_field = agentes_core.get("collective_field", {})
mythology_engine = agentes_core.get("mythology_engine", {})

total_agents = len(agents_list)
alive_agents = sum(1 for a in agents_list if a.get("is_alive", True))
deceased_agents = total_agents - alive_agents
survival_ratio = (alive_agents / total_agents) if total_agents > 0 else 0.0

# ── Barra de Métricas Globales (Cabecera) ───────────────────────────────────

m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)

with m_col1:
    st.metric("Día / Hora de Simulación", f"Día {dia_simulado} — {hora_simulada:02d}:00 Ticks")

with m_col2:
    status_label = "Población Activa"
    st.metric(
        label=status_label,
        value=f"{alive_agents} / {total_agents} Vivos",
        delta=f"💀 {deceased_agents} Muertes" if deceased_agents > 0 else "Estable",
        delta_color="inverse"
    )

with m_col3:
    st.metric(
        label="Tasa de Supervivencia",
        value=f"{survival_ratio:.2%}",
        delta="Riesgo Extremo" if survival_ratio < 0.3 else "Sostenible"
    )

with m_col4:
    pressure = collective_field.get("emotional_pressure", 0.0)
    st.metric(
        label="Presión del Inconsciente",
        value=f"{pressure:.1%}",
        delta="Polarización" if pressure > 0.5 else "Integración"
    )

with m_col5:
    # Calcular humor promedio del checkpoint actual
    avg_humor = sum(a.get("humor", 0.5) for a in agents_list) / len(agents_list) if agents_list else 0.5
    st.metric(
        label="Humor Promedio Poblacional",
        value=f"{avg_humor:.2f}",
        delta="Estable"
    )

st.markdown("---")

# ── Maquetación en Pestañas (Tabs) ──────────────────────────────────────────

tab_overview, tab_social, tab_collective, tab_inspector = st.tabs([
    "📈 Vista General y Tendencias",
    "⚛️ Red Social Cuántica",
    "🌌 Inconsciente Colectivo",
    "🔍 Inspector de Agentes"
])

# ── Tab 1: Vista General y Tendencias ───────────────────────────────────────
with tab_overview:
    st.markdown("### 📊 Evolución Histórica e Indicadores de Salud")
    st.markdown(
        """
        Esta sección muestra la evolución acumulada de la simulación consultada de forma directa y paralela
        desde la base de datos SQLite sin interrumpir el motor.
        """
    )
    
    col_graphs, col_log = st.columns([7, 3])
    
    with col_graphs:
        # Cargar históricos de la BD
        df_agents = load_historical_agent_metrics(db_path)
        df_climate = load_climate_metrics(db_path)
        
        if not df_agents.empty:
            st.markdown("#### Tendencia del Estado Emocional Poblacional")
            # Configurar índice para el gráfico
            df_chart_agents = df_agents.set_index("dia")[["Humor Promedio", "Energía Promedio", "Ansiedad Promedio"]]
            st.line_chart(df_chart_agents, height=220)
        else:
            st.warning("Aún no se han guardado snapshots de agentes en la BD. Espera al final del primer día simulado.")

        if not df_climate.empty:
            st.markdown("#### Registro Climático y de Riesgo de Supervivencia")
            df_chart_climate = df_climate.set_index("dia")[["Temperatura Promedio (°C)", "Riesgo de Supervivencia Promedio"]]
            st.line_chart(df_chart_climate, height=180)
        else:
            st.warning("Aún no se han guardado registros climáticos en la BD.")

    with col_log:
        st.markdown("#### 💀 Registro Histórico de Decesos")
        df_deaths = load_deaths_log(db_path)
        
        if not df_deaths.empty:
            st.dataframe(
                df_deaths,
                hide_index=True,
                use_container_width=True,
                height=420
            )
        else:
            st.success("🟢 No se registran decesos en la historia de este mundo simulado.")

# ── Tab 2: Red Social Cuántica ──────────────────────────────────────────────
with tab_social:
    st.markdown("### ⚛️ Estructura de Vínculos y Entrelazamiento Emocional")
    st.markdown(
        """
        Visualización en tiempo real de los lazos interpersonales de la población. 
        El <strong>Entrelazamiento Cuántico</strong> ocurre cuando dos agentes experimentan una sincronía extrema
        de sus funciones de onda (colapsando en estados armónicos/hostiles), generando telepatía onírica.
        """, 
        unsafe_allow_html=True
    )
    
    graph_col, details_col = st.columns([5, 4])
    
    with graph_col:
        st.markdown("#### Mapa Relacional (Network Graph)")
        fig = draw_quantum_network(social_network, agents_list)
        st.pyplot(fig)
        
    with details_col:
        st.markdown("#### Listado Detallado de Vínculos Cuánticos")
        
        edges = social_network.get("edges", [])
        if not edges:
            st.info("No se registran interacciones o vínculos sociales en la población todavía.")
        else:
            # Encontrar nombres de agentes
            agent_names = {a["id"]: a["nombre"] for a in agents_list}
            
            # Formatear la tabla de aristas
            formatted_edges = []
            for e in edges:
                u_name = agent_names.get(e["u"], e["u"])
                v_name = agent_names.get(e["v"], e["v"])
                bond = e.get("bond_strength", 0.0)
                intimacy = e.get("intimacy", 0.0)
                res = e.get("resonance", 0.0)
                entangled = "⚛️ Entrelazado" if e.get("entangled", False) else "Estable"
                
                formatted_edges.append({
                    "Agente A": u_name,
                    "Agente B": v_name,
                    "Fuerza Lazo": f"{bond:.2f}",
                    "Intimidad": f"{intimacy:.2f}",
                    "Resonancia": f"{res:.2f}",
                    "Estado Cuántico": entangled
                })
            
            df_edges = pd.DataFrame(formatted_edges)
            st.dataframe(
                df_edges,
                hide_index=True,
                use_container_width=True,
                height=450
            )

# ── Tab 3: Inconsciente Colectivo ───────────────────────────────────────────
with tab_collective:
    render_collective_field_section(collective_field, mythology_engine, agents_list)

# ── Tab 4: Inspector de Agentes ─────────────────────────────────────────────
with tab_inspector:
    render_agent_inspector_section(agents_list)

# ── Orquestador de auto-refresco en segundo plano ───────────────────────────
if auto_refresh:
    time.sleep(refresh_interval)
    st.rerun()
