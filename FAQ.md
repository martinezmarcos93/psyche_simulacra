# FAQ — PSYCHE SIMULACRA

Respuestas a las preguntas más frecuentes sobre el proyecto.

---

## ¿Qué es / para qué sirve?

### 1. ¿Qué es PSYCHE SIMULACRA y cuál es su objetivo?

PSYCHE SIMULACRA es un laboratorio computacional de emergencia cultural. Es un sistema ABM (Agent-Based Model) donde 100 individuos psicológicamente complejos interactúan en un mundo físico simulado y, sin que ningún comportamiento colectivo esté programado directamente, generan espontáneamente tribus, jerarquías, tabúes, mitos, estructuras culturales y leyendas.

El objetivo central es estudiar cómo el inconsciente colectivo —en el sentido jungiano— *emerge* de la interacción entre individuos con psicologías distintas, en lugar de ser construido desde arriba. El experimento busca responder preguntas como: ¿cuándo aparece el primer mito?, ¿el héroe emerge del poder o de la narrativa?, ¿la cooperación o la jerarquía aparece primero?

---

### 2. ¿Es una simulación científica, un juego, o algo intermedio?

Es una simulación científica con estética narrativa. No es un juego: el usuario no controla agentes ni toma decisiones en tiempo real. Es un experimento computacional que produce datos medibles (KL divergencia, MIG, IMI, VFE) y al mismo tiempo genera narrativa legible en lenguaje natural a través de un LLM local.

Se puede pensar como un microscopio: el mundo simulado es el preparado biológico, las métricas son las lecturas del instrumento, y la narrativa es la descripción en prosa de lo que se observa.

---

### 3. ¿Qué tiene de "junguiano"? ¿Qué aporta Jung a un ABM?

Jung aporta la arquitectura psicológica interna de cada agente. Cada individuo carga un `ArchetypeVector` con 12 pesos independientes (self, persona, sombra, anima/animus, héroe, sabio, trickster, madre, padre, niño divino, gobernante, rebelde), un `ComplexProfile` con 6 complejos activables por umbral (inferioridad, abandono, poder, culpa, materno, trascendencia), y genera sueños con contenido simbólico.

Lo junguiano no es cosmético. El arquetipo dominante de un agente modula cómo colapsa su estado de decisión, qué símbolos emite al campo colectivo, con quién forma vínculos, y qué tipo de mito tiende a protagonizar. La divergencia arquetípica entre tribus es la variable principal de medición científica.

---

## ¿Cómo funciona?

### 4. ¿Cómo decide qué hacer cada día un agente?

A través de una mecánica de colapso cuántico. Cada agente mantiene un vector de superposición conductual (`BehavioralSuperposition`) con probabilidades para cooperar, competir, aislarse o manipular. En cada tick, el `CollapseEngine` colapsa ese vector en una acción concreta, modulado por cuatro factores simultáneos:

1. Su arquetipo dominante actual (un gobernante tenderá a competir/manipular; una madre a cooperar)
2. Sus complejos activos (el complejo de poder amplifica la competencia)
3. El estado del campo colectivo local (si hay alta `emotional_pressure`, aumenta la agresividad)
4. El entrelazamiento social con otros agentes (los pares con `bond_strength` alto comparten sesgos de colapso)

Las necesidades biológicas (hambre, sed, fatiga) actúan como restricciones previas al colapso: un agente con sed crítica ignora la lógica arquetípica y busca agua.

---

### 5. ¿Cómo se forman las tribus? ¿Tiene algo predeterminado o emerge solo?

Emerge solo. Cada 30 días, el `TribeManager` aplica el algoritmo `greedy_modularity_communities` de NetworkX sobre el grafo social. Las comunidades que detecta se convierten en tribus si tienen suficiente cohesión interna. No hay un número de tribus prefijado ni líderes asignados por el sistema.

Una vez formada, una tribu desarrolla su propio inconsciente colectivo local (ICL), su propio `MythologyEngine`, y experimenta una deriva arquetípica lenta hacia los arquetipos asociados al bioma que habita (0.001/día). Esa deriva, compuesta a lo largo de cientos de días, es lo que produce divergencia cultural medible entre grupos.

---

### 6. ¿Qué son los sueños y para qué sirven mecánicamente?

Los sueños son el mecanismo de procesamiento psicológico nocturno. Al final de cada día, el `DreamGrammarEngine` genera un sueño único para cada agente combinando 5 capas ponderadas: bioma habitado (peso 1.0), arquetipo dominante (2.5), complejo activo (4.0), traumas recientes de la memoria episódica (5.0), y símbolo de resonancia grupal si el agente está entrelazado con otro (6.0).

