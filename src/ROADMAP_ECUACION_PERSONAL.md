# Ecuación Personal y Mini Cerebro — Roadmap (v2, alineado a la filosofía de emergencia)

> Rama de trabajo: `xperiment`
> Fecha: 2026-06-05
> Estado: Pendiente de aprobación
> Reemplaza la v1. El cambio de fondo: **nada de contenido simbólico se programa. Solo
> se instalan slots vacíos y el mismo motor de colapso del proyecto, una escala más abajo.**

---

## Principio rector (no negociable)

El proyecto declara dos capas (`02-PSYCHE_ORIGEN_INCONSCIENTE.md`):

- **Capa A — prefijada.** La *gramática* psíquica: módulos, instintos, y los arquetipos
  como **categorías vacías**. No emerge, ya está. Es legítimo instalarla.
- **Capa B — emergente.** El *vocabulario* simbólico: el nombre del mal, qué es sagrado,
  los mitos, los juicios morales. **No se programa: cristaliza** por fluctuación →
  resonancia → umbral → colapso.

La v1 de este roadmap violaba esto: sus operadores devolvían símbolos elegidos por el
diseñador (`return "explotación"`, enums de `moral_judgment ∈ {justo, injusto, sagrado…}`).
Eso es inyectar Capa B prefabricada. **Queda prohibido.**

**Regla de oro de esta v2:**
> El sistema instala los *slots* (las variables de la ecuación personal) **vacíos**.
> Cada agente los llena con el contenido que su historia de interacción vaya
> precipitando. Ningún `if` del diseñador decide qué significa nada.

---

## Las dos capas de la propuesta

| Capa | Qué agrega | Dónde se inserta |
|---|---|---|
| **InterpretiveFilter** | Convierte cada estímulo en una respuesta afectiva **escalar** (Capa A pura). El *nombre* del significado lo toma prestado del vocabulario que ya emergió en el colectivo — nunca de un enum. | Entre `WorldSnapshot`/percepción y `collapse_state` |
| **MentalVault** | Sustrato mental por agente cuyos enlaces **emergen por el mismo colapso estocástico** que usa el `CollectiveField`, no por reglas psicodinámicas deterministas. | Nuevo módulo `core/agents/mental_vault/` |

---

## TENSIÓN FILOSÓFICA — cómo se resuelve

| Componente | v1 (violaba) | v2 (alineado) |
|---|---|---|
| **InterpretiveFilter** | Operadores `if archetype > x: return "símbolo"` | Operadores que emiten **solo escalares** (`valence`, `arousal`, `relevance`, deltas de activación arquetípica). Los campos simbólicos (`attributed_cause`, `moral_judgment`, `narrative_frame`) nacen **vacíos** y se rellenan *por referencia* al vocabulario emergente (`CollectiveField` / `emergent_lexicon` / `mythology`). Si ese vocabulario aún no existe, el agente *siente* pero no *nombra*. |
| **MentalVault** | Motor de reglas MiniEllo→MiniSuperyo→MiniYo (sistema experto determinista) + clasificador junguiano que **asigna** arquetipo + compuertas piagetianas duras | Enlaces que **cristalizan por resonancia + umbral estocástico** (la física de `CollectiveField`, a escala individual). El arquetipo de una neurona **emerge** de a qué símbolos colectivos resuena. Las etapas piagetianas no son compuertas: **modulan la temperatura del colapso** (ruido/umbral). |

**El insight central:** no construimos un motor *distinto* para el individuo. **Recursamos el
mismo motor de emergencia hacia abajo.** El inconsciente personal emerge por la misma física
que el colectivo, una escala más abajo. Auto-similaridad fractal del colapso.

---

## FASE 1 — InterpretiveFilter (la Ecuación Personal, content-free)

**Prioridad:** Alta · **Riesgo:** Bajo · **Valor:** Alto · **Esfuerzo:** 2–3 sesiones
**Estado:** ✅ Implementada (2026-06-05) — desactivada por defecto.

Módulo autocontenido, activable con flag `INTERPRETIVE_FILTER_ENABLED=1` para comparar
corridas con y sin él (disciplina A/B con KL/MIG/VFE).

### Implementación entregada

| Archivo | Rol |
|---|---|
| `core/interface/perceived_event.py` | `Stimulus` (físico) + `PerceivedEvent` (slots Capa B vacíos + `action_bias()` content-free) |
| `core/agents/psyche/interpretive_filter.py` | `InterpretiveFilter` con 4 operadores que devuelven **solo escalares** + préstamo de `narrative_frame` |
| `core/agents/quantum/collapse.py` | nuevo canal `interpretive_influence` (peso 0.15) |
| `core/agents/agent.py` | flag `INTERPRETIVE_FILTER_ENABLED`, `_build_stimulus()`, cableado en `_decide_via_collapse`, `last_perceived_event` |
| `tests/test_interpretive_filter.py` | 14 tests: contrato Capa A/B, divergencia entre psiques, préstamo de vocabulario, modulación del colapso |

