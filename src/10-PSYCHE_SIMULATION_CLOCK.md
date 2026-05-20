# PSYCHE SIMULACRA — El Tiempo
## SimulationClock: La Entidad que Gobierna Ambos Núcleos

> *El tiempo es único.*  
> *Lo comparten el mundo y los agentes.*  
> *Si el tiempo frena, todo frena.*  
> *Si el tiempo avanza, todo avanza junto.*

---

## I. FILOSOFÍA DEL TIEMPO

El tiempo no pertenece al Núcleo 1 ni al Núcleo 2.
Es una entidad independiente que los gobierna a ambos.

```
                    ┌─────────────────────┐
                    │   SimulationClock   │
                    │                     │
                    │  tick: 14,423       │
                    │  dia:  600          │
                    │  hora: 23           │
                    │  estado: CORRIENDO  │
                    └──────────┬──────────┘
                               │
                 ┌─────────────┴─────────────┐
                 │                           │
                 ▼                           ▼
        ┌────────────────┐         ┌────────────────┐
        │   NÚCLEO 1     │         │   NÚCLEO 2     │
        │   El Mundo     │         │   Los Agentes  │
        │                │         │                │
        │  Escucha       │         │  Escucha       │
        │  ON_TICK       │         │  ON_TICK       │
        │  ON_DAY        │         │  ON_DAY        │
        │  ON_PAUSE      │         │  ON_PAUSE      │
        └────────────────┘         └────────────────┘

Cuando el clock emite ON_TICK:
  → Núcleo 1 actualiza el mundo
  → Núcleo 2 procesa los agentes
  En ese orden. Síncronos. Sin excepciones.

Cuando el clock emite ON_PAUSE:
  → Núcleo 1 congela su estado
  → Núcleo 2 congela su estado
  Los dos en el mismo instante.
```

---

## II. SIMULATIONCLOCK — La Implementación

