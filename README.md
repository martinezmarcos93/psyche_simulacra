# PSYCHE SIMULACRA

Laboratorio computacional de emergencia del inconsciente colectivo.

Un sistema de simulación de agentes (ABM) donde 100+ individuos psicológicamente
complejos interactúan en un mundo físico real, generando jerarquías, símbolos,
tabúes, mitos y rituales sin que ninguno de estos fenómenos esté programado.
El inconsciente colectivo emerge — no se construye.

---

## Concepto

Cada agente carga un vector arquetípico jungiano (12 arquetipos), rasgos
dimensionales (Big Five + clínico), complejos activables por contexto, memoria
episódica, sueños y vínculos sociales. Sus interacciones alimentan un campo
colectivo que acumula carga simbólica. Cuando esa carga supera un umbral,
cristaliza en proto-mitos con efectos conductuales reales sobre el grupo.

El experimento busca responder:
- ¿Cuándo emerge el primer mito?
- ¿El tabú del incesto aparece antes o después del primer mito?
- ¿El héroe emerge del poder o de la narrativa?
- ¿La cooperación o la jerarquía aparece primero?

---

## Arquitectura

```
[ Obsidian Vault ] <──> [ Motor Python ] <──> [ Dashboard Streamlit ]
  Perfiles vivos          ABM tick-based         Visualización del
  Red simbólica           Lógica psico-social     inconsciente colectivo
  Narrativa emergente     Mecánicas cuánticas
```

### Dos núcleos sincrónicos

```
SimulationClock (entidad independiente)
        │
        ├─── priority=10 ──> WorldCore   (Núcleo 1: mundo físico)
        │                    Clima, terreno, fauna, recursos
        │                    No conoce la psicología
        │
        └─── priority=20 ──> AgentCore  (Núcleo 2: agentes)
                             Psicología, decisiones, interacciones
                             No modifica el mundo directamente
```

**Ciclo de un tick (1 hora simulada):**
1. `WorldCore` actualiza clima, recursos, fauna → produce `WorldSnapshot`
2. `AgentCore` lee el snapshot → cada agente decide → produce lista de `WorldAction`
3. Las acciones se aplican al mundo para el tick siguiente
4. Persistencia a SQLite + checkpoints

### Cuatro capas del agente

| Capa | Contenido |
|------|-----------|
| Biológica | hambre, fatiga, salud, edad |
| Psicológica | 12 arquetipos, 6 complejos, Big Five, estado emocional, memoria episódica |
| Social | vínculos (grafo NetworkX), rol, status, deudas |
| Simbólica | carga de campo, proto-símbolos, sueños, herencia simbólica |

---

## Escala temporal (beta)

```
1 tick      = 1 hora simulada
1 día       = 24 ticks
1 min real  = 1 día simulado
1 hora real = ~60 días simulados (~2 meses)

Sesión de 2h → 120 días simulados (~4 meses de vida del grupo)
```

---

## Estructura del proyecto

