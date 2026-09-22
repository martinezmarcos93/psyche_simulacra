# MentalVault — el mini cerebro por agente

`core/agents/mental_vault/` (`mental_vault.py` + `neuron.py`). Es la Fase 2 de la
Ecuación Personal (ver `src/ROADMAP_ECUACION_PERSONAL.md`). Requiere
`MENTAL_VAULT_ENABLED=1` **y** `INTERPRETIVE_FILTER_ENABLED=1` (si se pide el
vault sin el filtro, `agent.py` lo desactiva — el vault consume `PerceivedEvent`,
no tiene otra fuente de datos).

El insight de diseño, citado directamente del roadmap porque es el criterio con
el que hay que juzgar cualquier cambio futuro a este módulo:

> No construimos un motor distinto para el individuo. Recursamos el mismo motor
> de emergencia hacia abajo. El inconsciente personal emerge por la misma física
> que el colectivo, una escala más abajo.

---

## 1. Nodos: la `Neuron`

```python
Neuron:
    id:                  str              # neuron_id(significante, signo(valence))
    significante:        str              # categoría física (Stimulus.kind) — no juicio
    estado_energetico:    float  # 0..1   # decae _DECAY_FACTOR=0.92/día; se refuerza al reactivarse
    carga_afectiva:       float  # -1..1  # EMA: 0.7*anterior + 0.3*valence del evento
    enlaces:              dict            # {otra_neuron_id: peso 0..1}, adyacencia simple (no NetworkX)
    arquetipo_resonante:  str | None      # EMERGE del campo; nace None
    resonance_accum:      dict            # {arquetipo: activación acumulada} — insumo del punto anterior
```

**Por qué la clave de la neurona incluye el signo de la valencia**
(`neuron_id = f"{significante}:{'p' if valence>=0 else 'n'}"`): sin esto, cargas
afectivas opuestas sobre la misma categoría física se promediarían hacia ~0 y la
ambivalencia nunca podría representarse. Con la clave partida, "hambruna sentida
como amenaza" (`hambruna:n`) y "hambruna sentida como oportunidad de mostrar
liderazgo" (`hambruna:p`) son dos neuronas que pueden **coexistir y enlazarse en
tensión** — es el mecanismo concreto que permite que la incoherencia (§4) emerja.

No hay clasificador ni tabla que decida qué es una neurona "buena" o "mala": el
signo sale directo de un escalar de Capa A ya calculado por `InterpretiveFilter`.

---

## 2. Formación: acumulación diaria, no por tick

`accumulate(pe)` (llamado desde `Agent.decide_action()` en cada tick si el
filtro produjo un `PerceivedEvent`) solo apila un registro liviano
(`significante, valence, arousal, intensity, activation`) en `_day_records` — O(1),
no crea neuronas ni enlaces todavía. La creación/enlace real ocurre **una vez por
día simulado**, en `consolidate()` (llamado desde `AgentCore.on_day()`, paso
"9b"), por costo: enlazar en cada tick sería demasiado caro y no aportaría señal
adicional (la resonancia necesita acumular varios eventos, no reaccionar a uno
solo).

`consolidate()`, paso 1: por cada registro del día, `neuron_id()` decide si
refuerza una neurona existente o crea una nueva; la energía sube con la
intensidad del evento, la carga afectiva se actualiza por media móvil, y la
activación arquetípica del evento (`resonance_accum`) se acumula — esta última es
el insumo puro para el paso 3 (nunca decide directamente el arquetipo).

---

## 3. Conexiones: enlazado por la misma física que un mito

Paso 2 de `consolidate()`. Los candidatos a enlazar son la unión de: lo percibido
*hoy* (`touched`) y lo que sigue "caliente" (`estado_energetico ≥
_LINK_ACTIVE_THRESHOLD=0.20`), no solo lo del mismo día — esto es lo que permite
que una creencia latente de hace varios días entre en tensión con algo nuevo.

Se construye un `ContextoEnunciativo` **individual** (la misma clase que usa
`CollectiveField` para decidir si un proto-mito cristaliza — ver `ARCHETYPES.md`
§4):

```python
ctx = ContextoEnunciativo(
    temperatura_semantica = mean(arousal del día),
    intencionalidad        = mean(energía de los candidatos),
    ruido_ambiental        = ansiedad_del_agente * fase_factor,
)
prob = ctx.probabilidad_cristalizacion() * fase_factor
```

Cada par (nuevo × candidato) se enlaza con probabilidad `prob` (`rng.random() <
prob`), reforzando el peso del enlace en ambas direcciones (`_LINK_WEIGHT=0.10`
por evento). Es **umbral + azar**, no una regla de si-tal-entonces-cual —
exactamente el mismo tipo de mecánica que decide si un `ProtoMito` cristaliza en
`MythologyEngine`, aplicada una escala más abajo. Los pares se recorren en orden
determinista (`sorted`) para que la misma semilla reproduzca el mismo resultado.

**Moduladores de fase de vida** (`_FASE_FACTOR`): niñez=1.5 (ruido alto, más
enlaces, símbolos inestables), adolescencia=1.0, adulto=0.7 (ruido bajo,
worldview más estable). Esto reutiliza `agent.fase_desarrollo`, que ya existe
para otros fines (imprinting, vigor). Es Capa A legítima: modula la *temperatura*
del colapso, no decide *qué* se enlaza.

---

## 4. Activación / resonancia: cómo una neurona obtiene (o no) un arquetipo

