# PSYCHE SIMULACRA — IDEAS DE IMPLEMENTACIÓN
## Expansión de Complejidad: Tiempo, Clima, Economía y Métricas

> *Este documento es un backlog vivo de ideas a implementar. Cada sección tiene una nota de complejidad estimada (🟢 baja / 🟡 media / 🔴 alta) y dependencias.*

---

## I. CRONOLOGÍA Y PASO DEL TIEMPO

### Concepto central
**1 día simulado = 10 minutos reales.**
Esto implica que el motor corre en tiempo real escalado, no por pasos discretos arbitrarios.

```
1 día simulado    = 10 min reales
1 hora simulada   = 25 segundos reales
1 semana simulada = 70 min reales
1 mes simulado    = ~5 horas reales
1 año simulado    = ~60 horas reales (2.5 días corridos)
```

---

### 1.1 Motor de Tiempo

- 🟢 **Tick granular:** Cada tick = 1 hora simulada. El motor procesa ~24 ticks por ciclo-día.
- 🟢 **Reloj global:** Un objeto `SimulationClock` que todos los agentes consultan. Expone: hora, día, día_semana, estación, año.
- 🟡 **Tiempo acelerado variable:** Permitir pausar, acelerar (×2, ×5) o ir a tiempo real durante observación.
- 🟡 **Eventos temporales:** Cosas que ocurren en fechas específicas (festivales, elecciones, estaciones).
- 🔴 **Memoria temporal:** Los agentes recuerdan *cuándo* ocurrieron eventos, no solo que ocurrieron. El tiempo transcurrido modula el peso emocional (el duelo se procesa, la euforia decae).

---

### 1.2 Rutinas Diarias

Cada agente tiene un **schedule** generado desde su perfil psicológico y rol social:

```
ESTRUCTURA DEL DÍA (24 slots de 1 hora)
─────────────────────────────────────────
00-06h  Sueño (procesamiento onírico activo)
06-07h  Despertar / rutina matinal
07-08h  Alimentación
08-12h  Trabajo / actividad principal
12-13h  Almuerzo / pausa social
13-17h  Trabajo / actividad principal
17-19h  Tiempo libre (interacciones electivas)
19-20h  Alimentación
20-23h  Ocio, vínculos afectivos, reflexión
23-00h  Transición al sueño
```

Ideas específicas:

- 🟢 **Schedule base por rol social:** Un Guerrero tiene rutina distinta a un Sabio o un Comerciante.
- 🟢 **Desviación arquetípica del schedule:** Un agente con `trickster` alto tiende a romper su rutina. Con `responsabilidad` alta, la cumple rígidamente.
- 🟡 **Rutinas de fin de semana:** Diferenciadas. Más interacción social, menos trabajo.
- 🟡 **Rutinas alteradas por estado emocional:** Depresión → incumplimiento del schedule. Euforia → extensión de tiempo social.
- 🟡 **Necesidades básicas como variables de estado:** `hambre`, `fatiga`, `sociabilidad_necesaria`. Si no se satisfacen, generan stress que altera arquetipos.
- 🔴 **Rutinas que evolucionan con el tiempo:** Un agente cambia sus hábitos después de un evento traumático. Su schedule muta.

---

### 1.3 Sueño y Procesamiento Onírico

- 🟢 **Fase de sueño obligatoria:** Si un agente no duerme lo suficiente, acumula `fatiga_cognitiva` que degrada decisiones.
- 🟡 **Calidad de sueño variable:** Ansiedad alta → sueño fragmentado → menor procesamiento de trauma.
- 🟡 **Sueños generados en tiempo de sueño:** El `DreamEngine` se activa durante las horas de sueño del agente.
- 🔴 **Pesadillas colectivas:** Si el campo colectivo tiene alta carga de un símbolo, múltiples agentes sueñan variaciones del mismo símbolo la misma noche. Eso es inconsciente colectivo funcionando.

---

### 1.4 Ciclos Temporales Más Largos

