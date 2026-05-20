"""
Tests del SimulationClock — Fase 1.
Verifica que el reloj emite ticks correctamente, gestiona estados,
serializa/deserializa y dispara eventos de día y estación.
"""
import pytest
from core.time import ClockState, SimulationClock, TimePoint


# ── Helpers ──────────────────────────────────────────────────────────────────

def run_clock_n_ticks(clock: SimulationClock, n: int) -> list[TimePoint]:
    """Corre el reloj exactamente n ticks y lo detiene."""
    collected: list[TimePoint] = []

    def on_tick(tp: TimePoint) -> None:
        collected.append(tp)
        if len(collected) >= n:
            clock.shutdown()

    clock.on_tick(on_tick)
    clock.start()
    return collected


# ── TimePoint ─────────────────────────────────────────────────────────────────

class TestTimePoint:

    def test_propiedades_basicas(self):
        clock = SimulationClock(start_dia=0, start_hora=6)
        tp = clock.now
        assert tp.tick == 6            # 0 días × 24 + 6 horas
        assert tp.dia_simulado == 0
        assert tp.hora_del_dia == 6
        assert tp.es_amanecer is True
        assert tp.es_dia is True
        assert tp.es_noche is False

    def test_noche(self):
        clock = SimulationClock(start_dia=0, start_hora=22)
        tp = clock.now
        assert tp.es_noche is True
        assert tp.es_dia is False

    def test_estaciones(self):
        # Día 0 → primavera
        assert SimulationClock(start_dia=0).now.estacion == "primavera"
        # Día 90 → verano
        assert SimulationClock(start_dia=90).now.estacion == "verano"
        # Día 180 → otoño
        assert SimulationClock(start_dia=180).now.estacion == "otoño"
        # Día 270 → invierno
        assert SimulationClock(start_dia=270).now.estacion == "invierno"
        # Día 360 → primavera (año 2)
        assert SimulationClock(start_dia=360).now.estacion == "primavera"

    def test_str_legible(self):
        clock = SimulationClock(start_dia=5, start_hora=12)
        s = str(clock.now)
        assert "primavera" in s
        assert "12:00h" in s
        assert "tick" in s

    def test_semana_y_mes(self):
        clock = SimulationClock(start_dia=35)
        tp = clock.now
        assert tp.semana_simulada == 5
        assert tp.mes_simulado == 1


# ── Ticks y conteo ───────────────────────────────────────────────────────────

class TestTickConteo:

    def test_tick_avanza(self):
        clock = SimulationClock(start_dia=0, start_hora=0)
        ticks = run_clock_n_ticks(clock, 10)
        assert len(ticks) == 10
        for i, tp in enumerate(ticks):
            assert tp.tick == i

    def test_hora_cicla_cada_24(self):
        clock = SimulationClock(start_dia=0, start_hora=0)
        ticks = run_clock_n_ticks(clock, 48)
        horas = [tp.hora_del_dia for tp in ticks]
        assert horas[:24] == list(range(24))
        assert horas[24:48] == list(range(24))

    def test_dia_avanza(self):
        clock = SimulationClock(start_dia=0, start_hora=0)
        ticks = run_clock_n_ticks(clock, 25)
        dias = [tp.dia_simulado for tp in ticks]
        assert dias[0] == 0
        assert dias[24] == 1   # Tick 24 = inicio día 1

    def test_estado_stopped_antes_de_start(self):
        clock = SimulationClock()
        assert clock.state == ClockState.STOPPED

    def test_estado_stopped_despues_de_shutdown(self):
        clock = SimulationClock()
        ticks = run_clock_n_ticks(clock, 5)
        assert clock.state == ClockState.STOPPED
        assert len(ticks) == 5


# ── Eventos ───────────────────────────────────────────────────────────────────

