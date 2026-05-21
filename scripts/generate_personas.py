#!/usr/bin/env python3
"""
Genera archivos YAML de agentes para PSYCHE SIMULACRA.

Uso:
    python scripts/generate_personas.py               # 100 agentes, seed=42
    python scripts/generate_personas.py --n 50        # 50 agentes
    python scripts/generate_personas.py --seed 7      # semilla distinta
    python scripts/generate_personas.py --output data/seeds/mi_grupo.yaml
"""
from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

try:
    import yaml
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyyaml", "-q"])
    import yaml

# ── Banco de nombres ──────────────────────────────────────────────────────────

_NOMBRES_M = [
    "Theron", "Damon", "Xanthos", "Phoibos", "Creon", "Ixion", "Argos",
    "Tycho", "Demos", "Orion", "Pyrros", "Cadmus", "Evander", "Medon",
    "Alcis", "Boreas", "Cephalos", "Doros", "Euthys", "Festus", "Galen",
    "Hector", "Idris", "Kyron", "Lykos", "Meleager", "Narkis", "Okaios",
    "Pallas", "Rhadys", "Skiros", "Talos", "Vergil", "Yaron", "Zylas",
    "Adras", "Brennus", "Cimber", "Durus", "Exan", "Feros", "Garan",
    "Hakon", "Isidor", "Kimon", "Lakon", "Macron", "Nauplius", "Perion",
    "Ristos", "Stenos", "Ulax", "Wulfar", "Xeron", "Bron", "Calix",
    "Drex", "Heron", "Ivar", "Kress",
]

_NOMBRES_F = [
    "Alethea", "Brysis", "Calyce", "Desma", "Eudora", "Phoibe", "Glaukia",
    "Hestia", "Iambe", "Kalliope", "Lachesis", "Meroe", "Nausicaa",
    "Oinone", "Prokne", "Rheia", "Selene", "Tainis", "Uritha", "Vespa",
    "Xanthe", "Ysolde", "Zephyra", "Aglaia", "Brenna", "Cyrene", "Daphne",
    "Erytheis", "Galatia", "Helice", "Idaea", "Jocasta", "Kleis", "Lyris",
    "Myrrha", "Nephele", "Omphale", "Persis", "Renia", "Skylla", "Thalia",
    "Ursa", "Velia", "Xaria", "Zoia", "Althaia", "Barea", "Cyma", "Decia",
    "Elara", "Fyria", "Graia", "Helia", "Imene", "Jora", "Karis",
    "Lysane", "Malia", "Neria", "Oris", "Peria",
]

# ── Plantillas arquetípicas ───────────────────────────────────────────────────
# Los 12 atributos del ArchetypeVector (se usa "self_" como clave YAML directa)

_ARCH_ATTRS = [
    "self_", "persona", "sombra", "anima_animus", "heroe", "sabio",
    "trickster", "madre", "padre", "nino_divino", "gobernante", "rebelde",
]

_TEMPLATES: dict[str, dict[str, float]] = {
    "heroe":       {"heroe": 0.85, "gobernante": 0.55, "padre": 0.45, "sombra": 0.25, "sabio": 0.38},
    "sombra":      {"sombra": 0.85, "trickster": 0.50, "rebelde": 0.42, "heroe": 0.18, "persona": 0.28},
    "madre":       {"madre": 0.85, "anima_animus": 0.55, "sabio": 0.38, "nino_divino": 0.42, "self_": 0.45},
    "padre":       {"padre": 0.82, "gobernante": 0.62, "sabio": 0.45, "heroe": 0.42, "persona": 0.50},
    "sabio":       {"sabio": 0.88, "self_": 0.62, "anima_animus": 0.50, "nino_divino": 0.35, "persona": 0.45},
    "trickster":   {"trickster": 0.85, "sombra": 0.48, "rebelde": 0.55, "persona": 0.42, "anima_animus": 0.38},
    "gobernante":  {"gobernante": 0.88, "padre": 0.62, "heroe": 0.50, "sombra": 0.35, "persona": 0.55},
    "rebelde":     {"rebelde": 0.85, "sombra": 0.52, "trickster": 0.42, "heroe": 0.38, "anima_animus": 0.45},
    "nino_divino": {"nino_divino": 0.82, "madre": 0.50, "self_": 0.48, "heroe": 0.35, "anima_animus": 0.40},
    "promedio":    {},
}

