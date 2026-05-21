> **ARCHIVO — COMPLETADO** | Fecha: 2026-05-21
> Roadmap original v1.0. Todas las fases implementadas y superadas.
> El proyecto implementado incluye sistemas no previstos: tribus, mitología geográfica, narrativa LLM, cultura material y métricas de emergencia científica.

---

# PSYCHE SIMULACRA
## Simulación del Inconsciente Colectivo — Roadmap Técnico v1.0 [COMPLETADO]

> *Una sociedad de 100 agentes psicológicamente ricos, modelados con Jung, psiquiatría computacional y mecánicas cuánticas de socialización, documentados vivos en Obsidian.*

---

## VISIÓN DEL PROYECTO

Construir un laboratorio filosófico-técnico donde el inconsciente colectivo **emerge** de la interacción de agentes cognitivos complejos — no es programado, sino observado.

El sistema tiene tres capas que se alimentan mutuamente:

```
[ OBSIDIAN VAULT ]  ←→  [ MOTOR PYTHON ]  ←→  [ DASHBOARD ]
   Psique documental      Simulación ABM        Visualización
   Perfiles vivos         Mecánica cuántica     Inconsciente
   Red simbólica          Transformación        colectivo
```

---

## ESTRUCTURA DEL PROYECTO

```
psyche-simulacra/
│
├── core/                          # Motor central de simulación
│   ├── __init__.py
│   ├── agent.py                   # Clase base del agente
│   ├── psyche/
│   │   ├── archetypes.py          # Vectores arquetípicos jungianos
│   │   ├── complexes.py           # Complejos activables por contexto
│   │   ├── traits.py              # Rasgos psiquiátricos dimensionales
│   │   └── neural_modules.py     # Módulos neurológicos simplificados
│   ├── quantum/
│   │   ├── superposition.py       # Estados conductuales superpuestos
│   │   ├── entanglement.py        # Vínculos sociales entrelazados
│   │   └── collapse.py            # Colapso por interacción
│   ├── social/
│   │   ├── network.py             # Grafo de relaciones (NetworkX)
│   │   ├── interaction.py         # Motor de interacciones
│   │   └── collective_field.py   # Campo memético emergente
│   └── simulation.py              # Orquestador principal (Mesa)
│
├── obsidian/                      # Interfaz con el vault
│   ├── reader.py                  # Lee frontmatter YAML de notas
│   ├── writer.py                  # Escribe estado actualizado
│   ├── templates/
│   │   └── persona_template.md    # Plantilla canónica
│   └── sync.py                    # Ciclo de sincronización bidireccional
│
├── vault/                         # El vault de Obsidian (gitsubmodule opcional)
│   ├── Personas/
│   │   ├── P-001.md
│   │   ├── P-002.md
│   │   └── ...
│   ├── Colectivo/
│   │   ├── Campo_Memetico.md
│   │   ├── Eventos_Colectivos.md
│   │   └── Mitologia_Emergente.md
│   └── Meta/
│       ├── Simulacion_Log.md
│       └── Arquetipos_Activos.md
│
├── dashboard/                     # Visualización (Streamlit)
│   ├── app.py
│   ├── components/
│   │   ├── network_graph.py
│   │   ├── collective_field.py
│   │   └── agent_inspector.py
│   └── static/
│
├── data/
│   ├── db/
│   │   └── simulation.db          # SQLite — log histórico completo
│   ├── exports/
│   └── seeds/
│       └── initial_personas.yaml  # Configuración inicial de 12 agentes
│
├── scripts/
│   ├── generate_personas.py       # Generación aleatoria controlada
│   ├── run_simulation.py          # Entry point
│   └── export_collective.py       # Exporta estado del inconsciente colectivo
│
├── tests/
│   ├── test_agent.py
│   ├── test_quantum.py
│   └── test_network.py
│
├── docs/
│   ├── model_spec.md              # Especificación formal del modelo
│   └── archetype_theory.md        # Base teórica jungiana aplicada
│
├── pyproject.toml
├── requirements.txt
└── README.md
```

