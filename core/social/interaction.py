from __future__ import annotations

import os
import random
from typing import TYPE_CHECKING

from core.social import communication

if TYPE_CHECKING:
    from core.agents import Agent
    from core.social.network import SocialNetwork
    from core.social.collective_field import CollectiveField
    from core.social.mythology import MythologyEngine
    from core.social.tribe_manager import TribeManager


# Intensidad relativa de transmisión mítica por tipo de encuentro (ver
# MythologyEngine.on_social_transmission). Punto de partida teórico: magnitud
# de los efectos emocionales ya codificados en cada rama de resolve_encounter
# (choque_violento > conflicto_explotacion > cooperacion_pura). Overridable por
# env var para calibración empírica (ver scripts/myth_calibration.py) sin
# recompilar — mismo patrón que MYTH_CONTEXT_THRESHOLD en mythology.py. No se
# conecta manipulacion_* — fuera de alcance (ver docs/handoffs/2026-09-21.md §7)
# y su contaminación afectiva es menor y ambigua (engaño exitoso vs. detectado).
_MYTH_TRANSMISSION_INTENSITY: dict[str, float] = {
    "choque_violento":       float(os.getenv("MYTH_TRANSMISSION_CHOQUE_VIOLENTO", "1.00")),
    "conflicto_explotacion": float(os.getenv("MYTH_TRANSMISSION_CONFLICTO_EXPLOTACION", "0.50")),
    "cooperacion_pura":      float(os.getenv("MYTH_TRANSMISSION_COOPERACION_PURA", "0.25")),
}


