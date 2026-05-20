from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable
import time


class ClockState(Enum):
    STOPPED  = auto()
    RUNNING  = auto()
    PAUSED   = auto()
    SHUTDOWN = auto()


@dataclass(frozen=True)
class TimePoint:
    tick:           int
    dia_simulado:   int
    hora_del_dia:   int
    dia_del_año:    int
    año_simulado:   int
    estacion:       str
    es_amanecer:    bool   # hora == 6
    es_mediodia:    bool   # hora == 12
    es_anochecer:   bool   # hora == 20
    es_medianoche:  bool   # hora == 0
    es_inicio_dia:  bool   # hora == 0  (mismo que medianoche, semántica distinta)
    es_fin_dia:     bool   # hora == 23
    timestamp_real: float  # time.monotonic() al emitir

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
        return (
            f"Año {self.año_simulado}, {self.estacion}, "
            f"Día {self.dia_del_año}, {self.hora_del_dia:02d}:00h "
            f"[tick {self.tick}]"
        )


class SimulationClock:
    """
    El tiempo único de la simulación.
    Gobierna a ambos núcleos. No pertenece a ninguno.
    Si frena, todo frena. Si avanza, todo avanza.
    """

    TICKS_PER_DAY:   int       = 24
    DAYS_PER_SEASON: int       = 90
    DAYS_PER_YEAR:   int       = 360
    SEASONS:         list[str] = ["primavera", "verano", "otoño", "invierno"]

    def __init__(self, start_dia: int = 0, start_hora: int = 6) -> None:
        self._tick:  int        = start_dia * self.TICKS_PER_DAY + start_hora
        self._state: ClockState = ClockState.STOPPED

        # Suscriptores — (prioridad, handler); menor prioridad = se llama antes
        # Núcleo 1 usa priority=10, Núcleo 2 usa priority=20
        self._on_tick_handlers:     list[tuple[int, Callable[[TimePoint], None]]]       = []
        self._on_day_handlers:      list[tuple[int, Callable[[TimePoint], None]]]       = []
        self._on_season_handlers:   list[tuple[int, Callable[[TimePoint], None]]]       = []
        self._on_pause_handlers:    list[Callable[[TimePoint, str], None]]              = []
        self._on_resume_handlers:   list[Callable[[TimePoint], None]]                  = []
        self._on_shutdown_handlers: list[Callable[[TimePoint], None]]                  = []

        # Performance
        self._ticks_this_session: int   = 0
        self._session_start_real: float = 0.0

        # None = máxima velocidad. float = segundos mínimos entre ticks.
        self._min_tick_interval: float | None = None

        # Seguimiento de estación para detectar cambios
        start_dia_del_año  = start_dia % self.DAYS_PER_YEAR
        self._last_season: str = self.SEASONS[start_dia_del_año // self.DAYS_PER_SEASON]

    # ── Suscripción ──────────────────────────────────────────────────────────

    def on_tick(self, handler: Callable[[TimePoint], None], priority: int = 50) -> None:
        self._on_tick_handlers.append((priority, handler))
        self._on_tick_handlers.sort(key=lambda x: x[0])

    def on_day(self, handler: Callable[[TimePoint], None], priority: int = 50) -> None:
        self._on_day_handlers.append((priority, handler))
        self._on_day_handlers.sort(key=lambda x: x[0])

    def on_season_change(self, handler: Callable[[TimePoint], None], priority: int = 50) -> None:
        self._on_season_handlers.append((priority, handler))
        self._on_season_handlers.sort(key=lambda x: x[0])

    def on_pause(self, handler: Callable[[TimePoint, str], None]) -> None:
        self._on_pause_handlers.append(handler)

    def on_resume(self, handler: Callable[[TimePoint], None]) -> None:
        self._on_resume_handlers.append(handler)

    def on_shutdown(self, handler: Callable[[TimePoint], None]) -> None:
        self._on_shutdown_handlers.append(handler)

    # ── Control ──────────────────────────────────────────────────────────────

    def start(self) -> None:
        if self._state != ClockState.STOPPED:
            raise RuntimeError(f"No se puede iniciar desde estado {self._state}")
        self._state = ClockState.RUNNING
        self._session_start_real = time.monotonic()
        self._run_loop()

    def pause(self, reason: str = "manual") -> None:
        if self._state == ClockState.RUNNING:
            self._state = ClockState.PAUSED
            tp = self.now
            for handler in self._on_pause_handlers:
                handler(tp, reason)

    def resume(self) -> None:
        if self._state != ClockState.PAUSED:
            raise RuntimeError(f"No se puede reanudar desde estado {self._state}")
        self._state = ClockState.RUNNING
        tp = self.now
        for handler in self._on_resume_handlers:
            handler(tp)
        self._run_loop()

    def shutdown(self) -> None:
        """
        Apagado ordenado. Completa el tick en curso y detiene el loop.
        Seguro llamar desde un handler de tick.
        """
        self._state = ClockState.SHUTDOWN

    def set_speed(self, seconds_per_tick: float | None = None) -> None:
        """
        None = máxima velocidad (simulación normal).
        0.1  = 10 ticks/segundo (observación).
        1.0  = 1 tick/segundo (debug).
        """
        self._min_tick_interval = seconds_per_tick

    # ── Loop principal ────────────────────────────────────────────────────────

    def _run_loop(self) -> None:
        while self._state == ClockState.RUNNING:
            tick_start = time.monotonic()
            tp = self._make_timepoint()

            self._emit_tick(tp)

            if tp.es_inicio_dia:
                self._emit_day(tp)

            self._check_season_change(tp)

            self._tick += 1
            self._ticks_this_session += 1

            if self._min_tick_interval is not None:
                elapsed = time.monotonic() - tick_start
                remaining = self._min_tick_interval - elapsed
                if remaining > 0:
                    time.sleep(remaining)

        # Si salimos por SHUTDOWN, notificar handlers y dejar en STOPPED
        if self._state == ClockState.SHUTDOWN:
            tp = self._make_timepoint()
            for handler in self._on_shutdown_handlers:
                handler(tp)
            self._state = ClockState.STOPPED

    def _emit_tick(self, tp: TimePoint) -> None:
        # Si alguien llama shutdown() dentro de un handler, completamos
        # el tick actual igualmente — no hay ticks parciales.
        for _, handler in self._on_tick_handlers:
            handler(tp)

    def _emit_day(self, tp: TimePoint) -> None:
        for _, handler in self._on_day_handlers:
            handler(tp)

    def _check_season_change(self, tp: TimePoint) -> None:
        if tp.estacion != self._last_season:
            self._last_season = tp.estacion
            for _, handler in self._on_season_handlers:
                handler(tp)

    # ── Estado ────────────────────────────────────────────────────────────────

    @property
    def now(self) -> TimePoint:
        return self._make_timepoint()

    @property
    def state(self) -> ClockState:
        return self._state

    @property
    def is_running(self) -> bool:
        return self._state == ClockState.RUNNING

    @property
    def tick(self) -> int:
        return self._tick

    @property
    def dia_simulado(self) -> int:
        return self._tick // self.TICKS_PER_DAY

    def _make_timepoint(self) -> TimePoint:
        hora        = self._tick % self.TICKS_PER_DAY
        dia         = self._tick // self.TICKS_PER_DAY
        dia_del_año = dia % self.DAYS_PER_YEAR
        año         = dia // self.DAYS_PER_YEAR
        estacion    = self.SEASONS[dia_del_año // self.DAYS_PER_SEASON]

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

    # ── Serialización ─────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "tick":         self._tick,
            "dia_simulado": self._tick // self.TICKS_PER_DAY,
            "hora_del_dia": self._tick % self.TICKS_PER_DAY,
            "año_simulado": (self._tick // self.TICKS_PER_DAY) // self.DAYS_PER_YEAR,
            "estacion":     self.now.estacion,
            "ticks_total":  self._ticks_this_session,
        }

    @classmethod
    def from_dict(cls, data: dict) -> SimulationClock:
        return cls(
            start_dia  = data["dia_simulado"],
            start_hora = data["hora_del_dia"],
        )

    # ── Métricas ──────────────────────────────────────────────────────────────

    def get_performance_metrics(self) -> dict:
        if self._ticks_this_session == 0:
            return {}
        elapsed_real     = time.monotonic() - self._session_start_real
        ticks_per_second = self._ticks_this_session / elapsed_real
        dias_per_minute  = (ticks_per_second * 60) / self.TICKS_PER_DAY

        return {
            "ticks_per_second":               round(ticks_per_second, 1),
            "dias_simulados_por_minuto_real":  round(dias_per_minute, 1),
            "dias_simulados_por_hora_real":    round(dias_per_minute * 60, 0),
            "ticks_esta_sesion":               self._ticks_this_session,
            "tiempo_real_segundos":            round(elapsed_real, 2),
        }
