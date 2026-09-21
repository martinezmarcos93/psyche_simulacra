# El cerebro digital de un agente

Este documento describe, pieza por pieza y con clases/métodos concretos, cómo un
`Agent` (`core/agents/agent.py`) percibe, siente, recuerda, sueña y decide. Es la
vista "de un solo agente"; `ARCHITECTURE.md` da la vista de todo el sistema y
`ARCHETYPES.md` / `MENTAL_VAULT.md` profundizan en dos subsistemas concretos.

---

## 1. Las cuatro capas (resumen de estructuras de datos)

| Capa | Atributo en `Agent` | Clase | Rango/forma |
|---|---|---|---|
| Biológica | `self.needs` | `Needs` (`core/agents/needs.py`) | hambre/sed/fatiga/salud ∈ [0,1] |
| Biológica | `self.schedule` | `ScheduleSystem` | actividad por hora del día, según `rol` |
| Psicológica | `self.archetypes` | `ArchetypeVector` | 12 floats ∈ [0,1], independientes |
| Psicológica | `self.complexes` | `ComplexProfile` | 6 floats ∈ [0,1] + `activos: dict` |
| Psicológica | `self.traits` | `TraitProfile` | Big Five (5) + 9 rasgos clínicos, todos ∈ [0,1] |
| Psicológica | `self.humor, .energia, .ansiedad` | floats | estado emocional de corto plazo |
| Cuántica | `self.behavioral_state` | `BehavioralState` | superposición sobre 4 acciones |
| Social | `self._perception` | `PerceptionSystem` | eventos recientes, rumores, asociaciones causales |
| Social | (vía `AgentCore.social_network`) | grafo NetworkX | `bond_strength` ∈ [-1,1] por par |
| Simbólica | `self.episodic_memory` | `EpisodicMemory` | recuerdos con re-vivencia |
| Simbólica (opcional) | `self._interpretive_filter` | `InterpretiveFilter` | activable por flag |
| Simbólica (opcional) | `self.mental_vault` | `MentalVault` | activable por flag, requiere el filtro |

---

## 2. Percepción: de estímulo físico a evento sentido

### 2.1 `PerceptionSystem` (siempre activo)

Cada agente tiene un radio de percepción de 3 hexes (`PERCEPTION_RADIUS`).
`witness(tipo, coord, intensidad, dia, agent_coord)` registra un evento solo si
está dentro de ese radio (o si `coord is None`, como el clima, que se percibe
siempre). Guarda los últimos 30 eventos (`_recent_events`).

- **Rumores**: `generate_rumors()` convierte los 5 eventos directos más recientes
  en `Rumor(hops=0)`; `receive_rumor()` los recibe con distorsión acumulada del
  20% por salto social (`_RUMOR_DECAY_PER_HOP`), descartándolos si caen bajo 0.05
  de intensidad. Así una misma noticia se degrada al viajar de boca en boca.
- **Atención selectiva**: `perceived_intensity()` amplifica ×1.5 la intensidad si
  el tipo de evento coincide con `ARCHETYPE_ATTENTION[arquetipo_dominante]` — un
  mapa fijo de qué categorías físicas "le importan" a cada arquetipo (ej.: el
  héroe atiende `conflicto/depredador/choque_violento`; la sombra atiende
  `muerte/traicion/veneno`). Este mapa **es diseño legítimo** (Capa A: qué mira
  cada arquetipo), no asignación de significado.
- **Sesgo causal → tabúes** (`check_causal_bias(dia)`): dos eventos de tipo
  distinto que co-ocurrieron dentro de una ventana de 3 días forman una
  `CausalAssociation(precursor, outcome, fuerza)`, con
  `fuerza = min(1.0, intensidad_a * intensidad_b * 2.0)` (se descartan asociaciones
  con fuerza < 0.15). Estas asociaciones son la base empírica y estocástica de los
  tabúes: cada agente forma **las suyas propias**, según qué le tocó vivir cerca en
  el tiempo — nadie le asigna una tabla de causas. `AgentCore._process_causal_bias`
  (día, prioridad `AGENT`) registra en la memoria cultural tribal las asociaciones
  con fuerza ≥ 0.40 como eventos `"taboo_causal"`.