El sueño produce un `delta_arquetipo` concreto: modifica ligeramente los pesos del vector jungiano del agente según el contenido del sueño. Es el principal mecanismo de plasticidad psicológica individual a largo plazo.

Los **sueños compartidos** ocurren cuando dos agentes tienen `bond_strength > 0.65`, pertenecen a la misma tribu con `bond > 0.35`, o están marcados como `entangled=True`. El agente con mayor tensión arquetípica emite un símbolo resonante que el otro recibe con peso máximo (6.0), haciendo que sus psicologías converjan gradualmente.

---

### 7. ¿Qué es el Campo Colectivo y cómo afecta a los agentes individuales?

El `CollectiveField` es el inconsciente colectivo del grupo. Mantiene contadores para los 12 símbolos jungianos, más tres métricas de presión: `emotional_pressure` (carga emocional acumulada sin procesar), `myth_pressure` (trauma colectivo sin narrativa que lo contenga), y `confusion` epistémica (incertidumbre sobre la identidad del grupo).

Afecta a los agentes de tres formas:
- **Directa:** el `CollapseEngine` lee el símbolo dominante del campo para sesgar el colapso conductual.
- **Estructural:** cuando `myth_pressure` supera umbrales, el `ContextoEnunciativo` (temperatura × intencionalidad + ruido) favorece la cristalización de un proto-mito.
- **Material:** los arquetipos dominantes del campo determinan qué estructuras físicas construye la tribu (tótem, altar, muralla, hoguera).

Cada tribu tiene además su propio ICL local, independiente del campo global.

---

### 8. ¿Cómo funciona la generación de mitos? ¿Los escribe la IA o los construye el motor?

El motor detecta cuándo cristaliza un mito; la IA lo narra. Son dos pasos separados.

**Detección (motor Python):** `MythologyEngine._check_proto_myths()` lee el par de arquetipos dominantes del ICL tribal. Un mapa de 11 pares simbólicos determina el tipo de mito Campbell correspondiente (cosmogonía, teogonía, antropogonía, escatología, mito moral). El proto-mito gana coherencia cada vez que se transmite socialmente. Cuando supera el umbral de cristalización —controlado por el `ContextoEnunciativo`— se convierte en `MythCrystal` activo con efectos conductuales reales sobre la tribu.

**Narración (Ollama):** una vez que el mito cristaliza, el `NarratorEngine` encola un evento de tipo "profecía" que Ollama procesa en background y escribe como texto narrativo en `vault/Colectivo/Leyendas/`. La IA recibe el contexto del mito (protagonistas, tipo Campbell, estado del campo) y genera una leyenda en español con framing jungiano.

Cuando los dos protagonistas del mito mueren, el mito se convierte en `Leyenda` permanente con intensidad decreciente (0.998/día) que irradia efectos sobre agentes arquetípicamente afines de toda la tribu.

---

### 9. ¿Qué mide el MIG y por qué importa? ¿Cómo sé que la emergencia no es ruido?

El **MIG (Mean Information Gain)** mide cuánta información aporta saber la tribu de un agente sobre su perfil psicológico. Formalmente: para cada una de las 12 dimensiones arquetípicas, calcula `I(z_k; v) / H(z_k)` —información mutua normalizada entre el arquetipo k y la variable tribu v—. El MIG es la media sobre las 12 dimensiones.

- **MIG ≈ 0:** la tribu no predice nada sobre la psicología individual. El sistema produce ruido.
- **MIG ≈ 1:** conocer la tribu determina completamente el perfil arquetípico. Identidades tribales perfectas.

Se usan cuatro métricas complementarias para descartar ruido:
- **KL Divergencia** (¿cuán distintas son las distribuciones arquetípicas de distintas tribus?)
- **IMI** (¿qué fracción de la varianza arquetípica total está explicada por membresía tribal?)
- **VFE proxy** (entropía del campo colectivo: ¿cuánta incertidumbre hay en el inconsciente?)
- **MIG** (información mutua normalizada tribu↔arquetipos)

`scripts/run_robustness.py` ejecuta N simulaciones con semillas distintas. Si las cuatro métricas son consistentemente superiores a los baselines de control, la emergencia es real y replicable.

---

## Instalación y uso

### 10. ¿Qué necesito instalar para correr la simulación?

**Requisitos mínimos:**
```bash
pip install -r requirements.txt   # numpy, networkx, pyyaml, rich, scipy, matplotlib
```

