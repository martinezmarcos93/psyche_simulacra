# PSYCHE SIMULACRA

Laboratorio computacional de emergencia del inconsciente colectivo.

Un sistema ABM (Agent-Based Model) donde 100 individuos psicológicamente complejos interactúan en un mundo físico real, generando jerarquías, tribus, símbolos, tabúes, mitos, estructuras culturales y leyendas sin que ninguno de estos fenómenos esté programado directamente.

**El inconsciente colectivo emerge — no se construye.**

---

## Concepto

Cada agente carga un vector arquetípico jungiano (12 arquetipos), rasgos dimensionales (Big Five + clínico), complejos activables, memoria episódica, sueños y vínculos sociales. Sus interacciones alimentan campos colectivos que acumulan carga simbólica. Cuando esa carga supera umbrales, cristaliza en proto-mitos con efectos conductuales reales. Las tribus que emergen desarrollan culturas materiales distintas y divergen psicológicamente a lo largo del tiempo.

El experimento busca responder:
- ¿Cuándo emerge el primer mito?
- ¿El tabú del incesto aparece antes o después del primer mito?
- ¿El héroe emerge del poder o de la narrativa?
- ¿La cooperación o la jerarquía aparece primero?
- ¿Cuánto tarda una tribu en desarrollar una identidad arquetípica diferenciable de otra?

---

## Arquitectura

```
[ Obsidian Vault ] <──> [ Motor Python ] <──> [ Dashboard Streamlit ]
  Perfiles vivos          ABM tick-based         Visualización del
  Red simbólica           Lógica psico-social     inconsciente colectivo
  Narrativa emergente     Mecánicas cuánticas
  Leyendas tribales       Tribus + Mitología
```

### Dos núcleos sincrónicos

```
SimulationClock (tick = 1 hora simulada)
        │
        ├─── priority=10 ──> WorldCore   (mundo físico)
        │                    Clima, terreno hexagonal, fauna, recursos, fuego
        │
        └─── priority=20 ──> AgentCore   (agentes)
                             Psicología, decisiones cuánticas, interacciones
                             Tribus, cultura material, narrativa LLM
```

**Ciclo de un día simulado (24 ticks):**
1. `WorldCore` actualiza clima, recursos, fauna → produce `WorldSnapshot`
2. `AgentCore` lee el snapshot → cada agente colapsa estado cuántico → interacciones zonales
3. Al final del día: clustering tribal, construcción de estructuras, síntesis narrativa
4. Persistencia a SQLite + checkpoints JSON + vault Obsidian

### Cuatro capas del agente

| Capa | Contenido |
|------|-----------|
| Biológica | hambre, fatiga, sed, salud, edad, reproducción |
| Psicológica | 12 arquetipos jungianos, 6 complejos, Big Five + 9 rasgos clínicos, sueños, memoria episódica |
| Social | vínculos (grafo NetworkX), rol, deudas simbólicas, tribu |
| Simbólica | carga de campo colectivo, proto-símbolos, herencia cultural |

---

## Sistemas implementados

### Mundo físico
- **TerrainGrid** — grilla hexagonal 80×60 con 12 biomas (bosque, pradera, río, montaña, sabana, pantano, cueva, valle fértil, costa, desierto, colinas, lago)
- **ClimateSystem** — temperatura, precipitación, luminosidad, viento, eventos climáticos estacionales
- **ResourceSystem** — recursos por hex con regeneración estacional
- **FaunaSystem** — densidad con comportamiento estacional
- **FireSystem** — propagación, decaimiento, efecto del clima

### Psicología de agentes
- **ArchetypeVector** — 12 pesos jungianos independientes (0→1): self, persona, sombra, anima/animus, héroe, sabio, trickster, madre, padre, niño divino, gobernante, rebelde
- **ComplexProfile** — 6 complejos activables por umbral contextual: inferioridad, abandono, poder, culpa, materno, trascendencia
- **TraitProfile** — Big Five + 9 dimensiones clínicas (ansiedad, impulsividad, disociación, empatía, paranoia, narcisismo, agresividad, etc.)
- **DreamGrammarEngine** — pool composicional de 5 capas (bioma × arquetipo × complejo × trauma × resonancia grupal); sueños únicos por agente; entrelazamiento nocturno entre pares con bond alto o `entangled=True`
- **LindBladChannel** — canal de decoherencia arquetípica T1/T2: relajación (decay al baseline) + represión activa (bias suprimido cuando el arquetipo supera el umbral)

### Mecánica cuántica de decisión
- **BehavioralSuperposition** — vector de probabilidades conductuales (cooperar, competir, aislar, manipular)
- **CollapseEngine** — colapso modulado por arquetipos, complejos, campo colectivo y entrelazamiento social

