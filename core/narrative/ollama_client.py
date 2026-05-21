from __future__ import annotations

import json
import logging
import urllib.request
import urllib.error

from .config import OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT

logger = logging.getLogger(__name__)


class OllamaClient:
    """Cliente HTTP mínimo para la API local de Ollama (sin dependencias externas)."""

    def __init__(
        self,
        model:    str = OLLAMA_MODEL,
        base_url: str = OLLAMA_BASE_URL,
        timeout:  int = OLLAMA_TIMEOUT,
    ) -> None:
        self.model    = model
        self.base_url = base_url.rstrip("/")
        self.timeout  = timeout

    def is_available(self) -> bool:
        """Verifica que Ollama esté corriendo y el modelo esté disponible."""
        try:
            with urllib.request.urlopen(f"{self.base_url}/api/tags", timeout=3):
                return True
        except Exception:
            return False

    def generate(self, prompt: str, max_tokens: int = 350) -> str | None:
        """
        Envía el prompt a Ollama y devuelve la respuesta como string.
        Devuelve None si el servidor no está disponible o falla.
        """
        payload = json.dumps({
            "model":  self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": 0.88,
                "top_p":       0.92,
            },
        }).encode("utf-8")

        req = urllib.request.Request(
            url     = f"{self.base_url}/api/generate",
            data    = payload,
            headers = {"Content-Type": "application/json"},
            method  = "POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                text = data.get("response", "").strip()
                return text if text else None
        except urllib.error.URLError as exc:
            logger.warning("Ollama no disponible (%s): %s", self.model, exc)
            return None
        except Exception as exc:
            logger.warning("Error generando narrativa con Ollama: %s", exc)
            return None
