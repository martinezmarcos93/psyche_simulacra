# Ecuación Personal y Mini Cerebro — Análisis y Roadmap

> Rama de trabajo: `xperiment`
> Fecha: 2026-06-04
> Estado: Pendiente de aprobación

---

## Origen de la idea

La propuesta surge de dos conceptos que se fusionan naturalmente con la arquitectura existente:

**1. La ecuación personal (filtro perceptivo)**
Concepto traído de la psicología cognitiva: cada individuo posee una "ecuación" interna construida por su historia, valores, creencias y estado emocional que transforma cualquier estímulo bruto en un *significado subjetivo*. Dos personas frente a una mansión: una ve arquitectura hermosa, la otra ve corrupción. La misma casa física, dos realidades construidas.

Variables de la ecuación:
- Historia biográfica y memorias implícitas
- Creencias nucleares y valores activos
- Estado emocional crónico y puntual
- Identidad y pertenencia grupal
- Herramientas simbólicas disponibles (vocabulario, marcos teóricos)
- Marcadores somáticos (respuesta emocional pre-racional)

**2. Mini Cerebro Artificial (por agente)**
Inspirado en el proyecto *Cerebro Artificial* — un sistema de gestión de conocimiento que aprende por etapas (Piaget), forma enlaces por impulso interno (Freud: Ello/Yo/Superyó), y clasifica conceptos por resonancia arquetípica (Jung). La propuesta es embeber una versión miniaturizada dentro de cada agente de PSYCHE SIMULACRA.

---

## Qué propone concretamente

Dos capas distintas, con valor y riesgo independientes:

| Capa | Qué agrega | Dónde se inserta |
|---|---|---|
| **InterpretiveFilter** | Transforma cada estímulo en un `PerceivedEvent` con valence, causa atribuida, juicio moral, marco narrativo | Entre `WorldSnapshot` y `CollapseEngine` |
| **MentalVault** | Grafo de conocimiento interno por agente, motor psicodinámico diario, neuronas que se crean/enlazan/olvidan, etapas piagetianas | Nuevo módulo `core/agents/mental_vault/` |

---

## Evaluación y tensión filosófica central

El corazón del proyecto declara: *"El inconsciente colectivo emerge — no se construye."*

El **InterpretiveFilter preserva** esa filosofía. Cada agente filtra distinto, de esas diferencias emerge la cultura. Nadie programa qué mito va a surgir.

El **MentalVault tensiona** esa filosofía. Si cada agente tiene un motor que explícitamente construye una worldview con reglas psicodinámicas, el inconsciente personal ya no *emerge* — se *programa*. Lo que sigue emergiendo es el colectivo, pero los ladrillos son más artificialmente ricos. Esto no está mal, pero hay que ser consciente del trade-off: se mide la emergencia colectiva de 100 psicologías-máquina, no de agentes más "vacíos".

---

## Pros y contras globales

### Pros

| Beneficio | Impacto estimado |
|---|---|
| Divergencia cognitiva genuina — dos agentes con los mismos arquetipos interpretan distinto | Alto — acelera divergencia KL entre tribus |
| Memoria semántica — los eventos se guardan con su carga interpretativa, no como datos crudos | Alto — narrativas LLM incomparablemente más ricas |
| Desarrollo cognitivo por edad — un niño interpreta diferente a un anciano | Medio — agrega ciclo de vida psicológico |
| Conflicto interno como motor de conducta — la neurosis del agente lo hace impredecible | Medio-Alto — genera "personajes" emergentes naturales |
| Diálogos liminales más profundos — los agentes del xperiment hablarían desde su historia mental, no solo sus pesos arquetípicos | Alto — relevante para el experimento ya implementado |
| Puente entre proyectos — Cerebro Artificial y PSYCHE SIMULACRA se retroalimentan como laboratorios | Alto valor investigativo |

### Contras

| Riesgo | Severidad |
|---|---|
| Performance — 100 grafos NetworkX + ciclos psicodinámicos diarios = posible 3–5× slowdown | Alta — requiere benchmark antes de comprometerse |
| Complejidad de debugging — una capa entre percepción y decisión propaga errores de forma oscura | Alta — ya es difícil rastrear por qué cristalizó un mito |
| Overspecification del individuo — si el inconsciente personal es muy programado, ¿sigue siendo ciencia ABM o es simulación narrativa dirigida? | Media — filosófico pero relevante para validación científica |
| Carga de tests — ~100–150 nuevos tests para cubrir los módulos | Media |
| Inflación teórica — Jung + quantum + Piaget + Freud + Saussure en un sistema es potente pero difícil de argumentar científicamente | Media — depende del objetivo del proyecto |

