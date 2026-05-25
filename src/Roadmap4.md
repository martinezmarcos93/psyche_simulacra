# Roadmap 4 — Profundidad Emergente
*Creado: 2026-05-24 | Revisado: 2026-05-25*

**Principio rector:** el mundo ya tiene presión. Este roadmap añade alma.
Los sistemas del Roadmap 3 generan eventos; los sistemas del Roadmap 4 generan *significado acumulado*, *historia con peso causal* e *identidades que se fracturan y recomponen.*

**Marco teórico:** psicología analítica junguiana, antropología cognitiva, teoría del poder (Weber, Bourdieu), antropología del ritual (Van Gennep, Turner), cultura material (Leroi-Gourhan, Ingold).
No se clonan mecánicas de videojuego — se traducen principios de emergencia social al marco teórico del experimento.

---

## PARTE I — EXTENSIONES DEL SISTEMA DE CONOCIMIENTO
*(Continuación directa del Hito 10)*

---

### Extensión A — Linajes de Conocimiento con Fidelidad Variable
**Marco:** degradación epistémica transgeneracional (Bartlett, "Remembering"; Lévi-Strauss, bricoleur)

El conocimiento actual es binario: lo tienes o no lo tienes. En la realidad, la misma técnica transmitida por 5 generaciones con distorsión acumulada es *cualitativamente diferente* al conocimiento recién descubierto. Un conocimiento que pasó por manos torpes se convierte en superstición; uno transmitido directamente del descubridor conserva potencia.

#### Componentes
- `KnowledgeLineage`: cada instancia de un conocimiento tiene un identificador de linaje, una fidelidad (0.0–1.0) y un historial de transmisiones (quién → quién, con qué bond_strength)
- Fidelidad inicial = 1.0 (descubrimiento accidental); cada transmisión aplica `fidelidad *= (1 - complejidad × 0.15 × (1 - bond_strength))`
- Fidelidad alta (> 0.70) → efecto completo; fidelidad baja (< 0.35) → conocimiento presente pero aplicado incorrectamente → tabúes falsos o rituales ineficaces
- Fidelidad < 0.20 transmitida reiteradamente → se registra en CulturalMemory como "supersticion_tecnica"
- Distorsión máxima: N transmisiones con bajo bond mutan el nombre del conocimiento (proto-léxico emergente)

#### Criterio de salida
Un conocimiento descubierto en generación 1 debe ser irreconocible (fidelidad < 0.15, nombre mutado) en generación 5+, pero seguir presente en CulturalMemory como "técnica ancestral" con efectos distintos al original.

---

### Extensión B — Proto-Chamanismo: El Especialista como Mediador Simbólico
**Marco:** Mircea Eliade ("El chamanismo y las técnicas arcaicas del éxtasis"); Lévi-Strauss ("El pensamiento salvaje"); Winkelman ("Shamanism: A Biopsychosocial Paradigm")

El especialista del Hito 10 atrae bonds entrantes. Esta extensión hace que ese poder sea *mediación simbólica*: el portador de conocimiento ritual no solo sabe más — se convierte en interfaz entre la tribu y lo desconocido, rol que toda cultura humana documentada ha producido espontáneamente.

#### Componentes
- `ProtoChamanRole`: estado emergente para agentes con ≥ 2 conocimientos de tipo ritual/medicina + arquetipo sabio > 0.60; el rol no se asigna — emerge cuando la tribu comienza a dirigirle solicitudes (eventos de "consulta" registrados en CulturalMemory)
- Función de mediación: el proto-chamán es el agente al que otros acuden antes de una catástrofe, una enfermedad, o una muerte → sus respuestas (transmisión de conocimiento o silencio) generan gratitud o resentimiento
- Autoridad simbólica: el proto-chamán tiene acceso al ICL tribal de forma privilegiada — puede iniciar "integración de sombra" (Hito B) y "ritual de integración" (Hito K)
- Sin programar: el rol emerge de la acumulación de interacciones, no de un umbral hardcodeado
- Muerte del proto-chamán: si muere sin sucesor, la tribu pierde el rol de mediación → histeria colectiva + regresión tecnológica medible en los 30 días siguientes

