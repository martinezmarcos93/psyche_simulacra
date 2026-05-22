# PSYCHE SIMULACRA: INTERCONEXIÓN LIMINAL
## Roadmap — Arquitectura federada de civilizaciones emergentes

---

## Visión conceptual

**PSYCHE SIMULACRA** deja de ser una simulación aislada y se transforma en una red de mundos autónomos capaces de intercambiar información simbólica, cultural y eventualmente material, a través de un espacio compartido denominado **LIMINAL SPACE**.

- Cada participante ejecuta su propia simulación localmente.
- El servidor central **NO** ejecuta simulaciones completas.
- El servidor funciona como:
  - Espacio liminal compartido
  - Coordinador temporal
  - Broker de eventos
  - Memoria colectiva intersimulación
  - Gateway cultural

---

## Filosofía del sistema

La meta **NO** es conectar programas.

La meta es permitir que inconscientes colectivos separados, culturas emergentes, mitologías independientes y tribus divergentes puedan entrar en **resonancia**.

---

## Modelo arquitectónico

```
┌────────────────────┐
│ SIMULACIÓN LOCAL A │
│ WorldCore          │
│ AgentCore          │
│ CollectiveField    │
└─────────┬──────────┘
          │
          │  eventos simbólicos
          ▼
┌────────────────────┐
│   LIMINAL SERVER   │
│ LiminalCore        │
│ EventBroker        │
│ TimeTranslator     │
│ MemeticField       │
│ DiplomacyEngine    │
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│ SIMULACIÓN LOCAL B │
│ WorldCore          │
│ AgentCore          │
│ CollectiveField    │
└────────────────────┘
```

---

## Objetivos técnicos

### Fase 1 — Intercambio simbólico

Permitir que dos simulaciones compartan mitos, símbolos, sueños, presagios, narrativas, estados emocionales colectivos y artefactos culturales, **sin compartir agentes físicos**.

### Fase 2 — Exploradores intersimulación

Permitir que agentes especiales abandonen una simulación, atraviesen el espacio liminal y aparezcan en otra simulación.

### Fase 3 — Espacios híbridos

Crear regiones compartidas donde tribus de múltiples simulaciones coexistan, con diplomacia, conflicto, sincretismo cultural y contagio memético.

---

## Principios fundamentales

### 1. Cada simulación es soberana

Cada nodo controla su tiempo, sus agentes, su persistencia y su mundo. El servidor **NO** puede alterar directamente una simulación.

### 2. El servidor solo coordina

El servidor recibe eventos, los redistribuye, mantiene estados liminales, traduce temporalidades y evita conflictos.

### 3. Todo intercambio es asincrónico

No se usa sincronización lockstep inicialmente. Cada simulación avanza a su propio ritmo, puede pausarse, acelerarse o desconectarse.

---

## El problema central: el tiempo

### Problema

```
SIM A = día 300
SIM B = día 125
```

Ambos mundos tienen historias distintas.

### Solución: tiempo relativo liminal

El servidor mantiene un `LIMINAL_TIME` propio. Cada simulación reporta su estado local:

```json
{
  "simulation_id": "SIM_A",
  "local_day": 300,
  "tick": 7200
}
```

El servidor traduce: `LOCAL_TIME → LIMINAL_TIME`.

### Modelo temporal recomendado

No sincronizar ticks. Usar timestamps, ventanas temporales, causalidad débil y colas de eventos.

---

## Eventos liminales

Todo intercambio se modela como **eventos**.

### Estructura base

```json
{
  "event_id": "uuid",
  "origin_simulation": "SIM_A",
  "origin_tribe": "tribe_4",
  "local_time": 7200,
  "liminal_time": 112,
  "event_type": "myth",
  "payload": {},
  "signature": "hash"
}
```

### Tipos de eventos iniciales

**MythEvent**
```json
{
  "type": "myth",
  "symbol": "red_serpent",
  "intensity": 0.72,
  "emotion": "fear"
}
```

**DreamWaveEvent**
```json
{
  "type": "dream_wave",
  "archetype": "shadow",
  "strength": 0.44
}
```

**CulturalArtifactEvent**
```json
{
  "type": "artifact",
  "artifact": "totem",
  "traits": {
    "governance": 0.7,
    "fear": 0.2
  }
}
```

**ProphecyEvent**
```json
{
  "type": "prophecy",
  "text": "The devourer comes from the east"
}
```

---

## Arquitectura del servidor

### Estructura de carpetas

```
liminal_server/
│
├── core/
│   ├── event_broker.py
│   ├── time_translator.py
│   ├── simulation_registry.py
│   ├── causality_engine.py
│   └── conflict_resolver.py
│
├── memetics/
│   ├── memetic_field.py
│   ├── symbol_diffusion.py
│   ├── myth_synthesis.py
│   └── resonance_engine.py
│
├── diplomacy/
│   ├── diplomacy_engine.py
│   ├── treaties.py
│   ├── hostility.py
│   └── migration.py
│
├── transport/
│   ├── websocket_server.py
│   ├── event_protocol.py
│   └── serializers.py
│
├── persistence/
│   ├── database.py
│   ├── event_log.py
│   └── snapshots.py
│
├── monitoring/
│   ├── metrics.py
│   ├── tracing.py
│   └── dashboards.py
│
└── main.py
```

