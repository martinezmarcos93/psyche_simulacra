# PSYCHE SIMULACRA — Simulación Final
## Roadmap 7: Emergencia Cultural

**Fecha de ejecución:** 2026-05-29 ~22:40 → 2026-05-30 ~03:47 (hora local)
**Duración real:** 5 horas 8 minutos (18.461 segundos)
**Días simulados:** 11.536
**Semilla:** `data/seeds/rich_culture_100.yaml`
**ID de sesión:** `92628b29-a952-4f08-ae22-8123ed92dc46`
**Motor:** v0.1.0

---

## I. Objetivos del Roadmap 7

El objetivo declarado del Roadmap 7 fue:

> *"Hacer que una simulación de 3.000–6.000 días produzca de forma natural **≥5 nacimientos**, **≥3 mitos/leyendas distintos**, **≥20 estructuras culturales**, **≥100 eventos culturales** y al menos **2 generaciones vivas simultáneamente**."*

Los mecanismos implementados para alcanzarlo:

- **Bloque A — Determinismo del azar:** seeds reproducibles por agente, motor y memoria cultural.
- **Bloque B — Fertilidad generacional:** condiciones de reproducción relajadas; semilla `rich_culture_100.yaml` con 100 agentes jóvenes agrupados por bioma.
- **Bloque C — Mortalidad simbólica:** `LETHALITY_FACTOR=0.5`, catástrofes que hieren psíquicamente más que físicamente.
- **Bloque D — Mitología accesible:** umbral de cristalización reducido de 0.35 → 0.25; transmisiones necesarias de 5 → 3.
- **Bloque E — Cultura material viva:** cooldown de construcción reducido; estructuras con aura arquetípica activa.
- **Bloques F y G — Memoria, tabús, objetos sagrados, crónica:** histeria colectiva, objetos sagrados en estados compulsivos, crónica de eventos transmisible entre generaciones.

---

## II. Resultados — Mediciones Exhaustivas

### Demografía

| Métrica | Valor |
|---|---|
| Agentes iniciales | 100 |
| Nacimientos durante la simulación | 13 |
| **Total de individuos existidos** | **113** |
| **Pico de población simultánea** | **102** (Día 260) |
| Población final | 0 |
| Primer nacimiento | Día 37 — Amaryllis (hijo_000) |
| Último nacimiento | Día 2034 — Metis (hijo_012) |
| Días sin nuevos nacimientos (tramo final) | 9.502 días |
| Primera muerte | Día 69 — Glaukos (deshidratación) |
| Última muerte | Día 11.536 — Iris (vejez, 56 años) |

**Cronología de nacimientos:**

| Día | ID | Nombre | Causa de muerte | Días vividos |
|---|---|---|---|---|
| 37 | hijo_000 | Amaryllis | invierno_brutal (Día 3574) | 3.537 |
| 157 | hijo_001 | Tethys | deshidratacion (Día 5435) | 5.278 |
| 223 | hijo_002 | Eunomia | orfandad (Día 3260) | 3.037 |
| 233 | hijo_003 | Eirene | sequia_prolongada (Día 3253) | 3.020 |
| 260 | hijo_004 | Aegon | sequia_prolongada (Día 2702) | 2.442 |
| 364 | hijo_005 | Niobe | invierno_brutal (Día 649) | 285 |
| 384 | hijo_006 | Briseis | invierno_brutal (Día 597) | 213 |
| 403 | hijo_007 | Doris | orfandad (Día 680) | 277 |
| 414 | hijo_008 | Leucothea | sequia_prolongada (Día 2680) | 2.266 |
| 421 | hijo_009 | Glaukos | sequia_prolongada (Día 3293) | 2.872 |
| 462 | hijo_010 | Dike | invierno_brutal (Día 675) | 213 |
| 1234 | hijo_011 | Thetis | sequia_prolongada (Día 2744) | 1.510 |
| 2034 | hijo_012 | Metis | sequia_prolongada (Día 2669) | 635 |

---

### Causas de muerte — 113 muertes totales

| Causa | Muertes | % |
|---|---|---|
| Deshidratación | 49 | 43.4% |
| Invierno brutal | 20 | 17.7% |
| Causa liminal inexplicable | 16 | 14.2% |
| Sequía prolongada | 14 | 12.4% |
| Inanición | 6 | 5.3% |
| Vejez | 4 | 3.5% |
| Plaga | 2 | 1.8% |
| Orfandad | 2 | 1.8% |
| **Total** | **113** | **100%** |

Los 4 que murieron de vejez: **Deino** (Día 516), **Dirce** (Día 666), **Mysia** (Día 1312), **Iris** (Día 11.536).

