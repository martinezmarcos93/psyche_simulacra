# PSYCHE SIMULACRA — Arquitectura de Nodos: Diseño y Estrategia de Transición

> **Rama:** `evolution`
> **Estado:** Documento de arquitectura. Sin implementación.
> **Fecha:** 2026-05-25
>
> Este documento describe la transición de PSYCHE SIMULACRA desde una aplicación
> monolítica multi-terminal hacia una plataforma distribuida basada en nodos y eventos.
> Nada de lo que aquí se describe debe implementarse sin autorización explícita.

---

## 0. Doctrinas Arquitectónicas y Decisiones Confirmadas

> Estas doctrinas son el núcleo filosófico del sistema.
> Toda decisión técnica futura debe evaluarse contra ellas.
> Violar una doctrina requiere revisión explícita de este documento, no silencio.

---

### Doctrina A — Runtime Primacy

> **El runtime es la realidad canónica del sistema.**
> **Toda visualización, narrativa o análisis es derivada.**

El runtime contiene el estado verdadero de la simulación. La UI, el dashboard, el narrator
y cualquier observer son lectores de ese estado — nunca fuentes de él. Ningún componente
de visualización debe tomar decisiones que afecten el estado interno del runtime.

**Implicación práctica:** si la UI y el runtime difieren, el runtime tiene razón.
La UI se actualiza; el runtime no se corrige para que la UI "tenga sentido".

---

### Doctrina B — Observer Independence

> **La simulación debe continuar existiendo aunque todos los observers desaparezcan.**

Una civilización simulada que solo existe mientras alguien la mira no es una civilización —
es una performance. El runtime debe ser capaz de correr indefinidamente en modo headless,
sin browser abierto, sin render activo, sin narrativa generada. Los observers se conectan
y desconectan. La simulación no los espera ni los necesita.

**Implicación práctica:** el runtime nunca llama a la UI. La UI llama al runtime.
Cualquier dependencia en la dirección contraria es un error arquitectónico.

---

### Doctrina C — Emergence over Control

> **El usuario observa, interpreta y analiza. No dirige la civilización.**

PSYCHE SIMULACRA no es un city builder, un god game, un RTS ni un sandbox editor.
Es un sistema de observación de emergencia civilizacional autónoma. La interfaz es
**epistemológica**, no instrumental. El usuario accede al estado emergente para comprenderlo,
no para modificarlo.

**Implicación práctica:** toda feature de UI que permita manipulación directa del mundo
es una deriva conceptual. Las únicas acciones del usuario sobre el sistema son:
iniciar, pausar, detener, observar, e inspeccionar.

---

### ⚠ Riesgo Filosófico Principal

> El mayor riesgo de esta migración no es técnico.
> **Es transformar accidentalmente PSYCHE SIMULACRA en una herramienta de control
> interactivo en lugar de un sistema de emergencia autónoma.**

Un mapa interactivo con clicks invita a añadir edición. Un inspector de agentes invita
a añadir comandos. Una UI rica invita a añadir controles. Cada uno de esos pasos,
tomado aisladamente, parece razonable. Tomados juntos, convierten el proyecto en otra
cosa. La Doctrina C existe para hacer esa deriva visible antes de que ocurra.

---

### Decisiones Arquitectónicas Confirmadas

**Decisión 1 — El mapa hex será interactivo desde v1, exclusivamente como interfaz de observación.**

| Permitido | Prohibido |
|---|---|
| Click en hex → información contextual | Mover agentes manualmente |
| Click en agente → inspector | Editar terreno |
| Hover → nombre tribu, temperatura, actividad | Spawn de entidades |
| Overlays simbólicos y analíticos | Comandos god-mode |
| Filtros y navegación espacial | Gameplay de cualquier tipo |

Consecuencia técnica: v1 = SVG interactivo. v2 = Canvas/WebGL si el rendimiento lo exige.
El diseño debe asumir esa migración desde el inicio — sin acoplar la lógica de interacción
al renderer SVG específico.

---

**Decisión 2 — El runtime soportará múltiples observers simultáneos desde el diseño inicial.**

Aunque en v1 solo haya un browser local, la arquitectura asume N observers. El
`SnapshotPipeline` se modela como broadcast pub/sub (`snapshot_subscribers[]`), no como
conexión singular a una UI. Snapshots: broadcast, stateless, desacoplados.

Casos futuros habilitados por esta decisión: dos browsers sobre la misma simulación,
panel analítico separado del mapa, observer remoto vía LAN, modo director para narrativa,
streaming de civilizaciones, replay histórico conectado al mismo pipeline.

---

**Decisión 3 — El modo headless es permanente y de primera clase.**

`python main.py --headless` (o `--runtime-only`) no es un fallback ni un modo legacy.
Es una propiedad fundamental. El runtime nunca depende de la UI. La UI depende del runtime.
Nunca al revés. (Ver Doctrinas A y B.)

---

**Decisión 4 — Streamlit coexistirá temporalmente como herramienta arqueológica.**

Durante la transición:
- **NiceGUI** = observación viva, runtime, mapa, tiempo real
- **Streamlit** = laboratorio histórico, minería de datos, arqueología civilizacional, análisis postmortem

En Fase 7+: Streamlit deja el launch principal pero permanece como
`streamlit run tools/historical_analysis.py`. No migrar analytics históricos apresuradamente.

---

**Decisión 5 — El core permanece tick-driven. El EventBus es la frontera, no el reemplazo.**

El loop determinista `SimulationClock → WorldCore → AgentCore → Persistence` es inamovible.
El EventBus **no** reemplaza el clock, **no** convierte el sistema en reactivo completo.
Es únicamente: frontera de desacoplamiento, mecanismo de observación, canal de difusión.