### Sistemas sociales
- **SocialNetwork** — grafo NetworkX con `bond_strength` ∈ [-1, 1], entrelazamiento cuántico termodinámico
- **InteractionEngine** — encuentros zonales: cooperación pura, conflicto/explotación, choque violento, manipulación
- **CollectiveField** — inconsciente colectivo global: 12 símbolos jungianos, `emotional_pressure`, `myth_pressure` (trauma sin narrativa), `confusion` epistémica; `ContextoEnunciativo` (temperatura × intencionalidad + ruido) controla cuándo y cómo colapsa un proto-mito
- **MythologyEngine** — cristalización N-dimensional probabilística: `ProtoMito` (proto-estado) gana coherencia con cada transmisión social hasta cristalizar en `MythCrystal`. 5 tipos Campbell (cosmogonía/teogonía/antropogonía/escatología/mito_moral) mapeados desde 11 pares simbólicos. Cuando los protagonistas mueren el mito se convierte en `Leyenda` de intensidad decreciente (0.998/día) que irradia efectos sobre toda la tribu

### Tribus y divergencia cultural
- **TribeManager** — clustering via `greedy_modularity_communities` (NetworkX) cada 30 días
- **CollectiveField local** — cada tribu tiene su propio inconsciente colectivo (ICL)
- **MythologyEngine local** — mitos independientes por tribu
- **Deriva por bioma** — 0.001/día de push hacia arquetipos del bioma habitado (12 biomas × afinidades)

### Cultura material
- **CultureEngine** — 4 tipos de estructuras con auras psicológicas:
  - **Tótem** — radio 2, impulsa gobernante, permanente
  - **Altar** — radio 2, reduce ansiedad, impulsa sabio/self, permanente
  - **Muralla** — radio 1, tensa a forasteros (+0.025 ansiedad), permanente
  - **Hoguera** — radio 3, mejora humor, impulsa madre, dura 30 días
- Triggers basados en complejos y arquetipos tribales dominantes
- Cooldown de 50 días entre construcciones por tribu

### Narrativa con LLM
- **OllamaDaemon** — auto-arranca `ollama serve` si el puerto 11434 no responde; verifica e instala el modelo configurado; invocado al inicio de `run_simulation.py` y `visualizer.py`
- **NarratorEngine** — daemon en background procesando cola de eventos narrativos
- 4 tipos de leyendas generadas con Ollama (llama3.2 u otro modelo local):
  - **Mito fundacional** — al formarse una nueva tribu
  - **Crónica** — cada 100 días por tribu
  - **Elegía** — por muertes con arquetipo dominante ≥ 0.70
  - **Profecía** — al cristalizar un nuevo mito
- Fallback con plantillas si Ollama no está disponible
- Deduplicación por archivo y por sesión; persistencia entre reinicios

### Métricas de emergencia científica
- **KL Divergencia** — divergencia psicológica entre culturas tribales (simétrica, pairwise)
- **VFE proxy** — entropía de Shannon del campo colectivo (incertidumbre del inconsciente)
- **IMI** — fracción de varianza arquetípica explicada por membresía tribal; R² estilo Jain-Dubes
- **MIG** — Mean Information Gain: I(z_k;v)/H(z_k) sobre 12 dimensiones arquetípicas; cuantifica cuánta información aporta la tribu sobre la psicología individual (Chen et al. 2018)
- Exportación automática a `data/metrics/emergence_series.csv` y `emergence_summary.json`
- `scripts/run_robustness.py` — suite de N ejecuciones con semillas distintas, salida JSON con KL/VFE/IMI/MIG
- `scripts/plot_emergence.py` — genera PNG con 6 gráficas automáticas (KL, MIG, IMI, VFE, MIG vs tribus, supervivencia)

### Persistencia y observabilidad
- **SQLite** (WAL) — snapshots de agentes, clima, escenario, muertes, sesiones
- **CheckpointManager** — guardado atómico JSON cada 10 días + al apagar
- **Obsidian Vault** — sincronización diaria: `vault/Personas/`, `vault/Colectivo/`, `vault/Tribus/`, `vault/Colectivo/Leyendas/`
- **Dashboard Streamlit** — red social, campo colectivo, inspector de agentes (solo lectura, corre en paralelo)
- **Visualizador Pygame** — mapa hexagonal en tiempo real con zoom y panning

---

## Escala temporal

```
1 tick      = 1 hora simulada
1 día       = 24 ticks
~1 min real = 1 día simulado (a máxima velocidad headless)
~1 hora real = ~60 días simulados

Sesión nocturna de 8h → ~480 días simulados (> 1 año de vida del grupo)
```

---