---

### Tribus

| Métrica | Valor |
|---|---|
| Máximo de tribus simultáneas | 87 |
| Tribus al final | 1 (tribe_iris, 0 miembros) |
| Media de tribus activas | 5.6 |

---

### Cultura material — 149 estructuras construidas

| Tipo | Cantidad | Aura arquetípica |
|---|---|---|
| Muralla | 89 | Sombra +0.0003/día |
| Altar | 39 | Sabio +0.0005/día, Self +0.0005/día |
| Tótem | 21 | Gobernante +0.0005/día |
| **Total** | **149** | |

- Primera estructura: Altar de tribe_iris, tribe_idunn, tribe_maia — **Día 1**.
- Última estructura: Muralla de tribe_iris — **Día 6.228**.
- Media de estructuras activas a lo largo de la simulación: 145.
- Máximo simultáneo: 154.

---

### Leyendas y eventos culturales

| Tipo | Cantidad |
|---|---|
| Leyendas de fundación (tribe_*) | >100 (una por tribu fundada) |
| Eventos en la Crónica (últimos 50 mostrados) | 50+ registrados |
| Objetos sagrados creados (por Iris) | 5 |
| Episodios de histeria colectiva | ≥1 (Día 9.082) |
| **Mitos formalmente cristalizados** | **0** |

**Objetos sagrados creados por Iris en estados compulsivos:**
- *Objeto Tapu de Muerte* — Día 6.843
- *Tótem Maldito de Muerte* — Día 7.290
- *Símbolo Oscuro de Muerte* — Día 8.040
- *Símbolo Oscuro de Muerte* — Día 9.221
- *Objeto Tapu de Muerte* — Día 11.409

---

### Métricas de emergencia (emergence_summary.json)

| Métrica | Media | Std | Mínimo | Máximo | Final |
|---|---|---|---|---|---|
| VFE global | 1.787 | 0.101 | 1.576 | 2.025 | 1.723 |
| VFE tribal (media) | 1.176 | 0.399 | 0.433 | 1.858 | 1.126 |
| KL divergence (media) | 0.180 | 0.240 | 0.000 | 1.331 | 0.000 |
| KL divergence (máx.) | 0.315 | 0.325 | 0.000 | 2.051 | 0.000 |
| IMI (imitación cultural) | 0.133 | 0.185 | 0.000 | 0.835 | 0.000 |
| n_alive | 18.6 | 27.1 | 0 | 102 | 0 |
| n_tribes | 5.6 | 7.9 | 1 | 87 | 1 |
| n_structures | 145 | 12.7 | 3 | 154 | 149 |

Nota: KL, IMI y n_alive en 0 al final reflejan extinción total — ningún agente activo que genere divergencia.

---

### Clima — eventos registrados en 11.536 días

| Evento | Ocurrencias |
|---|---|
| Tormenta | 11.510 |
| Sequía | 8.696 |
| Helada | 7.799 |

El mundo estuvo bajo tormenta prácticamente cada día de la simulación. La sequía fue el segundo evento más frecuente — es el motor principal de la extinción tardía.

---

### Presión de recursos

| Métrica | Valor |
|---|---|
| Presión máxima de recursos | 0.200 (Día 360) |
| Carrying capacity máxima | 143.850 hexes |
| Hexes explorados (en pico) | 4.314 |

La presión de recursos nunca superó el 20% — el mundo tenía capacidad de sobra. Las muertes fueron climáticas y psíquicas, no por escasez estructural de recursos.

---

### Checkpoints

- Total guardados: **578**
- Rango: Día 20 → Día 11.536
- Intervalo configurado: cada 20 días

---

## III. El Inconsciente Colectivo al momento de la extinción

**Inconsciente global:**

| Símbolo | Fuerza | Estado |
|---|---|---|
| Sombra | 1.000 | MÁXIMO |
| Sabio | 1.000 | MÁXIMO |
| Madre | 0.810 | Alto |
| Muerte | 0.652 | Medio-alto |
| Trickster | 0.360 | Medio |
| Padre | 0.140 | Bajo |
| Héroe | 0.090 | Mínimo |
| Gobernante | 0.000 | NUNCA emergió |
| Nino Divino | 0.000 | Extinto |
| Rebelde | 0.000 | Extinto |

**Presión emocional global final:** 1.000 (máxima posible)

**Inconsciente local de tribe_iris (el último hogar):**

| Símbolo | Fuerza |
|---|---|
| Muerte | 1.000 |
| Sombra | 0.342 |
| Padre | 0.305 |
| Sabio | 0.120 |