---

## MODELO CANÓNICO DEL AGENTE

### Estructura YAML (Frontmatter de cada Persona)

```yaml
---
id: P-001
alias: "El Guardián del Umbral"
edad: 42
rol_social: "Educador"

# ── ARQUETIPOS JUNGIANOS (0.0 → 1.0) ─────────────────────────
arquetipos:
  self: 0.61
  persona: 0.82        # Máscara social — alta → conformismo
  sombra: 0.74         # Contenidos reprimidos — alta → proyección
  anima_animus: 0.35
  heroe: 0.55
  sabio: 0.78
  trickster: 0.22
  madre: 0.40
  padre: 0.68
  nino_divino: 0.18
  gobernante: 0.50
  rebelde: 0.30

# ── COMPLEJOS ACTIVABLES ──────────────────────────────────────
complejos:
  abandono: 0.71       # Activado por: separaciones, pérdidas
  inferioridad: 0.45
  poder: 0.38
  culpa: 0.62
  materno: 0.55
  trascendencia: 0.80
  triggers:            # Contextos que activan cada complejo
    abandono: ["ruptura", "muerte", "rechazo"]
    culpa: ["fracaso_social", "traicion"]

# ── RASGOS PSIQUIÁTRICOS DIMENSIONALES ───────────────────────
rasgos:
  # Big Five
  apertura: 0.85
  responsabilidad: 0.72
  extraversion: 0.30
  amabilidad: 0.65
  neuroticismo: 0.48
  # Dimensiones clínicas
  ansiedad: 0.52
  impulsividad: 0.25
  disociacion: 0.18
  empatia: 0.77
  paranoia: 0.22
  narcisismo: 0.31
  estabilidad_emocional: 0.60
  sensibilidad_dopaminergica: 0.55
  agresividad: 0.28

# ── MÓDULOS NEUROLÓGICOS ─────────────────────────────────────
modulos_neurales:
  recompensa: 0.60
  amenaza: 0.45
  apego: 0.70
  exploracion: 0.80
  inhibicion: 0.50
  prediccion_social: 0.65

# ── ESTADO CUÁNTICO ACTUAL ───────────────────────────────────
estado_cuantico:
  vector_conductual:
    cooperacion: 0.55
    competencia: 0.20
    aislamiento: 0.15
    manipulacion: 0.10
  colapso_ultimo: "cooperacion"
  entrelazados_con: ["P-034", "P-087"]

# ── RED SOCIAL ────────────────────────────────────────────────
relaciones:
  - id: P-034
    tipo: "amistad_profunda"
    fuerza: 0.88
    resonancia_arquetipica: 0.72
    historia: "Trauma compartido — ciclo 047"
  - id: P-087
    tipo: "rivalidad"
    fuerza: -0.60
    resonancia_arquetipica: 0.15

# ── ESTADO DINÁMICO ──────────────────────────────────────────
estado_actual:
  emocion_dominante: "melancolia"
  energia: 0.55
  localizacion: "Biblioteca Central"
  ciclo_actual: 142

# ── MEMORIA EPISÓDICA ─────────────────────────────────────────
eventos_significativos:
  - ciclo: 23
    evento: "Muerte de P-012 (mentor)"
    impacto_arquetipo: {sabio: -0.12, sombra: +0.18}
  - ciclo: 98
    evento: "Confrontacion publica con P-055"
    impacto_complejo: {inferioridad: +0.09}

# ── INCONSCIENTE PERSONAL ────────────────────────────────────
suenos_recientes:
  - ciclo: 140
    simbolo_central: "torre_derrumbada"
    arquetipo_activado: "sombra"
    procesamiento: "integracion_parcial"

aspiraciones:
  conscientes:
    - "Transmitir conocimiento antes de envejecer"
    - "Ser recordado como justo"
  inconscientes:
    - "Ser rescatado del aislamiento"
    - "Recibir reconocimiento del padre"

intereses:
  - "Filosofía estoica"
  - "Astronomía amateur"
  - "Música polifónica"
---
```

