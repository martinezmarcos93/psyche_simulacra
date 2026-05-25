from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal


@dataclass
class RuntimeState:
    simulation:   Literal["stopped", "running", "paused", "error"] = "stopped"
    ollama:       Literal["stopped", "starting", "running", "error"] = "stopped"
    liminal:      Literal["stopped", "starting", "running", "error"] = "stopped"
    dia_simulado:   int       = 0
    agentes_vivos:  int       = 0
    tribus_activas: int       = 0
    ultimo_evento:  str       = ""
    timestamp_real: datetime  = field(default_factory=datetime.now)
    sim_session_id: str | None = None

    def to_dict(self) -> dict:
        return {
            "simulation":    self.simulation,
            "ollama":        self.ollama,
            "liminal":       self.liminal,
            "dia_simulado":  self.dia_simulado,
            "agentes_vivos": self.agentes_vivos,
            "tribus_activas": self.tribus_activas,
            "ultimo_evento": self.ultimo_evento,
            "timestamp_real": self.timestamp_real.isoformat(),
            "sim_session_id": self.sim_session_id,
        }