**Para la narrativa LLM (opcional pero recomendado):**
- Instalar [Ollama](https://ollama.com) — el daemon se auto-arranca y descarga el modelo al iniciar
- Modelo por defecto: `llama3.2` (configurable)

**Para el visualizador en tiempo real:**
```bash
pip install pygame
```

**Para el dashboard analítico:**
```bash
pip install streamlit plotly
```

No se requiere GPU. La simulación core corre completamente en CPU. Ollama puede usar CPU si no hay GPU disponible (más lento pero funcional).

---

### 11. ¿Qué es `main.py` y cuál es la diferencia con `run_simulation.py`?

`main.py` es la **llave maestra interactiva**: un TUI (terminal UI) con menú Rich que guía al usuario paso a paso. Permite iniciar nueva simulación, continuar una pausada, abrir el visualizador Pygame, abrir el dashboard, y archivar simulaciones completadas. Antes de lanzar una nueva simulación pregunta el número de agentes, la semilla, si activar la narrativa LLM, y el modelo Ollama.

`run_simulation.py` es el **motor headless de línea de comandos**, sin interactividad. Acepta todos los parámetros por flags (`--seeds-file`, `--days`, `--seed`, `--resume`) y es el apropiado para correr desde scripts, crons, o servidores sin interfaz.

Para uso cotidiano: `python main.py`. Para automatización o robustez: `python scripts/run_simulation.py`.

---

### 12. ¿Puedo correr la simulación sin Ollama instalado?

Sí. La narrativa LLM es completamente opcional. Si Ollama no está disponible, el `NarratorEngine` activa su modo fallback y genera leyendas con plantillas predefinidas en español. La simulación corre sin degradación en ninguna de las mecánicas de fondo (psicología, tribus, mitos, métricas).

Para desactivar la narrativa explícitamente al lanzar desde `main.py`, responder "N" a la pregunta *"¿Activar narrativa LLM?"*. Desde línea de comandos:
```bash
NARRATIVE_ENABLED=0 python scripts/run_simulation.py --seeds-file data/seeds/100_personas.yaml
```

---

### 13. ¿Cómo retomo una simulación que dejé pausada?

El `CheckpointManager` guarda el estado completo cada 10 días simulados y también al interrumpir con `Ctrl+C`. Para reanudar:

- **Desde `main.py`:** opciones `[1]` o `[2]` del menú principal retoman automáticamente desde el último checkpoint.
- **Desde línea de comandos:**
```bash
python scripts/run_simulation.py --resume --days 500
python scripts/run_simulation.py --resume --days 0    # hasta extinción
```

Los checkpoints están en `data/checkpoints/checkpoint_*.json`. El más reciente se usa automáticamente. Si el archivo de DB y el checkpoint están sincronizados, se puede reanudar incluso después de cerrar y reabrir la PC.

---

### 14. ¿Cuántos agentes es recomendable usar? ¿Hay un mínimo para que emerjan tribus?

El mínimo funcional para que emerjan tribus es aproximadamente **20 agentes**. Con menos, el algoritmo de clustering no encuentra comunidades con suficiente cohesión interna.

Para que emerjan 3 o más tribus con divergencia cultural medible, el rango recomendado es **50–100 agentes**. Con 100 agentes se observan consistentemente 3–6 tribus, cristalización de mitos entre el día 50 y 200, y métricas de emergencia estadísticamente significativas.

El sistema admite hasta **150 agentes simultáneos** (límite configurable en `agent_core.py`). Por encima de ese número el rendimiento por tick empieza a degradarse notablemente en hardware doméstico.

Para experimentación rápida (prueba de concepto, debugging), los 15 agentes de `data/seeds/initial_personas.yaml` son suficientes y corren a máxima velocidad.

---

## Datos y resultados

### 15. ¿Dónde se guardan los resultados? ¿Qué contiene cada archivo?

```
data/
├── db/simulation.db              Base de datos SQLite completa
│                                 (snapshots de agentes, muertes, sesiones, clima)
├── checkpoints/
│   └── checkpoint_NNNN.json      Estado completo del simulador (cada 10 días)
├── metrics/
│   ├── emergence_series.csv      Serie temporal de KL / VFE / IMI / MIG por día
│   ├── emergence_summary.json    Resumen de la sesión actual
│   └── robustez.json             Resultados de run_robustness.py (N ejecuciones)
└── archive/
    └── Simulacion_01/            Simulaciones completadas (DB + checkpoints + vault)
```

Para explorar la base de datos directamente:
```bash
sqlite3 data/db/simulation.db
.tables
SELECT nombre, dia_muerte, arquetipo_dominante FROM agentes WHERE is_alive = 0;
```

---

### 16. ¿Cómo leo las narrativas generadas? ¿Necesito Obsidian?

No. Las narrativas son archivos Markdown planos en `vault/Colectivo/Leyendas/` y los perfiles de agentes en `vault/Personas/`. Se pueden leer con cualquier editor de texto.

Obsidian aporta la capa de visualización: el grafo de relaciones entre personas, leyendas y tribus, los vínculos entre documentos, y la navegación visual del vault completo. Es la forma más rica de explorar los resultados, pero es completamente opcional.

Si se instala Obsidian, basta con abrir la carpeta `vault/` como vault existente. El grafo de conocimiento se construye automáticamente a partir del frontmatter YAML que el simulador escribe en cada archivo.

---

## Arquitectura y desarrollo

### 17. ¿Cómo está estructurado el código? ¿Por dónde empezar a leerlo?

La arquitectura tiene tres capas: mundo físico, agentes, y sistemas sociales/narrativos. El punto de entrada para entender el flujo es `core/simulation.py` (`SimulationRunner`), que orquesta el reloj y los dos núcleos.

**Orden de lectura recomendado:**
1. `core/time/simulation_clock.py` — el reloj central y su protocolo de tick
2. `core/world/world_core.py` — el núcleo del mundo físico
3. `core/agents/agent.py` + `agent_core.py` — el agente y su orquestador
4. `core/agents/psyche/archetypes.py` — la psicología interna
5. `core/social/collective_field.py` + `mythology.py` — los sistemas emergentes
6. `core/metrics/emergence.py` — cómo se mide lo que emerge

Para contribuciones, la convención es que cada sistema tiene su propio módulo en `core/`. Los sistemas se comunican exclusivamente a través de `WorldSnapshot` (mundo → agentes) y `WorldAction` (agentes → mundo). No hay referencias cruzadas directas entre `WorldCore` y `AgentCore`.

---

### 18. ¿Cómo agrego un nuevo arquetipo o un nuevo tipo de mito?

**Nuevo arquetipo:**
1. Agregar el nombre a `ARCHETYPE_NAMES` en `core/agents/psyche/archetypes.py`
2. Agregar el atributo correspondiente en `ArchetypeVector`
3. Agregar su símbolo pool en `_ARCHETYPE_SYMBOLS` en `dreams.py`
4. Agregar su afinidad de bioma en el dict de deriva de `tribe_manager.py`
5. Actualizar `_ARCH_ATTRS` en `core/metrics/emergence.py`

**Nuevo tipo de mito:**
1. Agregar el par simbólico a `_PAIR_TO_MYTH_TYPE` en `core/social/mythology.py` (clave: `frozenset({"arq_a", "arq_b"})`, valor: nombre del tipo)
2. Si es un tipo Campbell nuevo (los actuales son 5), agregar la lógica de efectos conductuales en `_apply_by_type()` dentro de `MythCrystal`
3. Agregar el prompt correspondiente en `core/narrative/prompts.py` si se quiere narrativa diferenciada para ese tipo

Los pares simbólicos ya mapeados son 11; cualquier combinación de los 12 arquetipos que no esté en el mapa simplemente no cristaliza mito (comportamiento intencional).

---

## Límites y roadmap

### 19. ¿Cuáles son las limitaciones conocidas del sistema?

**Limitaciones técnicas:**
- El terreno es estático (80×60 hexágonos, sin tectónica ni inundaciones progresivas). El tamaño está hardcodeado y cambiarlo rompe el schema de la base de datos.
- El clustering tribal ocurre cada 30 días por batch; no hay separaciones tribales en tiempo real ante conflictos violentos.
- La narrativa LLM es asíncrona y best-effort: si Ollama está lento, las leyendas se generan con retraso o caen al fallback de plantillas.
- La memoria episódica de cada agente tiene ventana limitada (últimos N eventos); no hay memoria semántica a largo plazo.

**Limitaciones científicas:**
- Las métricas de emergencia (KL, IMI, MIG) miden divergencia arquetípica, pero no capturan directamente la complejidad narrativa o la riqueza simbólica.
- El modelo jungiano es una aproximación computacional: los 12 arquetipos son vectores numéricos, no conceptos clínicos rigurosos.
- Los resultados dependen de las condiciones iniciales. `run_robustness.py` existe precisamente para verificar reproducibilidad con distintas semillas.

---

### 20. ¿Qué viene en fases futuras?

El ROADMAP v2.0 (ver `src/ROADMAP2.md`) tiene las fases 6–9 completadas. Las direcciones exploradas para fases futuras incluyen:

- **Parámetros configurables en el launcher** — checkpoint interval, modos de distribución arquetípica inicial (uniforme / extremo / bimodal), N tribus iniciales forzadas
- **Deriva de terreno** — eventos geológicos lentos que fuerzan migraciones y aceleran la divergencia cultural
- **Memoria semántica** — los agentes recuerdan el significado de símbolos, no solo su ocurrencia
- **Hibridación tribal** — cuando dos tribus comparten territorio durante tiempo prolongado, sus ICL locales pueden fusionarse parcialmente
- **Exportación a red semántica** — grafo de conocimiento exportable a formatos estándar (RDF, GraphML) para análisis externo