Razones: los procesos de PSYCHE SIMULACRA son continuos (no esporádicos), el determinismo
es imprescindible para Roadmap 5, y la conversión a event-time requeriría reescribir los
cores — exactamente lo que la migración busca evitar. Si en el futuro se necesita escala
civilizacional masiva, DES puede ser una optimización de performance, no una decisión
arquitectónica urgente.

---

## 1. Diagnóstico Arquitectónico Actual

### 1.1 Lo que existe

El sistema tiene actualmente **7 modos de operación** en `main.py`:

| Modo | Qué hace | Procesos que lanza |
|---|---|---|
| Terminal | Simulación sin UI, velocidad máxima | ninguno adicional |
| Pygame | Visualización hex en tiempo real | subprocess `visualizer.py` |
| Dashboard | Analytics histórico | subprocess `streamlit run app.py` |
| Nueva simulación | Init desde YAML + narrativa LLM | Ollama daemon + narrator thread |
| Reanudar | Carga checkpoint + terminal | Ollama daemon + narrator thread |
| Liminal Host | Servidor WebSocket + ngrok + Pygame | subprocess `liminal_server/main.py` |
| Liminal Join | Conecta a servidor remoto | ninguno adicional |

### 1.2 Topología actual de procesos

```
Usuario (teclado)
       │
   main.py (proceso principal)
       │
       ├─── SimulationRunner
       │         │
       │         ├─ SimulationClock (loop bloqueante)
       │         │       ├─ WorldCore.on_tick/on_day    [priority 10]
       │         │       ├─ AgentCore.on_tick/on_day    [priority 20]
       │         │       └─ Persistence._persist_day    [priority 30]
       │         │
       │         ├─ NarratorEngine (daemon thread)
       │         │       └─ Cola → OllamaDaemon → vault/*.md
       │         │
       │         └─ SQLite (WAL mode, multi-thread)
       │
       ├─── subprocess: visualizer.py
       │         └─ Pygame (main thread) + SimulationRunner (daemon thread)
       │              [duplica el runner — lee mismo checkpoint]
       │
       ├─── subprocess: streamlit run app.py
       │         └─ Lee SQLite directamente
       │
       ├─── subprocess: liminal_server/main.py
       │         ├─ asyncio loop (WebSocket server)
       │         └─ Pygame (main thread, mapa Liminal)
       │
       └─── proceso detached: ollama serve
```

### 1.3 Qué ya está bien desacoplado

Antes de listar problemas, es importante reconocer lo que ya funciona correctamente
y que debe **preservarse intacto**:

- **WorldAction / WorldSnapshot** — contrato limpio entre mundo y agentes. Es la
  abstracción correcta y no debe tocarse.
- **NarratorEngine** — ya es asíncrono por cola de eventos. Es el proto-event-bus del sistema.
- **Dashboard Streamlit** — ya es un observador puro (solo lee SQLite, no toca simulación).
- **SimulationClock** — ya tiene sistema de registro de handlers por prioridad. Es un
  proto-event-bus de tiempo, el leverage point más importante de la migración.
- **Checkpoint system** — escrituras atómicas, formato JSON portátil. No necesita cambiar.
- **Liminal WebSocket** — ya tiene broadcast y protocolo versionado. Prefigura el event bus.

---

## 2. Problemas Estructurales Actuales

### P1 — Sin orquestador central (el más grave)
`main.py` es un menú interactivo, no un gestor de ciclo de vida. Lanza subprocesos sin
monitorearlos, sin saber si fallaron, sin poder reiniciarlos. Si Ollama cae, nadie se entera.
Si el servidor Liminal crashea, la simulación sigue corriendo sin saber que el canal murió.

### P2 — UI y simulación acopladas structuralmente
`visualizer.py` instancia su propia copia de `SimulationRunner` en un thread daemon.
Eso significa que hay **dos instancias** del sistema corriendo contra el mismo SQLite cuando
el usuario abre la vista Pygame — una en main.py y otra en visualizer.py. Ambas leen y
escriben checkpoints. Eso es una condición de carrera latente.

### P3 — Sin event bus interno
El `SimulationClock` tiene handlers por prioridad, pero emite llamadas directas a objetos
concretos, no eventos desacoplados. Si querés que la UI sepa que un mito cristalizó, tenés
que añadir una llamada directa al handler del clock. No hay forma de suscribirse desde fuera
sin tocar el interior del runner.

### P4 — Sin streaming de estado
La única forma de que un consumidor externo vea el estado actual de la simulación es
(a) leer SQLite directamente como hace el dashboard, o (b) duplicar el runner como hace
Pygame. No hay un canal de estado serializable en tiempo real.

### P5 — Servicios manuales sin health check
Ollama, el servidor Liminal, y el dashboard son procesos que el usuario levanta manualmente
en terminales separadas, sin que nadie verifique si están vivos, en qué estado están, o si
necesitan reiniciarse.

### P6 — Estado del runtime disperso
El estado "¿qué está corriendo ahora mismo?" vive implícitamente en variables locales de
`main.py`, en el estado del proceso del clock, en el thread del narrator. No hay un objeto
único que responda `runtime.get_state()`.

### P7 — Sin headless mode formal
La simulación puede correr sin UI en modo terminal, pero eso es un modo entre 7, no una
arquitectura. El runtime no tiene una interfaz que permita a la UI conectarse y desconectarse
sin afectar la simulación.

---

## 3. Arquitectura Objetivo

### 3.1 Principio fundamental

> La UI no es el centro del sistema. El Runtime lo es.
> La UI es un suscriptor más del event bus — igual que el narrador, igual que el recorder.

### 3.2 Topología objetivo