```
PSYCHE SIMULACRA/
│
├── core/                          # Motor central
│   ├── time/
│   │   └── simulation_clock.py   # ✅ SimulationClock, TimePoint, ClockState
│   ├── interface/
│   │   ├── world_action.py       # ✅ WorldAction, ActionType
│   │   ├── world_snapshot.py     # ✅ WorldSnapshot (inmutable)
│   │   └── action_result.py      # ✅ ActionResult
│   ├── world/                    # Núcleo 1 — El mundo físico
│   │   ├── climate.py            # ✅ ClimateSystem
│   │   ├── terrain.py            # ✅ TerrainGrid hexagonal 80×60
│   │   ├── resources.py          # ✅ ResourceSystem
│   │   ├── fauna.py              # ✅ FaunaSystem
│   │   ├── fire.py               # ✅ FireSystem
│   │   └── world_core.py         # ✅ WorldCore (orquestador)
│   ├── agents/                   # Núcleo 2 — Los agentes
│   │   ├── agent.py              # ✅ Agent (capa biológica activa)
│   │   ├── needs.py              # ✅ NeedsSystem
│   │   ├── schedule.py           # ✅ ScheduleSystem
│   │   ├── agent_core.py         # ✅ AgentCore (orquestador)
│   │   ├── psyche/
│   │   │   ├── archetypes.py     # ✅ Vectores arquetípicos
│   │   │   ├── complexes.py      # ✅ Complejos jungianos
│   │   │   ├── traits.py         # ✅ Big Five + clínico
│   │   │   ├── dreams.py         # ✅ DreamEngine
│   │   │   └── individuation.py  # ⏳ Transformación arquetípica
│   │   └── quantum/
│   │       ├── superposition.py  # ✅ Estados conductuales
│   │       ├── collapse.py       # ✅ Colapso por contexto
│   │       └── entanglement.py   # ⏳ Entrelazamiento social
│   ├── social/
│   │   ├── interaction.py        # ⏳ InteractionEngine
│   │   ├── network.py            # ⏳ SocialNetwork (NetworkX)
│   │   ├── collective_field.py   # ⏳ CollectiveField
│   │   └── mythology.py          # ⏳ MythologyEngine
│   └── simulation.py             # ✅ SimulationRunner
│
├── persistence/                   # Capa de datos
│   ├── database.py               # ✅ DatabaseManager (SQLite)
│   ├── checkpoint.py             # ✅ CheckpointManager
│   ├── write_buffer.py           # ✅ WriteBuffer
│   └── session_log.py            # ✅ SessionLog
│
├── obsidian/                      # Integración con Obsidian
│   ├── reader.py                 # ⏳ Lee frontmatter YAML
│   ├── writer.py                 # ⏳ Escribe estado del agente
│   └── sync.py                   # ⏳ Sincronización bidireccional
│
├── dashboard/                     # Visualización (Streamlit)
│   ├── app.py                    # ⏳
│   └── components/
│       ├── network_graph.py      # ⏳
│       ├── collective_field.py   # ⏳
│       └── agent_inspector.py    # ⏳
│
├── vault/                         # Vault de Obsidian
│   ├── Personas/                 # Perfil de cada agente
│   ├── Colectivo/                # Campo memético, eventos, mitología
│   └── Meta/                     # Log de simulación, arquetipos activos
│
├── data/
│   ├── db/simulation.db          # ✅ Historial SQLite
│   ├── checkpoints/              # ✅ Estados guardados
│   └── seeds/
│       └── initial_personas.yaml # ✅ 15 agentes iniciales
│
├── config/                        # ⏳ YAML de configuración
├── scripts/                       # Entry points
│   └── run_simulation.py         # ✅ Nueva sesión y reanudación
├── src/                           # Documentación de diseño (11 docs)
├── tests/                         # Suite de tests
│   ├── test_agent.py             # ✅ Tests del SimulationClock (20/20)
│   ├── test_network.py           # ✅ Tests del Núcleo 1 (31/31)
│   ├── test_quantum.py           # ✅ Tests del Núcleo 2 (38/38)
│   ├── test_persistence.py       # ✅ Tests de Persistencia (30/30)
│   └── test_simulation.py        # ✅ Tests de Fase 5 (27/27)
├── pyproject.toml                 # ✅
└── requirements.txt               # ✅
```

**Leyenda:** ✅ implementado · ⏳ pendiente

---

## Roadmap de implementación

### ✅ Fase 0 — Fundación
Configuración del proyecto, dependencias, estructura de directorios.
- `pyproject.toml`, `requirements.txt`
- Directorios: `core/time/`, `core/world/`, `core/agents/`, `core/interface/`, `persistence/`, `config/`

### ✅ Fase 1 — Reloj + Tipos de Interfaz
El eje temporal y los tipos de datos que comunican los dos núcleos.
- `SimulationClock` con handlers por prioridad, pause/resume, shutdown limpio, serialización
- `WorldAction`, `WorldSnapshot` (inmutable), `ActionResult`
- 20 tests pasando

### ✅ Fase 2 — Núcleo 1: El Mundo
El mundo físico que existe independientemente de los agentes.
- `ClimateSystem` — temperatura, precipitación, luminosidad, viento, eventos climáticos
- `TerrainGrid` — grilla hexagonal 80×60 con 12 biomas, exploración incremental
- `ResourceSystem` — recursos por hex con regeneración estacional
- `FaunaSystem` — densidad de fauna con comportamiento estacional y ruido natural
- `FireSystem` — fuego con decaimiento, efecto del clima y mantenimiento por agentes
- `WorldCore` — orquestador registrado en SimulationClock (priority=10)
- Criterio cumplido: **1 año simulado (8640 ticks) en 1.56s** (límite: 5s)

### ✅ Fase 3 — Núcleo 2: Agente mínimo
Agentes con capa biológica únicamente. Sin psicología todavía.
- `Agent` — estructura base con las 4 capas (biológica activa, resto vacío)
- `NeedsSystem` — hambre, fatiga, sed con decay y umbrales
- `ScheduleSystem` — rutinas diarias por rol (dormir, buscar alimento, interactuar)
- `AgentCore` — orquestador que consume `WorldSnapshot` y produce `WorldAction[]`
- Criterio cumplido: **15 agentes corren 30 días simulados sin morir todos**

### ✅ Fase 4 — Persistencia
Capa de datos que permite pausar y reanudar sin pérdida de estado.
- `DatabaseManager` — SQLite con tablas de snapshots, muertes, clima, escenario, sesiones
- `CheckpointManager` — guardado atómico vía os.replace(); verifica integridad al cargar
- `WriteBuffer` — batching configurable; muertes siempre inmediatas
- `SessionLog` — registra metadata de cada ejecución
- Criterio cumplido: **estado restaurado desde checkpoint coincide con el original**