- 🟡 **Ciclos semanales:** Fatiga acumulada, anticipación del "descanso".
- 🟡 **Ciclos mensuales:** Para agentes con biología modelada, variaciones cíclicas de humor.
- 🟡 **Ciclos estacionales:** Las estaciones afectan humor, productividad, sexualidad, conflictos (ver Clima).
- 🔴 **Ciclos de vida:** Los agentes envejecen. Sus arquetipos evolucionan con la edad. Un arquetipo `héroe` en un joven se transforma en `sabio` en la vejez (individuación natural).
- 🔴 **Reproducción y muerte:** Nuevos agentes nacen con arquetipos heredados + variación. Agentes mueren por vejez, enfermedad, conflicto. La muerte de un agente importante dispara luto colectivo y altera el campo.

---

## II. CLIMA Y ENTORNO FÍSICO

### Concepto central
El clima no es decorado. Es un **operador de modulación** que afecta directamente el vector de estado conductual de todos los agentes simultáneamente. El ambiente es un agente más.

---

### 2.1 Sistema Climático

- 🟢 **Variables climáticas básicas:**
  - `temperatura` (°C, continua)
  - `precipitacion` (0→1: seco → diluvio)
  - `luminosidad` (0→1, afectada por nubosidad y estación)
  - `viento` (0→1)
  - `humedad` (0→1)

- 🟢 **Estaciones del año:** Cada estación tiene distribuciones climáticas características.
- 🟡 **Clima estocástico con tendencia:** No aleatorio puro — sigue patrones realistas con sorpresas.
- 🟡 **Microclimas por zona:** La Forja está más caliente. El Bosque más frío y húmedo. El mercado recibe todo el viento.
- 🔴 **Eventos climáticos extremos:** Tormenta eléctrica, sequía prolongada, nevada inesperada. Cada uno es un evento colectivo con impacto en el campo.

---

### 2.2 Efectos del Clima en los Agentes

```
FRÍO EXTREMO
  → fatiga +0.20
  → aislamiento social +0.30 (menos interacciones)
  → agresividad +0.10 (irritabilidad por incomodidad)
  → consumo de recursos +0.25 (más comida, combustible)
  → mood_base -0.15

CALOR EXTREMO
  → fatiga +0.25
  → impulsividad +0.15
  → agresividad +0.20 (correlación documentada en psicología social)
  → libido variable +0.10

LLUVIA MODERADA
  → introspección +0.20 (menos interacciones externas)
  → melancolía +0.15 (activa complejos de soledad)
  → productividad laboral -0.10

LLUVIA INTENSA / TORMENTA
  → ansiedad +0.25
  → búsqueda de refugio → fuerza interacciones familiares/de hogar
  → potencial de conflicto doméstico +0.20

SOLEADO Y TEMPLADO
  → humor_base +0.20
  → sociabilidad +0.25
  → productividad +0.15
  → libido +0.10

NIEBLA
  → disociación +0.15
  → paranoia +0.10
  → creatividad/simbolismo +0.20 (activa trickster, sombra)
```

- 🟡 **Modulación por rasgos:** Un agente con `neuroticismo` alto es más afectado por clima adverso que uno con alta `estabilidad_emocional`.
- 🟡 **Adaptación climática:** Agentes que llevan meses en frío se adaptan parcialmente (resiliencia climática).
- 🔴 **Clima como catalizador de eventos colectivos:** Una sequía prolongada crea escasez → tensión económica → conflicto → potencial estado liminal colectivo.

---

### 2.3 Entorno Físico y Locaciones

- 🟢 **Mapa de zonas:** Hogar, Mercado, Templo, Forja, Biblioteca, Campo, Taberna, etc.
- 🟢 **Los agentes se mueven entre zonas** según su schedule y estado.
- 🟡 **Las interacciones ocurren en zonas:** Solo puedes interactuar con agentes en tu misma zona en ese tick.
- 🟡 **Zonas con atmósfera propia:** La Taberna favorece impulsividad. El Templo favorece introspección. La Biblioteca activa el Sabio.
- 🔴 **Zonas que evolucionan:** Un Mercado que prospera atrae más agentes → densidad → más interacciones → más emergencia cultural.

---

## III. ECONOMÍA