---

## ROADMAP POR FASES

---

### FASE 0 — FUNDACIONAL (Semanas 1–2)
**Objetivo:** Base teórica, decisiones de diseño, entorno.

#### 0.1 Decisiones epistemológicas
Antes de escribir una sola línea de código, definir:

- [ ] **¿Qué ES el inconsciente computacionalmente?**
  Decisión: *espacio latente probabilístico* — el inconsciente de un agente es su distribución de estados no observados que influyen en la conducta observada.
- [ ] **¿Qué es una interacción?**
  Decisión: *operador matricial cuántico-inspirado* sobre el vector de estado conductual de ambos agentes.
- [ ] **¿Qué es transformación psicológica?**
  Decisión: *cambio persistente en pesos arquetípicos*, gatillado por eventos de alta carga emocional.

#### 0.2 Entorno de desarrollo
```bash
# Stack tecnológico
python = "^3.11"
mesa = "^2.3"           # ABM framework
networkx = "^3.2"       # Grafos de relaciones
numpy = "^1.26"         # Álgebra lineal (mecánica cuántica)
scipy = "^1.12"         # Distribuciones probabilísticas
pyyaml = "^6.0"         # Lectura/escritura vault Obsidian
streamlit = "^1.32"     # Dashboard
sqlite3                 # Built-in — logging histórico
pytest = "^8.0"         # Testing
loguru = "^0.7"         # Logging
```

#### 0.3 Vault Obsidian — Esqueleto
- [ ] Crear estructura de carpetas del vault
- [ ] Definir plantilla YAML canónica (ver arriba)
- [ ] Instalar plugins: Dataview, Templater, Graph Analysis

#### 0.4 Deliverables
- Documento `docs/model_spec.md` con todas las decisiones formalizadas
- Entorno Python configurado con `pyproject.toml`
- Vault Obsidian con estructura vacía

---

### FASE 1 — PROTOTIPO MÍNIMO VIABLE (Semanas 3–5)
**Objetivo:** 12 agentes corriendo, interactuando, transformándose.

> **Principio:** La emergencia viene de profundidad, no de cantidad. Empezamos con 12 agentes extremadamente ricos.

#### 1.1 Clase `Agent` — Núcleo Psicológico

**Archivo:** `core/agent.py`

```python
@dataclass
class Agent:
    id: str
    alias: str
    
    # Vectores psicológicos
    archetypes: ArchetypeVector      # 12 arquetipos × float
    complexes: ComplexProfile        # 6 complejos + triggers
    traits: TraitProfile             # Big Five + clínicos
    neural_modules: NeuralProfile    # 6 módulos
    
    # Estado cuántico
    behavioral_state: np.ndarray     # Vector de probabilidades conductuales
    entangled_with: list[str]        # IDs de agentes entrelazados
    
    # Red social
    relations: dict[str, Relation]
    
    # Memoria
    episodic_memory: list[Event]
    dreams: list[Dream]
    
    def step(self, context: SocialContext) -> BehavioralOutput:
        """Un tick de simulación para este agente."""
        ...
    
    def collapse_state(self, interaction: Interaction) -> str:
        """Colapso cuántico: de superposición a acción concreta."""
        ...
    
    def integrate_event(self, event: Event) -> None:
        """Actualiza arquetipos/complejos por evento significativo."""
        ...
    
    def dream(self) -> Dream:
        """Procesamiento onírico: reorganiza símbolos internos."""
        ...
```

#### 1.2 Módulo Cuántico — Superposición y Colapso

**Archivo:** `core/quantum/superposition.py`

El estado conductual es un vector de amplitudes complejas:

```
|ψ⟩ = α|cooperar⟩ + β|competir⟩ + γ|aislar⟩ + δ|manipular⟩

Donde: |α|² + |β|² + |γ|² + |δ|² = 1
```

El colapso se calcula como:
- Probabilidades base del vector conductual
- Modificadas por: contexto social, arquetipos activos, complejos disparados, campo colectivo
- Resultado: una acción concreta con historia registrada

