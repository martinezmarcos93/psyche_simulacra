# PSYCHE SIMULACRA — Arquitectura de Núcleos
## Núcleo 1 (Mundo) + Núcleo 2 (Agentes): Diseño Técnico

> *El mundo no espera a los agentes.  
> Los agentes viven dentro de un mundo que ya existía  
> y que seguirá existiendo cuando se vayan.*

---

## I. MODELO DE EJECUCIÓN

### Tick sincronizado — Por qué esta opción

```
CICLO DE UN TICK (1 hora simulada)
────────────────────────────────────────────────────────

  ┌─────────────────────────────────────────────────────┐
  │                  TICK N                             │
  │                                                     │
  │  1. NÚCLEO 1 — World Update                        │
  │     El mundo avanza 1 hora.                        │
  │     Clima, fauna, recursos, fuego.                  │
  │     Produce: WorldState(tick=N)                     │
  │                        │                            │
  │                        ▼                            │
  │  2. NÚCLEO 2 — Agent Update                        │
  │     Cada agente recibe WorldState(tick=N).         │
  │     Toma decisiones, interactúa, se transforma.    │
  │     Produce: lista de WorldActions                  │
  │                        │                            │
  │                        ▼                            │
  │  3. APLICAR ACCIONES AL MUNDO                      │
  │     Las acciones de los agentes modifican           │
  │     el WorldState para el tick siguiente.           │
  │     (Un agente cazó → fauna -= x)                   │
  │                        │                            │
  │                        ▼                            │
  │  4. PERSISTENCIA                                    │
  │     Write buffer + checkpoint logic                 │
  │                        │                            │
  └────────────────────────┼────────────────────────────┘
                           │
                     TICK N+1
```

**Por qué tick sincronizado y no threads paralelos:**
- Reproducibilidad total — mismos parámetros = mismo resultado
- Sin race conditions — el mundo nunca se actualiza mientras un agente lo lee
- Debuggeable — se puede pausar, inspeccionar, y reanudar en cualquier tick
- Suficientemente rápido para beta — 25 agentes × 24 ticks = 600 ops/día

---

## II. NÚCLEO 1 — EL MUNDO

### Responsabilidades exclusivas

El Núcleo 1 **no sabe que existen agentes**.
Solo sabe que hay acciones que llegaron desde afuera
y las aplica a su estado.

