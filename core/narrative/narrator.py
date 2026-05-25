from __future__ import annotations

import logging
import os
import queue
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from .config import NARRATIVE_ENABLED
from .ollama_client import OllamaClient
from . import prompts

if TYPE_CHECKING:
    from core.social.tribe_manager import TribeManager
    from core.social.mythology import MythologyEngine
    from core.agents import Agent

logger = logging.getLogger(__name__)

_TIPOS = ("fundacion", "cronica", "elegia", "profecia")

# Plantillas de fallback cuando Ollama no está disponible
_FALLBACK: dict[str, str] = {
    "fundacion": (
        "En el principio de los tiempos, cuando el mundo era joven y los sueños aún "
        "no tenían nombre, un puñado de almas convergió bajo el signo del {arquetipo}. "
        "El {bioma} los acogió como madre a sus hijos. Así nació esta tribu — "
        "no por voluntad sino por llamado del inconsciente que todo lo une."
    ),
    "cronica":   (
        "Y pasaron los días {dia_inicio} al {dia_fin} como agua entre piedras. "
        "La tribu del {arquetipo} siguió su camino, {n_miembros} almas cargando "
        "el peso del campo colectivo. El símbolo del {simbolo} marcó esta época."
    ),
    "elegia":    (
        "Que el nombre de {nombre} no sea olvidado. {edad} años vivió entre nosotros, "
        "portador del arquetipo {arquetipo}. La {causa} se lo llevó, pero su huella "
        "permanece grabada en el campo colectivo de su tribu."
    ),
    "profecia":  (
        "El inconsciente susurra: donde el {arquetipo} se alza, la sombra lo sigue. "
        "{heroe} y {antagonista} danzan la danza eterna. Lo que fue escrito en el campo "
        "colectivo, se cumplirá — porque los arquetipos no mienten, solo se transforman."
    ),
}


@dataclass
class NarrativeEvent:
    tipo:     str    # "fundacion" | "cronica" | "elegia" | "profecia"
    dia:      int
    tribe_id: str | None
    data:     dict   = field(default_factory=dict)