```
python main.py
       │
       ▼
  PsycheRuntime  ←─── único punto de entrada y control
       │
       ├─── ServiceManager
       │       ├─ OllamaService      [health: running|stopped|error]
       │       ├─ LiminalService     [health: running|stopped|error]
       │       └─ SimulationService  [health: running|paused|stopped|error]
       │
       ├─── EventBus (pub/sub interno)
       │       ├─ emit(event)
       │       └─ subscribe(type, handler)
       │
       ├─── SnapshotPipeline
       │       ├─ Genera WorldSnapshot serializable cada N ticks
       │       └─ Distribuye a todos los suscriptores registrados
       │
       ├─── SimulationRunner  [sin cambios internos]
       │       ├─ SimulationClock → emite a EventBus en lugar de handlers directos
       │       ├─ WorldCore
       │       ├─ AgentCore
       │       └─ Persistence
       │
       ├─── NarratorEngine    [ahora suscriptor del EventBus]
       │
       └─── Observers (suscriptores externos)
               ├─ UI (NiceGUI)        ← consumidor de snapshots + eventos
               ├─ Recorder           ← persiste eventos seleccionados
               ├─ Analytics          ← computa métricas sobre eventos
               └─ LiminalBridge      ← reenvía eventos relevantes al servidor Liminal
```

### 3.3 Separación Runtime / Visualización

```
┌─────────────────────────────────────────────────────┐
│                   PSYCHE RUNTIME                    │
│                                                     │
│  ServiceManager + EventBus + SnapshotPipeline       │
│  SimulationRunner + NarratorEngine + Persistence    │
│                                                     │
│  Puede correr HEADLESS (sin UI)                     │
│  Expone: WebSocket interno + estado serializable    │
└─────────────────┬───────────────────────────────────┘
                  │  eventos + snapshots (WebSocket / in-process)
                  ▼
┌─────────────────────────────────────────────────────┐
│                CAPA DE VISUALIZACIÓN                │
│                                                     │
│  NiceGUI UI                                         │
│  ├─ Panel de control (start/stop/pause)             │
│  ├─ Mapa hex en tiempo real                         │
│  ├─ Dashboard de métricas                           │
│  ├─ Inspector de agentes                            │
│  └─ Monitor de salud de servicios                   │
│                                                     │
│  Puede conectarse/desconectarse sin afectar runtime │
└─────────────────────────────────────────────────────┘
```

---

## 4. Diseño del Runtime

### 4.1 PsycheRuntime — el orquestador central

```python
# Diseño conceptual — NO implementar

class PsycheRuntime:
    """
    Único punto de entrada. Gestiona ciclo de vida de todos los servicios.
    No debe saber nada de UI. La UI se conecta a él.
    """

    # ── Control de servicios ──────────────────────────────────────
    def start_simulation(self, mode: Literal["new", "resume"]) -> None: ...
    def pause_simulation(self) -> None: ...
    def resume_simulation(self) -> None: ...
    def stop_simulation(self) -> None: ...

    def launch_ollama(self) -> ServiceHandle: ...
    def stop_ollama(self) -> None: ...

    def launch_liminal_server(self) -> ServiceHandle: ...
    def stop_liminal_server(self) -> None: ...

    # ── Estado observable ─────────────────────────────────────────
    def get_runtime_state(self) -> RuntimeState: ...

    # ── Event bus ─────────────────────────────────────────────────
    def subscribe(self, event_type: str, handler: Callable) -> SubscriptionHandle: ...
    def unsubscribe(self, handle: SubscriptionHandle) -> None: ...

    # ── Snapshot streaming ────────────────────────────────────────
    def get_current_snapshot(self) -> WorldSnapshot: ...
    def stream_snapshots(self, consumer: SnapshotConsumer) -> None: ...
```

### 4.2 RuntimeState — el estado observable

```python
@dataclass
class RuntimeState:
    simulation: Literal["stopped", "running", "paused", "error"]
    ollama:     Literal["stopped", "starting", "running", "error"]
    liminal:    Literal["stopped", "starting", "running", "error"]
    dia_simulado:    int
    agentes_vivos:   int
    tribus_activas:  int
    ultimo_evento:   str
    timestamp_real:  datetime
    sim_session_id:  str | None
```

### 4.3 ServiceManager — ciclo de vida de procesos

El `ServiceManager` es responsable de:
- Lanzar cada servicio como subproceso gestionado (no `subprocess.Popen` suelto)
- Monitorear health de cada servicio con heartbeat configurable
- Reintentar automáticamente si el servicio cae (con backoff exponencial, max 3 reintentos)
- Exponer `health_state` observable al EventBus
- Hacer shutdown ordenado (primero Narrator drain, luego checkpoint, luego servicios)

**Orden de startup:**
```
1. OllamaService.start()  →  espera hasta que /api/version responde
2. SimulationService.start()
3. LiminalService.start()   (opcional, solo si el usuario lo activa)
4. UI.connect()             (siempre último — se conecta al runtime ya caliente)
```

**Orden de shutdown:**
```
1. Pause simulation clock
2. Narrator.drain(timeout=30s)
3. Checkpoint final
4. LiminalService.stop()
5. SimulationService.stop()
6. OllamaService.stop()
7. UI.disconnect()
```

---

## 5. Diseño del Event Bus

### 5.1 Principios

- **Síncrono primero, asíncrono si se justifica**: los handlers corren en el thread del
  emisor por defecto. Los handlers lentos (narrator, UI) usan cola interna.
- **No bloquea el loop de simulación**: handlers de UI y narrator son asíncronos con
  cola bounded. Si la cola se llena, el evento se descarta (no se bloquea la simulación).
- **Tipado**: cada evento tiene un tipo fuerte, no dict libre.
- **Prioridades heredadas del clock**: el bus respeta el orden de prioridad ya establecido.
- **Replay opcional**: los eventos pueden persisirse para replay futuro (no en v1).

### 5.2 Catálogo de eventos