```python
# core/world/world_core.py

from dataclasses import dataclass, field
from typing import Optional
import numpy as np

@dataclass
class WorldCore:
    """
    Núcleo 1 — El mundo físico.
    Existe antes que los agentes.
    Existirá después que los agentes.
    No conoce la psicología — solo la física.
    """
    
    # ── ESTADO FUNDAMENTAL ───────────────────────────────────
    tick:           int = 0          # Hora absoluta desde el inicio
    dia_simulado:   int = 0          # Día simulado actual
    hora_del_dia:   int = 0          # 0–23
    año_simulado:   int = 0
    dia_del_año:    int = 0          # 0–359
    
    # ── COMPONENTES DEL MUNDO ────────────────────────────────
    climate:        'ClimateSystem'  = field(default_factory=...)
    terrain:        'TerrainGrid'    = field(default_factory=...)
    fauna:          'FaunaSystem'    = field(default_factory=...)
    resources:      'ResourceSystem' = field(default_factory=...)
    fire:           'FireSystem'     = field(default_factory=...)
    
    # ── ACCIONES PENDIENTES (vienen de Núcleo 2) ─────────────
    pending_actions: list['WorldAction'] = field(default_factory=list)
    
    def tick_update(self) -> 'WorldSnapshot':
        """
        El tick del mundo — 1 hora simulada.
        
        Orden de operaciones importa:
        1. Clima primero — afecta todo lo demás
        2. Recursos vegetales — dependen del clima
        3. Fauna — depende de recursos y clima
        4. Fuego — depende de clima y puede afectar recursos
        5. Aplicar acciones de agentes — al final del tick
        6. Calcular métricas globales
        """
        # 1. Avanzar reloj
        self._advance_clock()
        
        # 2. Actualizar clima
        climate_state = self.climate.update(self.hora_del_dia,
                                            self.dia_del_año)
        
        # 3. Actualizar recursos vegetales
        self.resources.update(climate_state, self.dia_del_año)
        
        # 4. Actualizar fauna
        self.fauna.update(climate_state, self.resources)
        
        # 5. Actualizar fuego
        self.fire.update(climate_state, self.terrain)
        
        # 6. Aplicar todas las acciones de agentes del tick anterior
        action_results = self._apply_agent_actions()
        
        # 7. Calcular estado global
        global_metrics = self._calculate_global_metrics()
        
        # 8. Producir snapshot inmutable para Núcleo 2
        snapshot = self._produce_snapshot(climate_state,
                                          global_metrics,
                                          action_results)
        
        # Limpiar acciones procesadas
        self.pending_actions.clear()
        
        return snapshot
    
    def receive_actions(self, actions: list['WorldAction']):
        """
        Recibe las acciones de los agentes.
        Las encola — se aplican al FINAL del tick actual.
        
        Esto garantiza que todos los agentes ven el mismo
        estado del mundo cuando toman sus decisiones.
        """
        self.pending_actions.extend(actions)
    
    def _apply_agent_actions(self) -> list['ActionResult']:
        """
        Aplica las acciones de todos los agentes al mundo.
        Las acciones están ya ordenadas por prioridad.
        """
        results = []
        for action in self.pending_actions:
            result = self._apply_single_action(action)
            results.append(result)
        return results
    
    def _apply_single_action(self, action: 'WorldAction') -> 'ActionResult':
        match action.type:
            case "cazar":
                return self.fauna.reduce(
                    action.coord, action.species, action.amount
                )
            case "recolectar":
                return self.resources.reduce(
                    action.coord, action.resource, action.amount
                )
            case "encender_fuego":
                return self.fire.ignite(action.coord, action.agent_id)
            case "construir_refugio":
                return self.terrain.add_structure(action.coord, "refugio")
            case "explorar":
                return self.terrain.reveal(action.coord, action.agent_id)
            case "cruzar_rio":
                return self.terrain.attempt_crossing(
                    action.coord_from, action.coord_to, action.agent_id
                )
    
    def _produce_snapshot(self, climate, metrics, action_results) -> 'WorldSnapshot':
        """
        Snapshot inmutable del estado del mundo.
        Los agentes leen esto — nunca el estado vivo directamente.
        """
        return WorldSnapshot(
            tick=self.tick,
            dia=self.dia_simulado,
            hora=self.hora_del_dia,
            estacion=self.climate.estacion_actual,
            
            # Clima
            temperatura=climate.temperatura,
            precipitacion=climate.precipitacion,
            luminosidad=climate.luminosidad,
            viento=climate.viento,
            evento_climatico=climate.evento_activo,
            
            # Recursos por zona (solo zonas conocidas por el grupo)
            recursos_disponibles=self.resources.get_available_summary(),
            
            # Fauna
            fauna_densidad=self.fauna.get_density_map(),
            
            # Fuego
            fuego_activo=self.fire.is_active,
            fuego_coord=self.fire.location,
            fuego_intensidad=self.fire.intensity,
            
            # Métricas globales
            carrying_capacity=metrics.carrying_capacity,
            resource_pressure=metrics.resource_pressure,
            
            # Resultados de las acciones del tick anterior
            # (el agente sabe si su caza tuvo éxito)
            action_results=action_results,
        )
```

### El Sistema Climático — ClimateSystem