### 2.2 `InterpretiveFilter` — la "ecuación personal" (Fase 1, opcional)

Activable con `INTERPRETIVE_FILTER_ENABLED=1`. Instanciado por agente pero sin
estado propio (toda la varianza sale de la psique del agente que recibe en cada
llamada). Corre **una vez por tick**, dentro de `Agent.decide_action()`, antes de
cualquier lógica de supervivencia — así el filtro ve también la amenaza/escasez
que hace *override* de la decisión social.

```
Stimulus (físico)             →  InterpretiveFilter.interpret(stim, agent, field,
  kind, threat, benefit,           mythology_engine)
  social, proximity, raw               │
                                        ▼
                              PerceivedEvent (Capa A + Capa B)
```

**Capa A — los 4 operadores, todos devuelven solo escalares:**

| Operador | Calcula | Palanca principal |
|---|---|---|
| `AttentionOperator.salience` | cuánta saliencia asigna al estímulo (0-1) | necesidad activa, atención arquetípica ×1.5, complejo activo +0.05 |
| `AffectiveOperator.appraise` | `(valence, arousal)` | `threat_gain`/`benefit_gain` idiosincráticos por rasgos (paranoia/neuroticismo/ansiedad amplifican la amenaza; apertura/estabilidad realzan el beneficio); ansiedad de estado tiñe negativamente |
| `RelevanceOperator.relevance` | `relevance_to_self` (0-1) | necesidades activas, `traits.social_drive()` |
| `ResonanceOperator.activation` | `{arquetipo: delta}` — qué se *encendió*, no qué *significa* | `ArchetypeVector` del agente como prior |

El punto filosófico central está en `AffectiveOperator.appraise`: la **misma**
realidad física (`Stimulus`) produce `valence` distinta —a veces de signo
opuesto— según los rasgos y el estado del agente que la recibe. Es lo que permite
que dos agentes idénticos en todo menos la psique interpreten el mismo evento de
forma opuesta (ver test
`test_misma_situacion_diverge_entre_psiques`), y que el mismo agente, en dos
momentos con distinta ansiedad, sienta la misma categoría de forma distinta (ver
`test_ansiedad_tine_la_valencia_negativamente` → ambivalencia → ver
`MENTAL_VAULT.md`).

**Capa B — tres slots simbólicos que nacen `None` y solo se llenan por préstamo**
(nunca por un `if`/enum del diseñador):

| Slot | Fuente del préstamo | Umbral |
|---|---|---|
| `narrative_frame` | el arquetipo que más resonó, si su símbolo ya cristalizó en `field.symbols` | carga ≥ 0.55 (`_VOCAB_THRESHOLD`) |
| `attributed_cause` | la `CausalAssociation` más fuerte que el propio agente ya formó (`PerceptionSystem.strongest_cause`) para este tipo de estímulo | fuerza ≥ 0.40 (`_CAUSE_THRESHOLD`) |
| `moral_judgment` | el `name` del `MythCrystal` de tipo `"mito_moral"` ya cristalizado cuyo `par` de arquetipos coincide con lo que se activó hoy | existencia del mito (no hay umbral adicional) |

Si nada de eso existe todavía, el agente **siente pero no nombra/atribuye/juzga**.
Esto es exactamente lo que separa este proyecto de un sistema experto: el
vocabulario no está precargado, se pide prestado a estructuras que ya emergieron
en otra parte del sistema (el campo colectivo, la propia memoria causal del
agente, o la mitología ya cristalizada).

`PerceivedEvent.action_bias()` traduce `(valence, arousal, relevance_to_self)` —
solo Capa A — en un delta para cada una de las 4 acciones conductuales; los slots
de Capa B **no** entran en esa traducción (ver §5). Su único consumo hoy es
narrativo/observacional y como insumo de `MentalVault.accumulate` (que tampoco
lee los slots de Capa B; ver `MENTAL_VAULT.md` §1).

