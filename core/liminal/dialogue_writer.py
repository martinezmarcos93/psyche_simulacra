"""
core/liminal/dialogue_writer.py — Escribe transcripciones de diálogos liminales al vault.

Cada diálogo se guarda como un archivo Markdown en vault/Liminal/Dialogos/.
"""
from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger("liminal.dialogue_writer")


class DialogueWriter:
    def __init__(self, vault_path: str = "vault") -> None:
        self.path = Path(vault_path) / "Liminal" / "Dialogos"

    def write(
        self,
        dialogue_id:    str,
        agent_a_name:   str,
        sim_a:          str,
        tribe_a:        str,
        agent_b_name:   str,
        sim_b:          str,
        tribe_b:        str,
        local_payload:  dict,
        other_payload:  dict,
        turns:          list[dict],
        dia:            int,
    ) -> None:
        self.path.mkdir(parents=True, exist_ok=True)

        filename = f"dialogo_dia_{dia:05d}_{_safe(agent_a_name)}_vs_{_safe(agent_b_name)}.md"
        filepath = self.path / filename

        def _fmt_myths(myths):
            if not myths:
                return "*(ninguno aún)*"
            return "\n".join(f"  - **{m['name']}** ({m['tipo']}, intensidad {m['intensity']:.2f})" for m in myths)

        def _fmt_symbols(symbols):
            if not symbols:
                return "*(ninguno)*"
            top = sorted(symbols.items(), key=lambda x: x[1], reverse=True)[:3]
            return ", ".join(f"{k} ({v:.2f})" for k, v in top)

        turns_md = "\n\n".join(
            f"**{t['speaker_name']}** *(sim: {t['speaker_sim'][:20]}…)*\n\n> {t['text']}"
            for t in turns
        )

        content = (
            f"---\n"
            f"tipo: dialogo_liminal\n"
            f"dia: {dia}\n"
            f"participante_a: {agent_a_name}\n"
            f"participante_b: {agent_b_name}\n"
            f"sim_a: {sim_a}\n"
            f"sim_b: {sim_b}\n"
            f"---\n\n"
            f"# Diálogo Liminal — Día {dia}\n\n"
            f"*Un encuentro entre mundos en la Zona Liminal.*\n\n"
            f"---\n\n"
            f"## Participantes\n\n"
            f"### {agent_a_name} — {tribe_a or 'tribu desconocida'}\n"
            f"**Mitos:** {_fmt_myths(local_payload.get('myths', []))}\n\n"
            f"**Símbolos:** {_fmt_symbols(local_payload.get('symbols', {}))}\n\n"
            f"**Léxico:** {', '.join(local_payload.get('lexicon', [])) or '*(sin lengua aún)*'}\n\n"
            f"### {agent_b_name} — {tribe_b or 'tribu desconocida'}\n"
            f"**Mitos:** {_fmt_myths(other_payload.get('myths', []))}\n\n"
            f"**Símbolos:** {_fmt_symbols(other_payload.get('symbols', {}))}\n\n"
            f"**Léxico:** {', '.join(other_payload.get('lexicon', [])) or '*(sin lengua aún)*'}\n\n"
            f"---\n\n"
            f"## Transcripción\n\n"
            f"{turns_md}\n"
        )

        try:
            filepath.write_text(content, encoding="utf-8")
            logger.info("Diálogo escrito: %s", filename)
            print(f"  [Diálogo] {filename}")
        except Exception as exc:
            logger.warning("No se pudo escribir diálogo %s: %s", filename, exc)


def _safe(name: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in name)[:20]