```python
# core/world/climate.py

class ClimateSystem:
    """
    Sistema climático autónomo.
    Funciona sin importar si hay agentes o no.
    """
    
    def __init__(self, seed: int = 42):
        self.rng = np.random.default_rng(seed)  # Reproducible
        self.estacion_actual = "primavera"
        self.dia_en_estacion = 0
        
        # Estado climático actual
        self.temperatura   = 16.0
        self.precipitacion = 0.45
        self.luminosidad   = 0.70
        self.viento        = 0.30
        self.humedad       = 0.55
        
        # Tendencia actual (clima no cambia bruscamente)
        self._tendencia_temp  = 0.0
        self._tendencia_lluvia = 0.0
        
        # Evento activo
        self.evento_activo: Optional[str] = None
        self.evento_duracion: int = 0
    
    def update(self, hora: int, dia_del_año: int) -> 'ClimateState':
        
        # 1. Determinar estación
        self._update_estacion(dia_del_año)
        
        # 2. Calcular valores base de la estación
        base = ESTACIONES[self.estacion_actual]
        temp_min, temp_max = base["temperatura"]
        
        # 3. Ciclo diario de temperatura (más frío de noche)
        ciclo_diario = np.sin((hora - 6) * np.pi / 12)  # Pico a las 12h
        temp_base = temp_min + (temp_max - temp_min) * (ciclo_diario * 0.5 + 0.5)
        
        # 4. Ruido estocástico con tendencia (el clima no es random puro)
        self._tendencia_temp += self.rng.normal(0, 0.5)
        self._tendencia_temp *= 0.95  # Decay — la tendencia se suaviza
        
        self.temperatura = np.clip(
            temp_base + self._tendencia_temp,
            temp_min - 10, temp_max + 10
        )
        
        # 5. Precipitación
        prob_lluvia = base["precipitacion"]
        if self.evento_activo == "tormenta":
            prob_lluvia = min(1.0, prob_lluvia * 2.5)
        
        self.precipitacion = np.clip(
            self.rng.normal(prob_lluvia, 0.15), 0, 1
        )
        
        # 6. Luminosidad (noche/día + nubes)
        es_dia = 6 <= hora <= 20
        self.luminosidad = (0.90 - self.precipitacion * 0.60) if es_dia else 0.05
        
        # 7. Eventos climáticos (baja probabilidad por hora)
        self._check_weather_events()
        
        return ClimateState(
            temperatura=self.temperatura,
            precipitacion=self.precipitacion,
            luminosidad=self.luminosidad,
            viento=self.viento,
            humedad=self.humedad,
            estacion=self.estacion_actual,
            evento_activo=self.evento_activo,
            # Modificadores calculados para los agentes
            mood_modifier=self._calculate_mood_modifier(),
            productivity_modifier=self._calculate_productivity_modifier(),
            survival_risk=self._calculate_survival_risk(),
        )
    
    def _calculate_mood_modifier(self) -> float:
        """
        Cómo el clima afecta el humor base de los agentes.
        El Núcleo 1 calcula esto — el Núcleo 2 lo aplica.
        """
        mod = 0.0
        
        # Temperatura óptima: 15–22°C
        if 15 <= self.temperatura <= 22:
            mod += 0.15
        elif self.temperatura < 0 or self.temperatura > 38:
            mod -= 0.30
        elif self.temperatura < 5 or self.temperatura > 33:
            mod -= 0.15
        
        # Lluvia moderada: neutro. Lluvia intensa: negativo.
        if self.precipitacion > 0.70:
            mod -= 0.20
        elif 0.20 < self.precipitacion < 0.50:
            mod += 0.05
        
        # Luminosidad — el sol importa
        mod += (self.luminosidad - 0.50) * 0.20
        
        return np.clip(mod, -0.50, 0.30)
```

---

## III. NÚCLEO 2 — LOS AGENTES

### Responsabilidades exclusivas

El Núcleo 2 **no modifica el mundo directamente**.
Produce `WorldAction` que le entrega al Núcleo 1.
El mundo decide si la acción es posible y qué efecto tiene.