### ✅ Fase 5 — Seeds + Primera simulación
Los 15 agentes beta y el entry point funcional.
- `data/seeds/initial_personas.yaml` — 15 agentes con diversidad arquetípica real (héroe, sombra, trickster, sabio, jóvenes…)
- `SimulationRunner` — orquestador que conecta clock, world, agents y persistencia; `new_session()` y `resume()`
- `scripts/run_simulation.py` — entry point con `--resume`, `--days`, `--seed`
- Criterio cumplido: **6/8 ítems del beta scope** (campo colectivo y vault en Fases 7-8)

### ✅ Fase 6 — Psicología
Las capas psicológica y cuántica de los agentes cargadas desde las semillas e integradas activamente en la simulación.
- `archetypes.py` — 12 vectores jungianos con pesos dinámicos.
- `complexes.py` — 6 complejos activables por umbral de supervivencia contextual.
- `traits.py` — Big Five (apertura, responsabilidad, extraversión, amabilidad, neuroticismo) + 9 dimensiones clínicas.
- `superposition.py` / `collapse.py` — mecánica de decisión cuántica basada en la personalidad, rasgos y contexto.
- `dreams.py` — procesamiento nocturno diario con aplicación de deltas oníricos al vector arquetípico.
- Criterio cumplido: **15 agentes cargados desde initial_personas.yaml con perfiles arquetípicos y rasgos diferenciados sobreviven 30 días de simulación sin colapsar por competencia de recursos.**

### ⏳ Fase 7 — Sistemas sociales
Las capas de interacción, red y campo colectivo.
- `InteractionEngine` — mecánica de encuentros (cooperar/conflicto/ignorar/compartir)
- `SocialNetwork` — grafo de vínculos con bond_strength (-1 → 1)
- `CollectiveField` — carga simbólica que sube, baja, cristaliza
- `MythologyEngine` — detección de umbral → proto-mito con efectos reales
- Criterio: primer proto-símbolo emergente observable antes del día 120

### ⏳ Fase 8 — Obsidian sync
El vault de Obsidian como interfaz narrativa de la simulación.
- `reader.py` — carga agentes desde frontmatter YAML al iniciar
- `writer.py` — escribe estado actualizado al final de cada día simulado
- `sync.py` — ciclo bidireccional, log de eventos significativos por agente
- Criterio: vault actualizado y legible en Obsidian tras cada sesión

### ⏳ Fase 9 — Dashboard
Visualización en tiempo real de la simulación.
- Grafo de red social interactivo
- Campo colectivo con mapa de carga simbólica
- Inspector de agente individual
- Métricas de emergencia
- Criterio: dashboard corre en paralelo a la simulación sin ralentizarla

---

## Instalación

```bash
# Clonar e instalar
pip install -e ".[dev]"

# Solo producción (sin herramientas de test)
pip install -e .

# Con dashboard
pip install -e ".[dashboard]"
```

## Tests

```bash
pytest
pytest -v              # verbose
pytest --tb=short      # traceback corto
```

---

## Stack técnico

| Componente | Tecnología |
|------------|-----------|
| Motor ABM | Mesa |
| Grafos sociales | NetworkX |
| Cálculo numérico | NumPy + SciPy |
| Vault | PyYAML (frontmatter Obsidian) |
| Persistencia | SQLite (stdlib) |
| Dashboard | Streamlit |
| Logging | Loguru |
| Tests | pytest |

---

## Documentación de diseño

Los documentos de diseño están en `src/`:

| Archivo | Contenido |
|---------|-----------|
| `00-PSYCHE_SIMULACRA_ROADMAP.md` | Roadmap completo por fases |
| `01-PSYCHE_IDEAS_IMPLEMENTACION.md` | Backlog de ideas con estimaciones |
| `02-PSYCHE_ORIGEN_INCONSCIENTE.md` | Teoría del inconsciente colectivo |
| `03-PSYCHE_BETA_SCOPE.md` | MVP: 15 agentes, criterios de éxito |
| `04-PSYCHE_SISTEMA_VIDA.md` | Nacimiento, muerte, herencia |
| `05-PSYCHE_LECCIONES_SIMULACIONES.md` | Lecciones de Sims, RimWorld, Spore, B&W2 |
| `06-PSYCHE_ESCENARIO_INICIAL.md` | Mundo hexagonal: 12 biomas |
| `07-PSYCHE_AUDITORIA_PERSISTENCIA.md` | Esquema de BD y checkpoints |
| `08-PSYCHE_EL_MUNDO.md` | Diseño completo de recursos y biomas |
| `09-PSYCHE_ARQUITECTURA_NUCLEOS.md` | WorldCore + AgentCore |
| `10-PSYCHE_SIMULATION_CLOCK.md` | SimulationClock |

---

*El inconsciente colectivo no se programa. Emerge.*
