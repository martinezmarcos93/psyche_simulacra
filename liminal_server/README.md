# LIMINAL ZONE — Servidor de Interconexión

**LIMINAL ZONE** es el servidor central del ecosistema PSYCHE SIMULACRA. Permite que múltiples instancias de la simulación se conecten a un espacio compartido donde los agentes de distintos mundos pueden encontrarse.

---

## Arquitectura

```
[PC-A: Simulación de Marcos]          [PC-B: Simulación del amigo]
  PSYCHE SIMULACRA                       PSYCHE SIMULACRA
  + LiminalClient ──────────┐            + LiminalClient ─────────┐
  + Portal Hex (Pygame)     │            + Portal Hex (Pygame)    │
                            ▼                                      ▼
                     ┌──────────────┐
                     │ LIMINAL ZONE │  ← este servidor
                     │  WebSocket   │
                     │  LiminalWorld│
                     │  Pygame viz  │
                     └──────────────┘
```

El servidor:
- **No** controla ninguna simulación.
- **No** tiene agentes propios — los agentes provienen de las simulaciones conectadas.
- Funciona como espacio compartido, coordinador de presencia y broker de eventos.

---

## Instalación

```bash
cd liminal_zone
pip install -r requirements.txt
```

---

## Uso

### Iniciar el servidor (quién hostea)

```bash
python main.py
```

Con opciones:

```bash
python main.py --host 0.0.0.0 --port 8765 --seed 0
```

El servidor abre una **ventana Pygame** mostrando el mapa liminal en tiempo real.

### Conectar una simulación

Desde `PSYCHE SIMULACRA`, iniciá el visualizador con el flag `--liminal`:

```bash
python scripts/visualizer.py --liminal --liminal-host 192.168.1.100 --liminal-port 8765
```

O desde el launcher `main.py` de PSYCHE SIMULACRA (opción de menú: `Zona Liminal`).

---

## Cómo funciona el portal

1. Al iniciar, PSYCHE SIMULACRA genera un **hexágono portal** en el mapa. Su posición es determinista: depende del seed de la simulación.
2. Cuando un agente llega a ese hexágono, **desaparece del mapa local** y aparece en la zona liminal.
3. En la ventana Pygame del servidor, el agente aparece con el color de su simulación de origen.
4. Agentes de distintas simulaciones pueden coincidir en la zona liminal.

---

## Configuración de red (para dos PCs)

1. El **hosteador** abre el puerto 8765 (TCP) en su router → redirige a su IP local.
2. El **que se conecta** edita `PSYCHE SIMULACRA/core/liminal/liminal_client.py` o usa el flag `--liminal-host <IP_PUBLICA_DEL_HOSTEADOR>`.
3. Ambos deben usar la misma `PROTOCOL_VERSION` (ver `config.py`).

---

## Estructura del proyecto

```
liminal_zone/
├── main.py                    ← Punto de entrada
├── config.py                  ← Configuración (host, puerto, seed)
├── requirements.txt
├── README.md
├── FAQ.md
├── core/
│   ├── liminal_world.py       ← Mapa hexagonal 30×20
│   ├── liminal_clock.py       ← Reloj propio del servidor
│   ├── simulation_registry.py ← Simulaciones conectadas
│   └── agent_registry.py      ← Agentes presentes en la zona
├── transport/
│   └── websocket_server.py    ← Servidor WebSocket (websockets + asyncio)
├── protocol/
│   └── schemas.py             ← Tipos de mensajes del protocolo
└── visualizer/
    └── liminal_pygame.py      ← Ventana Pygame del mapa liminal
```

---

## Stack técnico

| Componente | Tecnología |
|---|---|
| Networking | WebSockets (`websockets` library) |
| Async | asyncio |
| Visualización | Pygame |
| Mapa | Hexagonal axial (q, r) |
| Serialización | JSON |
| Protocolo | `PROTOCOL_VERSION = "0.1.0"` |

---

## Fases de desarrollo

| Fase | Estado | Descripción |
|---|---|---|
| 0 | ✅ | Estructura del proyecto, protocolo base |
| 1 | ✅ | Servidor mínimo — conexión y recepción de agentes |
| 2 | ✅ | Cliente en PSYCHE SIMULACRA — portal hexagonal |
| 3 | ✅ | Visualizador Pygame segunda ventana |
| 4 | Pendiente | Conexión real entre dos PCs (port forwarding) |
| 5 | Pendiente | Eventos simbólicos (mitos, sueños) cross-sim |
| 6 | Pendiente | Interacción entre agentes de distintas sims |
| 7 | Pendiente | Regreso de agentes a simulación de origen |
