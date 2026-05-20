# PSYCHE SIMULACRA — Sistema de Vida
## Nacimiento, Muerte, Herencia y Demografía

> *Un agente no es un objeto que se crea y se destruye.  
> Es una psique que nace con una gramática heredada,  
> vive acumulando historia, y muere dejando una huella simbólica  
> en el campo colectivo que sobrevive a su cuerpo.*

---

## I. ANATOMÍA DE UN AGENTE VIVO

Antes de definir la muerte y el nacimiento, hay que definir qué significa
estar vivo en la simulación.

Un agente vivo es un sistema con **cuatro capas de estado simultáneo:**

```
CAPA BIOLÓGICA          CAPA PSICOLÓGICA
─────────────────       ──────────────────────────────
hambre      [0→1]       arquetipos       [vector 12D]
fatiga      [0→1]       complejos        [vector 6D]
salud       [0→1]       rasgos           [vector 10D]
edad        [días]      estado_emocional [humor, ansiedad]
                        memoria_episódica [lista eventos]

CAPA SOCIAL             CAPA SIMBÓLICA
──────────────          ──────────────────────────────
vínculos    [grafo]     carga_campo      [contribución al campo]
rol_actual  [str]       proto_simbolos   [lista]
status      [0→1]       sueños           [lista]
deudas      [dict]      herencia_simbolica [post-mortem]
```

Un agente muere cuando la **capa biológica colapsa**.
Un agente nace cuando la **capa biológica se inicializa** con herencia de las capas
psicológica y simbólica de sus progenitores.

---

## II. SISTEMA DE MUERTE

### 2.1 Filosofía

La muerte nunca es aleatoria.
Siempre es la consecuencia acumulada de necesidades no satisfechas,
conflictos no resueltos, o condiciones extremas sostenidas.

El sistema no "mata" agentes. Los agentes mueren cuando su estado
biológico cruza umbrales que el código detecta pero no produce.

---

### 2.2 Causas de Muerte en Beta

#### CAUSA 1 — Inanición

```python
INANICION_UMBRAL_CRITICO = 0.92   # hambre
INANICION_DIAS_CRITICOS  = 3      # días consecutivos sobre el umbral

def check_inanicion(agent):
    if agent.hambre > INANICION_UMBRAL_CRITICO:
        agent.dias_criticos += 1
        agent.salud -= 0.08          # deterioro acelerado
        agent.fatiga += 0.12
        agent.humor  -= 0.15
        
        # Activación arquetípica por hambre extrema
        agent.archetypes["sombra"]  += 0.05
        agent.archetypes["nino_divino"] += 0.04  # regresión psíquica
        
        if agent.dias_criticos >= INANICION_DIAS_CRITICOS:
            return trigger_muerte(agent, causa="inanicion")
    else:
        agent.dias_criticos = max(0, agent.dias_criticos - 1)
```

**Condiciones previas típicas:**
- El grupo no redistribuyó recursos
- El agente tiene vínculos débiles (nadie lo alimentó)
- Estación de escasez sin surplus acumulado
- Marginado social — excluido de la reciprocidad del grupo

**Señal de alerta observable en vault:**
> *"Día 47 — [Agente_09] lleva 2 días sin alimentarse.  
> Su hambre está en 0.94. El grupo no ha respondido."*

---

#### CAUSA 2 — Violencia Inter-agente

```python
VIOLENCIA_BOND_UMBRAL    = -0.75  # vínculo mínimo para violencia
VIOLENCIA_AGRESIVIDAD    = 0.80   # agresividad mínima del atacante
VIOLENCIA_CAMPO_AMPLIF   = 1.0    # si campo tiene alta carga de conflicto

def check_violencia(agent_a, agent_b, context):
    bond = get_bond(agent_a, agent_b)
    
    if (bond < VIOLENCIA_BOND_UMBRAL and
        agent_a.traits["agresividad"] > VIOLENCIA_AGRESIVIDAD and
        context.field["conflicto"] > 0.65):
        
        # No muerte instantánea — escalada
        agent_b.salud -= 0.35
        agent_b.trauma_reciente = True
        
        if agent_b.salud < 0.10:
            return trigger_muerte(agent_b, causa="violencia",
                                  perpetrador=agent_a.id)
```