```python
# core/agents/agent_core.py

class AgentCore:
    """
    Núcleo 2 — El sistema de agentes.
    Recibe el estado del mundo, procesa agentes, produce acciones.
    """
    
    def __init__(self, agents: list['Agent']):
        self.agents = {a.id: a for a in agents}
        self.interaction_engine = InteractionEngine()
        self.collective_field   = CollectiveField()
        self.social_network     = SocialNetwork(agents)
        self.mythology_engine   = MythologyEngine()
        self.dream_engine       = DreamEngine()
        self.tech_engine        = TechnologyEngine()
    
    def tick_update(self,
                    world_snapshot: 'WorldSnapshot',
                    action_results: list['ActionResult']) -> list['WorldAction']:
        """
        El tick de los agentes — 1 hora simulada.
        
        Recibe el estado del mundo (qué hay afuera).
        Produce acciones (qué quieren hacer en el mundo).
        Todo lo psicológico ocurre internamente — no sale al mundo.
        """
        world_actions = []
        
        # 1. Actualizar el campo colectivo con los resultados del tick anterior
        self.collective_field.update_from_results(action_results)
        
        # 2. Propagar el estado del mundo a todos los agentes
        # (clima, amenazas, recursos disponibles)
        self._broadcast_world_state(world_snapshot)
        
        # 3. Determinar qué hace cada agente en esta hora
        # (en orden aleatorio para evitar ventajas sistemáticas)
        agent_order = self._get_random_order()
        
        for agent_id in agent_order:
            agent = self.agents[agent_id]
            
            if not agent.is_alive:
                continue
            
            # El agente decide su acción para esta hora
            action = self._process_agent_tick(agent, world_snapshot)
            
            if action:
                world_actions.append(action)
        
        # 4. Procesar interacciones entre agentes en la misma zona
        interaction_events = self.interaction_engine.process_zone_interactions(
            self.agents, world_snapshot
        )
        
        # 5. Actualizar campo colectivo con las interacciones
        self.collective_field.absorb_interactions(interaction_events)
        
        # 6. Verificar si hay cristalización de mitos
        self.mythology_engine.check_crystallization(self.collective_field)
        
        # 7. Procesar sueños (solo en horas de sueño)
        if world_snapshot.hora in range(0, 6):
            self._process_dreams(world_snapshot)
        
        # 8. Verificar condiciones de tecnología
        tech_actions = self.tech_engine.check_discoveries(
            self.agents, world_snapshot, self.collective_field
        )
        world_actions.extend(tech_actions)
        
        # 9. Verificar nacimientos y muertes
        self._check_vital_events(world_snapshot)
        
        return world_actions
    
    def _process_agent_tick(self,
                            agent: 'Agent',
                            world: 'WorldSnapshot') -> Optional['WorldAction']:
        """
        Un agente procesa su hora.
        
        Orden interno del agente:
        1. Actualizar estado biológico (hambre, fatiga, sed)
        2. Verificar override de supervivencia
        3. Determinar actividad según schedule
        4. Generar acción para el mundo (si aplica)
        5. Actualizar estado psicológico
        """
        # 1. Biología primero
        agent.update_biological_state(world)
        
        # 2. Override de supervivencia
        if agent.needs.survival_override_active():
            return agent.execute_survival_action(world)
        
        # 3. Schedule normal
        scheduled_activity = agent.schedule.get_activity(world.hora)
        
        # 4. ¿El agente sigue su schedule o lo rompe?
        actual_activity = self._resolve_activity(agent, scheduled_activity, world)
        
        # 5. Ejecutar actividad y producir acción de mundo (si aplica)
        world_action = agent.execute_activity(actual_activity, world)
        
        # 6. Actualizar estado psicológico post-actividad
        agent.update_psychological_state(world, actual_activity)
        
        return world_action
```

---

## IV. LA INTERFAZ ENTRE NÚCLEOS

### WorldAction — Lo que los agentes le hacen al mundo

```python
# core/interface/world_action.py

@dataclass
class WorldAction:
    """
    Todo lo que un agente puede hacer al mundo físico.
    El Núcleo 1 decide si es posible y qué efecto tiene.
    """
    agent_id:   str
    tick:       int
    type:       str          # Ver ActionType
    coord:      tuple        # Dónde ocurre (hex q, r)
    
    # Parámetros específicos por tipo
    params:     dict = field(default_factory=dict)
    
    # Prioridad — si hay conflicto (dos agentes por el mismo recurso)
    priority:   float = 0.5

class ActionType:
    # Recursos
    CAZAR           = "cazar"
    RECOLECTAR      = "recolectar"
    PESCAR          = "pescar"
    BEBER           = "beber"
    
    # Exploración
    EXPLORAR        = "explorar"
    MOVERSE         = "moverse"
    CRUZAR_RIO      = "cruzar_rio"
    
    # Construcción
    CONSTRUIR_REFUGIO = "construir_refugio"
    MANTENER_FUEGO  = "mantener_fuego"
    
    # Tecnología
    ENCENDER_FUEGO  = "encender_fuego"
    TALLAR_PIEDRA   = "tallar_piedra"
    USAR_TECNOLOGIA = "usar_tecnologia"
    
    # Exploración de recursos ocultos
    BUSCAR_RECURSO  = "buscar_recurso"
    # El agente busca activamente — el mundo decide si encuentra
```