#### Criterio de salida
En 300+ días, al menos un agente debe alcanzar estatus de proto-chamán mediante acumulación orgánica de consultas, y su muerte debe producir perturbación colectiva observable en el ICL durante ≥ 20 días.

---

## PARTE II — PSICOLOGÍA PROFUNDA

---

### Hito A — Sistema de Memorias Persistentes con Trauma que Regresa
**Marco:** compulsión de repetición (Freud, "Más allá del principio de placer"); activación de complejo (Jung); trauma transgeneracional (Faimberg, "El telescopaje de generaciones")

La mente actual del agente no recuerda funcionalmente. Tiene un log episódico pero no hay eventos que *regresen* a disturbar su estado psicológico semanas después. Los humanos reales reviven traumas; las tribus reales son perseguidas por sus muertos no procesados.

#### Componentes
- `EpisodicMemory`: 8 slots de corto plazo (FIFO) + 8 de largo plazo (desplazados solo por eventos de mayor intensidad emocional)
- Cada memoria: tipo_evento, intensidad_emocional, dia_origen, dia_ultimo_revivido, n_revivencias, agente_protagonista
- Re-vivencia: probabilidad `intensidad × 0.03` por día → resurface aplica 60% del impacto emocional original
- Distorsión por re-vivencia: cada episodio amplifica el elemento arquetípico dominante y borra detalles periféricos → convergencia hacia el arquetipo puro (el muerto se vuelve más héroe o más monstruo con cada recuerdo)
- Trauma activo: memorias de largo plazo con intensidad > 0.80 → sueños perturbadores + contribución negativa al ICL tribal
- Integración memorial: rituales colectivos pueden anclar una memoria traumática, reduciendo re-vivencias a cambio de convertirla en memoria cultural colectiva

#### Criterio de salida
La muerte de un agente con bond alto debe seguir afectando a los sobrevivientes durante 50+ días mediante re-vivencias con atenuación progresiva, salvo que un ritual de integración la transforme en mito antes del día 20.

---

### Hito B — Cascada de Estrés y Estados de Disociación por Sombra
**Marco:** posesión por el arquetipo sombra (Jung, "Aion"); enantiodromia; psicología de masas (Jung, "Sobre la psicología de las masas"); amok como síndrome cultural (Simons & Hughes, "The Culture-Bound Syndromes")

La ansiedad actual es un número. No tiene estados cualitativamente distintos. Los humanos bajo presión extrema no se ponen "más ansiosos": colapsan en modos específicos que la psicología analítica reconoce como posesión por contenidos inconscientes. El amok es un fenómeno documentado transculturalmente — no es terminología de videojuego sino psiquiatría cultural.

#### Componentes
- Umbral de colapso: ansiedad > 0.85 durante ≥ 5 días consecutivos → el agente entra en estado de "disociación por sombra"
- Cuatro estados (basados en fenomenología clínica y etnopsiquiatría):
  - **Melancolía disociativa** (Sombra-Víctima): el agente deja de actuar, acepta su muerte pasivamente; ansiedad no reduce aunque haya recursos → umbral de muerte baja a 30 días. *Paralelo clínico: depresión mayor con inhibición psicomotriz*
  - **Amok** (Sombra-Guerrero): el agente ataca a los miembros con mayor bond; interacciones sociales generan conflicto en lugar de cooperación. *Paralelo clínico: episodio disociativo con violencia dirigida, documentado como síndrome cultural en culturas malayas, filipinas y otras*
  - **Fuga disociativa** (Sombra-Trickster): el agente toma decisiones desconectadas de su perfil arquetípico; comportamiento errático sin patrón; sabotea su contribución al ICL. *Paralelo clínico: fuga disociativa*
  - **Estupor catatónico** (Sombra-Vacío): el agente no toma ninguna acción; consume recursos sin producir; no responde a interacciones. *Paralelo clínico: catatonía*
- Cascada tribal: la disociación de un agente con muchos bonds propaga ansiedad mediante contagio emocional → posible cascada en la red
- Intervención del proto-chamán: puede intentar "integración de sombra" → probabilidad = sabio × 0.40; si falla, el proto-chamán recibe impacto de ansiedad proporcional
- Sin intervención en ≤ 15 días → estado permanente hasta la muerte