**Condiciones previas típicas:**
- Rivalidad acumulada durante ciclos (bond decayendo gradualmente)
- Campo colectivo con alta carga de conflicto o miedo
- Complejo de poder + complejo de traición activados simultáneamente
- Ausencia de mediador (el agente "sabio" no está presente o está débil)

**Nota importante:** la violencia letal debería ser rara en beta.
No imposible — pero rara. Si ocurre frecuentemente, hay un bug en los
pesos de agresividad o en la mecánica de vínculos.

---

#### CAUSA 3 — Exposición Climática

Solo disponible si el agente está en una situación combinada:

```python
def check_exposicion(agent, clima):
    exposicion_critica = (
        clima.temperatura < -5 or clima.temperatura > 42
    ) and agent.energia < 0.15 and not agent.tiene_refugio

    if exposicion_critica:
        agent.salud -= 0.15 * clima.severidad
        
        if agent.salud < 0.05:
            return trigger_muerte(agent, causa="exposicion_climatica")
```

**Nota beta:** Esta causa es la menos probable de las tres.
Requiere la combinación de clima extremo + agente sin refugio + energía crítica.
Sirve como presión de diseño para que el grupo construya refugios básicos.

---

### 2.3 El Proceso de Muerte — `trigger_muerte()`

```python
def trigger_muerte(agent, causa, perpetrador=None):
    """
    La muerte no es una línea de código.
    Es un proceso de 6 pasos con consecuencias en cadena.
    """
    
    # PASO 1: Marcar al agente como muerto
    agent.status = "muerto"
    agent.dia_muerte = simulation.clock.dia_actual
    agent.causa_muerte = causa
    
    # PASO 2: Calcular carga simbólica del agente muerto
    # Un agente con más historia y vínculos tiene más peso simbólico
    carga_simbolica = calcular_carga_simbolica(agent)
    # carga_simbolica ∈ [0.1, 1.0]
    # Depende de: centralidad en red, días vividos, eventos significativos,
    #             arquetipos dominantes, rol social
    
    # PASO 3: Impactar el campo colectivo
    collective_field.absorb_death(
        agent       = agent,
        carga       = carga_simbolica,
        causa       = causa,
        perpetrador = perpetrador
    )
    # Si carga > 0.70 → alta probabilidad de proto-mito
    # Si causa == "violencia" → campo["conflicto"] sube fuerte
    # Si causa == "inanicion" → campo["miedo"] + campo["injusticia"] suben
    
    # PASO 4: Procesar duelo en agentes vinculados
    for agente_vinculado in get_agentes_con_vinculo(agent):
        procesar_duelo(agente_vinculado, fallecido=agent,
                       bond_strength=get_bond(agente_vinculado, agent))
    
    # PASO 5: Herencia de recursos y rol
    redistribuir_recursos(agent, grupo=simulation.grupo)
    liberar_rol(agent)
    
    # PASO 6: Documentar en vault
    vault.registrar_muerte(agent)
    # La nota del agente NO se borra. Se archiva con tag "muerto"
    # y se agrega sección "Legado simbólico" al final
```

---

### 2.4 Efectos de la Muerte en el Campo Colectivo