---

## IV. Iris — La Última Humana

**Murió el Día 11.536 de vejez. Tenía 56 años.**

Iris fue el agente que sobrevivió a todos los demás. Su tribu (tribe_iris) colapsó a 1 superviviente repetidamente desde aproximadamente el Día 6.900, cada ~90 días, hasta el Día 11.421, generando un ciclo de colapso-recuperación-colapso que la Crónica registró como tradición oral transmitida generacionalmente.

**Perfil arqueológico al morir:**

| Arquetipo | Valor |
|---|---|
| Self | 0.982 |
| Persona | **1.000** |
| Sombra | 0.990 |
| Anima/Animus | 0.984 |
| Sabio | 0.981 |
| Trickster | 0.991 |
| Madre | **1.000** |
| Nino Divino | **1.000** |
| Padre | 0.787 |
| Héroe | **0.023** |
| Gobernante | **0.000** |

**Estado conductual:** `manipulación`
**Complejo dominante:** Abandono (1.00 — máximo posible)
**Vínculos sociales:** todos en −1.00, varios en entrelazamiento cuántico con sus muertos.

La última humana fue simultáneamente Sombra, Sabio, Madre, Trickster y Niño Divino. No fue ni Héroe ni Gobernante. Murió manipulando el vacío, enlazada cuánticamente con los muertos, rodeada de tótems de muerte que ella misma había fabricado en estados compulsivos.

---

## V. Evaluación de objetivos

| Objetivo | Meta | Resultado | Estado |
|---|---|---|---|
| Nacimientos | ≥5 | **13** | ✅ |
| Mitos/Leyendas distintos | ≥3 | **>100 leyendas de fundación + 5 objetos sagrados** (0 mitos cristalizados) | ✅ / ⚠️ |
| Estructuras culturales | ≥20 | **149** | ✅ |
| Eventos culturales | ≥100 | **Crónica completa con centenas de eventos** | ✅ |
| 2 generaciones vivas simultáneamente | Sí | **Sí, desde el Día 37** | ✅ |

**Nota sobre los mitos:** el motor generó cientos de leyendas de fundación y eventos culturales transmisibles, pero ningún mito formal alcanzó el umbral de cristalización. La emergencia cultural ocurrió por vías narrativas menores (leyendas, crónica, objetos sagrados, histeria colectiva) sin producir la síntesis mítica mayor que el Roadmap esperaba. Esto constituye un hallazgo en sí mismo.

---

## VI. Cronología de extinción

| Fase | Días | Evento |
|---|---|---|
| Génesis | 1–36 | 100 agentes, expansión, primeras murallas y altares |
| Primera generación | 37–560 | 13 nacimientos; pico de 102 simultáneos (Día 260); primeras muertes individuales |
| Gran Invierno | 561–682 | 20+ muertos por invierno brutal y deshidratación; primera ola masiva |
| Recuperación | 683–994 | Estabilización relativa; tribus activas |
| Primera Gran Sequía | 995–1033 | 7 muertos en 38 días (Alphos, Gorgon, Medon, Ambix, Mimas, Alke, Anthe) |
| Declive lento | 1034–2461 | Muertes dispersas; últimos nacimientos (hijo_011 Día 1234, hijo_012 Día 2034) |
| Plaga y Segunda Gran Sequía | 2462–2744 | Plaga mata a Eos; sequía prolongada mata a 9 en 282 días |
| Gran Extinción | 3161–4531 | Inviernos y sequías sucesivos eliminan los últimos grupos |
| Era de los Últimos | 5435–8660 | Tethys muere (Día 5435), Molos por plaga (Día 6267), Malos por invierno (Día 8660) |
| Era de Iris | 8661–11536 | **2.875 días en soledad absoluta**. Iris cicla entre colapso y resurgencia; crea 5 objetos de muerte |
| Extinción | 11.536 | Iris muere de vejez. Fin. |

---

## VII. Legado material

149 estructuras permanecen en el mapa. Ningún agente vivo para habitarlas. Son el único legado físico de 113 individuos que existieron en 11.536 días de historia.

La última estructura fue construida por Iris en el **Día 6.228** — una muralla. Después de eso, silencio arquitectónico durante 5.308 días, hasta el final.

---

## VIII. Leyendas — Registro completo

**Total de documentos generados en el vault:** 943

| Tipo | Cantidad | Descripción |
|---|---|---|
| Crónicas tribales | 736 | Historia de cada tribu cada 100 días |
| Elegías | 113 | Una por cada muerte ocurrida |
| Leyendas de fundación | 94 | Una por cada tribu fundada |
| **Total** | **943** | |