### WorldSnapshot — Lo que el mundo le dice a los agentes

```python
@dataclass(frozen=True)  # Inmutable — los agentes no pueden modificarlo
class WorldSnapshot:
    """
    Foto del mundo en un tick.
    Inmutable — los agentes leen esto, nunca el estado vivo.
    """
    tick:               int
    dia:                int
    hora:               int
    estacion:           str
    
    # Clima
    temperatura:        float
    precipitacion:      float
    luminosidad:        float
    viento:             float
    evento_climatico:   Optional[str]
    
    # Modificadores precalculados por el Núcleo 1
    mood_modifier:      float    # Cómo el clima afecta el humor
    productivity_mod:   float    # Cómo el clima afecta la productividad
    survival_risk:      float    # Riesgo climático base
    
    # Recursos (solo los conocidos por el grupo)
    recursos_por_hex:   dict     # {coord: {recurso: cantidad}}
    
    # Fauna
    fauna_visible:      dict     # {coord: {especie: densidad}}
    
    # Fuego
    fuego_activo:       bool
    fuego_coord:        Optional[tuple]
    fuego_intensidad:   float
    fuego_calor_bonus:  float    # Beneficio de estar cerca del fuego
    
    # Estado global
    carrying_capacity:  int
    resource_pressure:  float    # 0=abundancia, 1=crisis
    
    # Resultados del tick anterior
    # El agente sabe si su caza tuvo éxito
    action_results:     dict     # {agent_id: ActionResult}
```

### ActionResult — El mundo responde a cada acción

```python
@dataclass
class ActionResult:
    """
    El resultado de una acción — el mundo respondió.
    El agente actualiza su estado basándose en esto.
    """
    agent_id:       str
    action_type:    str
    success:        bool
    
    # Si tuvo éxito
    resource_gained:    Optional[dict] = None
    # {"carne": 0.3, "cuero": 0.1}
    
    # Si falló
    failure_reason:     Optional[str]  = None
    # "fauna_insuficiente" / "terreno_inaccesible" / "sin_tecnologia"
    
    # Efectos secundarios (siempre, éxito o no)
    world_effects:      dict = field(default_factory=dict)
    # {"fauna_small_density": -0.02, "exploration_revealed": [(40,31)]}
    
    # Información nueva descubierta
    discoveries:        list = field(default_factory=list)
    # [{"tipo": "recurso_oculto", "recurso": "miel", "coord": (41, 30)}]
```

---

## V. EL ORQUESTADOR — SimulationRunner

