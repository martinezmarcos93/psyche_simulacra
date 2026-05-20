# PSYCHE SIMULACRA — Bibliografía Fundamental
## Fuentes Teóricas, Científicas y Técnicas del Proyecto

> *Un experimento sin bibliografía es filosofía de bar.*  
> *Con bibliografía es investigación.*

---

## CÓMO LEER ESTE DOCUMENTO

Cada fuente tiene:
- **Relevancia directa** — para qué sirve exactamente en el proyecto
- **Cita clave** — el concepto central que tomamos
- **Implementación** — qué parte del código valida o se apoya en esta fuente

Las fuentes están organizadas por capa teórica, no por autor.
El proyecto es la intersección de todas estas capas.

---

## I. JUNG — EL NÚCLEO TEÓRICO

### Obras Fundamentales

---

**Jung, C. G. (1959). *The Archetypes and the Collective Unconscious.***
*Collected Works, Vol. 9, Part I. Princeton University Press.*

> Relevancia directa: Define los arquetipos como "formas o imágenes de naturaleza colectiva que se producen en prácticamente toda la tierra como componentes de los mitos y al mismo tiempo como productos autóctonos individuales de origen inconsciente." Esta es la base de todo el vector arquetípico del agente.

> Cita clave: *"The collective unconscious is not a personal acquisition but is inborn."* — Justifica la Capa A (inconsciente colectivo base) que prefijamos en todos los agentes independientemente de su historia.

> Implementación: `core/agents/psyche/archetypes.py` — los 12 arquetipos como vector dimensional, no como tipos discretos.

---

**Jung, C. G. (1960). *The Structure and Dynamics of the Psyche.***
*Collected Works, Vol. 8. Princeton University Press.*

> Relevancia directa: Introduce el concepto de "energía psíquica" y su dinámica — cómo los complejos acumulan y liberan energía. Base del sistema de complejos activables por umbral.

> Cita clave: *"A complex is the image of a certain psychic situation which is strongly accentuated emotionally."* — Justifica que el complejo no es un rasgo estático sino una carga activable por contexto.

> Implementación: `core/agents/psyche/complexes.py` — `complex_weight` (crónico) vs `complex_activated` (agudo).

---

**Jung, C. G. (1956). *Symbols of Transformation.***
*Collected Works, Vol. 5. Princeton University Press.*

> Relevancia directa: El análisis de cómo los símbolos emergen del inconsciente y se transforman. Base del sistema de cristalización simbólica y el campo colectivo.

> Cita clave: *"The symbol is not a sign that disguises something generally known, but an expression for something that cannot be characterized in any other or better way."* — Justifica que el símbolo en el campo colectivo no es una etiqueta sino una entidad funcional con vida propia.

> Implementación: `core/social/collective_field.py` — los símbolos como unidades con carga, contagio y umbral de cristalización.

---

**Jung, C. G. (1963). *Mysterium Coniunctionis.***
*Collected Works, Vol. 14. Princeton University Press.*

> Relevancia directa: La alquimia como sistema simbólico y el proceso de individuación en su forma más completa. Base del motor de individuación dinámica.

> Cita clave: *"The goal of the individuation process is the synthesis of the self."* — Define qué significa que un agente "evolucione" psicológicamente: la integración progresiva de la Sombra hacia el Self.

> Implementación: `core/agents/psyche/individuation.py` — el arco de vida del agente como proceso, no como acumulación de stats.

---

**Jung, C. G. (1958). *Psychology and Religion: West and East.***
*Collected Works, Vol. 11. Princeton University Press.*

> Relevancia directa: Cómo el inconsciente colectivo produce experiencias religiosas y mitológicas. Base del sistema de proto-mitos y rituales emergentes.

> Cita clave: *"Religion is a careful and scrupulous observation of what Rudolf Otto aptly termed the numinosum."* — Justifica que la religión emerge de la experiencia numinosa, no de la teoría. En la simulación: la cueva, el fuego, la primera muerte son experiencias numinosas antes de ser mitos.

> Implementación: `core/social/mythology.py` — los mitos cristalizan de experiencias compartidas, no se declaran.

---

**Jung, C. G. (1921). *Psychological Types.***
*Collected Works, Vol. 6. Princeton University Press.*