## Estructura del proyecto

```
PSYCHE SIMULACRA/
│
├── core/
│   ├── time/
│   │   └── simulation_clock.py        SimulationClock, TimePoint
│   ├── interface/
│   │   ├── world_action.py
│   │   ├── world_snapshot.py
│   │   └── action_result.py
│   ├── world/
│   │   ├── climate.py                 ClimateSystem
│   │   ├── terrain.py                 TerrainGrid hexagonal 80x60
│   │   ├── resources.py               ResourceSystem
│   │   ├── fauna.py                   FaunaSystem
│   │   ├── fire.py                    FireSystem
│   │   ├── culture_engine.py          CultureEngine (estructuras + auras)
│   │   └── world_core.py              WorldCore (orquestador)
│   ├── agents/
│   │   ├── agent.py                   Agent (4 capas)
│   │   ├── needs.py                   NeedsSystem
│   │   ├── schedule.py                ScheduleSystem
│   │   ├── agent_core.py              AgentCore (orquestador)
│   │   ├── psyche/
│   │   │   ├── archetypes.py          ArchetypeVector (12 jungianos + individuacion + MID + fidelidad)
│   │   │   ├── complexes.py           ComplexProfile (6 complejos)
│   │   │   ├── traits.py              TraitProfile (Big Five + clinico)
│   │   │   ├── dreams.py              DreamGrammarEngine (5 capas, sueños compartidos)
│   │   │   └── lindblad.py            LindBladChannel T1/T2 (decoherencia arquetipica)
│   │   └── quantum/
│   │       ├── superposition.py       BehavioralSuperposition
│   │       └── collapse.py            CollapseEngine
│   ├── social/
│   │   ├── interaction.py             InteractionEngine
│   │   ├── network.py                 SocialNetwork (NetworkX)
│   │   ├── collective_field.py        CollectiveField
│   │   ├── mythology.py               MythologyEngine
│   │   └── tribe_manager.py           TribeManager + ICL local
│   ├── narrative/
│   │   ├── config.py                  OLLAMA_BASE_URL, modelo, flags
│   │   ├── ollama_client.py           Cliente HTTP sin dependencias externas
│   │   ├── prompts.py                 4 constructores de prompt en espanol
│   │   ├── narrator.py               NarratorEngine (queue + worker en hilo)
│   │   └── daemon.py                  OllamaDaemon (auto-start + ensure_model)
│   ├── metrics/
│   │   ├── emergence.py              EmergenceMetrics (KL, VFE, IMI, MIG)
│   │   └── exporter.py               MetricsExporter (CSV + JSON)
│   └── simulation.py                 SimulationRunner (orquestador principal)
│
├── persistence/
│   ├── database.py                   DatabaseManager (SQLite WAL)
│   ├── checkpoint.py                 CheckpointManager
│   ├── write_buffer.py               WriteBuffer (batching)
│   └── session_log.py                SessionLog
│
├── obsidian/
│   ├── reader.py                     Lee frontmatter YAML
│   ├── writer.py                     Escribe Personas, Tribus, Colectivo
│   └── sync.py                       Sincronizacion bidireccional
│
├── dashboard/
│   ├── app.py                        Streamlit (solo lectura)
│   └── components/
│       ├── network_graph.py
│       ├── collective_field.py
│       └── agent_inspector.py
│
├── vault/                            Vault de Obsidian (generado en runtime)
│   ├── Personas/                     Un .md por agente
│   ├── Colectivo/                    Campo, mitologia, cultura material
│   │   └── Leyendas/                 Narrativa generada por LLM
│   ├── Tribus/                       Un .md por tribu
│   └── Meta/                         Log de simulacion
│
├── data/
│   ├── db/simulation.db              Historial SQLite completo
│   ├── checkpoints/                  Estados JSON guardados
│   ├── metrics/                      Series temporales de emergencia
│   │   ├── emergence_series.csv
│   │   └── emergence_summary.json
│   ├── archive/                      Simulaciones completadas
│   └── seeds/
│       ├── initial_personas.yaml     15 agentes beta (perfiles extremos)
│       └── 100_personas.yaml         100 agentes (generados proceduralmente)
│
├── scripts/
│   ├── run_simulation.py             Motor headless (argparse completo)
│   ├── generate_personas.py          Generador procedural de agentes YAML
│   ├── run_robustness.py             Suite de N ejecuciones paralelas
│   ├── plot_emergence.py             Reporte PNG con 6 graficas (KL, MIG, IMI, VFE, scatter, supervivencia)
│   └── visualizer.py                 Visualizador Pygame en tiempo real
│
├── tests/                            181 tests (pytest)
│   ├── test_agent.py
│   ├── test_network.py
│   ├── test_quantum.py
│   ├── test_persistence.py
│   ├── test_simulation.py
│   ├── test_social.py
│   ├── test_obsidian.py
│   └── test_metrics.py              KL divergence, VFE, IMI, exporter
│
├── src/                              Documentos de diseno originales
│   └── archive/                      Roadmaps completados
│
├── main.py                           Launcher interactivo (TUI con Rich)
├── pyproject.toml
└── requirements.txt
```

