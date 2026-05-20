# PSYCHE SIMULACRA — El Mundo
## Diseño Completo del Escenario: Geografía, Recursos y Sistema de Descubrimiento

> *El mundo existe completo desde el momento cero.  
> Los agentes no lo crean — lo revelan.*

---

## I. FILOSOFÍA DEL MUNDO

### Tres principios fundamentales

**1. Completitud desde el origen**
Todo recurso, todo material, toda forma de energía que existirá
en la simulación ya existe en el día 1. Enterrado, latente, invisible —
pero presente. Los agentes descubren, no generan.

**2. El mundo tiene memoria**
Una zona sobrexplotada no se regenera instantáneamente.
Un bosque quemado tarda décadas en volver. Un río contaminado
afecta aguas abajo. El mundo recuerda lo que le hicieron.

**3. La escala importa**
Un mundo para potencialmente 1000 personas no puede ser
el mismo que para 15. El mundo tiene que ser genuinamente grande —
suficiente para que grupos puedan no encontrarse durante años,
para que haya territorios sin explorar, para que la geografía
sea una fuerza que moldea la cultura tanto como los arquetipos.

---

## II. REPRESENTACIÓN DEL ESPACIO

### Por qué no alcanza un grafo de zonas

Un grafo de zonas (Bosque → Pradera → Río) funciona para 15 agentes
en una región pequeña. Para 100–1000 agentes con potencial de
expansión territorial, fragmentación grupal, y comercio a distancia,
necesitamos que **la distancia importe**.

Dos grupos separados por una montaña tienen culturas distintas.
Una ruta comercial entre dos asentamientos tarda días en recorrerse.
Un recurso al otro lado del río requiere cruzarlo — eso es una decisión.

### Solución: Grilla Hexagonal de Biomas

```
ESPECIFICACIONES DE LA GRILLA

Tamaño:         80 × 60 hexágonos = 4800 celdas totales
Escala:         1 hexágono ≈ 1 km² (área caminable en 1 día)
Población max:  ~200–250 personas por hexágono densamente ocupado
                → 4800 hexs × densidad media 0.2 = ~960 personas máximo
                → Diseñado para 1000 con margen

Coordenadas:    Sistema axial hexagonal (q, r)
Distancia:      Medida en hexs — 1 hex = ~1 día de viaje a pie
                Con carga pesada: 0.5 hexs/día
                Terreno difícil: 0.3 hexs/día
```

```
VISTA ESQUEMÁTICA DEL MAPA (80×60 hexs)
────────────────────────────────────────────────────────────

  ╔══════════════════════════════════════════════════════╗
  ║  MONTAÑA    MONTAÑA    BOSQUE    BOSQUE   COSTA      ║
  ║  ALTA       ALTA       TEMPLADO  TROPICAL            ║
  ║                                                       ║
  ║  MONTAÑA    BOSQUE     PRADERA   PRADERA  DELTA      ║
  ║  MEDIA      MIXTO      HÚMEDA    SECA     FLUVIAL    ║
  ║                                                       ║
  ║  COLINAS    PRADERA    ●INICIO   SABANA   LAGO       ║
  ║  ROCOSAS    MIXTA      (15 ag.)  ABIERTA  INTERIOR   ║
  ║                                                       ║
  ║  VALLE      RÍO        SABANA    PANTANO  COSTA      ║
  ║  FÉRTIL     MAYOR      ARIDA     COSTERO             ║
  ║                                                       ║
  ║  CUEVA      COLINAS    LLANURA   DESIERTO ISLA       ║
  ║  SISTEMA    SUAVES     ALUVIAL   BORDE    PEQUEÑA    ║
  ╚══════════════════════════════════════════════════════╝

  ● = Posición inicial del grupo (día 1)
  El 90% del mapa es terra incognita en el día 1
```

---

## III. BIOMAS — Los 12 Tipos de Hexágono

Cada hexágono tiene un bioma que determina sus recursos base,
su clima, su dificultad de traversía, y sus recursos ocultos potenciales.

