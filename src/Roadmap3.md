# Roadmap 3 — Fricción Evolutiva Real
*Derivado de NOTAS_friccion_evolutiva.md | 2026-05-24*

**Principio rector:** el mundo debe volverse peligroso, opaco y con memoria propia.
Cada hito se apoya en los anteriores. No implementar un hito sin que el anterior esté en verde.

---

## Hito 1 — Memoria Transgeneracional con Distorsión
**Prioridad: CRÍTICA. Es el multiplicador de todo lo que sigue.**

Sin este sistema, cada generación parte de cero simbólico. Con él, el pasado pesa sobre el presente de forma acumulativa e irreversible.

### Componentes
- [ ] `TransmissionRecord`: estructura que representa un evento real (agente, día, descripción, arquetipo_dominante, intensidad_emocional)
- [ ] `DistortionEngine`: aplica ruido de transformación narrativa en cada acto de transmisión (simplificación, amplificación, moralización, identificación, actualización)
- [ ] `CulturalMemory` por tribu: lista ordenada de `TransmissionRecord` con versión actual distorsionada
- [ ] Mecanismo de transmisión: los agentes con extroversión alta + arquetipo sabio dominante transmiten con mayor frecuencia y alcance
- [ ] Herencia al nacer: el hijo recibe la versión *actual* distorsionada de los registros de su tribu, no los hechos originales
- [ ] Efectos de la memoria heredada sobre el arquetipo inicial del descendiente

### Criterio de salida
Un evento del día 10 debe ser rastreable en sus versiones distorsionadas en días 50, 200, y 500+, con el original irreconocible en la última transmisión.

---

## Hito 2 — Muerte Significativa y Tumbas Sagradas
**Depende de: Hito 1 (el muerto necesita entrar al sistema de memoria)**

La muerte actual es salida del sistema. Debe ser entrada a otro sistema: el cultural.

### Componentes
- [ ] Registro de muerte con coordenadas, arquetipo del muerto, agentes presentes, intensidad del vínculo roto
- [ ] `GraveHex`: hexágono que acumula carga simbólica por muertes ocurridas en él; contribuye al ICL tribal local
- [ ] Comportamiento post-muerte de sobrevivientes con bond alto: tendencia a regresar al hexágono de la muerte, aumento de myth_pressure local
- [ ] Distorsión de recuerdo del muerto según arquetipo del que recuerda (el héroe recuerda al muerto como héroe; el sabio como sabio)
- [ ] Peregrinación emergente: si el GraveHex supera umbral de carga simbólica, agentes con afinidad arquetípica se desplazan hacia él periódicamente
- [ ] El muerto que tiene más poder que vivo: si la versión mítica del muerto en CulturalMemory supera su bond_strength real, el agente es declarado figura simbólica activa en el ICL

### Criterio de salida
La muerte de un agente con arquetipo dominante fuerte debe producir, en las siguientes N generaciones, una figura mítica rastreable en CulturalMemory y un GraveHex con carga simbólica elevada.

---

## Hito 3 — Sustancias Psicoactivas
**Depende de: Hito 1 (la experiencia enteogénica debe entrar a CulturalMemory)**

El catalizador más potente para cristalización mítica acelerada y emergencia de especialización chamánica.

### Componentes
- [ ] `SubstanceType` enum: enteógeno, veneno, alcohol, medicinal, alucinógeno_visual, adictivo
- [ ] Distribución en biomas: cada sustancia tiene biomas válidos y probabilidad de descubrimiento por contacto accidental
- [ ] Efectos por tipo sobre el agente: modificadores de arquetipo, sueños, myth_pressure, emotional_pressure, estado físico
- [ ] Efectos sobre CollectiveField cuando múltiples agentes consumen en proximidad (resonancia grupal)
- [ ] Cadena chamánica emergente: el agente que media el acceso a la sustancia sube en bond_strength con quienes tuvieron visiones; si se repite, se convierte en nodo de transmisión privilegiado
- [ ] Zona Liminal + sustancia: consumo dentro de zona liminal amplifica efectos × factor configurable
- [ ] Dependencia: sustancias adictivas degradan traits físicos lentamente; el poseedor gana poder instrumental sobre dependientes

