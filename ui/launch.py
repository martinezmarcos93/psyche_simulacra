#!/usr/bin/env python3
"""
ui/launch.py — Punto de entrada alternativo para la interfaz NiceGUI.

Equivalente a ejecutar main.py pero sin el chequeo de Ollama.
Útil para lanzar la UI directamente en desarrollo.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))


def main() -> None:
    from ui.app_state import state
    from ui.psyche_ui import launch_ui
    launch_ui(state)


if __name__ == "__main__":
    main()
