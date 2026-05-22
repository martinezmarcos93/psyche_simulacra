"""
OllamaDaemon — gestor del proceso local de Ollama.

Fase 6 del ROADMAP2: garantizar que Ollama corre automáticamente y que
el modelo configurado está instalado antes de iniciar la simulación.

Tres responsabilidades:
    1. Detectar si ollama serve está activo en localhost:11434.
    2. Si no está activo, arrancarlo como proceso hijo desacoplado.
    3. Verificar que el modelo configurado está instalado;
       ejecutar ollama pull si no lo está (bloqueante, con aviso al usuario).
"""

from __future__ import annotations

import json
import logging
import subprocess
import sys
import time
import urllib.request

from .config import OLLAMA_BASE_URL, OLLAMA_MODEL, NARRATIVE_ENABLED

logger = logging.getLogger(__name__)

_STARTUP_TIMEOUT_S = 12   # segundos máximos esperando a que el daemon arranque
_STARTUP_POLL_S    = 0.5  # intervalo de polling durante el arranque


class OllamaDaemon:
    """
    Gestor del daemon de Ollama para PSYCHE SIMULACRA.

    Uso típico (en run_simulation.py / visualizer.py, antes de crear el runner):

        from core.narrative.daemon import OllamaDaemon
        OllamaDaemon().setup()
    """

    def __init__(
        self,
        base_url: str = OLLAMA_BASE_URL,
        model:    str = OLLAMA_MODEL,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model    = model
        self._proc: subprocess.Popen | None = None

    # ── API pública ────────────────────────────────────────────────────────────

    def setup(self) -> bool:
        """
        Ciclo completo: asegura daemon corriendo + modelo instalado.

        Returns:
            True si Ollama está listo, False si hubo error (narrativa usará fallback).
        """
        if not NARRATIVE_ENABLED:
            return False

        if not self.ensure_running():
            logger.warning("Ollama no pudo arrancar — narrativa usará fallback")
            return False

        if not self.ensure_model():
            logger.warning("Modelo '%s' no disponible — narrativa usará fallback", self.model)
            return False

        return True

    def ensure_running(self) -> bool:
        """
        Verifica que ollama serve esté activo. Si no, lo inicia.

        Returns:
            True si el servidor responde, False si no pudo iniciarse.
        """
        if self._is_alive():
            logger.info("Ollama ya activo en %s", self.base_url)
            return True

        print(f"  [Ollama] No detectado — iniciando 'ollama serve'...")
        self._start_daemon()

        deadline = time.monotonic() + _STARTUP_TIMEOUT_S
        while time.monotonic() < deadline:
            if self._is_alive():
                print(f"  [Ollama] Daemon activo en {self.base_url}")
                return True
            time.sleep(_STARTUP_POLL_S)

        print(f"  [Ollama] Timeout esperando al daemon ({_STARTUP_TIMEOUT_S}s) — continuando sin Ollama")
        return False

    def ensure_model(self) -> bool:
        """
        Verifica que el modelo esté instalado. Si no, ejecuta ollama pull.

        Returns:
            True si el modelo está listo, False si no pudo instalarse.
        """
        if self._model_installed():
            logger.info("Modelo '%s' disponible", self.model)
            return True

        print(f"  [Ollama] Modelo '{self.model}' no encontrado — iniciando descarga...")
        print(f"  [Ollama] Esto puede tardar varios minutos la primera vez.")
        try:
            subprocess.run(["ollama", "pull", self.model], check=True)
            print(f"  [Ollama] Modelo '{self.model}' instalado correctamente.")
            return True
        except subprocess.CalledProcessError as exc:
            print(f"  [Ollama] Error al descargar modelo: {exc}")
            return False
        except FileNotFoundError:
            print("  [Ollama] Comando 'ollama' no encontrado en PATH.")
            return False

    # ── Métodos internos ───────────────────────────────────────────────────────

    def _is_alive(self) -> bool:
        """Verifica si el servidor responde en el puerto configurado."""
        try:
            with urllib.request.urlopen(f"{self.base_url}/api/tags", timeout=2):
                return True
        except Exception:
            return False

    def _model_installed(self) -> bool:
        """Verifica si el modelo aparece en la lista de modelos instalados."""
        try:
            with urllib.request.urlopen(f"{self.base_url}/api/tags", timeout=5) as resp:
                data   = json.loads(resp.read().decode("utf-8"))
                models = [m.get("name", "") for m in data.get("models", [])]
                # Coincidencia parcial para manejar tags como "llama3.2:latest"
                return any(self.model in m for m in models)
        except Exception:
            return False

    def _start_daemon(self) -> None:
        """Arranca ollama serve como proceso desacoplado (no bloquea al padre)."""
        try:
            if sys.platform == "win32":
                self._proc = subprocess.Popen(
                    ["ollama", "serve"],
                    creationflags=(
                        subprocess.CREATE_NEW_PROCESS_GROUP
                        | subprocess.DETACHED_PROCESS
                    ),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            else:
                self._proc = subprocess.Popen(
                    ["ollama", "serve"],
                    start_new_session=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
        except FileNotFoundError:
            print("  [Ollama] Comando 'ollama' no encontrado en PATH.")
        except Exception as exc:
            print(f"  [Ollama] No se pudo iniciar el daemon: {exc}")