_TEMPLATE_COUNTS: dict[str, int] = {
    "heroe": 10, "sombra": 8, "madre": 10, "padre": 8,
    "sabio": 8, "trickster": 5, "gobernante": 7,
    "rebelde": 5, "nino_divino": 5, "promedio": 34,
}  # total = 100

_BIG5_BASES: dict[str, dict[str, float]] = {
    "heroe":      {"apertura": 0.65, "responsabilidad": 0.75, "extraversion": 0.72, "amabilidad": 0.55, "neuroticismo": 0.30},
    "sombra":     {"apertura": 0.42, "responsabilidad": 0.30, "extraversion": 0.38, "amabilidad": 0.20, "neuroticismo": 0.78},
    "madre":      {"apertura": 0.62, "responsabilidad": 0.78, "extraversion": 0.58, "amabilidad": 0.82, "neuroticismo": 0.28},
    "padre":      {"apertura": 0.50, "responsabilidad": 0.82, "extraversion": 0.55, "amabilidad": 0.60, "neuroticismo": 0.25},
    "sabio":      {"apertura": 0.90, "responsabilidad": 0.72, "extraversion": 0.42, "amabilidad": 0.75, "neuroticismo": 0.22},
    "trickster":  {"apertura": 0.85, "responsabilidad": 0.32, "extraversion": 0.78, "amabilidad": 0.45, "neuroticismo": 0.48},
    "gobernante": {"apertura": 0.50, "responsabilidad": 0.85, "extraversion": 0.70, "amabilidad": 0.52, "neuroticismo": 0.28},
    "rebelde":    {"apertura": 0.78, "responsabilidad": 0.35, "extraversion": 0.62, "amabilidad": 0.38, "neuroticismo": 0.55},
    "nino_divino":{"apertura": 0.70, "responsabilidad": 0.45, "extraversion": 0.55, "amabilidad": 0.78, "neuroticismo": 0.40},
    "promedio":   {"apertura": 0.55, "responsabilidad": 0.58, "extraversion": 0.52, "amabilidad": 0.60, "neuroticismo": 0.42},
}

# ── Helpers de generación ─────────────────────────────────────────────────────

def _jitter(val: float, sigma: float, rng: random.Random) -> float:
    return round(min(1.0, max(0.05, val + rng.gauss(0, sigma))), 3)


def _gen_arquetipos(template: str, rng: random.Random) -> dict[str, float]:
    base = _TEMPLATES.get(template, {})
    result: dict[str, float] = {}
    for attr in _ARCH_ATTRS:
        if attr in base:
            result[attr] = _jitter(base[attr], 0.06, rng)
        elif template == "promedio":
            result[attr] = round(rng.uniform(0.28, 0.55), 3)
        else:
            result[attr] = round(rng.uniform(0.15, 0.42), 3)
    return result


def _gen_big5(template: str, rng: random.Random) -> dict[str, float]:
    base = _BIG5_BASES.get(template, _BIG5_BASES["promedio"])
    return {k: _jitter(base[k], 0.07, rng) for k in base}


def _gen_age(template: str, rng: random.Random) -> int:
    if template == "nino_divino":
        return rng.randint(8, 20)
    if template in ("sabio", "padre", "gobernante"):
        return rng.randint(30, 62)
    if template == "madre":
        return rng.randint(22, 55)
    return rng.randint(14, 52)


def _gen_position(rng: random.Random) -> list[int]:
    """Agentes en anillo alrededor del centro (40,30); radio 8-14."""
    q = rng.randint(26, 54)
    r = rng.randint(18, 42)
    return [q, r]