```python
# Eventos de mundo
WorldTickEvent(tick: int, timepoint: TimePoint)
WorldDayEvent(dia: int, season: str, climate: ClimateState)
WorldSeasonChangeEvent(old_season: str, new_season: str, dia: int)
ResourceDepletedEvent(hex_coord: tuple, resource_type: str, dia: int)
FireSpreadEvent(from_hex: tuple, to_hex: tuple, dia: int)
CatastropheEvent(tipo: str, severity: float, affected_hexes: list, dia: int)

# Eventos de agentes
AgentBornEvent(agent_id: str, nombre: str, tribe_id: str, dia: int, parents: tuple)
AgentDiedEvent(agent_id: str, nombre: str, tribe_id: str, causa: str, dia: int)
AgentActionEvent(agent_id: str, action_type: str, hex_coord: tuple, tick: int)
AgentDreamEvent(agent_id: str, archetype: str, symbol: str, dia: int)
AgentTraumaEvent(agent_id: str, trauma_type: str, intensity: float, dia: int)

# Eventos sociales
TribeFormedEvent(tribe_id: str, nombre: str, founder_ids: list, dia: int)
TribeCollapsedEvent(tribe_id: str, nombre: str, dia: int, causa: str)
SchismEvent(parent_tribe: str, new_tribe: str, dia: int, cause_agent_id: str)
BondFormedEvent(agent_a: str, agent_b: str, strength: float, dia: int)

# Eventos culturales
MythCrystallizedEvent(tribe_id: str, myth_tipo: str, archetype_pair: tuple, dia: int)
DeityEmergedEvent(tribe_id: str, deity_nombre: str, archetype: str, dia: int)
KnowledgeDiscoveredEvent(agent_id: str, knowledge: str, tribe_id: str, dia: int)
KnowledgeExtinctEvent(knowledge: str, dia: int)
SacredObjectCreatedEvent(obj_nombre: str, tipo: str, creador_id: str, dia: int)
SocialRoleAssignedEvent(tipo: str, portador_id: str, tribe_id: str, dia: int)
NarrativeGeneratedEvent(tribe_id: str, tipo: str, texto_preview: str, dia: int)

# Eventos Liminal
LiminalAgentEnteredEvent(agent_id: str, from_sim: str, dia: int)
LiminalAgentReturnedEvent(agent_id: str, to_sim: str, dia: int)
LiminalConnectionEvent(sim_id: str, connected: bool)

# Eventos de runtime
ServiceHealthEvent(service: str, state: str, detail: str)
CheckpointSavedEvent(dia: int, filepath: str)
SnapshotEmittedEvent(tick: int, snapshot_size_bytes: int)
```

### 5.3 Suscripciones de cada módulo

```
SimulationClock  →  emite:  WorldTickEvent, WorldDayEvent, WorldSeasonChangeEvent
WorldCore        →  emite:  ResourceDepletedEvent, FireSpreadEvent, CatastropheEvent
AgentCore        →  emite:  AgentBornEvent, AgentDiedEvent, AgentActionEvent, AgentDreamEvent,
                             MythCrystallizedEvent, DeityEmergedEvent, KnowledgeDiscoveredEvent,
                             SacredObjectCreatedEvent, SocialRoleAssignedEvent

NarratorEngine   →  suscribe: MythCrystallizedEvent, AgentDiedEvent, TribeFormedEvent, WorldDayEvent
Recorder         →  suscribe: todo (filtra por tipo configurado)
SnapshotPipeline →  suscribe: WorldTickEvent (genera snapshot cada N ticks)
UI               →  suscribe: todo vía WebSocket interno (snapshot + eventos visuales)
LiminalBridge    →  suscribe: AgentBornEvent, AgentDiedEvent, MythCrystallizedEvent
```

### 5.4 Formato de eventos en tránsito

```json
{
  "event_id":   "evt_00042891",
  "event_type": "MythCrystallized",
  "timestamp":  1748200800.123,
  "dia":        1950,
  "tick":       46800,
  "priority":   20,
  "payload": {
    "tribe_id":      "tribe_thalia",
    "myth_tipo":     "fundacional",
    "archetype_pair": ["heroe", "sombra"],
    "nombre_mito":   "El Guardián de la Oscuridad"
  }
}
```

### 5.5 Prioridades del bus

| Prioridad | Quién usa | Cuándo corre |
|---|---|---|
| 10 | WorldCore | Síncrono, en el tick, antes que agentes |
| 20 | AgentCore | Síncrono, en el tick, después del mundo |
| 30 | Persistence, Recorder | Síncrono, al final del tick |
| 50 | NarratorEngine | Asíncrono — cola con buffer 500 eventos |
| 80 | SnapshotPipeline | Asíncrono — cada N ticks |
| 100 | UI WebSocket | Asíncrono — cola con buffer 200 snapshots |

---

## 6. Diseño del Snapshot Pipeline

### 6.1 Qué es un snapshot

Un snapshot es una **fotografía serializable completa del estado del mundo** en un tick
dado. No es el checkpoint (que es para persistencia de largo plazo). Es para consumo en
tiempo real por la UI y analytics.

### 6.2 Estructura del snapshot

```json
{
  "meta": {
    "tick":        18211,
    "dia":         759,
    "season":      "verano",
    "timestamp":   1748200800.123,
    "sim_id":      "sim_abc123"
  },
  "world": {
    "climate":   { "temperatura": 28.4, "precipitacion": 0.1 },
    "fires":     [{"hex": [12, 34], "intensity": 0.8}],
    "resources": { "totales": 4200, "por_tipo": {} }
  },
  "agents": [
    {
      "id": "agent_001", "nombre": "Adras",
      "hex": [10, 22], "tribe_id": "tribe_bios",
      "archetype": "heroe", "vivo": true,
      "needs_critical": false
    }
  ],
  "tribes": [
    {
      "id": "tribe_bios", "nombre": "Bios",
      "agentes": 12, "icl_cohesion": 0.74,
      "mitos_activos": 3, "deidades": 1
    }
  ],
  "collective_field": {
    "tribe_bios": {
      "myth_pressure": 0.62,
      "emotional_pressure": 0.41,
      "dominant_archetype": "heroe"
    }
  },
  "events_since_last": [
    { "type": "MythCrystallized", "tribe_id": "tribe_bios", "dia": 759 }
  ],
  "metrics": {
    "emergence_index": 0.71,
    "cultural_diversity": 0.58,
    "mig_score": 0.44
  }
}
```

