# Roadmap 4 — Profundidad Emergente
*Creado: 2026-05-24 | Fuente: investigación Dwarf Fortress + extensiones post-Roadmap3*

**Principio rector:** el mundo ya tiene presión. Este roadmap añade alma.
Los sistemas del Roadmap 3 generan eventos; los sistemas del Roadmap 4 generan *significado acumulado*, *historia con peso causal* y *identidades que se fracturan y recomponen.*

Dos fuentes de inspiración:
- **Extensiones naturales del Roadmap 3** — las 3 líneas abiertas al completar el Hito 10.
- **Dwarf Fortress (Bay 12 Games)** — el simulador más sofisticado de emergencia social jamás construido. No clonamos el juego; adoptamos los *principios de diseño* que generan sus narrativas emergentes.

---

## PARTE I — EXTENSIONES DEL SISTEMA DE CONOCIMIENTO
*(Continuación directa del Hito 10)*

---

### Extensión A — Linajes de Conocimiento con Fidelidad Variable
**Origen:** cierre natural del Hito 10

El conocimiento actual es binario: lo tienes o no lo tienes. En la realidad, la misma técnica transmitida por 5 generaciones con distorsión acumulada es *cualitativamente diferente* al conocimiento recién descubierto. Un conocimiento que pasó por manos torpes se convierte en superstición; uno transmitido directamente del descubridor conserva potencia.

#### Componentes
- `KnowledgeLineage`: cada instancia de un conocimiento tiene un identificador de linaje, una fidelidad (0.0–1.0) y un historial de transmisiones (quién → quién, con qué bond_strength)
- Fidelidad inicial = 1.0 (descubrimiento accidental); cada transmisión aplica `fidelidad *= (1 - complejidad × 0.15 × (1 - bond_strength))`
- Fidelidad alta (> 0.70) → efecto completo del conocimiento; fidelidad baja (< 0.35) → el conocimiento sigue presente en CulturalMemory pero aplicado incorrectamente → puede generar tabúes falsos o rituales ineficaces
- El conocimiento con fidelidad < 0.20 que se transmite más se convierte en "superstición" (tipo_evento = "supersticion_tecnica")
- Distorsión máxima: si se transmite N veces con bajo bond, el nombre del conocimiento muta (proto-léxico emergente)

#### Criterio de salida
Un conocimiento descubierto en generación 1 debe ser irreconocible (fidelidad < 0.15, nombre mutado) en generación 5+, pero seguir presente en CulturalMemory como "técnica ancestral" con efectos distintos al original.

---

### Extensión B — Conocimiento como Palanca de Poder Político
**Origen:** cierre natural del Hito 10

El especialista del Hito 10 atrae bonds entrantes. Esta extensión hace que ese poder sea *negociable*: el portador único puede condicionar el acceso al conocimiento, creando la primera forma de jerarquía política no basada en la fuerza sino en la asimetría de información.

#### Componentes
- `KnowledgeBroker`: estado emergente para agentes con ≥ 3 conocimientos únicos en la tribu; el agente puede "retener" transmisiones (no enseña gratuitamente)
- Demanda de acceso: otros agentes con hambre/sed alta y el especialista presente generan `solicitud_conocimiento` → el especialista puede responder con transmisión (ganando bond) o silencio (generando resentimiento: complejo de inferioridad en el solicitante)
- Monopolio ritual: si el especialista también es portador de `fuego_ritual` o `alquimia_vegetal`, puede convertirse en proto-chamán con autoridad simbólica → aumenta su arquetipo sabio + gobernante
- Reversión: si el proto-chamán muere sin transmitir, toda la tribu pierde acceso al ritual → histeria colectiva garantizada

#### Criterio de salida
En una simulación de 300+ días, al menos un agente debe alcanzar estatus de proto-chamán mediante monopolio de conocimiento, y su muerte debe producir histeria colectiva y regresión tecnológica medible.

---