#### 1.3 Mecánica de Interacción

**Archivo:** `core/social/interaction.py`

Protocolo de cada interacción entre agentes A y B:

```
1. Calcular resonancia arquetípica (similitud vectorial)
2. Verificar complejos activados por contexto
3. Colapsar estados de ambos agentes
4. Aplicar operador de interacción (matriz de transformación)
5. Actualizar vínculos (bond_strength, emotional_resonance)
6. Alimentar campo colectivo con residuo simbólico
7. Registrar en SQLite + actualizar vault
```

#### 1.4 Tests unitarios base
- [ ] `test_archetype_vector.py` — normalización, transformación
- [ ] `test_quantum_collapse.py` — distribución de probabilidades
- [ ] `test_interaction.py` — mecánica de encuentro entre 2 agentes

#### 1.5 Deliverables
- 12 agentes definidos manualmente en YAML (arquetipos deliberadamente contrastantes)
- Motor de interacción funcionando
- Primeros logs de transformación en SQLite

---

### FASE 2 — CAMPO COLECTIVO Y RED SOCIAL (Semanas 6–8)
**Objetivo:** El inconsciente colectivo emerge de las interacciones.

#### 2.1 Campo Memético Global

**Archivo:** `core/social/collective_field.py`

```python
class CollectiveField:
    """
    El inconsciente colectivo como campo emergente.
    No es una base de datos — es una función de las interacciones.
    """
    symbols: dict[str, float]      # Símbolos activos y su carga
    archetypes_active: dict[str, float]  # Arquetipos dominantes colectivos
    emotional_pressure: float      # Tensión social acumulada
    
    def absorb_interaction(self, interaction: Interaction) -> None:
        """Cada interacción alimenta el campo."""
        ...
    
    def radiate(self) -> FieldInfluence:
        """El campo retroalimenta a todos los agentes."""
        ...
    
    def detect_emergence(self) -> list[Phenomenon]:
        """
        Detecta: mitos emergentes, chivos expiatorios,
        héroes colectivos, tabúes, rituales.
        """
        ...
```

#### 2.2 Red Social Multi-Capa

**Archivo:** `core/social/network.py`

Cinco grafos superpuestos (NetworkX MultiDiGraph):

| Red | Peso | Dinámica |
|-----|------|----------|
| Emocional | bond_strength (-1 → 1) | Lenta — cambia por eventos |
| Ideológica | ideological_alignment (0 → 1) | Media — influenciable |
| Económica | resource_dependency (0 → 1) | Lenta — roles fijos |
| Afectiva/Sexual | intimacy (0 → 1) | Variable — alta carga |
| Ritual/Simbólica | symbolic_resonance (0 → 1) | Emerge de campo |

#### 2.3 Entrelazamiento Social

Cuando dos agentes comparten un evento de alta carga emocional (trauma, amor, traición), quedan "entrelazados":

```python
class Entanglement:
    agent_a: str
    agent_b: str
    strength: float          # Intensidad del vínculo cuántico
    origin_event: str        # El evento fundante
    correlation_matrix: np.ndarray  # Cómo covaria su estado
    
    def propagate_change(self, source: str, delta: np.ndarray) -> np.ndarray:
        """Un cambio en A se propaga probabilísticamente a B."""
        ...
```

#### 2.4 Sincronización Bidireccional con Obsidian

**Archivo:** `obsidian/sync.py`

```python
class ObsidianSync:
    def read_agent(self, agent_id: str) -> dict:
        """Lee frontmatter YAML de la nota del agente."""
        ...
    
    def write_agent_state(self, agent: Agent) -> None:
        """Actualiza estado en vault tras cada ciclo."""
        ...
    
    def append_event(self, agent_id: str, event: Event) -> None:
        """Añade evento a la sección de memoria episódica."""
        ...
    
    def update_collective(self, field: CollectiveField) -> None:
        """Actualiza notas del inconsciente colectivo."""
        ...
```