> Relevancia directa: El sistema de tipos psicológicos que informa el modelo de rasgos dimensionales. No usamos MBTI (su derivado comercial) sino las funciones psicológicas originales.

> Cita clave: *"Every individual is an exception to the rule."* — Justifica la varianza individual sobre distribuciones: ningún agente es puro tipo, todos son combinaciones únicas.

> Implementación: `core/agents/psyche/traits.py` — rasgos como distribuciones continuas, no categorías.

---

**Jung, C. G. & Kerényi, K. (1949). *Essays on a Science of Mythology.***
*Princeton University Press.*

> Relevancia directa: El análisis del mito del niño divino y la doncella como arquetipos universales con manifestaciones culturales específicas. Base de la distinción Capa A / Capa B.

> Cita clave: *"The myth is the revelation of a divine life in man. It is not we who invent myth, rather it speaks to us as a Word of God."* — Fundamenta que los arquetipos son estructuras a priori, no construcciones culturales.

> Implementación: La distinción entre arquetipos prefijados (Capa A) y contenidos culturales emergentes (Capa B).

---

**Von Franz, M.-L. (1980). *Projection and Re-Collection in Jungian Psychology.***
*Open Court Publishing.*

> Relevancia directa: El mecanismo de proyección de la Sombra como fenómeno social — cómo el individuo proyecta sus contenidos inconscientes en otros. Base del sistema de chivo expiatorio emergente.

> Cita clave: *"Projection is a process by which a subjective content becomes alienated from the subject and is, so to speak, transferred to the object."* — Justifica técnicamente el mecanismo `shadow_projection` en las interacciones.

> Implementación: `core/social/interaction.py` — las interacciones negativas pueden ser proyecciones de la Sombra, no solo conflictos racionales.

---

## II. FILOSOFÍA — EL MARCO ONTOLÓGICO

### Heidegger

---

**Heidegger, M. (1927). *Sein und Zeit* [Being and Time].**
*Max Niemeyer Verlag. (Trad. Macquarrie & Robinson, Harper & Row, 1962.)*

> Relevancia directa: El concepto de *Dasein* — el ser-en-el-mundo — como modo de existencia que no puede separarse de su contexto. Fundamenta filosóficamente por qué los agentes no pueden modelarse como entidades abstractas: son constitutivamente su relación con el mundo.

> Cita clave: *"Dasein is an entity which does not just occur among other entities. Rather it is ontically distinguished by the fact that, in its very Being, that Being is an issue for it."* — El agente no solo existe en el mundo; su existencia es siempre una pregunta abierta sobre sí mismo. Eso es la individuación.

> Implementación: Los agentes no tienen un estado "objetivo" — tienen un estado siempre situado en un contexto (zona, hora, clima, vínculos). El `WorldSnapshot` no es el mundo: es el mundo-tal-como-aparece-para-el-agente.

---

**Heidegger, M. (1954). *Vorträge und Aufsätze* [Essays and Conferences].**
*(Trad. parcial: "The Question Concerning Technology", Harper & Row, 1977.)*

> Relevancia directa: La tecnología no como conjunto de herramientas sino como modo de revelar el mundo. Fundamenta el sistema de descubrimiento tecnológico: la tecnología no "desbloquea" capacidades, revela posibilidades que ya existían.

> Cita clave: *"Technology is a way of revealing."* — El fuego no crea calor: revela el calor que ya existía en la madera. El ocre no crea color: revela el potencial simbólico del pigmento.

> Implementación: `core/social/technology.py` — los recursos ocultos existen desde el día 0; la tecnología es el acto de revelarlos.

---

**Heidegger, M. (1950). *Der Ursprung des Kunstwerkes* [The Origin of the Work of Art].**
*(En: *Holzwege*. Vittorio Klostermann.)*

> Relevancia directa: El arte como modo de apertura del mundo — cómo una obra establece un mundo y lo hace visible. Fundamenta el rol del arte y el ritual en la simulación: el primer pigmento en la pared de la cueva no decora, funda un mundo.

> Cita clave: *"The work opens up a world and keeps it abidingly in force."* — El primer ritual del grupo no es un comportamiento repetido: es la fundación de un mundo compartido.

