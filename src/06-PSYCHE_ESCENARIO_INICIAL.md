# PSYCHE SIMULACRA — Variables del Escenario Inicial
## Recursos, Clima Base y Sistema de Tecnología Emergente

> *El escenario no es un mapa con objetos estáticos.  
> Es un sistema dinámico que respira, fluctúa y responde  
> a lo que el grupo le hace — o le deja de hacer.*

---

## I. FILOSOFÍA DEL ESCENARIO

Tres principios que gobiernan todo el diseño de recursos:

**1. La abundancia y la escasez son cíclicas, no constantes.**
Un grupo que siempre tiene hambre muere. Un grupo que nunca tiene hambre
no genera urgencia simbólica. La fluctuación es el motor del drama.

**2. El recurso no existe hasta que el grupo lo reconoce.**
El fuego existía antes de que alguien lo controlara.
Los hongos medicinales existían antes de que alguien los usara.
Un recurso solo entra al sistema cuando un agente con el perfil
adecuado lo descubre — antes, es parte del fondo invisible del entorno.

**3. El entorno responde al grupo.**
La caza excesiva reduce la fauna. El fuego mal controlado
destruye vegetación. El grupo no está en el escenario —
está en relación con él.

---

## II. EL MAPA — Zonas del Escenario Arcaico

### Topología base (beta)

Para beta, el mapa es conceptual — no tiene coordenadas pixel a pixel.
Son **zonas con propiedades** que determinan qué recursos contienen,
qué clima reciben, y qué capacidades requiere acceder a ellas.

```
ZONAS DEL ESCENARIO INICIAL
────────────────────────────────────────────────────────

  [BOSQUE]          [PRADERA]         [RÍO / LAGO]
  Recursos:         Recursos:         Recursos:
  - Frutos          - Animales        - Agua fresca
  - Raíces          - Plantas         - Peces
  - Refugio         - Exposición      - Arcilla
  - Leña            - Vista larga     - Juncos
  Clima: templado   Clima: variable   Clima: húmedo
  Riesgo: bajo      Riesgo: medio     Riesgo: bajo

  [MONTAÑA / ROCA]  [ZONA QUEMADA]
  Recursos:         Recursos:
  - Piedra          - Ceniza (fértil)
  - Vistas          - Carbón
  - Refugio alto    - Espacio abierto
  Clima: frío       Nota: emerge por evento
  Riesgo: alto      (fuego no controlado)
```

### Movilidad entre zonas

Los agentes se mueven entre zonas según su schedule y necesidades.
La zona donde se encuentran dos agentes determina el contexto
de su interacción — y el contexto modula el colapso cuántico.

```python
ZONA_MODIFICADORES = {
    "bosque": {
        "introversion":     +0.15,   # El bosque aísla, favorece reflexión
        "proto_simbolos":   +0.10,   # Más probabilidad de experiencia numinosa
        "cooperacion":      -0.05,   # Más difícil coordinar en terreno cerrado
    },
    "pradera": {
        "sociabilidad":     +0.20,   # Espacio abierto, más interacciones
        "agresividad":      +0.10,   # Exposición, tensión territorial
        "exploracion":      +0.15,
    },
    "rio_lago": {
        "calma":            +0.20,   # El agua calma
        "ritual_prob":      +0.15,   # El agua como primer espacio sagrado
        "vinculo":          +0.10,   # Las interacciones en el río son más íntimas
    },
    "montaña": {
        "perspectiva":      +0.25,   # Literalmente ve más
        "proto_simbolos":   +0.20,   # Las alturas como espacio numinoso
        "riesgo_fisico":    +0.30,
    }
}
```

---

## III. RECURSOS — Variables y Dinámicas

### 3.1 Comida

#### Tipos de alimento arcaico