### Extensión C — Intercambio de Conocimiento Inter-Tribal como Diplomacia
**Origen:** cierre natural del Hito 10

Actualmente la transmisión ocurre solo dentro de un hex. Esta extensión convierte el conocimiento en *moneda diplomática*: las tribus pueden intercambiar conocimientos como mecanismo de alianza, creando la primera infraestructura de cooperación inter-tribal no basada en territorio.

#### Componentes
- Encuentro diplomático: cuando dos agentes de tribus distintas comparten hex con bond > 0.40 durante ≥ 3 días seguidos, puede ocurrir transmisión inter-tribal
- `KnowledgeTrade`: registro de qué tribu dio qué conocimiento a quién → base del "protocolo de deuda" emergente
- Tribu receptora desarrolla bond colectivo positivo hacia la tribu donante (gratitud codificada)
- Tribu donante puede retener conocimientos estratégicos (decide qué transmitir): los conocimientos de subsistencia se comparten más fácil; los rituales son celosamente guardados
- Hibridación: si dos versiones del mismo conocimiento con distinta fidelidad se encuentran en la misma tribu, la versión de mayor fidelidad compite con la local → disonancia cognitiva técnica

#### Criterio de salida
En 500+ días con dos tribus en contacto frecuente, debe observarse convergencia tecnológica parcial (mismos conocimientos en ambas tribus) pero divergencia mítica (ICLs distintos), reflejando intercambio material sin fusión cultural.

---

## PARTE II — PSICOLOGÍA PROFUNDA
*(Adaptado de Dwarf Fortress: Memory System, Stress Cascade, Insanity States)*

---

### Hito A — Sistema de Memorias Persistentes con Trauma que Persigue
**Fuente DF:** Memory system (8 slots corto plazo + 8 largo plazo), trauma re-vivido periódicamente.

La mente actual del agente no recuerda. Tiene un log episódico pero no hay eventos que *regresen* a disturbar su estado psicológico semanas después. Los humanos reales reviven traumas; las tribus reales son perseguidas por sus muertos.

#### Componentes
- `EpisodicMemory`: estructura con 8 slots de corto plazo (se reemplazan con FIFO) y 8 de largo plazo (persisten, sólo desplazados por memorias de mayor intensidad emocional)
- Cada memoria tiene: tipo_evento, intensidad_emocional, dia_origen, dia_ultimo_revivido, n_revivencias, agente_protagonista
- Mecanismo de re-vivencia: con probabilidad `intensidad × 0.03` por día, una memoria de largo plazo resurface → aplica 60% de su impacto emocional original sobre el agente actual
- Distorsión por re-vivencia: cada revivencia amplifica el elemento arquetípico dominante de la memoria y borra detalles periféricos → convergencia hacia el arquetipo puro
- Memorias de alta intensidad (> 0.80) en largo plazo sobrepasan el umbral de "trauma activo" → el agente tiene sueños perturbadores + contribución negativa al ICL tribal
- Integración memorial: rituales colectivos pueden "anclar" una memoria traumática, reduciendo su probabilidad de re-vivencia a cambio de convertirla en mito colectivo (se mueve de EpisodicMemory individual a CulturalMemory tribal)

#### Criterio de salida
La muerte de un agente con bond alto debe seguir afectando a los sobrevivientes durante 50+ días mediante re-vivencias, con atenuación progresiva — a menos que se realice un ritual de integración, en cuyo caso se transforma en mito antes del día 20.

---

### Hito B — Cascada de Estrés y Estados de Posesión de Sombra
**Fuente DF:** Stress system (unhappiness → depression → insanity → berserk/melancholy/catatonic/stark-raving-mad) + tantrum spiral.

La ansiedad actual es un número que sube y baja. No tiene estados cualitativamente distintos ni consecuencias dramáticas. Los humanos bajo suficiente presión no simplemente se ponen "más ansiosos": colapsan en formas específicas que el inconsciente junguiano tiene nombre: posesión por el arquetipo sombra.