### 6.3 Delta vs Full snapshots

| Tipo | Frecuencia | Tamaño | Uso |
|---|---|---|---|
| **Full snapshot** | Cada 24 ticks (1 día) | ~50–200 KB | UI al reconectar, checkpoint de observación |
| **Delta snapshot** | Cada tick (opcional) | ~2–10 KB | UI en tiempo real — solo lo que cambió |
| **Metric snapshot** | Cada 100 días | ~5 KB | Analytics histórico, reemplaza lectura directa de SQLite |

### 6.4 Frecuencia y performance

Con 80×60 = 4800 hexágonos y hasta 150 agentes, un full snapshot JSON es ~80 KB
serializado. A 1 snapshot/día (24 ticks), el overhead es mínimo. La UI puede pedir
full snapshots al reconectarse y recibir deltas en tiempo real.

**Regla:** el SnapshotPipeline **nunca bloquea el clock**. Corre en un thread separado
con cola. Si la cola se llena (UI lenta), descarta snapshots intermedios — nunca la
simulación espera a la UI.

---

## 7. Modelo de Procesos e Hilos

### 7.1 Topología objetivo de threads

```
Proceso principal (python main.py)
│
├─ Thread: SimulationClock (loop de tick — hilo principal de simulación)
│       ├─ WorldCore.on_tick/on_day     [síncrono, priority 10]
│       ├─ AgentCore.on_tick/on_day     [síncrono, priority 20]
│       ├─ EventBus.emit()             [síncrono para priority ≤ 30]
│       └─ Persistence._persist_day    [síncrono, priority 30]
│
├─ Thread: NarratorEngine daemon
│       └─ Cola → OllamaClient → vault/*.md
│
├─ Thread: SnapshotPipeline
│       └─ Serializa estado → cola de WebSocket interno
│
├─ Thread: ServiceManager heartbeat
│       ├─ Ping Ollama cada 30s
│       ├─ Ping Liminal cada 15s
│       └─ Emite ServiceHealthEvent si cambia estado
│
└─ Thread: UI server (NiceGUI / FastAPI)
        ├─ Sirve la interfaz web
        ├─ WebSocket: push snapshots + eventos a browser
        └─ Recibe comandos del usuario (start/pause/stop)

Subproceso separado (gestionado por ServiceManager):
└─ ollama serve          [monitorizado por heartbeat]

Subproceso separado (gestionado por ServiceManager, opcional):
└─ liminal_server/main.py  [monitorizado por heartbeat]
```

### 7.2 Comunicación entre threads

| Canal | Tipo | Dirección | Bloqueante |
|---|---|---|---|
| SimulationClock → EventBus | Llamada directa | Síncrono | Sí (priority ≤ 30) |
| EventBus → NarratorEngine | `queue.Queue` | Asíncrono | No |
| EventBus → SnapshotPipeline | `queue.Queue` | Asíncrono | No |
| SnapshotPipeline → UI | `asyncio.Queue` | Asíncrono | No |
| UI → PsycheRuntime | Llamada directa (thread-safe) | Síncrono | Sí (comandos simples) |
| ServiceManager → EventBus | Llamada directa | Síncrono | Sí |

### 7.3 Por qué NO multiprocessing para el runtime

El `AgentCore` y `WorldCore` comparten estado en memoria (WorldSnapshot, agentes dict,
collective fields). Mover a multiprocessing requeriría serializar ese estado en cada
tick — overhead de ~50ms por tick en un mundo de 150 agentes, inaceptable.

**Threading es suficiente** porque el cuello de botella es CPU (el clock loop), no I/O.
El GIL libera durante las operaciones de I/O (SQLite writes, Ollama HTTP, WebSocket push),
que son exactamente los threads auxiliares. El clock loop corre solo en su thread.

**Multiprocessing sí para procesos externos:**
- `ollama serve` → subproceso separado (ya es así)
- `liminal_server` → subproceso separado (ya es así)
- Ambos gestionados por ServiceManager con health checks

---

## 8. Estrategia de Migración Incremental

La migración se hace en **fases reversibles**. En cada fase, `main` permanece intacto.
Todo ocurre en la rama `evolution`. Cada fase termina con tests de regresión.

### Fase 0 — Preparación (sin tocar simulación)
**Objetivo:** crear la estructura base sin romper nada.

- Crear `core/runtime/__init__.py` con `PsycheRuntime` stub
- Crear `core/runtime/event_bus.py` con `EventBus` básico (pub/sub síncrono)
- Crear `core/runtime/service_manager.py` con `ServiceManager` stub
- Crear `core/runtime/runtime_state.py` con `RuntimeState` dataclass
- **NO** tocar `SimulationClock`, `AgentCore`, `WorldCore`
- Tests: el sistema existente sigue funcionando idéntico

### Fase 1 — EventBus conectado al clock
**Objetivo:** el clock emite eventos al bus. Handlers existentes no cambian.

- `SimulationClock.emit_tick()` → también `event_bus.emit(WorldTickEvent(...))`
- `SimulationClock.emit_day()` → también `event_bus.emit(WorldDayEvent(...))`
- Los handlers priority 10/20/30 siguen siendo llamadas directas (no cambian)
- El EventBus es un canal paralelo, no reemplaza los handlers todavía
- Verificar: los eventos llegan al bus. La simulación no cambia su comportamiento.

### Fase 2 — NarratorEngine migra a EventBus
**Objetivo:** el narrator deja de recibir llamadas directas, suscribe al bus.

- `NarratorEngine` suscribe: `MythCrystallizedEvent`, `AgentDiedEvent`, `TribeFormedEvent`
- `SimulationRunner._queue_narrative_events()` se elimina — el narrator reacciona solo
- Verificar: las crónicas se siguen generando igual. El vault sigue recibiendo archivos.