### Criterio de salida
Una tribu que descubre un enteógeno debe, sin intervención programada, producir un proto-chamán y acelerar la cristalización de un mito de tipo teogonía en los siguientes 30 días simulados.

---

## Hito 4 — Error Epistemológico y Percepción Limitada
**Depende de: Hitos 1 y 2 (los rumores deben distorsionarse como la memoria)**

Convierte agentes racionales en humanos reales. El mundo debe ser parcialmente ilegible.

### Componentes
- [ ] Radio de percepción por agente (configurable, base ~3 hexágonos): eventos fuera del radio no se perciben directamente
- [ ] Sistema de rumores: eventos lejanos llegan a través de la cadena de vínculos sociales, aplicando distorsión en cada salto
- [ ] Atención selectiva por arquetipo dominante: el héroe prioriza conflictos, la madre prioriza nacimientos/muertes de menores, el sabio prioriza eventos inexplicables
- [ ] Sesgo de causalidad: dos eventos temporalmente cercanos generan una asociación causal en el agente; si la asociación se transmite, se convierte en tabú
- [ ] Contagio emocional: el miedo de un agente con muchos vínculos se propaga como dato social antes de que haya amenaza real
- [ ] Disonancia cognitiva: cuando un mito falla como predicción, el agente no lo abandona sino que agrega capa de explicación (reforma religiosa, no apostasía)
- [ ] Histeria colectiva: cuando myth_pressure + confusion + emotional_pressure superan umbrales simultáneos en un cluster de agentes, se dispara estado de histeria colectiva

### Criterio de salida
Un eclipse (evento climático puro) debe poder producir, sin código específico de "eclipse genera mito", un proto-mito escatológico en tribus con agentes de alta paranoia y vínculos densos.

---

## Hito 5 — Catástrofes Climáticas Irreversibles
**Depende de: Hito 4 (los agentes deben percibir e interpretar mal la catástrofe)**

La diferencia entre una sequía de 10 días (estadística) y una de 80 días que mata el 40% de una tribu (historia).

### Componentes
- [ ] `CatastropheEngine`: genera eventos de gran escala con duración, área de efecto y severidad
- [ ] Tipos: sequía prolongada, invierno brutal, incendio masivo, plaga, eclipse
- [ ] Efectos diferenciados: mortalidad selectiva por vulnerabilidad (niños, ancianos primero), destrucción de estructuras físicas, migración forzada
- [ ] Persistencia: las catástrofes dejan huella en el terreno (hexágonos quemados, pozos secos) que dura N días configurables
- [ ] Tumbas sagradas resistentes: estructuras o GraveHex que sobreviven una catástrofe aumentan carga simbólica automáticamente
- [ ] Plaga como terror epistemológico: muerte aparentemente aleatoria → marcación de enfermos (tabú de contagio) → jerarquía nueva emergente

### Criterio de salida
Una sequía de 80 días sobre una tribu de 30 agentes debe producir: mortalidad del 30-50%, migración de sobrevivientes, y al menos un proto-mito de tipo resistencia o castigo divino en CulturalMemory.

---

## Hito 6 — Fauna como Actor Simbólico
**Depende de: Hito 5 (la fauna liminal requiere biomas extremos)**

Los animales no son recursos con patas; son espejos arquetípicos. El objetivo no es que los agentes cacen eficientemente sino que los animales generen mitos.

### Componentes
- [ ] `FaunaEntity`: entidad con tipo (depredador, migratorio, nocturno, carroñero, raro), territorio, comportamiento básico
- [ ] Carga simbólica diferencial por tribu: distintas tribus que observan el mismo animal acumulan carga distinta en su ICL local
- [ ] Depredadores territoriales: matan agentes con probabilidad basada en proximidad; dos muertes en una semana activan cristalización mítica
- [ ] Especies migratorias: patrón de aparición cíclico → proto-calendario → proto-cosmogonía
- [ ] Animales raros: baja frecuencia de aparición → cualquier avistamiento se convierte en evento significativo en ICL
- [ ] Fauna carroñera: los cadáveres atraen fauna en días siguientes → presión adicional hacia ritos funerarios
- [ ] Fauna liminal: animales en zonas liminales tienen propiedades distintas; el mismo animal en territorio conocido vs zona liminal genera carga simbólica radicalmente diferente

