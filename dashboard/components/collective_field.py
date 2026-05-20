from __future__ import annotations

import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd

def draw_symbols_chart(symbols_data: dict) -> plt.Figure:
    """
    Genera un gráfico de barras horizontales estilizado para las cargas meméticas de los símbolos.
    """
    # Ordenar símbolos de mayor a menor carga
    sorted_symbols = sorted(symbols_data.items(), key=lambda x: x[1])
    names = [x[0].capitalize() for x in sorted_symbols]
    values = [x[1] for x in sorted_symbols]

    # Paleta de colores premium para los símbolos
    colors = []
    for name in names:
        n = name.lower()
        if n == "heroe":
            colors.append("#00D2B4")  # Cyan/Verde
        elif n == "sombra" or n == "muerte":
            colors.append("#FF4B4B")  # Rojo/Coral
        elif n == "fuego":
            colors.append("#FF9F43")  # Naranja
        elif n == "madre":
            colors.append("#E040FB")  # Púrpura/Magenta
        elif n == "comida":
            colors.append("#4CAF50")  # Verde bosque
        else:
            colors.append("#F4D03F")  # Amarillo/Trickster

    fig, ax = plt.subplots(figsize=(6, 3.5), facecolor="#0E1117")
    ax.set_facecolor("#0E1117")

    # Dibujar barras
    bars = ax.barh(names, values, color=colors, edgecolor="rgba(255,255,255,0.05)", height=0.6)

    # Añadir valores a las barras
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

    # Estilizar ejes
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#2D3139')
    ax.spines['bottom'].set_color('#2D3139')
    
    ax.tick_params(colors='#A0AEC0', labelsize=9)
    ax.set_xlim(0, 1.05)
    ax.grid(axis='x', linestyle='--', alpha=0.1, color='#E2E8F0')

    plt.tight_layout()
    return fig

def render_collective_field_section(collective_data: dict, mythology_data: dict, agents_data: list[dict]) -> None:
    """
    Renderiza la sección completa del inconsciente colectivo en Streamlit.
    """
    symbols = collective_data.get("symbols", {})
    pressure = collective_data.get("emotional_pressure", 0.0)
    active_myths = mythology_data.get("active_myths", [])

    st.markdown("### 🌌 El Inconsciente Colectivo")
    st.markdown(
        """
        El inconsciente colectivo es un campo simbólico que absorbe y metaboliza cada interacción social
        y evento significativo del mundo, alterando la probabilidad cuántica de colapso conductual.
        """
    )

    col1, col2 = st.columns([5, 4])

    with col1:
        st.markdown("#### Carga Memética de los Símbolos Arquetípicos")
        fig = draw_symbols_chart(symbols)
        st.pyplot(fig)

    with col2:
        st.markdown("#### Tensión Colectiva Global")
        # Mostrar presión con indicador de color dinámico
        color_class = "normal"
        if pressure > 0.7:
            color_class = "danger"
            status_text = "🔴 Presión Crítica — Campo altamente inestable, propenso a colapsos hostiles."
        elif pressure > 0.4:
            color_class = "warning"
            status_text = "🟡 Presión Elevada — Tensión latente en aumento en el grupo."
        else:
            status_text = "🟢 Campo Estable — Flujo psíquico armónico y cooperativo."

        st.metric(
            label="Presión Emocional Colectiva",
            value=f"{pressure:.2%}",
            delta="Inestabilidad de Campo" if pressure > 0.5 else "Estado Integrado"
        )
        st.markdown(f"**Estado:** {status_text}")
        
        # Mini indicador visual
        st.markdown(
            f"""
            <div style="background-color: rgba(255, 255, 255, 0.02); padding: 12px; border-left: 4px solid {'#FF4B4B' if pressure > 0.7 else '#FF9F43' if pressure > 0.4 else '#00D2B4'}; border-radius: 4px; margin-top: 10px;">
                <small style="color: #A0AEC0; font-family: monospace;">
                    Fórmula de Campo: Ψ(t) = ∑ S_i(t) * W_i
                    <br>
                    La presión colectiva incrementa con conflictos y decesos, y se atenúa mediante cooperación e integración mítica.
                </small>
            </div>
            """, 
            unsafe_allow_html=True
        )

    st.markdown("---")
    st.markdown("### 📜 Mitología Emergente & Cristalizaciones Míticas")

    # Filtrar mitos activos
    active = [m for m in active_myths if m.get("active", False)]

    if not active:
        st.info(
            "✨ **Sin mitos activos actualmente.**\n\n"
            "El inconsciente colectivo aún no ha cristalizado una narrativa arquetípica central. "
            "Para que cristalice el mito de **'Héroe vs Monstruo'**, los símbolos colectivos de **Héroe** y **Sombra** "
            "deben cruzar los umbrales de saturación (0.75 y 0.65 respectivamente) y la población debe contar con "
            "agentes cuyas psiques posean una fuerte polarización en dichos arquetipos dominantes (>0.80)."
        )
    else:
        for myth in active:
            if myth.get("name") == "heroe_vs_monstruo":
                hero_id = myth["hero_id"]
                monster_id = myth["monster_id"]
                dia_c = myth["day_crystallized"]

                # Encontrar nombres de héroe y monstruo
                agent_names = {a["id"]: a["nombre"] for a in agents_data}
                hero_name = agent_names.get(hero_id, hero_id)
                monster_name = agent_names.get(monster_id, monster_id)

                st.markdown(
                    f"""
                    <div style="background: linear-gradient(135deg, rgba(224, 64, 251, 0.1) 0%, rgba(0, 210, 180, 0.05) 100%); border: 1px solid rgba(224, 64, 251, 0.2); border-radius: 8px; padding: 20px;">
                        <h4 style="margin: 0 0 10px 0; color: #E040FB;">⚡ Mito Cristalizado: Héroe contra el Monstruo</h4>
                        <p style="margin: 0 0 15px 0; color: #E2E8F0; font-size: 14px;">
                            El inconsciente colectivo ha canalizado su tensión cristalizando una lucha polarizada. 
                            Este mito ha fijado un piso de carga para los símbolos de Héroe (50%) y Sombra (40%), 
                            generando retroalimentación persistente en las psiques de los involucrados.
                        </p>
                        <div style="display: flex; gap: 20px; flex-wrap: wrap;">
                            <div style="background: rgba(0, 210, 180, 0.1); border-left: 4px solid #00D2B4; padding: 10px 15px; border-radius: 4px; flex: 1; min-width: 200px;">
                                <strong style="color: #00D2B4;">🌟 El Héroe</strong><br>
                                <span style="font-size: 18px; font-weight: bold; color: #FFF;">{hero_name}</span><br>
                                <small style="color: #A0AEC0;">Efecto: Ansiedad reducida (-5%) y Humor aumentado (+5%) por día.</small>
                            </div>
                            <div style="background: rgba(255, 75, 75, 0.1); border-left: 4px solid #FF4B4B; padding: 10px 15px; border-radius: 4px; flex: 1; min-width: 200px;">
                                <strong style="color: #FF4B4B;">👹 El Chivo Expiatorio (Monstruo)</strong><br>
                                <span style="font-size: 18px; font-weight: bold; color: #FFF;">{monster_name}</span><br>
                                <small style="color: #A0AEC0;">Efecto: Ansiedad aumentada (+8%) y Humor deprimido (-5%) por día.</small>
                            </div>
                        </div>
                        <div style="margin-top: 15px; text-align: right;">
                            <small style="color: #888;">Cristalizado en el Día Simulado: {dia_c}</small>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
