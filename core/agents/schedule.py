from __future__ import annotations

# Default hourly schedule: hora 0-23 → activity
_DEFAULT_SCHEDULE: dict[int, str] = {
    0:  "dormir", 1:  "dormir", 2:  "dormir", 3:  "dormir",
    4:  "dormir", 5:  "dormir",
    6:  "buscar_agua",
    7:  "buscar_alimento", 8:  "buscar_alimento", 9:  "buscar_alimento",
    10: "buscar_alimento", 11: "buscar_alimento",
    12: "descansar",
    13: "interactuar",
    14: "buscar_alimento", 15: "buscar_alimento", 16: "buscar_alimento",
    17: "explorar",
    18: "interactuar", 19: "interactuar",
    20: "descansar", 21: "descansar",
    22: "dormir", 23: "dormir",
}

# Role overrides — only the hours that differ from default
_ROLE_OVERRIDES: dict[str, dict[int, str]] = {
    "cazador": {
        7: "cazar", 8: "cazar", 9: "cazar", 14: "cazar", 15: "cazar",
    },
    "explorador": {
        7: "explorar", 8: "explorar", 9: "explorar", 17: "explorar",
    },
    "recolector": {
        # default is already buscar_alimento-heavy; no change needed
    },
    "guardian": {
        6: "interactuar", 13: "descansar", 18: "buscar_alimento",
    },
}


class ScheduleSystem:
    def __init__(self, rol: str = "generico") -> None:
        self.rol = rol
        overrides = _ROLE_OVERRIDES.get(rol, {})
        self._schedule: dict[int, str] = {**_DEFAULT_SCHEDULE, **overrides}

    def get_activity(self, hora: int) -> str:
        return self._schedule.get(hora % 24, "descansar")

    def adjust_for_season(self, estacion: str) -> None:
        """Placeholder — season-based schedule adjustments come in Phase 6."""
        pass

    def to_dict(self) -> dict:
        return {"rol": self.rol}

    @classmethod
    def from_dict(cls, data: dict) -> ScheduleSystem:
        return cls(rol=data.get("rol", "generico"))