```python
FUENTES_ALIMENTO = {
    "frutos_silvestres": {
        "zona":             "bosque",
        "disponibilidad":   "estacional",  # Solo en primavera/verano
        "abundancia_base":  0.70,
        "requiere":         "recoleccion",
        "calorias":         0.40,          # Bajo valor calórico
        "riesgo":           0.05,          # Casi ninguno
        "decay_sin_consumir": 0.15,        # Se pudre rápido
    },
    "raices_tuberculos": {
        "zona":             "bosque_pradera",
        "disponibilidad":   "todo_el_año",
        "abundancia_base":  0.55,
        "requiere":         "conocimiento_basico",  # Saber cuáles son comibles
        "calorias":         0.60,
        "riesgo":           0.10,          # Algunas son venenosas sin conocimiento
        "decay_sin_consumir": 0.03,        # Duran más
    },
    "caza_menor": {
        "zona":             "pradera_bosque",
        "disponibilidad":   "variable",    # Depende de migración animal
        "abundancia_base":  0.45,
        "requiere":         "caza_cooperativa",
        "calorias":         0.80,
        "riesgo":           0.15,
        "decay_sin_consumir": 0.25,        # Se pudre en días
        "efecto_colectivo": "ritual_caza", # La caza exitosa genera proto-ritual
    },
    "peces": {
        "zona":             "rio_lago",
        "disponibilidad":   "estacional_alta",
        "abundancia_base":  0.65,
        "requiere":         "pesca_basica",
        "calorias":         0.70,
        "riesgo":           0.05,
        "decay_sin_consumir": 0.30,
        "bonus_social":     0.10,          # Pescar es actividad social
    },
    "miel": {
        "zona":             "bosque",
        "disponibilidad":   "rara",        # 10% de días en verano
        "abundancia_base":  0.20,
        "requiere":         "descubrimiento",  # Alguien tiene que encontrarla
        "calorias":         0.90,
        "riesgo":           0.25,          # Las abejas
        "valor_simbolico":  0.80,          # Alto — primera experiencia de dulce intenso
        "decay_sin_consumir": 0.01,        # No se pudre
        # El descubrimiento de miel tiene alta probabilidad de generar proto-ritual
    }
}
```

#### Dinámica de abundancia/escasez

```python
class FoodSystem:
    
    def calcular_abundancia(self, zona, estacion, dias_desde_ultima_caza):
        """
        La abundancia no es estática.
        Fluctúa por estación, por presión de caza, y por eventos climáticos.
        """
        base = FUENTES_ALIMENTO[zona]["abundancia_base"]
        
        # Modificador estacional
        mod_estacion = ESTACION_MODIFICADORES[estacion][zona]
        
        # Presión de caza — si cazaron mucho, los animales migran o escasean
        presion = self.calcular_presion_caza(dias_desde_ultima_caza)
        
        # Evento climático reciente
        mod_clima = self.get_clima_modificador()
        
        return np.clip(base * mod_estacion * (1 - presion) * mod_clima, 0, 1)
    
    def regenerar(self):
        """
        Los recursos se regeneran si el grupo los presiona poco.
        La sobrexplotación los destruye.
        """
        for zona in self.zonas:
            if zona.presion_actual < 0.30:
                zona.abundancia = min(1.0, zona.abundancia + 0.02)
            elif zona.presion_actual > 0.70:
                zona.abundancia = max(0.0, zona.abundancia - 0.05)
```

---

### 3.2 Agua

El agua es diferente a la comida: más crítica a corto plazo, más estable.

```python
AGUA = {
    "fuentes": {
        "rio_lago": {
            "disponibilidad":  "permanente",   # Excepto en sequía extrema
            "abundancia_base": 0.90,
            "riesgo":          0.10,           # Contaminación natural
            "distancia_grupo": "variable",     # El grupo se aleja en nomadismo
        },
        "lluvia": {
            "disponibilidad":  "estacional",
            "abundancia_base": "depende_clima",
            "recolectable":    False,          # Sin tecnología no se almacena
        },
        "rocio_plantas": {
            "disponibilidad":  "matutina",
            "abundancia_base": 0.20,           # Complemento, no fuente principal
            "requiere":        "conocimiento",
        }
    },
    
    "consumo_diario_agente": 0.15,  # Unidades por día
    "critico_sin_agua":      2,     # Días hasta deterioro de salud
    "letal_sin_agua":        5,     # Días hasta muerte
    
    # El agua como primer espacio sagrado
    "valor_simbolico_rio":   0.60,  # Los ríos tienen alta carga simbólica arcaica
}
```

---

### 3.3 Fauna — Animales como Sistema, No como Objetos

Los animales no son ítems estáticos esperando ser cazados.
Son una población con su propia dinámica.