class TestEventos:

    def test_on_day_se_dispara_al_inicio_del_dia(self):
        clock = SimulationClock(start_dia=0, start_hora=0)
        dias_recibidos: list[int] = []

        def on_day(tp: TimePoint) -> None:
            dias_recibidos.append(tp.dia_simulado)

        clock.on_day(on_day)
        run_clock_n_ticks(clock, 50)   # 2 días + 2 ticks

        # Día 0 (tick 0) y día 1 (tick 24)
        assert 0 in dias_recibidos
        assert 1 in dias_recibidos

    def test_on_season_change_se_dispara_al_cambiar_estacion(self):
        # Empezamos al final de primavera para ver el cambio a verano
        clock = SimulationClock(start_dia=89, start_hora=23)
        estaciones_nuevas: list[str] = []

        def on_season(tp: TimePoint) -> None:
            estaciones_nuevas.append(tp.estacion)

        clock.on_season_change(on_season)
        run_clock_n_ticks(clock, 2)   # tick 89h23 → 90h00 → cambia estación

        assert "verano" in estaciones_nuevas

    def test_prioridad_handlers(self):
        """Handlers con menor prioridad se ejecutan antes."""
        clock = SimulationClock()
        orden: list[int] = []

        clock.on_tick(lambda tp: orden.append(30), priority=30)
        clock.on_tick(lambda tp: orden.append(10), priority=10)
        clock.on_tick(lambda tp: orden.append(20), priority=20)

        run_clock_n_ticks(clock, 1)

        assert orden == [10, 20, 30]

    def test_on_shutdown_se_llama(self):
        clock = SimulationClock()
        shutdown_llamado = []

        clock.on_shutdown(lambda tp: shutdown_llamado.append(tp.tick))
        run_clock_n_ticks(clock, 3)

        assert len(shutdown_llamado) == 1


# ── Serialización ─────────────────────────────────────────────────────────────

class TestSerializacion:

    def test_to_dict_contiene_campos_necesarios(self):
        clock = SimulationClock(start_dia=5, start_hora=12)
        d = clock.to_dict()
        assert "tick" in d
        assert "dia_simulado" in d
        assert "hora_del_dia" in d
        assert "año_simulado" in d
        assert "estacion" in d

    def test_from_dict_restaura_estado(self):
        clock1 = SimulationClock(start_dia=42, start_hora=15)
        d = clock1.to_dict()

        clock2 = SimulationClock.from_dict(d)
        assert clock2.now.dia_simulado == 42
        assert clock2.now.hora_del_dia == 15
        assert clock2.now.estacion == clock1.now.estacion

    def test_checkpoint_redondeo(self):
        """Correr N ticks, serializar, restaurar y verificar continuidad."""
        clock = SimulationClock(start_dia=0, start_hora=0)
        run_clock_n_ticks(clock, 100)

        d = clock.to_dict()
        clock2 = SimulationClock.from_dict(d)

        assert clock2.now.tick == clock.now.tick
        assert clock2.now.dia_simulado == clock.now.dia_simulado


# ── Performance ───────────────────────────────────────────────────────────────

class TestPerformance:

    def test_metricas_disponibles_tras_correr(self):
        clock = SimulationClock()
        run_clock_n_ticks(clock, 50)
        m = clock.get_performance_metrics()
        assert "ticks_per_second" in m
        assert m["ticks_esta_sesion"] == 50

    def test_metricas_vacias_antes_de_correr(self):
        clock = SimulationClock()
        assert clock.get_performance_metrics() == {}

    def test_velocidad_minima_entre_ticks(self):
        """Con set_speed, el reloj no corre más rápido del límite."""
        import time
        clock = SimulationClock()
        clock.set_speed(0.01)   # 10ms entre ticks

        t0 = time.monotonic()
        run_clock_n_ticks(clock, 5)
        elapsed = time.monotonic() - t0

        # 5 ticks × 10ms = al menos 40ms (algo de overhead es normal)
        assert elapsed >= 0.04