#### 2.5 Deliverables
- Campo colectivo emergente funcionando
- 5 redes sociales activas y dinámicas
- Vault actualizado automáticamente tras cada ciclo de simulación
- Primera detección de fenómenos emergentes (rol de chivo expiatorio, líder simbólico)

---

### FASE 3 — TRANSFORMACIÓN PSICOLÓGICA (Semanas 9–11)
**Objetivo:** Los agentes evolucionan. La individuación es dinámica.

> *Esta fase es el corazón filosófico del proyecto. La mayoría de simulaciones fracasan aquí.*

#### 3.1 Motor de Individuación

**Archivo:** `core/psyche/individuation.py`

Reglas de transformación arquetípica:

```python
TRANSFORMATION_RULES = {
    "trauma": {
        "shadow": +0.15,        # Trauma activa sombra
        "hero": -0.08,          # Debilita héroe
        "child_divine": +0.12,  # Regresión psíquica
    },
    "power_corruption": {
        "gobernante": +0.20,
        "sombra": +0.18,
        "empatia_trait": -0.15,
    },
    "prolonged_isolation": {
        "sombra": +0.25,
        "persona": -0.20,       # Máscara se deteriora
        "trickster": +0.10,
    },
    "sacred_crisis": {           # Crisis que genera símbolo nuevo
        "self": +0.20,
        "rebelde": +0.15,
        "collective_field.rebirth": +0.30,
    },
    "deep_bond": {
        "anima_animus": +0.12,
        "shadow": -0.08,         # El amor integra sombra
    },
}
```

#### 3.2 Sistema Onírico

**Archivo:** `core/psyche/dreams.py`

Los agentes "sueñan" cada N ciclos. El sueño:
- Procesa el trauma más reciente no integrado
- Activa el símbolo del complejo dominante
- Puede producir insight (reducción de complejo) o amplificación (aumento)
- Genera contenido para la nota del vault

```python
class DreamEngine:
    def generate_dream(self, agent: Agent) -> Dream:
        """
        Genera sueño basado en:
        - Complejos activados recientemente
        - Arquetipos en tensión
        - Campo colectivo actual
        """
        dominant_complex = self._find_dominant_complex(agent)
        symbol = self._select_symbol(dominant_complex, agent.archetypes)
        outcome = self._process_trauma(agent, symbol)
        return Dream(symbol=symbol, outcome=outcome, ciclo=self.current_cycle)
```

#### 3.3 Mitología Emergente

**Archivo:** `core/social/mythology.py`

Cuando un patrón arquetípico se repite suficientes veces en el campo colectivo, cristaliza en mito:

```
Condición de emergencia:
  field["heroe"] > 0.75 AND
  field["sombra"] > 0.65 AND
  existe_agente_con(heroe > 0.80) AND
  existe_agente_con(sombra > 0.80)

→ Emerge narrativa de "héroe vs monstruo"
→ Se documenta en vault: Colectivo/Mitologia_Emergente.md
→ Altera comportamiento de todos los agentes (self-fulfilling myth)
```

#### 3.4 Estados Liminales Colectivos

Eventos que alteran TODO el campo psíquico:

| Evento | Trigger | Efecto en campo |
|--------|---------|-----------------|
| Epidemia | random + contagio_social > 0.8 | death_archetype +0.40 |
| Líder carismático | agente con hero > 0.85 emerge | gobernante +0.35, rebelde +0.20 |
| Colapso institucional | economic_network density < 0.2 | caos_field +0.50 |
| Revelación colectiva | field["self"] > 0.80 | rebirth +0.45 |

#### 3.5 Deliverables
- Agentes que se transforman de forma coherente con su historia
- Sistema onírico generando contenido en vault
- Primeros mitos emergentes documentados
- Log forense: rastrear origen de cada transformación

---

### FASE 4 — ESCALADO A 100 AGENTES (Semanas 12–14)
**Objetivo:** La sociedad completa. Optimización y emergencia a escala.

#### 4.1 Generación Procedural de Personas