---

## 3. Psicología estable: arquetipos, complejos, rasgos

Ver `ARCHETYPES.md` para el arquetipo en detalle. En resumen, para este documento:

- **`ArchetypeVector`**: 12 pesos independientes (no suman 1). `dominant()` da el
  de mayor peso; `action_bias(accion)` combina `_ACTION_AFFINITY` (mapa fijo
  arquetipo→acción) ponderado por el peso actual de cada arquetipo.
- **`ComplexProfile`**: 6 complejos con intensidad base + `activos: dict` (los que
  superaron `_ACTIVATION_THRESHOLD=0.65` ante un trigger contextual). Mientras
  activo, decae `_DECAY_PER_TICK` por tick y `_DECAY_PER_DAY` adicional por día.
  `action_bias()` usa `_COMPLEX_ACTION_BIAS`, un mapa fijo complejo→acción.
- **`TraitProfile`**: Big Five + 9 rasgos clínicos, estáticos salvo por deriva
  lenta (sueños, sustancias, imprinting). `mood_modifier()` y `action_bias()`
  derivan de combinaciones fijas de rasgos.

Estos tres mapas (`_ACTION_AFFINITY`, `_COMPLEX_ACTION_BIAS`, rasgos→acción) son
**Capa A explícita**: son la "gramática psíquica" que el proyecto declara
legítimo prefijar (ver `EMERGENCE.md`). Lo que emerge no es *que* el héroe
tienda a competir, sino *cuánto* pesa cada arquetipo en cada agente con el tiempo,
y qué símbolo termina llevando su nombre en el colectivo.

---

## 4. Memoria: episódica, sueños, causal

- **`episodic_log`** (lista de texto plano) alimenta al `DreamGrammarEngine` — es
  la "materia prima" narrativa de los sueños.
- **`EpisodicMemory`** (estructurada, con re-vivencias, Hito A/Roadmap 4): guarda
  recuerdos con intensidad y permite que un recuerdo antiguo se "reviva"
  (re-entre en juego) según condiciones contextuales — ver
  `_revivir_memorias_largo_plazo` en `agent_core.py`.
- **`DreamGrammarEngine`** (`core/agents/psyche/dreams.py`): genera un sueño único
  por agente y noche, combinando 5 capas ponderadas — bioma (1.0), arquetipo
  dominante (2.5), complejo activo (4.0), traumas recientes de la memoria
  episódica (5.0), símbolo de resonancia grupal si el agente está entrelazado con
  otro (6.0). El sueño produce un `delta_arquetipo` que se aplica de vuelta al
  `ArchetypeVector` — es el principal mecanismo de plasticidad psicológica de
  largo plazo, y **content-free en el mismo sentido** que el filtro: el peso de
  cada capa está diseñado, pero *qué* combinación sale cada noche depende de la
  historia acumulada del agente.
- **Asociaciones causales** (`PerceptionSystem._causal_assocs`): ver §2.1. Son el
  único mecanismo persistente de "creencia propia" de un agente sobre el mundo
  físico, independiente del campo colectivo.
- **`LindBladChannel`** (`core/agents/psyche/lindblad.py`): canal de decoherencia
  arquetípica T1/T2 — relajación hacia el baseline + represión activa (bias
  suprimido cuando un arquetipo supera cierto umbral). Es lo que evita que un
  arquetipo activado por un evento puntual quede "pegado" para siempre.

---

## 5. Decisión: de la psique a una `WorldAction`

Ver `ARCHITECTURE.md` §4 para el árbol completo de `decide_action()`. El núcleo
cuántico (`collapse_state`, `core/agents/quantum/collapse.py`) mezcla seis
canales, cada uno como `{acción: delta}` ponderado:

