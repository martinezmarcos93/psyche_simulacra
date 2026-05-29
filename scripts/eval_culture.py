"""
eval_culture.py — Evaluador de riqueza cultural (Roadmap 7, G2).

Carga el checkpoint más reciente y calcula un score 0-100 basado en:
  - Nacimientos registrados en CulturalMemory
  - Proto-mitos activos y mitos cristalizados
  - Estructuras culturales activas
  - Eventos totales en CulturalMemory
  - Generaciones vivas simultáneamente

Uso:
    python scripts/eval_culture.py
    python scripts/eval_culture.py --checkpoint data/checkpoints/latest.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def _load_checkpoint(path: Path | None) -> dict:
    if path is not None:
        with open(path) as f:
            return json.load(f)

    # Buscar el checkpoint más reciente automáticamente
    ckpt_dir = ROOT / "data" / "checkpoints"
    if not ckpt_dir.exists():
        sys.exit("No se encontró data/checkpoints/. Ejecutá la simulación primero.")

    files = sorted(ckpt_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        sys.exit("No hay checkpoints en data/checkpoints/.")

    print(f"Usando checkpoint: {files[0]}")
    with open(files[0]) as f:
        return json.load(f)


def _count_births(cultural_memories: list[dict]) -> int:
    count = 0
    for cm in cultural_memories:
        for rec in cm.get("records", []):
            if rec.get("tipo_evento") == "nacimiento":
                count += 1
    return count


def _count_constructions(cultural_memories: list[dict]) -> int:
    count = 0
    for cm in cultural_memories:
        for rec in cm.get("records", []):
            if rec.get("tipo_evento") == "construccion":
                count += 1
    return count


def _count_cultural_events(cultural_memories: list[dict]) -> int:
    return sum(len(cm.get("records", [])) for cm in cultural_memories)


def _count_generations(agents: list[dict]) -> int:
    """Aproxima generaciones vivas como 1 + (rango de edades / 30)."""
    alive_ages = [a.get("edad", 0) for a in agents if a.get("is_alive", False)]
    if not alive_ages:
        return 0
    age_range = max(alive_ages) - min(alive_ages)
    return max(1, 1 + age_range // 30)


def evaluate(data: dict) -> dict:
    agent_core = data.get("agent_core", data)

    agents: list[dict] = list(agent_core.get("agents", {}).values())

    myth_data = agent_core.get("mythology_engine", {})
    proto_myths   = myth_data.get("proto_myths", [])
    active_myths  = [m for m in myth_data.get("active_myths", []) if m.get("active")]
    legends       = [m for m in myth_data.get("active_myths", []) if m.get("es_leyenda")]

    tribe_mem_raw = agent_core.get("tribe_manager", {}).get("cultural_memories", {})
    cultural_memories: list[dict] = list(tribe_mem_raw.values()) if isinstance(tribe_mem_raw, dict) else []

    culture_structures = agent_core.get("culture_engine", {}).get("structures", [])

    n_births       = _count_births(cultural_memories)
    n_proto        = len(proto_myths)
    n_crystal      = len(active_myths)
    n_legends      = len(legends)
    n_structures   = len(culture_structures)
    n_constructions = _count_constructions(cultural_memories)
    n_events       = _count_cultural_events(cultural_memories)
    n_generations  = _count_generations(agents)
    n_alive        = sum(1 for a in agents if a.get("is_alive", False))

    # Puntaje parcial por categoría (cada una aporta hasta 20 puntos)
    score_births       = min(20, n_births * 4)
    score_myths        = min(20, n_crystal * 6 + n_proto * 2 + n_legends * 3)
    score_structures   = min(20, n_structures * 1 + n_constructions * 0.5)
    score_events       = min(20, n_events * 0.2)
    score_generations  = min(20, (n_generations - 1) * 10)

    total = score_births + score_myths + score_structures + score_events + score_generations

    return {
        "agentes_vivos":      n_alive,
        "nacimientos":        n_births,
        "proto_mitos":        n_proto,
        "mitos_cristalizados": n_crystal,
        "leyendas":           n_legends,
        "estructuras_activas": n_structures,
        "construcciones_registradas": n_constructions,
        "eventos_culturales": n_events,
        "generaciones_estimadas": n_generations,
        "score_births":       round(score_births, 1),
        "score_myths":        round(score_myths, 1),
        "score_structures":   round(score_structures, 1),
        "score_events":       round(score_events, 1),
        "score_generations":  round(score_generations, 1),
        "score_total":        round(total, 1),
    }


def _print_table(result: dict) -> None:
    print("\n" + "=" * 52)
    print("  EVALUACIÓN DE RIQUEZA CULTURAL — Roadmap 7")
    print("=" * 52)
    rows = [
        ("Agentes vivos",              result["agentes_vivos"],            "—"),
        ("Nacimientos",                result["nacimientos"],              f"{result['score_births']}/20"),
        ("Proto-mitos activos",        result["proto_mitos"],              "—"),
        ("Mitos cristalizados",        result["mitos_cristalizados"],      f""),
        ("Leyendas",                   result["leyendas"],                 f"{result['score_myths']}/20"),
        ("Estructuras activas",        result["estructuras_activas"],      "—"),
        ("Construcciones (memoria)",   result["construcciones_registradas"], f"{result['score_structures']}/20"),
        ("Eventos culturales totales", result["eventos_culturales"],       f"{result['score_events']}/20"),
        ("Generaciones vivas (est.)",  result["generaciones_estimadas"],   f"{result['score_generations']}/20"),
    ]
    for label, value, pts in rows:
        pts_str = f"  [{pts}]" if pts and pts != "—" else ""
        print(f"  {label:<30} {str(value):>6}{pts_str}")
    print("-" * 52)
    score = result["score_total"]
    grade = "EXCELENTE" if score >= 80 else "BUENO" if score >= 60 else "REGULAR" if score >= 40 else "BAJO"
    print(f"  SCORE TOTAL: {score:>5.1f} / 100   → {grade}")
    print("=" * 52 + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evalúa riqueza cultural del checkpoint")
    parser.add_argument("--checkpoint", type=Path, default=None)
    args = parser.parse_args()

    data = _load_checkpoint(args.checkpoint)
    result = evaluate(data)
    _print_table(result)


if __name__ == "__main__":
    main()