### Fase 3 — SnapshotPipeline
**Objetivo:** la simulación emite snapshots serializables. La UI ya puede consumirlos.

- Crear `core/runtime/snapshot_pipeline.py`
- El pipeline suscribe `WorldDayEvent` y produce snapshots JSON
- Los snapshots van a un buffer en memoria (aún no a WebSocket)
- `PsycheRuntime.get_current_snapshot()` retorna el último snapshot
- Verificar: los snapshots son correctos. No hay overhead medible en el clock.

### Fase 4 — ServiceManager operativo
**Objetivo:** `python main.py` lanza y monitorea todos los servicios.

- `ServiceManager.launch_ollama()` reemplaza el código ad-hoc de `main.py`
- `ServiceManager.launch_liminal()` reemplaza el subprocess manual
- Health checks activos: el runtime sabe si Ollama está vivo
- `RuntimeState` siempre refleja el estado real
- El menú interactivo de `main.py` delega a `PsycheRuntime` en lugar de hacer todo inline
- Verificar: los 7 modos existentes siguen funcionando. El menú sigue apareciendo.

### Fase 5 — UI desacoplada (NiceGUI)
**Objetivo:** reemplazar el menú interactivo de terminal por interfaz unificada.

- Instalar y configurar NiceGUI
- El browser se abre automáticamente al `python main.py`
- La UI consume `PsycheRuntime.stream_snapshots()` vía WebSocket interno
- Mapa hex: primera versión como SVG estático actualizado por snapshot
- Dashboard: charts Plotly alimentados por métricas del snapshot
- Panel de control: botones que llaman a `runtime.start_simulation()`, etc.
- El menú terminal queda como fallback (`main.py --headless`)
- Verificar: la simulación no se ve afectada por si la UI está abierta o cerrada.

### Fase 6 — Mapa hex en tiempo real
**Objetivo:** el mapa hex se actualiza tick a tick, no solo día a día.

- Delta snapshots: solo posiciones de agentes + cambios de hex
- El mapa en NiceGUI usa WebSocket para recibir deltas a alta frecuencia
- Primera versión: SVG dinámico. Segunda versión: Canvas HTML5 si hace falta performance.
- Inspector de agentes: click en hex → ver agentes en ese hex → click en agente → stats

### Fase 7 — Liminal integrado en la UI
**Objetivo:** el servidor Liminal aparece como un panel dentro de la UI unificada.

- La UI muestra estado del servidor Liminal (conectado/desconectado, sims conectadas)
- Botón "Activar servidor Liminal" dentro de la UI
- Panel lateral con eventos Liminal en tiempo real
- El mapa Pygame de Liminal queda deprecado — la UI unificada lo absorbe

---

## 9. Evaluación Tecnológica de UI

Evaluación desde arquitectura distribuida, no desde estética.

### 9.1 NiceGUI ✅ Recomendado

**Paradigma:** Python puro → servidor web local → browser como frontend

**Por qué es el candidato natural:**

| Criterio | Evaluación |
|---|---|
| Solo Python | ✅ Sin JavaScript manual |
| WebSocket nativo | ✅ `ui.timer()` + `ui.notify()` para real-time |
| Headless-capable | ✅ La UI es un suscriptor opcional del runtime |
| Plotly nativo | ✅ `ui.plotly()` — el dashboard migra fácil |
| Mapa hex | ⚠️ Necesita reescribirse como SVG o `ui.scene()` (3D) |
| Multi-observer | ✅ Varios browsers pueden conectarse al mismo runtime |
| Compatibilidad Liminal | ✅ El server Liminal puede exponer otro endpoint en el mismo host |
| Multiplayer futuro | ✅ Cada sim puede conectar su propia pestaña de browser |
| Proceso único | ✅ NiceGUI corre en el mismo proceso que el runtime |
| Auto-abre browser | ✅ `ui.run(show=True)` |

**Debilidades:**
- El mapa hex Pygame necesita reescribirse. La lógica de renderizado hex existe y es
  reutilizable; solo cambia el renderer (de `pygame.draw.polygon` a SVG path o canvas).
- Performance del mapa: SVG con 4800 hexágonos + 150 agentes puede ser lento. Solución:
  Canvas HTML5 con JavaScript mínimo para el render del mapa (solo el mapa, no todo el UI).

**Arquitectura con NiceGUI:**
```
python main.py
    │
    ├─ PsycheRuntime.start()
    │       └─ [simulación corriendo en background thread]
    │
    └─ NiceGUI.run(host="localhost", port=8080)
            ├─ Consume PsycheRuntime.stream_snapshots()
            ├─ Renderiza mapa hex (SVG/Canvas)
            ├─ Renderiza métricas (Plotly)
            └─ Envía comandos a PsycheRuntime
```

---

### 9.2 DearPyGui — Descartado para este proyecto

**Por qué no:**
- Immediate mode: excelente para rendimiento, pero la UI es una ventana nativa no
  compartible. Múltiples observers (multiplayer futuro, Liminal) requieren múltiples
  ventanas del mismo proceso — que DearPyGui no soporta.
- Sin soporte WebSocket out-of-the-box: habría que añadir FastAPI o similar de todas
  formas, perdiendo la ventaja de "proceso único".
- El ecosystem de componentes es menos maduro que NiceGUI para dashboard científico.
- No escala bien hacia la visión de plataforma distribuida.

**Cuándo sería mejor:** si el proyecto fuera puramente local, single-user, sin visión
de multiplayer ni acceso remoto. No es el caso de PSYCHE SIMULACRA.

---

### 9.3 FastAPI + Canvas HTML5 — Alternativa para el mapa

**No como UI principal, sí como solución parcial para el mapa hex:**