```python
BIOMAS = {

    "bosque_templado": {
        "color_mapa":       "#2D6A4F",
        "traversia":        0.70,      # Moderada
        "recursos_visibles": {
            "madera":       0.85,
            "frutos":       0.65,      # Estacional
            "raices":       0.60,
            "leña":         0.80,
            "fibras":       0.55,
            "agua_lluvia":  0.50,
        },
        "fauna_visible": {
            "pequena":      0.65,
            "grande":       0.35,
        },
        "recursos_ocultos": {
            "miel":         {"prob_deposito": 0.20, "descubrimiento": "exploracion"},
            "hongos_medicinales": {"prob": 0.30, "desc": "conocimiento_botanico"},
            "arcilla_subterranea": {"prob": 0.15, "desc": "excavacion"},
            "pedernal_calidad": {"prob": 0.25, "desc": "busqueda_piedra"},
        },
        "clima_mod":        {"temperatura": 0, "humedad": +0.15},
        "capacidad_sustento": 40,      # Personas que puede sostener por hex
        "regeneracion_base": 0.03,     # Por día simulado sin presión
    },

    "pradera_húmeda": {
        "color_mapa":       "#6B9E3A",
        "traversia":        0.95,      # Fácil
        "recursos_visibles": {
            "pasto_forraje": 0.80,
            "raices":        0.55,
            "agua_arroyos":  0.45,
            "fibras":        0.70,
        },
        "fauna_visible": {
            "pequena":       0.45,
            "grande":        0.65,     # Más fauna grande en praderas
            "aves":          0.50,
        },
        "recursos_ocultos": {
            "arcilla_superficial": {"prob": 0.35, "desc": "observacion"},
            "sal_mineral":  {"prob": 0.10, "desc": "seguir_fauna"},
            # Los animales van a los depósitos de sal — observarlos revela la sal
            "turba":        {"prob": 0.20, "desc": "excavacion_pantano"},
            "semillas_cultivables": {"prob": 0.15, "desc": "conocimiento_botanico"},
            # La agricultura empieza cuando alguien reconoce semillas cultivables
        },
        "clima_mod":        {"viento": +0.20, "exposicion": +0.30},
        "capacidad_sustento": 55,
        "regeneracion_base": 0.04,
    },

    "rio_mayor": {
        "color_mapa":       "#1E6091",
        "traversia":        0.40,      # Difícil de cruzar sin tecnología
        "recursos_visibles": {
            "agua_fresca":   1.00,
            "peces":         0.70,
            "arcilla_orilla": 0.60,
            "juncos":        0.65,
            "cantos_rodados": 0.80,    # Piedra redondeada — buena para herramientas
        },
        "recursos_ocultos": {
            "pepitas_metal_nativo": {"prob": 0.05, "desc": "busqueda_piedra_avanzada"},
            # Oro, cobre nativo — visible si sabes buscarlo
            "plantas_medicinales_ribereñas": {"prob": 0.40, "desc": "observacion_cuidadosa"},
            "vado_natural":  {"prob": 0.30, "desc": "exploracion_rio"},
            # Encontrar un vado permite cruzar sin tecnología
        },
        "genera_recurso": {
            "peces":         True,     # Se regenera si no se sobrexplota
            "arcilla":       True,     # Reposición anual por aluvión
        },
        "bloqueador":        True,     # Divide el mapa — la tecnología de cruce es hito
        "capacidad_sustento": 70,      # Muy alto — los ríos sostienen civilizaciones
        "regeneracion_base": 0.05,
    },

    "montaña_alta": {
        "color_mapa":       "#8B8B8B",
        "traversia":        0.20,      # Muy difícil
        "recursos_visibles": {
            "piedra_dura":   0.95,
            "pedernal":      0.60,
            "obsidiana":     0.10,     # Rara pero visible en afloramientos
        },
        "fauna_visible": {
            "pequena":       0.20,
            "grande_altitud": 0.30,    # Fauna específica de altura
        },
        "recursos_ocultos": {
            "mena_cobre":    {"prob": 0.08, "desc": "mineria_basica"},
            # El cobre es el primer metal trabajable — revolución tecnológica
            "mena_hierro":   {"prob": 0.04, "desc": "mineria_avanzada"},
            "cueva_habitable": {"prob": 0.35, "desc": "exploracion"},
            "sal_roca":      {"prob": 0.12, "desc": "exploracion_profunda"},
            "cristales_cuarzo": {"prob": 0.20, "desc": "busqueda_minerales"},
            # El cuarzo tiene valor simbólico altísimo en culturas arcaicas
            "paso_montaña":  {"prob": 0.15, "desc": "exploracion_sistematica"},
            # Encontrar un paso abre acceso al otro lado — hito geográfico
        },
        "clima_mod":        {"temperatura": -0.30, "viento": +0.40},
        "peligro_fisico":   0.40,      # Alto riesgo de lesión/muerte
        "capacidad_sustento": 15,
        "regeneracion_base": 0.008,    # Muy lenta
        "valor_estrategico": 0.90,     # Vista, defensa, recursos únicos
        "valor_simbolico":   0.80,     # Las alturas son sagradas — siempre
    },

    "sabana_abierta": {
        "color_mapa":       "#C9A84C",
        "traversia":        0.85,
        "recursos_visibles": {
            "pasto_seco":    0.75,
            "arboles_esparcidos": 0.30,
            "agua_temporal": 0.25,     # Solo en lluvias
        },
        "fauna_visible": {
            "grande_manada": 0.80,     # Grandes manadas — caza mayor
            "pequena":       0.35,
            "aves_rapaces":  0.45,
        },
        "recursos_ocultos": {
            "pozo_natural":  {"prob": 0.10, "desc": "seguir_fauna_en_sequia"},
            "sal_superficial": {"prob": 0.15, "desc": "observacion"},
            "hueso_fosil":   {"prob": 0.08, "desc": "excavacion"},
            # Los fósiles — primer encuentro con lo que existió antes
            # Potencial simbólico enorme
        },
        "estacionalidad":   "extrema", # Seco y húmedo muy marcados
        "capacidad_sustento": 35,
        "regeneracion_base": 0.025,
    },

    "pantano_costero": {
        "color_mapa":       "#4A7C59",
        "traversia":        0.25,      # Muy difícil sin conocimiento
        "recursos_visibles": {
            "juncos_densos": 0.90,
            "agua":          0.85,     # Pero salobre — no bebible sin tratar
            "aves_acuaticas": 0.70,
            "peces_agua_salada": 0.55,
        },
        "recursos_ocultos": {
            "sal_evaporacion": {"prob": 0.40, "desc": "observacion_estacional"},
            # La sal aparece al evaporarse el agua en verano — revolucionaria
            # como conservante y luego como moneda
            "ruta_costera":  {"prob": 0.20, "desc": "exploracion"},
            "mariscos":      {"prob": 0.60, "desc": "exploracion_litoral"},
            "turba_combustible": {"prob": 0.30, "desc": "excavacion"},
        },
        "peligro_sanitario": 0.30,     # Enfermedades — post-beta
        "capacidad_sustento": 25,
        "regeneracion_base": 0.035,
    },

    "cueva_sistema": {
        "color_mapa":       "#3D3D3D",
        "traversia":        0.50,      # Requiere conocimiento del sistema
        "recursos_visibles": {
            "piedra_caliza":  0.90,
            "agua_subterranea": 0.60,  # Manantial si se encuentra
            "refugio_absoluto": True,  # La cueva es el mejor refugio
        },
        "recursos_ocultos": {
            "espacio_ritual": {"prob": 0.70, "desc": "exploracion_interior"},
            # Las cuevas profundas son los primeros espacios sagrados — universal
            # La oscuridad + resonancia acústica + aislamiento = experiencia numinosa
            "pigmentos_minerales": {"prob": 0.45, "desc": "exploracion_interior"},
            "manantial_puro": {"prob": 0.35, "desc": "exploracion_profunda"},
            "cristalizaciones": {"prob": 0.25, "desc": "exploracion_profunda"},
        },
        "valor_simbolico":   0.95,     # Las cuevas tienen el valor simbólico más alto
        # Paleolítico: toda el arte rupestre está en cuevas profundas, no en entradas
        # La oscuridad absoluta como primer acceso al inconsciente colectivo
        "capacidad_sustento": 8,
        "regeneracion_base": 0.001,    # Prácticamente no se regenera
    },

    "lago_interior": {
        "color_mapa":       "#2980B9",
        "traversia":        0.60,      # Bordeable pero sin cruzar sin tecnología
        "recursos_visibles": {
            "agua_fresca":   0.95,
            "peces_lago":    0.75,
            "aves_acuaticas": 0.60,
            "arcilla_orilla": 0.70,
        },
        "recursos_ocultos": {
            "ruta_lacustre": {"prob": 0.20, "desc": "navegacion_basica"},
            # Navegar el lago — requiere balsa (tecnología)
            "isla_central":  {"prob": 0.15, "desc": "navegacion"},
            # Una isla en el lago — inaccesible sin navegación
            # Alto valor simbólico: el lugar que no se puede alcanzar a pie
            "peces_profundidad": {"prob": 0.40, "desc": "pesca_avanzada"},
        },
        "valor_estrategico": 0.85,     # Control del agua = poder
        "capacidad_sustento": 80,
        "regeneracion_base": 0.04,
    },

    "valle_fértil": {
        "color_mapa":       "#27AE60",
        "traversia":        0.90,
        "recursos_visibles": {
            "suelo_profundo": 0.90,    # Potencial agrícola — inútil sin agricultura
            "agua_canal":    0.80,
            "madera":        0.50,
            "plantas_silvestres": 0.75,
        },
        "recursos_ocultos": {
            "semillas_cereales": {"prob": 0.35, "desc": "conocimiento_botanico_avanzado"},
            # El descubrimiento de semillas cultivables + suelo fértil
            # = inicio posible de agricultura — revolución neolítica en miniatura
            "arcilla_aluvial": {"prob": 0.55, "desc": "observacion"},
            "vena_agua_subterranea": {"prob": 0.20, "desc": "excavacion"},
        },
        "capacidad_sustento": 120,     # El más alto — los valles sostienen ciudades
        "regeneracion_base": 0.06,     # La más alta
        "potencial_agricola": True,    # Especial — puede volverse tierra de cultivo
    },

    "costa_abierta": {
        "color_mapa":       "#85C1E9",
        "traversia":        0.75,
        "recursos_visibles": {
            "mariscos":      0.70,
            "peces_costa":   0.65,
            "sal_evaporacion": 0.30,   # Visible en ciertas condiciones
            "piedra_costera": 0.60,
        },
        "recursos_ocultos": {
            "ruta_maritima": {"prob": 0.10, "desc": "navegacion_avanzada"},
            # La costa como ruta comercial — post-arcaico pero presente en el mundo
            "conchas_ornamento": {"prob": 0.80, "desc": "exploracion_litoral"},
            # Las conchas son el primer objeto de valor simbólico inter-grupal
            # documentado — aparecen en sitios a cientos de km de la costa
            "ámbar":         {"prob": 0.05, "desc": "busqueda_especializada"},
            # El ámbar: primer material de valor puramente simbólico/comercial
        },
        "valor_comercial":   0.80,     # La costa facilita el intercambio futuro
        "capacidad_sustento": 45,
        "regeneracion_base": 0.04,
    },

    "desierto_borde": {
        "color_mapa":       "#E8C454",
        "traversia":        0.35,
        "recursos_visibles": {
            "piedra_arida":  0.80,
            "plantas_xerofitas": 0.20,
        },
        "recursos_ocultos": {
            "oasis":         {"prob": 0.08, "desc": "exploracion_desesperada"},
            # Solo se busca cuando no hay otra opción — presión máxima
            "obsidiana_afloramiento": {"prob": 0.12, "desc": "busqueda_piedra"},
            "sal_playa_seca": {"prob": 0.20, "desc": "observacion"},
            "ruta_comercial_antigua": {"prob": 0.05, "desc": "seguir_rastros"},
            # Vestigios de pasos que otros usaron — post-arcaico
        },
        "peligro_fisico":   0.50,      # Muy peligroso sin conocimiento
        "capacidad_sustento": 5,
        "regeneracion_base": 0.003,
    },

    "colinas_suaves": {
        "color_mapa":       "#A9B18F",
        "traversia":        0.70,
        "recursos_visibles": {
            "piedra_media":  0.65,
            "pasto_mixto":   0.60,
            "arbustos_fruto": 0.45,
            "vista_panoramica": True,  # Permite ver más hexs adyacentes
        },
        "fauna_visible": {
            "pequena":       0.50,
            "grande":        0.40,
        },
        "recursos_ocultos": {
            "pedernal_calidad": {"prob": 0.30, "desc": "busqueda_piedra"},
            "manantial":     {"prob": 0.25, "desc": "exploracion"},
            "refugio_natural": {"prob": 0.20, "desc": "exploracion"},
            "ocre_deposito": {"prob": 0.15, "desc": "busqueda_minerales"},
            # El ocre — primer pigmento — aparece en colinas con depósitos ferrosos
        },
        "capacidad_sustento": 30,
        "regeneracion_base": 0.03,
    },
}
```