```python
# core/time/simulation_clock.py

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, Optional
import time


class ClockState(Enum):
    STOPPED  = auto()   # No iniciado todavía
    RUNNING  = auto()   # Corriendo normalmente
    PAUSED   = auto()   # Pausado (checkpoint, inspección)
    SHUTDOWN = auto()   # Cerrando — último tick en curso


@dataclass
class TimePoint:
    """
    Un momento en el tiempo de la simulación.
    Inmutable — representa un instante, no un estado mutable.
    """
    tick:           int     # Hora absoluta desde el inicio (0, 1, 2, ...)
    dia_simulado:   int     # Día absoluto (0, 1, 2, ...)
    hora_del_dia:   int     # 0–23
    dia_del_año:    int     # 0–359
    año_simulado:   int     # 0, 1, 2, ...
    estacion:       str     # "primavera" / "verano" / "otoño" / "invierno"
    es_amanecer:    bool    # hora == 6
    es_mediodia:    bool    # hora == 12
    es_anochecer:   bool    # hora == 20
    es_medianoche:  bool    # hora == 0
    es_inicio_dia:  bool    # hora == 0 — inicio del nuevo día
    es_fin_dia:     bool    # hora == 23 — último tick del día

    # Tiempo real transcurrido (para métricas de performance)
    timestamp_real: float   # time.monotonic() al emitir este tick

    @property
    def es_noche(self) -> bool:
        return self.hora_del_dia < 6 or self.hora_del_dia >= 21

    @property
    def es_dia(self) -> bool:
        return 6 <= self.hora_del_dia < 21

    @property
    def semana_simulada(self) -> int:
        return self.dia_simulado // 7

    @property
    def mes_simulado(self) -> int:
        return self.dia_simulado // 30

    def __str__(self) -> str:
        return (f"Año {self.año_simulado}, {self.estacion}, "
                f"Día {self.dia_del_año}, {self.hora_del_dia:02d}:00h "
                f"[tick {self.tick}]")


class SimulationClock:
    """
    El tiempo único de la simulación.
    
    Gobierna a ambos núcleos.
    No pertenece a ninguno.
    
    Cuando frena, todo frena.
    Cuando avanza, todo avanza.
    """

    # Escala de tiempo
    TICKS_PER_DAY:   int = 24    # 1 tick = 1 hora simulada
    DAYS_PER_SEASON: int = 90    # 4 estaciones × 90 días = 360 días/año
    DAYS_PER_YEAR:   int = 360
    SEASONS: list[str] = ["primavera", "verano", "otoño", "invierno"]

    def __init__(self, start_dia: int = 0, start_hora: int = 6):
        # Estado del reloj
        self._tick:  int = start_dia * self.TICKS_PER_DAY + start_hora
        self._state: ClockState = ClockState.STOPPED

        # Suscriptores — quiénes escuchan el tick
        # Orden garantizado: Núcleo 1 siempre antes que Núcleo 2
        self._on_tick_handlers:     list[tuple[int, Callable]] = []
        self._on_day_handlers:      list[tuple[int, Callable]] = []
        self._on_season_handlers:   list[tuple[int, Callable]] = []
        self._on_pause_handlers:    list[Callable] = []
        self._on_resume_handlers:   list[Callable] = []
        self._on_shutdown_handlers: list[Callable] = []

        # Métricas de performance
        self._ticks_this_session:   int   = 0
        self._session_start_real:   float = 0.0
        self._last_tick_real:       float = 0.0

        # Control de velocidad
        # None = tan rápido como pueda (default para simulación)
        # float = segundos mínimos entre ticks (para modo observación)
        self._min_tick_interval:    Optional[float] = None

    # ── SUSCRIPCIÓN DE HANDLERS ───────────────────────────────

    def on_tick(self, handler: Callable, priority: int = 50):
        """
        Registrar un handler que se llama en cada tick.
        Priority: menor número = se llama antes.
        Núcleo 1 usa priority=10, Núcleo 2 usa priority=20.
        """
        self._on_tick_handlers.append((priority, handler))
        self._on_tick_handlers.sort(key=lambda x: x[0])

    def on_day(self, handler: Callable, priority: int = 50):
        """Handler llamado al inicio de cada nuevo día (hora==0)."""
        self._on_day_handlers.append((priority, handler))
        self._on_day_handlers.sort(key=lambda x: x[0])

    def on_season_change(self, handler: Callable, priority: int = 50):
        """Handler llamado cuando cambia la estación."""
        self._on_season_handlers.append((priority, handler))
        self._on_season_handlers.sort(key=lambda x: x[0])

    def on_pause(self, handler: Callable):
        """Handler llamado cuando el reloj se pausa."""
        self._on_pause_handlers.append(handler)

    def on_resume(self, handler: Callable):
        """Handler llamado cuando el reloj se reanuda."""
        self._on_resume_handlers.append(handler)

    def on_shutdown(self, handler: Callable):
        """Handler llamado en el shutdown — último en ejecutarse."""
        self._on_shutdown_handlers.append(handler)

    # ── CONTROL DEL RELOJ ────────────────────────────────────

    def start(self):
        """Iniciar el reloj."""
        assert self._state == ClockState.STOPPED, \
            "El reloj ya está corriendo"
        self._state = ClockState.RUNNING
        self._session_start_real = time.monotonic()
        self._run_loop()

    def pause(self, reason: str = "manual"):
        """
        Pausar el reloj.
        Ambos núcleos se congelan en el siguiente tick completo.
        """
        if self._state == ClockState.RUNNING:
            self._state = ClockState.PAUSED
            for handler in self._on_pause_handlers:
                handler(self.now, reason)

    def resume(self):
        """Reanudar el reloj pausado."""
        if self._state == ClockState.PAUSED:
            self._state = ClockState.RUNNING
            for handler in self._on_resume_handlers:
                handler(self.now)
            self._run_loop()

    def shutdown(self):
        """
        Apagado ordenado.
        Completa el tick actual y notifica a todos los handlers.
        """
        self._state = ClockState.SHUTDOWN
        # Los handlers de shutdown se llaman después del último tick
        for handler in self._on_shutdown_handlers:
            handler(self.now)
        self._state = ClockState.STOPPED

    def set_speed(self, seconds_per_tick: Optional[float] = None):
        """
        Controlar velocidad de la simulación.
        None = máxima velocidad (para simulación normal)
        0.1  = 10 ticks por segundo (para observación)
        1.0  = tiempo real muy lento (para debugging)
        """
        self._min_tick_interval = seconds_per_tick

    # ── LOOP PRINCIPAL ────────────────────────────────────────

    def _run_loop(self):
        """
        El loop de tiempo.
        Cada iteración = 1 tick = 1 hora simulada.
        """
        while self._state == ClockState.RUNNING:
            tick_start = time.monotonic()

            # Producir el TimePoint actual
            tp = self._make_timepoint()

            # Emitir el tick a todos los suscriptores
            # EN ORDEN DE PRIORIDAD — Núcleo 1 antes que Núcleo 2
            self._emit_tick(tp)

            # Emitir eventos especiales si corresponde
            if tp.es_inicio_dia:
                self._emit_day(tp)

            self._check_season_change(tp)

            # Avanzar el tick
            self._tick += 1
            self._ticks_this_session += 1
            self._last_tick_real = time.monotonic()

            # Control de velocidad (si está activado)
            if self._min_tick_interval:
                elapsed = time.monotonic() - tick_start
                if elapsed < self._min_tick_interval:
                    time.sleep(self._min_tick_interval - elapsed)

    def _emit_tick(self, tp: TimePoint):
        """
        Emite el tick a todos los handlers en orden de prioridad.
        Si el reloj pasa a PAUSED o SHUTDOWN durante la emisión,
        completa el tick actual antes de detenerse.
        """
        for priority, handler in self._on_tick_handlers:
            handler(tp)
            # Si alguien pausó el reloj durante el tick,
            # completamos este tick igualmente — no hay ticks parciales.

    def _emit_day(self, tp: TimePoint):
        for priority, handler in self._on_day_handlers:
            handler(tp)

    def _check_season_change(self, tp: TimePoint):
        if tp.dia_del_año % self.DAYS_PER_SEASON == 0 and tp.hora_del_dia == 0:
            if tp.dia_del_año > 0:  # No emitir en el día 0
                for priority, handler in self._on_season_handlers:
                    handler(tp)

    # ── ESTADO ACTUAL ─────────────────────────────────────────

    @property
    def now(self) -> TimePoint:
        return self._make_timepoint()

    @property
    def state(self) -> ClockState:
        return self._state

    @property
    def is_running(self) -> bool:
        return self._state == ClockState.RUNNING

    def _make_timepoint(self) -> TimePoint:
        hora       = self._tick % self.TICKS_PER_DAY
        dia        = self._tick // self.TICKS_PER_DAY
        dia_del_año = dia % self.DAYS_PER_YEAR
        año        = dia // self.DAYS_PER_YEAR
        estacion   = self.SEASONS[dia_del_año // self.DAYS_PER_SEASON]

        return TimePoint(
            tick           = self._tick,
            dia_simulado   = dia,
            hora_del_dia   = hora,
            dia_del_año    = dia_del_año,
            año_simulado   = año,
            estacion       = estacion,
            es_amanecer    = hora == 6,
            es_mediodia    = hora == 12,
            es_anochecer   = hora == 20,
            es_medianoche  = hora == 0,
            es_inicio_dia  = hora == 0,
            es_fin_dia     = hora == 23,
            timestamp_real = time.monotonic(),
        )

    # ── SERIALIZACIÓN (para checkpoint) ──────────────────────

    def to_dict(self) -> dict:
        """Serializar para checkpoint."""
        return {
            "tick":         self._tick,
            "dia_simulado": self._tick // self.TICKS_PER_DAY,
            "hora_del_dia": self._tick % self.TICKS_PER_DAY,
            "año_simulado": (self._tick // self.TICKS_PER_DAY) // self.DAYS_PER_YEAR,
            "estacion":     self.now.estacion,
            "ticks_total":  self._ticks_this_session,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'SimulationClock':
        """Restaurar desde checkpoint."""
        clock = cls(
            start_dia  = data["dia_simulado"],
            start_hora = data["hora_del_dia"],
        )
        return clock

    # ── MÉTRICAS ──────────────────────────────────────────────

    def get_performance_metrics(self) -> dict:
        """¿Qué tan rápido está corriendo la simulación?"""
        if self._ticks_this_session == 0:
            return {}

        elapsed_real = time.monotonic() - self._session_start_real
        ticks_per_second = self._ticks_this_session / elapsed_real
        dias_per_minute  = (ticks_per_second * 60) / self.TICKS_PER_DAY

        return {
            "ticks_per_second":     round(ticks_per_second, 1),
            "dias_simulados_por_minuto_real": round(dias_per_minute, 1),
            "dias_simulados_por_hora_real":   round(dias_per_minute * 60, 0),
            "ticks_esta_sesion":    self._ticks_this_session,
            "tiempo_real_segundos": round(elapsed_real, 1),
        }
```

