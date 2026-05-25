"""
LegendsExporter — R4-F: Modo Leyendas exportable.

Genera un JSON estructurado y un documento Markdown con el historial
narrativo completo de una simulación: tribus, mitos, deidades, muertes
notables y catástrofes. Diseñado para exportar después de `run_prehistory()`
o al final de una simulación.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.simulation import SimulationRunner


class LegendsExporter:
    """Exporta el historial narrativo de una SimulationRunner a JSON y Markdown."""

    def __init__(self, runner: "SimulationRunner") -> None:
        self._runner = runner

    # ── API pública ───────────────────────────────────────────────────────────

    def export_json(self, path: str | Path) -> dict:
        data = self._build_payload()
        Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return data

    def export_markdown(self, path: str | Path) -> str:
        data = self._build_payload()
        text = self._render_markdown(data)
        Path(path).write_text(text, encoding="utf-8")
        return text

    def export_both(self, base_path: str | Path) -> tuple[dict, str]:
        base = Path(base_path)
        data = self.export_json(base.with_suffix(".json"))
        text = self.export_markdown(base.with_suffix(".md"))
        return data, text

    # ── Construcción del payload ──────────────────────────────────────────────

    def _build_payload(self) -> dict:
        r        = self._runner
        agents   = r.agents
        myth_eng = agents.mythology_engine
        cat_eng  = r.world.catastrophe

        return {
            "meta": {
                "dia_simulado":   r.clock.now.dia_simulado,
                "agentes_vivos":  r.alive_count,
                "agentes_total":  len(agents.agents),
                "tribus_activas": len(agents.tribe_manager.tribes),
            },
            "tribus":      self._serialize_tribes(agents),
            "mitos":       self._serialize_myths(myth_eng),
            "deidades":    self._serialize_deities(myth_eng),
            "muertes":     self._serialize_deaths(agents),
            "catastrofes": self._serialize_catastrophes(cat_eng),
        }

    # ── Serializadores ────────────────────────────────────────────────────────

    def _serialize_tribes(self, agents) -> list[dict]:
        out: list[dict] = []
        tm = agents.tribe_manager
        for tribe_id, member_ids in tm.tribes.items():
            vivos = sum(
                1 for aid in member_ids
                if agents.agents.get(aid) and agents.agents[aid].is_alive
            )
            cmem = tm.cultural_memories.get(tribe_id)
            records = []
            if cmem is not None:
                records = [
                    {
                        "dia":        r.dia_origen,
                        "tipo":       r.tipo_evento,
                        "desc":       r.descripcion_actual,
                        "intensidad": round(r.intensidad_emocional, 3),
                    }
                    for r in cmem.records[-20:]
                ]
            lf = tm.local_fields.get(tribe_id)
            field_state: dict = {}
            if lf is not None:
                field_state = {
                    "myth_pressure":      round(lf.myth_pressure, 3),
                    "confusion":          round(lf.confusion, 3),
                    "emotional_pressure": round(lf.emotional_pressure, 3),
                }
            out.append({
                "id":                   tribe_id,
                "miembros":             len(member_ids),
                "vivos":                vivos,
                "campo":                field_state,
                "registros_culturales": records,
            })
        return out

    def _serialize_myths(self, myth_eng) -> list[dict]:
        return [
            {
                "nombre":           m.name,
                "tipo":             m.tipo,
                "par":              list(m.par),
                "intensidad":       round(m.intensidad, 3),
                "dia_cristalizado": m.day_crystallized,
                "es_leyenda":       m.es_leyenda,
            }
            for m in getattr(myth_eng, "active_myths", [])
        ]

    def _serialize_deities(self, myth_eng) -> list[dict]:
        return [
            {
                "nombre":              d.nombre,
                "arquetipo":           d.arquetipo_fundacional,
                "esfera":              d.esfera_de_influencia,
                "intensidad":          round(d.intensidad, 3),
                "dia_cristalizacion":  d.dia_cristalizacion,
                "tribu_origen":        d.tribu_origen,
                "causa":               d.causa,
                "activa":              d.is_active,
            }
            for d in getattr(myth_eng, "deities", [])
        ]

    def _serialize_deaths(self, agents) -> list[dict]:
        return [
            {
                "nombre":    d.get("nombre", ""),
                "dia":       d.get("dia", 0),
                "causa":     d.get("causa", "desconocida"),
                "edad":      d.get("edad", 0),
                "tribu":     d.get("tribe_id", ""),
                "arquetipo": d.get("arquetipo", ""),
            }
            for d in agents.death_log
        ]

    def _serialize_catastrophes(self, cat_eng) -> list[dict]:
        return [
            {
                "tipo":       c.tipo,
                "dia_inicio": c.dia_inicio,
                "duracion":   c.duracion_dias,
                "severidad":  round(c.severidad, 3),
            }
            for c in cat_eng.history
        ]

    # ── Render Markdown ───────────────────────────────────────────────────────

    def _render_markdown(self, data: dict) -> str:
        lines: list[str] = []

        meta = data["meta"]
        lines += [
            "# Leyendas de PSYCHE SIMULACRA",
            "",
            f"**Día simulado:** {meta['dia_simulado']}  ",
            f"**Agentes:** {meta['agentes_vivos']} vivos / {meta['agentes_total']} total  ",
            f"**Tribus activas:** {meta['tribus_activas']}",
            "",
        ]

        cats = data["catastrofes"]
        if cats:
            lines += ["## Catástrofes", ""]
            for c in cats:
                lines.append(
                    f"- **{c['tipo'].replace('_', ' ').capitalize()}** "
                    f"(día {c['dia_inicio']}, {c['duracion']} días, "
                    f"severidad {c['severidad']:.2f})"
                )
            lines.append("")

        deidades = data["deidades"]
        if deidades:
            lines += ["## Deidades emergentes", ""]
            for d in deidades:
                estado = "activa" if d["activa"] else "inactiva"
                lines.append(
                    f"- **{d['nombre']}** [{estado}] — {d['esfera']} "
                    f"(intensidad {d['intensidad']:.2f}, día {d['dia_cristalizacion']})"
                )
            lines.append("")

        mitos = data["mitos"]
        if mitos:
            lines += ["## Mitos y Leyendas", ""]
            for m in mitos:
                etiqueta = "Leyenda" if m["es_leyenda"] else "Mito"
                lines.append(
                    f"### [{etiqueta}] {m['nombre']} *(día {m['dia_cristalizado']})*"
                )
                lines.append(
                    f"Tipo: `{m['tipo']}` | Par: `{m['par'][0]}` vs `{m['par'][1]}` "
                    f"| Intensidad: {m['intensidad']:.2f}"
                )
                lines.append("")

        tribus = data["tribus"]
        if tribus:
            lines += ["## Crónicas tribales", ""]
            for t in tribus:
                lines.append(
                    f"### Tribu `{t['id']}` — {t['vivos']}/{t['miembros']} vivos"
                )
                if t["campo"]:
                    f = t["campo"]
                    lines.append(
                        f"*Campo: presión mítica {f.get('myth_pressure', 0):.2f}, "
                        f"confusión {f.get('confusion', 0):.2f}*"
                    )
                recs = t.get("registros_culturales", [])
                if recs:
                    lines.append("")
                    lines.append("**Registros culturales:**")
                    for e in recs:
                        lines.append(
                            f"- [día {e['dia']}] `{e['tipo']}` — {e['desc']}"
                        )
                lines.append("")

        muertes = data["muertes"][-20:]
        if muertes:
            lines += ["## Muertes notables", ""]
            for d in muertes:
                lines.append(
                    f"- **{d['nombre']}** (edad {d['edad']}, día {d['dia']}) "
                    f"— {d['causa']} | tribu `{d['tribu']}`"
                )
            lines.append("")

        return "\n".join(lines)
