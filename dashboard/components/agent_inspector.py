from __future__ import annotations

import streamlit as st
import matplotlib.pyplot as plt

def render_custom_progress(label: str, val: float, color: str) -> None:
    """Renderiza una barra de progreso HTML premium estilizada."""
    pct = val * 100
    st.markdown(
        f"""
        <div style="margin-bottom: 12px;">
            <div style="display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 4px;">
                <span style="color: #A0AEC0; font-weight: 500;">{label}</span>
                <span style="color: #E2E8F0; font-weight: bold; font-family: monospace;">{pct:.1f}%</span>
            </div>
            <div style="background-color: #1A1D24; border: 1px solid #2D3139; border-radius: 4px; height: 10px; overflow: hidden; width: 100%;">
                <div style="background-color: {color}; width: {min(pct, 100.0):.1f}%; height: 100%; border-radius: 3px;"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

def draw_archetypes_chart(archetypes_data: dict) -> plt.Figure:
    """Genera un gráfico de barras estilizado de los arquetipos psicológicos."""
    # Renombrar 'self_' o 'self' para mostrarlo elegante
    raw_sorted = sorted(archetypes_data.items(), key=lambda x: x[1])
    names = []
    for k, v in raw_sorted:
        name = "Self" if k in ("self", "self_") else k.capitalize()
        names.append(name)
    values = [x[1] for x in raw_sorted]

    fig, ax = plt.subplots(figsize=(6, 4.5), facecolor="#0E1117")
    ax.set_facecolor("#0E1117")

    # Colores degradados en azul-púrpura para arquetipos
    colors = plt.cm.Purples(np.linspace(0.4, 0.9, len(names)))

    bars = ax.barh(names, values, color="#9F7AEA", edgecolor="rgba(255,255,255,0.05)", height=0.6)
    
    # Colorear de manera especial el dominante (el valor más alto)
    if bars:
        bars[-1].set_color("#E040FB")  # El arquetipo dominante brilla en magenta

    for bar in bars:
        width = bar.get_width()
        ax.text(
            width + 0.02,
            bar.get_y() + bar.get_height()/2,
            f"{width:.2f}",
            color="#E2E8F0",
            ha="left",
            va="center",
            fontsize=8,
            fontweight="bold"
        )

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#2D3139')
    ax.spines['bottom'].set_color('#2D3139')
    
    ax.tick_params(colors='#A0AEC0', labelsize=9)
    ax.set_xlim(0, 1.05)
    ax.grid(axis='x', linestyle='--', alpha=0.1, color='#E2E8F0')

    plt.tight_layout()
    return fig

# Import numpy for colormap generation inside
import numpy as np

def render_agent_inspector_section(agents_data: list[dict]) -> None:
    """
    Sección completa del inspector de agentes en el dashboard.
    """
    if not agents_data:
        st.info("No hay agentes disponibles para inspeccionar.")
        return

    # Selector de agente en el subpanel
    agent_options = {a["id"]: f"{a['nombre']} ({a['rol'].capitalize()})" for a in agents_data}
    selected_agent_id = st.selectbox(
        "🔍 Selecciona un agente a inspeccionar:",
        options=list(agent_options.keys()),
        format_func=lambda x: agent_options[x]
    )

    # Buscar datos del agente seleccionado
    agent = next(a for a in agents_data if a["id"] == selected_agent_id)

    # 1. Cabecera del Agente
    is_alive = agent.get("is_alive", True)
    status_indicator = "🟢 Vivo" if is_alive else "💀 Fallecido"
    status_color = "#00D2B4" if is_alive else "#FF4B4B"

    # Encontrar causa de muerte si falleció
    cause_str = ""
    if not is_alive:
        # Intentar obtener la causa del episodic_log o decesos
        dead_logs = [log for log in agent.get("episodic_log", []) if "Falleció" in log or "muerto" in log.lower()]
        if dead_logs:
            cause_str = f" — {dead_logs[-1]}"
        else:
            cause_str = " — Causa desconocida"

    st.markdown(
        f"""
        <div style="background-color: #1A1D24; padding: 18px; border-radius: 8px; border: 1px solid #2D3139; margin-bottom: 20px;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                <div>
                    <h3 style="margin: 0; color: #FFF; font-size: 22px;">{agent['nombre']}</h3>
                    <p style="margin: 4px 0 0 0; color: #A0AEC0; font-size: 14px;">
                        Rol: <span style="color: #E2E8F0; font-weight: 500;">{agent['rol'].capitalize()}</span> | 
                        Género: <span style="color: #E2E8F0; font-weight: 500;">{agent['sexo']}</span> | 
                        Edad: <span style="color: #E2E8F0; font-weight: 500;">{agent['edad']} años</span> | 
                        Posición Hex: <span style="color: #E2E8F0; font-weight: 500;">{agent['posicion']}</span>
                    </p>
                </div>
                <div style="background-color: rgba({('0, 210, 180' if is_alive else '255, 75, 75')}, 0.1); border: 1px solid {status_color}; padding: 6px 14px; border-radius: 20px; font-weight: bold; color: {status_color}; margin-top: 10px;">
                    {status_indicator}{cause_str}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 2. Layout Principal: Biología y Emoción vs Psicología
    left_col, right_col = st.columns([1, 1])

    with left_col:
        st.markdown("#### 🔋 Estado Psicobiológico")
        
        # Tarjetas de estado emocional
        e_col1, e_col2, e_col3 = st.columns(3)
        with e_col1:
            st.metric("Humor", f"{agent.get('humor', 0.5):.2f}")
        with e_col2:
            st.metric("Energía", f"{agent.get('energia', 0.8):.2f}")
        with e_col3:
            st.metric("Ansiedad", f"{agent.get('ansiedad', 0.2):.2f}")

        st.markdown("<br>", unsafe_allow_html=True)
        
        # Necesidades Biológicas
        needs = agent.get("needs", {})
        hambre = needs.get("hambre", 0.0)
        sed = needs.get("sed", 0.0)
        fatiga = needs.get("fatiga", 0.0)
        soc = needs.get("sociabilidad", 0.5)

        # Coloreado adaptativo (rojo/amarillo si son críticas)
        render_custom_progress("Hambre (Nutrición)", hambre, "#FF4B4B" if hambre > 0.6 else "#FF9F43" if hambre > 0.4 else "#00D2B4")
        render_custom_progress("Sed (Hidratación)", sed, "#FF4B4B" if sed > 0.6 else "#2196F3" if sed > 0.4 else "#00D2B4")
        render_custom_progress("Fatiga (Agotamiento)", fatiga, "#FF4B4B" if fatiga > 0.7 else "#FFD700" if fatiga > 0.4 else "#00D2B4")
        render_custom_progress("Sociabilidad (Aislamiento)", 1.0 - soc, "#9F7AEA" if soc < 0.2 else "#00D2B4")

        # Comportamiento cuántico actual
        st.markdown("#### ⚛️ Estado Conductual Cuántico")
        conducta = agent.get("estado_conductual") or "Neutro"
        conducta_desc = {
            "cooperacion": "🤝 Cooperación — Buscando el beneficio mutuo y lazos estables.",
            "competencia": "⚔️ Competencia — Enfocado en la recolección individual y defensiva.",
            "aislamiento": "🛖 Aislamiento — Conservando energía y recursos de manera solitaria.",
            "manipulacion": "🎭 Manipulación — Explotación del entorno o engaño táctico.",
        }
        desc = conducta_desc.get(conducta, f"Indeterminado (Último colapso: {conducta})")
        st.markdown(
            f"""
            <div style="background-color: rgba(159, 122, 234, 0.08); border-left: 4px solid #9F7AEA; padding: 10px 15px; border-radius: 4px; margin-top: 10px;">
                <span style="color: #E2E8F0; font-weight: bold;">Colapso Cuántico:</span> 
                <span style="color: #D6BCFA;">{desc}</span>
            </div>
            """,
            unsafe_allow_html=True
        )

    with right_col:
        # Pestañas del perfil psicológico profundo
        tab_arch, tab_complex, tab_dreams = st.tabs(["📊 Arquetipos & Rasgos", "🔥 Complejos Activos", "🌙 Onirismo (Sueños)"])

        with tab_arch:
            st.markdown("##### Vector de Arquetipos Jungianos")
            archetypes = agent.get("archetypes", {})
            if archetypes:
                fig = draw_archetypes_chart(archetypes)
                st.pyplot(fig)
            else:
                st.info("Sin datos arquetípicos")

            st.markdown("##### Rasgos Estables de Personalidad (Big Five)")
            traits = agent.get("traits", {})
            if traits:
                # Mostrar en bonita cuadrícula
                t_cols = st.columns(2)
                t_items = list(traits.items())
                for idx, (trait_key, val) in enumerate(t_items):
                    col_target = t_cols[idx % 2]
                    col_target.markdown(f"**{trait_key.capitalize()}:** `{val:.2f}`")
            else:
                st.info("Sin rasgos de personalidad")

        with tab_complex:
            st.markdown("##### Perfil de Complejos Psíquicos")
            st.markdown("<small style='color: #888;'>Carga latente de complejos en la psique (umbral de activación: >0.65):</small>", unsafe_allow_html=True)
            complexes = agent.get("complexes", {})
            
            if complexes:
                activos = complexes.get("activos", {})
                
                # Excluir las claves internas de la lista visual
                comp_names = ["abandono", "inferioridad", "poder", "culpa", "materno", "trascendencia"]
                
                for cname in comp_names:
                    val = complexes.get(cname, 0.3)
                    is_active = cname in activos
                    
                    if is_active:
                        badge = f"<span style='background-color: #FF4B4B; color: #FFF; font-size: 10px; font-weight: bold; padding: 2px 6px; border-radius: 10px; margin-left: 10px;'>🔥 ACTIVO</span>"
                        label_style = f"color: #FF4B4B; font-weight: bold;"
                    else:
                        badge = ""
                        label_style = "color: #E2E8F0;"

                    st.markdown(
                        f"""
                        <div style="display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid #2D3139;">
                            <span style="{label_style}">{cname.capitalize()}{badge}</span>
                            <span style="font-family: monospace; font-weight: bold;">{val:.2f}</span>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
            else:
                st.info("Sin datos de complejos")

        with tab_dreams:
            st.markdown("##### Últimos Sueños del Agente")
            dreams = agent.get("dreams", [])
            
            if not dreams:
                st.info("El agente aún no ha tenido sueños registrados en esta sesión.")
            else:
                for d in reversed(dreams):
                    st.markdown(
                        f"""
                        <div style="background-color: rgba(26, 29, 36, 0.6); border: 1px solid #2D3139; padding: 12px; border-radius: 6px; margin-bottom: 10px;">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                                <strong style="color: #9F7AEA;">🌙 Símbolo: '{d['simbolo']}'</strong>
                                <small style="color: #888;">Día {d['dia']}</small>
                            </div>
                            <div style="font-size: 13px; color: #E2E8F0; margin-bottom: 6px;">
                                <strong>Insight:</strong> {d['insight']}
                            </div>
                            <div style="display: flex; justify-content: space-between; font-size: 11px; color: #A0AEC0;">
                                <span>Arquetipo: <code style="color:#D6BCFA;">{d['arquetipo']}</code></span>
                                <span>Complejo implicado: <code style="color:#FEB2B2;">{d['complejo'] or 'Ninguno'}</code></span>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

    # 3. Crónicas del Agente: Memoria Episódica
    st.markdown("---")
    st.markdown("### 📖 Crónica Narrativa y Memoria Episódica")
    st.markdown("<small style='color: #888;'>Registro temporal de vivencias, sueños e interacciones sociales experimentadas por el agente:</small>", unsafe_allow_html=True)
    
    episodic_log = agent.get("episodic_log", [])
    if not episodic_log:
        st.info("La memoria episódica de este agente está vacía. Espera a que transcurran días en la simulación.")
    else:
        # Timeline premium
        timeline_html = "<div style='background-color: #11141A; border: 1px solid #2D3139; padding: 15px; border-radius: 8px; max-height: 250px; overflow-y: auto; font-family: sans-serif;'>"
        for entry in reversed(episodic_log):
            # Parsear día si viene en formato "Día X: ..."
            parts = entry.split(":", 1)
            if len(parts) == 2 and "Día" in parts[0]:
                day_badge = f"<span style='background-color: #4A5568; color: #FFF; font-size: 10px; font-weight: bold; padding: 2px 6px; border-radius: 4px; margin-right: 8px;'>{parts[0].strip()}</span>"
                text = parts[1].strip()
            else:
                day_badge = ""
                text = entry

            # Dar color al texto según tipo de evento
            text_color = "#E2E8F0"
            if "Falleció" in text or "muerto" in text.lower():
                text_color = "#FF4B4B"
            elif "Soñó" in text:
                text_color = "#B7791F"  # Dorado onírico
            elif "explotado" in text or "engaño" in text or "aprovechó" in text:
                text_color = "#E53E3E"
            elif "Cooperó" in text or "cooperó" in text.lower():
                text_color = "#319795"  # Teal

            timeline_html += f"""
            <div style="border-left: 2px solid #4A5568; padding-left: 15px; margin-bottom: 12px; position: relative;">
                <div style="position: absolute; left: -6px; top: 4px; width: 10px; height: 10px; border-radius: 50%; background-color: #A0AEC0; border: 2px solid #11141A;"></div>
                <div style="display: flex; align-items: center; margin-bottom: 2px;">
                    {day_badge}
                </div>
                <div style="color: {text_color}; font-size: 13.5px;">{text}</div>
            </div>
            """
        timeline_html += "</div>"
        st.markdown(timeline_html, unsafe_allow_html=True)