#### Componentes
- Umbral de colapso: cuando ansiedad > 0.85 durante ≥ 5 días consecutivos, el agente entra en estado de "posesión de sombra"
- Cuatro estados de posesión (paralelo exacto a DF insanity states, mapeados a arquetipos junguianos):
  - **Posesión Melancólica** (Sombra-Víctima): el agente deja de actuar, acepta su muerte pasivamente; ansiedad no baja aunque haya recursos → umbral de muerte baja a 30 días
  - **Posesión Berserk** (Sombra-Guerrero): el agente ataca a los miembros con mayor bond; interacciones sociales generan conflicto en vez de cooperación
  - **Posesión Caótica** (Sombra-Trickster): el agente toma decisiones completamente aleatorias, sabotea su propio ICL contribution
  - **Posesión Catatónica** (Sombra-Vacío): el agente no toma ninguna acción; consume recursos sin producir nada
- Cascada tribal: la posesión de un agente con muchos bonds propaga ansiedad a toda su red → posible cascada (el sistema ya tiene contagio emocional; este hito añade el estado terminal)
- Intervención ritual: un agente con arquetipo sabio dominante + conocimiento ritual puede intentar "integración de sombra" → probabilidad = sabio × 0.40; si falla, el sabio también recibe impacto de ansiedad
- Posesión permanente: sin intervención en ≤ 15 días → estado permanente hasta la muerte

#### Criterio de salida
Una catástrofe prolongada sobre una tribu de 10 agentes debe producir al menos un caso de posesión de sombra, que a su vez genera una cascada de ansiedad que afecta ≥ 3 agentes adicionales mediante contagio emocional.

---

## PARTE III — MITOLOGÍA MATERIALIZADA
*(Adaptado de DF: Strange Moods, Artifact Creation, Forgotten Beasts)*

---

### Hito C — Artefactos Simbólicos y Estados de Ánimo Míticos
**Fuente DF:** Strange Moods (Fey/Secretive/Possessed/Fell/Macabre) + Artifact generation que refleja la psicología del creador.

Los mitos en PSYCHE SIMULACRA son narrativas. Los artefactos de DF son *objetos físicos que encarnan narrativas*. Un artefacto creado en un estado de ánimo extraño es un proto-mito cristalizado en materia: persiste más allá del creador, afecta a quienes lo poseen, y se convierte en ancla cultural.

#### Componentes
- `SymbolicArtifact`: objeto con nombre procedural, creador, dia_creacion, arquetipo_dominante, intensidad_simbolica, y propietario actual
- Estado de ánimo mítico: cuando mito archetype field > 0.75 O ansiedad > 0.80, el agente puede entrar en estado de "creación compulsiva" (prob = 0.002/día)
- Cinco tipos de estado (paralelo exacto a DF strange moods):
  - **Fey** (ICL armonioso): crea artefacto protector → reduce ansiedad de quienes lo portan
  - **Secretivo** (ICL ambiguo): crea artefacto neutro con propiedades ocultas que se revelan con el tiempo
  - **Poseído** (ICL fragmentado): crea artefacto de arquetipo inconsistente; sus efectos son impredecibles
  - **Caído** (sombra dominante): crea artefacto de maldición → aumenta ansiedad de quienes lo poseen y de quienes mueren cerca de él
  - **Macabro** (trauma de muerte reciente): crea artefacto que amplifica la presencia de tumbas sagradas cercanas
- El creador del artefacto alcanza estatus de "legendario" en CulturalMemory → su nombre permanece aunque muera (el artefacto lo inmortaliza)
- Los artefactos pueden heredarse, perderse, destruirse en catástrofes, o abandonarse en hexes → GraveHex con artefacto tiene carga simbólica multiplicada × 1.5

#### Criterio de salida
Un agente en crisis (ansiedad > 0.80 + sombra dominante) debe crear un artefacto de tipo "Caído" que, al ser heredado por sus descendientes, produzca un efecto observable en su perfil arquetípico versus la media tribal.