```python
# core/simulation_runner.py

class SimulationRunner:
    """
    El director de orquesta.
    Coordina Núcleo 1 y Núcleo 2.
    Maneja persistencia, checkpoints y ciclo de vida.
    """
    
    def __init__(self, config: 'SimulationConfig'):
        self.config  = config
        self.world   = WorldCore.from_config(config.world_config)
        self.agents  = AgentCore.from_config(config.agent_config)
        self.db      = DatabaseManager(config.db_path)
        self.checkpoint_mgr = CheckpointManager(config.checkpoint_dir)
        self.session = SessionLog.new()
        
        # Handlers de cierre seguro
        self._register_shutdown_handlers()
        
        # Estado del runner
        self.running = False
        self.tick    = 0
    
    def run(self, max_dias: Optional[int] = None):
        """
        El loop principal.
        
        Por cada tick:
        1. Mundo avanza
        2. Agentes procesan
        3. Acciones se aplican
        4. Se persiste
        """
        self.running = True
        self.session.start()
        
        target_ticks = (max_dias * 24) if max_dias else float('inf')
        
        while self.running and self.tick < target_ticks:
            self._execute_tick()
            self.tick += 1
            
            # Control de velocidad
            # El motor corre tan rápido como puede
            # El límite es el hardware, no un sleep artificial
        
        self._shutdown(reason="target_reached")
    
    def _execute_tick(self):
        """Un tick completo — el ciclo fundamental."""
        
        # ── NÚCLEO 1: El mundo avanza ────────────────────────
        world_snapshot = self.world.tick_update()
        
        # ── NÚCLEO 2: Los agentes procesan ───────────────────
        world_actions = self.agents.tick_update(
            world_snapshot=world_snapshot,
            action_results=self.world.last_action_results
        )
        
        # ── INTERFAZ: Las acciones van al mundo ──────────────
        self.world.receive_actions(world_actions)
        
        # ── PERSISTENCIA ──────────────────────────────────────
        self._persist_tick(world_snapshot, world_actions)
        
        # ── CHECKPOINT (si corresponde) ───────────────────────
        if self._should_checkpoint():
            self.checkpoint_mgr.save(self.world, self.agents,
                                     reason="auto")
    
    def _persist_tick(self, snapshot, actions):
        """
        Decide qué va a la DB en este tick.
        No todo se escribe en cada tick — ver estrategia de escritura.
        """
        dia_cambio = (self.tick % 24 == 23)  # Último tick del día
        
        # Siempre inmediato
        self.db.write_immediate(self.agents.get_critical_events())
        
        # Por tick — al buffer
        self.db.buffer_interactions(self.agents.get_tick_interactions())
        self.db.buffer_archetype_deltas(self.agents.get_archetype_changes())
        
        # Por día
        if dia_cambio:
            self.db.flush_day_buffer()
            self.db.write_agent_snapshots(self.agents.snapshot_all())
            self.db.write_world_snapshot(snapshot)
            self.db.write_climate(snapshot)
    
    def _should_checkpoint(self) -> bool:
        dia_actual = self.tick // 24
        return (
            dia_actual % 10 == 0 and  # Cada 10 días simulados
            self.tick % 24 == 0       # Al inicio del día (no a mitad)
        )
    
    def _register_shutdown_handlers(self):
        import signal, atexit
        signal.signal(signal.SIGINT,  self._graceful_shutdown)
        signal.signal(signal.SIGTERM, self._graceful_shutdown)
        atexit.register(self._emergency_save)
    
    def _graceful_shutdown(self, signum=None, frame=None):
        """Ctrl+C — tenemos tiempo."""
        self.running = False
        logger.info(f"Cerrando. Día simulado: {self.tick // 24}")
        
        self.db.flush_all_buffers()
        self.checkpoint_mgr.save(self.world, self.agents, reason="shutdown")
        self.session.close(razon="normal")
        
        sys.exit(0)
    
    def _emergency_save(self):
        """Proceso muriendo — guardar lo que se pueda."""
        try:
            self.db.flush_all_buffers(timeout=3)
            self.checkpoint_mgr.save_minimal(self.world, self.agents)
        except Exception as e:
            logger.error(f"Emergency save falló: {e}")
```

---

## VI. ESTRUCTURA DE ARCHIVOS — DEFINITIVA