#### Criterio de salida
Una catástrofe prolongada sobre una tribu de 10 agentes debe producir al menos un episodio de disociación, que a su vez genere una cascada de ansiedad observable en ≥ 3 agentes adicionales.

---

## PARTE III — MITOLOGÍA MATERIALIZADA

---

### Hito C — Objetos Sagrados y Estados de Creación Compulsiva
**Marco:** objeto transicional (Winnicott); fetiche y tótem (Freud, "Tótem y tabú"); objetos sagrados como condensadores simbólicos (Eliade, "Lo sagrado y lo profano"); materialidad de la cultura (Miller, "Material Culture and Mass Consumption")

Los mitos son narrativas. Este hito añade la dimensión material: objetos físicos que cristalizan un estado psicológico colectivo. Un tótem no es decoración — es un nodo del ICL hecho materia, que persiste más allá de su creador y sigue irradiando efectos sobre quienes lo poseen.

#### Componentes
- `SacredObject`: objeto con nombre emergente, creador, dia_creacion, arquetipo_dominante, intensidad_simbolica, propietario actual, historial de posesión
- Estado de creación compulsiva: cuando un agente tiene ICL archetype field > 0.75 O ansiedad > 0.80 → probabilidad 0.002/día de entrar en estado creativo
- Cuatro tipos de objeto según el estado psicológico del creador:
  - **Objeto protector** (ICL cohesionado, baja ansiedad): reduce ansiedad de portadores con arquetipo afín. *Etnografía: amuleto, fetiche de protección*
  - **Objeto ambiguo** (ICL en tensión): sus efectos dependen del arquetipo del portador; la misma reliquia es fuente de poder para unos y de angustia para otros. *Etnografía: objetos sagrados que "eligen" a su portador*
  - **Objeto de duelo** (trauma de muerte reciente activo): ancla la memoria de una pérdida; amplifica la carga simbólica del GraveHex asociado. *Etnografía: objeto del muerto guardado por los sobrevivientes*
  - **Objeto perturbador** (sombra dominante, estado disociativo): aumenta ansiedad de portadores y quienes mueren cerca. *Etnografía: objeto maldito, tapu*
- El creador queda registrado en CulturalMemory como figura de significancia — su nombre persiste aunque muera
- Los objetos pueden heredarse, perderse en catástrofes, o quedar en hexes → GraveHex con objeto tiene carga simbólica × 1.5

#### Criterio de salida
Un agente en crisis debe crear un objeto perturbador que, al ser heredado, produzca efecto observable en el perfil arquetípico del heredero versus la media tribal.

---

### Hito E — Cristalización de Deidades desde el ICL
**Marco:** proyección arquetípica como génesis religiosa (Jung, "Psicología y Religión"); lo numinoso (Otto, "Lo Santo"); deidades procedurales como condensaciones del inconsciente colectivo

El motor de mitología cristaliza mitos pero no produce *deidades*. Un mito dice "algo pasó"; una deidad dice "algo *siempre* es verdad". La diferencia es la permanencia: una deidad sobrevive a la tribu que la creó porque ya no habita en individuos sino en el campo colectivo mismo.

#### Componentes
- `DeityRecord`: entidad emergente cuando un arquetipo en el ICL supera umbral de coherencia durante ≥ 30 días consecutivos, O cuando un mito cristaliza por 3ª vez con el mismo par arquetípico
- La deidad tiene: nombre procedural, arquetipo_fundacional, esfera_de_influencia, intensidad, dia_cristalizacion, tribu_origen
- Persiste en CulturalMemory independientemente del ICL actual — sobrevive a decaimientos del campo
- Proto-sacerdocio emergente: el agente con mayor alineación arquetípica al fundacional + más interacciones con el locus sagrado → se convierte en proto-chamán (o consolida el rol si ya lo tiene)
- Conflicto teológico: dos tribus con deidades del mismo arquetipo pero nombres distintos → tensión que puede resolverse en sincretismo o en hostilidad arquetípica

#### Criterio de salida
En 400+ días, al menos una deidad debe cristalizarse, generar proto-sacerdocio emergente, y sobrevivir 100+ días después de la muerte de su primer portador.

---

## PARTE IV — HISTORIA COMO INFRAESTRUCTURA

---

### Hito F — Registro Histórico Exportable
*Tratado como infraestructura de análisis, no como sistema que afecta agentes directamente.*

