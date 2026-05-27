# ROADMAP 5 — Historia, Herencia y Civilización

> **Estado:** Diseño. Sin implementación hasta autorización explícita.
> **Diagnóstico central:** El sistema tiene psicología individual sofisticada y emergencia tribal funcional.
> El próximo salto es **historia**: profundidad temporal + mundo con memoria física.
>
> Dos ejes complementarios:
> - **Eje horizontal:** presión del mundo (catástrofes, fauna, sustancias, zonas liminales)
> - **Eje vertical:** profundidad temporal (infancia, herencia, lenguaje, cultura acumulativa)
>
> Sin el eje vertical, la presión del mundo produce estadísticas. Con él, produce historia.

---

## BLOQUE A — Profundidad Temporal
*El multiplicador de todo. Sin esto, cada generación reinicia simbólicamente.*

---

### Hito A1 — Memoria Transgeneracional con Distorsión
**Prioridad: Crítica. Implementar primero.**

Los hijos no heredan la memoria de los padres: heredan su *versión distorsionada actual*.
Cada transmisión cultural aplica ruido acumulativo: simplificación, amplificación, moralización,
identificación del transmisor, actualización al presente.

**Mecánica central:**
- Cada mito/leyenda tiene un campo `distorsion_acumulada` (float 0.0–1.0)
- Cada transmisión aplica delta según: vínculo transmisor–receptor, tiempo transcurrido,
  arquetipo dominante del transmisor (el héroe amplifica lo heroico, el sabio racionaliza)
- Después de N transmisiones el relato original es irreconocible
- El nombre del evento original queda en `nombre_original`; el relato activo en `relato_actual`

**Ejemplo trazado (sin programar — emerge de las mecánicas):**
```
Día 45: Adras mata un oso en territorio liminal, muere desangrado al día siguiente.
Día 50: "Adras mató un oso gigante en la montaña sagrada y murió por la maldición del lugar."
Día 100: "Adras venció al espíritu oso pero el espíritu se llevó su alma."
Día 300: "El héroe Adras fue elegido por los dioses para combatir al oso primordial."
Día 600: "Adras es el espíritu protector. Invocar su nombre ahuyenta a los osos."
```

**Genealogía simbólica:** el hijo de Adras crece creyendo descender de un ser sobrenatural.
Eso modifica su arquetipo desde el nacimiento — sin que el sistema lo programe.

**Guardianes del mito (emergente):**
Los agentes con extroversión alta + sabio dominante + muchos vínculos son nodos de transmisión
naturales. Se convierten en custodios del relato — proto-sacerdotes — sin ser designados.

**Conexión con sistemas existentes:** extiende `MythologyEngine` y `CulturalMemory`.

---

### Hito A2 — Infancia y Desarrollo
**Prioridad: Alta.**

Los agentes actualmente "aparecen completos". La psicología humana se imprime durante el
desarrollo. Este hito es el que convierte un ABM complejo en antropología simulada.

**Fases de desarrollo:**
- `niñez` (0–N días): alta plasticidad, imprinting de arquetipos por figura de apego principal.
  Trauma en esta fase = complejo estructural permanente, no procesable como trauma adulto normal.
- `adolescencia` (N–M días): cristalización del arquetipo dominante por contexto tribal.
  El arquetipo puede divergir del heredado si el entorno es suficientemente distinto.
- `adulto`: estado actual del sistema — sin cambios en lógica adulta.

**Imprinting:**
El agente que tiene mayor bond_strength con el recién nacido en sus primeros días se convierte
en figura de apego. Sus arquetipos y complejos activos en ese período dejan huella proporcional
a su bond e intensidad de interacción.

**Caso central:**
Dos agentes con herencia psicológica idéntica (mismo padre, misma madre) → arquetipos opuestos
por experiencias infantiles distintas (uno con figura de apego sombra dominante, otro con madre
dominante). Eso es el núcleo de la identidad individual emergente.