---

## Instalacion

```bash
pip install -e ".[dev]"          # desarrollo + tests
pip install -e .                 # solo produccion
pip install -e ".[dashboard]"    # con Streamlit
```

**Dependencias opcionales:**
- `pygame` — para el visualizador en tiempo real
- Ollama con `llama3.2` descargado — para narrativa LLM local
  ```bash
  ollama pull llama3.2
  ```

---

## Ejecucion

### Launcher interactivo (recomendado)

```bash
python main.py
```

Menu TUI que detecta la simulacion activa, muestra el dia y los agentes vivos.
Al iniciar nueva simulacion, **archiva automaticamente la anterior** en `data/archive/`.
Permite seleccionar entre archivos de semillas disponibles (15 o 100 agentes).

### Motor headless (maxima velocidad)

```bash
# Nueva sesion con 100 agentes, correr hasta extincion
python scripts/run_simulation.py --seeds-file data/seeds/100_personas.yaml --days 0

# Reanudar desde ultimo checkpoint
python scripts/run_simulation.py --resume --days 0

# Reanudar N dias mas
python scripts/run_simulation.py --resume --days 500
```

### Visualizador Pygame

```bash
python scripts/visualizer.py --resume --fps 10 --days 0
```

### Dashboard analitico (solo lectura, corre en paralelo)

```bash
python -m streamlit run dashboard/app.py
# Abrir http://localhost:8501
```

### Generar nuevas semillas de agentes

```bash
python scripts/generate_personas.py --n 100 --seed 42
python scripts/generate_personas.py --n 50 --seed 7 --output data/seeds/grupo_pequeno.yaml
```

### Suite de robustez

```bash
python scripts/run_robustness.py --runs 10 --days 200
# Resultados en data/metrics/robustez.json
```

---

## Tests

```bash
pytest               # 181 tests
pytest -v            # verbose
pytest --tb=short    # traceback corto
pytest tests/test_metrics.py -v   # solo metricas de emergencia
```

---

## Variables de entorno (narrativa LLM)

```bash
OLLAMA_BASE_URL=http://localhost:11434   # default
OLLAMA_MODEL=llama3.2                    # default
OLLAMA_TIMEOUT=120                       # segundos
NARRATIVE_ENABLED=1                      # 0 para desactivar
```

---

## Stack tecnico

| Componente | Tecnologia |
|------------|-----------|
| Motor ABM | SimulationClock propio (tick-based, sin Mesa) |
| Grafos sociales | NetworkX |
| Vault | PyYAML (frontmatter Obsidian) |
| Persistencia | SQLite stdlib (WAL mode) |
| Dashboard | Streamlit |
| Visualizador | Pygame |
| Launcher TUI | Rich |
| Narrativa LLM | Ollama (llama3.2, cliente stdlib sin deps externas) |
| Tests | pytest |

---

## Documentacion de diseno

Los documentos originales de diseno estan en `src/`:

| Archivo | Contenido |
|---------|-----------|
| `01-PSYCHE_IDEAS_IMPLEMENTACION.md` | Backlog de ideas con estimaciones |
| `02-PSYCHE_ORIGEN_INCONSCIENTE.md` | Teoria del inconsciente colectivo |
| `03-PSYCHE_BETA_SCOPE.md` | MVP: criterios de exito |
| `04-PSYCHE_SISTEMA_VIDA.md` | Nacimiento, muerte, herencia |
| `05-PSYCHE_LECCIONES_SIMULACIONES.md` | Lecciones de Sims, RimWorld, Spore |
| `06-PSYCHE_ESCENARIO_INICIAL.md` | Mundo hexagonal: 12 biomas |
| `07-PSYCHE_AUDITORIA_PERSISTENCIA.md` | Esquema de BD y checkpoints |
| `08-PSYCHE_EL_MUNDO.md` | Diseno completo de recursos y biomas |
| `09-PSYCHE_ARQUITECTURA_NUCLEOS.md` | WorldCore + AgentCore |
| `10-PSYCHE_SIMULATION_CLOCK.md` | SimulationClock |
| `archive/00-ROADMAP_ORIGINAL_v1_COMPLETADO.md` | Roadmap original completado |

---

*El inconsciente colectivo no se programa. Emerge.*