```python
class FaunaSystem:
    """
    La fauna es una población que responde a la presión del grupo.
    No hay animales individuales en beta — hay densidad poblacional por zona.
    """
    
    def __init__(self):
        self.poblaciones = {
            "herbivoros_pequeños": {  # Conejos, roedores, aves
                "densidad":        0.70,
                "tasa_reproduccion": 0.05,  # Por semana simulada
                "movilidad":       "alta",  # Se mueven entre zonas
                "calorias_caza":   0.40,
                "dificultad_caza": 0.30,
            },
            "herbivoros_grandes": {   # Ciervos, jabalíes
                "densidad":        0.40,
                "tasa_reproduccion": 0.02,
                "movilidad":       "media",
                "calorias_caza":   0.90,
                "dificultad_caza": 0.65,
                "requiere":        "caza_cooperativa",  # Solo en grupo
                "valor_simbolico": 0.70,  # Alta carga ritual
                # La caza mayor genera los primeros rituales documentados
                # en poblaciones históricas
            },
        }
    
    def responder_a_presion(self, caza_semanal):
        """
        Si el grupo caza más de lo que la población regenera,
        los animales migran o su densidad cae.
        Eso es una consecuencia emergente — nadie la programa como evento.
        """
        for especie, datos in self.poblaciones.items():
            presion = caza_semanal.get(especie, 0)
            regeneracion = datos["densidad"] * datos["tasa_reproduccion"]
            
            if presion > regeneracion:
                datos["densidad"] -= (presion - regeneracion) * 0.5
                if datos["densidad"] < 0.20:
                    self.trigger_migracion(especie)
            else:
                datos["densidad"] = min(1.0, datos["densidad"] + regeneracion)
    
    def trigger_migracion(self, especie):
        """
        Cuando la densidad cae demasiado, la especie migra.
        El grupo tiene que seguirla (nomadismo forzado)
        o encontrar otras fuentes (innovación forzada).
        """
        # Efecto en campo colectivo
        collective_field["escasez"]  += 0.25
        collective_field["miedo"]    += 0.15
        
        # Presión para descubrimiento tecnológico
        # Si el grupo no puede seguir cazando lo mismo,
        # aumenta la probabilidad de que alguien pruebe algo nuevo
        self.presion_innovacion += 0.30
```

---

### 3.4 Materiales — Lo que Permite la Tecnología

```python
MATERIALES_ARCAICOS = {
    "piedra": {
        "zona":        "montaña_rio",
        "abundancia":  0.90,           # Muy abundante
        "uso_base":    "ninguno",      # Sin tecnología no se usa
        "uso_potencial": ["herramienta_corte", "arma", "raspador"],
        "requiere_descubrimiento": True,
    },
    "madera": {
        "zona":        "bosque",
        "abundancia":  0.80,
        "uso_base":    "leña_refugio",
        "uso_potencial": ["lanza", "arco", "recipiente"],
        "requiere_descubrimiento": True,
    },
    "hueso": {
        "zona":        "post_caza",    # Solo disponible tras caza exitosa
        "abundancia":  "variable",
        "uso_base":    "ninguno",
        "uso_potencial": ["aguja", "anzuelo", "flauta"],
        "requiere_descubrimiento": True,
        "valor_simbolico": 0.60,       # Los huesos son simbólicamente cargados
    },
    "arcilla": {
        "zona":        "rio_lago",
        "abundancia":  0.60,
        "uso_base":    "ninguno",
        "uso_potencial": ["recipiente", "sellado_refugio"],
        "requiere_descubrimiento": True,
    },
    "fibras_vegetales": {
        "zona":        "pradera_bosque",
        "abundancia":  0.70,
        "uso_base":    "ninguno",
        "uso_potencial": ["cuerda", "cesteria", "ropa_basica"],
        "requiere_descubrimiento": True,
    },
    "ocre_pigmentos": {
        "zona":        "montaña_rio",
        "abundancia":  0.30,
        "uso_base":    "ninguno",
        "uso_potencial": ["pintura_corporal", "marca_simbolica"],
        "requiere_descubrimiento": True,
        "valor_simbolico": 0.90,       # Los pigmentos tienen altísima carga
        # El ocre es el primer material con uso exclusivamente simbólico
        # documentado en arqueología — 100.000 años atrás
    },
}
```

---

## IV. CLIMA BASE DEL ESCENARIO

### 4.1 Ciclo Estacional

