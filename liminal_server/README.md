# LIMINAL ZONE — Servidor de Interconexión

**LIMINAL ZONE** es el servidor central del ecosistema PSYCHE SIMULACRA. Permite que múltiples instancias de la simulación se conecten a un espacio compartido donde los agentes de distintos mundos pueden encontrarse.

---

## Qué es la Zona Liminal

Un espacio de tránsito puro entre simulaciones. **No tiene recursos, clima, fauna ni mecánicas de supervivencia.**

| Elemento | Detalle |
|----------|---------|
| Mapa | 30×20 hexágonos con 5 biomas visuales: `vacío`, `nebulosa`, `cristalino`, `sombra`, `aurora` |
| Recursos | Ninguno — los agentes no tienen hambre, sed ni fatiga mientras están aquí |
| Agentes | En suspensión biológica: `in_liminal = True` pausa todos sus sistemas |
| Duración | 60 ticks liminales (~2 min) y el servidor los devuelve a su simulación de origen |
| Encuentros | Agentes de distintas sims se ven entre sí con el color de su sim de origen |
| Spawn | Cerca del centro (radio 1-3 hex) para favorecer encuentros |

Los biomas son puramente estéticos — dan identidad visual al mapa pero no producen ni consumen nada.

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
cd liminal_server
pip install -r requirements.txt
```

---

## Instructivo paso a paso — dos PCs

### Antes de empezar

- Ambas PCs deben tener PSYCHE SIMULACRA instalado con sus dependencias.
- El servidor liminal solo necesita estar corriendo en **una** de las dos PCs (la que hostea).
- El orden importa: **el servidor debe estar activo antes de que alguien se conecte.**

---

### PC-A (hosteador — quien tiene el servidor)

**Paso 1 — Correr la simulación**

```bash
python main.py
```
En la página de inicio del Observatorio NiceGUI (puerto 8080):
- **Nueva simulación** (primera vez) o **Continuar** (desde checkpoint).
Dejala correr unos días simulados para tener agentes con historia.

**Paso 2 — Activar Zona Liminal**

En el launcher NiceGUI, antes de iniciar (o reiniciar), marcar **Zona Liminal**:
- El campo **Host** debe ser `localhost` (servidor local) o la IP del hosteador.
- El campo **Puerto** es `8765` por defecto.
- Al iniciar, el servidor se lanza en background y el tab **Liminal** aparece en el Observatorio.

> Si PC-B va a conectarse desde otra red: abrí el puerto 8765 (TCP) en tu router con port forwarding hacia tu IP local.

---

### PC-B (el amigo — quien se conecta)

**Paso 1 — Correr su propia simulación en una terminal**

```
python main.py → [4] Primera simulación
```

**Paso 2 — Conectarse al servidor de PC-A (en otra terminal)**

```
python main.py → [6] Conectarse a servidor
  → IP del servidor: <IP que te dio PC-A>
  → Puerto: 8765
```

- Se abre el visualizador con el portal visible en su mapa.
- El HUD mostrará `Liminal: CONECTADO`.

---

### Qué pasa ahora

Cuando un agente de cualquiera de las dos simulaciones llega al hexágono portal (violeta pulsante), **desaparece de su mapa local** y aparece en la ventana del servidor liminal. Si en ese momento hay agentes de la otra simulación también en la zona, se ven entre sí. Tras ~2 minutos el servidor los devuelve a su simulación de origen con los efectos del encuentro grabados.

---

### Diagrama del orden

```
PC-A  (terminal 1)          PC-A  (terminal 2)        PC-B  (terminal 2)
──────────────────          ──────────────────        ──────────────────
[1] python main.py          [2] python main.py        [2] python main.py
    → [1] Continuar  ──────────→ [5] Levantar         → [6] Conectarse
      (sim corriendo)               servidor               → IP de PC-A
                                    + conectar
```

---

## Uso manual (alternativa al launcher)

```bash
# Servidor
cd liminal_server
python main.py --host 0.0.0.0 --port 8765 --seed 0

# Cliente (misma PC)
python scripts/visualizer.py --liminal

# Cliente (otra PC)
python scripts/visualizer.py --liminal --liminal-host 192.168.1.100 --liminal-port 8765
```

---

## Cómo funciona el portal

1. Al conectarse al servidor, PSYCHE SIMULACRA genera un **hexágono portal** en el mapa. Su posición es determinista: depende del seed de la simulación — siempre está en el mismo lugar para la misma semilla.
2. Cuando un agente llega a ese hexágono, **desaparece del mapa local** (`in_liminal = True`).
3. El cliente envía `agent_enter` al servidor con los datos psicológicos del agente (arquetipos, rasgos, tribu).
4. El servidor asigna una posición cerca del centro y confirma con `agent_placed`.
5. El agente aparece en el tab **Liminal** del Observatorio NiceGUI con el color de su sim de origen.
6. Todas las simulaciones conectadas reciben `agent_arrived`.
7. Tras 60 ticks liminales el servidor envía `agent_return` y el agente reaparece en su sim.

---

## Estructura del proyecto

```
liminal_server/
├── main.py                    ← Punto de entrada
├── config.py                  ← Configuración (host, puerto, seed, return ticks)
├── requirements.txt
├── README.md
├── FAQ.md
├── core/
│   ├── liminal_world.py       ← Mapa hexagonal 30×20 (5 biomas etéreos)
│   ├── liminal_clock.py       ← Reloj propio del servidor
│   ├── simulation_registry.py ← Simulaciones conectadas
│   └── agent_registry.py      ← Agentes presentes en la zona
├── transport/
│   └── websocket_server.py    ← Servidor WebSocket (websockets + asyncio)
└── protocol/
    └── schemas.py             ← Tipos de mensajes del protocolo
```

> El visualizador Pygame (`liminal_pygame.py`) fue archivado en `src/archive/`.
> La visualización del estado liminal se realiza desde el tab **Liminal** del dashboard NiceGUI,
> que consulta el endpoint HTTP `/state` del servidor.

---

## Stack técnico

| Componente | Tecnología |
|---|---|
| Networking | WebSockets (`websockets` library) |
| Async | asyncio |
| Visualización | NiceGUI (tab Liminal del dashboard principal) |
| Mapa | Hexagonal axial (q, r) — 30×20 |
| Serialización | JSON |
| Protocolo | `PROTOCOL_VERSION = "0.1.0"` |

---

## Fases de desarrollo

| Fase | Estado | Descripción |
|---|---|---|
| 0 | ✅ | Estructura del proyecto, protocolo base |
| 1 | ✅ | Servidor mínimo — conexión y recepción de agentes |
| 2 | ✅ | Cliente en PSYCHE SIMULACRA — portal hexagonal |
| 3 | ✅ | Visualizador Pygame segunda ventana (`liminal_pygame.py`) |
| 4 | Pendiente | Conexión real entre dos PCs (port forwarding / túnel) |
| 5 | ⚠️ Parcial | Eventos simbólicos cross-sim — `AgentTransferHandler.on_day` propaga arquetipo/rasgos; eventos de mitos/sueños pendientes |
| 6 | ⚠️ Parcial | Interacción cross-sim — agentes llegan al mundo liminal y se mueven; interacción directa entre agentes de distintas sims pendiente |
| 7 | ⚠️ Parcial | Regreso — `AgentTransferHandler` maneja `agent_return` del servidor; reintegración completa al mundo de origen pendiente |