Validado: 14/14 tests nuevos verdes; suites existentes (quantum/repro/persistence) sin
regresión; corrida de humo de 15 días con el flag activo sin errores. Con el flag
desactivado (default) las corridas existentes son byte-idénticas.

### Qué produce — `PerceivedEvent` con SLOTS, no con contenido

```yaml
PerceivedEvent:
  # ── Capa A: escalares que el filtro SÍ calcula (estructura, no contenido) ──
  stimulus_type:        str        # categoría física del estímulo (estructura/agente/clima/muerte…)
  stimulus_id:          str
  valence:              float      # -1..+1  — sale de módulos amenaza/recompensa/apego
  arousal:              float      # 0..1    — intensidad emocional
  relevance_to_self:    float      # 0..1    — ¿me afecta?
  archetype_activation: dict       # {arquetipo: delta} — qué se activó, NO qué significa

  # ── Capa B: SLOTS VACÍOS — se rellenan por referencia al vocabulario emergente ──
  attributed_cause:     str|None = None   # se llena SOLO si la tribu ya tiene ese símbolo
  moral_judgment:       str|None = None   # idem — nace None; no hay enum del diseñador
  narrative_frame:      str|None = None   # idem — referencia a un mito ya cristalizado

  raw_stimulus:         dict       # datos crudos originales
```

**La clave:** `attributed_cause`, `moral_judgment` y `narrative_frame` **nacen `None`**.
No existe ninguna lista de valores posibles escrita por nosotros. Un agente solo puede
poner `moral_judgment = "injusto"` si el símbolo "injusticia" **ya cristalizó** en su
`CollectiveField`/`emergent_lexicon`. Antes de eso, frente a la fortaleza ajena el agente
**siente** `valence=-0.7, arousal alto, sombra+` pero **no juzga** — porque todavía no
tiene la palabra. La palabra llega después, emergente.

### Los operadores (sin contenido, solo modulación)

Cada agente instancia los operadores; todos devuelven **escalares** y **modulan
probabilidades** del colapso. Ninguno devuelve un string simbólico.

| Operador | Qué calcula (todo escalar) | De dónde sale |
|---|---|---|
| `AttentionOperator` | A qué estímulo asigna saliencia | `needs`, saliencia arquetípica, complejos activos |
| `AffectiveOperator` | `valence` + `arousal` | módulos amenaza/recompensa/apego, `bond_strength` |
| `RelevanceOperator` | `relevance_to_self` | rol, vínculos, pertenencia |
| `ResonanceOperator` | qué arquetipos se activan (deltas) | `ArchetypeVector` del agente como prior |

El `narrative_frame` **no lo elige un operador**: lo provee, *si existe*, una consulta de
solo-lectura al vocabulario colectivo. Es préstamo, no generación.

### Cómo se conecta (sin romper nada)

- **`collapse_state`**: el `PerceivedEvent` modula las probabilidades de la
  `BehavioralState` vía sus escalares (`valence`, `arousal`, deltas arquetípicos). Esto
  ya es exactamente el patrón que usa `field_influence` hoy — un canal más de sesgo.