```python
ESTACIONES = {
    "primavera": {
        "duracion_dias":    90,
        "temperatura":      (12, 22),      # Rango °C
        "precipitacion":    0.55,          # Moderada
        "luminosidad":      0.70,
        "efecto_recursos": {
            "frutos":        +0.40,
            "fauna":         +0.25,         # Cría de animales
            "agua":          +0.20,
        },
        "efecto_agentes": {
            "humor_base":    +0.15,
            "energia":       +0.10,
            "sociabilidad":  +0.20,         # Más interacciones
        },
        "notas": "Época de abundancia relativa. Mayor probabilidad de surplus."
    },
    "verano": {
        "duracion_dias":    90,
        "temperatura":      (22, 38),
        "precipitacion":    0.25,          # Seco
        "luminosidad":      0.95,
        "efecto_recursos": {
            "frutos":        +0.60,         # Pico de abundancia
            "fauna":         -0.10,         # Animales buscan agua
            "agua":          -0.20,         # Fuentes se reducen
        },
        "efecto_agentes": {
            "humor_base":    +0.10,
            "agresividad":   +0.15,         # Calor → irritabilidad
            "impulsividad":  +0.10,
        },
        "notas": "Abundancia de frutos pero escasez de agua. Tensión territorial."
    },
    "otoño": {
        "duracion_dias":    90,
        "temperatura":      (8, 18),
        "precipitacion":    0.60,
        "luminosidad":      0.55,
        "efecto_recursos": {
            "frutos":        -0.30,         # Declinando
            "fauna":         +0.40,         # Migración — caza alta
            "agua":          +0.30,
        },
        "efecto_agentes": {
            "humor_base":    -0.05,
            "prevision":     +0.20,         # El grupo "siente" que viene el invierno
            "cohesion":      +0.15,         # Preparación colectiva
        },
        "notas": "Temporada de caza mayor. Alta cohesión grupal. Primeros surplus."
    },
    "invierno": {
        "duracion_dias":    90,
        "temperatura":      (-5, 8),
        "precipitacion":    0.40,          # Nieve posible
        "luminosidad":      0.30,
        "efecto_recursos": {
            "frutos":        -0.90,         # Prácticamente nada
            "fauna":         -0.50,         # Hibernación o migración
            "agua":          -0.30,         # Congelada o reducida
        },
        "efecto_agentes": {
            "humor_base":    -0.25,
            "ansiedad":      +0.20,
            "introspección": +0.30,         # El invierno obliga al interior
            "proto_simbolos":+0.25,         # Más sueños, más símbolos
        },
        "notas": "Escasez. Alta mortalidad infantil. Máxima actividad onírica y simbólica.",
        "riesgo_muerte":    0.40,           # Modificador de riesgo estacional
    }
}
```

### 4.2 El Invierno como Catalizador Simbólico

El invierno merece atención especial.

Los pueblos arcaicos históricos concentran su producción simbólica
en los meses de invierno — no porque tengan más tiempo,
sino porque la presión existencial + el encierro + la oscuridad
activan el procesamiento onírico y la narración.

Las mitologías del hemisferio norte tienen una densidad simbólica
radicalmente mayor en sus relatos de invierno.
El solsticio de invierno es el evento ritual más universal conocido.

```python
def winter_symbolic_amplification(agent, campo_colectivo):
    """
    En invierno, la actividad simbólica se amplifica.
    No es un bonus arbitrario — es la presión existencial
    convirtiendo la oscuridad en símbolo.
    """
    if simulation.clock.estacion == "invierno":
        
        # Los sueños son más intensos
        agent.dream_probability    *= 1.80
        agent.dream_intensity      *= 1.50
        
        # Los proto-símbolos tienen más probabilidad de cristalizar
        campo_colectivo.cristalizacion_threshold *= 0.75
        
        # La narración emerge — el grupo habla más alrededor del fuego
        # (si ya descubrieron el fuego)
        if "fuego" in simulation.tecnologias_activas:
            agent.narracion_probability *= 2.0
            # La narración alrededor del fuego es el origen de la mitología
```

---

## V. TECNOLOGÍA — Sistema de Emergencia

### 5.1 La Pregunta Fundamental

> ¿Dejamos que la tecnología emerja sola, o la prefijamos?

**Respuesta: ni una cosa ni la otra.**

Si la dejamos emerger completamente libre, puede no aparecer nunca
en una simulación de días. Si la prefijamos por calendario, es scripting.

