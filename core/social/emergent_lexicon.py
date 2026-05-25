"""
R5-A4: Lenguaje emergente — proto-vocabulario tribal.

Cuando un símbolo domina el campo colectivo de una tribu durante suficiente
tiempo, la tribu le asigna un nombre fonético. Ese nombre estabiliza el símbolo
(naming → myth consolidation) y diverge entre tribus, creando identidad cultural.

Las palabras pueden transferirse en contacto inter-tribal con mutaciones.
"""
from __future__ import annotations

import random as _random

_SILABAS = ["ka", "ta", "ma", "na", "ra", "la", "da", "ba", "sa", "ha",
            "ko", "mo", "ro", "lo", "do", "bo", "so", "ho",
            "ki", "mi", "ri", "li", "di", "bi", "si", "hi"]

_NAMING_DAYS   = 30    # días con símbolo dominante antes de que reciba nombre
_NAMING_THRESH = 0.55  # nivel mínimo del símbolo en el campo para contar
_SPREAD_PROB   = 0.15  # probabilidad de adoptar la palabra de otra tribu en contacto
_MYTH_BOOST    = 0.010 # boost diario al myth_pressure del símbolo nombrado


def _random_word(rng, length: int = 2) -> str:
    return "".join(rng.choice(_SILABAS) for _ in range(length))


class TribalLexicon:
    """Vocabulario simbólico de una tribu."""

    def __init__(self, tribe_id: str, seed: int = 0) -> None:
        self.tribe_id      = tribe_id
        self._rng          = _random.Random(seed)
        # arch_name → palabra tribal (e.g., "heroe" → "kama")
        self.words:        dict[str, str] = {}
        # arch_name → días consecutivos como símbolo dominante
        self._streak:      dict[str, int] = {}

    def on_day(self, dominant_arch: str, arch_level: float) -> str | None:
        """
        Avanza el contador de racha para el símbolo dominante.
        Si se cumple el umbral, genera un nombre nuevo.
        Devuelve el nombre generado (o None si aún no hay nombramiento).
        """
        if arch_level < _NAMING_THRESH:
            self._streak.pop(dominant_arch, None)
            return None

        streak = self._streak.get(dominant_arch, 0) + 1
        self._streak[dominant_arch] = streak

        if streak >= _NAMING_DAYS and dominant_arch not in self.words:
            word = _random_word(self._rng)
            self.words[dominant_arch] = word
            return word
        return None

    def adopt(self, arch: str, foreign_word: str) -> bool:
        """Adopta la palabra de otra tribu si la propia no tiene nombre para ese arq."""
        if arch in self.words:
            return False
        if self._rng.random() >= _SPREAD_PROB:
            return False
        # Mutación fonética: 30% de probabilidad de alterar la primera sílaba
        if self._rng.random() < 0.30 and len(foreign_word) >= 2:
            mutated = _random_word(self._rng, 1) + foreign_word[2:]
            self.words[arch] = mutated
        else:
            self.words[arch] = foreign_word
        return True

    def myth_boost(self) -> dict[str, float]:
        """Boost de myth_pressure para cada símbolo que tiene nombre."""
        return {arch: _MYTH_BOOST for arch in self.words}

    def to_dict(self) -> dict:
        return {
            "tribe_id": self.tribe_id,
            "words":    dict(self.words),
            "streak":   dict(self._streak),
        }

    @classmethod
    def from_dict(cls, data: dict, seed: int = 0) -> "TribalLexicon":
        lex = cls(data["tribe_id"], seed)
        lex.words  = dict(data.get("words",  {}))
        lex._streak = {k: int(v) for k, v in data.get("streak", {}).items()}
        return lex


class EmergentLexiconSystem:
    """
    Gestiona los léxicos de todas las tribus.
    Se llama desde AgentCore.on_day() después de los campos tribales.
    """

    def __init__(self) -> None:
        self._lexicons: dict[str, TribalLexicon] = {}

    def get_or_create(self, tribe_id: str, seed: int = 0) -> TribalLexicon:
        if tribe_id not in self._lexicons:
            self._lexicons[tribe_id] = TribalLexicon(tribe_id, seed)
        return self._lexicons[tribe_id]

    def get(self, tribe_id: str) -> TribalLexicon | None:
        return self._lexicons.get(tribe_id)

    def on_day(
        self,
        tribe_fields:  dict,    # tribe_id → CollectiveField (local)
        cultural_memories: dict,# tribe_id → CulturalMemory
        dia: int,
    ) -> list[dict]:
        """
        Procesa un día de evolución lingüística para todas las tribus.
        Devuelve eventos de nombramiento (para registro cultural).
        """
        events: list[dict] = []

        for tribe_id, lf in tribe_fields.items():
            lex = self.get_or_create(tribe_id, seed=hash(tribe_id) % 10000)

            dominant, _ = lf.dominant_archetype_pair()
            arch_level   = lf.symbols.get(dominant, 0.0)
            new_word = lex.on_day(dominant, arch_level)
            if new_word is not None:
                events.append({
                    "tribe_id": tribe_id,
                    "arch":     dominant,
                    "word":     new_word,
                    "dia":      dia,
                })
                # Registrar en memoria cultural
                cmem = cultural_memories.get(tribe_id)
                if cmem is not None:
                    cmem.record_event(
                        dia                 = dia,
                        agente_nombre       = "colectivo",
                        arquetipo_dominante = dominant,
                        tipo_evento         = "palabra_emergente",
                        descripcion         = (
                            f"La tribu nombra '{dominant}' con la palabra "
                            f"'{new_word}' tras {_NAMING_DAYS} días de resonancia."
                        ),
                        intensidad          = 0.50,
                    )

            # Boost de myth_pressure para símbolos nombrados
            for arch, boost in lex.myth_boost().items():
                if arch in lf.symbols:
                    lf.myth_pressure = min(1.0, lf.myth_pressure + boost * 0.3)

        return events

    def spread_across_tribes(
        self,
        tribe_a: str,
        tribe_b: str,
    ) -> list[str]:
        """
        Contacto inter-tribal → palabras pueden transferirse entre lexicones.
        Devuelve lista de arquetipos adoptados.
        """
        adopted: list[str] = []
        lex_a = self.get(tribe_a)
        lex_b = self.get(tribe_b)
        if lex_a is None or lex_b is None:
            return adopted

        for arch, word in list(lex_a.words.items()):
            if lex_b.adopt(arch, word):
                adopted.append(arch)
        for arch, word in list(lex_b.words.items()):
            if lex_a.adopt(arch, word):
                adopted.append(arch)
        return adopted

    def to_dict(self) -> dict:
        return {
            tid: lex.to_dict()
            for tid, lex in self._lexicons.items()
        }

    @classmethod
    def from_dict(cls, data: dict) -> "EmergentLexiconSystem":
        els = cls()
        for tid, ld in data.items():
            els._lexicons[tid] = TribalLexicon.from_dict(ld, seed=hash(tid) % 10000)
        return els