- **`episodic_log` / `episodic_memory`**: la entrada guarda la **carga escalar**
  (`valence`, arquetipo activado, intensidad). El *texto narrado* ("lo vi como
  explotación") lo genera la capa LLM **leyendo el vocabulario que ya emergió**, no un
  string precintado en el filtro.
- **`CollectiveField.absorb_*`**: interpretaciones con `valence` extremo y
  `relevance_to_self` alto contribuyen a `emotional_pressure` — igual que hoy.

### Estímulos soportados (alcance inicial acotado — control de coste por tick)

Lista corta y fija de *categorías físicas* (no simbólicas): estructura ajena, acción de
otro agente, muerte cercana, nacimiento vinculado, clima extremo, recurso escaso,
forastero, encuentro liminal. La categoría es física; el significado emerge.

---

## FASE 2 — MentalVault (Mini Cerebro por colapso, no por reglas)

**Prioridad:** Media · **Riesgo:** Medio · **Valor:** Alto *si la Fase 1 valida*
**Esfuerzo:** 4–6 sesiones · **Condición de entrada:** la Fase 1 debe mostrar impacto
medible en divergencia KL antes de comprometer esto.

### Qué es

Un sustrato mental por agente: neuronas (conceptos) que se crean a partir de los
`PerceivedEvent`, se enlazan **por resonancia estocástica**, decaen y se podan. **No hay
árbol de reglas psicodinámicas.** El enlazado usa la misma maquinaria conceptual que la
cristalización de mitos en `CollectiveField` (`probabilidad_cristalizacion`,
temperatura/intencionalidad/ruido), pero a escala individual.

### La neurona — SLOTS vacíos

```yaml
Neuron:
  id:                     str
  significante:           str        # etiqueta perceptiva derivada del stimulus físico
  estado_energetico:      float      # 0..1 — decae con el tiempo; se refuerza al re-activarse
  carga_afectiva:         float      # viene del PerceivedEvent (escalar Capa A)
  enlaces:                dict       # {otra_neuron_id: peso} — adjacencia simple (NO NetworkX)
  arquetipo_resonante:    str|None = None   # EMERGE de a qué símbolo colectivo resuena; nace None
  tags:                   list       # categorías físicas, no juicios
```

Nada aquí trae significado precargado. `arquetipo_resonante` **nace `None`** y se llena
cuando la neurona resuena con un símbolo ya cargado en el campo — no por un clasificador
que lo asigna.

### El motor — colapso, no arbitraje

Corre **una vez por día simulado** (no por tick: amortización clave para el coste).

```
PerceivedEvents acumulados del día
        │
        ▼
1. Crear/reforzar neuronas (energía += carga afectiva)
        │
        ▼
2. ENLAZADO POR RESONANCIA (la física de CollectiveField, local):
   - se calcula un "contexto enunciativo individual"
     (temperatura = arousal acumulado; intencionalidad = energía de las
      neuronas candidatas; ruido = ansiedad del agente)
   - dos neuronas se enlazan con probabilidad = probabilidad_cristalizacion(contexto)
   - NO hay validador de reglas: hay umbral + azar, igual que un mito
        │
        ▼
3. RESONANCIA ARQUETÍPICA EMERGENTE:
   - arquetipo_resonante de una neurona = el símbolo del CollectiveField con el que
     más co-activa. Si el campo aún no tiene ese símbolo, queda None.
        │
        ▼
4. DECAY + PRUNING: energía *= factor; si supera el cap (≤ 50 neuronas), se podan
   las de menor energía.
```

Comparado con la v1: desaparecen `MiniEllo`, `MiniSuperyo`, `MiniYo` y el clasificador
que *asignaba* arquetipos. En su lugar, **la misma fluctuación → resonancia → umbral →
colapso** que ya define todo el proyecto.

### Etapas del desarrollo — moduladores, no compuertas

La edad no bloquea qué tipos de neurona pueden existir. **Modula la temperatura del
colapso**, reutilizando el `_need_factor`/plasticidad que el agente ya tiene por edad:

| Fase (edad ya modelada) | Efecto sobre el colapso mental |
|---|---|
| Niñez (`< 6`) | Ruido alto, umbral bajo → símbolos inestables, muchos enlaces efímeros |
| Adolescencia (`6–14`) | Ruido medio → enlaces más persistentes |
| Adulto (`≥ 15`) | Ruido bajo, energía más estable → worldview más coherente |

Esto es Capa A legítima: estructura que modula, no contenido inyectado. Y se apoya en el
ciclo de vida que `agent.py` ya implementa (`fase_desarrollo`, `_vigor_por_edad`).

### Feedback conductual

- Neuronas de alta energía con `arquetipo_resonante` refuerzan *levemente* ese arquetipo
  en el `ArchetypeVector` (canal de feedback mente↔psique base), con el mismo patrón de
  delta acotado que ya usan sueños y sustancias.
- La incoherencia interna (muchos enlaces contradictorios sin resolver) sube el `ruido`
  individual → más entropía en el colapso conductual → agente más impredecible. La
  "neurosis" emerge; no se programa.

### Serialización

- `MentalVault.to_dict()` / `from_dict()` → se suma al checkpoint existente.
- Opcional: una sección `vault/Personas/<nombre>/MenteInterna.md` con las neuronas más
  activas — coherente con cómo el vault ya narra cada persona.

---

## FASE 3 — Observabilidad (posterior, opcional)

Condición: Fases 1 y 2 con impacto medible y estable.

- Tab "Mentes" en el dashboard: inspector del MentalVault (grafo, energías, arquetipos
  resonantes emergidos).
- Métrica **coherencia de worldview individual** (alta = dogmatismo; baja = apertura/neurosis).
- Correlación observable: ¿los agentes con más incoherencia interna generan mitos o
  mueren primero?

---

## Criterios de aceptación (incluye el test filosófico)

```
[ Fase 1 ] → correr xperiment con flag activo → medir KL/MIG/VFE
        │
        ▼
  ¿Divergencia cultural mediblemente mayor?  ──NO→ revisar operadores antes de seguir
        │ SÍ
        ▼
  TEST FILOSÓFICO (obligatorio antes de Fase 2):
  ¿Algún símbolo, juicio o frame que aparezca en los datos fue elegido por el
  diseñador en un enum o un `if`?
        │
       SÍ → NO es emergencia: es lectura de inputs. Rediseñar.
       NO → emergencia genuina. Proceder a Fase 2.
```

La frase de cierre solo es honesta si se cumple lo anterior:

> *El inconsciente colectivo no se programa. Emerge. Y la ecuación personal de cada
> mente que lo construye también emerge — nosotros solo instalamos los slots vacíos.*
</content>
</invoke>