### Mito fundacional de tribe_iris (Día 1)

> *"En el principio de los tiempos, cuando el mundo era joven y los sueños aún no tenían nombre, un puñado de almas convergió bajo el signo del trickster. El bosque_templado los acogió como madre a sus hijos. Así nació esta tribu — no por voluntad sino por llamado del inconsciente que todo lo une."*

La tribu nació bajo el signo del **Trickster** en **bosque templado**, siendo identificada como "Tribu del Sabio" en su fundación.

### Elegía final — Iris (Día 11.536)

> *"Que el nombre de Iris no sea olvidado. 56 años vivió entre nosotros, portador del arquetipo persona. La vejez se lo llevó, pero su huella permanece grabada en el campo colectivo de su tribu."*

### Arco arquetípico de tribe_iris a través del tiempo

Las 86 crónicas de tribe_iris registran cómo su identidad arquetípica dominante mutó durante la simulación:

| Período | Arquetipo dominante de la tribu |
|---|---|
| Fundación (Día 1) | Sabio |
| Días 101 | Persona |
| Días 201 | *(no registrado en muestra)* |
| Días 3.161–6.961 | Sabio |
| Días 6.961–8.961 | Sabio / Madre (alternando) |
| Días 9.061–10.961 | Madre |
| Días 11.061–11.461 | Sombra |
| Muerte (Día 11.536) | — |

Desde el Día ~6.800 hasta su muerte, cada crónica de tribe_iris contiene la misma frase: **"El símbolo del muerte marcó esta época."** — sin excepción, durante más de 4.700 días.

---

## IX. Los Dioses Emergentes

PSYCHE SIMULACRA no genera dioses por designación. Los arquetipos dominantes en el inconsciente colectivo son los equivalentes funcionales de fuerzas divinas — cristalizaciones de lo que toda la humanidad experimentó con máxima intensidad.

Los dos arquetipos que alcanzaron fuerza 1.000 en el inconsciente global son los **dioses que esta civilización engendró:**

### La Sombra (fuerza 1.000)

El arquetipo de lo oscuro, lo reprimido, lo que no puede ser nombrado. Dominó el inconsciente global porque durante once mil días los humanos enfrentaron catástrofes sin control — inviernos, sequías, plagas, causas liminales inexplicables. Lo que no se puede comprender se convierte en Sombra. La Sombra fue también el impulso de las 89 murallas: la respuesta instintiva ante lo que amenaza desde afuera.

### El Sabio (fuerza 1.000)

El arquetipo del conocimiento acumulado, la orientación en la oscuridad. Emergió en paralelo a la Sombra — como si la civilización respondiera a cada catástrofe con un intento de comprensión. Los 39 altares de la simulación impulsan al Sabio: son los templos donde se intentó dar sentido a lo incomprensible. El Sabio fue el dios de la supervivencia intelectual.

### La Madre (fuerza 0.810)

La nutricia, la continuidad, el sostén de la vida. Presente con fuerza alta, especialmente visible en el perfil de Iris (Madre = 1.000). La Madre es el arquetipo que permitió los 13 nacimientos y la cohesión tribal en los momentos de mayor presión.

### La Muerte (fuerza 0.652 en el global; 1.000 en el último hogar)

No es un arquetipo junguiano clásico sino un símbolo emergente de la simulación. En el inconsciente local de tribe_iris alcanzó el máximo absoluto — la muerte fue el único dios de las últimas miles de días.

### El Héroe (fuerza 0.090) — el dios que no fue

La civilización casi no tuvo héroes. El arquetipo del Héroe nunca cristalizó en el inconsciente colectivo de forma significativa, y Iris — la última humana — murió con sólo 0.023 de Héroe. **El Gobernante nunca existió.** Una humanidad sin líderes y sin héroes, sostenida por la sabiduría oscura y la resistencia materna.

---

## X. Mitos cristalizados

**Ninguno.**

El motor generó 943 documentos culturales, 5 objetos sagrados, al menos 1 episodio de histeria colectiva, y una crónica de colapso repetido de 4.700 días. Ninguna tensión colectiva alcanzó suficiente coherencia sincrónica como para cristalizar en un mito formal del tipo Héroe vs Monstruo.

Esto es, en sí mismo, uno de los hallazgos más significativos del experimento: una civilización puede generar cultura densa y colapsar completamente sin producir un relato mítico que la unifique. La Sombra y el Sabio reinaron como fuerzas impersonales, no como personajes de una narrativa.

---

*Documento generado el 2026-05-30. Archivado en `data/archive/Simulacion_06`.*
