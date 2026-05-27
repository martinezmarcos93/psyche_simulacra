# Roadmap 5.2 — Observatorio NiceGUI: refinamiento y fidelidad visual

**Contexto:** Roadmap 5 (simulación) completado en branch `evolution`.
La UI NiceGUI está funcional con 9 tabs. Este roadmap cubre la deuda técnica
de fidelidad visual y las secciones que necesitan refinamiento antes del merge a `main`.

---

## Bloque A — Fidelidad visual: Tendencias

**Estado actual:** 4 gráficos básicos (Plotly line charts) que muestran datos reales desde la DB.

**Objetivo:** Paridad con el dashboard Streamlit original (`dashboard/app.py`).

### A1 — Mejorar Tendencias: eje Y dinámico y eventos superpuestos
- Detectar y marcar en el gráfico los días con eventos climáticos extremos (líneas verticales)
- Superposición de `hysteria_active` como banda roja de fondo
- Eje X compartido entre los 4 sub-gráficos (sincronizar zoom horizontal)
- Tooltips con día simulado + valores exactos + nombre del evento si aplica

### A2 — Agregar métricas de emergencia a Tendencias
- Leer `data/metrics/emergence_series.csv` y mostrar:
  - **KL Divergencia** (divergencia psicológica inter-tribal)
  - **VFE proxy** (entropía del campo colectivo = incertidumbre del inconsciente)
  - **IMI** (varianza arquetípica explicada por tribu)
  - **MIG** (información que la tribu aporta sobre el individuo)
- Referencia: `core/metrics/emergence.py` + `scripts/plot_emergence.py`

---

## Bloque B — Fidelidad visual: ICL (Inconsciente Colectivo)

**Estado actual:** Gráfico de barras de símbolos + mitos + léxico.

**Objetivo:** Paridad con `dashboard/components/collective_field.py`.

### B1 — Indicadores de estado del campo
- Gauge o semáforo de `emotional_pressure` (igual que en Streamlit: rojo > 0.7)
- Historial de presión emocional (sparkline) en la misma tarjeta
- Fórmula visible: Ψ(t) = ∑ S_i(t) × W_i

### B2 — Gráfico de símbolos con arquetipos descriptivos
- Tooltip con descripción del arquetipo al hover
- Ordenar por carga descendente
- Mostrar qué tribu tiene más carga en ese símbolo (sub-texto)

### B3 — Timeline de cristalización mítica
- Gráfico temporal: en qué días cristalizaron mitos y de qué tipo (Campbell)
- Marcar el momento en que un mito se convirtió en leyenda

---

## Bloque C — Fidelidad visual: Red Social Cuántica

**Estado actual:** Layout circular simple, filtro de aristas por bond_strength > 0.45.

**Objetivo:** Paridad con `dashboard/components/network_graph.py`.

### C1 — Layout spring (simulado)
- Implementar Fruchterman-Reingold en Python puro (sin NetworkX en el cliente)
  o pre-computar las posiciones en el backend y pasarlas al gráfico
- Agrupar visualmente por tribu (misma zona del canvas)
- Nodos muertos con marcador X (como en Streamlit)

### C2 — Tabla de aristas debajo del grafo
- Listado de las 20 aristas más fuertes con: nombre A, nombre B, bond_strength,
  intimidad, resonancia, estado cuántico (entrelazado sí/no)
- Filtro por tribu

### C3 — Panel de estadísticas de red
- Total de nodos / aristas activas
- Clusters detectados (componentes conectados)
- Agente con más conexiones (hub)
- Número de pares entrelazados

---

## Bloque D — Mapa hexagonal: paridad con Pygame

**Estado actual:** Scatter de círculos sobre hexes explorados (recursos_por_hex),
sin posiciones de agentes, sin zoom eficiente.

**Objetivo:** Reproducir la estética del visualizador Pygame (`scripts/visualizer.py`).

### D1 — Renderizar TODO el terreno (no solo explorado)
- Usar `plotly.scattergl` (WebGL) para manejar los 4800 hexes sin lag
- Hexes no explorados: color muy oscuro/transparente (nieble de guerra)
- Hexes explorados: color de bioma completo

### D2 — Agentes como capa separada
- Posición de cada agente vivo como punto coloreado por arquetipo dominante
- Tooltip: nombre, edad, humor, tribu, estado conductual
- Agentes muertos: pequeña X gris en su última posición conocida
- Actualización cada 5s (no 20s)