---

## Roadmap de implementación

### Fase 1 — InterpretiveFilter (Ecuación Personal)

**Prioridad:** Alta  
**Riesgo:** Bajo  
**Valor:** Alto  
**Esfuerzo estimado:** 2–3 sesiones de trabajo

Un módulo limpio y autocontenido que se inserta entre la percepción y la decisión. No requiere nuevas estructuras de datos complejas. Activable con flag `INTERPRETIVE_FILTER_ENABLED=1` para comparar simulaciones con y sin él.

#### Pipeline resultante

```
WorldSnapshot → [AttentionFilter] → [InterpretiveFilter] → PerceivedEvent[] → CollapseEngine
                                                                    │
                                                                    ├─→ episodic_log (etiquetado)
                                                                    └─→ CollectiveField (presión emocional)
```

#### Componentes a crear

**`core/interface/perceived_event.py`**
```python
@dataclass
class PerceivedEvent:
    stimulus_type:           str          # "estructura", "agente", "recurso", "clima", "muerte"...
    stimulus_id:             str
    valence:                 float        # -1.0 (muy negativo) → +1.0 (muy positivo)
    attributed_cause:        str          # "esfuerzo", "corrupción", "azar", "generosidad", "amenaza"...
    moral_judgment:          str          # "justo", "injusto", "sagrado", "profano", "neutro"
    relevance_to_self:       float        # 0.0 → 1.0 (¿me afecta directamente?)
    archetype_activation:    dict         # {"rebelde": +0.02, "sabio": -0.01, ...}
    narrative_frame:         str          # "historia de abuso", "historia de maestría", "amenaza externa"...
    raw_stimulus:            dict         # datos crudos originales
```

**`core/agents/psyche/interpretive_filter.py`**

Clase `InterpretiveFilter` con 4 operadores modulares instanciados por agente:

| Operador | Qué hace | Variables usadas |
|---|---|---|
| `AttentionOperator` | Qué nota primero el agente; qué pasa al siguiente operador y qué se ignora | `needs` (hambre→busca comida), `archetype salience`, `active_complexes` |
| `CausalAttributionOperator` | Por qué *existe* este estímulo; asigna `attributed_cause` | `paranoia`, `arquetipo rebelde/gobernante`, `complex_power`, `episodic_log` reciente |
| `EmotionalEvaluationOperator` | Valence + intensidad emocional | `active_complexes`, `mood_modifier`, `bond_strength` con el agente involucrado |
| `SocialComparisonOperator` | Qué dice este estímulo sobre yo vs. los demás | `tribe_id`, `narcisismo`, `empatía`, `rol social`, `deudas simbólicas` |
| `NarrativeFrameOperator` | En qué historia encaja este evento | `mitos activos de la tribu`, `cultural_memory`, `arquetipo dominante colectivo` |

Ejemplo de lógica del `CausalAttributionOperator`:
```python
def apply(self, stimulus, agent) -> str:
    if stimulus.tipo == "estructura" and stimulus.tamaño == "grande":
        if agent.archetypes.rebelde > 0.6 and agent.complexes.inferiority.active:
            return "explotación"
        if agent.archetypes.gobernante > 0.6:
            return "liderazgo legítimo"
        if agent.traits.apertura > 0.7:
            return "expresión creativa"
    return "causa desconocida"
```

#### Integraciones requeridas

- **`CollapseEngine`**: el `PerceivedEvent` modula directamente las probabilidades de la `BehavioralSuperposition`.
  - `valence < -0.5` → aumenta peso de *competir* o *manipular*
  - `moral_judgment == "injusto"` → aumenta peso de *competir*
  - `valence > 0.5` → aumenta peso de *cooperar*
  - `narrative_frame == "amenaza externa"` → aumenta *aislar*

- **`episodic_log`**: las entradas ya no son solo `"[EVENTO] Encontré comida"` sino `"[EVENTO] Encontré la gran fortaleza de otro grupo. La interpreté como símbolo de explotación. Sentí indignación (valence=-0.7)."`

- **`CollectiveField.absorb_event()`**: las interpretaciones con `valence` extremo y `relevance_to_self > 0.5` contribuyen a `emotional_pressure` del campo colectivo local de la tribu.

#### Tipos de estímulos soportados (alcance inicial)

