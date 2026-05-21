# 🚀 Roadmap de Desarrollo: PSYCHE SIMULACRA

Este documento establece las directrices arquitectónicas y los objetivos a implementar en futuras iteraciones del proyecto, asegurando la evolución del sistema desde un simulador de supervivencia individual hacia un **motor generativo de sociología e inconsciente colectivo**.

---

## 🧬 Fase 1: Evolución Biológica (Ciclo de Vida y Herencia)

**Objetivo:** Permitir simulaciones transgeneracionales donde los agentes no sean inmortales y el peso psicológico se herede.

### Tareas de Código:
- [ ] **Mortalidad por Edad:** Implementar una curva de declive de `energia` máxima y aumento de `fatiga` base a medida que avanza la `edad` en `AgentCore`. Añadir una probabilidad de muerte por senectud tras superar cierta edad límite.
- [ ] **Sistema de Reproducción:** 
  - Crear una nueva `WorldAction` de tipo `REPRODUCIRSE`.
  - Condicionar la acción a umbrales de entrelazamiento positivo (ej. `vínculo > 0.8`) y niveles altos de saciedad.
  - Implementar la función `_generate_offspring(parent_a, parent_b)` que instancie un nuevo agente.
- [ ] **Herencia Genética y Psíquica:**
  - El recién nacido debe heredar un promedio ponderado de los tensores de `arquetipos` base de sus progenitores.
  - Heredar predisposiciones de `complejos` (ej. si ambos padres tienen el *Complejo de Abandono* activo, el hijo nace con un nivel base de `0.5`).

---

## 🏕️ Fase 2: Formación de Tribus y Mitología Geográfica

**Objetivo:** Transicionar el Inconsciente Colectivo de una entidad global a múltiples entes locales que compiten, formando culturas y subculturas.

### Tareas de Código:
- [ ] **Clustering de Agentes:** Extender `SocialNetwork` para detectar clanes/tribus de forma dinámica usando algoritmos de clustering (ej. detección de comunidades en grafos con `networkx`).
- [ ] **Inconsciente Colectivo Local (ICL):**
  - Modificar `collective_unconscious.py` para instanciar objetos `LocalUnconscious` vinculados a coordenadas geográficas (epicentros tribales).
  - Hacer que los sueños y arquetipos de un agente sean influenciados predominantemente por el ICL de la tribu a la que pertenece físicamente en lugar del global.
- [ ] **Divergencia Cultural:** Implementar un loop donde las condiciones extremas del entorno (biomas hostiles vs. amigables) polaricen los arquetipos de las distintas tribus a lo largo del tiempo.

---

## 🗣️ Fase 3: Síntesis Narrativa (Integración de LLMs)

**Objetivo:** Darle una voz literaria a la simulación traduciendo los vectores matemáticos puros en textos comprensibles y relatos míticos.

### Tareas de Código:
- [ ] **Cliente LLM:** Integrar un módulo en `core/utils/` (usando librerías como `openai`, `google-genai` o `langchain`) para invocar a un LLM externo.
- [ ] **Prompt Engineering Dinámico:** 
  - Crear una rutina periódica (ej. cada 100 días simulados o mediante un `Observer`) que tome un resumen JSON del estado de una tribu (líderes, muertes, arquetipo dominante, complejos activos).
  - Solicitar al LLM que genere un "Mito Fundacional", una "Profecía" o un "Cuento Folklórico" representativo de la época.
- [ ] **Bóveda de Leyendas:** Escribir estos mitos generados directamente en la bóveda de Obsidian bajo `vault/Colectivo/Leyendas/`, expandiendo la mitología de la simulación.

---

## 🏛️ Fase 4: Cultura Material (Alteración Permanente del Entorno)

**Objetivo:** Permitir que los estados psicológicos influyan permanentemente en la geografía del `TerrainGrid`.

### Tareas de Código:
- [ ] **Estructuras Avanzadas:** Ampliar las capacidades de construcción (`TerrainGrid.add_structure`) para incluir "Tótems", "Altares", o "Murallas".
- [ ] **Construcción Motivada por Complejos:** 
  - Condicionar la construcción de ciertas estructuras a estados psicológicos (ej. una tribu dominada por el complejo de "Inferioridad" o "Abandono" construirá murallas defensivas; una tribu dominada por "Self" o "Trascendencia" construirá altares).
- [ ] **Radiación Psicológica (Auras):** 
  - Implementar que las estructuras emitan un "aura" modificadora que altere los ritmos de decaimiento de `ansiedad` o `humor` de los agentes que transiten o vivan en esos hexágonos.

---

## 🔬 Fase 5: Validación Científica de la Emergencia (Rigor Cuantitativo)

**Objetivo:** Transformar la simulación de un experimento anecdótico a un modelo científico validable (Generative Social Science). Demostrar que los "mitos" son verdaderas propiedades emergentes medibles matemáticamente y no meros artefactos de programación.

### Tareas de Código:
- [ ] **Operacionalización de Fenómenos (MythologyEngine):**
  - Definir patrones numéricos estrictos para la consolidación de un "mito".
  - Ejemplo: Un mito de *Héroe vs Monstruo* solo cristaliza si la "carga heroica" (centralidad de un agente + éxito en conflictos) supera un umbral `X`, y la "carga de amenaza" en el `CollectiveField` supera un umbral `Y` simultáneamente.
- [ ] **Métricas Cuantitativas de Emergencia:**
  - Implementar cálculos de **Mean Information Gain (MIG)** o **Energía Libre Variacional** sobre el estado del `CollectiveField`.
  - Crear un tracker temporal para identificar cuándo el campo simbólico pasa de ruido blanco (caos) a un estado sincronizado, demostrando matemáticamente la cristalización de una creencia cultural.
- [ ] **Suite de Análisis de Sensibilidad (Robustez):**
  - Desarrollar un nuevo módulo de testing riguroso: `tests/test_emergence_robustness.py`.
  - Automatizar la ejecución de 50 o 100 simulaciones variando levemente las semillas iniciales (`--seed`) y alterando en un ~5% los perfiles de `initial_personas.yaml` o la distribución espacial de recursos.
  - Generar reportes estadísticos que prueben que la emergencia del Inconsciente Colectivo ocurre bajo diversas condiciones y no depende de un *hardcode* o configuración única.