### D3 — Capas de información
- Toggle (checkbox) para activar/desactivar capas:
  - Terreno base
  - Agentes
  - Tumbas
  - Estructuras (altares, tótems, refugios)
  - Fauna simbólica
  - Hexes liminales
  - Fuego
- Zoom y pan nativos de Plotly (ya funcionan, solo documentar)

### D4 — Forma hexagonal real
- Investigar uso de `go.Scatter` con símbolo `hexagon` en modo WebGL
  o construir hexágonos como shapes SVG via `fig.add_shape()`
- Alternativa: librería `plotly-hexbin` o renderizado custom via `go.Scattergl`

---

## Bloque E — Refinamiento: Sueños

**Estado actual:** Lista de sueños individuales + resumen por tribu (carga desde checkpoint).

### E1 — Visualización de frecuencia simbólica
- Gráfico de barras: frecuencia de cada símbolo onírico por tribu
- Comparar contra los símbolos del campo colectivo (¿sueñan lo que el ICL presiona?)

### E2 — Sueños compartidos (entrelazamiento)
- Destacar sueños con `shared_with` no vacío
- Mostrar el par entrelazado y si ambos aún están vivos

### E3 — Timeline de sueños por agente
- Al hacer click en un agente en el tab Agentes, mostrar su historial completo de sueños
- (Requiere interactividad NiceGUI: `on_click` en la tabla de agentes)

---

## Bloque F — Refinamiento: Civilización

**Estado actual:** HTML estático de estructuras y tecnologías desde checkpoint.

### F1 — Mapa de estructuras (overlay sobre Mapa)
- Integrar estructuras como capa en el Tab Mapa (ver D3)
- En Tab Civilización: tabla filtrable por tipo/tribu/estado

### F2 — Árbol de linaje del conocimiento
- Visualizar cómo un conocimiento se transmitió entre agentes (KnowledgeLineage)
- Mostrar degradación de fidelidad a lo largo del árbol
- Detectar y destacar "supersticiones" (fidelidad < 0.35)

### F3 — Materiales sagrados
- Mostrar `sacred_objects` del checkpoint (objetos rituales)
- Vincular con la tribu que los posee y el día de creación

---

## Bloque G — Refinamiento: Inspector de Agentes

### G1 — Detalle individual al hacer click
- Click en fila de la tabla → panel lateral con:
  - Radar chart del vector arquetípico (12 ejes)
  - Log episódico completo (scroll)
  - Últimos 5 sueños
  - Complejos activos
  - Vínculos sociales (top 5 por bond_strength)

### G2 — Filtros
- Filtrar por tribu, estado conductual, rango de edad, arquetipo dominante
- Ordenar por humor / ansiedad / edad

---

## Bloque H — Mejoras generales de la UI

### H1 — Performance general
- Verificar que `ui.plotly` no re-renderiza el gráfico completo cuando solo cambian
  unos pocos puntos (explorar `update_traces` / `restyle` en lugar de `update_figure`)
- Considerar `ui.refreshable` para secciones de texto HTML

### H2 — Notificaciones de eventos
- Cuando cristaliza un nuevo mito → `ui.notify` con nombre del mito y tribu
- Cuando muere un agente con arquetipo ≥ 0.70 → notificación elegía
- Cuando se activa histeria colectiva → banner rojo en el header

### H3 — Página de configuración
- Desde el launcher: poder editar `NARRATIVE_ENABLED`, `OLLAMA_MODEL`,
  número de días del checkpoint, días hasta clustering
- Sin necesidad de editar variables de entorno manualmente

---

## Orden de prioridad sugerido

```
D1 → D2 → D3    (mapa primero: es lo más visible)
C1 → C2 → C3    (red social: el feedback más claro del usuario)
A1 → A2         (tendencias: ya funciona pero le falta profundidad)
B1 → B2 → B3    (ICL: refinamiento conceptual)
E1 → E2         (sueños: depende de que el DreamEngine esté generando)
F1 → F3         (civilización: depende de datos en checkpoint)
G1 → G2         (agentes: nice-to-have)
H1 → H2 → H3    (mejoras transversales: al final)
```

---

*Rama de trabajo: `evolution`. Merge a `main` solo con autorización explícita.*