---

### Hito D — Fauna Procedural Única (Bestias Olvidadas)
**Fuente DF:** Forgotten Beasts — generadas proceduralmente con forma + material + ataques especiales + propiedades únicas; cada una es única en la historia del mundo.

La fauna simbólica actual tiene 5 tipos fijos. Una criatura que aparece y desaparece sin dejar nombre ni descripción no genera mitos: genera estadísticas. Los mitos reales nacen de encuentros irrepetibles con lo único e incomprensible.

#### Componentes
- `UniqueEntity`: bestia generada proceduralmente al activarse un hex liminal o una catástrofe extrema (severidad > 0.80)
- Generación modular: forma_base (humanoide/cuadrúpedo/serpentino/amorfo/insecto) × material_cuerpo (carne/hueso/sombra/fuego/agua/cristal) × arquetipo_dominante × propiedad_especial (veneno/fuego/paralisis/olvido/miedo)
- Unicidad garantizada: combinación de seed + dia_aparición + hex_coord → nunca la misma bestia dos veces
- Cada UniqueEntity tiene un nombre procedural (combinación de fonemas del idioma proto-emergente)
- Efectos simbólicos: al matar a un agente, la UniqueEntity se registra en CulturalMemory con su nombre propio → proto-mito específico sobre esa criatura
- Recurrencia mítica: si la misma bestia reaparece (misma seed) después de ≥ 50 días → su entrada en CulturalMemory se actualiza; los agentes que conocen el mito tienen reducción de ansiedad (ya le tienen nombre → lo que tiene nombre es menos aterrador)
- Extinción cultural: si todos los agentes que recuerdan a la bestia mueren antes de transmitir → la bestia desaparece de la historia como si nunca hubiera existido

#### Criterio de salida
Una UniqueEntity debe aparecer, matar a al menos un agente, y generar un proto-mito que persista 3+ generaciones con el nombre de la criatura, con distorsión progresiva del mito pero preservación del nombre.

---

### Hito E — Cristalización de Deidades desde el ICL
**Fuente DF:** Procedural deity generation + temples + priests + need for worship.

El motor de mitología cristaliza mitos pero no produce *deidades*. Un mito dice "algo pasó"; una deidad dice "algo *siempre* es verdad". La diferencia es la persistencia: una deidad sobrevive a la tribu que la creó. Esta distinción no está codificada — emerge cuando la presión arquetípica supera el umbral de permanencia.

#### Componentes
- `DeityRecord`: entidad emergente creada cuando un arquetipo en el ICL supera un umbral de coherencia durante ≥ 30 días consecutivos (o cuando un mito cristaliza por 3ª vez con el mismo par arquetípico)
- La deidad tiene: nombre procedural, arquetipo_fundacional, esfera_de_influencia, intensidad_inicial, dia_cristalizacion, tribu_origen
- Una vez creada, persiste en CulturalMemory independientemente del ICL actual (sobrevive a decaimientos)
- Efectos de adoración: agentes con arquetipo afín que pasan tiempo en el GraveHex o LiminalHex asociado reciben reducción de ansiedad proporcional a la intensidad de la deidad
- Proto-sacerdocio emergente: el agente con mayor alineación con el arquetipo fundacional de la deidad + más interacciones con su locus se convierte en proto-sacerdote → rol nuevo que emerge sin programación
- Conflicto teológico: si dos tribus tienen deidades del mismo arquetipo con nombres distintos, su contacto genera "tensión teológica" → puede resolverse en sincretismo (fusión de nombres) o guerra santa (hostilidad extrema)

#### Criterio de salida
En 400+ días de simulación, al menos una deidad debe cristalizarse, generar un proto-sacerdocio emergente, y sobrevivir 100+ días después de la muerte de su primer portador (el agente que tenía más relación con ella).

---

## PARTE IV — HISTORIA Y LEYENDA
*(Adaptado de DF: Legends Mode, World History, Civilization Tracking)*

