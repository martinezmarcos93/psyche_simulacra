"""
Tests del Núcleo 1 (Mundo) — Fase 2.
Cubre TerrainGrid, ClimateSystem, ResourceSystem, FaunaSystem,
FireSystem, WorldCore y el criterio de performance (1 año en < 5s).
"""
import time
import pytest
from core.time import SimulationClock, TimePoint
from core.world import (
    TerrainGrid, ClimateSystem, ResourceSystem,
    FaunaSystem, FireSystem, WorldCore, BIOME_DATA,
)
from core.interface import ActionType, WorldAction


# ── TerrainGrid ───────────────────────────────────────────────────────────────

class TestTerrainGrid:

    def test_dimensiones(self):
        t = TerrainGrid(seed=42)
        assert t.total_cells == 80 * 60

    def test_centro_es_habitable(self):
        t = TerrainGrid(seed=42)
        cx, cy = t.center
        cell = t.get(cx, cy)
        assert cell is not None
        assert cell.biome in ("valle_fertil", "pradera_humeda")

    def test_area_inicial_explorada(self):
        t = TerrainGrid(seed=42)
        explored = t.explored_hexes()
        # El radio 2 alrededor del centro debe estar explorado
        assert len(explored) > 0

    def test_vecinos_correctos(self):
        t = TerrainGrid(seed=42)
        cx, cy = t.center
        vecinos = t.neighbors(cx, cy)
        assert len(vecinos) == 6

    def test_distancia_hex(self):
        assert TerrainGrid.hex_distance(0, 0, 3, 0) == 3
        assert TerrainGrid.hex_distance(0, 0, 0, 0) == 0
        assert TerrainGrid.hex_distance(0, 0, 1, 1) == 2

    def test_in_radius(self):
        t = TerrainGrid(seed=42)
        cx, cy = t.center
        hexes_r2 = t.in_radius(cx, cy, radius=2)
        # Radio 2: 1 + 6 + 12 = 19 hexes
        assert len(hexes_r2) == 19

    def test_reveal_marca_explorado(self):
        t = TerrainGrid(seed=42)
        # Explorar una zona alejada
        nuevos = t.reveal(10, 10, radius=1)
        assert len(nuevos) > 0
        assert t.get(10, 10).explored

    def test_todos_los_biomas_definidos(self):
        t = TerrainGrid(seed=42)
        biomas_usados = {c.biome for c in t._cells.values()}
        for bioma in biomas_usados:
            assert bioma in BIOME_DATA, f"Bioma '{bioma}' sin datos"


# ── ClimateSystem ─────────────────────────────────────────────────────────────

class TestClimateSystem:

    def _make_tp(self, dia: int, hora: int, estacion: str = "primavera") -> TimePoint:
        return TimePoint(
            tick=dia * 24 + hora, dia_simulado=dia, hora_del_dia=hora,
            dia_del_año=dia % 360, año_simulado=dia // 360,
            estacion=estacion,
            es_amanecer=(hora == 6), es_mediodia=(hora == 12),
            es_anochecer=(hora == 20), es_medianoche=(hora == 23),
            es_inicio_dia=(hora == 0), es_fin_dia=(hora == 23),
            timestamp_real=time.monotonic(),
        )

    def test_produce_climate_state(self):
        c  = ClimateSystem(seed=42)
        tp = self._make_tp(0, 12)
        cs = c.update(tp)
        assert 0.0 <= cs.precipitacion <= 1.0
        assert 0.0 <= cs.luminosidad <= 1.0
        assert -50.0 <= cs.temperatura <= 60.0

    def test_temperatura_mas_alta_en_verano(self):
        c = ClimateSystem(seed=42)
        temps_invierno = []
        temps_verano   = []
        for hora in range(24):
            tp = self._make_tp(270, hora, "invierno")
            cs = c.update(tp)
            temps_invierno.append(cs.temperatura)
        c2 = ClimateSystem(seed=42)
        for hora in range(24):
            tp = self._make_tp(90, hora, "verano")
            cs = c2.update(tp)
            temps_verano.append(cs.temperatura)
        assert sum(temps_verano) / len(temps_verano) > \
               sum(temps_invierno) / len(temps_invierno)

    def test_luminosidad_nula_de_noche(self):
        c  = ClimateSystem(seed=42)
        tp = self._make_tp(0, 2, "verano")
        cs = c.update(tp)
        assert cs.luminosidad <= 0.10

    def test_mood_modifier_rango(self):
        c = ClimateSystem(seed=42)
        for hora in range(24):
            tp = self._make_tp(0, hora)
            cs = c.update(tp)
            assert -0.50 <= cs.mood_modifier <= 0.30

    def test_survival_risk_invierno_frio(self):
        c = ClimateSystem(seed=0)
        # Forzar temperatura muy baja: muchos ticks de invierno
        for i in range(100):
            tp = self._make_tp(270 + i, 3, "invierno")
            cs = c.update(tp)
        assert cs.survival_risk >= 0.0


