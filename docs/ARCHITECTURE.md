# Arquitectura de PSYCHE SIMULACRA

Este documento describe la arquitectura real del sistema tal como está implementada
en el código, no como aspiración. Cuando el código y la documentación anterior
(README, roadmaps) discreparan, este documento sigue al código.

---

## 1. Vista general

Dos núcleos sincrónicos, gobernados por un reloj único, más una capa de
observabilidad/persistencia que se cuelga de ambos vía eventos:

```
                    ┌─────────────────────┐
                    │   SimulationClock    │  tick = 1 hora simulada
                    │ (core/time)          │  24 ticks = 1 día
                    └──────────┬───────────┘
                               │ emite tick / day / season_change
                               │ a handlers por prioridad (menor primero)
        ┌──────────────────────┼───────────────────────┬───────────────┐
        │ priority=10          │ priority=20            │ priority=25   │ priority=30/99/100
        ▼                      ▼                        ▼               ▼
  ┌───────────┐         ┌─────────────┐          ┌──────────────┐  ┌────────────┐
  │ WorldCore │  snap-  │  AgentCore  │  accio-  │AgentTransfer │  │Persistencia│
  │ (mundo    │ ─shot─▶ │ (agentes,   │ ─nes───▶ │Handler       │  │/ métricas /│
  │  físico)  │         │  psicología,│          │(Zona Liminal,│  │ stopper /  │
  │           │◀────────│  sociedad)  │          │ opcional)    │  │ extinction │
  └───────────┘ pending └─────────────┘          └──────────────┘  └────────────┘
     actions
```

`SimulationClock` (`core/time/simulation_clock.py`) no pertenece a ninguno de los
dos núcleos. Mantiene tres listas de handlers (`on_tick`, `on_day`,
`on_season_change`), cada una ordenada por `ClockPriority` (menor se ejecuta
primero): `WORLD=10 → EVENT_BRIDGE=15 → AGENT=20 → LIMINAL=25 → PERSISTENCE=30 →
STOPPER=99 → EXTINCTION=100`. El loop principal (`_run_loop`) por cada tick:

1. Construye el `TimePoint` (hora, día, año, estación, flags de amanecer/mediodía/etc.).
2. `_emit_tick(tp)` — llama todos los handlers de tick en orden de prioridad.
3. Si `tp.es_inicio_dia` (hora 0), `_emit_day(tp)` — handlers de día.
4. `_check_season_change(tp)` — si cambió la estación, handlers de estación.
5. Avanza el tick. Si `set_speed()` fijó un intervalo mínimo, duerme lo que falte
   (para observación en tiempo real); si no, `time.sleep(0)` (solo cede el
   intérprete, corre a máxima velocidad — así funciona el modo headless).

Un `shutdown()` llamado desde cualquier handler completa el tick en curso (nunca
hay ticks parciales) y termina el loop de forma ordenada.

---

## 2. El ciclo de un tick, en orden real de ejecución

```
SimulationClock._run_loop()
│
├─ WorldCore.on_tick(tp)                                    [priority=10]
│   ├─ climate.update(tp)                     → nuevo estado climático
│   ├─ fire.update(climate_state)             → propagación/decaimiento de fuego
│   ├─ _apply_pending_actions(climate_state)  → resuelve las WorldAction del tick anterior
│   └─ _produce_snapshot(tp, climate_state)   → WorldSnapshot (lo que AgentCore leerá)
│
├─ AgentCore.on_tick(tp)                                    [priority=20]
│   snapshot = world_ref.current_snapshot
│   para cada agente vivo (no en tránsito liminal):
│     ├─ agent.update_biological(tp, snapshot)      → hambre/sed/fatiga/salud
│     ├─ agent.decide_action(tp, snapshot,
│     │        local_field, hay_aliados,
│     │        mythology_engine)                    → WorldAction | None
│     │        (ver §4 — aquí vive la "ecuación personal")
│     └─ se acumula en `actions`
│   ├─ interaction_engine.process_zone_interactions(...)   → cooperación/conflicto/
│   │                                                          manipulación entre
│   │                                                          agentes co-ubicados
│   ├─ social_network.propagate_entanglement(agents)        → entrelazamiento cuántico
│   ├─ world_ref.receive_actions(actions)                    → encola para el próximo
│   │                                                          on_tick de WorldCore
│   └─ cadena chamánica: sustancias psicoactivas consumidas este tick
│
└─ (si tp.es_inicio_dia) → on_day de ambos núcleos, ver §3
```

