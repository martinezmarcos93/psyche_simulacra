# PSYCHE SIMULACRA — El Origen
## Inconsciente Colectivo Base y Estado Arcaico de la Simulación

> *No simulamos una sociedad que ya tiene inconsciente colectivo.  
> Simulamos el momento en que uno nace.*

---

## LA PREGUNTA CORRECTA

Jung no dice que el inconsciente colectivo sea una construcción social.
Dice que es una **estructura a priori de la psique** — anterior a la experiencia, anterior a la cultura, anterior al lenguaje.

El tabú del incesto aparece en culturas sin contacto histórico entre sí.
El arquetipo del Héroe emerge en mitologías de todos los continentes.
La figura de la Gran Madre precede a cualquier religión organizada.

Para Jung, eso no es coincidencia cultural. Es evidencia de que hay algo en la arquitectura psíquica que *produce* esos contenidos inevitablemente, bajo las condiciones adecuadas.

**Conclusión para la simulación:**
Hay dos capas de inconsciente colectivo, y hay que distinguirlas con precisión:

```
CAPA A — Inconsciente colectivo BASE (prefijar)
  Hardwired en la arquitectura del agente.
  No emerge — ya está. Es la gramática.
  Análogo: instintos + estructura neurológica.

CAPA B — Inconsciente colectivo CULTURAL (emergente)
  Construido por la experiencia colectiva.
  No se programa — nace. Es el vocabulario.
  Análogo: lenguaje, mitos, rituales, tabúes específicos.
```

El experimento real es observar cómo la Capa A, bajo presión,
genera inevitablemente contenidos de la Capa B.

---

## CAPA A — INCONSCIENTE COLECTIVO BASE

### Lo que se prefija en todos los agentes sin excepción

Estos no son valores culturales. Son constriccionas estructurales de la psique.
Se implementan como **módulos de activación automática**, no como reglas.

---

### 1. Prohibición del Incesto

No se implementa como una norma ("no harás X").
Se implementa como una **aversión afectiva hardwired** en el módulo de `apego`.

```python
# Pseudocódigo conceptual
def calculate_sexual_attraction(agent_a, agent_b):
    base_attraction = compute_base(agent_a, agent_b)
    
    kinship_coefficient = get_kinship(agent_a, agent_b)
    
    # Efecto Westermarck: convivencia temprana suprime atracción
    westermarck_suppression = cohabitation_years_early * 0.40
    
    # No es una regla. Es una aversión que emerge del módulo de apego.
    aversion_factor = kinship_coefficient * westermarck_suppression
    
    return base_attraction * (1 - aversion_factor)
```

**Por qué esto es importante:**
El tabú del incesto *como norma cultural* emerge después.
Primero viene la aversión psíquica. Luego el grupo la nombra, la codifica, la ritualiza.
En la simulación, el tabú debería aparecer como emergencia — como verbalización
de algo que todos los agentes ya sienten pero nadie ha nombrado todavía.

---

### 2. Priorización de la Supervivencia

El módulo de `amenaza` tiene **prioridad de procesamiento** sobre todos los demás.

```python
SURVIVAL_OVERRIDE_THRESHOLD = 0.70

def agent_step(agent):
    threat_level = agent.neural_modules["amenaza"]
    
    if threat_level > SURVIVAL_OVERRIDE_THRESHOLD:
        # Supervivencia suspende todos los otros procesos
        # Incluye: moralidad, vínculos sociales, identidad de rol
        return survival_mode(agent)
    
    return normal_decision_process(agent)
```

**Implicaciones emergentes:**
- Bajo presión extrema, los agentes violan sus propios valores
- El grupo puede sacrificar a uno por la supervivencia del resto
- El chivo expiatorio emerge naturalmente de esta lógica
- La cooperación emerge también — porque un grupo sobrevive más que un individuo solo

---

### 3. Cuidado de la Cría (arquetipo Madre/Padre como activación automática)

El arquetipo `madre` no es solo un peso en el vector de personalidad.
Es también un **módulo de activación** que se dispara ante ciertos estímulos:

```python
NURTURANCE_TRIGGERS = [
    "presencia_infante",        # Cualquier criatura pequeña y vulnerable
    "llanto_agudo",             # Frecuencia de angustia infantil
    "expresion_facial_bebe",    # Ojos grandes, frente alta (Kindchenschema)
    "vulnerabilidad_extrema",   # Cualquier agente en estado crítico
]

# No requiere vínculo genético — es una respuesta ante el estímulo
# Esto produce altruismo hacia no-parientes bajo ciertas condiciones
```

---

### 4. Jerarquía Dominancia/Sumisión

El módulo de `prediccion_social` evalúa automáticamente la posición relativa
de cada agente en cualquier interacción.

```python
# Señales que activan evaluación jerárquica automática
DOMINANCE_SIGNALS = [
    "tamaño_fisico",
    "exito_previo_en_conflicto",
    "riqueza_recursos",          # En arcaico: comida acumulada
    "apoyo_de_grupo",
    "seguridad_postural",        # Proxy de salud y confianza
    "edad_y_experiencia",
]

# El resultado modula automáticamente la conducta
# No es una decisión consciente — es una respuesta pre-reflexiva
```