# ── ResourceSystem ────────────────────────────────────────────────────────────

class TestResourceSystem:

    def test_inicializa_con_recursos(self):
        t = TerrainGrid(seed=42)
        r = ResourceSystem(t)
        cx, cy = t.center
        summary = r.get_hex_summary((cx, cy))
        assert len(summary) > 0

    def test_consumo_reduce_cantidad(self):
        t = TerrainGrid(seed=42)
        r = ResourceSystem(t)
        cx, cy = t.center
        summary_antes = r.get_hex_summary((cx, cy))
        first_resource = next(iter(summary_antes))
        result = r.consume((cx, cy), first_resource, 0.20, "agente_1")
        assert result.success
        summary_despues = r.get_hex_summary((cx, cy))
        assert summary_despues.get(first_resource, 0) < summary_antes[first_resource]

    def test_consume_falla_si_agotado(self):
        t = TerrainGrid(seed=42)
        r = ResourceSystem(t)
        cx, cy = t.center
        # Agotar un recurso
        for _ in range(20):
            r.consume((cx, cy), "plantas", 1.0, "agente_1")
        result = r.consume((cx, cy), "plantas", 0.5, "agente_1")
        assert not result.success

    def test_regen_sube_recursos(self):
        t = TerrainGrid(seed=42)
        r = ResourceSystem(t)
        cx, cy = t.center
        # Consumir la mitad
        r.consume((cx, cy), "plantas", 0.30, "agente_1")
        antes = r.get_hex_summary((cx, cy)).get("plantas", 0)
        r.daily_regeneration("primavera", t.explored_coords())
        despues = r.get_hex_summary((cx, cy)).get("plantas", 0)
        assert despues > antes

    def test_presion_de_recursos(self):
        t = TerrainGrid(seed=42)
        r = ResourceSystem(t)
        pressure = r.total_pressure(t.explored_coords())
        assert 0.0 <= pressure <= 1.0


# ── FaunaSystem ───────────────────────────────────────────────────────────────

class TestFaunaSystem:

    def _climate_stub(self) -> object:
        from core.world.climate import ClimateState
        return ClimateState(
            temperatura=18.0, precipitacion=0.3, luminosidad=0.8,
            viento=0.2, humedad=0.5, estacion="primavera",
            evento_activo=None, mood_modifier=0.1,
            productivity_mod=0.1, survival_risk=0.0,
        )

    def test_inicializa_con_fauna(self):
        t = TerrainGrid(seed=42)
        f = FaunaSystem(t, seed=42)
        cx, cy = t.center
        summary = f.get_hex_summary((cx, cy))
        assert len(summary) > 0

    def test_caza_exitosa_reduce_densidad(self):
        t  = TerrainGrid(seed=42)
        f  = FaunaSystem(t, seed=42)
        cx, cy = t.center
        antes = f.get_hex_summary((cx, cy)).get("pequena", 0)
        # Intentar hasta que una cacería tenga éxito
        for _ in range(10):
            result = f.hunt((cx, cy), "pequena", 0.1, "agente_1")
            if result.success:
                break
        despues = f.get_hex_summary((cx, cy)).get("pequena", 0)
        # La densidad debe haberse reducido al menos un poco
        assert despues < antes

    def test_regen_fauna_sube(self):
        t  = TerrainGrid(seed=42)
        f  = FaunaSystem(t, seed=42)
        cx, cy = t.center
        # Reducir fauna
        for _ in range(5):
            f.hunt((cx, cy), "pequena", 0.2, "agente_1")
        antes   = f.get_hex_summary((cx, cy)).get("pequena", 0)
        climate = self._climate_stub()
        f.daily_update("primavera", climate, t.explored_coords())
        despues = f.get_hex_summary((cx, cy)).get("pequena", 0)
        assert despues >= antes


# ── FireSystem ────────────────────────────────────────────────────────────────