El sistema actualmente produce datos. Este hito hace que produzca *historia con cadena causal* — legible como narrativa, exportable para análisis externo.

#### Componentes
- `WorldLedger`: registro de eventos de alta significancia con estructura causal (A → causó → B → derivó en → C)
- Cada entrada: tipo, agentes_involucrados, dia, intensidad, consecuencias[], mitos_generados[]
- Exportación JSON + Markdown narrativo
- Figuras históricas: agentes cuya huella en CulturalMemory supera umbral → registrados con métrica de influencia (n_mitos_generados, n_agentes_afectados, n_objetos_creados)
- Linaje de objetos: trazabilidad completa de objetos sagrados (creador → propietarios → efectos)

*No tiene criterio de salida psicológico — es herramienta de observación del experimento.*

---

### Hito G — Historia Pre-Simulación *(diferido)*
*Alta complejidad técnica, baja urgencia. Implementar cuando los sistemas psicológicos centrales estén maduros. El concepto (trauma transgeneracional antes del primer tick) es válido pero depende de que Hitos A, J, K funcionen establemente primero.*

---

## PARTE V — DINÁMICA SOCIAL Y PODER

---

### Hito H — Roles Sociales Emergentes y Estructuras de Autoridad
**Marco:** tipos de autoridad (Weber: tradicional/carismática/racional-legal); big man y jefe (Marshall Sahlins, "Stone Age Economics"); capital simbólico (Bourdieu); banda y tribu (Elman Service, "Primitive Social Organization"); número de Dunbar como límite de complejidad social

La jerarquía actual es implícita en los bonds. Este hito la hace *explícita y reconocida colectivamente*: ciertos agentes asumen roles que la tribu legitima, con la autoridad y la fragilidad que eso implica. No hay "nobles con demandas" — hay estructuras de autoridad que emergen de dinámicas de poder documentadas en la etnografía.

#### Componentes
- `SocialRole`: rol emergente sin asignación programada; surge cuando la tribu acumula suficientes interacciones de reconocimiento hacia un agente específico
- Cuatro roles basados en etnografía real:
  - **Anciano/Elder**: el agente de mayor edad con bonds > 0.60 promedio; autoridad tradicional (Weber); función de memoria del grupo; su muerte activa duelo diferenciado máximo
  - **Big Man** (Sahlins): agente con mayor redistribución de recursos hacia otros (generosidad como mecanismo de poder); autoridad carismática; su poder cae si deja de redistribuir
  - **Proto-chamán**: ya definido en Ext. B; autoridad carismática de base ritual
  - **Cazador focal**: agente con más éxitos de subsistencia consecutivos; autoridad funcional, no simbólica; más frágil (depende de rendimiento continuo)
- Sucesión no programada: cuando el portador muere, el rol queda vacante; el agente con perfil más cercano lo absorbe gradualmente mediante acumulación de interacciones, no por asignación directa
- Período de transición: 15–30 días de inestabilidad tras la muerte del portador → ICL baja, conflictos de bond aumentan
- Ningún rol tiene "demandas" hardcodeadas — la tensión surge de la expectativa social acumulada en CulturalMemory

#### Criterio de salida
En 400+ días, al menos un rol debe emerger, sobrevivir la muerte de su primer portador mediante sucesión orgánica, y la transición debe producir período medible de inestabilidad en el ICL tribal.

---

### Hito I — Rencores Arquetípicos, Cismas y Cascadas de Lealtad
**Marco:** tensión de opuestos (Jung, "Tipos psicológicos"); fisión de bandas (Service); dinámica de lealtad en redes sociales (Simmel, "Sociología")

El sistema actual tiene celos y traición. Este hito añade la capa ideológica: agentes con arquetipos incompatibles que conviven inevitablemente acumulan fricción. La fractura no se programa — emerge de la acumulación de pequeñas incompatibilidades, exactamente como ocurre en grupos humanos reales.