`WorldCore` y `AgentCore` nunca se llaman directamente entre sí: `WorldCore`
publica un `WorldSnapshot` (`core/interface/world_snapshot.py`) inmutable por
tick, y `AgentCore` publica `WorldAction`s (`core/interface/world_action.py`) que
`WorldCore` recién aplica en **el tick siguiente**. Este desacople de un tick es
deliberado — evita que el orden de iteración de agentes afecte el mundo dentro
del mismo tick.

---

## 3. El ciclo de un día simulado

`AgentCore.on_day()` (`core/agents/agent_core.py:259`) es el método más largo del
proyecto — encadena ~30 sistemas, en este orden real (ver comentarios numerados en
el código fuente, que son la referencia autoritativa si este documento queda
desactualizado):

1. Decaimiento del campo memético global (`CollectiveField.decay()`).
2. Atención selectiva a eventos climáticos + propagación de rumores.
3. Cristalización mítica global (`MythologyEngine.check_crystallization`, incluye
   `apply_myth_effects`).
4. Mecánicas tribales: re-clustering (`TribeManager`, cada 30 días), campos locales,
   mitos locales, deriva arquetípica por bioma.
5. Cultura material: construcción de estructuras (`CultureEngine`) y aplicación de
   sus auras.
6. Vitalidad: hambre/sed/vejez → muertes; mortalidad selectiva por catástrofe;
   migración forzada; orfandad.
7. Envejecimiento anual + distorsión narrativa pasiva de los mitos.
8. Reproducción (cooldowns, nacimientos).
9. Resonancia grupal por sustancias psicoactivas compartidas.
10. Sueños nocturnos con entrelazamiento (`DreamGrammarEngine`).
11. **Consolidación del MentalVault** (paso "9b" en el código — una vez por
    agente vivo con el flag activo; ver §6).
12. Contagio emocional, histeria colectiva multi-umbral.
13. **Sesgo causal → tabúes emergentes** (`PerceptionSystem.check_causal_bias`,
    registrado en memoria cultural tribal si supera umbral).
14. Proyección/autoengaño, sesgo de atribución, paranoia tribal, disonancia
    cognitiva post-mito.
15. Conocimiento técnico: descubrimiento accidental, transmisión, especialización,
    intercambio inter-tribal.
16. Economía simbólica (deuda ritual, prestigio), imprinting infantil, geografía
    psicológica, lenguaje emergente (`EmergentLexiconSystem`), eco inter-tribal.
17. Re-vivencias de memoria episódica, disociación por sombra, duelo diferenciado,
    presencia ancestral, rencores arquetípicos, proto-chamanismo, cristalización
    de deidades, objetos sagrados, roles sociales emergentes.
18. Refugio nocturno + actualización de coordenadas ocupadas para `WorldCore`.

`WorldCore.on_day()` corre en paralelo (prioridad 10, antes que `AgentCore`):
catástrofes, fauna simbólica, geografía psíquica, regeneración de recursos y
fauna, tumbas, sustancias.

La longitud y el numerado no-consecutivo (`3b`, `3d`, `9b`, `17h`…) reflejan la
historia real del proyecto: cada roadmap insertó su paso donde correspondía
causalmente, no al final. Es deuda de legibilidad conocida, no un error.

---

## 4. `Agent.decide_action()` — dónde vive la decisión individual

```
decide_action(tp, snapshot, collective_field, hay_aliados, mythology_engine)
│
├─ [si InterpretiveFilter activo] percibir SIEMPRE, una vez por tick
│    stim = _build_stimulus(snapshot, hay_aliados)          (Stimulus físico)
│    last_perceived_event = interpretive_filter.interpret(
│        stim, self, collective_field, mythology_engine)    (PerceivedEvent)
│    [si MentalVault activo] mental_vault.accumulate(last_perceived_event)
│
├─ disociación activa → override total (ver AGENT_BRAIN.md §Disociación)
├─ necesidad crítica (sed/hambre/fatiga) → override de supervivencia
├─ aislamiento social crítico → _decide_via_collapse(...)
├─ actividad == "interactuar" (agenda horaria) → _decide_via_collapse(...)
└─ resto de la agenda → dormir/descansar/buscar_alimento/buscar_agua/cazar/explorar
```