---

## III. CÓMO SE CONECTA TODO

### El SimulationRunner con el Clock

```python
# core/simulation_runner.py

class SimulationRunner:

    def __init__(self, config):
        # El clock se crea primero — es el eje de todo
        self.clock  = SimulationClock()
        self.world  = WorldCore(config.world)
        self.agents = AgentCore(config.agents)
        self.db     = DatabaseManager(config.db_path)
        self.checkpoint = CheckpointManager(config.checkpoint_dir)

        # Registrar núcleos en el clock
        # Priority 10 = Núcleo 1 SIEMPRE antes que Núcleo 2
        self.clock.on_tick(self.world.on_tick,   priority=10)
        self.clock.on_tick(self.agents.on_tick,  priority=20)
        self.clock.on_tick(self._on_tick_persist, priority=90)

        # Eventos de día
        self.clock.on_day(self.world.on_day,     priority=10)
        self.clock.on_day(self.agents.on_day,    priority=20)
        self.clock.on_day(self._on_day_checkpoint, priority=90)

        # Cambio de estación
        self.clock.on_season_change(self.world.on_season_change,   priority=10)
        self.clock.on_season_change(self.agents.on_season_change,  priority=20)

        # Shutdown
        self.clock.on_shutdown(self._on_shutdown)
        self.clock.on_pause(self._on_pause)

        # Handlers de señales del SO
        self._register_os_signals()

    def run(self):
        self.clock.start()   # Esto bloquea hasta que se detenga

    def _register_os_signals(self):
        import signal
        signal.signal(signal.SIGINT,  lambda s, f: self.clock.shutdown())
        signal.signal(signal.SIGTERM, lambda s, f: self.clock.shutdown())

    def _on_shutdown(self, tp: TimePoint):
        """El clock terminó — guardar todo."""
        self.db.flush_all()
        self.checkpoint.save(self.clock, self.world, self.agents,
                             reason="shutdown")
        print(f"\nSimulación pausada en: {tp}")
        print(self.clock.get_performance_metrics())

    def _on_pause(self, tp: TimePoint, reason: str):
        """El clock se pausó — checkpoint inmediato."""
        self.checkpoint.save(self.clock, self.world, self.agents,
                             reason=f"pause_{reason}")
```

