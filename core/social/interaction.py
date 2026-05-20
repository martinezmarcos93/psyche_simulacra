from __future__ import annotations

import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.agents import Agent
    from core.social.network import SocialNetwork
    from core.social.collective_field import CollectiveField
    from core.social.mythology import MythologyEngine


class InteractionEngine:
    """
    Motor de Interacciones Sociales. Procesa y resuelve encuentros entre agentes
    que ocupan el mismo hexágono, decidiendo los efectos emocionales, biológicos,
    cambios de afinidad en la red y alimentación del campo colectivo.
    """

    def process_zone_interactions(
        self,
        agents: dict[str, Agent],
        network: SocialNetwork,
        collective_field: CollectiveField,
        mythology_engine: MythologyEngine | None = None,
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
                self.resolve_encounter(a, b, network, collective_field, mythology_engine)

    def resolve_encounter(
        self,
        a: Agent,
        b: Agent,
        network: SocialNetwork,
        collective_field: CollectiveField,
        mythology_engine: MythologyEngine | None = None,
    ) -> None:
        """
        Resuelve un encuentro individual cara a cara entre el agente A y el agente B,
        considerando los arquetipos míticos activos de la mitología.
        """
        state_a = a.estado_conductual or "aislamiento"
        state_b = b.estado_conductual or "aislamiento"

        # 1. Influencia de Mitología Activa en la percepción mutua
        hero_id, monster_id = None, None
        if mythology_engine:
            hero_id, monster_id = mythology_engine.get_myth_hero_monster()

        # Si A o B es el Héroe, inspira al otro a cooperar
        if hero_id:
            if a.id == hero_id and state_b in ("competencia", "manipulacion"):
                # 50% de probabilidad de que el héroe inspire cooperación en B
                if b._rng.random() < 0.50:
                    state_b = "cooperacion"
            elif b.id == hero_id and state_a in ("competencia", "manipulacion"):
                # 50% de probabilidad de que el héroe inspire cooperación en A
                if a._rng.random() < 0.50:
                    state_a = "cooperacion"

        # Si A o B es el Monstruo (chivo expiatorio), genera hostilidad o aislamiento
        if monster_id:
            if a.id == monster_id and state_b == "cooperacion":
                # La cooperación se convierte en competencia (hostilidad) o aislamiento
                state_b = b._rng.choice(["competencia", "aislamiento"])
            elif b.id == monster_id and state_a == "cooperacion":
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

            collective_field.absorb_interaction("cooperacion", "cooperacion", "cooperacion_pura")

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

            collective_field.absorb_interaction("cooperacion", "competencia", "conflicto_explotacion")

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

            collective_field.absorb_interaction("competencia", "competencia", "choque_violento")

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

            collective_field.absorb_interaction("manipulacion", "cooperacion", "exito_manipulacion")

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

            collective_field.absorb_interaction("manipulacion", "competencia", "fracaso_manipulacion")

        # Caso Manipulación - Manipulación (Juegos Mentales)
        elif state_a == "manipulacion" and state_b == "manipulacion":
            # Resistencia mutua
            network.modify_bond(a.id, b.id, -0.05)
            network.modify_bond(b.id, a.id, -0.05)

            a.ansiedad = min(1.0, a.ansiedad + 0.04)
            b.ansiedad = min(1.0, b.ansiedad + 0.04)