### Comunicación de red

Se recomienda **WebSockets** (no REST polling) por sus eventos en tiempo real, streams bidireccionales y baja latencia.

**Librerías recomendadas:**

| Rol | Librería |
|-----|----------|
| Servidor | FastAPI, uvicorn, websockets, asyncio |
| Cliente | websockets, aiohttp |

---

## Flujo de ejemplo

```
SIM A
  └─ Nace mito → CollectiveField supera umbral → genera MythEvent → envía al servidor

LIMINAL SERVER
  └─ Recibe evento → calcula resonancia → decide difusión → redistribuye

SIM B
  └─ Recibe símbolo → aumenta carga arquetípica → modifica sueños → produce nuevo comportamiento
```

---

## Persistencia

Cada simulación mantiene su propia base de datos (SQLite local, checkpoints, vault). El servidor mantiene únicamente:

- Eventos liminales
- Estados compartidos
- Causalidad cruzada
- Resonancias

**No se comparten bases de datos.**

---

## Identidad global

> ⚠️ **CRÍTICO:** Todos los objetos deben usar UUID globales.

```
# MAL
tribe_1
agent_3

# BIEN
SIM_A:TRIBE:uuid
SIM_B:AGENT:uuid
```

---

## Seguridad

Mínimo necesario por simulación:

- API key
- Firma de eventos (HMAC)
- Validación de schema

**Nunca confiar en:** payloads externos, timestamps externos ni IDs externos.

---

## Consideraciones importantes

| Tema | Descripción |
|------|-------------|
| **Desincronización** | El sistema debe tolerar simulaciones que se pausan, cierran, crashean o aceleran. |
| **Determinismo** | Para reproducibilidad: registrar toda interacción liminal, guardar seeds y versionar schemas. |
| **Versionado** | Mantener `protocol_version`, `schema_version` y `simulation_version`. Cambios sin versionar romperán simulaciones antiguas. |
| **Compatibilidad psicológica** | Ambas simulaciones deben compartir los mismos arquetipos, métricas, símbolos base y sistemas de interpretación. |
| **Compatibilidad semántica** | Si `shadow = agresión` en SIM A y `shadow = creatividad reprimida` en SIM B, los eventos serán incompatibles. |
| **Latencia** | No asumir tiempo real. El sistema debe tolerar retrasos, pérdida temporal de conexión y reenvíos. |

---

## Roadmap técnico

### Etapa 0 — Preparación

- UUID globales
- Sistema de eventos
- Schemas estables
- Serialización

**Implementar:** `core/events/`

### Etapa 1 — Cliente liminal

Cada simulación puede conectarse al servidor, enviar eventos y recibirlos.

```
network/
├── liminal_client.py
├── websocket_transport.py
├── event_queue.py
└── serializers.py
```

### Etapa 2 — Servidor mínimo

Servidor que recibe y redistribuye eventos: WebSocket server, event broker, simulation registry.

### Etapa 3 — Campo memético compartido

Crear un `GLOBAL_MEMETIC_FIELD` donde los símbolos se mezclan, mutan y propagan.

### Etapa 4 — Diplomacia tribal

Tratados, hostilidad, migraciones y guerras simbólicas.

### Etapa 5 — Exploradores

Mover agentes entre mundos.

### Etapa 6 — Espacios híbridos

Crear hexágonos compartidos entre simulaciones.

---

## Arquitectura de carpetas (en PSYCHE SIMULACRA)

```
core/
└── liminal/
    ├── client/
    ├── events/
    ├── protocol/
    ├── sync/
    └── resonance/
```

---

## Fuera de alcance inicial

> No implementar todavía:

- Combate cross-sim
- Pathfinding entre mundos
- Sincronización física completa
- Shared world state
- Shared terrain

---

## Stack recomendado

| Área | Tecnología |
|------|------------|
| Networking | WebSockets |
| Servidor | FastAPI |
| Async | asyncio |
| Serialización | msgpack o JSON |
| IDs | UUID |
| Persistencia | SQLite / PostgreSQL |
| Seguridad | API keys + HMAC |
| Observabilidad | Prometheus + Grafana |
| Contenedores | Docker |
| Deploy servidor | Ubuntu VPS |

---

## Primer objetivo real

> Un mito nacido en SIM A debe poder alterar sueños en SIM B.

Si se logra eso: el sistema está vivo, la resonancia intersimulación existe y el proyecto entra en territorio completamente nuevo.

---

## Consideración filosófica final

Una vez conectadas múltiples simulaciones, ninguna civilización volverá a estar realmente aislada. Podrían aparecer arquetipos universales, religiones intersimulación y entidades meméticas autónomas.

En ese momento, **PSYCHE SIMULACRA deja de ser una simulación. Se convierte en un ecosistema de inconscientes colectivos emergentes.**