```python
def absorb_death(agent, carga, causa, perpetrador):
    
    # Muerte siempre activa el símbolo de muerte
    collective_field["muerte"] += 0.20 * carga
    
    # Efectos adicionales por causa
    if causa == "inanicion":
        collective_field["miedo"]     += 0.15 * carga
        collective_field["escasez"]   += 0.20 * carga
        collective_field["injusticia"] += 0.10 * carga  # Si el grupo tenía recursos
        
    elif causa == "violencia":
        collective_field["conflicto"] += 0.30 * carga
        collective_field["miedo"]     += 0.25 * carga
        # El perpetrador puede convertirse en símbolo negativo
        if perpetrador:
            marcar_simbolo_negativo(perpetrador, intensidad=carga)
    
    elif causa == "exposicion_climatica":
        collective_field["miedo"]      += 0.20 * carga
        collective_field["naturaleza"] += 0.25 * carga  # La naturaleza como fuerza
    
    # Si varios agentes mueren en ciclos cercanos → amplificación
    if muertes_recientes(ventana=10) >= 2:
        collective_field["muerte"] *= 1.40  # El campo resuena
        check_cristalizacion("muerte")       # Umbral de primer mito
    
    # Muerte de agente con alta carga simbólica
    if carga > 0.70:
        # El agente muerto puede convertirse en figura mítica
        candidate_myth = {
            "tipo": inferir_tipo_mito(agent),  # heroe_caido, martir, ancestro
            "agente_origen": agent.id,
            "ciclo_emergencia": simulation.clock.dia_actual,
            "campo_trigger": collective_field.snapshot()
        }
        mythology.add_candidate(candidate_myth)
```

---

### 2.5 Procesamiento del Duelo

El duelo no es un estado binario. Es un proceso con fases que dependen
del arquetipo dominante del observador.

```python
DUELO_POR_ARQUETIPO = {
    "heroe": {
        "fase_inicial": "negacion_activa",    # Busca culpable, quiere actuar
        "duracion_dias": 15,
        "impacto": {"agresividad": +0.15, "shadow": +0.10}
    },
    "madre": {
        "fase_inicial": "cuidado_compensatorio",  # Redirige cuidado a otros
        "duracion_dias": 30,
        "impacto": {"ansiedad": +0.20, "apego_modulo": +0.15}
    },
    "sabio": {
        "fase_inicial": "integracion_simbolica",  # Busca significado
        "duracion_dias": 20,
        "impacto": {"apertura": +0.10, "proto_simbolos": +1}
        # El sabio es quien más probablemente genera el proto-mito
    },
    "trickster": {
        "fase_inicial": "desplazamiento",    # Conducta bizarra, humor negro
        "duracion_dias": 10,
        "impacto": {"imprevisibilidad": +0.25}
        # El trickster puede iniciar el primer ritual sin proponérselo
    },
    "sombra_dominante": {
        "fase_inicial": "proyeccion",        # Culpa a alguien del grupo
        "duracion_dias": 25,
        "impacto": {"paranoia": +0.20, "bond_negativo_target": -0.20}
    }
}

def procesar_duelo(observador, fallecido, bond_strength):
    arquetipo_dom = get_arquetipo_dominante(observador)
    config = DUELO_POR_ARQUETIPO.get(arquetipo_dom, DUELO_DEFAULT)
    
    # Intensidad del duelo proporcional al vínculo
    intensidad = abs(bond_strength)  # 0 → 1
    
    observador.estado_duelo = {
        "activo": True,
        "fallecido_id": fallecido.id,
        "fase": config["fase_inicial"],
        "dias_restantes": int(config["duracion_dias"] * intensidad),
        "impacto_aplicado": False
    }
    
    # Evento en memoria episódica
    observador.memoria.add_event(
        tipo="muerte_vinculo",
        descripcion=f"Muerte de {fallecido.alias}",
        impacto_emocional=intensidad * -0.8,
        ciclo=simulation.clock.dia_actual
    )
```

---

### 2.6 Herencia Simbólica Post-Mortem

El agente muerto no desaparece del sistema simbólico.

