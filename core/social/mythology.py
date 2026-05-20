from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.agents import Agent
    from core.social.collective_field import CollectiveField


class MythologyEngine:
    """
    Motor de Mitología Emergente. Detecta si la carga del campo colectivo y la
    configuración arquetípica de los agentes cumplen las condiciones para cristalizar
    un mito o tabú, aplicando retroalimentación persistente al grupo.
    """

    def __init__(self) -> None:
        self.active_myths: list[dict] = []

    def check_crystallization(
        self,
        field: CollectiveField,
        agents: dict[str, Agent],
        dia: int,
    ) -> None:
        """
        Verifica si se cumplen las condiciones para cristalizar nuevos mitos
        o mantener/romper los mitos activos.
        """
        # 1. Verificar mitos activos
        active_hero_vs_monster = None
        for myth in self.active_myths:
            if myth.get("name") == "heroe_vs_monstruo" and myth.get("active", False):
                active_hero_vs_monster = myth
                break

        if active_hero_vs_monster:
            # Verificar si los protagonistas siguen vivos
            hero_id = active_hero_vs_monster["hero_id"]
            monster_id = active_hero_vs_monster["monster_id"]

            if (hero_id not in agents or not agents[hero_id].is_alive) or \
               (monster_id not in agents or not agents[monster_id].is_alive):
                active_hero_vs_monster["active"] = False
                # El mito se ha roto
            else:
                # Mantener piso de carga para los símbolos colectivos correspondientes
                field.symbols["heroe"] = max(field.symbols["heroe"], 0.50)
                field.symbols["sombra"] = max(field.symbols["sombra"], 0.40)
            return

        # 2. Intentar cristalizar "Héroe vs Monstruo"
        if field.symbols.get("heroe", 0.0) > 0.75 and field.symbols.get("sombra", 0.0) > 0.65:
            hero_candidates = []
            monster_candidates = []

            for agent in agents.values():
                if not agent.is_alive:
                    continue
                dom = agent.archetypes.dominant()
                # Verificar valores de arquetipo por encima de 0.80
                if dom == "heroe" and getattr(agent.archetypes, "heroe", 0.0) > 0.80:
                    hero_candidates.append(agent)
                if dom == "sombra" and getattr(agent.archetypes, "sombra", 0.0) > 0.80:
                    monster_candidates.append(agent)

            if hero_candidates and monster_candidates:
                # Seleccionar los agentes con los vectores arquetípicos más cargados
                best_hero = max(hero_candidates, key=lambda a: getattr(a.archetypes, "heroe", 0.0))
                best_monster = max(monster_candidates, key=lambda a: getattr(a.archetypes, "sombra", 0.0))

                self.active_myths.append({
                    "name": "heroe_vs_monstruo",
                    "active": True,
                    "day_crystallized": dia,
                    "hero_id": best_hero.id,
                    "monster_id": best_monster.id,
                })

                # Piso de carga inmediato para consolidar el mito
                field.symbols["heroe"] = max(field.symbols["heroe"], 0.50)
                field.symbols["sombra"] = max(field.symbols["sombra"], 0.40)

    def apply_myth_effects(self, agents: dict[str, Agent]) -> None:
        """Aplica las penalizaciones y bonificaciones psicológicas de los mitos activos."""
        for myth in self.active_myths:
            if not myth.get("active", False):
                continue

            if myth.get("name") == "heroe_vs_monstruo":
                hero_id = myth["hero_id"]
                monster_id = myth["monster_id"]

                # Bonificaciones psicológicas al héroe
                if hero_id in agents and agents[hero_id].is_alive:
                    hero = agents[hero_id]
                    hero.humor = min(1.0, hero.humor + 0.05)
                    hero.ansiedad = max(0.0, hero.ansiedad - 0.05)

                # Penalizaciones psicológicas al chivo expiatorio/monstruo
                if monster_id in agents and agents[monster_id].is_alive:
                    monster = agents[monster_id]
                    monster.ansiedad = min(1.0, monster.ansiedad + 0.08)
                    monster.humor = max(0.0, monster.humor - 0.05)

    def is_myth_active(self, myth_name: str) -> bool:
        """Verifica si un mito específico está activo en la simulación."""
        return any(m.get("name") == myth_name and m.get("active", False) for m in self.active_myths)

    def get_myth_hero_monster(self) -> tuple[str | None, str | None]:
        """Obtiene las IDs del héroe y del monstruo activos, si existen."""
        for myth in self.active_myths:
            if myth.get("name") == "heroe_vs_monstruo" and myth.get("active", False):
                return myth["hero_id"], myth["monster_id"]
        return None, None

    # ── Serialización ─────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "active_myths": [dict(m) for m in self.active_myths]
        }

    @classmethod
    def from_dict(cls, data: dict) -> MythologyEngine:
        engine = cls()
        engine.active_myths = [dict(m) for m in data.get("active_myths", [])]
        return engine