**Trauma infantil:**
Muerte del cuidador principal durante niñez = complejo de abandono máximo + predisposición alta
a arquetipo muerte o rebelde. No procesable con los mecanismos adultos normales de duelo.

---

### Hito A3 — Herencia Psicológica
**Prioridad: Alta. Requiere A2.**

No biología realista. Sí linajes míticos con efectos mecánicos.

**Herencia de rasgos:**
Al nacer, el agente hereda distribución arquetípica con variación:
- Base: promedio ponderado de arquetipos de ambos padres (60/40 según dominancia)
- Variación: ruido gaussiano proporcional a `disociacion` del ICL local en el día de nacimiento
- Deriva: arquetipos recesivos de abuelos pueden reaparecer (probabilidad baja)

**Linajes míticos:**
Cuando un ancestro tiene mito activo (A1), sus descendientes heredan predisposición hacia el
arquetipo de ese mito. No determinismo — probabilidad aumentada.

**Efectos emergentes (sin programarlos):**
- Clanes con paranoia hereditaria acumulativa
- Linajes con agresividad o sabio dominante por tres generaciones
- Descendientes de figura mítica con arquetipo sesgado desde nacimiento → castas, dinastías
- Profecías familiares (cuando el linaje mítico alcanza distorsión alta en A1)

**Selección social:**
Los agentes con arquetipos funcionales en el contexto tribal actual tienen mayor probabilidad
de reproducción — no por programación directa, sino porque sus bonds son más altos y su
integración simbólica más frecuente.

---

### Hito A4 — Lenguaje Emergente
**Prioridad: Media. Requiere A1.**

No NLP. Sí símbolos compartidos con efectos sobre percepción, sueños y cooperación.

La arquitectura ya tiene la base: el sistema de símbolos del ICL y `KnowledgeLineage`
son proto-vocabulario. Falta darle persistencia tribal y efectos sobre cognición.

**Vocabulario tribal:**
Cada tribu acumula un diccionario de `simbolos_lexicos`: palabras rituales para conceptos
clave (agua, fuego, muerte, extranjero, dios). Emergen de mitos cristalizados y eventos
con alta carga emocional colectiva.

**Divergencia lingüística:**
Una tribu puede desarrollar 7 símbolos para agua (ritual, potable, sagrada, contaminada,
oscura, de los muertos, de los dioses). Otra tribu tiene 1.
Eso cambia cómo sueñan, cómo perciben el entorno, qué pueden cooperar.

**Efectos mecánicos:**
- Agente con más vocabulario tribal = mejor integración de sueños compartidos
- Contacto inter-tribal: si los diccionarios difieren mucho → incomprensión real, no solo
  cultural. El mismo evento tiene nombres distintos y por tanto interpretaciones distintas.
- El chamán actual: guardián del vocabulario ritual → proto-sacerdote lingüístico

**Conexión con error cognitivo (D1):** la superstición nace cuando una tribu tiene una
sola palabra para dos fenómenos distintos y los trata como el mismo.

---

## BLOQUE B — Infraestructura Física y Mundo con Memoria
*El puente entre la actividad de los agentes y la historia irreversible del mapa.*

---

### Hito B1 — Herramientas como Conocimiento Materializado
**Prioridad: Media. Paralelo a Bloque A.**

Adaptación del concepto Valheim/Minecraft: no crafting como mecánica de juego.
La herramienta es **conocimiento que sobrevive a su creador**.

**Principios:**
1. Las herramientas se crean solo cuando el agente tiene el `KnowledgeLineage` correspondiente
   con fidelidad suficiente (> 0.70 = herramienta completa, 0.35–0.70 = herramienta defectuosa)
2. La herramienta creada hereda la fidelidad de su creador — no es mejor que quien la hizo
3. Una herramienta puede ser usada por un agente sin el conocimiento subyacente, pero con
   eficiencia reducida y sin poder replicarla
4. Herramientas sin portador quedan en el hex — objetos arqueológicos latentes