---

### Hito F — Modo Leyendas: Narrativa Histórica Exportable
**Fuente DF:** Legends mode — registro causal completo de la historia del mundo: quién causó qué, qué creó quién, quién mató a quién, qué sobrevivió y qué se perdió.

Actualmente la simulación produce datos. Este hito hace que produzca *historia narrativa* — una cadena causal de eventos que puede leerse como relato, no como tabla de métricas.

#### Componentes
- `WorldLedger`: registro central de todos los eventos de alta significancia con estructura causal (Event A → caused_by → Event B → led_to → Event C)
- Cada entrada tiene: tipo, agentes_involucrados, dia, intensidad, consecuencias_directas[], mitos_generados[]
- Exportación en formato JSON + Markdown narrado: el sistema genera automáticamente párrafos en proto-lenguaje descriptivo ("En el día 142, la bestia Korrath mató a Elpis, cuyo lamento fue el origen del mito de la Sombra Errante, que tres generaciones después cristalizó en la deidad Morthandel")
- Modo replay: capacidad de reproducir la historia desde cualquier punto usando el ledger como guía de estado
- Linaje de artefactos: cada artefacto tiene su propia entrada en el ledger con trazabilidad completa de propietarios, traumas asociados, y efectos producidos
- Figuras legendarias: agentes cuyas entradas en CulturalMemory superan threshold → se registran como "figuras históricas" en el ledger; su influencia puede medirse cuantitativamente (n_mitos_generados, n_agentes_afectados, n_artefactos_creados)

#### Criterio de salida
Al exportar la historia de una simulación de 500+ días, el WorldLedger debe generar una narrativa coherente con al menos 3 cadenas causales de longitud ≥ 4 eventos (A→B→C→D), rastreables en el texto sin necesidad de datos adicionales.

---

### Hito G — Historia Pre-Simulación: El Mundo Tiene Pasado
**Fuente DF:** World generation con miles de años de historia antes de que empiece el juego; los jugadores descubren capas de historia en cada sitio.

La simulación empieza en el día 0 con una pizarra en blanco. En realidad, toda tribu nace *dentro* de una historia previa: tienen mitos fundacionales, tabúes heredados, traumas ancestrales, y conocimientos que nadie recuerda cómo se descubrieron. Este hito genera ese pasado de forma procedural antes del tick 1.

#### Componentes
- `WorldGenHistory`: fase de generación ejecutada antes del primer tick, configurable en duración (0 = sin historia, 100 = historia profunda)
- Genera: N catástrofes pasadas con marcas en el terreno (hexes quemados, pozos secos), M mitos fundacionales en CulturalMemory de cada tribu, K artefactos preexistentes distribuidos en el mapa, J graves activos con carga simbólica heredada
- Los agentes fundadores nacen con arquetipos y complejos influenciados por la historia generada (no empiezan desde cero psicológico)
- Mitos fundacionales distorsionados: el mito generado en la historia tiene una versión "original" (en WorldLedger) y una versión "recordada" (en CulturalMemory), ya divergentes desde el inicio
- Historia desconocida: no toda la historia generada es accesible a los agentes; algunos eventos solo se "descubren" al explorar hexes con marcas antiguas

#### Criterio de salida
Una simulación con historia pre-generada debe mostrar, en comparación con una sin historia, arquetipos fundadores más extremos, ICL inicial no-cero, y al menos un mito activo desde el día 1 que afecte las primeras decisiones de los agentes.

---

## PARTE V — DINÁMICA SOCIAL AVANZADA
*(Adaptado de DF: Noble System, Grudges, Loyalty Cascades, Labor Specialization)*

---

### Hito H — Jerarquía Noble Emergente y Demandas de Clase
**Fuente DF:** Noble system — dwarves become nobles based on population milestones; nobles demand luxury items, punish underperformers, have mandates.