**Implicación:** El liderazgo no se vota ni se hereda (todavía).
Emerge de la suma de señales de dominancia percibidas por el grupo.

---

### 5. Aversión al Caos y a la Muerte como Activador Simbólico

La muerte no es solo un evento en la simulación.
Es el **activador primario del pensamiento simbólico**.

Cuando un agente presencia la muerte de otro:
- El módulo de `amenaza` se dispara
- El arquetipo `sombra` sube
- Se activa una búsqueda de **significado** — reducción de ansiedad existencial
- Si muchos agentes viven esto simultáneamente, es el primer terreno fértil para un mito

```python
def process_witnessed_death(observer, deceased):
    observer.neural_modules["amenaza"] += 0.30
    observer.archetypes["sombra"] += 0.15
    
    # La psique busca contener el horror con significado
    # Si no hay mito disponible, el agente crea proto-explicación
    if collective_field.get("death_myth") is None:
        observer.generate_proto_symbol("muerte")
        # Si varios agentes generan proto-símbolos similares
        # → umbral → cristalización → primer mito colectivo
```

---

### 6. Reciprocidad como Fundamento Moral

Antes de cualquier sistema ético, la psique tiene **reciprocidad hardwired**.

```python
RECIPROCITY_TRACKING = {
    "favores_dados": {},
    "favores_recibidos": {},
    "deuda_percibida": {},      # Positiva o negativa
    "violaciones_registradas": {}
}

# Una violación de reciprocidad activa:
# - complejo de traición
# - arquetipo sombra hacia el infractor
# - impulso de justicia retributiva
# - potencial de exclusión social del grupo
```

Esto es el embrión de todos los sistemas legales y morales.
En el estado arcaico, se expresa como: *"tú me diste, yo te doy. Tú me quitaste, el grupo te expulsa."*

---

## EL ESTADO ARCAICO — PUNTO DE PARTIDA

### Por qué empezar en cazadores-recolectores nómadas

Si empezamos con instituciones, dinero, o roles sociales fijos —
ya estamos simulando el producto, no el proceso.

El estado arcaico es el único punto de partida honesto porque:

1. **Las instituciones no existen** — tienen que nacer
2. **El lenguaje simbólico no existe** — tiene que cristalizar
3. **La religión no existe** — solo hay experiencias numinosas sin nombre
4. **La economía no existe como sistema** — solo hay reciprocidad directa
5. **Los tabúes no existen como normas** — solo hay aversiones psíquicas

Cada uno de esos sistemas es un *emergente* del experimento.

---

### Parámetros del Estado Arcaico

```yaml
# Estado inicial de la simulación
estado_inicial:
  tamaño_grupo: 12-25  # Número de Dunbar básico: grupo de supervivencia
  estructura: "banda nómada"
  
  economia:
    sistema: "reciprocidad_directa"
    moneda: null
    propiedad: "uso_y_posesion" # No hay propiedad abstracta todavía
    surplus: 0.0               # No hay acumulación todavía
  
  organizacion_social:
    liderazgo: "situacional"   # Quién lidera depende del contexto
    roles_fijos: false         # Los roles emergen de competencias
    familia: "nuclear_extendida"
    exogamia: true             # El tabú del incesto ya opera (Capa A)
  
  conocimiento_colectivo:
    mitos: []                  # Vacío. Primer evento = primer proto-mito
    tabues_codificados: []     # Vacío. Las aversiones existen, los tabúes no
    rituales: []               # Vacío. Emergen de comportamientos repetidos
    dioses: []                 # Vacío. Las experiencias numinosas existen, los dioses no
  
  campo_colectivo:
    simbolos: {}               # Vacío al inicio
    presion_existencial: 0.60  # Alta por defecto: supervivencia es difícil
    cohesion_grupal: 0.50      # Media: el grupo se necesita pero hay tensión
  
  entorno:
    tipo: "sabana/bosque_templado"
    recursos: "escasos_variables"  # Abundancia y escasez cíclicas
    depredadores: true             # Presión de amenaza real
    clima: "variable_estacional"
```

---

### La Secuencia de Emergencia Esperada

Si el modelo es correcto, esta es la secuencia que debería observarse sin ser programada:

```
FASE ARCAICA TEMPRANA (Ciclos 1–200)
─────────────────────────────────────
→ El grupo sobrevive por reciprocidad y cooperación básica
→ Jerarquías situacionales emergen y se disuelven
→ Primera muerte significativa activa proto-símbolos en varios agentes
→ Los proto-símbolos similares resuenan → primer umbral de cristalización
→ PRIMER MITO: explicación colectiva de la muerte

FASE ARCAICA MEDIA (Ciclos 200–500)
─────────────────────────────────────
→ El mito de la muerte genera su opuesto: proto-mito de la vida/renacimiento
→ Un agente con héroe > 0.85 hace algo extraordinario
→ El grupo lo narra y re-narra → la narración se estabiliza → HÉROE FUNDADOR
→ La aversión al incesto, repetidamente vivida, se verbaliza por primera vez
→ PRIMER TABÚ CODIFICADO

FASE ARCAICA TARDÍA (Ciclos 500–1000)
───────────────────────────────────────
→ Surplus ocasional de recursos → primer conflicto por acumulación
→ Emergen roles especializados estables: el que sana, el que habla con los muertos
→ El ritual emerge de comportamientos repetidos que reducen ansiedad
→ PROTO-RELIGIÓN: el chamanismo como primer sistema simbólico formalizado

TRANSICIÓN A SOCIEDAD COMPLEJA (Ciclos 1000+)
──────────────────────────────────────────────
→ Si el grupo sobrevive y crece: división del trabajo
→ Economía de excedente → primera deuda → primera jerarquía fija
→ El mito del Héroe se convierte en mito de origen del grupo
→ El tabú del incesto se convierte en ley de exogamia
→ PROTO-ESTADO: liderazgo situacional → liderazgo hereditario
```

---

### Lo que el Experimento Debería Poder Responder

1. **¿Bajo qué presiones específicas nace el primer mito?**
   ¿Es siempre la muerte? ¿O puede ser la tormenta, la escasez, el depredador?

2. **¿El tabú del incesto emerge antes o después del primer mito?**
   Jung diría que antes — es Capa A. ¿La simulación lo confirma?

3. **¿El primer héroe es siempre el más fuerte o el que narra mejor?**
   ¿La figura heroica emerge del poder físico o del poder simbólico?

4. **¿Cuánto tiempo tarda en cristalizar el primer tabú?**
   ¿Hay un umbral poblacional mínimo para que ocurra?

5. **¿La cooperación o la jerarquía aparece primero?**
   ¿El grupo se organiza horizontalmente antes de generar dominancia?

6. **¿Qué destruye un grupo pequeño antes de que pueda generar cultura?**
   ¿La violencia interna? ¿La escasez? ¿La fragmentación simbólica?

---

### Implicaciones Técnicas del Estado Arcaico

#### La economía es reciprocidad, no dinero

```python
class ArcaicEconomy:
    """
    No hay moneda. No hay precio.
    Solo: quién le debe qué a quién, y cuándo.
    """
    
    def exchange(self, giver, receiver, resource, amount):
        # Actualiza deuda percibida
        receiver.reciprocity_debt[giver.id] += amount
        
        # Si la deuda acumula sin reciprocidad:
        # → activación de complejo de traición en el dador
        # → riesgo de exclusión del receptor
        
    def redistribute(self, leader, group, surplus):
        """
        El líder redistribuye el excedente.
        Esto es lo que hace al liderazgo legítimo en el arcaico.
        Quien acumula sin redistribuir pierde legitimidad.
        """
```

#### El primer dinero emerge de la simulación

No se programa una moneda. Pero si hay surplus repetido y el grupo crece,
debería emerger un **bien de referencia** — el objeto que todos aceptan como
intermediario. En grupos históricos: sal, pieles, conchas.

En la simulación: será lo que el campo colectivo haya cargado de valor simbólico.
Probablemente el recurso más escaso y más deseado en ese momento.

#### El primer ritual no se programa

Se detecta cuando un comportamiento:
- Se repite en el mismo contexto
- Es realizado por múltiples agentes
- Reduce la ansiedad del grupo (medible en el campo)
- Comienza a ser replicado por agentes que no lo iniciaron

Cuando eso ocurre: es un ritual. Y en ese momento se registra en el vault.

---

## RESUMEN: LO QUE SE PREFIJA VS LO QUE EMERGE

```
SE PREFIJA (Capa A — gramática psíquica universal)
  ✓ Aversión al incesto (módulo de apego + efecto Westermarck)
  ✓ Prioridad de supervivencia (override del módulo de amenaza)
  ✓ Cuidado de la cría (activación automática ante vulnerabilidad)
  ✓ Tracking de reciprocidad (embrión de toda moralidad)
  ✓ Evaluación jerárquica automática (dominancia/sumisión)
  ✓ Respuesta existencial ante la muerte (búsqueda de significado)
  ✓ Los 12 arquetipos como categorías vacías disponibles
  ✓ Los módulos neurales básicos (amenaza, recompensa, apego, etc.)

EMERGE (Capa B — vocabulario simbólico cultural)
  ✗ Qué animal es sagrado
  ✗ Quién es el héroe fundador
  ✗ Cuál es el nombre del mal
  ✗ Cuáles son los tabúes codificados
  ✗ Cuál es el primer ritual
  ✗ Qué sirve como dinero
  ✗ Cómo se organiza el liderazgo
  ✗ Cuál es el primer mito de origen
  ✗ Cuándo y cómo nace la religión
  ✗ Cómo se llama el dios
```

---

> *La diferencia entre un dios y un arquetipo es que el arquetipo es la estructura  
> y el dios es el nombre que una cultura específica le puso a esa estructura  
> después de que la experiencia colectiva la cristalizó en imagen.*
>
> — Síntesis para la simulación

---

*Psyche Simulacra — El Origen v1.0*  
*Documento de diseño fundamental — no modificar sin consenso del equipo*