---

## IV. RECURSOS OCULTOS — Taxonomía Completa

### Las cuatro categorías de ocultamiento

```python
CATEGORIAS_OCULTAMIENTO = {

    "INVISIBLE_TOTAL": {
        "descripcion": "No existe en el mapa del agente hasta ser descubierto.",
        "ejemplos": ["mena_cobre", "vena_agua_subterranea", "oasis"],
        "mecanismo": "Requiere acción específica de búsqueda en zona correcta.",
        "condicion": "El agente tiene que estar EN el hexágono Y ejecutar"
                    " la acción de búsqueda correcta.",
    },

    "VISIBLE_SIN_VALOR": {
        "descripcion": "Existe y es perceptible pero su utilidad no se conoce.",
        "ejemplos": ["arcilla", "ocre", "turba", "semillas_cultivables",
                    "conchas"],
        "mecanismo": "El agente ve el recurso pero no sabe qué hacer con él."
                    " El descubrimiento es del USO, no del objeto.",
        "condicion": "Perfil correcto (apertura + observación) + tiempo"
                    " + posiblemente un trigger (necesidad concreta).",
    },

    "CONDICIONAL": {
        "descripcion": "Solo existe bajo ciertas condiciones ambientales.",
        "ejemplos": ["sal_evaporacion", "agua_temporal", "hongos_estacionales"],
        "mecanismo": "Aparece en verano, en sequía, en la oscuridad."
                    " Si el agente no está ahí en el momento correcto, no existe.",
        "condicion": "Estar en el lugar correcto + momento correcto del año.",
    },

    "MEDIADO_POR_FAUNA": {
        "descripcion": "Solo se descubre siguiendo el comportamiento animal.",
        "ejemplos": ["sal_mineral", "pozo_natural", "plantas_medicinales"],
        "mecanismo": "Los animales van a la sal, al agua, a las plantas."
                    " Observar a los animales revela el recurso.",
        "condicion": "Observación sostenida de fauna + capacidad de inferencia.",
        "nota": "Este mecanismo es históricamente documentado —"
               " los humanos aprendieron botánica medicinal en parte"
               " observando qué comían los animales enfermos.",
    },
}
```