```python
class LegadoSimbolico:
    """
    Lo que queda de un agente después de su muerte.
    Puede persistir en el campo durante ciclos o años simulados.
    """
    
    agente_id: str
    alias: str
    dia_muerte: int
    causa_muerte: str
    
    # Carga que aporta al campo, decayendo con el tiempo
    carga_inicial: float
    decay_rate: float = 0.002  # Pierde ~0.2% de carga por día simulado
    
    # Si fue convertido en figura mítica, no decae
    es_figura_mitica: bool = False
    tipo_mito: str = None  # "heroe_fundador" / "martir" / "ancestro" / "monstruo"
    
    def get_carga_actual(self, dia_actual):
        if self.es_figura_mitica:
            return self.carga_inicial  # Los mitos no decaen solos
        dias_transcurridos = dia_actual - self.dia_muerte
        return self.carga_inicial * (1 - self.decay_rate) ** dias_transcurridos
    
    def puede_ser_invocado(self):
        """
        El grupo puede 'invocar' al muerto en rituales.
        Eso recarga su carga simbólica y refuerza el mito.
        """
        return self.es_figura_mitica and self.get_carga_actual() > 0.30
```

---

## III. SISTEMA DE NACIMIENTO

### 3.1 Filosofía

Un recién nacido trae la **Capa A completa** (gramática psíquica universal)
más una **herencia específica** de sus progenitores
más una **impronta del campo colectivo** en el momento de nacer.

Jung: el recién nacido no es tabla rasa.
Trae la estructura arquetípica, los módulos neurales, la capacidad simbólica.
Lo que no trae es ningún contenido cultural — ningún tabú específico,
ningún nombre para los arquetipos, ningún mito particular.

---

### 3.2 Condiciones Necesarias para el Nacimiento

```python
CONDICIONES_NACIMIENTO = {
    # Biológicas
    "vinculo_reproductivo": bond_strength >= 0.65,     # Vínculo afectivo mínimo
    "generos_distintos": True,                          # Por ahora binario en beta
    "edad_progenitor_a": agent_a.edad_dias >= 365 * 14, # ~14 años simulados
    "edad_progenitor_b": agent_b.edad_dias >= 365 * 14,
    "salud_minima_madre": madre.salud >= 0.50,
    
    # Grupales (el grupo tiene que poder sostener la cría)
    "recursos_grupo": surplus_promedio_30dias >= 0.20,
    "tamaño_grupo": len(grupo.agentes_vivos) < TAMAÑO_MAXIMO,
    "no_crisis_activa": collective_field["miedo"] < 0.85,
    
    # Probabilística (no determinista)
    "probabilidad_base": 0.05  # 5% por día si todas las condiciones se cumplen
    # Modificadores: vínculo más alto → mayor prob, escasez → menor prob
}
```

---

### 3.3 Sistema de Herencia — El Genoma Psicológico