> Implementación: `mythology_log` — los mitos y rituales no se registran como eventos sino como entidades que abren posibilidades nuevas para el grupo.

---

### Otros filósofos relevantes

---

**Merleau-Ponty, M. (1945). *Phénoménologie de la Perception.***
*Gallimard. (Trad. Landes, Routledge, 2013.)*

> Relevancia directa: El cuerpo como esquema que orienta la percepción y la acción en el mundo. Fundamenta que las necesidades biológicas (hambre, fatiga, sed) no son interrupciones del proceso psicológico — son el sustrato desde el cual toda percepción ocurre.

> Cita clave: *"The body is our general medium for having a world."* — El agente hambriento no percibe el mundo como el agente satisfecho. Las necesidades modifican la percepción antes de modificar la decisión.

> Implementación: `survival_risk` y `mood_modifier` en `WorldSnapshot` — el clima y las necesidades modifican cómo el agente "lee" el mundo, no solo qué decide hacer.

---

**Cassirer, E. (1944). *An Essay on Man.***
*Yale University Press.*

> Relevancia directa: El ser humano como *animal symbolicum* — el símbolo como la forma fundamental de la experiencia humana, anterior al lenguaje y a la razón. Fundamenta que el sistema simbólico del campo colectivo no es un añadido cultural sino la condición de posibilidad de la cultura.

> Cita clave: *"Man cannot live in a world of hard facts or according to his immediate needs and desires. He lives rather in the midst of imaginary emotions, in hopes and fears, in illusions and disillusions."* — Los agentes no solo tienen necesidades: tienen símbolos que median entre la necesidad y la acción.

> Implementación: El campo colectivo (`collective_field`) como capa mediadora entre el mundo físico y la decisión del agente.

---

**Durkheim, É. (1912). *Les Formes Élémentaires de la Vie Religieuse.***
*Alcan. (Trad. Fields, Free Press, 1995.)*

> Relevancia directa: El origen social de las categorías religiosas y morales. La religión como sistema de representaciones colectivas que trascienden al individuo. Fundamenta que el campo colectivo tiene efectos causales reales sobre los individuos.

> Cita clave: *"Religious force is only the sentiment inspired by the group in its members, but projected outside of the minds that experience them."* — El inconsciente colectivo no es metáfora: tiene efectos causales documentables. En la simulación: el campo colectivo modifica probabilidades de conducta.

> Implementación: `collective_field.radiate()` — el campo retroalimenta a los agentes con modificadores concretos.

---

## III. PSICOLOGÍA Y NEUROCIENCIA — VALIDACIÓN EMPÍRICA

### Psicología evolutiva y cognitiva

---

**Buss, D. M. (1999). *Evolutionary Psychology: The New Science of the Mind.***
*Allyn & Bacon.*

> Relevancia directa: La psicología evolutiva como marco para las preferencias y sesgos que son universales (Capa A). El tabú del incesto, la jerarquía de dominancia, el cuidado de la cría como conductas con base evolutiva.

> Cita clave: *"Psychological mechanisms are adaptations, crafted by natural selection over evolutionary time."* — Los módulos neurales de la simulación (amenaza, recompensa, apego) no son arbitrarios: corresponden a sistemas adaptivos documentados.

> Implementación: `core/agents/psyche/neural.py` — los módulos neurales como sistemas adaptivos, no como variables genéricas.

---

**Westermarck, E. (1891). *The History of Human Marriage.***
*Macmillan.*

> Relevancia directa: La descripción original del efecto Westermarck — la aversión sexual entre individuos que convivieron en la infancia temprana. Base empírica del tabú del incesto en la simulación.

> Cita clave: La evidencia del kibbutz israelí (Shepher, 1983) confirmó que de 2769 matrimonios examinados, ninguno ocurrió entre personas que habían sido criadas juntas en la infancia.

> Implementación: `core/agents/psyche/archetypes.py` — `westermarck_suppression` como función de años de convivencia temprana.

---

**Bowlby, J. (1969). *Attachment and Loss, Vol. 1: Attachment.***
*Basic Books.*

> Relevancia directa: La teoría del apego como sistema motivacional primario. Base del módulo neural de apego y de cómo los vínculos tempranos moldean la psique del agente.