#### Componentes
- Rencor arquetípico: dos agentes con arquetipos dominantes en pares opuestos (heroe/sombra, gobernante/rebelde, sabio/trickster) y bond < 0.30 acumulan rencor explícito (+0.01/día de convivencia en el mismo hex)
- Un rencor activo convierte interacciones neutrales en generadoras de ansiedad para ambos
- Umbral de pre-cisma: ≥ 30% de pares con rencores activos → la tribu entra en pre-cisma
- Cisma inevitable: ≥ 50% → la tribu se divide en dos grupos por afinidad arquetípica (fisión de banda documentada etnográficamente)
- Cascada de lealtad: un agente en amok que ataca a otro provoca respuesta de todos los agentes con bond > 0.50 hacia la víctima → escalada emergente del sistema de bonds existente
- El cisma genera dos tribus con herida en CulturalMemory ("schisma_tribal") → sus mitos divergen rápidamente

#### Criterio de salida
En tribu con arquetipos incompatibles, en 200+ días debe ocurrir cisma espontáneo. Las dos tribus hijas deben tener ICLs divergentes y mitos incompatibles para el día 100 post-cisma.

---

## PARTE VI — RITUAL Y MUERTE

---

### Hito J — Duelo Diferenciado y Ritual Funerario Emergente
**Marco:** rites de passage (Van Gennep); liminality y communitas (Victor Turner); duelo y melancolía (Freud); instituciones funerarias como primera forma de organización social (Ariès, "El hombre ante la muerte")

La muerte actual produce presión mítica y una tumba. Pero el *proceso de duelo* no existe: los sobrevivientes no hacen nada. El ritual funerario es probablemente la primera institución social humana — precede a la agricultura, a las ciudades, al lenguaje escrito. No puede ser una consecuencia invisible.

#### Componentes
- `GriefState`: duelo cuya duración y profundidad son proporcionales al bond con el fallecido
  - bond 0.50–0.70: duelo 20 días, reducción de productividad 20%
  - bond 0.70–0.90: duelo 50 días, ansiedad +0.30, sueños con símbolo del fallecido
  - bond > 0.90: duelo 90 días, riesgo de melancolía disociativa
- Ritual espontáneo: cuando ≥ 2 agentes con bond alto al fallecido se reúnen en el GraveHex en ≤ 5 días → ceremonia emergente → reduce duelo individual × 0.50 pero convierte el trauma en memoria colectiva
- Sin ritual: duelo sin resolución → probabilidad de re-vivencia del trauma (Hito A) × 2
- Muerte sin anclaje: agente que muere en hex sin GraveHex → sueños perturbadores en sobrevivientes cercanos por 30 días (la muerte sin lugar no puede convertirse en mito)
- Lugar sagrado: tribu que realiza ≥ 5 ceremonias en el mismo GraveHex → ese hex adquiere estado de "lugar sagrado permanente" con efectos × 2 sobre el ICL

#### Criterio de salida
La muerte de un agente con bonds altos en tribu que realiza ritual espontáneo debe reducir la duración del duelo colectivo en ≥ 40% versus tribu sin ritual, y producir proto-mito antes del día 30 post-muerte.

---

### Hito K — Presencia Ancestral: El Duelo No Procesado como Perturbación del Campo
**Marco:** duelo complicado (Bowlby); complejo autónomo como perturbador sistémico (Jung, "La estructura de la psique"); trauma transgeneracional (Faimberg); ancestros como figura cultural versus fantasma como figura patológica (Hertz, "La preeminencia de la mano derecha")

La diferencia entre un ancestro integrado (que protege) y una presencia perturbadora (que persigue) es si el duelo fue procesado. Este hito representa esa dualidad sin ningún elemento sobrenatural: es psicología del duelo colectivo no resuelto que se perpetúa en el ICL como patrón autónomo.

No hay fantasmas. Hay traumas no procesados que el ICL no puede cerrar.

#### Componentes
- `UnprocessedGrief`: estado emergente cuando un agente de alta significancia simbólica (proto-chamán, elder, figura con ≥ 2 conocimientos únicos) muere sin ritual, sin duelo completo, con trauma asociado activo
- Efectos en el ICL — todos explicables psicológicamente, ninguno sobrenatural:
  - Los arquetipos del fallecido se recargan en el ICL sin fuente trazable: la tribu habla de él, lo evoca, lo menciona en decisiones → el campo lo mantiene vivo simbólicamente
  - Los descendientes directos heredan complejidad de culpa aumentada (documentado en trauma transgeneracional)
  - El GraveHex genera eventos de presión simbólica con el arquetipo del muerto — la tribu evita el lugar o lo sobrevisita compulsivamente
