# Qué significa "emergencia" en PSYCHE SIMULACRA

Este documento existe para que nadie —ni el autor, ni un colaborador futuro, ni
un lector del README— pueda confundir "el sistema produce un patrón interesante"
con "el sistema decidió eso mediante un `if`". Separa, para cada subsistema
relevante, cinco capas:

- **A. Variables y estructuras diseñadas directamente** — existen porque alguien
  las escribió así; no emergen, son la gramática a priori.
- **B. Reglas de interacción diseñadas** — funciones fijas que combinan A para
  producir un número o un evento; también diseñadas, pero producen *magnitudes*,
  no *contenido simbólico*.
- **C. Estados derivados** — el resultado acumulado de aplicar B repetidamente
  sobre el historial real de una corrida. Es aquí donde empieza a haber algo que
  el diseñador no controló directamente (depende del RNG, del seed, de quién
  interactuó con quién).
- **D. Patrones que emergen de esas interacciones** — regularidades que aparecen
  en C sin que ningún paso individual las haya apuntado (una tribu con identidad
  arquetípica propia, un mito con un nombre concreto, una divergencia cultural
  medible entre grupos).
- **E. Interpretaciones narrativas generadas posteriormente** — texto en lenguaje
  natural (vía LLM) que *describe* D después de que ya ocurrió. Nunca alimenta
  hacia atrás al modelo (salvo el préstamo explícito de vocabulario ya
  cristalizado — ver más abajo).

**Regla de auditoría**: algo solo puede llamarse "emergente" (categoría D) si se
puede señalar la cadena C→D sin que ningún paso individual haya sido un
`if valor == X: asignar símbolo Y` escrito por el diseñador. Si existe ese `if`,
lo que hay es **lectura de inputs disfrazada de emergencia** — hay que llamarlo
por su nombre y, si corresponde, corregirlo.

---

## 1. Arquetipos y campo colectivo

| Capa | Qué es | Dónde |
|---|---|---|
| A | 12 nombres de arquetipo fijos; `_ACTION_AFFINITY`, `_TRANSFORMATIONS`, `ARCHETYPE_ATTENTION` (mapas fijos arquetipo↔acción/evento/atención) | `archetypes.py`, `perception.py` |
| B | `absorb_interaction`, `absorb_event` (reglas fijas: qué tipo de evento sube qué símbolo cuánto); `decay()`; `radiate()` | `collective_field.py` |
| C | El vector `symbols` de cada `CollectiveField` en un día dado — resultado acumulado de miles de `absorb_*` reales, único por tribu | runtime |
| D | Qué arquetipo termina dominando en cada tribu, y cuánto diverge una tribu de otra (medido por KL/MIG/IMI, ver `experiments/`) | runtime + métricas |
| E | El nombre generado del `MythCrystal` (`_deity_name`, hash arquetipo+tribu) y su relato en lenguaje natural (`NarratorEngine`) | `mythology.py`, `core/narrative/` |

**Veredicto**: legítimamente emergente. La taxonomía (A) y la física de carga (B)
están fijas, pero ningún paso decide *qué* arquetipo va a dominar en una tribu
dada — eso depende de qué agentes con qué psicología terminaron juntos y qué les
pasó. `_PAIR_TO_MYTH_TYPE` (mapa fijo par→tipo de mito) es Capa A defendible:
fija la *forma* narrativa posible (5 categorías campbellianas), no *cuál* mito
cristaliza ni con qué nombre.

---

## 2. `InterpretiveFilter` (Fase 1 — Ecuación Personal)

| Capa | Qué es | Dónde |
|---|---|---|
| A | `Stimulus.kind` (8 categorías físicas fijas); rasgos de personalidad del agente | `perceived_event.py`, `traits.py` |
| B | `AttentionOperator`, `AffectiveOperator`, `RelevanceOperator`, `ResonanceOperator` — 4 funciones fijas que combinan A en escalares (`valence`, `arousal`, `relevance_to_self`, deltas de activación) | `interpretive_filter.py` |
| C | El `PerceivedEvent` concreto de un agente en un tick concreto | runtime |
| D | Que dos psiques distintas interpreten el mismo estímulo físico con signo opuesto (validado por test); que un agente ansioso sienta la misma categoría distinto según su estado | runtime + `tests/test_interpretive_filter.py` |
| E | (si el agente narra el evento en su log episódico vía LLM) | `core/narrative/` |

Los tres slots de Capa B del `PerceivedEvent` (`narrative_frame`,
`attributed_cause`, `moral_judgment`) están diseñados explícitamente para **no**
tener una vía directa de C: nacen `None` y solo se llenan por *préstamo* de algo
que ya cristalizó en otra parte (§1, o la memoria causal propia del agente, o un
`MythCrystal` de tipo `mito_moral`). Antes de esta sesión (2026-09-21),
`attributed_cause` y `moral_judgment` estaban declarados pero **nunca se llenaban
en ningún punto del código** — un slot vacío para siempre no es "emergencia
todavía no ocurrida", es una función sin implementar. Se completó reutilizando
estructuras que ya existían (`PerceptionSystem._causal_assocs`,
`MythologyEngine.active_myths`) — ver `experiments/2026-09-21-fase1-ecuacion-personal.md`.

