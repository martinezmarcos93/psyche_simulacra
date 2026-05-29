from __future__ import annotations

import networkx as nx
import matplotlib.pyplot as plt
import numpy as np

def draw_quantum_network(social_network_data: dict, agents_data: list[dict]) -> plt.Figure:
    """
    Genera una visualización premium de la red social cuántica.
    - Nodos coloreados según humor (de rojo a verde) o gris si están fallecidos.
    - Vínculos coloreados según bond_strength (azul/verde para positivo, rojo para negativo).
    - Entrelazamientos cuánticos resaltados en púrpura brillante/glowing.
    """
    # 1. Crear el grafo dirigido
    G = nx.DiGraph()

    # Mapear agentes para búsquedas rápidas
    agent_map = {a["id"]: a for a in agents_data}

    # Añadir nodos
    for node_id in social_network_data.get("nodes", []):
        agent_info = agent_map.get(node_id, {})
        nombre = agent_info.get("nombre", node_id)
        is_alive = agent_info.get("is_alive", True)
        humor = agent_info.get("humor", 0.5)
        rol = agent_info.get("rol", "generico")
        
        G.add_node(
            node_id,
            nombre=nombre,
            is_alive=is_alive,
            humor=humor,
            rol=rol
        )

    # Añadir aristas
    for edge in social_network_data.get("edges", []):
        u = edge["u"]
        v = edge["v"]
        bond_strength = edge.get("bond_strength", 0.0)
        entangled = edge.get("entangled", False)
        
        G.add_edge(
            u, v,
            bond_strength=bond_strength,
            entangled=entangled
        )

    # 2. Configurar la figura Matplotlib con estética Dark
    fig, ax = plt.subplots(figsize=(9, 6), facecolor="#0E1117")
    ax.set_facecolor("#0E1117")

    if not G.nodes:
        # Grafo vacío
        ax.text(0.5, 0.5, "Sin agentes en la red social", color="#888888",
                ha="center", va="center", fontsize=14)
        ax.axis("off")
        return fig

    # 3. Disposición de nodos (layout)
    # k regula la distancia entre nodos, seed para reproducibilidad
    pos = nx.spring_layout(G, k=1.2, seed=42)

    # Separar nodos vivos y muertos
    nodes_alive = [n for n, attr in G.nodes(data=True) if attr.get("is_alive", True)]
    nodes_dead = [n for n, attr in G.nodes(data=True) if not attr.get("is_alive", True)]

    # Colores de nodos vivos basados en Humor (escala Red-Yellow-Green/Blue)
    alive_humors = [G.nodes[n].get("humor", 0.5) for n in nodes_alive]
    
    # Crear colormap personalizado: Rojo (triste/bajo) -> Amarillo -> Verde/Cyan (feliz/alto)
    node_cmap = plt.cm.RdYlGn  # Red-Yellow-Green

    # 4. Dibujar nodos
    if nodes_alive:
        alive_draw = nx.draw_networkx_nodes(
            G, pos,
            nodelist=nodes_alive,
            node_color=alive_humors,
            cmap=node_cmap,
            vmin=0.0, vmax=1.0,
            node_size=600,
            edgecolors=(1.0, 1.0, 1.0, 0.25),
            linewidths=1.5,
            ax=ax
        )
    
    if nodes_dead:
        nx.draw_networkx_nodes(
            G, pos,
            nodelist=nodes_dead,
            node_color="#2D3139",
            node_size=450,
            edgecolors="#4E525A",
            linewidths=1.0,
            alpha=0.6,
            node_shape="X",  # Forma de X para indicar fallecido
            ax=ax
        )

    # 5. Dibujar aristas con estilo premium
    edges_normal_pos = []
    edges_normal_neg = []
    edges_entangled = []

    for u, v, data in G.edges(data=True):
        bond = data.get("bond_strength", 0.0)
        entangled = data.get("entangled", False)
        
        if entangled:
            edges_entangled.append((u, v))
        elif bond >= 0:
            edges_normal_pos.append((u, v))
        else:
            edges_normal_neg.append((u, v))

    # Dibujar aristas normales positivas (verde translúcido)
    if edges_normal_pos:
        nx.draw_networkx_edges(
            G, pos,
            edgelist=edges_normal_pos,
            edge_color="#00D2B4",
            width=1.5,
            alpha=0.6,
            arrowsize=12,
            arrowstyle="-|>",
            connectionstyle="arc3,rad=0.15",
            ax=ax
        )

    # Dibujar aristas normales negativas (rojo translúcido)
    if edges_normal_neg:
        nx.draw_networkx_edges(
            G, pos,
            edgelist=edges_normal_neg,
            edge_color="#FF4B4B",
            width=1.5,
            alpha=0.6,
            arrowsize=12,
            arrowstyle="-|>",
            connectionstyle="arc3,rad=0.15",
            ax=ax
        )

    # Dibujar aristas entrelazadas (Púrpura brillante, más gruesas)
    if edges_entangled:
        # Dibujar una sombra brillante translúcida detrás
        nx.draw_networkx_edges(
            G, pos,
            edgelist=edges_entangled,
            edge_color="#E040FB",
            width=4.0,
            alpha=0.3,
            arrowsize=0,
            connectionstyle="arc3,rad=0.15",
            ax=ax
        )
        # El núcleo del lazo cuántico
        nx.draw_networkx_edges(
            G, pos,
            edgelist=edges_entangled,
            edge_color="#F48FB1",
            width=2.2,
            alpha=0.9,
            arrowsize=14,
            arrowstyle="-|>",
            connectionstyle="arc3,rad=0.15",
            ax=ax
        )

    # 6. Dibujar etiquetas de nodos (nombres)
    labels = {n: attr.get("nombre", n) for n, attr in G.nodes(data=True)}
    # Desplazar etiquetas un poco hacia arriba para no solapar
    pos_labels = {node: (coords[0], coords[1] + 0.08) for node, coords in pos.items()}
    nx.draw_networkx_labels(
        G, pos_labels,
        labels=labels,
        font_color="#E2E8F0",
        font_size=9,
        font_weight="bold",
        ax=ax
    )

    # 7. Finalizar estilo y añadir leyenda discreta
    ax.axis("off")
    
    # Crear elementos de leyenda personalizados
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], color='#00D2B4', lw=2, label='Vínculo Positivo'),
        Line2D([0], [0], color='#FF4B4B', lw=2, label='Vínculo Negativo'),
        Line2D([0], [0], color='#E040FB', lw=3, label='Entrelazamiento Cuántico ⚛️'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#2D3139', markersize=8, markeredgecolor='#4E525A', label='Fallecido 💀'),
    ]
    ax.legend(handles=legend_elements, loc='upper right', facecolor='#1A1D24', edgecolor='#2D3139', labelcolor='#E2E8F0', fontsize=9)

    plt.tight_layout()
    return fig