El mayor cuello de botella de NiceGUI es el mapa hex con 4800 hexágonos actualizándose
en tiempo real. Si el SVG resulta lento, la solución es un Canvas HTML5 renderizado por
JavaScript mínimo — no un framework completo, solo el mapa.

**Arquitectura híbrida viable:**
```
NiceGUI (dashboard + controles + inspector)
    │
    └─ iframe o panel embebido: Canvas HTTP/WebSocket
            ├─ FastAPI micro-endpoint: /api/world/stream (WebSocket)
            └─ JavaScript mínimo: dibuja hex map en Canvas 60fps
```

Esto permite que NiceGUI maneje todo excepto el mapa, y el mapa sea un componente
web independiente de alto rendimiento. La separación es limpia porque el mapa es
solo visualización — no necesita comunicación bidireccional compleja.

---

### 9.4 Streamlit — Descartado para runtime

Streamlit tiene un modelo de ejecución basado en reruns completos del script por
cada interacción. Eso lo hace incompatible con un loop de simulación de larga duración.
**Puede mantenerse como herramienta de análisis histórico** (lo que ya hace bien),
pero no puede ser la UI unificada.

---

### 9.5 Decisión recomendada

```
Interfaz principal:   NiceGUI
Mapa hex (v1):        SVG via NiceGUI (aceptable hasta ~50 agentes simultáneos en pantalla)
Mapa hex (v2):        Canvas HTML5 embebido si v1 resulta lento
Dashboard métricas:   Plotly via NiceGUI (migración directa desde Streamlit)
Runtime API:          PsycheRuntime interno (no FastAPI público en v1)
Analytics histórico:  Streamlit existente puede mantenerse como herramienta separada
```

---

## 10. Riesgos y Tradeoffs

### R1 — Reescritura del mapa hex [RIESGO ALTO]
El mapa Pygame tiene lógica de renderizado hex (coordenadas axiales, colores por bioma,
zoom/pan) que funciona bien. Reescribirla en SVG/Canvas implica riesgo de regresión
visual y tiempo de desarrollo significativo.

**Mitigación:** mantener Pygame como fallback durante la transición. El modo `--headless`
+ Pygame separado sigue siendo opción hasta que NiceGUI tenga paridad visual.

### R2 — Thread safety del EventBus [RIESGO MEDIO]
Si el EventBus es accedido desde múltiples threads (clock thread + ServiceManager thread),
hay riesgo de condiciones de carrera en las listas de suscriptores.

**Mitigación:** el EventBus usa `threading.Lock` en las operaciones de suscripción.
Los handlers priority ≤ 30 solo son llamados desde el clock thread (síncrono).
Los handlers priority ≥ 50 reciben eventos vía `queue.Queue` (thread-safe por diseño).

### R3 — Performance del snapshot [RIESGO BAJO-MEDIO]
Serializar 150 agentes + 4800 hexágonos a JSON cada día puede añadir latencia si la
simulación corre en modo acelerado (terminal mode, máxima velocidad).

**Mitigación:** el SnapshotPipeline es un suscriptor asíncrono — no bloquea el clock.
En modo headless (sin UI conectada), los snapshots se descartan después de generarse
(solo se mantiene el último en buffer). La serialización ocurre en su propio thread.

### R4 — Complejidad de ServiceManager [RIESGO MEDIO]
Gestionar ciclo de vida de subprocesos con health checks y reintentos es más complejo
que el `subprocess.Popen` actual. El riesgo es introducir bugs en el startup/shutdown.

**Mitigación:** fases de migración graduales. El ServiceManager empieza como wrapper
simple del código existente, y añade sophistication incrementalmente.

### R5 — Compatibilidad con Roadmap 5 [RIESGO BAJO]
Los sistemas del Roadmap 5 (memoria transgeneracional, infancia, construcciones) añaden
estado nuevo al `AgentCore` y `WorldCore`. Si la migración arquitectónica toca esos
mismos módulos, puede haber conflictos.

**Mitigación:** la arquitectura de nodos NO toca los internos de `AgentCore`/`WorldCore`.
Solo añade listeners externos y un pipeline de serialización. Roadmap 5 puede implementarse
en paralelo sin conflicto.

### R6 — El servidor Liminal corre con su propio Pygame [RIESGO BAJO]
`liminal_server/main.py` lanza su propio Pygame para visualizar el mapa Liminal.
Al integrar todo en NiceGUI, ese Pygame queda obsoleto pero sigue funcionando.

**Mitigación:** el servidor Liminal sigue como subproceso independiente en todas las
fases de migración. Su visualización se absorbe en NiceGUI solo en Fase 7 (última).

---

## 11. Roadmap de Transición

```
ESTADO ACTUAL
main.py (menú terminal) + 3+ terminales manuales

FASE 0: Estructura base de runtime
   [sin cambios visibles — solo nueva estructura de archivos]

FASE 1: EventBus conectado al clock
   [sin cambios visibles — canal paralelo]

FASE 2: NarratorEngine migra a EventBus
   [el vault sigue recibiendo archivos — comportamiento idéntico]

FASE 3: SnapshotPipeline activo
   [primeros snapshots JSON disponibles — sin UI todavía]

FASE 4: ServiceManager operativo
   [python main.py lanza Ollama automáticamente — menú terminal persiste]

FASE 5: NiceGUI — primer launch
   [python main.py abre browser — menú terminal persiste como --headless]

FASE 6: Mapa hex en tiempo real
   [la visualización Pygame queda deprecada pero disponible]

FASE 7: Liminal integrado en UI
   [plataforma unificada completa]

ESTADO FINAL
python main.py → browser con runtime completo, mapa hex, dashboard, Liminal — todo
```

**Duración estimada por fase:** variable. Ninguna fase debe tomar más de 1 sesión
de trabajo si se respeta la regla de "no tocar lo que funciona".

---

## 12. Qué NO hacer

