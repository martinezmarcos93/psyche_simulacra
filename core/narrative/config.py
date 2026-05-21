"""Configuración del módulo narrativo. Todas las opciones son sobreescribibles
por variables de entorno."""
import os

OLLAMA_BASE_URL    = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL       = os.environ.get("OLLAMA_MODEL",    "llama3.2")
OLLAMA_TIMEOUT     = int(os.environ.get("OLLAMA_TIMEOUT", "120"))
NARRATIVE_ENABLED  = os.environ.get("NARRATIVE_ENABLED", "1").strip() not in ("0", "false", "no")