### Los recursos que cambian todo — Hitos de Descubrimiento

```python
HITOS_DESCUBRIMIENTO = {

    "sal": {
        "impacto":        "REVOLUCIONARIO",
        "por_que":        "Conservación de alimentos → fin de la escasez estacional"
                         " → primer bien de intercambio universal",
        "derivados":      ["conservacion_carne", "comercio", "poder_quien_controla"],
        "campo_simbolico": "La sal como pureza, valor, alianza — universal",
        "tiempo_estimado_descubrimiento": "50–200 días simulados",
    },

    "cobre_nativo": {
        "impacto":        "CIVILIZACIONAL",
        "por_que":        "Primer metal → herramientas superiores → división trabajo"
                         " → acumulación de valor → jerarquía económica formal",
        "requiere_previo": ["herramienta_piedra", "fuego_controlado"],
        "derivados":      ["herrería_primitiva", "adorno_metal", "comercio_metal"],
        "tiempo_estimado": "Años simulados — post-arcaico temprano",
    },

    "semillas_cultivables": {
        "impacto":        "REVOLUCIONARIO",
        "por_que":        "Posibilidad de agricultura → sedentarismo → todo cambia",
        "requiere_previo": ["conocimiento_botanico", "valle_fértil_cercano"],
        "derivados":      ["agricultura_primitiva", "almacenamiento", "propiedad"],
        "tiempo_estimado": "Cientos de días — requiere conocimiento acumulado",
        "nota":           "La agricultura no ocurre de golpe —"
                         " hay un período largo de proto-cultivo"
                         " antes de que sea un sistema",
    },

    "navegacion_basica": {
        "impacto":        "EXPANSIVO",
        "por_que":        "Acceso al otro lado del río/lago → territorio duplicado"
                         " → contacto con grupos aislados",
        "requiere_previo": ["madera_trabajada", "cuerda"],
        "derivados":      ["balsa", "canoa_simple", "comercio_lacustre"],
        "desbloquea":     "El 30% del mapa que los ríos/lagos bloqueaban",
    },

    "cueva_ritual": {
        "impacto":        "SIMBOLICO_MASIVO",
        "por_que":        "La oscuridad absoluta + resonancia + aislamiento ="
                         " primera experiencia colectiva de lo numinoso"
                         " sin mediación del mundo exterior",
        "requiere_previo": "Explorar cueva profunda + agente con sabio/trickster alto",
        "derivados":      ["ritual_cueva", "arte_rupestre", "espacio_sagrado",
                          "rol_chamán"],
        "campo_simbolico": "Disparo masivo de proto-mitos — el mayor catalizador"
                          " simbólico disponible en el mapa",
    },

    "conchas_ornamento": {
        "impacto":        "SIMBOLICO_COMERCIAL",
        "por_que":        "Primer objeto de valor puramente simbólico"
                         " que viaja entre grupos — el embrión del dinero",
        "requiere_previo": "Acceso a costa + reconocimiento de valor ornamental",
        "derivados":      ["ornamento_personal", "regalo_intergrupal",
                          "valor_de_intercambio"],
        "nota":           "Las conchas aparecen a 500km de la costa en yacimientos"
                         " de hace 130.000 años — viajaban como valor",
    },

    "ocre_pigmento": {
        "impacto":        "SIMBOLICO_FUNDACIONAL",
        "por_que":        "Primer material de uso exclusivamente simbólico"
                         " → marca de identidad → diferenciación grupal"
                         " → arte → comunicación no-verbal",
        "requiere_previo": "Encontrar depósito + agente con apertura muy alta",
        "derivados":      ["pintura_corporal", "marca_muertos", "identidad_grupal",
                          "arte_primitivo"],
        "nota":           "El rojo = sangre = vida. El ocre es rojo."
                         " La ecuación es universal y pre-lingüística.",
    },
}
```