Paso 3 de `consolidate()`, y es idéntico en espíritu al préstamo de
`narrative_frame` del filtro (`AGENT_BRAIN.md` §2.2): para cada neurona con
`resonance_accum` no vacío, se toma el arquetipo de mayor activación acumulada
(`top_arch`) y se consulta `field.symbols.get(top_arch, 0.0)`. Si esa carga ya
cristalizó (≥ 0.55, mismo `_VOCAB_THRESHOLD` que el filtro), la neurona **hereda**
ese nombre como `arquetipo_resonante`; si no, queda `None` — la neurona sigue
existiendo (tiene energía, carga afectiva, enlaces) pero es un concepto sin
nombre todavía, exactamente como un `PerceivedEvent` puede sentir sin nombrar.

**Feedback a la psique** (`_compute_archetype_feedback`): las neuronas de alta
energía con `arquetipo_resonante` no-`None` empujan levemente ese arquetipo en el
`ArchetypeVector` del agente (`+0.01 * energía`, tope `_MAX_ARCH_DELTA=0.03` por
arquetipo) — el mismo patrón acotado que usan sueños y sustancias. Es el único
canal por el que el mini cerebro individual retroalimenta la psique de base.

---

## 5. Recuperación / consumo: ruido conductual, no consulta directa

El vault **no expone una API de "recordar X"** que otro sistema pueda consultar a
demanda. Su único producto hacia afuera es un escalar: `_compute_ruido()`, vía
`worldview_coherence()`.

```python
worldview_coherence():
    para cada enlace (n, other) con peso > 0:
        si carga_afectiva(n) * carga_afectiva(other) < 0: contradictorio += 1
        total += 1
    retorna 1.0 - contradictorios/total     # 1.0 si no hay enlaces (sin contradicción todavía)
```

`ruido = clamp(0, 0.5, (1 - worldview_coherence) * 0.5)`. Este `ruido` entra a
`collapse_state(noise=...)`, que **interpola las probabilidades de acción hacia
la distribución uniforme** en proporción al ruido — más incoherencia interna →
conducta más entrópica/impredecible. Esta es la "neurosis" del roadmap: no es un
estado con nombre ni un enum (`"neurótico"`), es un número que hace que el
agente se vuelva más errático cuanto más enlaces contradictorios sin resolver
acumula. Nadie decide cuándo un agente "es neurótico" — se mide, no se declara.

---

## 6. Decay, poda y límites

- **Decay**: toda neurona pierde 8%/día de energía (`_DECAY_FACTOR=0.92`).
- **Olvido**: se elimina si `estado_energetico < 0.02` y no tiene enlaces que la
  sostengan.
- **Techo duro**: máximo 50 neuronas (`_CAP_NEURONAS`) por agente; si se excede,
  se conservan las de mayor energía. Esto acota el costo computacional por
  agente independientemente de cuántos días lleve viviendo.

## 7. Persistencia

`to_dict()`/`from_dict()` serializan la lista de neuronas (con sus enlaces y
`arquetipo_resonante`); se integra al checkpoint del agente igual que el resto de
su estado psicológico.

---

## 8. Diferencias con `CollectiveField`

| | `CollectiveField` | `MentalVault` |
|---|---|---|
| Escala | tribu / global | un agente |
| Unidad | símbolo (12 arquetipos fijos) | neurona (concepto abierto, keyed por estímulo físico + signo) |
| Estructura | dict plano de cargas | grafo simple de adyacencia (`enlaces`) |
| Mecanismo de cristalización | `ContextoEnunciativo` → `ProtoMito` → `MythCrystal` | `ContextoEnunciativo` individual → enlace probabilístico entre neuronas |
| Vocabulario que produce | nombres de arquetipo, tipos de mito, nombres de mito/deidad | nada nuevo — solo *hereda* nombres del campo cuando resuena |
| Consumo | `radiate()` (canal 0.10 del colapso), efectos de mitos | un escalar `noise` (canal implícito, aplana probabilidades) |
| Persistencia | por tribu / global | por agente |

El vault es deliberadamente más pobre que el campo colectivo: no genera
vocabulario propio, solo estructura y afecto. Todo nombre que un agente pueda
"pensar" tuvo que cristalizar primero a nivel colectivo — la individualidad
psicológica no es una fuente alternativa de símbolos, es un patrón de *cómo se
distribuyen y contradicen* los símbolos que el colectivo ya produjo.

---

## 9. Límites actuales (honestos)

- `attributed_cause` y `moral_judgment` del `PerceivedEvent` (ver
  `AGENT_BRAIN.md` §2.2) **sí son leídos** por `accumulate()` desde la sesión
  2026-09-21 (segunda parte): cuando vienen nombrados por préstamo, el vault
  forma una neurona adicional por ese nombre (misma física de enlazado, sin
  campo nuevo en `Neuron`, sin activación arquetípica propia para evitar doble
  conteo del mismo evento — ver el docstring de `accumulate()`). Sigue sin
  violar "solo por préstamo": el nombre ya fue vetado por el `InterpretiveFilter`
  antes de llegar acá. Pendiente de validar con una corrida real si esto mueve
  `worldview_coherence` de forma medible (no se corrió ese experimento todavía,
  solo se validó con tests unitarios).
- No hay tab de observabilidad todavía (Fase 3 del roadmap, opcional) — el único
  modo de inspeccionar un vault hoy es leer el JSON serializado o instrumentar
  código ad hoc.
- El límite de 50 neuronas es arbitrario (elegido por costo, no por un modelo de
  capacidad cognitiva); no se validó experimentalmente que sea suficiente ni que
  no distorsione el `worldview_coherence` en agentes muy longevos.
