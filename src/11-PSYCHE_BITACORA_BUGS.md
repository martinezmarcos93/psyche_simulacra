# Bitácora de Bugs y Soluciones

Este documento sirve como registro histórico de los bugs más crípticos y complejos encontrados durante el desarrollo de **PSYCHE SIMULACRA**, junto con su análisis y resolución. Esto permite mantener un entendimiento claro de cómo interactúan las capas biológicas, psicológicas y del entorno.

---

## Bug #001: El Éxodo hacia el Vacío (Inanición Masiva)

**Síntoma:**
Al correr simulaciones largas (ej. 1000 días simulados), invariablemente todos los agentes terminaban muriendo por inanición o deshidratación, sin importar la abundancia inicial de recursos en su zona de origen.

**Análisis:**
El error no residía en la tasa de regeneración de recursos ni en las rutinas de alimentación, sino en la **Mecánica de Exploración (`_explore_action`)**.
1. Cuando un agente no encuentra recursos en su hexágono actual (porque los ha agotado temporalmente o porque es un bioma árido), la supervivencia sobreescribe su rutina y lo obliga a explorar (`_find_food_action` hace fallback a `_explore_action`).
2. La función `_explore_action` elegía una dirección aleatoria y actualizaba `self.posicion = target`.
3. **El problema:** No existía validación de los límites del mapa (una grilla estática de 80x60). Con el tiempo, la caminata aleatoria llevaba a los agentes a superar el borde (`q < 0`, `q >= 80`, `r < 0`, `r >= 60`).
4. Al salir del mapa, el agente entraba en coordenadas donde `TerrainGrid` no tenía celdas y `WorldCore` no generaba recursos. Al no haber recursos en el vacío, el agente volvía a explorar eternamente, adentrándose más en la nada hasta morir.

**Solución:**
Se implementó un `bounds checking` (validación de límites) en `_explore_action` dentro de `core/agents/agent.py`. Ahora, antes de elegir una dirección, el agente filtra las opciones inválidas. Si se encuentra en un borde, solo seleccionará direcciones que lo devuelvan hacia el interior de la isla (la grilla válida).

**Impacto:**
Los agentes ahora permanecen confinados al entorno simulado. Cuando agotan los recursos en el borde, se ven obligados a regresar hacia zonas previamente exploradas o a competir por el espacio, lo que reactiva la dinámica social y frena las muertes ilógicas por inanición, permitiendo a la simulación avanzar años sin colapsar por este motivo geométrico.

---

## Bug #002: El Letargo Sediento (Desbalance Metabólico)

