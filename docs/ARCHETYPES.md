# Arquetipos: del individuo al mito colectivo

Este documento sigue un arquetipo desde que se activa en un agente hasta que
puede terminar dándole nombre a un mito que toda una tribu hereda. Distingue en
cada paso qué está diseñado (Capa A) y qué debe cristalizar (Capa B) — ver
`EMERGENCE.md` para la definición formal de esa distinción.

---

## 1. El vector arquetípico individual

`ArchetypeVector` (`core/agents/psyche/archetypes.py`) — 12 pesos independientes,
∈ [0,1], que **no** suman 1 (no son una distribución de probabilidad; un agente
puede tener varios arquetipos altos a la vez):

```
self, persona, sombra, anima_animus, heroe, sabio, trickster,
madre, padre, nino_divino, gobernante, rebelde
```

- `dominant()` devuelve el de mayor peso actual.
- `action_bias(accion)` combina `_ACTION_AFFINITY[accion]` (mapa **fijo**
  arquetipo→peso, ej.: la madre suma +0.20 a cooperación, el trickster suma +0.25
  a manipulación) ponderado por el peso actual del agente en cada arquetipo.
- `_TRANSFORMATIONS` (también fijo) traduce eventos de vida (`trauma`,
  `power_corruption`, `deep_bond`, `betrayal`...) en deltas concretos al vector —
  esto es la "gramática de instintos" del proyecto: **legítimamente diseñada**
  (Capa A), porque no asigna significado simbólico, solo dice cómo un tipo de
  experiencia mueve la disposición interna.

Estos tres mapas son intencionalmente estáticos y auditables — son el único lugar
del sistema arquetípico donde el diseñador decide algo directamente.

---

## 2. Activación (por tick, vía `InterpretiveFilter`)

`ResonanceOperator.activation(stim, agent, arousal)`
(`core/agents/psyche/interpretive_filter.py`):

```python
attending = _ATTENTION_BY_KIND[stim.kind]        # qué arquetipos "miran" esta categoría física
for arch in attending:
    prior = agent.archetypes.to_dict()[arch]      # el peso YA existente del agente
    delta = 0.02 * prior * (0.5 + 0.5 * arousal)  # más resuena cuanto más pesa ya + más intenso el estímulo
```

Esto **no es cristalización** — es solo "se encendió una lucecita": un delta
pequeño y transitorio, calculado en el momento, que vive dentro del
`PerceivedEvent` de ese tick y se descarta si nadie lo consume. Content-free: el
operador nunca dice "esto significa X", solo "el arquetipo X del agente se activó
esta magnitud".

`_ATTENTION_BY_KIND` es el inverso de `ARCHETYPE_ATTENTION`
(`core/social/perception.py`) — otro mapa fijo, Capa A: qué categorías físicas
atiende cada arquetipo (el héroe atiende conflicto; la sombra atiende
muerte/traición/veneno).

---

## 3. Del individuo al campo: cómo un arquetipo entra al inconsciente colectivo

Las interacciones y eventos —no la activación privada del §2— son lo que carga el
`CollectiveField` (`core/social/collective_field.py`), global y también uno local
por tribu (`TribeManager.get_local_field`):

- `absorb_interaction(state_a, state_b, outcome_type)`: cooperación pura sube
  `heroe`/`madre` y baja `emotional_pressure`; un choque violento sube `sombra`
  fuerte (+0.18) y `emotional_pressure` (+0.15).
- `absorb_event(event_type, intensity)`: muerte sube `muerte`/`sombra`; nacimiento
  sube `madre`/`nino_divino`/`heroe`; transmisión de conocimiento sube
  `sabio`/`gobernante`; un líder establecido sube `gobernante`/`padre`.
- `absorb_trauma`, `absorb_myth_broadcast`: trauma sin narrativa sube
  `myth_pressure` y `confusion`; un mito ya emitido por otra tribu (eco
  inter-tribal) recarga los símbolos de su par.

Estas reglas de absorción **también son Capa A** — son la física del campo, fija
por diseño (cuánto pesa cada tipo de evento). Lo que emerge es el **resultado
acumulado**: qué símbolo termina dominando en qué tribu, algo que depende
enteramente de la historia real de esa tribu, no de una tabla.

`CollectiveField.decay()` corre una vez por día: todos los símbolos decaen 2%,
`myth_pressure` decae más lento (trauma persiste), `confusion` decae más rápido.
`dominant_archetype_pair()` da el par de mayor carga — es el insumo del motor de
mitología (§4).

**Diferencia clave activación vs. carga de campo**: la activación (§2) es privada,
transitoria, por tick, y modula solo el colapso conductual de *ese* agente. La
carga del campo (§3) es pública, persistente (con decay), acumulada por *todos*
los agentes de la tribu, y es lo único que puede eventualmente cristalizar en
vocabulario compartido.

---

## 4. Cristalización: de campo cargado a `MythCrystal`

`MythologyEngine` (`core/social/mythology.py`), llamado desde
`AgentCore.on_day()`:

1. **`ContextoEnunciativo`** (portado del mismo formalismo que `collapse_state`):
   `temperatura_semantica` (presión emocional+mítica), `intencionalidad` (qué tan
   cargado está el par dominante), `ruido_ambiental` (confusión). Su
   `probabilidad_cristalizacion() = min(1, temperatura×intencionalidad + ruido×0.3)`.