- Resolución: el proto-chamán puede iniciar un proceso de integración colectiva (ritual de cierre de duelo) → probabilidad éxito = sabio × 0.35; si tiene éxito, la presencia perturbadora se convierte en presencia ancestral protectora
- Sin resolución: el patrón persiste activo mientras el GraveHex tenga carga simbólica — puede durar generaciones

#### Criterio de salida
La muerte sin ritual de una figura de alta significancia debe producir efectos observables en el ICL durante ≥ 50 días, con efectos en la distribución arquetípica de la generación siguiente.

---

## RESUMEN DE DEPENDENCIAS

```
Ext. A (Linajes conocimiento) ─── Hito 10
Ext. B (Proto-chamanismo)    ─── Hito 10 + Ext. A

Hito A (Memorias+trauma)     ─── Hito 1
Hito B (Disociación/Amok)    ─── Hito 4 + Hito 9
Hito C (Objetos sagrados)    ─── Hito A + Hito B
Hito E (Deidades desde ICL)  ─── Hito C + Hito A
Hito F (Registro histórico)  ─── infraestructura paralela
Hito G (Historia pre-sim)    ─── diferido
Hito H (Roles sociales)      ─── Hito 10 + Ext. B
Hito I (Rencores/cismas)     ─── Hito 7 + Hito 9
Hito J (Duelo/ritual)        ─── Hito 2 + Hito A
Hito K (Presencia ancestral) ─── Hito J + Hito E
```

## Tabla de estado

| # | Hito | Marco teórico | Depende de | Estado |
|---|---|---|---|---|
| Ext. A | Linajes de conocimiento | Lévi-Strauss, Bartlett | Hito 10 | ✅ Implementado |
| Ext. B | Proto-chamanismo | Eliade, Winkelman | Hito 10, Ext. A | ✅ Implementado |
| A | Memorias persistentes + trauma | Freud, Jung, Faimberg | Hito 1 | ✅ Implementado |
| B | Cascada de estrés / Amok | Jung, etnopsiquiatría | Hito 4, Hito 9 | ✅ Implementado |
| C | Objetos sagrados | Winnicott, Eliade, Miller | Hito A, Hito B | ✅ Implementado |
| E | Cristalización de deidades | Jung, Otto | Hito C, Hito A | ✅ Implementado |
| F | Registro histórico | infraestructura | paralelo | Pendiente |
| G | Historia pre-simulación | diferido | — | Diferido |
| H | Roles sociales emergentes | Weber, Sahlins, Bourdieu | Hito 10, Ext. B | ✅ Implementado |
| I | Rencores y cismas | Jung, Service, Simmel | Hito 7, Hito 9 | ✅ Implementado |
| J | Duelo y ritual funerario | Van Gennep, Turner, Ariès | Hito 2, Hito A | ✅ Implementado |
| K | Presencia ancestral | Jung, Bowlby, Hertz | Hito J, Hito E | ✅ Implementado |

## Orden de implementación aprobado

**A → B → J → K → I → Ext. A → E → C → H**

*(Ext. B y Hito F se desarrollan en paralelo a medida que los demás sistemas maduran)*

---

## Criterio global de validación del Roadmap 4

Al ejecutar una simulación de 1000+ días con todos los sistemas activos, el registro histórico exportado debe producir una narrativa que un humano pueda leer como historia de una civilización primitiva — con figuras de autoridad identificables, conflictos rastreables a incompatibilidades arquetípicas, y una cosmología cuya teología se explica por los traumas de las primeras generaciones.

---

*Marco teórico: Jung (obras completas, vols. 6, 9, 11); Freud ("Tótem y tabú", "Duelo y melancolía"); Eliade ("El chamanismo", "Lo sagrado y lo profano"); Van Gennep ("Ritos de paso"); Turner ("El proceso ritual"); Sahlins ("Stone Age Economics"); Weber ("Economía y sociedad"); Bourdieu ("El sentido práctico"); Service ("Primitive Social Organization"); Simmel ("Sociología"); Leroi-Gourhan ("El gesto y la palabra"); Winnicott ("Realidad y juego"); Bartlett ("Remembering"); Simons & Hughes ("The Culture-Bound Syndromes").*