class NarratorEngine:
    """
    Motor de síntesis narrativa. Corre en un hilo de fondo, genera texto
    con Ollama y lo escribe en vault/Colectivo/Leyendas/.
    Silencioso si Ollama no está disponible (escribe fallback o nada).
    """

    def __init__(self, vault_path: str = "vault") -> None:
        self.enabled       = NARRATIVE_ENABLED
        self.client        = OllamaClient()
        self.leyendas_path = Path(vault_path) / "Colectivo" / "Leyendas"

        self._queue:         queue.Queue[NarrativeEvent] = queue.Queue()
        self._known_tribes:  set[str]                    = set()
        self._known_myths:   set[str]                    = set()  # tribe_id+day
        self._worker:        threading.Thread | None     = None
        self._running:       bool                        = False

    # ── Ciclo de vida ─────────────────────────────────────────────────────────

    def start(self) -> None:
        if not self.enabled:
            return
        self.leyendas_path.mkdir(parents=True, exist_ok=True)
        self._load_known_from_disk()
        self._running = True
        self._worker  = threading.Thread(target=self._process_loop, daemon=True, name="NarratorWorker")
        self._worker.start()
        available = self.client.is_available()
        if available:
            logger.info("NarratorEngine iniciado — modelo: %s", self.client.model)
            print(f"  [Narrador] Activo (Ollama · {self.client.model})")
        else:
            logger.warning("Ollama no disponible — narrativa usara plantillas de fallback")
            print("  [Narrador] Activo (modo fallback — Ollama sin conexion)")

    def stop(self, join_timeout: float = 30.0) -> None:
        self._running = False
        if self._worker is not None:
            self._worker.join(timeout=join_timeout)

    def drain(self, timeout: float = 30.0) -> None:
        """Espera hasta timeout segundos a que se vacíe la cola."""
        import time
        deadline = time.monotonic() + timeout
        while self._queue.unfinished_tasks > 0 and time.monotonic() < deadline:
            time.sleep(0.1)

    # ── Encolado de eventos (llamado desde el hilo principal) ─────────────────

    def on_new_tribe(self, tribe_id: str, dia: int, data: dict) -> None:
        if not self.enabled or tribe_id in self._known_tribes:
            return
        self._known_tribes.add(tribe_id)
        # Solo si no hay ya un mito fundacional para esta tribu en disco
        if not self._legend_exists("fundacion", tribe_id=tribe_id):
            self._queue.put(NarrativeEvent("fundacion", dia, tribe_id, data))

    def on_cronica_day(self, tribe_id: str, dia: int, data: dict) -> None:
        if not self.enabled:
            return
        self._queue.put(NarrativeEvent("cronica", dia, tribe_id, data))

    def on_death(self, agent_id: str, dia: int, data: dict) -> None:
        if not self.enabled:
            return
        if not self._legend_exists("elegia", agent_id=agent_id):
            self._queue.put(NarrativeEvent("elegia", dia, None, {**data, "agent_id": agent_id}))

    def on_myth_crystallized(self, tribe_id: str, dia: int, data: dict) -> None:
        if not self.enabled:
            return
        key = f"{tribe_id}_{dia}"
        if key not in self._known_myths and not self._legend_exists("profecia", tribe_id=tribe_id, dia=dia):
            self._known_myths.add(key)
            self._queue.put(NarrativeEvent("profecia", dia, tribe_id, data))

    # ── Worker loop (hilo de fondo) ───────────────────────────────────────────

    def _process_loop(self) -> None:
        while self._running or not self._queue.empty():
            try:
                event = self._queue.get(timeout=0.5)
            except queue.Empty:
                continue
            try:
                self._process_event(event)
            except Exception as exc:
                logger.warning("Error procesando evento narrativo: %s", exc)
            finally:
                self._queue.task_done()

    def _process_event(self, event: NarrativeEvent) -> None:
        text = self._generate_text(event)
        if text:
            self._write_legend(event, text)

    def _generate_text(self, event: NarrativeEvent) -> str | None:
        d = event.data
        try:
            if event.tipo == "fundacion":
                prompt = prompts.prompt_mito_fundacional(
                    tribe_name = d.get("tribe_name", "tribu"),
                    nombres    = d.get("nombres", []),
                    bioma      = d.get("bioma", "tierra desconocida"),
                    arquetipo  = d.get("arquetipo", "heroe"),
                    simbolos   = d.get("simbolos", {}),
                )
            elif event.tipo == "cronica":
                prompt = prompts.prompt_cronica(
                    tribe_name  = d.get("tribe_name", "tribu"),
                    dia_inicio  = d.get("dia_inicio", 0),
                    dia_fin     = event.dia,
                    n_miembros  = d.get("n_miembros", 0),
                    arquetipo   = d.get("arquetipo", "heroe"),
                    presion     = d.get("presion", 0.0),
                    simbolo_dom = d.get("simbolo_dom", "sombra"),
                    eventos     = d.get("eventos", []),
                )
            elif event.tipo == "elegia":
                prompt = prompts.prompt_elegia(
                    nombre    = d.get("nombre", "el difunto"),
                    edad      = d.get("edad", 0),
                    causa     = d.get("causa", "causas desconocidas"),
                    arquetipo = d.get("arquetipo", "heroe"),
                    tribu     = d.get("tribe_name", "su tribu"),
                    memorias  = d.get("memorias", []),
                )
            elif event.tipo == "profecia":
                prompt = prompts.prompt_profecia(
                    tribe_name  = d.get("tribe_name", "tribu"),
                    arquetipo   = d.get("arquetipo", "heroe"),
                    heroe_nombre  = d.get("heroe_nombre", "el Elegido"),
                    antagonista   = d.get("antagonista", "la Sombra"),
                    presion       = d.get("presion", 0.0),
                    simbolos      = d.get("simbolos", {}),
                )
            else:
                return None
        except Exception as exc:
            logger.warning("Error construyendo prompt '%s': %s", event.tipo, exc)
            return None

        text = self.client.generate(prompt)
        if text:
            return text

        # Fallback de plantilla
        return self._fallback_text(event)

    def _fallback_text(self, event: NarrativeEvent) -> str | None:
        d = event.data
        tmpl = _FALLBACK.get(event.tipo)
        if tmpl is None:
            return None
        try:
            return tmpl.format(
                arquetipo   = d.get("arquetipo", "heroe"),
                bioma       = d.get("bioma", "la tierra"),
                dia_inicio  = d.get("dia_inicio", 0),
                dia_fin     = event.dia,
                n_miembros  = d.get("n_miembros", 0),
                simbolo     = d.get("simbolo_dom", "sombra"),
                nombre      = d.get("nombre", "el difunto"),
                edad        = d.get("edad", 0),
                causa       = d.get("causa", "causas desconocidas"),
                heroe       = d.get("heroe_nombre", "el Elegido"),
                antagonista = d.get("antagonista", "la Sombra"),
            )
        except Exception:
            return None

    # ── Escritura en vault ────────────────────────────────────────────────────

    def _write_legend(self, event: NarrativeEvent, text: str) -> None:
        filename = self._legend_filename(event)
        path     = self.leyendas_path / filename

        tipo_label = {
            "fundacion": "Mito Fundacional",
            "cronica":   "Crónica",
            "elegia":    "Elegía",
            "profecia":  "Profecía",
        }.get(event.tipo, event.tipo.capitalize())

        tribe_str = event.tribe_id or event.data.get("agent_id", "desconocido")

        content = (
            f"---\n"
            f"tipo: {event.tipo}\n"
            f"dia: {event.dia}\n"
            f"tribu: {tribe_str}\n"
            f"---\n"
            f"# 📜 {tipo_label} — Día {event.dia}\n\n"
            f"> *{event.data.get('tribe_name', tribe_str)}*\n\n"
            f"---\n\n"
            f"{text}\n"
        )
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            logger.info("Leyenda escrita: %s", filename)
            print(f"  [Leyenda] {filename}")
        except Exception as exc:
            logger.warning("No se pudo escribir leyenda %s: %s", filename, exc)

    def _legend_filename(self, event: NarrativeEvent) -> str:
        if event.tipo == "elegia":
            key = event.data.get("agent_id", "desconocido")
        else:
            key = event.tribe_id or "global"
        return f"dia_{event.dia:05d}_{event.tipo}_{key}.md"

    def _legend_exists(
        self,
        tipo:     str,
        tribe_id: str | None = None,
        agent_id: str | None = None,
        dia:      int | None = None,
    ) -> bool:
        if not self.leyendas_path.exists():
            return False
        if agent_id:
            return any(self.leyendas_path.glob(f"*_{tipo}_{agent_id}.md"))
        if tribe_id and dia is not None:
            return (self.leyendas_path / f"dia_{dia:05d}_{tipo}_{tribe_id}.md").exists()
        if tribe_id:
            return any(self.leyendas_path.glob(f"*_{tipo}_{tribe_id}.md"))
        return False

    def _load_known_from_disk(self) -> None:
        """Carga el estado de leyendas ya generadas para no duplicar."""
        if not self.leyendas_path.exists():
            return
        for f in self.leyendas_path.glob("*.md"):
            parts = f.stem.split("_")
            if len(parts) >= 3:
                tipo     = parts[2] if len(parts) > 2 else ""
                tribe_id = "_".join(parts[3:]) if len(parts) > 3 else ""
                if tipo == "fundacion" and tribe_id:
                    self._known_tribes.add(tribe_id)