2. **`_check_proto_myths`**: si esa probabilidad supera `_PROTO_MYTH_THRESHOLD`,
   nace un `ProtoMito(tipo, par, dia_origen, intensidad_contexto)`. El `tipo` sale
   de `_PAIR_TO_MYTH_TYPE[frozenset(par)]` — un mapa **fijo** que traduce pares de
   arquetipos a una de 5 categorías campbellianas (cosmogonía, teogonía,
   antropogonía, escatología, mito_moral). Esto es Capa A: la *taxonomía* de tipos
   de mito posibles está prefijada (como los arquetipos mismos); *cuál* par
   cristaliza y *cuándo* no lo está.
3. **`on_social_transmission`**: cuando dos agentes comparten una experiencia
   emocional intensa, el proto-mito más avanzado (mayor coherencia) recibe
   `transmitir(+1.0)`. Necesita `coherencia ≥ 3.0` (`_COHERENCE_TO_CRYSTALLIZE`)
   para cristalizar — es decir, **transmisión social real entre agentes**, no un
   contador de tiempo. Un proto-mito que nadie comparte nunca cristaliza.
4. Al cristalizar: `MythCrystal(name, tipo, par, protagonista_id, antagonista_id,
   tribe_id, ...)`. El `name` es generado (ver `_deity_name`, hash determinista
   por arquetipo+tribu → epíteto), no elegido de una lista de nombres con
   significado. Si el protagonista muere, el mito no desaparece: se vuelve
   `Leyenda` (`es_leyenda=True`) que sigue irradiando efectos con intensidad
   decreciente (0.998/día).
5. **Distorsión transgeneracional** (`_distort_myths`): el relato vivo
   (`relato_actual`) diverge del original con el tiempo — otro punto donde el
   *mecanismo* de distorsión es diseño, pero el *contenido* distorsionado en cada
   corrida es producto de la historia real de esa simulación.

---

## 5. Cómo un arquetipo influye la conducta (dos vías distintas)

1. **Directa, individual**: `ArchetypeVector.action_bias()` es uno de los 6
   canales de `collapse_state` (peso 0.30 — el más alto de todos). Esto pasa
   *siempre*, con o sin ningún mito cristalizado.
2. **Indirecta, colectiva**: `CollectiveField.radiate()` traduce las cargas
   simbólicas del campo en deltas de acción (peso 0.10 en `collapse_state`) —
   ej.: `sombra` alta empuja competencia/aislamiento; `trickster` alto empuja
   manipulación. Esta vía es cómo el inconsciente colectivo "presiona" de vuelta
   sobre cada individuo, incluso uno que nunca vivió el evento original.

Un `MythCrystal` activo también aplica `_MYTH_EFFECTS[tipo]` directamente a los
agentes afines a su par arquetípico (`apply_myth_effects`) — la tercera vía, más
fuerte y explícita, reservada a mitos ya consolidados.

---

## 6. Qué vocabulario simbólico puede aparecer, y qué lo impide

El único vocabulario simbólico que el sistema puede producir es:

- Los **12 nombres de arquetipo** (fijos, Capa A — son la gramática, no el léxico).
- Los **5 tipos de mito campbellianos** (fijos, Capa A — la taxonomía narrativa).
- Los **nombres generados** de mitos/deidades (`_deity_name`, hash determinista
  arquetipo+tribu — no elegidos de una lista con significado).
- Las **palabras fonéticas emergentes** de `EmergentLexiconSystem` (sílabas
  aleatorias, nunca palabras con significado preexistente).

Lo que el sistema **no puede** hacer, por diseño, es introducir un juicio moral,
una causa atribuida, o un frame narrativo que no haya cristalizado primero en
alguna de estas estructuras — ver los tres slots de Capa B en `AGENT_BRAIN.md` §2.2
y la auditoría completa en `EMERGENCE.md`.

---

## 7. Recorrido completo de ejemplo

```
ESTÍMULO            Un forastero se acerca a la tribu (kind="agente", social=1.0)
      │
PERCEPCIÓN          PerceptionSystem.witness() lo registra (dentro del radio)
      │
ACTIVACIÓN          ResonanceOperator: agente con self.gobernante alto →
                     archetype_activation={"gobernante": 0.018}
                     AffectiveOperator: agente paranoico → valence = -0.6, arousal = 0.7
      │
RESONANCIA          Si "gobernante" ya cristalizó en field.symbols (≥0.55) →
                     narrative_frame = "gobernante" (préstamo, no invención)
      │
MEMORIA             Si co-ocurrió antes con "hambruna" (fuerza≥0.40) en la
                     PerceptionSystem del agente → attributed_cause = "hambruna"
      │
CAMPO               La interacción real (si termina en conflicto) hace
                     collective_field.absorb_interaction(..., "conflicto_explotacion")
                     → symbols["sombra"] += 0.10, emotional_pressure += 0.08
      │
CRISTALIZACIÓN      Tras suficiente temperatura + transmisión social repetida,
                     nace un ProtoMito(tipo="mito_moral", par=("gobernante","sombra"))
      │
MITO                Tras coherencia ≥ 3.0 transmisiones → MythCrystal cristaliza,
                     name="El Custodio de Sombra" (generado)
      │
CONDUCTA            apply_myth_effects() empuja a los agentes afines a ese par;
                     el PRÓXIMO forastero que llegue puede activar
                     moral_judgment = "El Custodio de Sombra" en cualquier agente
                     cuya activación resuene con ese par — el mito ya es vocabulario
                     disponible para toda la tribu.
```