class InteractionEngine:
    """
    Motor de Interacciones Sociales. Procesa y resuelve encuentros entre agentes
    que ocupan el mismo hexágono, decidiendo los efectos emocionales, biológicos,
    cambios de afinidad en la red y alimentación del campo colectivo.
    """

    def process_zone_interactions(
        self,
        agents:           dict[str, Agent],
        network:          SocialNetwork,
        collective_field: CollectiveField,
        mythology_engine: MythologyEngine | None = None,
        dia:              int = 0,
        tribe_manager:    TribeManager | None = None,
    ) -> None:
        """
        Agrupa a todos los agentes vivos por coordenadas, los empareja y
        resuelve encuentros sociales si comparten el mismo espacio.
        """
        by_pos: dict[tuple[int, int], list[Agent]] = {}
        for agent in agents.values():
            if not agent.is_alive:
                continue
            by_pos.setdefault(agent.posicion, []).append(agent)

        for pos, group in by_pos.items():
            if len(group) < 2:
                continue

            # Agrupación determinista por ID y luego barajado simple para encuentros
            shuffled = list(group)
            shuffled.sort(key=lambda x: x.id)
            
            # Usamos un generador de aleatoriedad para la sesión de encuentros
            # Para mantener coherencia con seeds, usamos el RNG de uno de los agentes
            rng = shuffled[0]._rng if hasattr(shuffled[0], "_rng") else random.Random()
            rng.shuffle(shuffled)

            # Emparejar agentes
            while len(shuffled) >= 2:
                a = shuffled.pop()
                b = shuffled.pop()
                self.resolve_encounter(a, b, network, collective_field, mythology_engine, dia, tribe_manager)

    def _absorb(
        self,
        state_a:          str,
        state_b:          str,
        outcome:          str,
        global_field:     CollectiveField,
        tribe_manager:    TribeManager | None,
        a_id:             str,
        b_id:             str,
    ) -> None:
        """Alimenta el campo global y, si corresponde, los campos tribales locales."""
        global_field.absorb_interaction(state_a, state_b, outcome)
        if tribe_manager is None:
            return
        la = tribe_manager.get_local_field(a_id)
        lb = tribe_manager.get_local_field(b_id)
        if la is lb and la is not None:
            # Misma tribu — campo compartido
            la.absorb_interaction(state_a, state_b, outcome)
        else:
            # Tribus distintas — cada una absorbe el eco
            if la is not None:
                la.absorb_interaction(state_a, state_b, outcome)
            if lb is not None and lb is not la:
                lb.absorb_interaction(state_a, state_b, outcome)

    def _local_context(
        self,
        agent_id:         str,
        global_field:     CollectiveField,
        global_mythology: MythologyEngine | None,
        tribe_manager:    TribeManager | None,
    ) -> tuple[CollectiveField, MythologyEngine | None]:
        """
        Resuelve el campo/mitología que le corresponde a un agente para
        reinterpretar un encuentro: los de SU tribu si tiene una y existen,
        el global si no. Misma resolución local/global que ya usa `_absorb`
        para alimentar el campo — aquí, en la otra dirección, para leerlo.

        Que cada agente reinterprete con el vocabulario de su propia tribu
        (en vez de uno único compartido) es lo que permite que el mismo
        encuentro cristalice significados distintos según quién lo viva
        (multiacentualidad — Voloshinov).
        """
        if tribe_manager is None:
            return global_field, global_mythology
        local_field = tribe_manager.get_local_field(agent_id)
        tribe_id = tribe_manager.get_tribe_id(agent_id)
        local_mythology = tribe_manager.local_myths.get(tribe_id) if tribe_id else None
        return (local_field or global_field), (local_mythology or global_mythology)

    def _reinterpret_pair(
        self,
        a:                Agent,
        b:                Agent,
        role_a:           str,
        role_b:           str,
        network:          SocialNetwork,
        collective_field: CollectiveField,
        mythology_engine: MythologyEngine | None,
        tribe_manager:    TribeManager | None,
    ) -> None:
        """
        Cada agente reinterpreta el encuentro ya resuelto a través de su
        propia Ecuación Personal (ver core/social/communication.py). No-op
        si `communication.REINTERPRETATION_ENABLED` está apagado (por
        defecto) — no altera en nada el comportamiento existente.
        """
        if not communication.REINTERPRETATION_ENABLED:
            return
        field_a, myth_a = self._local_context(a.id, collective_field, mythology_engine, tribe_manager)
        field_b, myth_b = self._local_context(b.id, collective_field, mythology_engine, tribe_manager)
        communication.reinterpret_encounter(a, b, role_a, network, field_a, myth_a)
        communication.reinterpret_encounter(b, a, role_b, network, field_b, myth_b)

    def resolve_encounter(
        self,
        a:                Agent,
        b:                Agent,
        network:          SocialNetwork,
        collective_field: CollectiveField,
        mythology_engine: MythologyEngine | None = None,
        dia:              int = 0,
        tribe_manager:    TribeManager | None = None,
    ) -> None:
        """
        Resuelve un encuentro individual cara a cara entre el agente A y el agente B,
        considerando los arquetipos míticos activos de la mitología.
        """
        state_a = a.estado_conductual or "aislamiento"
        state_b = b.estado_conductual or "aislamiento"

        # 1. Influencia de Mitología Activa en la percepción mutua. Cada agente
        # reconoce héroe/monstruo según SU PROPIA mitología (la de su tribu si
        # tiene una asignada vía tribe_manager; la global si no) — no una
        # única mitología compartida por toda la simulación. El mismo agente
        # puede así ser Héroe para su tribu y una figura sin estatus mítico
        # (o el propio Monstruo) para otra que cristalizó un mito distinto
        # sobre el mismo par arquetípico (multiacentualidad — Voloshinov).
        _, myth_a = self._local_context(a.id, collective_field, mythology_engine, tribe_manager)
        _, myth_b = self._local_context(b.id, collective_field, mythology_engine, tribe_manager)
        hero_for_a, monster_for_a = myth_a.get_myth_hero_monster() if myth_a is not None else (None, None)
        hero_for_b, monster_for_b = myth_b.get_myth_hero_monster() if myth_b is not None else (None, None)

        # B reconoce a A como Héroe (según la mitología de B) → A lo inspira a cooperar
        if hero_for_b and a.id == hero_for_b and state_b in ("competencia", "manipulacion"):
            # 50% de probabilidad de que el héroe inspire cooperación en B
            if b._rng.random() < 0.50:
                state_b = "cooperacion"
        # A reconoce a B como Héroe (según la mitología de A) → B lo inspira a cooperar
        if hero_for_a and b.id == hero_for_a and state_a in ("competencia", "manipulacion"):
            # 50% de probabilidad de que el héroe inspire cooperación en A
            if a._rng.random() < 0.50:
                state_a = "cooperacion"

        # B reconoce a A como el Monstruo (chivo expiatorio de B) → hostilidad en B
        if monster_for_b and a.id == monster_for_b and state_b == "cooperacion":
            # La cooperación se convierte en competencia (hostilidad) o aislamiento
            state_b = b._rng.choice(["competencia", "aislamiento"])
        # A reconoce a B como el Monstruo (chivo expiatorio de A) → hostilidad en A
        if monster_for_a and b.id == monster_for_a and state_a == "cooperacion":
            # La cooperación se convierte en competencia (hostilidad) o aislamiento
            state_a = a._rng.choice(["competencia", "aislamiento"])

        # 2. Matriz de Resolución de Encuentros
        # Caso Aislamiento: no ocurre interacción significativa
        if state_a == "aislamiento" or state_b == "aislamiento":
            return

        # Caso Cooperación - Cooperación (Cooperación pura)
        if state_a == "cooperacion" and state_b == "cooperacion":
            # Actualizar vínculos
            network.modify_bond(a.id, b.id, 0.08)
            network.modify_bond(b.id, a.id, 0.08)

            # Efectos emocionales y fatiga
            a.humor = min(1.0, a.humor + 0.05)
            a.ansiedad = max(0.0, a.ansiedad - 0.05)
            a.needs.fatiga = max(0.0, a.needs.fatiga - 0.02)

            b.humor = min(1.0, b.humor + 0.05)
            b.ansiedad = max(0.0, b.ansiedad - 0.05)
            b.needs.fatiga = max(0.0, b.needs.fatiga - 0.02)

            # Posibilidad de entrelazamiento cuántico social
            if network.get_bond(a.id, b.id) > 0.40:
                if a._rng.random() < 0.30:
                    network.entangle(a.id, b.id)

            a.episodic_log.append(f"Día {dia}: Cooperó de forma mutua y armónica con {b.nombre}. Su lazo social se fortaleció.")
            b.episodic_log.append(f"Día {dia}: Cooperó de forma mutua y armónica con {a.nombre}. Su lazo social se fortaleció.")

            self._absorb("cooperacion", "cooperacion", "cooperacion_pura",
                         collective_field, tribe_manager, a.id, b.id)

            # Cooperación pura también es una experiencia compartida significativa
            # (aunque menos intensa que un choque violento) — empuja al proto-mito
            # más avanzado hacia la cristalización, igual que la competencia mutua.
            if mythology_engine is not None:
                mythology_engine.on_social_transmission(
                    collective_field, intensity=_MYTH_TRANSMISSION_INTENSITY["cooperacion_pura"]
                )

            self._reinterpret_pair(a, b, "cooperacion_mutua", "cooperacion_mutua",
                                    network, collective_field, mythology_engine, tribe_manager)

        # Caso Cooperación - Competencia (Conflicto / Explotación)
        elif (state_a == "cooperacion" and state_b == "competencia") or \
             (state_a == "competencia" and state_b == "cooperacion"):
            
            victim = a if state_a == "cooperacion" else b
            exploiter = b if state_b == "competencia" else a

            # Actualizar vínculos
            network.modify_bond(victim.id, exploiter.id, -0.18)
            network.modify_bond(exploiter.id, victim.id, -0.02)

            # Efectos en víctima
            victim.humor = max(0.0, victim.humor - 0.12)
            victim.ansiedad = min(1.0, victim.ansiedad + 0.15)
            # Transferencia asimétrica de recursos (robo de comida)
            if victim.needs.hambre < 0.5:
                # La víctima cede parte de su saciedad al explotador
                victim.needs.hambre = min(1.0, victim.needs.hambre + 0.15)
                exploiter.needs.hambre = max(0.0, exploiter.needs.hambre - 0.15)

            # Efectos en explotador
            exploiter.humor = min(1.0, exploiter.humor + 0.05)
            exploiter.ansiedad = max(0.0, exploiter.ansiedad - 0.03)

            # Traición/trauma tiene una pequeña chance de entrelazar de forma negativa
            if victim._rng.random() < 0.10:
                network.entangle(victim.id, exploiter.id)

            victim.episodic_log.append(f"Día {dia}: Sufrió explotación y hostilidad de {exploiter.nombre}, cediendo recursos biológicos.")
            exploiter.episodic_log.append(f"Día {dia}: Se impuso competitivamente ante {victim.nombre}, absorbiendo sus recursos biológicos.")

            self._absorb("cooperacion", "competencia", "conflicto_explotacion",
                         collective_field, tribe_manager, a.id, b.id)

            # La explotación (traición de la cooperación) es una experiencia
            # compartida intensa para ambas partes — también empuja al proto-mito
            # más avanzado hacia la cristalización.
            if mythology_engine is not None:
                mythology_engine.on_social_transmission(
                    collective_field, intensity=_MYTH_TRANSMISSION_INTENSITY["conflicto_explotacion"]
                )

            self._reinterpret_pair(victim, exploiter, "explotado", "explotador",
                                    network, collective_field, mythology_engine, tribe_manager)

        # Caso Competencia - Competencia (Choque Violento)
        elif state_a == "competencia" and state_b == "competencia":
            # Caída mutua severa de vínculos
            network.modify_bond(a.id, b.id, -0.22)
            network.modify_bond(b.id, a.id, -0.22)

            # Efectos destructivos
            for agent in (a, b):
                agent.humor = max(0.0, agent.humor - 0.15)
                agent.ansiedad = min(1.0, agent.ansiedad + 0.20)
                agent.energia = max(0.0, agent.energia - 0.10)
                agent.needs.fatiga = min(1.0, agent.needs.fatiga + 0.08)

            # El trauma severo del conflicto violento entrelaza a los dos rivales
            if a._rng.random() < 0.15:
                network.entangle(a.id, b.id)

            a.episodic_log.append(f"Día {dia}: Se enfrentó en un choque violento y destructivo contra {b.nombre}.")
            b.episodic_log.append(f"Día {dia}: Se enfrentó en un choque violento y destructivo contra {a.nombre}.")

            self._absorb("competencia", "competencia", "choque_violento",
                         collective_field, tribe_manager, a.id, b.id)

            # Un choque violento es la experiencia compartida más intensa del motor de
            # encuentros (intensity=1.0, ver _MYTH_TRANSMISSION_INTENSITY) — es la que
            # más empuja al proto-mito más avanzado hacia la cristalización (igual
            # que cooperación pura y conflicto/explotación, ver
            # docs/experiments/2026-09-21-fase1-ecuacion-personal.md).
            if mythology_engine is not None:
                mythology_engine.on_social_transmission(
                    collective_field, intensity=_MYTH_TRANSMISSION_INTENSITY["choque_violento"]
                )

            self._reinterpret_pair(a, b, "choque_violento", "choque_violento",
                                    network, collective_field, mythology_engine, tribe_manager)

        # Caso Manipulación - Cooperación (Éxito de manipulación)
        elif (state_a == "manipulacion" and state_b == "cooperacion") or \
             (state_a == "cooperacion" and state_b == "manipulacion"):
            
            manipulator = a if state_a == "manipulacion" else b
            cooperator = b if state_b == "cooperacion" else a

            # El cooperador es engañado: su vínculo hacia el manipulador aumenta
            network.modify_bond(cooperator.id, manipulator.id, 0.04)
            # El manipulador se aprovecha pragmáticamente
            network.modify_bond(manipulator.id, cooperator.id, 0.02)

            # Efectos
            manipulator.humor = min(1.0, manipulator.humor + 0.08)
            manipulator.ansiedad = max(0.0, manipulator.ansiedad - 0.05)
            # Transferencia menor de saciedad/recursos
            cooperator.needs.hambre = min(1.0, cooperator.needs.hambre + 0.10)
            manipulator.needs.hambre = max(0.0, manipulator.needs.hambre - 0.10)

            cooperator.episodic_log.append(f"Día {dia}: Cedió ingenuamente ante la manipulación de {manipulator.nombre}.")
            manipulator.episodic_log.append(f"Día {dia}: Manipuló con éxito y astucia a {cooperator.nombre} para ceder recursos.")

            self._absorb("manipulacion", "cooperacion", "exito_manipulacion",
                         collective_field, tribe_manager, a.id, b.id)

            self._reinterpret_pair(cooperator, manipulator, "manipulado_exitosamente", "manipulador_exitoso",
                                    network, collective_field, mythology_engine, tribe_manager)

        # Caso Manipulación - Competencia (Fracaso de manipulación)
        elif (state_a == "manipulacion" and state_b == "competencia") or \
             (state_a == "competencia" and state_b == "manipulacion"):
            
            manipulator = a if state_a == "manipulacion" else b
            competitor = b if state_b == "competencia" else a

            # Sospecha extrema
            network.modify_bond(manipulator.id, competitor.id, -0.10)
            network.modify_bond(competitor.id, manipulator.id, -0.15)

            # Efectos
            manipulator.humor = max(0.0, manipulator.humor - 0.08)
            manipulator.ansiedad = min(1.0, manipulator.ansiedad + 0.10)

            manipulator.episodic_log.append(f"Día {dia}: Intentó manipular a {competitor.nombre}, pero fue descubierto.")
            competitor.episodic_log.append(f"Día {dia}: Detectó y rechazó un intento de manipulación de {manipulator.nombre}.")

            self._absorb("manipulacion", "competencia", "fracaso_manipulacion",
                         collective_field, tribe_manager, a.id, b.id)

            self._reinterpret_pair(manipulator, competitor, "manipulador_fracasado", "manipulacion_resistida",
                                    network, collective_field, mythology_engine, tribe_manager)

        # Caso Manipulación - Manipulación (Juegos Mentales)
        elif state_a == "manipulacion" and state_b == "manipulacion":
            # Resistencia mutua
            network.modify_bond(a.id, b.id, -0.05)
            network.modify_bond(b.id, a.id, -0.05)

            a.ansiedad = min(1.0, a.ansiedad + 0.04)
            b.ansiedad = min(1.0, b.ansiedad + 0.04)

            a.episodic_log.append(f"Día {dia}: Se vio envuelto en intrigas de manipulación mutua y juegos mentales con {b.nombre}.")
            b.episodic_log.append(f"Día {dia}: Se vio envuelto en intrigas de manipulación mutua y juegos mentales con {a.nombre}.")

            self._reinterpret_pair(a, b, "juego_mental_mutuo", "juego_mental_mutuo",
                                    network, collective_field, mythology_engine, tribe_manager)