### Concepto central
La economía no es un sistema de puntos. Es una **estructura de poder simbólico** que determina qué agentes pueden satisfacer sus necesidades, quiénes dependen de quiénes, y cómo eso moldea la psique colectiva.

---

### 3.1 Sistema Monetario Base

- 🟢 **Moneda única:** `aurum` (o el nombre que elija el proyecto). Valor relativo al coste de vida base.
- 🟢 **Salario por rol social:** Cada rol tiene un ingreso base diario. Hay varianza por habilidad.
- 🟢 **Coste de vida básico:** Alimentación + refugio = gasto mínimo diario para no caer en `privación`.
- 🟡 **Capital acumulable:** Los agentes pueden ahorrar, invertir, perder.
- 🟡 **Inflación emergente:** Si el campo tiene alta ansiedad, el intercambio se contrae → deflación conductual.
- 🔴 **Clases económicas dinámicas:** Los agentes pueden ascender o descender de clase. Eso altera arquetipos (`poder` crece con riqueza, `inferioridad` crece con pobreza).

---

### 3.2 Roles Económicos y Acceso al Dinero

```
ROL              INGRESO BASE   ACCESO A CAPITAL   LÍMITE SOCIAL
──────────────── ────────────── ────────────────── ─────────────
Gobernante/Noble Alto           Muy alto           Puede acumular ilimitado
Comerciante      Medio-alto     Alto               Limitado por red
Artesano         Medio          Medio              Estable pero rígido
Educador         Medio-bajo     Bajo               Prestigio simbólico ≠ dinero
Guerrero         Medio          Bajo-medio         Ingreso por campaña
Agricultor       Bajo           Muy bajo           Subsistencia
Sanador          Variable       Bajo               Dones vs dinero
Marginado        Mínimo         Ninguno            Economía paralela/robo
Místico/Sabio    Donaciones     Bajo               Economía simbólica
```

- 🟡 **Economía informal:** Trueque entre agentes que no tienen dinero o desconfían del sistema.
- 🟡 **Deuda:** Los agentes pueden pedir prestado. La deuda crea dependencia → activa `poder` y `inferioridad`.
- 🟡 **Herencia:** Un agente que muere transfiere capital a sus vínculos familiares.
- 🔴 **Corrupción económica:** Agentes con alto `gobernante` + alto `sombra` pueden acumular dinero de formas que dañan a otros. Esto debería emerger, no estar programado.
- 🔴 **Monopolios simbólicos:** Un agente que controla el Templo controla el capital simbólico aunque no el dinero. Equivalencia entre poder económico y poder arquetípico.

---

### 3.3 Para Qué Sirve el Dinero

```
NECESIDADES BÁSICAS
  - Alimentación diaria (costo fijo)
  - Alquiler/mantenimiento de hogar
  - Ropa adecuada al clima

NECESIDADES SOCIALES
  - Acceso a zonas premium (Taberna, Mercado central)
  - Regalos para fortalecer vínculos (bond_strength +)
  - Rituales y ceremonias (acceso al Templo)

INVERSIÓN Y CRECIMIENTO
  - Aprender habilidades nuevas
  - Abrir un negocio (nodo económico propio)
  - Contratar servicios de otros agentes

PODER SIMBÓLICO
  - Financiar rituales colectivos → influencia en campo memético
  - Patronazgo de artistas/sabios → capital simbólico
  - Soborno → manipulación de red social

CONSECUENCIAS DE LA POBREZA
  - privación → fatiga + ansiedad + sombra acumulada
  - No acceder a zonas → aislamiento social forzado
  - Deuda → pérdida de autonomía → complejo de inferioridad activado crónicamente
  - Desesperación extrema → umbral de conducta antisocial
```

---

### 3.4 Mercado como Sistema Emergente

- 🟡 **Oferta y demanda básica:** El precio de bienes fluctúa según disponibilidad y demanda de agentes.
- 🟡 **Reputación comercial:** Un Comerciante con alta `amabilidad` tiene más clientes recurrentes.
- 🔴 **Crisis económicas emergentes:** Si muchos agentes no pueden costear lo básico → tensión → potencial estado liminal colectivo (revolución, plaga de robos, éxodo).
- 🔴 **Economía simbólica paralela:** En tiempos de crisis, surgen monedas alternativas, trueque, solidaridad o criminalidad. Depende del campo colectivo dominante.

