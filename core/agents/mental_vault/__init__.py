"""
MentalVault — el mini cerebro por agente (Ecuación Personal, Fase 2).

El inconsciente personal emerge por la misma física que el colectivo, una escala más
abajo: auto-similaridad fractal del colapso. Ver ROADMAP_ECUACION_PERSONAL.md (Fase 2).
"""
from .neuron import Neuron
from .mental_vault import MentalVault, neuron_id

__all__ = ["MentalVault", "Neuron", "neuron_id"]