---

## V. SISTEMA DE EXPLORACIÓN Y DESCUBRIMIENTO

### 5.1 El Mapa del Agente vs. El Mapa Real

```python
class WorldMap:
    """El mundo real — completo desde el día 0."""
    hexagons: dict[Coord, Hexagon]  # Todos los hexágonos con todos sus recursos
    
class AgentKnowledgeMap:
    """Lo que sabe el agente — incompleto, crece con exploración."""
    
    known_hexagons: dict[Coord, KnownHexagon]
    # KnownHexagon solo tiene los recursos que el agente descubrió
    
    visibility_radius: int = 2  # Hexs visibles desde posición actual
    # (más alto si está en colinas/montaña con vista panorámica)
    
    def explore(self, agent, hexagon):
        """
        Explorar un hexágono revela sus recursos visibles.
        Los ocultos requieren acción adicional.
        """
        known = KnownHexagon(coord=hexagon.coord)
        
        # Recursos visibles se revelan automáticamente
        for recurso, cantidad in hexagon.recursos_visibles.items():
            known.recursos[recurso] = cantidad
        
        # Recursos ocultos requieren condiciones
        for recurso, config in hexagon.recursos_ocultos.items():
            if self.check_discovery_conditions(agent, recurso, config, hexagon):
                prob = config["prob_deposito"] * self.get_discovery_modifier(agent)
                if random.random() < prob:
                    known.recursos[recurso] = hexagon.recursos_ocultos_cantidades[recurso]
                    self.trigger_discovery_event(agent, recurso, hexagon)
        
        self.known_hexagons[hexagon.coord] = known

class CollectiveKnowledgeMap:
    """
    El mapa colectivo del grupo — la suma del conocimiento de todos.
    No todos saben lo mismo, pero el grupo como entidad sí.
    """
    # Un agente puede ir a un recurso que él no conoce
    # si otro miembro del grupo lo conoce y lo guía
    collective_known: dict[Coord, set[str]]  # coord → recursos conocidos por alguien
    knowledge_holder: dict[str, str]  # recurso_key → agent_id quien lo sabe
```