**Veredicto**: limpio. No hay ningún `if kind == "muerte": return "duelo"` en
ningún operador — se verificó línea por línea (ver ese mismo experimento, sección
"test filosófico").

---

## 3. `MentalVault` (Fase 2)

| Capa | Qué es | Dónde |
|---|---|---|
| A | `neuron_id()` (categoría física + signo de valencia); `_FASE_FACTOR` (moduladores de edad) | `mental_vault.py` |
| B | Enlazado probabilístico vía `ContextoEnunciativo.probabilidad_cristalizacion()` (la misma fórmula que usa `MythologyEngine`, a escala individual); decay/pruning | `mental_vault.py` |
| C | El grafo de `Neuron` de un agente en un momento dado | runtime |
| D | `worldview_coherence()` bajo — es decir, incoherencia interna medible, sin que nadie haya escrito "este agente está en crisis" | runtime |
| E | (no hay narrativa directa del vault todavía — ver límite en `MENTAL_VAULT.md` §9) | — |

**Veredicto**: limpio, y es el subsistema más disciplinado del proyecto en este
sentido — no tiene ningún árbol de reglas psicodinámicas (la v1 del roadmap, que
sí lo tenía, fue descartada explícitamente por esto).

---

## 4. Dónde el proyecto SÍ fija contenido a mano (y por qué está bien)

Ser honesto también significa no fingir que todo es libre. Estas decisiones son
Capa A deliberada, documentada como tal desde el propio roadmap
(`02-PSYCHE_ORIGEN_INCONSCIENTE.md`, citado en
`src/ROADMAP_ECUACION_PERSONAL.md`):

- Los **12 arquetipos** y sus nombres son fijos — Jung no emerge, se instala.
- Los **6 complejos** y sus triggers contextuales (`_DEFAULT_TRIGGERS`) son fijos.
- Los pesos de canal de `collapse_state` (0.30/0.25/0.20/0.15/0.10/0.15) son
  fijos y elegidos a mano, no ajustados por ningún proceso de aprendizaje.
- Las **8 categorías físicas** de `Stimulus.kind` son una lista cerrada.
- Los **5 tipos de mito campbellianos** son una lista cerrada.
- Los umbrales de cristalización (`_VOCAB_THRESHOLD=0.55`, `_CAUSE_THRESHOLD=0.40`,
  `_COHERENCE_TO_CRYSTALLIZE=3.0`, `_PROTO_MYTH_THRESHOLD`) son constantes elegidas
  a mano, no derivadas de un principio.

La línea que el proyecto traza —y que este documento existe para vigilar— no es
"nada debe estar diseñado" (eso sería imposible: hasta el RNG necesita una
semilla). Es: **el vocabulario simbólico concreto que aparece en los datos de una
corrida particular** (qué mito cristalizó, con qué nombre, qué agente lo
protagoniza, qué juicio moral se le atribuye a qué situación) no puede haber sido
elegido por un `if`/enum del diseñador — tiene que ser trazable a una cadena
estocástica que empieza en A/B y pasa por C.

---

## 5. Limitación arquitectónica conocida (no oculta)

`MythologyEngine` es una única instancia global en `AgentCore`
(`self.mythology_engine`), no una instancia por tribu — a diferencia de
`CollectiveField`, que sí tiene versión local por tribu
(`TribeManager.get_local_field`). El README describe "MythologyEngine local —
mitos independientes por tribu" como si fuera así; el código actual no lo es.
`MythCrystal.tribe_id` etiqueta de qué tribu salió cada mito, así que hay
atribución, pero el *motor* de cristalización (umbrales, coherencia acumulada) es
compartido entre todas las tribus. Esto no invalida la emergencia (el `par` y el
`tribe_id` de cada mito siguen siendo resultado de la historia real de esa
tribu), pero sí significa que la independencia entre mitologías tribales es más
débil de lo que sugiere la documentación de más alto nivel. Ver
`docs/DEVELOPMENT_LOG.md` para cuándo se detectó esto (sesión 2026-09-21, durante
la implementación de `_borrow_judgment` en `InterpretiveFilter`, que sí puede
tomar prestado el mito de *cualquier* tribu, no solo la propia, precisamente por
esta razón arquitectónica).

---

## 6. Checklist para auditar código nuevo contra este documento

Antes de mergear cualquier cambio a `core/agents/psyche/`, `core/social/`, o
`core/agents/mental_vault/`, preguntar:

1. ¿Esta función devuelve un símbolo/nombre/juicio directamente desde un `if` o
   un `dict` de contenido, o devuelve un escalar / referencia a algo que ya
   existía en otro sistema?
2. Si devuelve una referencia prestada: ¿la fuente de esa referencia (campo,
   memoria causal, mitología) pudo, en principio, no tener nada que prestar? Si
   la respuesta es "no, siempre hay algo" (por ejemplo, un fallback que inventa
   contenido cuando no hay vocabulario), **eso rompe la regla**.
3. ¿Un test verifica explícitamente el caso "sin vocabulario todavía → None"?
   (Ver los patrones en `tests/test_interpretive_filter.py`.)

Si las tres respuestas son correctas, el cambio pertenece a la categoría B/D de
este documento. Si no, hay que rediseñarlo antes de mergear — no documentarlo
como si emergiera.