**La solución:** la tecnología ocurre cuando se dan simultáneamente
**tres condiciones convergentes**. Sin las tres juntas, no ocurre.

```
CONDICIÓN 1 — PRESIÓN DEL PROBLEMA
  El grupo enfrenta un problema que su conducta actual no puede resolver.
  Ejemplo: la fauna migró y no hay suficiente proteína.
  Sin presión, no hay innovación.

CONDICIÓN 2 — AGENTE CON PERFIL ADECUADO
  Debe existir un agente con la combinación arquetípica/rasgo correcta.
  Ejemplo: exploración_neural > 0.70 + apertura > 0.75 + trickster > 0.60
  Sin el individuo adecuado, la presión no produce solución.

CONDICIÓN 3 — TIEMPO DE EXPLORACIÓN DISPONIBLE
  El agente tiene que tener tiempo no comprometido con sobrevivencia básica.
  Si todos están en modo crisis de hambre, nadie experimenta.
  Hay que tener margen — aunque sea pequeño.
```

### 5.2 El Árbol de Tecnología Arcaica

No es un árbol de habilidades de videojuego.
Es un mapa de dependencias lógicas:
algunas tecnologías son imposibles sin otras previas.

```
NIVEL 0 — Conducta innata (no requiere descubrimiento)
  ✓ Uso de ramas como palancas básicas
  ✓ Uso de piedras como proyectiles sin tallar
  ✓ Refugio bajo saliente rocoso o árbol denso
  ✓ Recolección de frutos obvios

NIVEL 1 — Primeras innovaciones (Probabilidad alta, ocurren pronto)
  → Piedra tallada básica (percutor)
     Presión: necesidad de cortar/raspar
     Perfil: exploración alta + observación
     Requiere: acceso a piedra + tiempo
     
  → Lanza de madera simple
     Presión: caza ineficiente
     Perfil: héroe alto + exploración
     Requiere: madera + piedra tallada (o no — punta endurecida al fuego)
     
  → Refugio construido básico (ramas + hojas)
     Presión: frío / lluvia
     Perfil: responsabilidad alta + madre alto
     Requiere: madera + fibras

NIVEL 2 — Innovaciones medias (Probabilidad media, requieren Nivel 1)
  → Control del fuego ★
     Presión: frío extremo O necesidad de cocinar para más calorías
     Perfil: exploración > 0.75 + apertura > 0.70 + trickster > 0.55
     Requiere: piedra tallada (para chispa) O presenciar rayo/fuego natural
     Tiempo: largo — múltiples intentos fallidos antes del éxito
     NOTA: El fuego es el umbral más importante de la simulación.
           Es simultáneamente tecnología y símbolo.
           Su descubrimiento debería disparar el primer gran evento
           del campo colectivo.
     
  → Recipiente (corteza, cuero, arcilla cruda)
     Presión: necesidad de transportar agua / almacenar
     Perfil: responsabilidad + exploración
     Requiere: post-caza (cuero) O acceso a arcilla
     
  → Cuerda de fibras
     Presión: necesidad de atar, construir, cargar
     Perfil: responsabilidad alta + apertura
     Requiere: fibras vegetales + tiempo de experimentación

NIVEL 3 — Innovaciones complejas (Probabilidad baja, requieren Nivel 2)
  → Anzuelo de hueso
     Presión: pesca ineficiente
     Requiere: hueso + herramienta de corte + cuerda
     
  → Arco y flecha (FUERA DE BETA)
     Complejidad demasiado alta para primera fase
     
  → Cerámica básica (FUERA DE BETA)
     Requiere fuego controlado + arcilla + tiempo extenso

NIVEL SIMBÓLICO — Tecnología no-material (puede ocurrir en cualquier nivel)
  → Marca con ocre (pintura corporal / señal)
     Presión: necesidad de distinguir "nosotros" de "ellos"
             O ritual de duelo O celebración de caza
     Perfil: apertura > 0.80 + sabio/trickster alto
     Requiere: ocre/pigmento + evento emocional cargado
     Valor: ALTÍSIMO para el campo simbólico
     
  → Entierro de muertos
     Presión: primera muerte + duelo colectivo sin protocolo
     Perfil: sabio alto + madre alta en el grupo
     Requiere: nada material — solo duelo y tiempo
     Valor: primer proto-ritual garantizado si hay muerte
     
  → Narración oral
     Presión: necesidad de transmitir experiencia (caza exitosa, lugar peligroso)
     Perfil: trickster alto O sabio alto + extraversión
     Requiere: nada material
     Valor: el origen de toda mitología posterior
```