### Cómo los Núcleos escuchan el tick

```python
# core/world/world_core.py

class WorldCore:

    def on_tick(self, tp: TimePoint):
        """
        El mundo recibe el tick del clock.
        Solo sabe la hora — no sabe nada de agentes.
        """
        self.climate.update(tp)
        self.resources.update(tp)
        self.fauna.update(tp)
        self.fire.update(tp)
        self._apply_pending_agent_actions()
        self._produce_snapshot(tp)   # Para que Núcleo 2 lo lea

    def on_day(self, tp: TimePoint):
        """Inicio de un nuevo día — regeneración, métricas."""
        self.resources.daily_regeneration()
        self.fauna.daily_update()
        self._log_world_state(tp)

    def on_season_change(self, tp: TimePoint):
        """La estación cambió — ajustar distribuciones base."""
        self.climate.transition_season(tp.estacion)
        self.resources.adjust_seasonal_availability(tp.estacion)
        self.fauna.adjust_seasonal_behavior(tp.estacion)


# core/agents/agent_core.py

class AgentCore:

    def on_tick(self, tp: TimePoint):
        """
        Los agentes reciben el tick del clock.
        El mundo ya se actualizó (priority 10 < 20).
        """
        world_snapshot = self.world_ref.current_snapshot
        
        actions = []
        for agent in self.alive_agents:
            agent.update_biological(tp, world_snapshot)
            action = agent.decide_action(tp, world_snapshot)
            if action:
                actions.append(action)

        # Interacciones entre agentes en la misma zona
        self.interaction_engine.process(tp, world_snapshot)

        # Actualizar campo colectivo
        self.collective_field.update(tp)

        # Sueños solo de noche
        if tp.es_noche:
            self.dream_engine.process(tp)

        # Enviar acciones al mundo para el siguiente tick
        self.world_ref.receive_actions(actions)

    def on_day(self, tp: TimePoint):
        """Inicio de día — snapshots, verificaciones vitales."""
        self._check_births_and_deaths(tp)
        self._snapshot_all_agents(tp)
        self._check_technology_discoveries(tp)

    def on_season_change(self, tp: TimePoint):
        """La estación cambió — ajustar schedules."""
        for agent in self.alive_agents:
            agent.schedule.adjust_for_season(tp.estacion)
```