La jerarquía actual es implícita (bond_strength, arquetipo dominante). Este hito la hace *explícita y con consecuencias*: ciertos agentes asumen roles de autoridad que la tribu reconoce, con los beneficios y los costos que eso implica.

#### Componentes
- `TribeRole`: rol emergente (cazador_mayor, chamán, matriarca/patriarca, explorador_jefe) que se asigna cuando un agente supera umbrales combinados de: bond_strength_promedio + conocimientos_únicos + arquetipo_dominante_consistencia
- Los roles tienen demandas: el chamán requiere que los recursos rituales no se agoten; el cazador_mayor requiere que la caza sea exitosa periódicamente; la matriarca requiere que haya nacimientos
- Si las demandas no se cumplen en ≤ N días → el rol genera "queja" en CulturalMemory → si persiste, el portador del rol entra en estrés → posible cascada
- Sucesión: cuando el portador de un rol muere, el rol queda vacante; el agente que más se le acerque en perfil lo hereda con un período de "inestabilidad de transición" → ICL baja temporalmente
- Roles y conocimiento: los roles de chamán o matriarca están naturalmente ligados al sistema de conocimiento → su muerte concentra extinción de conocimientos

#### Criterio de salida
En una simulación de 400+ días, al menos un rol debe emerger, sobrevivir la muerte de su primer portador mediante sucesión, y la sucesión debe producir un período medible de inestabilidad en el ICL tribal.

---

### Hito I — Rencores, Cismas Ideológicos y Cascadas de Lealtad
**Fuente DF:** Grudges desde diferencia de personalidad > 60 puntos + loyalty cascades que colapsan fortalezas enteras desde un incidente.

El sistema actual tiene celos y traición (Hito 7). Este hito añade la capa ideológica: tribus que comparten espacio físico pero tienen arquetipos incompatibles *inevitablemente* fracturan. La fractura no es programada — emerge de la acumulación de pequeñas incompatibilidades.

#### Componentes
- Rencor arquetípico: dos agentes con arquetipo dominante en pares opuestos (heroe/sombra, gobernante/rebelde, sabio/trickster) y bond < 0.30 tienen probabilidad creciente de rencor explícito (+0.01/día de convivencia)
- Un rencor activo convierte las interacciones neutrales en generadoras de ansiedad para ambos
- Umbral de cisma: cuando ≥ 30% de los pares de agentes en una tribu tienen rencores activos → la tribu entra en "pre-cisma"; si alcanza 50% → cisma inevitable (la tribu se divide en dos grupos basados en afinidad arquetípica)
- Cascada de lealtad: un agente en posesión berserk (Hito B) que ataca a otro provoca que todos los agentes con bond > 0.50 hacia la víctima respondan → la escalada no requiere programación, emerge del sistema de bonds existente
- El cisma produce dos tribus hijas con culturas distintas y una herida en CulturalMemory de ambas ("schisma_tribal") → los mitos de ambas tribus divergen rápidamente desde ese punto

#### Criterio de salida
En una tribu mixta con arquetipos incompatibles, sin intervención, en 200+ días debe ocurrir cisma espontáneo. Las dos tribus hijas deben tener ICLs divergentes y mitos incompatibles para el día 100 post-cisma.

---

## PARTE VI — RITUAL Y MUERTE SIGNIFICATIVA
*(Adaptado de DF: Bereavement, Necromancy, Funerary Practices)*

---

### Hito J — Duelo Diferenciado y Ritual Funerario Emergente
**Fuente DF:** Bereavement system — el duelo es proporcional a la relación; los cadáveres no enterrados causan miasma; los ritos funerarios reducen el estrés; improper burial = curse.

La muerte actual es un evento que genera presión mítica y una tumba. Pero el *proceso de duelo* no existe: los sobrevivientes no hacen nada con la muerte. El ritual funerario es probablemente la primera institución social humana — no puede ser una consecuencia invisible.