```
psyche-simulacra/
│
├── core/
│   ├── __init__.py
│   │
│   ├── world/                     # NÚCLEO 1
│   │   ├── __init__.py
│   │   ├── world_core.py          # WorldCore — orquestador del mundo
│   │   ├── climate.py             # ClimateSystem
│   │   ├── terrain.py             # TerrainGrid — grilla hexagonal
│   │   ├── hexagon.py             # Hexagon — celda individual
│   │   ├── fauna.py               # FaunaSystem
│   │   ├── resources.py           # ResourceSystem
│   │   ├── fire.py                # FireSystem
│   │   └── world_dynamics.py      # Regeneración, degradación
│   │
│   ├── agents/                    # NÚCLEO 2
│   │   ├── __init__.py
│   │   ├── agent_core.py          # AgentCore — orquestador de agentes
│   │   ├── agent.py               # Agent — el agente individual
│   │   ├── needs.py               # NeedsSystem (hambre, sed, fatiga)
│   │   ├── schedule.py            # ScheduleSystem (rutinas diarias)
│   │   ├── psyche/
│   │   │   ├── archetypes.py      # Vectores arquetípicos
│   │   │   ├── complexes.py       # Complejos jungianos
│   │   │   ├── traits.py          # Rasgos dimensionales
│   │   │   ├── neural.py          # Módulos neurales
│   │   │   ├── dreams.py          # DreamEngine
│   │   │   └── individuation.py   # Motor de transformación
│   │   └── quantum/
│   │       ├── superposition.py   # Estados conductuales superpuestos
│   │       ├── collapse.py        # Colapso por interacción
│   │       └── entanglement.py    # Entrelazamiento social
│   │
│   ├── social/                    # SISTEMAS SOCIALES (entre Núcleos)
│   │   ├── __init__.py
│   │   ├── interaction.py         # InteractionEngine
│   │   ├── network.py             # SocialNetwork
│   │   ├── collective_field.py    # CollectiveField
│   │   ├── mythology.py           # MythologyEngine
│   │   └── technology.py          # TechnologyEngine
│   │
│   └── interface/                 # INTERFAZ ENTRE NÚCLEOS
│       ├── __init__.py
│       ├── world_action.py        # WorldAction, ActionType
│       ├── world_snapshot.py      # WorldSnapshot (inmutable)
│       └── action_result.py       # ActionResult
│
├── persistence/
│   ├── __init__.py
│   ├── database.py                # DatabaseManager — SQLite
│   ├── checkpoint.py              # CheckpointManager — JSON
│   ├── write_buffer.py            # WriteBuffer — batching
│   └── session_log.py             # SessionLog
│
├── config/
│   ├── world_config.yaml          # Parámetros del mundo
│   ├── agent_config.yaml          # Parámetros de agentes
│   ├── simulation_config.yaml     # Parámetros de ejecución
│   └── initial_agents/
│       ├── agent_P001.yaml        # Los 15 agentes iniciales
│       └── ...
│
├── vault/                         # Obsidian vault
│   ├── Agentes/
│   ├── Colectivo/
│   └── Meta/
│
├── data/
│   ├── simulation.db
│   ├── checkpoints/
│   └── sessions/
│
├── scripts/
│   ├── run.py                     # Entry point
│   ├── resume.py                  # Reanudar desde checkpoint
│   └── inspect.py                 # Inspeccionar estado sin correr
│
└── pyproject.toml
```

---

## VII. ORDEN DE DESARROLLO

```
SEMANA 1 — Núcleo 1 sin agentes
  [ ] TerrainGrid con 80×60 hexs
  [ ] ClimateSystem corriendo 365 días sin agentes
  [ ] ResourceSystem con regeneración
  [ ] FaunaSystem básico
  [ ] Verificar: el mundo corre 1 año en < 5 segundos

SEMANA 2 — Núcleo 2 mínimo
  [ ] Agent con capa biológica (hambre, sed, fatiga)
  [ ] ScheduleSystem básico (dormir, buscar comida)
  [ ] WorldAction + WorldSnapshot funcionando
  [ ] Verificar: 15 agentes corren 30 días sin morir todos

SEMANA 3 — Persistencia
  [ ] DatabaseManager con todas las tablas
  [ ] CheckpointManager con save/load
  [ ] Shutdown handlers
  [ ] Verificar: cerrar y reanudar es transparente

SEMANA 4 — Psicología básica
  [ ] Arquetipos y rasgos en agentes
  [ ] Interacciones simples entre agentes
  [ ] CollectiveField básico
  [ ] Primera sesión de 2 horas sin crashes
```

---

> *El Núcleo 1 no sabe que hay agentes.*  
> *El Núcleo 2 no puede tocar el mundo directamente.*  
> *La interfaz entre los dos es donde ocurre la historia.*

---

*Psyche Simulacra — Arquitectura de Núcleos v1.0*