**Archivo:** `scripts/generate_personas.py`

Estrategia para los 88 agentes restantes:

```python
class PersonaGenerator:
    """
    Genera agentes con distribuciones estadísticamente realistas.
    No todos son casos extremos — la mayoría son "normales".
    """
    
    ARCHETYPE_DISTRIBUTIONS = {
        # La distribución en una sociedad real
        "gobernante": Normal(mu=0.35, sigma=0.20),
        "sombra": Normal(mu=0.50, sigma=0.25),  # Universal
        "self": Normal(mu=0.30, sigma=0.20),     # Raro en forma plena
        "heroe": Normal(mu=0.45, sigma=0.22),
    }
    
    SOCIAL_ROLES = [
        ("Artesano", 0.15),       # 15% de la población
        ("Comerciante", 0.12),
        ("Educador", 0.10),
        ("Líder político", 0.05),  # Minoría con alto gobernante
        ("Marginado", 0.08),       # Alto sombra, baja persona
        ("Sanador", 0.08),
        ("Guerrero", 0.10),
        ("Sabio/Místico", 0.04),
        # ...
    ]
```

#### 4.2 Optimización del Motor

- [ ] Paralelizar cálculo de interacciones con `asyncio`
- [ ] Cachear resonancias arquetípicas (no recalcular si no cambiaron)
- [ ] SQLite → WAL mode para escrituras concurrentes
- [ ] Batch updates al vault (no escribir cada ciclo, sino cada 10)

#### 4.3 Análisis de Red a Escala

```python
# Métricas de inconsciente colectivo a monitorear
metrics = {
    "polarization_index": nx.modularity(G, communities),
    "collective_anxiety": field["amenaza"].mean(),
    "myth_crystallization": len(mythology.active_myths),
    "shadow_projection_rate": interactions_hostile / total_interactions,
    "individuation_progress": agents.self_archetype.mean(),
    "scapegoat_index": max(agent.blame_received for agent in agents),
}
```

#### 4.4 Deliverables
- 100 agentes corriendo estables
- Performance: ≥10 ciclos/segundo
- Métricas del inconsciente colectivo en tiempo real

---

### FASE 5 — DASHBOARD Y ANÁLISIS (Semanas 15–17)
**Objetivo:** Ver el inconsciente colectivo moverse.

#### 5.1 Dashboard Streamlit

**Archivo:** `dashboard/app.py`

Paneles:

```
┌─────────────────────────────────────────────────────────┐
│  PSYCHE SIMULACRA  —  Ciclo: 342  —  ▶ Corriendo       │
├───────────────────┬─────────────────────────────────────┤
│  RED SOCIAL       │  CAMPO COLECTIVO                    │
│  (grafo vivo)     │  [radar de arquetipos activos]      │
│                   │  Miedo: ████████░░ 0.81             │
│  ● P-001          │  Esperanza: ██░░░░░░ 0.22           │
│  ● P-034 ──────── │  Sombra colectiva: ███████░ 0.74   │
│  ● P-087          │  Renacimiento: █░░░░░░░░ 0.12       │
├───────────────────┼─────────────────────────────────────┤
│  INSPECTOR        │  MITOLOGÍA EMERGENTE                │
│  [P-001 selec.]   │  • "El Juicio del Olvidado" (c.287) │
│  Arquetipos ↓     │  • "La Gran Madre Oscura" (c.301)   │
│  Sombra:  0.74    │  • "El Traidor Sagrado" (c.315)     │
│  Sabio:   0.78    ├─────────────────────────────────────┤
│  Estado:  melancol│  INDIVIDUACIÓN COLECTIVA            │
│                   │  [línea temporal de self.mean()]    │
└───────────────────┴─────────────────────────────────────┘
```

#### 5.2 Análisis Forense

**Archivo:** `scripts/export_collective.py`