`_decide_via_collapse()` es donde el motor cuántico decide una de cuatro acciones
conductuales (`cooperacion | competencia | aislamiento | manipulacion`), mezclando
sesgos de arquetipo, complejos, rasgos, campo colectivo y —si el filtro está
activo— la interpretación afectiva del estímulo actual. Ver `AGENT_BRAIN.md` y
`ARCHETYPES.md` para el detalle de cada canal.

---

## 5. Componentes principales y sus responsabilidades

| Componente | Archivo | Responsabilidad |
|---|---|---|
| `SimulationClock` | `core/time/simulation_clock.py` | Único reloj; ordena todo por prioridad. |
| `WorldCore` | `core/world/world_core.py` | Terreno, clima, fauna, recursos, fuego, catástrofes, estructuras persistentes. |
| `AgentCore` | `core/agents/agent_core.py` | Dueño de todos los `Agent`; orquesta el día (~30 sistemas sociales/culturales). |
| `Agent` | `core/agents/agent.py` | Las 4 capas de un individuo (biológica/psicológica/social/simbólica); decide su acción. |
| `PerceptionSystem` | `core/social/perception.py` | Percepción limitada por radio, rumores con distorsión por salto, sesgo causal → tabúes. |
| `InterpretiveFilter` | `core/agents/psyche/interpretive_filter.py` | La "ecuación personal": estímulo físico → respuesta afectiva escalar + préstamo de vocabulario (Fase 1). |
| `MentalVault` | `core/agents/mental_vault/` | Mini cerebro por agente; neuronas que se enlazan por la misma física que los mitos colectivos (Fase 2). |
| `ArchetypeVector` / `ComplexProfile` / `TraitProfile` | `core/agents/psyche/` | Los 12 arquetipos jungianos, 6 complejos activables, Big Five + rasgos clínicos. |
| `collapse_state` | `core/agents/quantum/collapse.py` | Colapsa la superposición conductual en una acción, mezclando todos los canales de sesgo. |
| `CollectiveField` (global y por tribu) | `core/social/collective_field.py` | El inconsciente colectivo: símbolos, `emotional_pressure`, `myth_pressure`, `confusion`. |
| `MythologyEngine` | `core/social/mythology.py` | Proto-mitos → cristalización → `MythCrystal` → `Leyenda`; deidades. |
| `TribeManager` | `core/social/tribe_manager.py` | Clustering (`greedy_modularity_communities`), campos locales, memoria cultural por tribu. |
| `CultureEngine` | `core/world/culture_engine.py` | Estructuras materiales (tótem/altar/muralla/hoguera) y sus auras. |
| `EmergentLexiconSystem` | `core/social/emergent_lexicon.py` | Nombres fonéticos para símbolos dominantes, por tribu. |
| `NarratorEngine` + `OllamaDaemon` | `core/narrative/` | Genera leyendas en lenguaje natural vía LLM local (Ollama), con fallback a plantillas. |
| `PsycheRuntime` | `core/runtime/psyche_runtime.py` | Orquestador para la UI: única fuente de verdad, `EventBus`, `ServiceManager`. |
| `SimulationRunner` | `core/simulation.py` | Orquestador "de motor": une clock + world + agents + persistencia + Obsidian. |
| `DatabaseManager` / `CheckpointManager` | `persistence/` | SQLite (WAL) + checkpoints JSON atómicos cada 10 días. |
| `ObsidianSync` | `obsidian/sync.py` | Sincroniza vault Markdown (personas, tribus, colectivo). |
| `AgentTransferHandler` / `LiminalClient` | `core/liminal/` | Zona Liminal opcional: agentes cruzan a un servidor WebSocket compartido entre simulaciones. |

---

## 6. Dos modos de ejecución

El proyecto corre en dos configuraciones muy distintas en costo, y es importante
no confundirlas al leer benchmarks o el README:

- **Modo completo** (`SimulationRunner`, vía `main.py` / `ui/`): con SQLite, vault
  Obsidian, narrativa LLM y el observatorio NiceGUI. Es el modo "de producción",
  pensado para sesiones largas en tiempo real (`~1 min real ≈ 1 día simulado` a
  máxima velocidad headless *con* estas capas, según el README).
- **Modo headless de investigación** (`scripts/ab_interpretive.py`,
  `scripts/run_robustness.py`): clock + `WorldCore` + `AgentCore` desnudos, sin
  BD/narrativa/Obsidian/UI. Es ~250-600× más rápido: en las mediciones de esta
  sesión, 300 días con 100 agentes corrieron en ~140-160 s (≈0.5 s/día), no
  minutos. Este es el modo correcto para experimentos A/B reproducibles — el
  costo de la narrativa LLM y la UI no debe confundirse con el costo del modelo
  psicológico en sí.

---

## 7. Dependencias entre componentes (qué necesita a qué)

```
Agent
 ├─ requiere: Needs, ScheduleSystem, ArchetypeVector, ComplexProfile, TraitProfile,
 │            PerceptionSystem, DreamGrammarEngine, LindBladChannel
 ├─ opcional (flags): InterpretiveFilter (requiere PerceivedEvent/Stimulus),
 │            MentalVault (requiere InterpretiveFilter activo)
 └─ recibe en cada decide_action(): WorldSnapshot, CollectiveField (local),
            MythologyEngine (global) — nunca los posee, solo los consulta

AgentCore
 ├─ posee: dict[str, Agent], TribeManager, CollectiveField (global),
 │         MythologyEngine (global, único — no hay una instancia por tribu pese
 │         a que CollectiveField sí tiene versión local por tribu; ver limitación
 │         en EMERGENCE.md), InteractionEngine, SocialNetwork, CultureEngine,
 │         EmergentLexiconSystem, CulturalMemory (por tribu, vía TribeManager)
 └─ lee: WorldCore.current_snapshot (nunca escribe el mundo directamente)

WorldCore
 └─ no conoce a AgentCore ni a Agent — solo lee WorldAction genéricas y expone
    WorldSnapshot. Esta es la frontera de desacople más estricta del proyecto.

SimulationRunner
 └─ conecta SimulationClock + WorldCore + AgentCore + persistencia + Obsidian +
    NarratorEngine. Es el único que conoce todas las piezas a la vez.
```

---

## 8. Persistencia, checkpoints y transferencia entre simulaciones

- **SQLite (WAL)** vía `DatabaseManager` + `WriteBuffer`: snapshots de agentes,
  clima, muertes, sesiones. Escritura en buffer para no bloquear el tick.
- **`CheckpointManager`**: guardado atómico JSON cada `CHECKPOINT_INTERVAL` días
  (10 por defecto) y al apagar (`atexit`). `SimulationRunner.resume()` reconstruye
  el estado completo desde el último checkpoint + DB.
- **`ObsidianSync`**: sincronización diaria a un vault Markdown legible por humanos
  (`vault/Personas/`, `vault/Tribus/`, `vault/Colectivo/`).
- **Zona Liminal** (opcional): cada simulación tiene un `SIM_ID` propio
  (`data/sim_id.txt`). Un `PortalHex` de posición determinista por seed permite
  que un agente "cruce" a un servidor WebSocket central (`liminal_server/`,
  headless, mapa hexagonal propio); el `AgentTransferHandler` (prioridad 25, entre
  `AgentCore` y la capa de persistencia) lo suspende del ciclo local mientras está
  en tránsito y lo reintegra tras `LIMINAL_RETURN_AFTER_TICKS`. Es la única vía por
  la que dos procesos de PSYCHE SIMULACRA se comunican en tiempo real.

---

## 9. Dónde mirar para más detalle

- `AGENT_BRAIN.md` — el "cerebro digital" de un agente, pieza por pieza.
- `ARCHETYPES.md` — el vector arquetípico, su activación/resonancia/cristalización.
- `MENTAL_VAULT.md` — el mini cerebro por agente (Fase 2 de la Ecuación Personal).
- `EMERGENCE.md` — qué está diseñado y qué emerge realmente, sin ambigüedad.
- `experiments/` — experimentos registrados con hipótesis, método y resultados.
- `DEVELOPMENT_LOG.md` — bitácora técnica sesión a sesión.