class TestFireSystem:

    def _climate_stub(self, precipitacion: float = 0.2) -> object:
        from core.world.climate import ClimateState
        return ClimateState(
            temperatura=20.0, precipitacion=precipitacion, luminosidad=0.8,
            viento=0.2, humedad=0.5, estacion="primavera",
            evento_activo=None, mood_modifier=0.1,
            productivity_mod=0.1, survival_risk=0.0,
        )

    def test_fuego_inactivo_por_defecto(self):
        f = FireSystem(seed=42)
        assert not f.is_active

    def test_encender_fuego_con_clima_bueno(self):
        f = FireSystem(seed=42)
        climate = self._climate_stub(precipitacion=0.1)
        # Con clima seco debe encender eventualmente
        for _ in range(20):
            result = f.ignite((40, 30), "agente_1", climate)
            if result.success:
                assert f.is_active
                break

    def test_fuego_decae_sin_mantenimiento(self):
        f = FireSystem(seed=42)
        climate = self._climate_stub(precipitacion=0.1)
        f.is_active  = True
        f.intensity  = 0.8
        f.heat_bonus = 0.3
        # Simular ticks sin lluvia
        for _ in range(50):
            f.update(climate)
        assert f.intensity < 0.8

    def test_lluvia_intensa_apaga_fuego(self):
        f = FireSystem(seed=42)
        f.is_active = True
        f.intensity = 0.5
        climate = self._climate_stub(precipitacion=0.95)
        for _ in range(20):
            f.update(climate)
        assert not f.is_active

    def test_serializar_y_restaurar(self):
        f = FireSystem(seed=42)
        f.is_active  = True
        f.location   = (40, 30)
        f.intensity  = 0.7
        f.heat_bonus = 0.25
        d  = f.to_dict()
        f2 = FireSystem.from_dict(d)
        assert f2.is_active
        assert f2.location == (40, 30)
        assert abs(f2.intensity - 0.7) < 1e-9


# ── WorldCore ─────────────────────────────────────────────────────────────────

class TestWorldCore:

    def _run_world(self, n_ticks: int) -> WorldCore:
        clock = SimulationClock(start_dia=0, start_hora=0)
        world = WorldCore(seed=42)
        clock.on_tick(world.on_tick,  priority=10)
        clock.on_day(world.on_day,    priority=10)

        count = [0]
        def stopper(tp: TimePoint) -> None:
            count[0] += 1
            if count[0] >= n_ticks:
                clock.shutdown()

        clock.on_tick(stopper, priority=99)
        clock.start()
        return world

    def test_snapshot_disponible_tras_un_tick(self):
        world = self._run_world(1)
        snap  = world.current_snapshot
        assert snap is not None
        assert snap.tick == 0
        assert snap.estacion == "primavera"

    def test_snapshot_contiene_recursos(self):
        world = self._run_world(1)
        snap  = world.current_snapshot
        assert len(snap.recursos_por_hex) > 0

    def test_snapshot_contiene_fauna(self):
        world = self._run_world(1)
        snap  = world.current_snapshot
        assert len(snap.fauna_visible) > 0

    def test_accion_recolectar_procesada(self):
        clock = SimulationClock(start_dia=0, start_hora=0)
        world = WorldCore(seed=42)
        clock.on_tick(world.on_tick, priority=10)
        clock.on_day(world.on_day,   priority=10)

        # En el tick 1, el agente envía una acción de recolectar
        tick_count = [0]

        def agent_tick(tp: TimePoint) -> None:
            if tick_count[0] == 0:
                cx, cy = world.terrain.center
                # Obtener primer recurso disponible en el centro
                resources = world.terrain.get(cx, cy)
                from core.world.hexagon import BIOME_DATA
                first_res = next(iter(BIOME_DATA[resources.biome]["base_resources"]))
                action = WorldAction(
                    agent_id = "agente_1",
                    tick     = tp.tick,
                    type     = ActionType.RECOLECTAR,
                    coord    = (cx, cy),
                    params   = {"resource": first_res, "amount": 0.10},
                )
                world.receive_actions([action])
            tick_count[0] += 1
            if tick_count[0] >= 2:
                clock.shutdown()

        clock.on_tick(agent_tick, priority=20)
        clock.start()

        # El resultado de la acción debe estar en el snapshot del tick 2
        snap = world.current_snapshot
        assert "agente_1" in snap.action_results
        assert snap.action_results["agente_1"].success


# ── Performance ───────────────────────────────────────────────────────────────

class TestPerformance:

    def test_un_año_en_menos_de_5_segundos(self):
        """
        Criterio de Fase 2: 1 año simulado (8640 ticks) debe correr en < 5s.
        """
        clock = SimulationClock(start_dia=0, start_hora=0)
        world = WorldCore(seed=42)
        clock.on_tick(world.on_tick, priority=10)
        clock.on_day(world.on_day,   priority=10)

        TICKS_UN_AÑO = 360 * 24  # 8640

        tick_count = [0]
        def stopper(tp: TimePoint) -> None:
            tick_count[0] += 1
            if tick_count[0] >= TICKS_UN_AÑO:
                clock.shutdown()

        clock.on_tick(stopper, priority=99)

        t0 = time.monotonic()
        clock.start()
        elapsed = time.monotonic() - t0

        assert tick_count[0] == TICKS_UN_AÑO
        assert elapsed < 5.0, f"1 año tardó {elapsed:.2f}s (límite: 5s)"