> Cita clave: *"The propensity to make strong emotional bonds to particular individuals is a basic component of human nature."* — Los vínculos no son opcionales en la simulación: son necesidades psicológicas que generan stress si no se satisfacen.

> Implementación: `sociabilidad_necesaria` como variable de necesidad, junto a hambre y fatiga.

---

**Kahneman, D. (2011). *Thinking, Fast and Slow.***
*Farrar, Straus and Giroux.*

> Relevancia directa: Los dos sistemas de pensamiento — Sistema 1 (rápido, automático, emocional) y Sistema 2 (lento, deliberado, racional). Base de la distinción entre respuestas arquetípicas automáticas y decisiones deliberadas.

> Cita clave: *"The situation has to be assessed before the appropriate response can be selected."* — El agente no siempre delibera: la mayoría de sus acciones son respuestas automáticas de Sistema 1 moduladas por los arquetipos activos.

> Implementación: El override de supervivencia y los complejos activados funcionan como Sistema 1 — suspenden la deliberación.

---

**Barrett, L. F. (2017). *How Emotions Are Made: The Secret Life of the Brain.***
*Houghton Mifflin Harcourt.*

> Relevancia directa: Las emociones no son categorías universales hardwired sino construcciones del cerebro basadas en predicción y contexto. Matiza y enriquece el modelo emocional de los agentes.

> Cita clave: *"Your brain is not reacting to the world. It is predicting the world."* — El agente no responde al clima: predice su significado basándose en historia previa. Un agente que sobrevivió una tormenta lee la lluvia distinto a uno que no.

> Implementación: La memoria episódica modula cómo el agente interpreta los modificadores del `WorldSnapshot`.

---

### Neurociencia computacional

---

**Friston, K. (2010). "The Free-Energy Principle: A Unified Brain Theory?"**
*Nature Reviews Neuroscience, 11, 127–138.*

> Relevancia directa: El principio de energía libre como marco unificado para entender la percepción, la acción y el aprendizaje. Los agentes minimizan su sorpresa sobre el mundo — actúan para que el mundo confirme sus predicciones.

> Cita clave: *"Biological agents resist the second law of thermodynamics by acting on the world to reduce the surprise of their sensory states."* — Los rituales, los tabúes y los mitos son mecanismos para reducir la incertidumbre existencial — formas de minimizar la energía libre colectiva.

> Implementación: El campo colectivo como mecanismo de reducción de incertidumbre grupal — los mitos funcionan porque hacen el mundo predecible.

---

**Deacon, T. W. (1997). *The Symbolic Species: The Co-Evolution of Language and the Brain.***
*W. W. Norton.*

> Relevancia directa: La co-evolución del símbolo y el cerebro humano. Los símbolos no son representaciones — son relaciones de ausencia que reorganizan la cognición. Base del sistema simbólico del campo colectivo.

> Cita clave: *"We are symbolic creatures... We inhabit a world of absences."* — El campo colectivo es un mundo de ausencias presentes: el muerto que moldea al vivo, el tabú que define lo permitido por su negación.

> Implementación: `symbol_propagation_log` — los símbolos viajan por el grupo como relaciones, no como objetos.

---

**Damasio, A. (1994). *Descartes' Error: Emotion, Reason, and the Human Brain.***
*Putnam.*

> Relevancia directa: La hipótesis del marcador somático — las emociones como señales que guían la toma de decisiones. Base de por qué el estado emocional del agente modifica sus probabilidades conductuales antes de cualquier deliberación.

> Cita clave: *"Feelings are the sensors for the match or lack thereof between nature and circumstance."* — El humor del agente no es un output estético: es una señal funcional que modifica el colapso cuántico.

> Implementación: `humor_base` como input al vector de probabilidades del estado cuántico, no como variable independiente.

---

## IV. SISTEMAS COMPLEJOS Y EMERGENCIA

---

**Holland, J. H. (1998). *Emergence: From Chaos to Order.***
*Addison-Wesley.*

> Relevancia directa: La emergencia como propiedad de sistemas complejos donde el todo tiene propiedades que no están en las partes. Base teórica de por qué el inconsciente colectivo puede ser genuinamente emergente.