---

## IV. ESTADOS DEL CLOCK Y SUS CONSECUENCIAS

```
STOPPED → RUNNING
  Ocurre: al iniciar la simulación o al reanudar desde checkpoint
  Núcleo 1: carga su estado y comienza a actualizar
  Núcleo 2: carga sus agentes y comienza a procesar
  Clock: comienza a emitir ticks

RUNNING → PAUSED
  Ocurre: checkpoint automático, inspección manual, evento mayor
  Clock: completa el tick actual y deja de emitir
  Núcleo 1: congela su estado (no se actualiza más)
  Núcleo 2: congela sus agentes (no procesan más)
  Persistencia: flush de buffers + checkpoint
  *** Ambos núcleos quedan en el MISMO instante ***

PAUSED → RUNNING
  Ocurre: checkpoint completado, inspección terminada
  Clock: reanuda desde el tick siguiente al que pausó
  Núcleo 1: continúa desde su estado congelado
  Núcleo 2: continúa desde sus agentes congelados
  *** El tiempo nunca retrocede ***

RUNNING → SHUTDOWN
  Ocurre: Ctrl+C, SIGTERM, timeout de sesión
  Clock: completa el tick actual, emite ON_SHUTDOWN, se detiene
  Núcleo 1: guarda estado completo
  Núcleo 2: guarda estado completo
  Persistencia: flush total + checkpoint final
  *** El próximo inicio retoma desde este exacto momento ***

SHUTDOWN → STOPPED → RUNNING (próxima sesión)
  El clock se restaura desde el checkpoint
  tick, dia, hora, estacion: exactamente donde quedó
  *** Para los agentes, no pasó tiempo ***
```

---

## V. EL CHECKPOINT DEL CLOCK

El clock es lo primero que se guarda y lo primero que se restaura.
Sin el tick exacto, el checkpoint de mundo y agentes no tiene referencia.

```python
# persistence/checkpoint.py

class CheckpointManager:

    def save(self, clock, world, agents, reason="auto"):
        """
        Orden de serialización:
        1. Clock primero — es el ancla temporal de todo
        2. Mundo — su estado depende del tick
        3. Agentes — su estado depende del tick
        """
        data = {
            "meta": {
                "reason":       reason,
                "timestamp_real": time.time(),
                "version":      VERSION,
            },
            "clock":   clock.to_dict(),      # ← PRIMERO
            "world":   world.to_dict(),
            "agents":  agents.to_dict(),
        }

        path = self._get_checkpoint_path(clock.now.dia_simulado)
        self._atomic_write(path, data)

    def load(self) -> tuple:
        """
        Orden de restauración:
        1. Clock — define el instante temporal
        2. Mundo — se restaura en ese instante
        3. Agentes — se restauran en ese instante
        """
        data = self._load_latest()

        clock  = SimulationClock.from_dict(data["clock"])   # ← PRIMERO
        world  = WorldCore.from_dict(data["world"])
        agents = AgentCore.from_dict(data["agents"])

        return clock, world, agents
```

---

## VI. RESUMEN — El Tiempo como Eje

```
                         SIMULATIONCLOCK
                         ═══════════════
                         tick: entero absoluto
                         state: STOPPED/RUNNING/PAUSED/SHUTDOWN
                         
                         Emite señales a:
                         ON_TICK → cada hora simulada
                         ON_DAY  → cada nuevo día
                         ON_SEASON → cada cambio de estación
                         ON_PAUSE → cuando frena
                         ON_SHUTDOWN → cuando termina
                         
                              │
                    ┌─────────┴─────────┐
                    │ priority=10       │ priority=20
                    ▼                   ▼
             NÚCLEO 1             NÚCLEO 2
             WorldCore            AgentCore
             
             Recibe ON_TICK       Recibe ON_TICK
             DESPUÉS del          DESPUÉS del
             Núcleo 1             Núcleo 1
             
             No conoce            No modifica
             la psicología        el mundo directo

REGLA ABSOLUTA:
  Si clock.state != RUNNING → ningún núcleo procesa nada.
  No hay excepciones.
  No hay procesamiento en background.
  El tiempo es único y compartido.
```

---

*Psyche Simulacra — SimulationClock v1.0*  
*El tiempo es único. Lo comparten ambos núcleos.*  
*Si frena, todo frena. Si avanza, todo avanza.*