**Tipos funcionales (no exhausstivo — emergen según qué conocimientos tiene la tribu):**
- Herramienta de caza (requiere `caza_avanzada`)
- Recipiente de conservación (requiere `conservacion_agua`)
- Instrumento ritual (requiere `fuego_ritual`)
- Kit médico primitivo (requiere `curacion` o `alquimia_vegetal`)

**Extinción tecnológica ampliada:**
Si el único agente que puede *reparar o replicar* una herramienta muere, la herramienta
existente sigue funcionando pero se degrada con el tiempo. La técnica se extingue igual que
en Ext. A, pero la herramienta queda como reliquia sin comprensión.

**Conexión con economía simbólica (D2):** una herramienta del único portador de un
conocimiento adquiere valor ritual automáticamente — sin programarlo.

---

### Hito B2 — Construcción y Estructuras Persistentes
**Prioridad: Media-Alta. Requiere B1 para construcciones avanzadas.**

Las estructuras son el mecanismo por el que el mundo acumula capas de historia física.
Sin ellas, las ruinas y las cicatrices ecológicas son metáforas. Con ellas, son datos.

**Tipos de estructura:**
- `cabaña` — protección climática, aumenta recuperación de agentes en hex
- `hoguera_permanente` — reduce probabilidad de extinción de `fuego_ritual`
- `granero_primitivo` — almacenamiento colectivo, reduce impacto de hambrunas
- `altar` — amplifica cristalización mítica y consultas chamánicas en hex
- `muralla` — reduce probabilidad de cisma por presión externa, aumenta defensa de hex
- `cementerio` — carga simbólica acumulativa, ver Hito B3
- `monumento` — creado alrededor de figura mítica muerta, amplifica distorsión A1

**Construcción como acto colectivo:**
Una estructura no la construye un agente solo. Requiere bonds mínimos y conocimiento
compartido. El acto de construir juntos aumenta cohesión del ICL.

**Degradación:**
Las estructuras se degradan con el tiempo si no hay mantenimiento activo. Una tribu que
colapsa deja sus estructuras intactas pero sin mantenimiento → se convierten en ruinas
en N días proporcionales a la complejidad original.

**Herencia:**
Las estructuras pertenecen a la tribu, no al agente. Una tribu que hereda el territorio de
otra hereda sus estructuras — incluidas las que no puede comprender.

---

### Hito B3 — Historia Irreversible: Geografía Psicológica del Mundo
**Prioridad: Alta. Requiere B2.**

El núcleo de "historia irreversible": el mundo físico acumula carga simbólica que afecta
a los agentes que lo habitan generaciones después, aunque no sepan por qué.

**Tipos de marca permanente en el hex:**
- `ruina` — estructura de una tribu anterior. Aumenta curiosidad e incertidumbre ontológica.
  Las tribus que las encuentran las interpretan según su ICL actual (ver D1).
- `zona_traumatica` — hex donde ocurrió una catástrofe mayor (masacre, plaga, hambruna).
  Aumenta ansiedad de todos los agentes que lo ocupen. Puede generar tabú espacial emergente.
- `cementerio_activo` — hex designado formalmente para muertos. Carga simbólica acumulativa.
  Agentes con bond alto hacia enterrados regresan con mayor frecuencia (proto-peregrinación).
- `cicatriz_ecologica` — zona donde un incendio, sequía o colapso alteró recursos permanentemente.
  El cambio ecológico es irreversible en escala de simulación.
- `lugar_sagrado` — cementerio o altar con carga simbólica > umbral. Genera peregrinación
  activa, aumenta myth_pressure local, atrae chamanes y proto-sacerdotes.
- `zona_maldita` — hex con historia de muertes inexplicables o eventos perturbadores. Tabú
  emergente: los agentes evitan el hex aunque los recursos sean óptimos.

**Geografía psicológica:**
El mapa deja de ser neutral. Cada hex tiene una historia que afecta físicamente a quienes
lo habitan, aunque esa historia tenga miles de días de antigüedad y ningún agente vivo la
recuerde directamente. Solo existe en los mitos distorsionados (A1) y en la carga del hex.

