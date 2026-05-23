"""
config.py — Configuración central del servidor LIMINAL ZONE.

Modificá SERVER_HOST / SERVER_PORT para ajustar la red.
Para conectar desde otra PC: el hosteador abre este puerto en su router
y el otro configura SERVER_HOST con la IP pública del hosteador en su cliente.
"""

# ── Red ──────────────────────────────────────────────────────────────────────
SERVER_HOST = "0.0.0.0"   # Escucha en todas las interfaces
SERVER_PORT = 8765

# ── Mapa liminal ─────────────────────────────────────────────────────────────
WORLD_WIDTH  = 30
WORLD_HEIGHT = 20
WORLD_SEED   = 0          # Seed del mapa liminal (igual en todos los nodos)

# ── Protocolo ────────────────────────────────────────────────────────────────
PROTOCOL_VERSION = "0.1.0"

# ── Comportamiento de la zona liminal ────────────────────────────────────────
# Ticks liminales antes de devolver al agente a su simulación de origen.
# El reloj liminal avanza ~1 tick cada 2 segundos (60 frames a 30 FPS).
# 60 ticks ≈ 2 minutos de permanencia.
LIMINAL_RETURN_AFTER_TICKS = 60

# ── Seguridad básica (para versiones futuras) ─────────────────────────────────
API_KEY = ""   # Vacío = sin autenticación. Completar para producción.