> Cita clave: *"Emergent phenomena in complex adaptive systems arise from the interactions between components."* — El campo colectivo no está programado: emerge de las interacciones de los agentes. Esto no es una metáfora — es una propiedad técnica del sistema.

> Implementación: `collective_field.py` — el campo no se inicializa con valores: comienza vacío y se llena de interacciones.

---

**Kauffman, S. (1993). *The Origins of Order: Self-Organization and Selection in Evolution.***
*Oxford University Press.*

> Relevancia directa: La auto-organización como proceso que genera estructura sin diseño. Los sistemas en el "borde del caos" — ni demasiado ordenados ni demasiado caóticos — son los más creativos.

> Cita clave: *"Life exists at the edge of chaos."* — El grupo arcaico en la simulación debería operar en ese borde: suficiente orden para sobrevivir, suficiente caos para innovar.

> Implementación: Los parámetros de beta están calibrados para que el grupo no sea ni perfectamente estable ni inmediatamente caótico.

---

**Axelrod, R. (1984). *The Evolution of Cooperation.***
*Basic Books.*

> Relevancia directa: Cómo la cooperación emerge entre agentes egoístas sin autoridad central. El tit-for-tat como estrategia evolutivamente estable. Base del sistema de reciprocidad arcaica.

> Cita clave: *"Under suitable conditions, cooperation can indeed emerge in a world of egoists without central authority."* — La cooperación del grupo arcaico no necesita ser programada: emerge del tracking de reciprocidad si los parámetros son correctos.

> Implementación: `core/agents/psyche/complexes.py` — el complejo de traición como respuesta al breaking de reciprocidad.

---

**Nowak, M. A. & Highfield, R. (2011). *SuperCooperators.***
*Free Press.*

> Relevancia directa: Los cinco mecanismos de evolución de la cooperación: selección de parientes, reciprocidad directa e indirecta, reciprocidad de red, selección de grupo. Todos relevantes para el grupo arcaico.

> Cita clave: *"Cooperation is the architect of creativity throughout evolution."* — La cooperación no es un valor moral en la simulación: es una estrategia que emerge cuando las condiciones la favorecen.

> Implementación: Los vínculos familiares (bond automático) vs. vínculos de reciprocidad (bond construido) como dos mecanismos distintos de cooperación.

---

## V. SIMULACIÓN DE AGENTES — TÉCNICO

---

**Epstein, J. M. & Axtell, R. (1996). *Growing Artificial Societies.***
*Brookings Institution Press / MIT Press.*

> Relevancia directa: El libro fundacional del modelado basado en agentes (ABM) como metodología científica. Define cómo "hacer crecer" fenómenos sociales de abajo hacia arriba.

> Cita clave: *"If you didn't grow it, you didn't explain it."* — El inconsciente colectivo de la simulación solo es válido si emerge de las interacciones individuales. Si lo prefijamos, no lo explicamos.

> Implementación: La arquitectura completa del proyecto — ABM como metodología, no como herramienta.

---

**Wilensky, U. & Rand, W. (2015). *An Introduction to Agent-Based Modeling.***
*MIT Press.*

> Relevancia directa: Manual técnico de ABM con foco en NetLogo/Mesa. Patrones de diseño, validación de modelos, análisis de sensibilidad.

> Relevancia técnica: Cómo calibrar parámetros, cómo validar que el modelo hace lo que creés que hace, cómo distinguir emergencia de artifacts del código.

> Implementación: Metodología de testing y validación del motor de simulación.

---

**Tesfatsion, L. & Judd, K. L. (Eds.) (2006). *Handbook of Computational Economics, Vol. 2: Agent-Based Computational Economics.***
*North-Holland.*

> Relevancia directa: Economía computacional basada en agentes — cómo modelar sistemas económicos emergentes sin asumir equilibrio. Base del sistema económico arcaico.

> Implementación: El sistema de reciprocidad directa como economía sin precio ni equilibrio — los precios emergen si el sistema los produce.

---

**Bonabeau, E. (2002). "Agent-Based Modeling: Methods and Techniques for Simulating Human Systems."**
*Proceedings of the National Academy of Sciences, 99(suppl 3), 7280–7287.*

> Relevancia directa: Cuándo usar ABM vs. otras metodologías. Validación y limitaciones del enfoque.