### Criterio de salida
Un depredador territorial que mata dos agentes en siete días debe generar, sin intervención programada, un proto-mito de tipo protector o amenaza cósmica en el ICL de la tribu afectada.

---

## Hito 7 — Linajes, Parentesco y Tabú del Incesto
**Depende de: Hito 1 (los linajes necesitan memoria transgeneracional para tener efectos)**

Las estructuras de parentesco son el primer software social de la humanidad.

### Componentes
- [ ] Linaje rastreable: cada agente nace con padres conocidos; la genealogía se persiste en base de datos
- [ ] Herencia de arquetipos con variación: los hijos reciben combinación ponderada de arquetipos paternos + ruido
- [ ] Herencia de enemistades y alianzas: bond_strength heredado con variación desde el entorno familiar
- [ ] Celos como motor de conflicto: interferencia en vínculo de exclusividad activa complejo de abandono + impulso agresivo + narrativa de traición
- [ ] Paternidad incierta: en condiciones de poligamia emergente, los agentes masculinos no pueden verificar paternidad → estructuras de control emergentes
- [ ] Alianzas matrimoniales inter-tribales: intercambio de agentes reproductores entre tribus → transferencia cultural real de perfiles arquetípicos
- [ ] Tabú del incesto emergente: si la endogamia produce traits deteriorados estadísticamente observables, el tabú emerge como distorsión de percepción causal; no se programa, se observa

### Criterio de salida
En una simulación de 500+ días, dos tribus que intercambian agentes deben mostrar convergencia parcial de ICL. Una tribu que practica endogamia por aislamiento debe mostrar deterioro de traits en generaciones 3+.

---

## Hito 8 — Zonas Liminales Expandidas (Hexágono Especial)
**Depende de: Hito 6 (fauna liminal) y Hito 3 (sustancias en zonas liminales)**

Las zonas liminales ya existen como conexión cross-sim. Este hito las expande como geografía simbólica local con efectos propios.

### Componentes
- [ ] `LiminalHex`: tipo de hexágono con propiedades de misterio configurable
- [ ] Variabilidad onírica aumentada: agentes que duermen adyacentes a LiminalHex tienen mayor probabilidad de sueños compartidos y sueños con símbolos no presentes en su ICL
- [ ] Modificación arquetípica no linear: amplifica cualquier arquetipo, no solo los dominantes; puede empujar arquetipos dormidos
- [ ] Generación de símbolos ICL autónomos: el LiminalHex puede inyectar símbolos en el campo colectivo local sin que provenga de ningún agente individual
- [ ] Efectos no trazables causalmente: fauna, microclima, sustancias raras; los agentes no pueden rastrear la causa → superstición automática
- [ ] Interfaz cross-sim: el LiminalHex local es el punto de entrada/salida para el proyecto Zona Liminal externo

### Criterio de salida
Agentes que frecuentan un LiminalHex deben desarrollar, en comparación con la media tribal, perfiles arquetípicos más extremos y mayor tasa de generación de proto-mitos.

---

## Hito 9 — Psicología Oscura
**Depende de: Hito 4 (los mecanismos cognitivos oscuros son extensiones del error epistemológico)**

La psicología actual es sofisticada pero honesta. Los humanos reales raramente sienten lo que sienten.