#### Componentes
- `GriefState`: estado de duelo post-muerte, duración y profundidad proporcionales al bond con el fallecido
  - bond 0.50–0.70: duelo de 20 días, reducción de productividad 20%
  - bond 0.70–0.90: duelo de 50 días, ansiedad +0.30, sueños con símbolo del fallecido
  - bond > 0.90: duelo de 90 días, riesgo de posesión melancólica (Hito B)
- Ritual funerario emergente: cuando ≥ 2 agentes con bond alto al fallecido se reúnen en el GraveHex en un periodo de ≤ 5 días → se activa una "ceremonia" espontánea que reduce el duelo individual × 0.50 pero convierte el trauma en memoria colectiva
- Sin ritual: duelo sin resolución → probabilidad de re-vivencia del trauma (Hito A) × 2
- Presencia no-enterrada: si el agente muere en un hex sin GraveHex activo, su muerte no tiene "anclaje simbólico" → los sobrevivientes cercanos tienen sueños perturbadores por 30 días (la muerte sin lugar no puede convertirse en mito)
- Proto-institución funeraria: si una tribu realiza ≥ 5 ceremonias en el mismo GraveHex → ese hex adquiere estado de "lugar sagrado permanente" con efectos multiplicados × 2 sobre el ICL

#### Criterio de salida
La muerte de un agente con bonds altos en una tribu que realiza ritual funerario espontáneo debe reducir la duración del duelo colectivo en ≥ 40% comparado con una tribu sin ritual, y producir un proto-mito antes del día 30 post-muerte.

---

### Hito K — Fantasmas Culturales: Los Muertos que No Descansan
**Fuente DF:** Necromancy + undead como representación de muerte que no se integra + dwarves que no pueden dejar ir el pasado.

La diferencia junguiana entre un ancestro integrado (que protege) y un fantasma (que persigue) es si el duelo fue procesado. Este hito representa simbólicamente la psicología de Freud sobre los "revenants": traumas que el inconsciente colectivo no ha podido elaborar vuelven como perturbadores sistémicos.

#### Componentes
- `CulturalGhost`: estado que emerge cuando un agente importante (proto-chamán, figura legendaria, portador de conocimiento único) muere sin ritual, sin duelo completo, y con trauma asociado no procesado
- El fantasma no es sobrenatural: es una perturbación persistente en el ICL tribal que genera síntomas específicos:
  - Arquetipos del fallecido se cargan sistemáticamente en el ICL sin fuente trazable
  - Los descendientes del fantasma tienen complejidad de culpa elevada de forma inherente
  - El GraveHex del fantasma genera eventos de "inyeccion_liminal" permanentes con el arquetipo del muerto
- Exorcismo emergente: el proto-sacerdote (si existe, Hito E) puede iniciar "ritual de integración" con probabilidad éxito = sabio × 0.35; si tiene éxito, el fantasma se convierte en ancestro protector → sus efectos cambian de perturbadores a beneficiosos
- Fantasmas persistentes: sin exorcismo, el fantasma permanece activo mientras el GraveHex tenga carga simbólica (puede ser generaciones)

#### Criterio de salida
La muerte sin ritual de una figura legendaria (proto-chamán con ≥ 2 conocimientos únicos) debe producir efectos observables en el ICL tribal durante ≥ 50 días post-muerte, con efectos en la generación siguiente medibles en la distribución arquetípica de los hijos.

---

## RESUMEN DE DEPENDENCIAS