> Cita clave: *"ABM captures emergent phenomena, provides a natural description of a system, and is flexible."* — Justifica por qué ABM y no ecuaciones diferenciales para modelar el inconsciente colectivo.

---

### Mecánica Cuántica Aplicada a Sistemas Sociales

---

**Busemeyer, J. R. & Bruza, P. D. (2012). *Quantum Models of Cognition and Decision.***
*Cambridge University Press.*

> Relevancia directa: El uso de modelos cuánticos para capturar paradojas de la cognición humana que los modelos clásicos no pueden explicar — interferencia, superposición de creencias, efectos de orden.

> Cita clave: *"Quantum probability theory provides a completely new way to think about human judgment and decision making."* — Justifica técnicamente el sistema de superposición conductual y el colapso por interacción.

> Implementación: `core/agents/quantum/superposition.py` — la formalización matemática del estado conductual como vector de amplitudes complejas.

---

**Khrennikov, A. (2010). *Ubiquitous Quantum Structure: From Psychology to Finance.***
*Springer.*

> Relevancia directa: Aplicaciones de la formalización cuántica a sistemas no-físicos — psicología, economía, lingüística. Sin física cuántica literal, sino matemática cuántica aplicada a incertidumbre y correlación.

> Implementación: El entrelazamiento social como correlación no-clásica entre estados de agentes vinculados.

---

**Pothos, E. M. & Busemeyer, J. R. (2013). "Can Quantum Probability Provide a New Direction for Cognitive Modeling?"**
*Behavioral and Brain Sciences, 36(3), 255–274.*

> Relevancia directa: Revisión crítica de cuándo y por qué los modelos cuánticos superan a los clásicos en cognición. Fundamental para justificar la mecánica cuántica de socialización.

---

## VI. ANTROPOLOGÍA Y ARQUEOLOGÍA — EL ESTADO ARCAICO

---

**Diamond, J. (1997). *Guns, Germs, and Steel.***
*W. W. Norton.*

> Relevancia directa: Cómo el entorno geográfico y los recursos disponibles moldean el desarrollo cultural. Justifica que el mapa (Núcleo 1) es tan determinante como la psicología (Núcleo 2).

> Cita clave: *"History followed different courses for different peoples because of differences among peoples' environments, not because of biological differences among peoples themselves."* — La geografía de la simulación no es decorado: es una variable causal del desarrollo cultural.

> Implementación: El diseño de la grilla hexagonal con biomas que tienen carrying capacity real.

---

**Dunbar, R. (1996). *Grooming, Gossip, and the Evolution of Language.***
*Harvard University Press.*

> Relevancia directa: El número de Dunbar — el límite cognitivo del tamaño del grupo social gestionable. Para grupos de cazadores-recolectores: 25–50 personas para el grupo funcional, 150 para el grupo cognitivo.

> Cita clave: *"The figure of 150 seems to represent the maximum number of individuals with whom we can have a genuinely social relationship."* — Justifica el tamaño inicial de 15 agentes y el diseño para 100–1000.

> Implementación: El grupo beta de 15 agentes como unidad de supervivencia, no como número arbitrario.

---

**Mithen, S. (1996). *The Prehistory of the Mind.***
*Thames and Hudson.*

> Relevancia directa: Cómo la mente humana primitiva combinó inteligencias modulares separadas para producir pensamiento simbólico. El origen cognitivo de los mitos y el arte.

> Cita clave: *"The appearance of fully modern humans... involved a critical change in the architecture of the mind."* — El momento en que los módulos cognitivos separados empezaron a comunicarse es el origen del símbolo. En la simulación: el primer proto-símbolo es ese momento.

> Implementación: Los módulos neurales (`amenaza`, `recompensa`, `apego`, `exploración`) como sistemas que pueden actuar juntos (símbolo) o por separado (instinto).

---

**Cauvin, J. (1994). *Naissance des Divinités, Naissance de l'Agriculture.***
*CNRS Éditions. (Trad. Watkins, Cambridge University Press, 2000.)*

> Relevancia directa: La revolución simbólica precede a la revolución neolítica — los humanos primero cambiaron su relación simbólica con el mundo y luego cambiaron su tecnología. El símbolo precede a la herramienta.