### 5.3 El Motor de Descubrimiento

```python
class TechnologyEngine:
    
    def check_discovery_conditions(self, tecnologia, agente, grupo):
        """
        Evalúa si se dan las tres condiciones simultáneamente.
        Devuelve una probabilidad de descubrimiento por día.
        """
        config = TECNOLOGIA_CONFIG[tecnologia]
        
        # CONDICIÓN 1: Presión del problema
        presion = self.calcular_presion(config["presion_trigger"], grupo)
        if presion < 0.40:
            return 0.0  # Sin presión suficiente, imposible
        
        # CONDICIÓN 2: Agente adecuado
        perfil_match = self.evaluar_perfil(agente, config["perfil_requerido"])
        if perfil_match < 0.50:
            return 0.0  # El agente no tiene el perfil
        
        # CONDICIÓN 3: Tiempo disponible
        tiempo_libre = 1.0 - agente.tiempo_comprometido
        if tiempo_libre < 0.20:
            return 0.0  # Sin margen de exploración
        
        # Las tres condiciones se multiplican — ninguna compensa otra
        prob_base = config["probabilidad_base"]
        prob_final = prob_base * presion * perfil_match * tiempo_libre
        
        # El fracaso previo aumenta probabilidad (aprendizaje por error)
        intentos_previos = self.get_intentos(agente, tecnologia)
        prob_final *= (1 + intentos_previos * 0.15)
        
        return min(prob_final, 0.80)  # Máximo 80% por día
    
    def attempt_discovery(self, agente, tecnologia, grupo):
        prob = self.check_discovery_conditions(tecnologia, agente, grupo)
        
        if random.random() < prob:
            self.trigger_discovery(agente, tecnologia, grupo)
        else:
            # El intento fallido también tiene valor
            agente.intentos_tecnologia[tecnologia] += 1
            # Leve frustración que puede convertirse en motivación
            agente.archetypes["trickster"] += 0.01  # Aumenta irreverencia
    
    def trigger_discovery(self, agente, tecnologia, grupo):
        """
        El momento del descubrimiento es un evento mayor.
        No solo se "desbloquea" la tecnología —
        se convierte en un evento del campo simbólico.
        """
        # Registrar el descubrimiento
        simulation.tecnologias_activas[tecnologia] = {
            "descubridor":   agente.id,
            "dia":           simulation.clock.dia_actual,
            "condiciones":   self.get_condiciones_snapshot(),
        }
        
        # El descubridor gana status en el grupo
        agente.status += 0.20
        agente.archetypes["heroe"] += 0.05   # El descubridor es heroizado
        
        # El conocimiento se transmite — pero no instantáneamente
        self.schedule_knowledge_transfer(tecnologia, agente, grupo)
        
        # Impacto en el campo colectivo
        collective_field.absorb_discovery(tecnologia, agente)
        
        # Log en vault
        vault.registrar_evento(
            tipo="descubrimiento_tecnologico",
            agente=agente,
            tecnologia=tecnologia,
            descripcion=self.generar_narrativa_descubrimiento(agente, tecnologia)
        )
```

### 5.4 Transmisión del Conocimiento

El conocimiento no se comparte instantáneamente.
Un descubrimiento individual tarda en volverse conocimiento grupal.

```python
TRANSMISION_CONOCIMIENTO = {
    "mecanismo":    "observacion_e_imitacion",
    "velocidad":    "lenta",
    
    # Por cada agente del grupo:
    "prob_aprender_por_dia": 0.10,  # 10% por día si observa al descubridor
    
    # Factores que aceleran la transmisión:
    "aceleradores": {
        "bond_fuerte_con_descubridor": +0.15,
        "apertura_alta":               +0.10,
        "exploracion_alta":            +0.08,
        "observacion_directa":         +0.20,  # Estar en la misma zona
    },
    
    # Factores que la bloquean:
    "bloqueadores": {
        "responsabilidad_baja":        -0.10,  # No le interesa aprender
        "conflicto_con_descubridor":   -0.20,
        "crisis_supervivencia_activa": -0.30,  # Muy ocupado sobreviviendo
    },
    
    # El conocimiento puede perderse
    "perdida_por_muerte_unico_portador": True,
    # Si muere el único que sabe hacer fuego antes de transmitirlo,
    # el conocimiento se pierde — hay que redescubrirlo
}
```