**Síntoma:**
Aún tras solucionar el éxodo al vacío (Bug #001), simulaciones largas mostraban una extinción total cerca del día 100. Todos los agentes morían de `deshidratacion` y algunos de `inanicion`.

**Análisis:**
El análisis numérico del metabolismo en `core/agents/needs.py` y `core/agents/agent.py` reveló dos problemas fatales:
1. **Rendimiento de Recursos Mínimo:** La acción de beber agua consumía 1 hora (1 tick), pero el agua recolectada (`0.20` unidades) multiplicada por `_AGUA_POR_BEBER` (`0.60`) apenas saciaba un `12%` de la sed. Dado que la sed aumentaba `68%` por día, el agente requería agotar múltiples hexágonos enteros diariamente solo para sobrevivir, deforestando la isla de agua virtualmente al instante.
2. **Fatiga Acumulativa (Letargo):** El decaimiento de fatiga al dormir (`0.045` por tick) era insuficiente para compensar la fatiga ganada despiertos (`0.035` por tick). En 4 días, la fatiga superaba el umbral crítico de supervivencia (`0.80`). Al intentar resolver la fatiga, el agente "descansaba" en lugar de beber agua. Al permanecer despierto, la fatiga seguía aumentando y la sed se volvía mortal.

**Solución:**
1. Se ajustó `_FATIGA_RECOVER_SLEEP` en `needs.py` a `0.075` para que 8 horas de sueño restauren por completo el cansancio de 16 horas de actividad.
2. Se reajustaron drásticamente los factores de conversión metabólicos en `agent.py`: `_COMIDA_POR_RECOLECTA = 4.0`, `_COMIDA_POR_CAZA = 8.0` y `_AGUA_POR_BEBER = 5.0`.

**Impacto:**
Ahora una recolección exitosa de agua o comida sacia la necesidad en un 80-100%, permitiendo al agente hidratarse/alimentarse rápidamente y destinar el resto de sus horas del día a socializar, explorar o mantener el fuego, habilitando la verdadera emergencia social y permitiendo la supervivencia más allá de cientos de días.

---

## Bug #003: Colisión Hídrica Inicial (Muertes en Cluster — Días 10–27 y 200–700)

**Síntoma:**
En la Simulación 02 (8 horas, 27.675 días simulados), 69 de 105 muertes (65.7%) fueron por deshidratación. El primer cluster ocurrió entre los días 10–27 (10 muertos en el primer mes) y el segundo entre los días 200–700 (~40 muertos). El motor reportaba resource_pressure promedio de 0.038 — el mundo tenía agua más que suficiente.

**Análisis:**
Se identificaron tres causas compuestas que actuaban simultáneamente:

1. **Búsqueda de agua ciega al hex actual** (`core/agents/agent.py`, `_find_water_action()`):
   La función solo verificaba recursos en el hexágono en el que el agente ya estaba parado. Si no había agua allí (threshold `> 0.1`), el fallback era `_explore_action()`, que movía al agente a un hex vecino **sin intentar beber en ese nuevo hex hasta el siguiente tick**. El agente gastaba ticks moviéndose en lugar de beber.

2. **Competencia masiva por el mismo hex de agua** (`data/seeds/initial_personas.yaml`):
   Los 100 agentes fundadores inician todos en el mismo hex `[40, 30]`. Ese bioma tiene `agua_lluvia` capeada en `0.60`. Con 100 agentes compitiendo simultáneamente, solo ~3 podían beber por tick. El resto acumulaba sed sin posibilidad de saciarla.

3. **Schedule infra-dotado para agua** (`core/agents/schedule.py`):
   El schedule default asignaba **solo 1 hora/día** (hora 6) a `buscar_agua`, contra 8 horas para `buscar_alimento`. La sed acumula ~0.68/día; con 1 hora efectiva de búsqueda y competencia por recursos, el balance era insostenible para la mayoría.

El cluster secundario (días 200–700) se explica por el mismo bug amplificado por el modificador estacional: en invierno la regeneración de agua baja a 20% (`_REGEN_MOD["invierno"] = 0.20`), haciendo que los hexes habituales queden secos y los agentes no logren encontrar agua en radio inmediato.

**Solución:**
1. `_find_water_action()` ampliada para buscar agua en los **6 hexágonos vecinos** si el hex actual está seco, moviéndose directamente al primero con agua disponible en lugar de explorar aleatoriamente.
2. Schedule default ajustado: se agrega hora 7 como segunda hora de `buscar_agua` (total: 2 horas/día para agua, manteniendo 7 para alimento).

**Impacto:**
Los agentes con sed crítica ahora tienen un radio de búsqueda activa de agua en lugar de quedarse varados en hexes secos. El cluster de días 10–27 debería desaparecer (la competencia por el hex inicial se resuelve porque los agentes se dispersan hacia hexes vecinos con agua). El cluster de invierno debería atenuarse significativamente.

---

## Auditoría General de Codebase — 2026-05-23

Auditoría exhaustiva realizada tras implementar el sistema cross-sim liminal, integración ngrok y menú simplificado. Se escaneó el proyecto completo en busca de bugs, inconsistencias lógicas, problemas arquitectónicos, rendimiento, edge cases y cobertura de tests.

---

### 🔴 CRÍTICOS (causan crash o pérdida de datos)

**C1 — Mutación directa de posición dentro del bucle de decisión**
`core/agents/agent.py` — `_find_water_action` (~línea 459) y `_explore_action` (~línea 503)

El agente muta `self.posicion` durante `decide_action()`, que es llamado desde `AgentCore._tick_agents()`. Esto ocurre antes de que `world_ref.receive_actions(actions)` procese los movimientos. El mundo nunca aprueba estas posiciones: colisiones no se detectan, recursos no se actualizan correctamente (la celda "origen" no se libera), y el contador `pos_counts` usado para detectar aliados queda desincronizado en el mismo tick. Si dos agentes mutan a la misma celda, el mundo no lo ve.

**Estado:** ✅ CORREGIDO (2026-05-24) — `_find_water_action` ahora devuelve MOVERSE cuando el agua está en otro hex y recolecta el tick siguiente. `_explore_action` conserva la mutación directa porque es el mecanismo establecido de movimiento en esta arquitectura.

---

**C2 — `_connected` se activa antes de que `sim_connect` llegue al servidor**
`core/liminal/liminal_client.py`

La flag `self._connected = True` se establece en el handler de apertura del WebSocket, antes de que `sim_connect` llegue al servidor. Si el AgentTransferHandler llama `send_agent_enter` en ese tick estrecho, el servidor recibe un agente de una simulación no registrada, lo rechaza silenciosamente, y el agente queda con `in_liminal=True` permanentemente — suspendido para siempre, sin posibilidad de retorno.

**Estado:** ⚠️ MITIGADO — C3 ahora tiene timeout de recuperación (480 ticks). El race condition en C2 sigue existente pero tiene salvaguarda.

---

**C3 — Agentes con `in_liminal=True` permanente si el servidor se cae antes de `agent_placed`**
`core/liminal/agent_transfer.py`

Si la conexión se corta entre `agent_enter` enviado y `agent_placed` recibido, el agente queda en `self._in_transit` con `agent.in_liminal=True`. Al reconectar, el cliente no reenvía agentes en tránsito pendientes. El agente queda congelado hasta el próximo `agent_return` que nunca llega. No hay timeout de recuperación.

**Estado:** ✅ CORREGIDO (2026-05-24) — Agregado `_transit_ticks` dict y `_recover_stuck_agents()`. Tras 480 ticks (~20 días simulados) sin recibir `agent_placed`, el agente se restaura automáticamente al portal con cooldown de reentrada.

---

### 🟠 IMPORTANTES (comportamiento incorrecto)

**I1 — O(n²) en procesamiento nocturno de sueños**
`core/agents/agent_core.py` — `_process_nightly_dreams`

Itera todos los pares de agentes vivos para calcular resonancia de sueños. Para 100 agentes = 4.950 comparaciones/noche; para 200 = ~20.000. Con simulaciones largas y poblaciones crecientes, este loop domina el tiempo de CPU.

**Estado:** ✅ CORREGIDO (2026-05-24) — Optimizado a O(E): itera aristas del grafo social (`social_network.graph.edges(data=True)`) con deduplicación de pares via `frozenset`. La condición `same_tribe + bond > 0.35` requiere arista existente, por lo que no se pierde ningún par elegible.

---

**I2 — Agentes muertos procesan complejos psicológicos**
`core/agents/agent.py` — `on_day()` (~línea 278)

Los agentes muertos activan complejos basados en el evento "muerte" en cada tick diario. Los complejos de un cadáver evolucionan silenciosamente. No produce crash, pero contamina datos de análisis y consume CPU innecesariamente.

**Estado:** ✅ CORREGIDO (2026-05-24) — `on_day()` retorna inmediatamente si `not self.is_alive`. Cero procesamiento en agentes muertos.

---

**I3 — `es_medianoche` y `es_inicio_dia` son idénticos**
`core/time/simulation_clock.py` — líneas 27-28

```python
es_medianoche  = hora == 0
es_inicio_dia  = hora == 0
```

Ambas flags son exactamente iguales. La intención probablemente era que `es_medianoche` fuera `hora == 23`. Cualquier código que distinga semántica entre ellas tiene un bug silencioso.

**Estado:** ✅ CORREGIDO (2026-05-24) — `es_medianoche = hora == 23`, `es_inicio_dia = hora == 0`. Ambas flags y sus tests actualizados.

---

**I4 — Inconsistencia en fuentes de agua: sed crítica vs sed normal**
`core/agents/agent.py`

`_decide_via_collapse` (sed crítica) reconoce: `agua`, `lago`, `rio`, `oasis`.
`_find_water_action` (sed normal) reconoce: `agua`, `lago`, `rio`, `oasis`, `agua_salobre`, `nieve`.

Los tipos `agua_salobre` y `nieve` son ignorados durante sed crítica. Un agente con sed crítica parado sobre nieve no bebe y muere.

**Estado:** ✅ CORREGIDO (2026-05-24) — `agua_salobre` y `nieve` añadidos a la lista de fuentes en `_decide_via_collapse`. Ambas funciones ahora reconocen los mismos 6 tipos.

---

**I5 — Inicio de simulación dispara `es_inicio_dia=True` en tick 0**
`core/simulation.py` — `new_session()`

La simulación arranca con `hora=0`. El primer tick activa inmediatamente los handlers de `on_day`: chequeos de muerte, generación de sueños, crystallización de mitos, persistencia — todo antes de que cualquier agente haya actuado. Agentes que empiezan con necesidades altas pueden morir en el primer tick sin haber tenido oportunidad de actuar.

**Estado:** ✅ CORREGIDO (2026-05-24) — `SimulationRunner.__init__` arranca en `start_hora=6` (6 AM). El primer `on_day` se dispara a las 24 horas reales de simulación, tras un día completo de actividad.

---

**I6 — Pool de nombres se agota sin advertencia**
`core/agents/agent_core.py` — `_generate_offspring`

El pool tiene 38 nombres. Al agotarse, los descendientes reciben `f"Descendiente_{hijo_id}"` sin ningún log de warning. En simulaciones largas con alta natalidad, el mapa se llena de "Descendiente_847".

**Estado:** ✅ CORREGIDO (2026-05-24) — Agotamiento del pool emite `print` de advertencia visible en consola. Expandir el pool de nombres es tarea futura (sin prioridad).

---

**I7 — `sociabilidad` nunca dispara override**
`core/agents/needs.py`

La necesidad `sociabilidad` se incrementa correctamente pero nunca supera `OVERRIDE_THRESHOLD=0.80` para disparar una acción prioritaria, porque ningún handler la consume ni la reduce. Es un acumulador sin consumidor — sube indefinidamente hasta 1.0 sin efecto.

**Estado:** ✅ CORREGIDO (2026-05-24) — `Needs.social_override_active()` añadido. `_decide_via_collapse()` consume `-0.30` de sociabilidad al ejecutarse. En `Agent.decide_action()`, aislamiento crítico (sociabilidad ≥ 0.80) dispara `_decide_via_collapse` incluso fuera de la hora de "interactuar".

---

### 🟡 MENORES (code smells, deuda técnica)

**M1 — `_DREAM_HORA = 22` es código muerto**
`core/agents/agent.py` línea 26. La constante está definida pero los sueños siempre se procesan en `on_day()` a hora=0. Nunca se usa.

**Estado:** ✅ CORREGIDO (2026-05-24) — Constante eliminada.

**M2 — Stubs vacíos en `core/psyche/` y `core/quantum/`**
Ambos contienen solo `__init__.py` de una línea. `core/psyche/archetypes.py` es un stub, pero `core/agents/psyche/archetypes.py` es el real. Un import accidental de la ruta equivocada importa silenciosamente un stub vacío sin error.

**Estado:** ✅ CORREGIDO (2026-05-24) — Directorios `core/psyche/` y `core/quantum/` eliminados. Verificado que ningún módulo importaba de esas rutas.

**M3 — `hay_aliados` calculado sobre posiciones pre-mutación**
`pos_counts` se construye antes de las mutaciones directas de `_find_water_action`/`_explore_action`. Los agentes que se mueven "fuera del sistema" afectan el contador de aliados de otros agentes de forma inconsistente.

**M4 — Doble responsabilidad frágil en registro de muertes**
`_register_death` actualiza el campo tribal local; `absorb_event("muerte")` global ocurre solo en `_persist_day`. Si `_persist_day` falla (excepción, shutdown abrupto), el campo colectivo global no registra la muerte.

**M5 — `on_day()` llamado para agentes `in_liminal`**
Los agentes en el liminal reciben `on_day()` completo. Aunque los checks críticos están guarded, otros efectos secundarios (complejos, sueños locales) pueden ejecutarse. Requiere auditoría caso por caso.

**M6 — `_apply_encounter_effects` usa `arch_attr = "self_"` para arquetipo "self"**
Si el atributo real en `ArchetypeProfile` no se llama `self_`, el `setattr` falla silenciosamente sin lanzar excepción.

---

### 🧩 INCONSISTENCIAS DOCUMENTACIÓN vs CÓDIGO

**D1 — FAQ.md del liminal dice que el retorno no está implementado (Fase 7 pendiente)**
El retorno está completamente implementado en `agent_transfer._handle_agent_return` y `websocket_server._return_agent`. La documentación está desactualizada.

**D2 — README del liminal dice "Duración: 60 ticks liminales (~2 min)" como si fuera fijo**
El valor es configurable via `return_after_ticks` del servidor.

**D3 — README del liminal dice spawn "radio 1-3 hex" — verificar contra código real en `agent_registry.py`**

**D4 — FAQ raíz puede tener referencias a 8 opciones de menú (el menú actual tiene 7)**

**D5 — README liminal menciona `python scripts/visualizer.py --liminal` — verificar que el flag exista**

---

### 🏗️ PROBLEMAS ARQUITECTÓNICOS

**A1 — Dos fuentes de verdad para posición del agente**
`WorldCore` mantiene un grid hexagonal con ocupantes. `Agent.posicion` es la fuente de verdad del agente. Las mutaciones directas en `agent.py` crean divergencia. La arquitectura correcta: el agente propone acción → world valida → world actualiza grid → world actualiza `agent.posicion`.

**A2 — Queue del WebSocket puede acumular `agent_enter` duplicados bajo lag de red**
Si hay retry logic y la queue crece más rápido de lo que el send_loop la consume, el servidor puede recibir múltiples entradas del mismo agente.

**A3 — Sin circuit breaker para el liminal**
Si el servidor está caído y el reconnect loop está activo, `_in_transit` acumula IDs sin timeout de limpieza. No hay mecanismo para recuperar agentes suspendidos tras una desconexión prolongada.

**A4 — Prioridades del SimulationClock no están documentadas centralmente**
Los handlers se registran con prioridades hardcodeadas en distintos archivos (WorldCore=10, AgentCore=20, AgentTransferHandler=25, persistence=30). No existe un archivo central que liste todas las prioridades. Un nuevo handler con prioridad incorrecta rompe el orden silenciosamente.

---

### 🧪 FALTA DE COBERTURA EN TESTS

**T1 — Zero tests para el flujo liminal completo**
`agent_enter → agent_placed → agent_return → _apply_encounter_effects` no tiene ningún test.

**T2 — Zero tests para edge cases de muerte**
Agente muere en tick 0, agente con `in_liminal=True` y `is_alive=False` simultáneamente, `_register_death` llamado dos veces.

**T3 — Zero tests para WebSocket bajo desconexión**
Servidor cae después de `agent_enter` pero antes de `agent_placed`, reconexión con agentes en `_in_transit`, timeout de ngrok.

**T4 — Sin tests de integración para el orden de ejecución del SimulationClock**
El orden de handlers no está verificado — un refactor de prioridades puede romperlo sin que ningún test falle.

**T5 — Sin tests para `_apply_encounter_effects` con arquetipos inválidos**
Si `dominant_archetype` no está en `_ARCH_RESONANCE` o `arch_attr` no existe en `agent.archetypes`, el efecto falla silenciosamente.

---

### ✅ COSAS QUE FUNCIONAN CORRECTAMENTE

- **Import de `_ARCHETYPE_SYMBOLS`** en `agent_core.py` — correcto, sin import circular.
- **Deaths no se cuentan doble** — `_register_death` actualiza solo el campo tribal local; `absorb_event("muerte")` global ocurre solo en `_persist_day`. Confirmado por comentario explícito.
- **`queue.Queue` para thread-safety del liminal** — comunicación entre thread WebSocket y thread del clock correcta.
- **Cooldown de reentrada al portal (48 ticks)** — implementado correctamente, previene reentrada inmediata sin prohibir visitas futuras.
- **Detección de huérfanos** — lógica correcta, sin falsos positivos conocidos.
- **ngrok auto-detección** via `localhost:4040/api/tunnels` — método oficial de ngrok.
- **Serialización de checkpoint** — `in_liminal` serializado, `_pending_liminal_encounter` transient intencional.
- **`drain_incoming()` es idempotente** — vaciar una queue vacía no lanza excepción.
- **Biomas liminales puramente visuales** — no producen ni consumen recursos.

---

### Top 10 Acciones Priorizadas — Estado Final

| # | Acción | Estado |
|---|--------|--------|
| 1 | Mutaciones directas de posición en `_find_water_action` | ✅ CORREGIDO |
| 2 | Timeout de `_in_transit` (C3) | ✅ CORREGIDO |
| 3 | `agua_salobre` y `nieve` en sed crítica (I4) | ✅ CORREGIDO |
| 4 | `es_medianoche = hora==23` (I3) | ✅ CORREGIDO |
| 5 | `on_day()` retorna si agente muerto (I2) | ✅ CORREGIDO |
| 6 | Optimización O(n²) → O(E) en sueños (I1) | ✅ CORREGIDO |
| 7 | `start_hora=6` en nueva sesión (I5) | ✅ CORREGIDO |
| 8 | FAQ.md liminal: retorno implementado (D1) | ✅ CORREGIDO |
| 9 | Tests de integración liminal (T1–T5) | ✅ CORREGIDO (43 tests en `test_bug_fixes.py`) |
| 10 | Eliminar stubs vacíos `core/psyche/` y `core/quantum/` (M2) | ✅ CORREGIDO |

### Bug extra descubierto durante tests

**B1 — `agent.archetypes.weights` no existe — debería ser `to_dict()`**
`core/liminal/agent_transfer.py` — `_transfer_agent()`
El código usaba `agent.archetypes.weights.items()` que lanzaría `AttributeError` cada vez que un agente cruzara el portal. Corregido a `agent.archetypes.to_dict().items()`.
**Estado:** ✅ CORREGIDO (2026-05-24)

**B2 — `agent.traits.openness/conscientiousness/agreeableness/neuroticism` no existen**
`core/liminal/agent_transfer.py` — `_transfer_agent()`
Los rasgos en `TraitProfile` usan nombres en español (`apertura`, `responsabilidad`, `amabilidad`, `neuroticismo`). El código usaba los nombres en inglés, causando `AttributeError`. Corregido a `agent.traits.to_dict()`.
**Estado:** ✅ CORREGIDO (2026-05-24)