> Cita clave: *"The revolution in symbols preceded the Neolithic revolution."* — Justifica el sistema de tecnología simbólica (ocre, ritual, mito) como anterior y más fundamental que la tecnología material.

> Implementación: `NIVEL_SIMBOLICO` en el árbol tecnológico — puede ocurrir antes que `NIVEL_1` material.

---

**Clottes, J. & Lewis-Williams, D. (1996). *The Shamans of Prehistory.***
*Harry N. Abrams.*

> Relevancia directa: El análisis del arte rupestre paleolítico como evidencia de estados alterados de conciencia y experiencia numinosa en la cueva. Base del valor simbólico de las cuevas en el mapa.

> Cita clave: *"The caves themselves were considered to be alive, perhaps portals to the spirit world."* — Justifica que la cueva en el mapa tiene el valor simbólico más alto: es el primer espacio sagrado universalmente documentado.

> Implementación: `cueva_sistema` en el mapa con `valor_simbolico: 0.95` y el recurso oculto `espacio_ritual`.

---

## VII. REFERENCIAS TÉCNICAS DE IMPLEMENTACIÓN

---

**Mesa Framework**
Kazil, J., Masad, D., & Crooks, A. (2020).
"Utilizing Python for Agent-Based Modeling: The Mesa Framework."
*Social, Cultural, and Behavioral Modeling. SBP-BRiMS 2020.*
https://github.com/projectmesa/mesa

---

**NetworkX**
Hagberg, A., Swart, P., & Schult, D. (2008).
"Exploring Network Structure, Dynamics, and Function using NetworkX."
*Proceedings of the 7th Python in Science Conference.*

---

**NumPy / SciPy**
Harris, C. R., et al. (2020). "Array programming with NumPy."
*Nature, 585, 357–362.*

---

**SQLite**
Hipp, R. D. (2000–present). SQLite.
https://www.sqlite.org
*"SQLite is a C-language library that implements a small, fast, self-contained, high-reliability, full-featured, SQL database engine."*

---

**Hexagonal Grid Theory**
Patel, A. (2013). "Hexagonal Grids."
*Red Blob Games.*
https://www.redblobgames.com/grids/hexagons/
*La referencia técnica estándar para implementación de grillas hexagonales con coordenadas axiales.*

---

## VIII. LECTURAS COMPLEMENTARIAS RECOMENDADAS

*(No usadas directamente pero forman el contexto intelectual)*

- Campbell, J. (1949). *The Hero with a Thousand Faces.* — El monomito como estructura arquetípica universal.
- Eliade, M. (1957). *The Sacred and the Profane.* — Lo sagrado como categoría de experiencia humana.
- Lévi-Strauss, C. (1962). *La Pensée Sauvage.* — El pensamiento mítico como lógica, no como pre-lógica.
- Prigogine, I. (1980). *From Being to Becoming.* — La termodinámica del no-equilibrio y la emergencia de orden.
- Wolfram, S. (2002). *A New Kind of Science.* — Los autómatas celulares y la emergencia de complejidad.
- Watts, D. J. (2003). *Six Degrees.* — La estructura de las redes sociales y la propagación de información.
- Girard, R. (1972). *La Violence et le Sacré.* — El mecanismo del chivo expiatorio como origen de lo sagrado.
- Rappaport, R. A. (1999). *Ritual and Religion in the Making of Humanity.* — El ritual como sistema adaptivo.

---

## IX. NOTA EPISTEMOLÓGICA FINAL

Este proyecto no es psicología computacional en sentido estricto.
No es simulación social convencional.
No es física cuántica aplicada.

Es la intersección de todas estas disciplinas alrededor de una pregunta
que ninguna de ellas puede responder sola:

> **¿Puede una sociedad artificial desarrollar un inconsciente colectivo genuinamente emergente si sus agentes tienen la arquitectura psíquica correcta?**

La bibliografía no responde esa pregunta.
La proporciona el terreno desde el cual la pregunta puede hacerse con rigor.

La respuesta la da la simulación.

---

*Psyche Simulacra — Bibliografía v1.0*  
*"Standing on the shoulders of giants to look at algo que ellos no pudieron ver."*