**Ejemplo sin programar — emerge de las mecánicas:**
```
Día 200: tribu Bios realiza sacrificios repetidos en el lago del hex (3,7).
Día 201-400: hex acumula carga simbólica perturbadora.
Día 450: tribu Bios se extingue por plaga.
Día 600: tribu Thalia migra al hex (3,7). Sus agentes desarrollan ansiedad elevada sin
causa aparente. Sus chamanes lo asocian con "el agua que recuerda".
Día 700: tabú emergente — los agentes de Thalia no beben directamente del lago.
Día 1000: el lago aparece en sus mitos como fuente de poder oscuro.
```
Ninguna de estas consecuencias fue programada. Solo la acumulación de carga y su efecto.

---

### Hito B4 — Catástrofes Ambientales Irreversibles
**Prioridad: Alta.**

El clima actual describe condiciones. Necesita producir historia.

**La diferencia:** una sequía de 10 días que reduce recursos es un sistema de recursos.
Una sequía de 80 días que mata el 40% de la tribu y obliga al resto a migrar hacia
territorio enemigo es *historia*. El segundo evento genera mitos; el primero, estadísticas.

**Catástrofes y sus efectos narrativos:**
- **Sequía prolongada (60+ días):** mueren los más vulnerables. El grupo sobreviviente tiene
  arquetipo colectivo sesgado hacia gobernante/héroe. Mito de la resistencia.
- **Invierno brutal inesperado:** destruye estructuras sin hoguera permanente. Genera tabú
  retroactivo sobre comportamientos que "atrajeron el frío". Superstición estadística mal
  interpretada.
- **Incendio masivo:** destruye estructuras físicas. Tumbas y altares que sobreviven se
  vuelven más sagrados. Un profeta que muere en el incendio queda inmortalizado.
- **Plaga:** mata de forma aparentemente aleatoria → terror epistemológico → causalidad
  inventada → discriminación → jerarquía nueva basada en quién "atrajo" la enfermedad.
- **Eclipse:** ninguna muerte directa. Terror masivo + paranoia colectiva. Si coincide con
  una batalla, el bando ganador lo atribuye al eclipse → cosmogonía bélica.
- **Colapso de ecosistema:** fauna clave desaparece de una región. Si era fauna ritualizada
  (ver C1), la ausencia se convierte en señal mítica. El calendario ritual queda huérfano.

---

## BLOQUE C — Ecología Profunda
*El mundo como actor, no como escenario.*

---

### Hito C1 — Fauna como Actor Simbólico
**Prioridad: Media.**

Los animales no son recursos con patas. Son espejos arquetípicos. Los humanos primitivos
no consumían fauna — la interpretaban.

**Tipos de fauna y sus efectos:**
- **Depredadores territoriales:** terror existencial, cohesión tribal por miedo, mitos
  protectores. Un depredador que mata dos agentes en una semana cristaliza más mito que
  cien días de interacción social.
- **Especies migratorias:** ciclos rituales. Si las manadas pasan dos veces al año, aparecen
  calendarios. Los calendarios son el primer paso hacia cosmogonía.
- **Animales nocturnos:** amplificación de lo onírico. Un búho en el mismo hex donde un
  agente sueña genera asociación simbólica real — no programada.
- **Fauna carroñera:** aceleración del trauma post-muerte. Presiona hacia ritos funerarios
  más elaborados (conexión con B3 cementerio).
- **Manadas que desplazan tribus:** migración forzada. Una tribu que pierde su territorio
  y se superpone con otra es el origen del 80% de los conflictos históricos reales.
- **Especies raras:** singularidad mítica automática. Un animal que solo tres agentes han
  visto en toda la simulación se vuelve significativo por la rareza misma.

**Lectura arquetípica diferenciada:**
El mismo animal es leído distinto por tribus con ICL distinto. No el animal cambia — la
interpretación cambia según el diccionario simbólico de cada tribu (conexión con A4).
Un lobo puede ser protector (tribu con madre dominante) o cazador mítico (tribu con héroe
dominante) o mensajero de muerte (tribu con morte dominante).