### 5.2 Rango de Movimiento y Exploración

```python
MOVIMIENTO = {
    "velocidad_base":       1.0,   # Hexs por día
    "con_carga_pesada":     0.5,
    "terreno_dificil":      0.3,   # Montaña, pantano
    
    "rango_exploracion_diaria": {
        # Cuántos hexs puede explorar un agente en un día
        # (no solo cruzar — explorar con atención)
        "sin_carga":        1,     # Explora el hex actual + adyacentes
        "con_mision":       0,     # Si tiene misión específica, se queda
    },
    
    "modificadores_perfil": {
        "exploración_alta":     +0.20,   # Módulo neural exploración > 0.70
        "apertura_alta":        +0.15,
        "heroe_alto":           +0.10,
        "responsabilidad_alta": -0.10,   # Prefiere quedarse
        "ansiedad_alta":        -0.20,   # No sale del área conocida
        "madre_alta":           -0.15,   # Prioriza quedarse con el grupo
    },
}
```

### 5.3 El Conocimiento Viaja con los Agentes

```python
def on_agent_death(agent, grupo):
    """
    Cuando un agente muere, su conocimiento geográfico
    puede perderse si nadie más lo sabe.
    """
    for coord, known_hex in agent.knowledge_map.items():
        for recurso in known_hex.recursos:
            # Verificar si alguien más lo sabe
            otros_que_saben = [
                a for a in grupo.agentes_vivos
                if recurso in a.knowledge_map.get(coord, {}).recursos
            ]
            
            if not otros_que_saben:
                # Pérdida de conocimiento geográfico
                events_log.register(
                    tipo="perdida_conocimiento_geografico",
                    recurso=recurso,
                    coord=coord,
                    agente_fallecido=agent.id
                )
                # El grupo tendrá que redescubrirlo
```