---

## IV. LISTA DE CALIDAD — FACTORES A MAXIMIZAR

### 4.1 Realismo Psicológico
- [ ] Los agentes no actúan de forma óptima — cometen errores guiados por complejos
- [ ] Las decisiones tienen ambivalencia genuina (superposición cuántica real)
- [ ] El cambio psicológico es lento y no lineal (no hay arcos perfectos)
- [ ] Los agentes pueden engañarse a sí mismos (racionalización de la Sombra)
- [ ] La máscara social (Persona) puede ser radicalmente distinta al estado interno
- [ ] Memoria sesgada: los eventos se recuerdan coloreados por el estado emocional en que ocurrieron

### 4.2 Emergencia Genuina
- [ ] Ningún fenómeno colectivo (mito, chivo expiatorio, líder) está hardcodeado
- [ ] El campo colectivo debe poder sorprender al diseñador
- [ ] Las redes sociales deben restructurarse sin intervención
- [ ] Las crisis deben poder escalar o resolverse solas

### 4.3 Coherencia Narrativa
- [ ] Cada agente tiene una historia rastreable en el vault de Obsidian
- [ ] Los eventos tienen causas que se pueden rastrear hacia atrás en el log
- [ ] Las transformaciones arquetípicas tienen sentido en función de la historia del agente
- [ ] El vault es legible como una novela si se ordenan los eventos

### 4.4 Robustez Técnica
- [ ] El sistema no se rompe si un agente muere
- [ ] Las interacciones concurrentes no producen race conditions
- [ ] El vault puede corromperse parcialmente sin perder la simulación
- [ ] Los datasets se guardan en tiempo real (no solo al final del ciclo)

### 4.5 Observabilidad
- [ ] Cada decisión de cada agente tiene un log con su razonamiento (probabilidades)
- [ ] El campo colectivo tiene una visualización en tiempo real
- [ ] Se puede pausar la simulación e inspeccionar cualquier agente en detalle
- [ ] Se puede "rebobinar" a cualquier ciclo pasado

---

## V. MÉTRICAS — DATASETS COMPLETOS

### Dataset 1: `agent_snapshots` — Estado de cada agente por ciclo

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `snapshot_id` | UUID | PK |
| `agent_id` | str | FK → agente |
| `ciclo` | int | Tick de simulación |
| `timestamp_real` | datetime | Momento real del snapshot |
| `hora_simulada` | int | 0-23 |
| `dia_simulado` | int | Día absoluto |
| `estacion` | str | primavera/verano/otoño/invierno |
| `locacion` | str | Zona donde está el agente |
| `energia` | float | 0-1 |
| `hambre` | float | 0-1 |
| `fatiga` | float | 0-1 |
| `emocion_dominante` | str | Categoría emocional actual |
| `humor_base` | float | -1 → 1 |
| `ansiedad` | float | 0-1 |
| `archetype_self` | float | |
| `archetype_shadow` | float | |
| `archetype_persona` | float | |
| `archetype_hero` | float | |
| `archetype_sage` | float | |
| `archetype_trickster` | float | |
| `archetype_anima` | float | |
| `archetype_ruler` | float | |
| `archetype_rebel` | float | |
| `archetype_child` | float | |
| `complex_abandonment` | float | |
| `complex_inferiority` | float | |
| `complex_power` | float | |
| `complex_guilt` | float | |
| `trait_openness` | float | |
| `trait_conscientiousness` | float | |
| `trait_extraversion` | float | |
| `trait_agreeableness` | float | |
| `trait_neuroticism` | float | |
| `trait_anxiety` | float | |
| `trait_impulsivity` | float | |
| `trait_empathy` | float | |
| `quantum_state_vector` | JSON | [coop, comp, aisle, manip] |
| `last_collapse` | str | Última acción colapsada |
| `dinero` | float | Capital actual |
| `deuda` | float | Deuda acumulada |
| `clase_economica` | str | bajo/medio/alto/elite |
| `red_size` | int | Cantidad de vínculos activos |
| `bond_avg_strength` | float | Promedio de fuerza de vínculos |
| `entanglements_count` | int | Agentes entrelazados actualmente |
| `sleep_quality_last` | float | Calidad del último sueño |
| `dream_symbol_last` | str | Símbolo del último sueño |
| `individuation_index` | float | Proxy: self / (shadow + persona) |

