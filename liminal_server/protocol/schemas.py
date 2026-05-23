"""
protocol/schemas.py — Tipos de mensajes del protocolo LIMINAL ZONE.

Todos los mensajes son dicts JSON. Los MsgType definen el campo "type"
que identifica cada mensaje. Usar encode() / decode() para serializar.
"""

from __future__ import annotations

import json
from enum import Enum


PROTOCOL_VERSION = "0.1.0"


class MsgType(str, Enum):
    # SIM → SERVER
    SIM_CONNECT    = "sim_connect"
    AGENT_ENTER    = "agent_enter"
    PING           = "ping"

    # SERVER → SIM
    SIM_REGISTERED   = "sim_registered"
    SIM_JOINED       = "sim_joined"
    SIM_DISCONNECTED = "sim_disconnected"
    AGENT_PLACED     = "agent_placed"
    AGENT_ARRIVED    = "agent_arrived"
    AGENT_RETURN     = "agent_return"     # servidor devuelve agente a su sim de origen
    AGENTS_MEET      = "agents_meet"      # dos agentes de distintas sims en el mismo hex
    PONG             = "pong"
    ERROR            = "error"


# ── Constructores de mensajes ────────────────────────────────────────────────

def msg_sim_connect(sim_id: str, seed: int) -> dict:
    return {
        "type":    MsgType.SIM_CONNECT,
        "sim_id":  sim_id,
        "seed":    seed,
        "version": PROTOCOL_VERSION,
    }


def msg_agent_enter(sim_id: str, agent_id: str, nombre: str,
                    archetypes: dict, traits: dict,
                    tribe_id: str | None = None) -> dict:
    return {
        "type":       MsgType.AGENT_ENTER,
        "sim_id":     sim_id,
        "agent_id":   agent_id,
        "nombre":     nombre,
        "archetypes": archetypes,
        "traits":     traits,
        "tribe_id":   tribe_id,
    }


def msg_ping() -> dict:
    return {"type": MsgType.PING}


# ── Serialización ─────────────────────────────────────────────────────────────

def encode(msg: dict) -> str:
    return json.dumps(msg, ensure_ascii=False)


def decode(raw: str) -> dict:
    return json.loads(raw)