---

## VI. CHECKPOINT DEL MUNDO — WorldState

### Lo que hay que serializar para reanudar

```python
@dataclass
class WorldCheckpoint:
    """
    El estado completo del mundo en un momento dado.
    Suficiente para reproducirlo exactamente.
    """
    
    # ESTADO DE CADA HEXÁGONO
    hexagon_states: dict[str, HexagonState]
    # Por cada hex: recursos actuales (pueden diferir del base por presión),
    #               fauna actual, degradación acumulada,
    #               quién estuvo aquí y cuándo,
    #               recursos descubiertos hasta ahora
    
    # ESTADO DE FAUNA GLOBAL
    fauna_populations: dict[str, FaunaState]
    # Por especie: densidad actual por zona, tendencia migratoria,
    #              presión de caza acumulada
    
    # FUEGO — Si existe
    fire_state: dict | None
    # Si está activo: hexágono, cuidador, ciclos activo,
    #                 radio de influencia, riesgo de propagación
    
    # CONOCIMIENTO COLECTIVO
    collective_knowledge_map: dict[str, set]
    # coord → recursos conocidos por alguien en el grupo
    
    # MODIFICACIONES PERMANENTES
    permanent_changes: list[WorldChange]
    # Zonas quemadas, agotadas, o transformadas permanentemente
    
    # RECURSOS GLOBALES — Índices agregados
    global_resource_index: dict[str, float]
    # {"comida_total": 0.62, "agua_total": 0.85, "madera_total": 0.71}
    # Para evaluación rápida de viabilidad del grupo
    
    # METADATA
    dia_simulado: int
    presion_acumulada_por_zona: dict[str, float]
    zonas_sobrexplotadas: list[str]
    
    def get_carrying_capacity_actual(self) -> int:
        """
        ¿Cuántas personas puede sostener el territorio
        conocido por el grupo en este momento?
        """
        known_hexs = self.collective_knowledge_map.keys()
        return sum(
            BIOMAS[self.hexagon_states[h].bioma]["capacidad_sustento"]
            * self.hexagon_states[h].recurso_factor
            for h in known_hexs
        )
```

---

## VII. DINÁMICA DE REGENERACIÓN Y AGOTAMIENTO

### El mundo respira — ciclos de 90 días

```python
class WorldDynamics:
    
    def daily_update(self, world, climate, grupo):
        """
        El mundo se actualiza cada día simulado,
        independientemente de lo que haga el grupo.
        """
        self.update_fauna(world, grupo)
        self.update_vegetation(world, climate)
        self.update_water(world, climate)
        self.check_degradation(world)
        self.check_fire(world, climate)
        self.seasonal_events(world, climate)
    
    def update_fauna(self, world, grupo):
        for especie, poblacion in world.fauna.items():
            # Reproducción natural
            crecimiento = poblacion.densidad * poblacion.tasa_reproduccion
            
            # Presión de caza del grupo
            caza = grupo.get_caza_reciente(especie, dias=7)
            
            # Balance
            delta = crecimiento - caza
            poblacion.densidad = np.clip(poblacion.densidad + delta, 0, 1)
            
            # Migración si la presión es muy alta
            if poblacion.densidad < 0.15:
                self.trigger_migracion(especie, world)
                # La migración mueve la densidad a hexs adyacentes menos presionados
    
    def seasonal_transition(self, world, nueva_estacion):
        """
        El cambio de estación modifica los recursos disponibles.
        No es instantáneo — tarda ~7 días en completarse.
        """
        for hex in world.hexagons.values():
            bioma_config = BIOMAS[hex.bioma]
            estacion_config = ESTACIONES[nueva_estacion]
            
            for recurso, mod in estacion_config["efecto_recursos"].items():
                if recurso in hex.recursos:
                    # Transición gradual, no instantánea
                    hex.recursos_objetivo[recurso] = (
                        bioma_config["recursos_visibles"].get(recurso, 0) *
                        (1 + mod)
                    )
                    hex.recursos_en_transicion.add(recurso)
    
    def check_degradation(self, world):
        """
        Algunos daños son permanentes o de recuperación muy lenta.
        """
        for hex in world.hexagons.values():
            if hex.presion_acumulada > 0.85:
                # Degradación permanente
                hex.capacidad_sustento *= 0.90
                hex.regeneracion_rate  *= 0.85
                
                events_log.register(
                    tipo="degradacion_zona",
                    coord=hex.coord,
                    descripcion=f"La zona {hex.coord} ha sido sobrexplotada."
                )
                
                # El campo colectivo lo siente
                collective_field["escasez"]    += 0.10
                collective_field["naturaleza"] += 0.15
                # "La naturaleza respondió" — proto-mito posible
```