---

### Dataset 2: `interactions` — Cada interacción entre agentes

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `interaction_id` | UUID | PK |
| `ciclo` | int | |
| `agent_a` | str | |
| `agent_b` | str | |
| `locacion` | str | Donde ocurrió |
| `tipo_interaccion` | str | cooperacion/conflicto/ritual/economica/afectiva |
| `iniciador` | str | Quién inició |
| `archetype_resonance` | float | Similitud vectorial arquetípica |
| `complex_triggered_a` | str | Complejo activado en A |
| `complex_triggered_b` | str | Complejo activado en B |
| `quantum_state_pre_a` | JSON | Vector de A antes |
| `quantum_state_pre_b` | JSON | Vector de B antes |
| `collapse_result_a` | str | Acción colapsada de A |
| `collapse_result_b` | str | Acción colapsada de B |
| `outcome` | str | Resultado neto |
| `bond_delta` | float | Cambio en fuerza del vínculo |
| `shadow_projection` | bool | ¿Hubo proyección de sombra? |
| `field_contribution` | JSON | Qué aportó al campo colectivo |
| `clima_momento` | JSON | Estado climático durante la interacción |
| `transferencia_economica` | float | Dinero transferido (+ o -) |
| `nueva_entanglement` | bool | ¿Se creó entrelazamiento? |
| `duracion_ticks` | int | Cuántos ticks duró la interacción |

---

### Dataset 3: `collective_field_history` — Estado del campo por ciclo

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `field_snapshot_id` | UUID | PK |
| `ciclo` | int | |
| `symbol_fear` | float | Carga del símbolo miedo |
| `symbol_hope` | float | |
| `symbol_death` | float | |
| `symbol_rebirth` | float | |
| `symbol_hero` | float | |
| `symbol_shadow` | float | |
| `symbol_mother` | float | |
| `symbol_war` | float | |
| `symbol_love` | float | |
| `symbol_chaos` | float | |
| `archetype_dominant` | str | Arquetipo más activo colectivamente |
| `emotional_pressure` | float | Tensión social acumulada |
| `polarization_index` | float | Fragmentación de la red |
| `myth_count_active` | int | Mitos activos actualmente |
| `scapegoat_id` | str | Agente más proyectado |
| `hero_id` | str | Agente con más proyección positiva |
| `collective_mood` | float | -1 → 1 |
| `superradiance_index` | float | Sincronización emocional colectiva |
| `liminality_active` | bool | ¿Estado liminal colectivo? |
| `liminality_type` | str | Tipo si activo |
| `total_interactions_day` | int | Interacciones en el día |
| `shadow_projections_day` | int | Proyecciones de sombra en el día |
| `economic_gini` | float | Coeficiente de desigualdad |
| `mean_individuation` | float | Promedio de individuación |

---

### Dataset 4: `events_log` — Eventos significativos

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `event_id` | UUID | PK |
| `ciclo` | int | |
| `tipo` | str | trauma/revelation/death/birth/ritual/crisis/bond |
| `agentes_involucrados` | JSON | Lista de IDs |
| `descripcion` | str | Narrativa del evento |
| `impacto_arquetipos` | JSON | {arquetipo: delta} |
| `impacto_complejos` | JSON | {complejo: delta} |
| `impacto_campo` | JSON | {simbolo: delta} |
| `impacto_economico` | float | Efecto económico agregado |
| `clima_contexto` | JSON | Estado climático |
| `mito_generado` | str | Si cristalizó en mito |
| `cascada_eventos` | JSON | IDs de eventos que desencadenó |
| `severidad` | float | 0-1 |