---

### Hito C2 — Sustancias Psicoactivas
**Prioridad: Media-Alta.**

El catalizador más potente para la cristalización mítica. La mayoría de las religiones
tempranas tienen componente enteogénico documentado.

**Taxonomía:**

| Tipo | Efecto sobre agente | Efecto sobre ICL colectivo |
|---|---|---|
| Enteógeno | +sueños compartidos, -individuación, +visiones | +cristalización acelerada, -tiempo al primer mito |
| Veneno | muerte lenta, delirio, narrativa del moribundo | trauma + mito escatológico si el agente era arquetípicamente significativo |
| Fermentación | +impulsividad, -inhibición, +vínculos rápidos pero frágiles | +emotional_pressure, +violencia nocturna |
| Medicinal | curación acelerada, gratitud al poseedor | +status chamán, proto-especialización |
| Alucinógeno visual | +paranoia, +creatividad, símbolos extraños | símbolos nunca vistos en ICL, disrupción del campo existente |
| Adictivo | dependencia, degradación física lenta | el poseedor adquiere poder real sobre los dependientes |

**Cadena chamánica no programada:**
Tribu descubre hongo enteogénico → sueño vívido compartido → myth_pressure explota →
cristalización de tipo teogonía ("el hongo es el dios") → chamán controla el acceso →
primera proto-casta. Sin que ningún paso esté programado explícitamente.

**Conexión Zona Liminal:** consumir enteógeno dentro de zona liminal amplifica efectos.
La zona puede generar sustancias raras como parte de su misterio.

---

## BLOQUE D — Fricción Cognitiva y Economía Cultural
*El agente que se equivoca, miente, intercambia y olvida.*

---

### Hito D1 — Error Cognitivo Profundo
**Prioridad: Alta.**

Los agentes actuales son psicológicamente complejos pero internamente honestos.
Los humanos reales raramente sienten lo que sienten — se cuentan una historia sobre lo que sienten.

**Mecanismos cognitivos a implementar:**

- **Autoengaño:** el complejo activo no se reconoce como propio. Se racionaliza como cualidad
  del exterior. Complejo de inferioridad activo → "la tribu del otro es inferior".
- **Sesgo retroactivo:** dos eventos cercanos en el tiempo construyen causalidad.
  Eclipse + muerte del líder → tabú sobre observar el cielo.
- **Contagio emocional:** el miedo de un agente con bond alto se transmite como dato social
  antes de que haya amenaza real. Pánico colectivo por un solo agente conectado.
- **Disonancia cognitiva:** el mito que falló no se abandona. Se añade capa de explicación.
  "El mito es verdadero pero lo aplicamos mal" → reforma religiosa, no abandono.
- **Histeria colectiva:** myth_pressure + confusion + emotional_pressure superan umbrales
  simultáneamente → comportamiento errático, visiones no oníricas, transmisión masiva
  distorsionada. El campo colectivo explota y se reconfigura.
- **Paranoia tribal:** tribu atacada múltiples veces desarrolla prior de amenaza.
  Un extranjero que se acerca a dar agua es percibido como espía.

**Radio de percepción limitado:**
Lo que ocurre a 5+ hexágonos no llega directamente — llega como rumor a través de vínculos,
ya distorsionado en proporción a los nodos intermedios. Atención selectiva por arquetipo:
el héroe nota conflictos, la madre nota muertes de menores. Mismo mundo, narrativas distintas.

---

### Hito D2 — Economía Simbólica
**Prioridad: Media.**

No comercio clásico. Deuda ritual, prestigio, reciprocidad ceremonial.
El origen de la política y la diplomacia sin programarlas.

**Mecanismos:**
- `deuda_ritual`: un acto de salvamento, curación o protección genera obligación simbólica
  registrada entre agentes y entre tribus. No se salda con recursos — se salda con lealtad,
  protección futura, o intercambio de agentes (alianzas matrimoniales).