1. Estructuras de otro grupo (tótem, muralla, altar, hoguera)
2. Acciones de otro agente (cooperación, conflicto, manipulación)
3. Muerte cercana (de alguien con bond_strength alto)
4. Nacimiento (propio o de alguien vinculado)
5. Evento climático extremo
6. Descubrimiento de recurso escaso
7. Entrada de un forastero al territorio
8. Encuentro en la Zona Liminal

#### Pros específicos de la Fase 1
- Directamente aplicable al xperiment ya commiteado — los diálogos liminales serían más ricos
- No rompe ningún sistema existente (flag para activar/desactivar)
- Medible científicamente: comparar KL/MIG/VFE con y sin filtro activo
- Narrativas del LLM incomparablemente más texturizadas

#### Contras específicos
- Requiere definir los tipos de estímulos con cuidado (si la lista es muy larga, cada tick hace muchas evaluaciones)
- Los operadores son inicialmente heurísticos; necesitan calibración tras primeras simulaciones
- Sin el MentalVault, los efectos del filtro son *locales* a cada tick — no hay acumulación de creencias entre días

---

### Fase 2 — MentalVault (Mini Cerebro Artificial)

**Prioridad:** Media  
**Riesgo:** Alto  
**Valor:** Alto *si la Fase 1 valida la dirección*  
**Esfuerzo estimado:** 5–8 sesiones de trabajo

**Condición de entrada:** La Fase 1 debe demostrar impacto medible en divergencia KL antes de comprometer el esfuerzo de la Fase 2.

#### Estructura interna del MentalVault

```
agent.mental_vault
    ├── graph: nx.DiGraph                   # conceptos y sus enlaces
    ├── neurons: dict[str, Neuron]          # neuronas en memoria
    ├── piaget_stage: PiagetStage           # etapa cognitiva actual
    ├── conflict_queue: list[ConflictNeuron]# conflictos pendientes de resolver
    └── energy_decay_rate: float            # qué tan rápido se olvida
```

**`Neuron` (dataclass):**
```yaml
id: neurona_agente42_00003
etapa_creacion: preoperacional
tipo: simbolo                     # esquema_sensoriomotor | simbolo | concepto | regla | conflicto
significante: casa_grande
significados_diferenciales:       # otras neuronas en el grafo
  - cueva
  - mi_refugio
estado_energetico: 0.8           # 0.0 (olvidada) → 1.0 (muy activa)
arquetipo_vinculado: gobernante  # resultado del clasificador junguiano
carga_emocional: -0.6            # viene del InterpretiveFilter
tags: [percibido, estructura, riqueza]
```

#### Subfases de implementación

**2a. Estructura base**
- `core/agents/mental_vault/mental_vault.py` — clase `MentalVault`
- `core/agents/mental_vault/neuron.py` — dataclass `Neuron`
- Lógica de pruning: máx. 50 neuronas por agente; se eliminan las de menor `estado_energetico` cuando se supera el límite
- Las neuronas se crean a partir de los `PerceivedEvent` de la Fase 1

**2b. Motor psicodinámico mínimo**

Corre **una vez por día simulado** (no por tick):

```
PerceivedEvent[] acumulados hoy
        │
        ▼
MiniEllo → propone enlace: neurona con alta energía + baja conectividad
        │
        ▼
MiniSuperyo → valida:
    - no autoenlace
    - no contradicción directa sin neurona de conflicto intermediaria
    - no enlace ya existente
        │
        ▼
MiniYo → ejecuta enlace  ──o──  crea neurona de conflicto
```

Los conflictos no resueltos se acumulan en `conflict_queue` y afectan el comportamiento.

**2c. Clasificador junguiano embebido**

La neurona nueva recibe el arquetipo que más resuena con su significante, usando el `ArchetypeVector` del agente como prior. Si el agente tiene alto `sabio`, su neurona "río" se etiqueta `sabio`. Si tiene alto `rebelde`, se etiqueta `sombra`.

**2d. Etapas piagetianas**

| Etapa | Edad simulada | Efecto en el agente |
|---|---|---|
| Sensoriomotora | 0–5 años | Solo crea neuronas de tipo `esquema_sensoriomotor`; sin simbolización; InterpretiveFilter muy binario |
| Preoperacional | 5–15 años | Puede crear `simbolo` y `conflicto`; ecuación personal activa pero rígida y egocéntrica |
| Operaciones Concretas | 15–30 años | Crea `concepto` y `regla`; interpretaciones más matizadas; el MiniYo media mejor |
| Operaciones Formales | > 30 años | Pensamiento abstracto; puede crear `arquetipo` propio; menor sesgo emocional; mayor profundidad en diálogos liminales |