- **No reescribir AgentCore ni WorldCore** para esta migración. Son el núcleo conceptual
  y están probados. Solo añadir la capa de eventos encima, no dentro.
- **No eliminar el modo terminal** (headless). Es esencial para simulaciones de larga
  duración sin UI, para CI/CD, y para debugging.
- **No convertir el runtime en FastAPI público** en v1. El runtime es interno; la UI
  es un suscriptor local. Si en el futuro se quiere acceso remoto al runtime, se añade
  entonces.
- **No hacer el EventBus asíncrono completo** desde el inicio. El clock loop es síncrono
  y debe seguir siéndolo. Solo los handlers de UI y narrator son asíncronos.
- **No implementar replay de eventos** en v1. Es tentador pero añade complejidad al
  persistence layer sin beneficio inmediato.
- **No mover el Streamlit dashboard existente** hasta que NiceGUI tenga paridad de
  features. Streamlit puede coexistir — solo quitar el menú que lo lanza manualmente.
- **No empezar por la UI**. Empezar por el Runtime (Fases 0–4) y luego conectar la UI
  a un runtime ya estable. Empezar por la UI y construir el runtime alrededor de ella
  es el error más común y produce acoplamiento al revés.

---

## 13. Qué Mantener Intacto

**No tocar en ninguna fase:**

- `core/agents/agent_core.py` — internos del loop de simulación
- `core/agents/agent.py` — modelo de agente individual
- `core/world/world_core.py` — WorldAction/WorldSnapshot/WorldCore
- `core/interface/` — el contrato mundo↔agente
- `core/time/simulation_clock.py` — solo añadir emit de eventos, no cambiar el loop
- `core/social/mythology.py` — MythologyEngine
- `core/social/collective_field.py` — CollectiveField
- `persistence/` — checkpoint, database, write_buffer
- `liminal_server/` — todo el servidor Liminal permanece independiente hasta Fase 7
- `data/` — estructura de datos, checkpoints existentes, SQLite
- `vault/` — el vault Obsidian no es responsabilidad de la migración arquitectónica

**Preservar funcionalidad en todo momento:**
- Las simulaciones en curso deben poder reanudarse desde checkpoints
- Los checkpoints existentes deben ser compatibles hacia adelante
- El vault Obsidian debe seguir recibiendo crónicas

---

## 14. Compatibilidad con Roadmap 5

El Roadmap 5 añade sistemas al `AgentCore` y `WorldCore` (memoria transgeneracional,
infancia, construcciones, fauna, sustancias). La arquitectura de nodos no interfiere
con eso porque:

1. **Los sistemas nuevos del R5 emiten eventos al bus** — no necesitan saber quién suscribe.
   `StructureBuiltEvent`, `TransgenerationalMemoryTransmittedEvent`, etc. se añaden al
   catálogo de eventos. La UI los recibe automáticamente.

2. **Los snapshots se extienden** — cuando R5 añade estructuras físicas al mundo, el
   snapshot añade el campo `"structures": [...]`. El pipeline de serialización es extensible.

3. **Ningún sistema del R5 requiere acceso directo a la UI** — todos operan sobre el
   estado interno de los cores. El event bus es la frontera.

**Orden recomendado:**

```
Ahora:
   R5-A1 (memoria transgeneracional) → primera implementación R5

   En paralelo (rama evolution):
   Fase 0-1-2 (runtime base + event bus)

   Cuando R5-A1 esté completo:
   Añadir TransgenerationalMemoryEvent al catálogo → lo hereda la UI automáticamente

   Cuando Fase 4-5 estén completas:
   Continuar con R5-A2, R5-B3, etc. — cada nuevo sistema añade eventos, no cambia la arquitectura
```

Los dos roadmaps pueden avanzar **en ramas separadas** que se mergean periódicamente
sin conflicto estructural. El núcleo de la simulación (donde vive R5) no se toca en la
migración arquitectónica (donde vive `evolution`).

---

## Apéndice A — Estructura de archivos nueva

```
core/
  runtime/
    __init__.py
    psyche_runtime.py       ← PsycheRuntime (orquestador)
    event_bus.py            ← EventBus (pub/sub)
    event_types.py          ← catálogo de dataclasses de eventos
    service_manager.py      ← ciclo de vida de servicios externos
    runtime_state.py        ← RuntimeState dataclass
    snapshot_pipeline.py    ← generación y distribución de snapshots
    snapshot_schema.py      ← estructura del snapshot serializable

ui/
  __init__.py
  nicegui_app.py            ← aplicación NiceGUI
  panels/
    hex_map.py              ← panel del mapa hexagonal
    dashboard.py            ← panel de métricas
    agent_inspector.py      ← panel de inspección de agentes
    control_panel.py        ← panel de control del runtime
    liminal_monitor.py      ← panel de estado Liminal
  components/
    hex_renderer.py         ← lógica de renderizado SVG del hexágono
    metrics_charts.py       ← charts Plotly reutilizables
```

---

## Apéndice B — Preguntas abiertas antes de implementar

1. **¿El mapa hex necesita ser interactivo en v1?** (click en hex → inspector de agentes)
   Si sí → Canvas + WebSocket. Si no → SVG actualizable suficiente.

2. **¿Querés que múltiples browsers puedan conectarse al mismo runtime simultáneamente?**
   Si sí → el SnapshotPipeline debe soportar múltiples suscriptores WebSocket (NiceGUI ya
   lo hace naturalmente).

3. **¿El modo headless (`python main.py --headless`) es necesario desde Fase 5?**
   Recomendado sí — para mantener la opción de correr la simulación en servidor sin pantalla.

4. **¿Querés que el dashboard Streamlit existente siga disponible en paralelo durante
   la transición?** (acceso vía `localhost:8501` mientras NiceGUI está en `localhost:8080`)

---

*Última actualización: 2026-05-25*
*Rama: evolution*
*Estado: diseño completo — pendiente autorización para iniciar Fase 0*