```sql
-- ¿Cuándo emergió el primer chivo expiatorio?
SELECT ciclo, agent_id, event_type, blame_delta
FROM interactions
WHERE event_type = 'projection_shadow'
ORDER BY ciclo ASC
LIMIT 1;

-- Evolución del arquetipo "sombra" colectivo
SELECT ciclo, AVG(shadow_weight) as shadow_colectivo
FROM agent_snapshots
GROUP BY ciclo;

-- Momentos de máxima cristalización mítica
SELECT ciclo, myth_name, trigger_agent, field_intensity
FROM mythology_log
ORDER BY field_intensity DESC;
```

#### 5.3 Deliverables
- Dashboard funcional con 4 paneles
- Exportación de análisis histórico completo
- Primeros hallazgos documentados en vault: `Meta/Simulacion_Log.md`

---

### FASE 6 — EXPERIMENTOS Y PUBLICACIÓN (Semanas 18+)
**Objetivo:** El laboratorio filosófico en acción.

#### 6.1 Experimentos Diseñados

| Experimento | Pregunta | Variable manipulada |
|-------------|----------|---------------------|
| **Sombra Espejo** | ¿Los agentes proyectan su sombra en quienes más se parecen o en quienes más difieren? | Similitud arquetípica |
| **El Héroe Necesario** | ¿El campo genera héroes cuando la presión colectiva supera un umbral? | emotional_pressure |
| **Individuación vs. Tribu** | ¿El proceso de individuación aísla o conecta? | self_archetype velocity |
| **Trauma Colectivo** | ¿Un evento traumático sincroniza o fragmenta el campo? | Crisis event injection |
| **Mito Auto-Profético** | ¿Un mito emergente altera el comportamiento futuro hacia su propia realización? | Mythology feedback loop |

#### 6.2 Exportación como Investigación
- Notebook Jupyter con análisis estadístico de cada experimento
- El vault de Obsidian como "publicación viva" del estado de la sociedad
- Opción: paper filosófico-técnico sobre el modelo

---

## STACK TECNOLÓGICO DEFINITIVO

| Capa | Tecnología | Justificación |
|------|-----------|---------------|
| Simulación ABM | Mesa 2.x | Estándar en Python ABM, visualización incluida |
| Redes | NetworkX | Multi-grafo, análisis de centralidad |
| Álgebra cuántica | NumPy + SciPy | Vectores de estado, distribuciones |
| Vault | Obsidian + PyYAML | Psique documental viva |
| Persistencia | SQLite (WAL) | Log histórico completo, consultas forenses |
| Dashboard | Streamlit | Prototipado rápido, suficiente para investigación |
| Testing | Pytest + Hypothesis | Property-based testing para modelos probabilísticos |
| Logging | Loguru | Trazabilidad de transformaciones |

### ¿Por qué no Rust/Go?
El cuello de botella no es velocidad de cómputo sino **complejidad conceptual**. Python permite iterar el modelo psicológico rápidamente. Si en Fase 4 el motor de interacciones es lento, se extrae ese módulo a Rust con PyO3 — pero solo entonces.

---

## MÉTRICAS DE ÉXITO DEL PROYECTO

| Hito | Criterio |
|------|---------|
| F1 completa | 12 agentes interactúan y se transforman coherentemente |
| F2 completa | Campo colectivo emerges de interacciones (no hardcodeado) |
| F3 completa | Un agente cambia su arquetipo dominante por historia vivida |
| F4 completa | 100 agentes, ≥10 ciclos/segundo |
| F5 completa | Se puede identificar visualmente el "estado psíquico" de la sociedad |
| F6 completa | Al menos 3 experimentos con resultados interpretables |

---

## PRÓXIMOS PASOS INMEDIATOS

```bash
# Semana 1 — hoy mismo
1. Crear repositorio git
2. Definir los 12 agentes iniciales manualmente
   (elegirlos con arquetipos deliberadamente contrastantes)
3. Escribir model_spec.md con decisiones epistemológicas
4. Configurar entorno Python
5. Crear vault Obsidian con estructura base
```

---

*Psyche Simulacra — v1.0 Roadmap — Un laboratorio donde el inconsciente no se programa, se observa.*