- `prestigio_acumulado`: acciones públicas con testigos de bond alto aumentan prestigio.
  El prestigio modifica cómo los otros agentes leen las acciones futuras del portador —
  el mismo acto de un agente de alto prestigio se interpreta de forma más favorable.
- `reciprocidad_ceremonial`: intercambios regulares de objetos simbólicos entre tribus
  (reliquias, herramientas rituales, sustancias raras) crean red de obligaciones mutuas.
  Romper la cadena de reciprocidad activa mecánica similar a la traición de bond.
- `sacrificio_colectivo`: destrucción voluntaria de recursos ante el ICL colectivo.
  El que sacrifica más adquiere prestigio máximo — el big_man de Sahlins, emergente.

**Efectos en política (emergentes):**
- Diplomacia: dos tribus con red de deuda ritual tienen umbral de ataque más alto.
- Guerra santa: una tribu que siente que la deuda ritual fue profanada puede activar
  el sistema de cisma + cascada de lealtad ya implementado en Hito I, pero ahora con
  justificación narrativa.
- Casta sacerdotal: los guardianes del sistema de deuda ritual (quiénes deben qué a quién)
  se vuelven imprescindibles → poder sin violencia.

---

### Hito D3 — Muerte Cultural y Colapso Civilizatorio
**Prioridad: Media-Alta.**

Ahora mueren agentes y sobreviven mitos. Falta que mueran culturas enteras y que
la pérdida de conocimiento sea arqueológicamente visible.

**Colapso civilizatorio:**
Una tribu se extingue completamente cuando el último agente muere sin herederos ni
agentes absorbidos por otra tribu. Sus estructuras quedan como ruinas (B3). Su ICL
se congela como "eco colectivo" — presencia residual en el campo de la zona que
los agentes que lleguen después podrán percibir pero no descifrar.

**Interpretación errónea de ruinas:**
Una tribu que encuentra las ruinas de otra las interpreta según su propio ICL actual:
- Sus símbolos leen los símbolos ajenos como confirming de sus propios mitos
- Los objetos sagrados encontrados adquieren significado local — no el significado original
- El mito que emerge sobre los constructores de las ruinas es una proyección de quien lo narra

**Ejemplo de la tesis central:**
```
Tribu Bios construye altar al dios-lobo (su arquetipo dominante).
Tribu Bios se extingue en plaga.
Tribu Thalia llega 300 días después, encuentra altar con figuras de lobo.
El arquetipo dominante de Thalia es madre.
Thalia interpreta el lobo como "protector de los recién nacidos".
Nace una religión falsa basada en los restos de una religión que no tuvo nada que ver.
ESO es humanidad.
```

**Olvido histórico:**
El mito distorsionado (A1) de una tribu extinta llega a generaciones futuras con
distorsión máxima. Después de suficientes transmisiones, el origen real desaparece.
Solo queda el relato — irreconocible respecto al evento original.

---

## BLOQUE E — Arquitectura Trans-Simulación
*La Zona Liminal como inconsciente colectivo del multiverso.*

---

### Hito E1 — Zonas Liminales como Geografía Física
**Prioridad: Media. Puede implementarse en paralelo con bloques anteriores.**

Un tipo de hex especial donde convergen condiciones extremas: fauna rara, microclima
anómalo, sustancias psicoactivas naturales. El misterio lo crean los agentes al no
poder rastrear las causas — no el código.

**Propiedades del hex liminal:**
- Aumenta variabilidad onírica (más sueños compartidos, más sueños extraños)
- Modifica arquetipos de forma no lineal (puede amplificar cualquiera, no solo dominantes)
- Genera símbolos del ICL que no provienen de ningún agente individual
- Aumenta disociación en agentes con paranoia alta
- Puede producir muertes aparentemente aleatorias (fauna liminal, microclima)
- Los efectos no son rastreables causalmente por los agentes → superstición automática

**Lo crucial:** la zona liminal no es sobrenatural en el código. Es un hexágono donde
las condiciones extremas convergen. El misterio lo producen los agentes al interpretarlo.

