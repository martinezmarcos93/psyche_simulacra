# Roadmap 6.0 — Estabilización, Mapa Real y Zona Liminal Integrada

**Rama de trabajo:** `evolution` — merge a `main` solo al completar bloque E.

**Criterio de orden:** menor → mayor complejidad técnica. Cada bloque es desplegable independientemente.

---

## Bloque A — Estabilización crítica ✦ baja complejidad ✅ COMPLETO

> Fixes urgentes, sin diseño nuevo.

### A1 ✅ — Commit de correcciones acumuladas (staging actual)
- `plotly` instalado y añadido a `requirements.txt` / `pyproject.toml`
- `_BIOME_COLORS` corregido con los nombres reales de `hexagon.py`
- `explored_coords` desde `terrain._explored_set` en lugar de `snap.recursos_por_hex`
- Control de velocidad (`MAX / ×20 / ×5 / ×1 / Paso`) en el header del monitor
- Botón Pausar / Reanudar con `threading.Event` en el sim thread
- Fix radar G1: `e.args.get("rows")` en lugar de `e.selection`

### A2 ✅ — Primer carga inmediata de gráficos
- Los gráficos de tendencias y emergencia esperan 3 ciclos (6s) antes de cargar.
- Disparar la primera carga en el tick inicial (`_charts_tick[0] = 99` al inicio).
- Mismo patrón para el mapa (`_map_tick`) y el slow tick (`_slow_tick`).

### A3 ✅ — Error logging visible
- El `except Exception: pass` en `_refresh()` traga errores en silencio.
- Reemplazar por `except Exception as e: print(f"[UI] {e}", file=sys.stderr)`.
- Permite diagnosticar problemas sin romper la UI.

### A4 ✅ — Dependencias en pyproject.toml
- `plotly>=5.0`, `nicegui>=2.0`, `websockets>=12.0`, `aiohttp>=3.9` añadidos.
- Extras `dashboard` (matplotlib, pandas), `liminal` y `dev` documentados.
- Paquetes `ui*` y `liminal_server*` incluidos en setuptools packages.find.
- `requirements.txt` y `pyproject.toml` sincronizados.

---

## Bloque B — Mapa del mundo: capas faltantes ✦ baja-media complejidad

> El mapa ahora muestra biomas con colores reales. Este bloque añade las capas que faltan.

### B1 — Estructuras como capa del mapa
- Leer `snap` o checkpoint para obtener `persistent_structures`.
- Añadir traza Scattergl: altares (▲ dorado), tótems (◆ violeta), murallas (■ gris), hogueras (● rojo).
- Toggle "Estructuras" en el panel de capas (D3 del R5.2 ya tiene la infraestructura).

### B2 — Portal liminal visible en el mapa del mundo
- Si el servidor liminal está activo, resaltar el hex portal como un marcador pulsante (círculo violeta grande).
- Tooltip: "Portal Liminal · conectado / desconectado".

### B3 — Hexes liminales con símbolo especial
- Los hexes liminales ya se cargan del snapshot. Cambiar el símbolo de `circle-open` a algo más visible (estrella o rombo).
- Añadir etiqueta con el nivel de misterio directamente en el mapa (texto pequeño).

---

## Bloque C — Zona Liminal: integración NiceGUI ✦ media complejidad

> Reemplazar la ventana Pygame externa por una visualización embedded. La mayor parte del código del servidor no cambia — solo la capa de visualización.

### C1 ⚠️ PENDIENTE — Eliminar Pygame del servidor liminal
- `liminal_server/visualizer/liminal_pygame.py` sigue activo en el árbol (no archivado).
- Mover a `src/archive/` y dejar el servidor como **WebSocket puro**.
- Hasta que no se archive, el proceso del servidor puede abrir ventana Pygame.

### C2 ✅ — Tab Zona Liminal: mapa Plotly del mundo liminal
- El servidor liminal expone un endpoint HTTP `/state` (JSON) con el estado actual.
  - Hexes del mundo liminal 30×20 con sus biomas/portales.
  - Lista de agentes presentes (id, posición, sim_id de origen).
  - Simulaciones conectadas (id, n_agentes, última señal).
- El tab Zona Liminal en NiceGUI hace polling HTTP cada 5s a ese endpoint.
- Mapa Plotly Scattergl del mundo liminal (misma técnica que el mapa del mundo).