**2e. Feedback conductual**

- Las neuronas de conflicto no resueltas aumentan la entropía en `BehavioralSuperposition` → el agente es más impredecible
- Las neuronas con `arquetipo_vinculado` activo refuerzan ligeramente ese arquetipo en el `ArchetypeVector` (+0.003/día mientras la neurona tenga alta energía) — feedback entre mente individual y psicología base

**2f. Serialización**

- `MentalVault.to_dict()` / `from_dict()` → integración con `CheckpointManager`
- Sync con vault de Obsidian: cada agente tendría una sección `vault/Personas/<nombre>/MenteInterna.md` con sus neuronas más activas y conflictos pendientes

**2g. Integración con narrativa LLM**

El `NarratorEngine` accede a las neuronas más activas del agente para enriquecer los prompts:
- Elegías: "El Guerrero que creía que la riqueza era corrupción, cuyas neuronas de conflicto sobre el poder quedaron sin resolver..."
- Diálogos liminales: el agente habla desde las neuronas activas de su MentalVault, no solo desde sus pesos arquetípicos del momento

#### Pros específicos de la Fase 2
- Convierte a cada agente en un "personaje" con historia intelectual propia y auditable
- Los conflictos internos como variable observable pueden correlacionarse con la emergencia de líderes, chamanes, exiliados o "locos de la tribu"
- Hace el xperiment exponencialmente más rico: el diálogo liminal estaría mediado por worldviews construidas durante meses de simulación
- Conecta directamente con Cerebro Artificial como laboratorio paralelo de validación

#### Contras específicos
- Mayor riesgo de performance — requiere benchmark obligatorio antes de comprometerse
- Los conflictos del MiniYo pueden acumularse y causar "neurosis colectivas" que provoquen extinción artificial si no se calibra el motor
- Añade ~8 archivos nuevos y ~120 tests al suite
- El vault de Obsidian con 100 MentalVaults activos puede ser difícil de navegar sin una vista dedicada en el dashboard
- Riesgo filosófico: si cada psicología individual es muy programada, la emergencia colectiva pierde parte de su mérito científico como fenómeno genuinamente espontáneo

---

### Fase 3 — Observabilidad y síntesis (posterior, opcional)

**Condición de entrada:** Fases 1 y 2 demuestran impacto medible y estable.

- Nuevo tab en el dashboard NiceGUI: **"Mentes"** — inspector de MentalVault por agente (grafo visualizado, neuronas por arquetipo, conflictos pendientes)
- Métrica nueva: **Coherencia de worldview individual** — qué tan consistente es la ecuación personal de un agente (alta coherencia = dogmatismo; baja = apertura o neurosis)
- Los prompts del LLM acceden directamente al MentalVault para narrativas hiperpersonalizadas
- Correlación observable: ¿los agentes con más conflictos internos son los que generan mitos o los que mueren primero?

---

## Recomendación de secuencia

```
[ Fase 1: InterpretiveFilter ]
        │
        ▼
  Correr xperiment con Fase 1 activa
  Medir impacto en KL/MIG/VFE
        │
        ▼
  ¿Divergencia cultural mediblemente mayor?
        │
       SÍ → [ Fase 2: MentalVault ]
        │
       NO → Revisar diseño de operadores antes de comprometerse
```

**La pregunta clave antes de aprobar la Fase 2:** ¿El InterpretiveFilter solo ya genera divergencia cultural mediblemente mayor? Si sí, el MentalVault es un refinamiento de calidad. Si no, hay que revisar el diseño de los operadores antes de agregar complejidad.

---

## Conexión con el xperiment actual

El trabajo ya commiteado en esta rama (diálogos liminales entre dos IAs) se potencia directamente con la Fase 1:

- Los `cultural_payload` que se envían al servidor liminal ya incluyen mitos, símbolos y memorias. Con el InterpretiveFilter, esas memorias tendrían carga interpretativa real.
- El `prompt_dialogo()` puede recibir el `narrative_frame` del agente como variable adicional, haciendo que cada agente hable desde *su versión* de la realidad, no solo desde los datos objetivos de su tribu.
- El resultado: dos civilizaciones que dialogan no solo con *culturas diferentes* sino con *epistemologías diferentes* — distintas formas de darle sentido al mundo.

---

*El inconsciente colectivo no se programa. Emerge. Pero cada mente que lo construye tiene su propia ecuación del mundo.*