```python
def generar_nuevo_agente(progenitor_a, progenitor_b, campo_colectivo):
    """
    El nuevo agente hereda de tres fuentes:
    1. Progenitores (promedio con varianza)
    2. Campo colectivo (impronta del momento)
    3. Ruido aleatorio (individualidad irreducible)
    """
    
    nuevo = Agent()
    
    # ── HERENCIA DE ARQUETIPOS ────────────────────────────────
    for arquetipo in ARQUETIPOS:
        # Base: promedio parental
        base = (progenitor_a.archetypes[arquetipo] +
                progenitor_b.archetypes[arquetipo]) / 2
        
        # Varianza genética: ±20% del promedio
        varianza = np.random.normal(0, base * 0.20)
        
        # Impronta del campo: el símbolo dominante del campo
        # imprime una predisposición ligera
        simbolo_dominante = campo_colectivo.get_simbolo_dominante()
        impronta_campo = calcular_impronta(arquetipo, simbolo_dominante) * 0.10
        
        nuevo.archetypes[arquetipo] = np.clip(
            base + varianza + impronta_campo,
            0.05, 0.95  # Nunca 0 ni 1 — siempre potencial de cambio
        )
    
    # ── HERENCIA DE RASGOS (Big Five) ─────────────────────────
    # Heredabilidad empírica: 40–60% según el rasgo
    HEREDABILIDAD = {
        "apertura":          0.57,
        "responsabilidad":   0.49,
        "extraversion":      0.54,
        "amabilidad":        0.42,
        "neuroticismo":      0.58,
        "sensibilidad_dopaminergica": 0.65,  # Alta heredabilidad
        "ansiedad":          0.55,
    }
    
    for rasgo, h in HEREDABILIDAD.items():
        base_parental = (progenitor_a.traits[rasgo] +
                         progenitor_b.traits[rasgo]) / 2
        componente_heredado = base_parental * h
        componente_ambiental = np.random.uniform(0.1, 0.9) * (1 - h)
        
        nuevo.traits[rasgo] = np.clip(
            componente_heredado + componente_ambiental,
            0.05, 0.95
        )
    
    # ── HERENCIA DE MÓDULOS NEURALES ─────────────────────────
    for modulo in MODULOS_NEURALES:
        nuevo.neural_modules[modulo] = np.clip(
            np.random.normal(
                mean=(progenitor_a.neural_modules[modulo] +
                      progenitor_b.neural_modules[modulo]) / 2,
                std=0.12
            ),
            0.10, 0.90
        )
    
    # ── IMPRONTA DEL CAMPO COLECTIVO ─────────────────────────
    # El símbolo más cargado del campo en el momento del nacimiento
    # deja una huella arquetípica en el recién nacido
    # Esto es Jung puro: el inconsciente colectivo imprime al individuo
    
    nuevo.impronta_natal = {
        "campo_snapshot": campo_colectivo.snapshot(),
        "simbolo_dominante": simbolo_dominante,
        "dia_nacimiento": simulation.clock.dia_actual,
        "nota": inferir_nota_natal(simbolo_dominante)
        # Ej: nacer con campo["muerte"] = 0.80 → leve predisposición a sombra
    }
    
    # ── ESTADO INICIAL ────────────────────────────────────────
    nuevo.edad_dias      = 0
    nuevo.salud          = 0.95
    nuevo.hambre         = 0.40  # Depende de la madre los primeros ciclos
    nuevo.fatiga         = 0.20
    nuevo.energia        = 0.80
    nuevo.fase_vital     = "infancia"
    nuevo.puede_actuar   = False  # Inactivo hasta fase "niñez"
    
    # ── VÍNCULOS INICIALES ────────────────────────────────────
    nuevo.vinculos = {
        progenitor_a.id: Vinculo(tipo="familia", bond_strength=0.90),
        progenitor_b.id: Vinculo(tipo="familia", bond_strength=0.90),
    }
    # Efecto Westermarck activado desde el inicio con co-residentes
    for agente in simulation.grupo.agentes_vivos:
        if agente.id not in nuevo.vinculos:
            nuevo.westermarck_registro[agente.id] = {
                "anios_convivencia_temprana": 0,
                "aversion_sexual": 0.0
            }
    
    return nuevo
```

---

### 3.4 La Impronta del Campo — Por Qué Importa

```
EJEMPLOS DE IMPRONTA NATAL

Nace cuando campo["muerte"] > 0.75:
  → sombra base ligeramente más alta (+0.08 sobre promedio parental)
  → sensibilidad a la pérdida más alta
  → Predisposición: el agente que procesa la muerte del grupo

Nace cuando campo["heroe"] > 0.70 + héroe fundador activo:
  → héroe base ligeramente más alto (+0.06)
  → modulo exploración más alto
  → Predisposición: el agente que continúa la narrativa del héroe

Nace cuando campo["miedo"] > 0.80 (crisis de supervivencia):
  → ansiedad base más alta (+0.10)
  → modulo amenaza más sensible
  → Predisposición: el agente hipervigilante, conservador, tribal

Nace en período de surplus y campo["esperanza"] > 0.60:
  → apertura más alta (+0.08)
  → modulo exploración más alto
  → Predisposición: el agente innovador, curioso, menos tribal
```