# ── Función principal ─────────────────────────────────────────────────────────

def generate(n: int = 100, seed: int = 42) -> list[dict]:
    rng = random.Random(seed)

    # Construir lista de plantillas
    templates: list[str] = []
    for tmpl, count in _TEMPLATE_COUNTS.items():
        templates.extend([tmpl] * count)
    rng.shuffle(templates)
    templates = templates[:n]

    # Pools de nombres (sexo)
    nombres_m = list(_NOMBRES_M); rng.shuffle(nombres_m)
    nombres_f = list(_NOMBRES_F); rng.shuffle(nombres_f)

    # Distribución de roles
    role_pool = (
        ["cazador"] * 15 + ["recolector"] * 25 + ["explorador"] * 12
        + ["guardian"] * 13 + ["generico"] * 35
    )
    rng.shuffle(role_pool)

    # Asignación de sexo: madre→F, padre→M, resto ~50/50
    sexo_extra_m = 42   # para alcanzar ~50 M total (8 padre + 42)
    sexo_extra_f = 40   # para alcanzar ~50 F total (10 madre + 40)

    agents: list[dict] = []
    used_ids: set[str] = set()
    extra_m = sexo_extra_m
    extra_f = sexo_extra_f

    for i, tmpl in enumerate(templates):
        if tmpl == "madre":
            sexo = "F"
        elif tmpl == "padre":
            sexo = "M"
        elif extra_m > 0 and (extra_f == 0 or rng.random() < 0.5):
            sexo = "M"
            extra_m -= 1
        else:
            sexo = "F"
            extra_f -= 1

        if sexo == "M" and nombres_m:
            nombre = nombres_m.pop()
        elif sexo == "F" and nombres_f:
            nombre = nombres_f.pop()
        else:
            nombre = f"Anon{i + 1:03d}"

        agent_id = nombre.lower()
        # Garantizar unicidad
        suffix = 1
        base_id = agent_id
        while agent_id in used_ids:
            agent_id = f"{base_id}_{suffix}"
            suffix += 1
        used_ids.add(agent_id)

        edad = _gen_age(tmpl, rng)
        rol  = role_pool[i % len(role_pool)]
        if edad < 16:
            rol = "generico"

        agents.append({
            "id":        agent_id,
            "nombre":    nombre,
            "edad":      edad,
            "sexo":      sexo,
            "rol":       rol,
            "posicion":  _gen_position(rng),
            "arquetipos": _gen_arquetipos(tmpl, rng),
            "big_five":  _gen_big5(tmpl, rng),
        })

    return agents


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera agentes para PSYCHE SIMULACRA")
    parser.add_argument("--n",      type=int, default=100,  help="Numero de agentes")
    parser.add_argument("--seed",   type=int, default=42,   help="Semilla aleatoria")
    parser.add_argument("--output", default="data/seeds/100_personas.yaml", help="Archivo de salida")
    args = parser.parse_args()

    agents = generate(n=args.n, seed=args.seed)

    data = {
        "meta": {
            "version":    "2.0",
            "seed":       args.seed,
            "n_agentes":  len(agents),
            "descripcion": f"Grupo de {len(agents)} agentes con diversidad arquetipica amplia — generado proceduralmente",
        },
        "agents": agents,
    }

    out = ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False,
                  sort_keys=False, width=120)

    vivos_count = len(agents)
    print(f"Generados {vivos_count} agentes en {out}")
    print(f"  M: {sum(1 for a in agents if a['sexo']=='M')}  "
          f"F: {sum(1 for a in agents if a['sexo']=='F')}")
    roles = {}
    for a in agents:
        roles[a['rol']] = roles.get(a['rol'], 0) + 1
    for rol, cnt in sorted(roles.items()):
        print(f"  {rol}: {cnt}")


if __name__ == "__main__":
    main()