### C3 ✅ — Panel de estado del servidor liminal
- En el tab Zona Liminal:
  - Badge "Servidor: activo / inactivo" con ping.
  - Lista de simulaciones conectadas (sim_id, agentes enviados / recibidos).
  - Lista de agentes actualmente en tránsito.
  - Log de eventos recientes (agentes que entraron / salieron).

### C4 ✅ — Conexión desde launcher
- En el launcher (página `/`), si el servidor liminal está activo, mostrar IP:puerto.
- Campo "Conectar a servidor externo" (IP:puerto para multijugador entre PCs).
- `_start_sim` levanta `LiminalClient` + `PortalHex` + `AgentTransferHandler` y los registra en el clock.

---

## Bloque D — Polish y bugs pendientes ✦ media complejidad

### D1 — Fix DreamEngine: variabilidad de sueños
- Bug conocido: agentes con mismo arquetipo dominante + mismo complejo generan sueños idénticos.
- Causa: el pool composicional no usa suficiente entropía individual.
- Fix: añadir `agent.id[-4:]` como seed en la selección de símbolos; diversificar la capa de trauma.

### D2 — Tendencias: sincronización de zoom y primer carga
- Los 4 gráficos de Tendencias tienen ejes X independientes → al hacer zoom en uno no se propaga.
- Usar `subplots` con `shared_xaxes=True` en lugar de 4 figuras separadas.
- Esto requiere refactorizar `_build_trend_figure` en una sola figura multi-panel.

### D3 — ICL: sparkline de presión emocional
- El B1 del R5.2 prometía un historial sparkline de `emotional_pressure`.
- Implementar: pequeño `go.Scatter` de ancho 100% × alto 40px debajo del gauge.
- Data: los últimos 50 días de `cf_history` (si existe en checkpoint) o desde DB.

### D4 — Inspector de agentes: log episódico completo
- El G1 del R5.2 muestra radar pero no el log episódico prometido.
- Añadir en el dialog: scroll de los últimos 10 eventos del `episodic_memory` del agente.

### D5 — Mapa: agentes visibles en tiempo real
- Los agentes deben aparecer como marcadores sobre su hex actual, actualizándose en vivo.
- Diagnosticar por qué `_extract_agents_data` puede retornar lista vacía (excepciones silenciosas).
- Verificar que `agent.posicion` llega correctamente a `_hex_xy` y que el marcador (size=14) no queda oculto bajo el terreno (size=17).
- Meta: al hacer hover sobre un agente, ver nombre, tribu, arquetipo, humor y estado.

### D6 — Botón Cerrar simulación
- Añadir botón "Cerrar" en el header (junto a Pausar/Reanudar) que detenga el hilo de simulación limpiamente y cierre el servidor NiceGUI.
- Evitar tener que interrumpir con Ctrl+C en la consola.
- Implementación sugerida: `runner.stop()` → `app_state._pause_event.clear()` → `ui.run_javascript("window.close()")` o `app.shutdown()`.

---

## Bloque E — Merge y release ✦ proceso (requiere A+B+C completos)

### E1 — Tests de smoke para la UI
- Tests mínimos que verifiquen que las funciones de construcción de figuras no explotan:
  - `_build_hex_map` con datos reales del checkpoint.
  - `_build_social_graph` con checkpoint.
  - `_build_trend_figure` con datos de DB.
- No requieren NiceGUI corriendo — solo verifican que devuelven un objeto no-None.

### E2 — Merge `evolution` → `main`
- Requiere autorización explícita del usuario.
- Checklist previo: todos los tests verdes, UI funcional manual, README actualizado.

### E3 — Tag versión 1.0
- `git tag v1.0.0` en `main` con changelog.

---

## Orden de prioridad sugerido

```
A1 (commit staging)
A2 → A3 → A4       (estabilización, < 30 min)
B1 → B2 → B3       (mapa completo, ~1 hora)
C1 → C2 → C3 → C4  (zona liminal integrada, ~3-4 horas)
D1 → D2 → D3 → D4  (polish y bugs, ~2 horas)
E1 → E2 → E3       (merge y release)
```

---

*Rama: `evolution`. Merge a `main` solo con autorización explícita del usuario.*