### Componentes
- [ ] Autoengaño: el agente con complejo activo no lo reconoce; lo racionaliza como atributo del otro (proyección)
- [ ] Sesgo de atribución: los fracasos propios se atribuyen a causas externas; los fracasos ajenos a causas internas
- [ ] Paranoia tribal: una tribu que ha sido atacada múltiples veces desarrolla prior de amenaza; eventos neutros se interpretan como hostiles
- [ ] Contagio emocional codificado: el miedo/euforia se propaga con velocidad proporcional a bond_strength del portador
- [ ] Disonancia cognitiva: implementar el mecanismo de reforma religiosa (no abandono) cuando un mito falla
- [ ] Histeria colectiva: trigger multicriterio + comportamiento errático colectivo + reconfiguración del ICL local

### Criterio de salida
Una tribu que sufre un ataque debe mostrar, en los siguientes 20 días, interpretación hostil de al menos un evento neutro de una tribu vecina (rumor distorsionado → decisión agresiva sin causa real).

---

## Hito 10 — Tecnología Emergente y Asimetría de Conocimiento
**Depende de: todos los anteriores. La especialización emerge solo cuando hay suficiente presión y linajes.**

El objetivo no es crafting sino la asimetría de conocimiento como fuente de poder social.

### Componentes
- [ ] `KnowledgeUnit`: representación de un conocimiento (conservación, fuego ritual, curación, técnica constructiva)
- [ ] Descubrimiento accidental: probabilidad de descubrimiento ligada a exposición a condiciones específicas, no a investigación sistemática
- [ ] Transmisión imperfecta: cada acto de enseñanza tiene probabilidad de pérdida o distorsión del conocimiento
- [ ] Extinción por muerte del portador: si el único agente con un conocimiento muere sin transmitir, el conocimiento desaparece
- [ ] Asimetría de poder: el monopolio de un conocimiento valioso aumenta el bond_strength entrante del portador; los demás aumentan su dependencia
- [ ] Especialización emergente: cuando un agente es el único portador de N conocimientos valiosos, se convierte en nodo crítico de la tribu sin intervención programada
- [ ] Pérdida tecnológica post-guerra: tribu que pierde su segmento adulto pierde los conocimientos que solo adultos portaban

### Criterio de salida
Una tribu que pierde a su agente con mayor número de conocimientos debe mostrar regresión medible en capacidad de respuesta a eventos climáticos en las 2 generaciones siguientes.

---

## Restricciones del roadmap

1. **No implementar** Hito N+1 hasta que Hito N tenga tests en verde y criterio de salida verificado manualmente en una simulación de prueba.
2. **No agregar arquetipos nuevos** en ningún hito. 12 es suficiente; el problema es más presión, no más dimensiones.
3. **No agregar métricas** antes de tener eventos nuevos que medir (las métricas se agregan al final de cada hito, no al principio).
4. **No convertir fauna en juego de supervivencia.** El objetivo de cada sistema de fauna es producir mitos, no que los agentes gestionen recursos eficientemente.
5. **No implementar tecnología** como árbol de investigación. La tecnología emerge del accidente y del vínculo social, no de la decisión racional.
6. **Todo lo que se agregue debe integrarse con CulturalMemory** (Hito 1). Si un nuevo sistema no produce entradas en CulturalMemory, no genera historia.

---

## Estado inicial

| Hito | Estado | Desbloqueado |
|---|---|---|
| 1. Memoria transgeneracional | Pendiente | Sí — primer hito |
| 2. Muerte significativa | Pendiente | Tras Hito 1 |
| 3. Sustancias psicoactivas | Pendiente | Tras Hito 1 |
| 4. Error epistemológico | Pendiente | Tras Hitos 1 y 2 |
| 5. Catástrofes irreversibles | Pendiente | Tras Hito 4 |
| 6. Fauna simbólica | Pendiente | Tras Hito 5 |
| 7. Linajes y tabú | Pendiente | Tras Hito 1 |
| 8. Zonas liminales expandidas | Pendiente | Tras Hitos 6 y 3 |
| 9. Psicología oscura | Pendiente | Tras Hito 4 |
| 10. Tecnología emergente | Pendiente | Tras todos los anteriores |

---

*Fuente: NOTAS_friccion_evolutiva.md*
*El diagnóstico de fondo: el mundo exterior no genera suficiente presión irreversible. Este roadmap lo corrige.*