---

### Dataset 5: `economy_log` — Transacciones económicas

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `tx_id` | UUID | PK |
| `ciclo` | int | |
| `agente_origen` | str | |
| `agente_destino` | str | Null si es gasto (comida, alquiler) |
| `monto` | float | |
| `tipo` | str | salario/compra/regalo/deuda/robo/herencia/impuesto |
| `bien_o_servicio` | str | Qué se intercambió |
| `voluntario` | bool | ¿Fue libre o forzado? |
| `impacto_bond` | float | Efecto en el vínculo |
| `impacto_poder_a` | float | Cambio en arquetipo poder del origen |
| `impacto_inferioridad_b` | float | Cambio en complejo destino |
| `precio_mercado_actual` | float | Precio de referencia del bien |

---

### Dataset 6: `climate_log` — Estado climático por ciclo

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `clima_id` | UUID | PK |
| `ciclo` | int | |
| `hora_simulada` | int | |
| `temperatura` | float | °C |
| `precipitacion` | float | 0-1 |
| `luminosidad` | float | 0-1 |
| `viento` | float | 0-1 |
| `humedad` | float | 0-1 |
| `estacion` | str | |
| `evento_extremo` | str | Null o tipo de evento |
| `mood_modifier_global` | float | Modificador calculado al campo |
| `productivity_modifier` | float | Modificador de productividad |
| `aggression_modifier` | float | Modificador de agresividad |
| `social_modifier` | float | Modificador de sociabilidad |

---

### Dataset 7: `dreams_log` — Sueños de cada agente

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `dream_id` | UUID | PK |
| `ciclo` | int | |
| `agent_id` | str | |
| `hora_simulada_inicio` | int | |
| `simbolo_central` | str | |
| `arquetipos_activos` | JSON | Lista de arquetipos en el sueño |
| `complejo_procesado` | str | |
| `trauma_origen` | str | Event_id del trauma procesado |
| `outcome` | str | integracion/amplificacion/disociacion |
| `impacto_shadow` | float | Delta en arquetipo sombra |
| `impacto_self` | float | Delta en arquetipo self |
| `calidad_sueno` | float | 0-1 |
| `colectivo_resonante` | bool | ¿Eco de sueño colectivo? |
| `simbolo_campo` | str | Si hubo resonancia, el símbolo del campo |

---

### Dataset 8: `mythology_log` — Mitos emergentes

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `myth_id` | UUID | PK |
| `ciclo_emergencia` | int | Cuándo cristalizó |
| `nombre` | str | Nombre generado |
| `tipo` | str | heroe/sombra/madre/trickster/apocalipsis/renacimiento |
| `agentes_prototipo` | JSON | Los agentes que lo encarnaron |
| `campo_trigger` | JSON | Estado del campo que lo generó |
| `narrativa` | str | Descripción del mito |
| `activo` | bool | ¿Sigue activo? |
| `ciclo_disolucion` | int | Cuándo dejó de resonar |
| `impacto_conducta_global` | float | Cuánto modificó comportamiento promedio |
| `mito_hijo` | str | Myth_id de mito derivado |

---

### Dataset 9: `agent_relations` — Red social en el tiempo

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `relation_id` | UUID | PK |
| `ciclo` | int | |
| `agent_a` | str | |
| `agent_b` | str | |
| `tipo_vinculo` | str | amistad/rivalidad/amor/familia/laboral/ritual |
| `bond_strength` | float | -1 → 1 |
| `emotional_resonance` | float | 0-1 |
| `symbolic_dependency` | float | 0-1 |
| `entangled` | bool | |
| `entanglement_origin` | str | Event_id del evento fundante |
| `historia_compartida` | int | Cantidad de interacciones acumuladas |
| `trauma_compartido` | bool | |
| `red_emocional_peso` | float | |
| `red_economica_peso` | float | |
| `red_ideologica_peso` | float | |
| `red_afectiva_peso` | float | |
| `red_ritual_peso` | float | |

---

### Métricas Derivadas para Análisis (no datasets, sino vistas/cálculos)

