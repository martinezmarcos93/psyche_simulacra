"""
Neuron — la unidad del MentalVault (Ecuación Personal, Fase 2).

Una neurona es un *concepto perceptivo* que el agente fue precipitando. Sus slots
de contenido nacen vacíos: `arquetipo_resonante` es `None` hasta que la neurona
resuena con un símbolo que YA cristalizó en el campo colectivo. Ningún clasificador
del diseñador le asigna significado — emerge por resonancia, igual que un mito.

`significante` es solo la categoría *física* del estímulo que la originó (la misma
taxonomía content-free de Stimulus.kind): no es un juicio ni un símbolo.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Neuron:
    id:                str
    significante:      str                       # categoría física del estímulo (no juicio)
    estado_energetico: float = 0.0               # 0..1 — decae; se refuerza al re-activarse
    carga_afectiva:    float = 0.0               # -1..1 — tono afectivo (EMA de valence)
    enlaces:           dict = field(default_factory=dict)  # {neuron_id: peso} — adyacencia simple
    arquetipo_resonante: str | None = None       # EMERGE del campo; nace None
    resonance_accum:   dict = field(default_factory=dict)  # {arquetipo: activación acumulada}
    tags:              list = field(default_factory=list)   # categorías físicas, no juicios

    def to_dict(self) -> dict:
        return {
            "id":                  self.id,
            "significante":        self.significante,
            "estado_energetico":   self.estado_energetico,
            "carga_afectiva":      self.carga_afectiva,
            "enlaces":             dict(self.enlaces),
            "arquetipo_resonante": self.arquetipo_resonante,
            "resonance_accum":     dict(self.resonance_accum),
            "tags":                list(self.tags),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Neuron":
        return cls(
            id                  = data["id"],
            significante        = data.get("significante", data["id"]),
            estado_energetico   = float(data.get("estado_energetico", 0.0)),
            carga_afectiva      = float(data.get("carga_afectiva", 0.0)),
            enlaces             = {k: float(v) for k, v in data.get("enlaces", {}).items()},
            arquetipo_resonante = data.get("arquetipo_resonante"),
            resonance_accum     = {k: float(v) for k, v in data.get("resonance_accum", {}).items()},
            tags                = list(data.get("tags", [])),
        )