Esto produce **generaciones con carácter colectivo** — algo observable en la historia real:
las generaciones que nacen en crisis tienen perfiles distintos a las que nacen en prosperidad.
No por determinismo — por impronta estadística.

---

### 3.5 Fases de Vida del Agente

```python
FASES_VITALES = {
    "infancia": {
        "rango_dias":    (0, 365 * 5),      # 0–5 años simulados
        "puede_actuar":  False,
        "depende_de":    "progenitores",    # Consume recursos del grupo
        "vulnerabilidad": 0.80,             # Alta mortalidad infantil arcaica
        "efecto_grupo":  "activa_modulo_madre_en_adultos",
        "desarrollo":    "imprime_vinculos_primarios"
    },
    "niñez": {
        "rango_dias":    (365 * 5, 365 * 12),
        "puede_actuar":  True,              # Participa en tareas simples
        "depende_de":    "grupo",
        "vulnerabilidad": 0.30,
        "desarrollo":    "forma_personalidad_base"
        # Aquí el efecto Westermarck se consolida
    },
    "adolescencia": {
        "rango_dias":    (365 * 12, 365 * 18),
        "puede_actuar":  True,
        "puede_reproducirse": False,
        "vulnerabilidad": 0.15,
        "desarrollo":    "individuacion_temprana",
        # El agente desafía al dominante → tensión de jerarquía
        "tension_jerarquica": True
    },
    "adultez": {
        "rango_dias":    (365 * 18, 365 * 45),
        "puede_actuar":  True,
        "puede_reproducirse": True,
        "vulnerabilidad": 0.08,
        "desarrollo":    "consolidacion_arquetipica"
    },
    "madurez": {
        "rango_dias":    (365 * 45, 365 * 65),
        "puede_actuar":  True,
        "puede_reproducirse": False,        # Reducido fuertemente
        "vulnerabilidad": 0.20,
        "desarrollo":    "integracion_o_rigidez",
        # El arquetipo héroe tiende a sabio si hay individuación
        # Si no hay individuación: rigidez, autoridad, resistencia al cambio
        "transformacion_arquetipica": {
            "heroe → sabio": "si self > 0.55",
            "heroe → gobernante_rigido": "si self < 0.30"
        }
    },
    "vejez": {
        "rango_dias":    (365 * 65, None),  # Hasta muerte
        "puede_actuar":  True,              # Con limitaciones
        "vulnerabilidad": 0.45,             # Sube cada año
        "desarrollo":    "legado_o_amargura",
        "carga_simbolica": "alta",          # Los viejos tienen más peso simbólico
        # Su muerte activa más fuertemente el proto-mito del ancestro
    }
}
```

---

### 3.6 Mortalidad Infantil — La Realidad Arcaica

En grupos de cazadores-recolectores históricos, la mortalidad infantil
es del 40–50% antes de los 5 años.

```python
MORTALIDAD_INFANTIL = {
    "fase": "infancia",
    "probabilidad_base_diaria": 0.0015,  # ~40% acumulada en 5 años
    
    # Factores que la reducen:
    "reduccion_por_vinculo_fuerte_madre": -0.0008,
    "reduccion_por_surplus_recursos":     -0.0006,
    "reduccion_por_grupo_grande":         -0.0004,
    
    # Factores que la aumentan:
    "aumento_por_crisis_recursos":        +0.0010,
    "aumento_por_clima_extremo":          +0.0007,
    "aumento_por_conflicto_interno":      +0.0005,
}
```

**Implicación narrativa:** la muerte de un infante es uno de los eventos
más cargados simbólicamente que puede ocurrir en el grupo.
Activa fuertemente el arquetipo `madre` en todos los adultos,
y puede ser el origen de los primeros rituales de protección de la cría.

---

## IV. DEMOGRAFÍA Y VIABILIDAD DEL GRUPO

### 4.1 Zonas Demográficas