```python
METRICAS_INCONSCIENTE_COLECTIVO = {
    # Cohesión y fragmentación
    "polarization_index": "modularity(emotional_network)",
    "collective_synchrony": "std(mood_base) → inversión",
    "shadow_projection_rate": "hostile_interactions / total",
    
    # Individuación colectiva
    "mean_individuation": "agents.self / (agents.shadow + agents.persona)",
    "individuation_variance": "std de individuación — heterogeneidad",
    "shadow_integration_rate": "agentes con shadow < 0.4",
    
    # Economía y poder
    "gini_coefficient": "distribución de aurum",
    "economic_stress_index": "agentes_en_privacion / total",
    "power_concentration": "top10%_capital / total_capital",
    
    # Campo simbólico
    "mythogenesis_rate": "mitos_nuevos / semana_simulada",
    "dominant_archetype_stability": "ciclos_con_mismo_arquetipo_dominante",
    "liminality_frequency": "estados_liminales / mes_simulado",
    
    # Clima y adaptación
    "climate_resilience_index": "mood_drop / intensidad_evento_climático",
    "seasonal_behavior_variance": "diferencia_conducta_entre_estaciones",
    
    # Salud colectiva
    "mean_sleep_quality": "promedio calidad sueño",
    "dream_collective_resonance": "% sueños con símbolo compartido",
    "trauma_unprocessed_rate": "agentes_con_trauma_no_integrado / total",
    
    # Emergencia
    "scapegoat_rotation": "frecuencia de cambio de chivo expiatorio",
    "hero_emergence_threshold": "presión colectiva al surgir héroe",
    "taboo_formation_rate": "nuevos tabúes / mes_simulado",
}
```

---

## VI. IDEAS ADICIONALES QUE NO ENTRAN EN LAS CATEGORÍAS ANTERIORES

### Lenguaje y Comunicación
- 🟡 Los agentes tienen un **léxico simbólico** que evoluciona. Ciertas palabras/conceptos ganan carga emocional colectiva.
- 🔴 **Lenguaje memético:** Conceptos que se contagian. Una idea que surge en un agente puede propagarse y mutar.
- 🔴 **Rumores:** Información incorrecta que circula y altera la percepción de agentes que no vivieron el evento.

### Ritual y Religión
- 🟡 **Rituales colectivos:** Eventos que sincronizan el campo. Reducen ansiedad, refuerzan mitos.
- 🟡 **Tabúes emergentes:** Conductas que la colectividad comienza a rechazar sin que nadie lo declare.
- 🔴 **Religión emergente:** Si un mito de tipo "madre/sabio/renacimiento" supera cierto umbral + hay un agente que lo encarna, emerge una proto-religión con seguidores activos.

### Arte y Cultura
- 🟡 **Producción cultural:** Agentes con alto `apertura` + `exploración` generan "obras" que afectan el campo simbólico.
- 🔴 **Movimientos culturales:** Múltiples agentes produciendo en la misma dirección simbólica → estilo, movimiento, época.

### Conflicto y Violencia
- 🟡 **Conflictos interpersonales:** Escalada de interacciones negativas → ruptura de vínculo → enemistad.
- 🟡 **Violencia como colapso cuántico extremo:** No es el default — emerge cuando se supera un umbral de agresividad + provocación + presión del campo.
- 🔴 **Guerra civil o conflicto colectivo:** Si dos facciones ideológicas acumulan suficiente tensión y el campo tiene alta polarización.

### Salud y Enfermedad
- 🟡 **Enfermedades físicas:** Afectan energía, humor, productividad. Pueden ser contagiosas.
- 🟡 **Enfermedades psicológicas emergentes:** Un agente con suficiente acumulación de complejos no integrados puede desarrollar un estado clínico (depresión mayor, paranoia sostenida).
- 🔴 **Epidemia psíquica:** Si una enfermedad psicológica es "contagiosa" a través del campo (como la histeria colectiva), se propaga por la red afectiva.

---

*Documento vivo — actualizar con cada sprint de desarrollo.*
*Psyche Simulacra — Ideas v1.0*