---

### Hito E2 — Zona Liminal como Inconsciente Colectivo del Multiverso
**Prioridad: Depende de estado del proyecto Zona Liminal externo.**

Este es el salto arquitectónico más ambicioso. Trasciende PSYCHE SIMULACRA como sistema
individual.

**Visión:**
La Zona Liminal no es solo "multiplayer simbólico" — es el inconsciente colectivo objetivo
que trasciende instancias de simulación. Un espacio donde:
- Los sueños de agentes de distintas simulaciones se mezclan
- Los mitos migran entre mundos sin traducción directa
- Los arquetipos se contagian entre instancias
- Aparecen religiones trans-simulación (una figura mítica de Sim A llega como portento a Sim B)
- Un héroe muerto en Sim A se vuelve dios en Sim B porque su mito llegó antes que su nombre

**Interfaz técnica mínima:**
Un JSON de estado de agente (arquetipo dominante, mitos portados, trauma activo, carga simbólica)
que cruza entre sistemas y regresa modificado según las reglas del sistema receptor.
La complejidad es conceptual, no técnica.

**La pregunta que define el diseño:**
¿Qué reglas tiene el otro lado? Eso es un documento aparte — el Roadmap del proyecto
Zona Liminal. Este hito solo define la interfaz desde el lado de PSYCHE SIMULACRA.

**Consecuencia si se implementa:**
PSYCHE SIMULACRA deja de ser una simulación de una civilización.
Se convierte en la primera capa de una arqueología de civilizaciones artificiales.

---

## Lo que NO hay que hacer

- No agregar más arquetipos. 12 es suficiente; el problema es más presión, no más dimensiones.
- No agregar más tipos de métricas antes de tener más eventos que medir.
- No implementar ningún hito sin primero diseñar su integración con **A1 (memoria transgeneracional)**.
  Todo depende de que el pasado tenga peso sobre el presente.
- No convertir B1 (herramientas) en un juego de crafting. El objetivo es que el conocimiento
  sobreviva a su creador — no que los agentes gestionen inventarios.
- No convertir C1 (fauna) en supervivencia. El objetivo es que los animales generen mitos.
- No implementar A3 (herencia psicológica) como genética determinista. El arquetipo heredado
  es punto de partida, no destino.

---

## Secuencia de implementación recomendada

```
A1 (memoria transgeneracional)   ← primero. Multiplicador de todo.
    ↓
A2 (infancia y desarrollo)       ← requiere A1 para que el imprinting tenga historia
    ↓
B3 (historia irreversible)       ← en paralelo con A2; requiere que haya historia que marcar
B4 (catástrofes)                 ← en paralelo; produce los eventos que B3 cristaliza
    ↓
B2 (construcción y estructuras)  ← produce las ruinas que B3 registra
B1 (herramientas)                ← en paralelo con B2
    ↓
A3 (herencia psicológica)        ← requiere A2 para tener desarrollo sobre el que heredar
A4 (lenguaje emergente)          ← requiere A1 para tener mitos que lexicalizar
    ↓
D1 (error cognitivo profundo)    ← amplifica todo lo anterior con sesgo y distorsión
C2 (sustancias psicoactivas)     ← catalizador, puede ir en paralelo con D1
C1 (fauna simbólica)             ← en paralelo
    ↓
D2 (economía simbólica)          ← requiere que haya historia de deudas y prestige acumulados
D3 (muerte cultural)             ← requiere que haya civilizaciones que puedan colapsar
    ↓
E1 (zonas liminales físicas)     ← puede ir antes, es relativamente independiente
E2 (Zona Liminal multiverso)     ← último, requiere coordinar con proyecto externo
```

---

## Hitos del Roadmap 4 pendientes

**Hito F — Registro Histórico Exportable:** pendiente. Infraestructura de análisis, no
psicología de agente. Puede implementarse en cualquier punto sin bloquear este roadmap.

---

*Última actualización: 2026-05-25*
*Estado: diseño completo — sin implementación*