---

## VIII. VARIABLES COMPLETAS DEL MUNDO — Checklist

### Por hexágono
- [x] Bioma
- [x] Coordenadas (q, r) axiales
- [x] Recursos visibles con cantidad actual
- [x] Recursos ocultos con probabilidad y condición de descubrimiento
- [x] Fauna actual por categoría
- [x] Tasa de regeneración actual (puede degradarse)
- [x] Capacidad de sustento actual
- [x] Presión acumulada
- [x] Modificador climático propio
- [x] Peligro físico
- [x] Valor simbólico
- [x] Valor estratégico
- [x] ¿Es bloqueador? (ríos, montañas altas)
- [x] ¿Tiene vista panorámica? (colinas, montaña)
- [ ] Historial de ocupación (qué agentes estuvieron aquí) ← **AGREGAR**
- [ ] Modificaciones permanentes (quemado, agotado) ← **AGREGAR**
- [ ] Recursos descubiertos hasta ahora (subconjunto de los ocultos) ← **AGREGAR**

### Global del mundo
- [x] Estado de fauna por especie
- [x] Fuego activo (sí/no, dónde, quién cuida)
- [x] Zonas en degradación
- [x] Estación actual y días en estación
- [x] Mapa de conocimiento colectivo
- [x] Índice de recursos global
- [x] Carrying capacity actual del territorio conocido
- [ ] Temperatura promedio global (para tracking climático) ← **AGREGAR**
- [ ] Eventos climáticos activos (lluvia intensa, sequía) ← **AGREGAR**
- [ ] Rutas conocidas entre hexs (el grupo "aprende" los caminos) ← **AGREGAR**

---

## IX. ESTADO INICIAL — Día 0

```yaml
# world_state_day0.yaml

mapa:
  dimensiones: "80x60 hexagonos"
  sistema_coordenadas: "axial_hexagonal"
  total_hexs: 4800
  
posicion_inicial_grupo:
  coord: [40, 30]     # Centro del mapa
  bioma: "colinas_suaves"
  razon: "Las colinas dan visibilidad + recursos moderados + no extremo"

hexs_visibles_dia0:
  # Solo los hexs dentro del rango de visibilidad inicial (radio 2)
  total: 19           # 1 centro + 6 adyacentes + 12 del anillo exterior
  porcentaje_mapa: "0.4% — el 99.6% es terra incognita"

recursos_conocidos_dia0:
  # Solo los visibles en los 19 hexs iniciales
  piedra_media: 0.65
  pasto_mixto: 0.60
  arbustos_fruto: 0.45
  # Todo lo demás: desconocido

tecnologias_activas: []
fuego_activo: false
mitos_activos: []
rituales_detectados: []
tabus_codificados: []

fauna_inicial:
  herbivoros_pequeños:
    densidad_zona_inicial: 0.55
  herbivoros_grandes:
    densidad_zona_inicial: 0.40

clima_dia0:
  estacion: "primavera"
  temperatura: 16
  precipitacion: 0.45
  luminosidad: 0.70

carrying_capacity_territorio_conocido: 180
# Con 19 hexs de colinas/pradera visible, el grupo puede sostener
# hasta ~180 personas — más que suficiente para comenzar con 15
```

---

## X. PREGUNTAS QUE ESTE MUNDO PUEDE RESPONDER

```
EXPANSIÓN TERRITORIAL
  ¿Cuándo decide el grupo explorar más allá del radio inicial?
  ¿La presión de recursos o la curiosidad impulsa la exploración?
  ¿El primer explorador tiene perfil distinto al del grupo?

DESCUBRIMIENTO
  ¿La sal o el fuego llegan primero?
  ¿El ocre se descubre antes o después de la primera muerte?
  ¿La cueva ritual se encuentra antes de que haya mitos para llenarla?

ADAPTACIÓN
  ¿El grupo sigue a la fauna cuando migra o innova para quedarse?
  ¿La degradación de una zona cambia el comportamiento del grupo?

GEOGRAFÍA Y CULTURA
  ¿El río divide al grupo antes o después de que tengan mitos distintos?
  ¿Los grupos separados por montaña desarrollan tabúes diferentes?
  ¿El control del lago se convierte en poder político?
```

---

*Psyche Simulacra — El Mundo v1.0*  
*El mundo existe completo desde el momento cero.*  
*Son los agentes quienes van a transformarlo todo.*