### 5.5 El Fuego — Caso Especial

El fuego merece tratamiento especial porque es simultáneamente
la tecnología más impactante y el primer símbolo colectivo mayor.

```python
FUEGO_CONFIG = {
    # Como tecnología
    "efectos_tecnologicos": {
        "calorias_coccion":    +0.30,   # Cocinar aumenta calorías disponibles
        "conservacion":        +0.40,   # Carne cocinada dura más
        "refugio_calor":       +0.50,   # Reduce riesgo de muerte por exposición
        "defensa_fauna":       +0.30,   # Los animales temen el fuego
        "herramientas":        True,    # Desbloquea punta endurecida, carbón
    },
    
    # Como símbolo — ESTO ES LO MÁS IMPORTANTE
    "efectos_simbolicos": {
        "campo_colectivo": {
            "transformacion":  +0.60,   # El fuego = transformación
            "vida":            +0.40,   # Da calor = vida
            "peligro":         +0.30,   # También destruye
            "comunidad":       +0.50,   # Todos se juntan alrededor
        },
        
        # El fuego genera el primer espacio de narración colectiva
        "narración_alrededor_fuego": {
            "prob_narracion_por_noche": 0.70,
            "amplificacion_simbolica":  2.0,
            "proto_mito_prob":          +0.40,
            # Las historias contadas alrededor del fuego tienen
            # el doble de probabilidad de convertirse en mitos
        },
        
        # El fuego como primer ritual
        "ritual_del_fuego": {
            "emerge_si": "fuego_activo_por_7_dias",
            # Si el grupo mantiene el fuego por una semana,
            # emergen comportamientos rituales alrededor de él
            "responsable_del_fuego": True,  # Alguien asume ese rol
            # Ese agente gana status simbólico — proto-sacerdote
        }
    },
    
    # Riesgo
    "puede_perderse": True,          # Si nadie lo cuida, se apaga
    "puede_descontrolarse": True,    # Si se descuida, puede quemar zona
    "prob_perdida_sin_cuidado": 0.25,  # Por noche sin cuidador
}
```

---

## VI. VARIABLES INICIALES — El Estado del Día 1

### Estado del escenario al inicio de la simulación

```yaml
# escenario_inicial.yaml

mapa:
  zonas_activas: ["bosque", "pradera", "rio_lago"]
  zona_campamento_inicial: "bosque_borde"  # Entre bosque y pradera

recursos_iniciales:
  comida:
    frutos_silvestres:    0.65  # Abundancia inicial moderada
    raices:               0.55
    caza_menor:           0.50
    peces:                0.60
  agua:
    rio_disponibilidad:   0.85
  materiales:
    piedra:               0.90  # Abundante pero sin uso todavía
    madera:               0.80
    fibras:               0.70
    ocre:                 0.20  # Raro — cuando alguien lo encuentre, es un evento

fauna:
  herbivoros_pequeños:    0.65
  herbivoros_grandes:     0.40

clima:
  estacion_inicial:       "primavera"  # El mejor punto de partida
  temperatura_dia1:       18           # °C
  precipitacion:          0.40

tecnologias_activas: []  # Ninguna al inicio
  # Nivel 0 (conducta innata) no requiere activación

campo_colectivo_inicial:
  simbolos: {}            # Vacío — todo por construir
  presion_existencial:    0.45  # Media — no trivial, no crítica
  cohesion_grupal:        0.55

grupo:
  tamaño:                 15
  composicion:            "ver_perfiles_agentes.yaml"
```

---

## VII. PREGUNTAS QUE EL ESCENARIO DEBERÍA PODER RESPONDER

```
¿Bajo qué condiciones climáticas emerge el primer proto-ritual?
¿La escasez de fauna lleva al nomadismo o a la innovación tecnológica?
¿El fuego, cuando llega, es siempre un punto de inflexión cultural?
¿El ocre se usa primero para el cuerpo vivo o para el muerto?
¿La narración oral emerge antes o después del primer mito?
¿Qué recurso es el primero en escasear y qué produce esa escasez en el campo?
¿El invierno destruye más al grupo de lo que lo une, o al revés?
```

---

*Psyche Simulacra — Variables del Escenario Inicial v1.0*