```python
ZONAS_DEMOGRAFICAS = {
    "optima":   {"rango": (15, 25), "descripcion": "Grupo funcional y dinámico"},
    "segura":   {"rango": (12, 14), "descripcion": "Viable, menor diversidad"},
    "tension":  {"rango": (8, 11),  "descripcion": "Alta presión, cohesión o ruptura"},
    "critica":  {"rango": (5, 7),   "descripcion": "Supervivencia prioritaria"},
    "colapso":  {"rango": (3, 4),   "descripcion": "Fin probable del experimento"},
    "extincion":{"rango": (0, 2),   "descripcion": "Fin del experimento"}
}

def get_zona_demografica(n_agentes):
    for zona, config in ZONAS_DEMOGRAFICAS.items():
        rango = config["rango"]
        if rango[0] <= n_agentes <= rango[1]:
            return zona
    return "extincion"
```

---

### 4.2 Efectos de la Zona Demográfica en el Sistema

```python
EFECTOS_ZONA = {
    "tension": {
        "collective_field_modificador": {"miedo": +0.20, "cohesion": +0.25},
        "probabilidad_nacimiento":  +0.03,  # El grupo busca reproducirse
        "agresividad_intergrupal":  -0.20,  # Cooperación interna sube
        "umbral_cristalizacion":    -0.10,  # Más fácil que emerja un mito
        # La presión existencial acelera la formación de símbolos
    },
    "critica": {
        "collective_field_modificador": {"miedo": +0.45, "muerte": +0.30},
        "probabilidad_nacimiento":  -0.04,  # El cuerpo "sabe" que no es el momento
        "override_supervivencia":   True,   # Todos los agentes en modo amenaza
        "probabilidad_mito_emergencia": 0.85,  # La crisis genera mitos
    },
    "colapso": {
        "narrative_event": "fin_inminente",
        "vault_registro":  "El grupo no sobrevivió",
        "campo_ultimo_estado": "guardar_snapshot_final"
    }
}
```

---

### 4.3 El Colapso como Resultado Válido

```python
def handle_extincion(grupo, campo_colectivo):
    """
    La extinción del grupo no es un error del sistema.
    Es un resultado experimental con valor informativo.
    """
    
    # Guardar historia completa
    vault.crear_nota_epitafio(
        titulo=f"Historia del Grupo — {grupo.nombre}",
        contenido={
            "dias_vividos":       simulation.clock.dia_actual,
            "agentes_totales":    grupo.total_agentes_historico,
            "causa_colapso":      inferir_causa_colapso(grupo, campo_colectivo),
            "mitos_generados":    mythology.get_all(),
            "tabues_emergidos":   taboos.get_all(),
            "rituales_formados":  rituals.get_all(),
            "ultimo_campo":       campo_colectivo.snapshot(),
            "linea_tiempo":       events_log.get_all(),
        }
    )
    
    # Preguntas para el investigador
    vault.crear_nota_reflexion(
        preguntas=[
            "¿En qué día se cruzó el umbral de no retorno?",
            "¿Hubo un evento específico que desencadenó el colapso?",
            "¿El grupo generó algún símbolo antes de desaparecer?",
            "¿La estructura de vínculos predijo el colapso?",
            "¿Qué agente sobrevivió más tiempo y por qué?",
        ]
    )
    
    simulation.status = "extinto"
    # Ofrecer opción: reiniciar con parámetros ajustados
    # o analizar los datos del grupo fallido
```

---

## V. DATASETS DE VIDA — Lo que se registra