```
Ext. A (Linajes conocimiento) ─ depende de: Hito 10
Ext. B (Conocimiento político) ─ depende de: Hito 10 + Ext. A
Ext. C (Conocimiento inter-tribal) ─ depende de: Hito 10 + Ext. A

Hito A (Memorias persistentes) ─ depende de: Hito 1 (memoria transgeneracional)
Hito B (Cascada de estrés) ─ depende de: Hito 4 (error epistemológico) + Hito 9 (psicología oscura)
Hito C (Artefactos simbólicos) ─ depende de: Hito A (memorias) + Hito B (estrés)
Hito D (Fauna única/procedural) ─ depende de: Hito 6 (fauna simbólica)
Hito E (Cristalización de deidades) ─ depende de: Hito C (artefactos) + Hito A (memorias)
Hito F (Modo Leyendas) ─ depende de: todos los anteriores
Hito G (Historia pre-simulación) ─ depende de: Hito F (modo leyendas)
Hito H (Jerarquía noble) ─ depende de: Hito 10 (conocimiento) + Ext. B (conocimiento político)
Hito I (Rencores y cismas) ─ depende de: Hito 7 (linajes) + Hito 9 (psicología oscura)
Hito J (Duelo funerario) ─ depende de: Hito 2 (muerte significativa) + Hito A (memorias)
Hito K (Fantasmas culturales) ─ depende de: Hito J (duelo) + Hito E (deidades)
```

## Tabla de estado

| # | Hito | Origen | Depende de | Estado |
|---|---|---|---|---|
| Ext. A | Linajes de conocimiento | Post-R3 | Hito 10 | Pendiente |
| Ext. B | Conocimiento político | Post-R3 | Hito 10, Ext. A | Pendiente |
| Ext. C | Conocimiento inter-tribal | Post-R3 | Hito 10, Ext. A | Pendiente |
| A | Memorias persistentes | Dwarf Fortress | Hito 1 | Pendiente |
| B | Cascada de estrés y sombra | Dwarf Fortress | Hito 4, Hito 9 | Pendiente |
| C | Artefactos simbólicos | Dwarf Fortress | Hito A, Hito B | Pendiente |
| D | Fauna procedural única | Dwarf Fortress | Hito 6 | Pendiente |
| E | Cristalización de deidades | Dwarf Fortress | Hito C, Hito A | Pendiente |
| F | Modo Leyendas | Dwarf Fortress | Todos | Pendiente |
| G | Historia pre-simulación | Dwarf Fortress | Hito F | Pendiente |
| H | Jerarquía noble | Dwarf Fortress | Hito 10, Ext. B | Pendiente |
| I | Rencores y cismas | Dwarf Fortress | Hito 7, Hito 9 | Pendiente |
| J | Duelo funerario | Dwarf Fortress | Hito 2, Hito A | Pendiente |
| K | Fantasmas culturales | Dwarf Fortress | Hito J, Hito E | Pendiente |

---

## Notas de diseño

**El problema de la escala:** Dwarf Fortress corre en tiempo real; PSYCHE SIMULACRA tiene ticks discretos. Las cascadas de DF ocurren en segundos de juego; aquí deben tener efectos en días simulados. Los umbrales y probabilidades de este roadmap asumen que los efectos se acumulan día a día — si la simulación corre más rápido, los umbrales deben ajustarse.

**El principio de Tarn Adams aplicado aquí:** "La historia no se escribe — emerge de reglas físicas y sociales bajo presión ambiental." Ningún hito de este roadmap debe producir drama directamente. Cada hito añade un sistema de reglas que interactúa con los anteriores. El drama es consecuencia inevitable de la interacción, no objetivo directo de la implementación.

**Criterio global de validación del Roadmap 4:** Al ejecutar una simulación de 1000+ días con todos los sistemas activos, el WorldLedger exportado debe producir una narrativa histórica que un humano pueda leer como historia de una civilización primitiva — con figuras legendarias identificables, conflictos rastreables a causas, y una religión cuya teología se explica por los traumas de las primeras generaciones.

---

*Fuentes de investigación: Dwarf Fortress Wiki, Game AI Pro Vol. 2 Cap. 41 (Simulation Principles from Dwarf Fortress, Tarn Adams), IEEE Explore "Amorphous Fortress: Exploring Emergent Behavior", dwarffortresswiki.org sistemas: Emotion, Memory, Stress, Strange Mood, Legends, Religion, Forgotten Beasts, Artifacts, Noble, Grudges, Insanity.*