| Canal | Peso | Fuente |
|---|---|---|
| Arquetipos | 0.30 | `ArchetypeVector.action_bias()` |
| Complejos | 0.25 | `ComplexProfile.action_bias()` |
| Rasgos | 0.20 | `TraitProfile.action_bias()` |
| Contexto | 0.15 | `_context_bias()` — peligro/recursos/aliados/amenaza, sin psicología |
| Campo colectivo | 0.10 | `CollectiveField.radiate()` |
| Ecuación personal | 0.15 | `PerceivedEvent.action_bias()` (Fase 1, si está ON) |

Los deltas ponderados se suman al vector de probabilidades base
(`BehavioralState.probabilities()`), se renormalizan, y — si `MentalVault` está
activo — se interpolan hacia la distribución uniforme en proporción al `noise`
(incoherencia interna del mini cerebro; ver `MENTAL_VAULT.md`). El muestreo final
es estocástico (`rng.choices`, ponderado), no un arg-max: **el colapso siempre
puede sorprender**, incluso con el mismo estado psicológico.

Resultado: una de `cooperacion | competencia | aislamiento | manipulacion`, que
`_decide_via_collapse()` traduce a una `WorldAction` concreta (moverse, acercarse,
alejarse...).

---

## 6. Disociación y desregulación (cuando la psique hace *override*)

`Agent.dissociation_state` (Hito B, Roadmap 4) puede tomar el control completo de
`decide_action()` antes de que se llegue al colapso normal:

- `estupor_catatonico` / `melancolia_disociativa` → inacción total.
- `fuga_disociativa` → movimiento errático puro, ignora arquetipo/necesidades/RNG
  psicológico (`_fuga_disociativa_action`).
- `amok` → la lógica normal sigue, pero los ataques se procesan aparte en
  `AgentCore._process_dissociation()`.

Se dispara por `_dias_ansiedad_alta` sostenidos (ver `agent_core.py`
"Disociación por sombra y cascada de estrés — Hito B").

---

## 7. Influencia social y aprendizaje

- **`SocialNetwork`** (grafo NetworkX, en `AgentCore`, no en `Agent`): `bond_strength`
  ∈ [-1,1] por par; se refuerza por interacción, cadena chamánica, cría compartida.
- **Entrelazamiento cuántico** (`propagate_entanglement`): pares con vínculo alto
  pueden compartir sesgos de colapso y sueños entrelazados nocturnos.
- **Contagio emocional / histeria colectiva**: ansiedad e intensidad afectiva se
  propagan por la red social cuando superan umbrales (`agent_core.on_day` pasos
  10-11).
- **Proyección, sesgo de atribución, paranoia tribal, disonancia cognitiva**
  (Hito 9, pasos 13-16 de `on_day`): mecanismos de sesgo cognitivo colectivo que
  retroalimentan al individuo — ver `ARCHITECTURE.md` §3 para el listado completo.

---

## 8. Relación experiencia ↔ representación simbólica (el mapa completo)

```
Stimulus físico (kind, threat, benefit, social, proximity)
        │
        ▼  InterpretiveFilter (Capa A: escalares)
PerceivedEvent (valence, arousal, relevance, archetype_activation)
        │                                   │
        │ action_bias()                     │ accumulate()
        ▼                                   ▼
  collapse_state (canal 0.15)        MentalVault._day_records
        │                                   │  (una vez por día)
        ▼                                   ▼
   WorldAction                       Neuron ligada por resonancia
                                      (misma física que CollectiveField,
                                       a escala individual — ver MENTAL_VAULT.md)
        │                                   │
        ▼                                   ▼
  interacción social ───────────▶ CollectiveField (símbolos, presión mítica)
                                            │
                                            ▼
                                   MythologyEngine → ProtoMito → MythCrystal
                                            │
                    préstamo (narrative_frame / moral_judgment) ◀──┘
                                            │
                                            ▼
                          de vuelta a PerceivedEvent del PRÓXIMO tick
                          (el ciclo se retroalimenta, nunca se inventa)
```

Esta es la razón de ser de `EMERGENCE.md`: en cada flecha de este diagrama hay que
poder señalar si es una regla fija (Capa A) o si el contenido que fluye por ella
tuvo que cristalizar primero en otra parte del sistema (Capa B).