### Dataset: `agent_lifecycle`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `agent_id` | str | |
| `alias` | str | Nombre simbólico |
| `dia_nacimiento` | int | |
| `dia_muerte` | int | Null si vive |
| `causa_muerte` | str | inanicion / violencia / exposicion / vejez |
| `perpetrador_id` | str | Null si no aplica |
| `dias_vividos` | int | |
| `fase_vital_final` | str | |
| `progenitor_a` | str | Null si agente inicial |
| `progenitor_b` | str | Null si agente inicial |
| `impronta_natal_simbolo` | str | Símbolo dominante al nacer |
| `impronta_natal_campo` | JSON | Snapshot del campo al nacer |
| `carga_simbolica_final` | float | Peso simbólico al morir |
| `es_figura_mitica` | bool | |
| `tipo_mito` | str | Si aplica |
| `legado_campo_dias` | int | Cuántos días siguió activo en el campo |
| `total_vinculos` | int | Vínculos en el momento de muerte |
| `vinculo_mas_fuerte` | str | ID del agente |
| `vinculo_mas_fuerte_valor` | float | |
| `eventos_significativos_count` | int | |
| `arquetipo_dominante_final` | str | |
| `transformaciones_arquetipicas` | int | Cuántas veces cambió su dominante |

### Dataset: `births_log`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `birth_id` | UUID | |
| `ciclo` | int | |
| `nuevo_agente_id` | str | |
| `progenitor_a` | str | |
| `progenitor_b` | str | |
| `bond_strength_progenitores` | float | Al momento del nacimiento |
| `tamaño_grupo_momento` | int | |
| `surplus_grupo_momento` | float | |
| `campo_snapshot` | JSON | Estado del campo al nacer |
| `simbolo_impronta` | str | |
| `arquetipo_mas_heredado` | str | El que más se parecía a los padres |
| `arquetipo_mas_mutado` | str | El que más difirió |
| `condiciones_criticas` | bool | ¿Nació en zona crítica? |

### Dataset: `deaths_log`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `death_id` | UUID | |
| `ciclo` | int | |
| `agente_id` | str | |
| `causa` | str | |
| `fase_vital` | str | |
| `edad_dias` | int | |
| `salud_previa_7dias` | JSON | Evolución de salud previa |
| `hambre_previa_7dias` | JSON | |
| `campo_momento` | JSON | Estado del campo |
| `agentes_en_duelo` | JSON | IDs y bond_strength |
| `carga_simbolica` | float | |
| `proto_mito_generado` | bool | |
| `tipo_mito_generado` | str | |
| `tamaño_grupo_postmortem` | int | |
| `zona_demografica_postmortem` | str | |

---

## VI. RESUMEN — Ciclo de Vida Completo

```
NACER
  ← Herencia arquetípica de progenitores (promedio + varianza)
  ← Herencia de rasgos (heredabilidad empírica por rasgo)
  ← Impronta del campo colectivo en el momento natal
  ← Ruido individual irreducible
  → Vínculos primarios con progenitores (bond = 0.90)
  → Efecto Westermarck activado con co-residentes

VIVIR
  → Fases vitales: infancia → niñez → adolescencia → adultez → madurez → vejez
  → Cada fase tiene vulnerabilidad, capacidades y transformaciones arquetípicas
  → La historia vivida modifica los arquetipos lentamente
  → Los vínculos construyen la red social
  → Los eventos acumulan en memoria episódica
  → Los sueños procesan trauma y generan proto-símbolos
  → La individuación (o su ausencia) define el arco del agente

MORIR
  → Por inanición / violencia / exposición / vejez
  → Nunca al azar — siempre como consecuencia acumulada
  → Impacta el campo colectivo proporcional a su carga simbólica
  → Genera duelo diferenciado en los vinculados
  → La nota en Obsidian se archiva, no se borra
  → El legado simbólico persiste y decae (o no, si se vuelve mito)
  → Puede convertirse en figura mítica que retroalimenta al grupo
    después de muerto
```

---

> *La diferencia entre un ancestro y un fantasma  
> es que el ancestro sigue siendo útil para el grupo.*
>
> *En la simulación, ambos existen — la diferencia  
> está en el valor de su carga simbólica en el campo colectivo.*

---

*Psyche Simulacra — Sistema de Vida v1.0*
