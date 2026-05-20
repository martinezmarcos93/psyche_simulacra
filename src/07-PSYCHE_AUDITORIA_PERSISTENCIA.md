# PSYCHE SIMULACRA — Auditoría de Persistencia
## Variables, Datasets y Sistema de Checkpoint

> *El peor momento para descubrir que falta un dato  
> es después de 600 días simulados.*

---

## I. AUDITORÍA DE DATASETS EXISTENTES

### Lo que ya está definido

| Dataset | Qué captura | Frecuencia | Estado |
|---------|------------|-----------|--------|
| `agent_snapshots` | Estado completo del agente | Por ciclo | ✅ Definido |
| `interactions` | Cada interacción entre agentes | Por evento | ✅ Definido |
| `collective_field_history` | Estado del campo colectivo | Por ciclo | ✅ Definido |
| `events_log` | Eventos significativos | Por evento | ✅ Definido |
| `economy_log` | Transacciones económicas | Por evento | ✅ Definido |
| `climate_log` | Estado climático | Por ciclo | ✅ Definido |
| `dreams_log` | Sueños de cada agente | Por evento | ✅ Definido |
| `mythology_log` | Mitos emergentes | Por evento | ✅ Definido |
| `agent_relations` | Red social en el tiempo | Por ciclo | ✅ Definido |
| `agent_lifecycle` | Nacimientos y muertes | Por evento | ✅ Definido |
| `births_log` | Detalle de nacimientos | Por evento | ✅ Definido |
| `deaths_log` | Detalle de muertes | Por evento | ✅ Definido |

### Lo que falta

| Dataset | Qué captura | Por qué importa | Estado |
|---------|------------|-----------------|--------|
| `simulation_checkpoints` | Estado vivo completo para reanudar | Sin esto no hay persistencia real | ❌ Falta |
| `technology_log` | Árbol tecnológico y transmisión | Sin esto no sabés por qué el grupo pudo o no innovar | ❌ Falta |
| `scenario_state_log` | Estado del escenario físico | Sin esto no reconstruís el contexto de las decisiones | ❌ Falta |
| `schedule_log` | Qué hizo cada agente cada hora | Sin esto perdés granularidad de rutinas | ⚠️ Parcial |
| `needs_log` | Evolución de necesidades biológicas | Hambre/fatiga afectan todo — necesitás la serie temporal | ⚠️ Parcial |
| `archetype_delta_log` | Cada cambio en pesos arquetípicos | Sin esto no podés rastrear la individuación | ❌ Falta |
| `complex_activation_log` | Cuándo y por qué se activó cada complejo | El corazón jungiano — sin esto no ves el inconsciente | ❌ Falta |
| `symbol_propagation_log` | Cómo se contagia un símbolo entre agentes | Sin esto el campo colectivo es una caja negra | ❌ Falta |
| `ritual_log` | Detección y evolución de rituales | Comportamiento repetido → ritual → no hay dataset | ❌ Falta |
| `knowledge_transmission_log` | Quién le enseñó qué a quién | Sin esto la tecnología no tiene historia | ❌ Falta |
| `westermarck_log` | Evolución de aversión por convivencia | Capa A — necesita seguimiento propio | ❌ Falta |
| `session_log` | Metadata de cada sesión de ejecución | Sin esto no sabés qué pasó en qué sesión | ❌ Falta |

---

## II. SISTEMA DE CHECKPOINT — El Más Crítico

### El problema

Los datasets de análisis registran *qué pasó*.
El checkpoint registra *cómo estaba todo* — suficiente para continuar.

Son cosas diferentes.

```
DATASETS DE ANÁLISIS     vs     CHECKPOINT
─────────────────────────────────────────────
Registro histórico              Estado vivo
Para investigar                 Para continuar
Append-only                     Sobreescribe
Puede ser parcial               Tiene que ser completo
SQLite                          JSON + SQLite
```

### Qué tiene que guardar un checkpoint

```python
@dataclass
class SimulationCheckpoint:
    
    # METADATA
    checkpoint_id:      str       # UUID
    dia_simulado:       int       # Día exacto al guardar
    hora_simulada:      int       # Hora del día (0-23)
    timestamp_real:     datetime  # Cuándo se guardó en tiempo real
    session_id:         str       # A qué sesión pertenece
    version_motor:      str       # Versión del código que lo generó
    
    # RELOJ
    reloj: dict = {
        "dia_absoluto":     int,
        "hora_actual":      int,
        "estacion":         str,
        "año_simulado":     int,
        "dia_del_año":      int,
    }
    
    # TODOS LOS AGENTES — Estado vivo completo
    agentes: list[AgentState]
    # Incluye: arquetipos, complejos, rasgos, módulos,
    #          estado cuántico, memoria episódica, vínculos,
    #          necesidades biológicas, estado de duelo,
    #          schedule actual, fase vital, edad exacta
    
    # CAMPO COLECTIVO — Estado vivo completo
    campo_colectivo: dict
    # Incluye: todos los símbolos con carga,
    #          candidatos a mito en evaluación,
    #          estado de cristalización de cada símbolo,
    #          presión emocional acumulada
    
    # RED SOCIAL — Grafo completo
    red_social: dict
    # Incluye: todos los vínculos con su historia,
    #          entrelazamientos activos,
    #          modificadores de opinión con decay acumulado
    
    # ESCENARIO — Estado vivo del entorno
    escenario: dict
    # Incluye: abundancia de cada recurso por zona,
    #          densidad de fauna actual,
    #          estado de cada zona (intacta/degradada),
    #          fuego activo (sí/no, quién lo cuida, ciclos sin cuidado)
    
    # TECNOLOGÍA — Estado del árbol
    tecnologias: dict
    # Incluye: tecnologías descubiertas con metadata,
    #          intentos fallidos por agente por tecnología,
    #          estado de transmisión (quién sabe qué)
    
    # MITOLOGÍA Y RITUALES
    mitologia: dict
    rituales_detectados: list
    tabues_activos: list
    
    # DEMOGRAFÍA
    tamaño_grupo:           int
    zona_demografica:       str
    total_nacimientos:      int
    total_muertes:          int
    
    # ESTADO DE LA SESIÓN
    ciclos_esta_sesion:     int
    tiempo_real_sesion:     float   # Segundos
```

### Cuándo guardar el checkpoint

```python
CHECKPOINT_STRATEGY = {
    
    # Automático — sin intervención del usuario
    "auto_cada_N_dias": 10,        # Cada 10 días simulados
    "auto_fin_sesion":  True,      # Siempre al cerrar (Ctrl+C o timeout)
    "auto_evento_mayor": True,     # Muerte, nacimiento, mito cristalizado
    
    # Protección contra cierre forzado
    "signal_handler": True,        # Captura SIGINT, SIGTERM
    "checkpoint_emergencia": True, # Si el proceso recibe señal de kill,
                                   # guarda lo que puede antes de morir
    
    # Retención
    "mantener_ultimos_N": 5,       # Los 5 checkpoints más recientes
    "mantener_eventos_mayores": True,  # Los checkpoints de eventos
                                        # mayores nunca se borran
}
```

### Implementación del guardado seguro

```python
class CheckpointManager:
    
    def save(self, simulation, reason="auto"):
        """
        Guardado atómico — o guarda todo o no guarda nada.
        Nunca deja un checkpoint parcialmente escrito.
        """
        checkpoint = self.serialize(simulation)
        
        # Primero escribir a archivo temporal
        temp_path = f"{self.checkpoint_dir}/temp_{checkpoint.checkpoint_id}.json"
        final_path = f"{self.checkpoint_dir}/checkpoint_{checkpoint.dia_simulado:05d}.json"
        
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(checkpoint, f, indent=2, ensure_ascii=False,
                     default=self.json_serializer)
        
        # Solo mover al path final si la escritura fue exitosa
        # Esto garantiza que nunca haya un checkpoint corrupto
        os.replace(temp_path, final_path)
        
        # También guardar en SQLite para consultas rápidas
        self.db.insert_checkpoint_metadata(checkpoint)
        
        logger.info(f"Checkpoint guardado: día {checkpoint.dia_simulado} "
                   f"({reason}) → {final_path}")
    
    def load_latest(self):
        """Carga el checkpoint más reciente."""
        checkpoints = sorted(
            glob.glob(f"{self.checkpoint_dir}/checkpoint_*.json"),
            reverse=True
        )
        if not checkpoints:
            raise FileNotFoundError("No hay checkpoints. Primera ejecución.")
        
        return self.deserialize(checkpoints[0])
    
    def verify_integrity(self, checkpoint_path):
        """
        Antes de cargar, verifica que el checkpoint no está corrupto.
        Un checkpoint corrupto es peor que no tener checkpoint.
        """
        try:
            with open(checkpoint_path) as f:
                data = json.load(f)
            
            # Verificar campos críticos
            required = ["checkpoint_id", "dia_simulado", "agentes",
                       "campo_colectivo", "escenario", "reloj"]
            for field in required:
                assert field in data, f"Campo faltante: {field}"
            
            # Verificar consistencia
            assert len(data["agentes"]) > 0, "Sin agentes"
            assert data["dia_simulado"] >= 0
            
            return True, "OK"
        except Exception as e:
            return False, str(e)
```

---

## III. DATASETS FALTANTES — DEFINICIÓN COMPLETA

### Dataset: `technology_log`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `tech_id` | UUID | |
| `tecnologia` | str | Nombre de la tecnología |
| `nivel` | int | 0-3 según árbol |
| `descubridor_id` | str | Agente que la descubrió |
| `dia_descubrimiento` | int | |
| `intentos_previos_descubridor` | int | |
| `presion_trigger` | str | Qué problema la disparó |
| `presion_valor` | float | Intensidad de la presión |
| `perfil_descubridor` | JSON | Snapshot arquetipos/rasgos del descubridor |
| `tiempo_libre_momento` | float | Disponibilidad del agente |
| `campo_momento` | JSON | Estado del campo al descubrir |
| `estacion` | str | |
| `portadores_actuales` | JSON | Lista de agentes que la conocen |
| `dia_transmision_completa` | int | Cuando todo el grupo la sabe |
| `perdida` | bool | Si el conocimiento se perdió |
| `dia_perdida` | int | Si aplica |
| `causa_perdida` | str | Muerte portador único, etc |
| `valor_simbolico_campo` | float | Impacto en campo colectivo |

### Dataset: `knowledge_transmission_log`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `transmission_id` | UUID | |
| `tecnologia` | str | |
| `dia` | int | |
| `emisor_id` | str | Quien enseña |
| `receptor_id` | str | Quien aprende |
| `bond_emisor_receptor` | float | Vínculo entre ellos |
| `apertura_receptor` | float | Rasgo apertura del receptor |
| `mismo_zona` | bool | ¿Estaban en la misma zona? |
| `exito` | bool | ¿El receptor aprendió? |
| `intentos_previos` | int | Veces que intentó aprender esto |

### Dataset: `scenario_state_log`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `scenario_id` | UUID | |
| `dia` | int | |
| `estacion` | str | |
| `temperatura` | float | |
| `precipitacion` | float | |
| `zona_bosque_abundancia` | float | |
| `zona_pradera_abundancia` | float | |
| `zona_rio_abundancia` | float | |
| `fauna_pequeña_densidad` | float | |
| `fauna_grande_densidad` | float | |
| `presion_caza_acumulada` | float | |
| `fuego_activo` | bool | |
| `fuego_cuidador_id` | str | Null si no hay fuego |
| `fuego_ciclos_activo` | int | |
| `zonas_degradadas` | JSON | Lista de zonas con degradación |
| `recursos_totales_disponibles` | float | Índice agregado |
| `carrying_capacity_actual` | int | Cuántos agentes puede sostener |

### Dataset: `archetype_delta_log`

Cada vez que un arquetipo cambia de valor en un agente.
Permite reconstruir la historia de individuación.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `delta_id` | UUID | |
| `dia` | int | |
| `agent_id` | str | |
| `arquetipo` | str | |
| `valor_anterior` | float | |
| `valor_nuevo` | float | |
| `delta` | float | Cambio (+ o -) |
| `causa` | str | trauma/vinculo/sueño/evento/individuacion |
| `evento_trigger_id` | str | FK a events_log si aplica |
| `interaction_trigger_id` | str | FK a interactions si aplica |
| `dream_trigger_id` | str | FK a dreams_log si aplica |

### Dataset: `complex_activation_log`

Cada vez que un complejo se activa en un agente.
Es el corazón del sistema jungiano — sin esto el inconsciente es invisible.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `activation_id` | UUID | |
| `dia` | int | |
| `hora` | int | |
| `agent_id` | str | |
| `complejo` | str | abandono/inferioridad/poder/culpa/etc |
| `intensidad_activacion` | float | Qué tan fuerte se activó |
| `trigger_tipo` | str | contexto/interaccion/sueño/campo |
| `trigger_id` | str | FK al trigger |
| `contexto_descripcion` | str | Descripción narrativa del trigger |
| `conducta_resultante` | str | Qué hizo el agente tras la activación |
| `duracion_activacion_dias` | int | Cuánto duró activo |
| `integracion` | bool | ¿Se integró o se reprimió? |
| `impacto_en_shadow` | float | Delta en arquetipo sombra |

### Dataset: `symbol_propagation_log`

Cómo se contagia un símbolo entre agentes.
Sin esto el campo colectivo es una caja negra.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `prop_id` | UUID | |
| `dia` | int | |
| `simbolo` | str | |
| `agente_origen_id` | str | Quién lo tenía primero |
| `agente_receptor_id` | str | Quién lo recibió |
| `mecanismo` | str | interaccion/sueño/ritual/narracion/campo |
| `carga_transmitida` | float | Intensidad del contagio |
| `carga_campo_momento` | float | Carga del símbolo en el campo al transmitir |
| `bond_origen_receptor` | float | Vínculo entre ellos |
| `evento_context_id` | str | Si hubo un evento que facilitó la transmisión |

### Dataset: `ritual_log`

Detección y evolución de rituales emergentes.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `ritual_id` | UUID | |
| `dia_deteccion` | int | Cuando el sistema lo detectó como ritual |
| `dia_primera_ocurrencia` | int | Primera vez que ocurrió la conducta |
| `tipo_conducta` | str | Descripción de la conducta repetida |
| `agente_iniciador_id` | str | Quien lo empezó |
| `frecuencia_ocurrencias` | int | Veces que ocurrió antes de ser "ritual" |
| `agentes_participantes` | JSON | Lista de IDs |
| `contexto_tipico` | str | En qué situación ocurre |
| `zona_tipica` | str | Dónde ocurre |
| `efecto_ansiedad_campo` | float | Cuánto reduce la ansiedad colectiva |
| `simbolo_asociado` | str | Qué símbolo del campo refuerza |
| `activo` | bool | Sigue ocurriendo |
| `dia_extincion` | int | Si dejó de ocurrir |
| `evolucionó_en` | str | Ritual_id si mutó en otro ritual |

### Dataset: `session_log`

Metadata de cada sesión de ejecución.
Sin esto no sabés qué pasó en qué sesión.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `session_id` | UUID | |
| `timestamp_inicio` | datetime | |
| `timestamp_fin` | datetime | Null si sesión activa |
| `dia_inicio_simulado` | int | |
| `dia_fin_simulado` | int | Null si activa |
| `dias_procesados` | int | |
| `duracion_real_segundos` | float | |
| `razon_fin` | str | normal/timeout/ctrl_c/error/crash |
| `checkpoints_generados` | int | |
| `eventos_procesados` | int | |
| `interacciones_procesadas` | int | |
| `muertes_sesion` | int | |
| `nacimientos_sesion` | int | |
| `mitos_cristalizados_sesion` | int | |
| `tecnologias_descubiertas_sesion` | JSON | |
| `version_motor` | str | |
| `parametros_config` | JSON | Config de esa sesión |
| `error_mensaje` | str | Si terminó con error |

---

## IV. VARIABLES QUE NECESITAN REVISIÓN

### Variables que están en agent_snapshots pero son insuficientes

```
PROBLEMA: agent_snapshots guarda el estado por ciclo
pero no registra el DELTA — la diferencia con el ciclo anterior.

Para analizar individuación necesitás ver el cambio en el tiempo,
no solo el valor en cada momento.

SOLUCIÓN: archetype_delta_log captura cada cambio individual.
Los snapshots dan el estado. Los deltas dan el movimiento.
```

### Variables del campo colectivo que faltan

```python
# Lo que tenemos en collective_field_history:
simbolos = {"miedo": 0.61, "esperanza": 0.33, ...}

# Lo que FALTA:
{
    # Velocidad de cambio (momentum)
    "simbolo_velocidad": {"miedo": +0.05, "esperanza": -0.02},
    # ¿El campo está acelerando hacia crisis o estabilizándose?
    
    # Símbolos en umbral de cristalización
    "cristalizando": {"muerte": 0.68},  # Está cerca del umbral
    
    # Símbolos que estaban activos y decayeron
    "simbolos_extintos": [{"nombre": "caza_exitosa", "dia_extincion": 45}],
    
    # Coherencia del campo — ¿los símbolos apuntan en direcciones similares?
    "coherencia_campo": 0.72,  # Alta = campo unificado, baja = caos simbólico
    
    # Resonancia colectiva — ¿cuántos agentes están sincronizados?
    "agentes_resonantes": 0.60,  # 60% del grupo resuena con el campo
}
```

### Variables del agente que faltan en los snapshots

```python
# Faltan en agent_snapshots:

"necesidades": {
    "hambre":       float,   # Ya está ✅
    "fatiga":       float,   # Ya está ✅
    "sed":          float,   # ❌ FALTA — crítica en arcaico
    "sociabilidad_necesaria": float,  # ❌ FALTA — cuánto necesita interactuar
    "seguridad_percibida":    float,  # ❌ FALTA — amenaza subjetiva
},

"estado_complejo": {
    # No solo el peso del complejo — si está ACTIVADO ahora mismo
    "abandono_activo":      bool,
    "inferioridad_activo":  bool,
    "poder_activo":         bool,
    # El peso es crónico. La activación es aguda.
    # Son datos diferentes.
},

"schedule_actual": {
    "actividad_hora_actual":  str,    # Qué se supone que hace ahora
    "actividad_real":         str,    # Qué está haciendo realmente
    "desviacion_schedule":    bool,   # ¿Rompió su rutina?
    # La desviación del schedule es información psicológica clave
},

"estado_tecnologia": {
    "tecnologias_conocidas":  list,   # Qué sabe hacer
    "intentos_fallidos":      dict,   # Qué intentó sin éxito
    "rol_transmisor":         bool,   # ¿Está enseñando a alguien?
},

"fase_vital_detalle": {
    "fase":                   str,    # Ya está ✅
    "dias_en_fase_actual":    int,    # ❌ FALTA
    "proxima_transicion_en":  int,    # ❌ FALTA — cuándo cambia de fase
},
```

---

## V. ESTRATEGIA DE PERSISTENCIA COMPLETA

### Arquitectura de archivos

```
psyche-simulacra/
├── data/
│   ├── simulation.db              # SQLite — TODOS los datasets
│   ├── checkpoints/
│   │   ├── checkpoint_00001.json  # Día 1
│   │   ├── checkpoint_00010.json  # Día 10
│   │   ├── checkpoint_00087.json  # Día 87 — evento mayor
│   │   └── checkpoint_LATEST.json # Symlink al más reciente
│   ├── sessions/
│   │   ├── session_2024-01-15.log # Log de cada sesión
│   │   └── session_2024-01-16.log
│   └── exports/
│       └── analisis_dia_120.csv   # Exports manuales para análisis
```

### Qué va a SQLite y qué va a JSON

```
SQLite (simulation.db)                  JSON (checkpoints/)
──────────────────────────────────────  ────────────────────────────
agent_snapshots          (append-only)  Estado vivo de agentes
interactions             (append-only)  Campo colectivo vivo
collective_field_history (append-only)  Red social viva
events_log               (append-only)  Escenario vivo
economy_log              (append-only)  Tecnologías vivas
climate_log              (append-only)  Rituales activos
dreams_log               (append-only)  Tabúes activos
mythology_log            (append-only)
ritual_log               (append-only)
technology_log           (append-only)  ← También en JSON para
knowledge_transmission   (append-only)    reload rápido
archetype_delta_log      (append-only)
complex_activation_log   (append-only)
symbol_propagation_log   (append-only)
agent_lifecycle          (append-only)
births_log               (append-only)
deaths_log               (append-only)
scenario_state_log       (append-only)
session_log              (upsert)
```

### Frecuencia de escritura

```python
WRITE_STRATEGY = {
    # Escritura inmediata — no puede perderse
    "inmediato": [
        "deaths_log",           # Una muerte no se puede reconstruir
        "births_log",
        "mythology_log",        # Cristalización de mito
        "ritual_log",           # Detección de ritual
        "technology_log",       # Descubrimiento
        "events_log",           # Eventos mayores
        "complex_activation_log",  # Activación de complejo
    ],
    
    # Escritura por lote — cada N ticks
    "batch_cada_tick": [
        "interactions",         # Muchas por día — batch eficiente
        "archetype_delta_log",
        "symbol_propagation_log",
        "knowledge_transmission_log",
    ],
    
    # Escritura por día simulado
    "diario": [
        "agent_snapshots",
        "collective_field_history",
        "climate_log",
        "scenario_state_log",
        "agent_relations",
        "economy_log",
        "dreams_log",
        "schedule_log",
    ],
    
    # Checkpoint completo
    "checkpoint": [
        "cada_10_dias",
        "en_eventos_mayores",
        "al_cerrar_sesion",
    ]
}
```

### Protección contra cierre forzado

```python
import signal
import atexit

class SimulationRunner:
    
    def __init__(self):
        # Registrar handlers para cierre seguro
        signal.signal(signal.SIGINT,  self.graceful_shutdown)
        signal.signal(signal.SIGTERM, self.graceful_shutdown)
        atexit.register(self.emergency_save)
        
        # Buffer de escritura — los datos no escritos viven aquí
        self.write_buffer = WriteBuffer(max_size=1000)
    
    def graceful_shutdown(self, signum, frame):
        """
        Ctrl+C o kill normal — tenemos tiempo para guardar bien.
        """
        logger.info("Cierre solicitado. Guardando estado...")
        
        # Flush del buffer
        self.write_buffer.flush_to_db()
        
        # Checkpoint completo
        self.checkpoint_manager.save(
            self.simulation,
            reason="shutdown_graceful"
        )
        
        # Cerrar sesión
        self.session_log.close(razon="normal")
        
        logger.info(f"Estado guardado. Día simulado: {self.simulation.clock.dia_actual}")
        sys.exit(0)
    
    def emergency_save(self):
        """
        Último recurso — proceso terminando de forma inesperada.
        Guarda lo que puede, rápido.
        """
        try:
            # Flush del buffer primero
            self.write_buffer.flush_to_db(timeout=5)
            
            # Checkpoint de emergencia — puede estar incompleto
            # pero es mejor que nada
            self.checkpoint_manager.save(
                self.simulation,
                reason="emergency"
            )
        except Exception as e:
            logger.error(f"Emergency save falló: {e}")
            # Al menos guardar el día actual y el estado básico
            self.save_minimal_state()
```

---

## VI. CHECKLIST FINAL — Variables Confirmadas

### Capa Biológica del Agente ✅
- [x] hambre (0→1)
- [x] fatiga (0→1)
- [ ] sed (0→1) ← **AGREGAR**
- [x] salud (0→1)
- [x] energia (0→1)
- [x] edad_dias
- [x] fase_vital
- [ ] dias_en_fase_actual ← **AGREGAR**

### Capa Psicológica del Agente ✅
- [x] 12 arquetipos con pesos
- [ ] arquetipo_activo_bool por arquetipo ← **AGREGAR** (activo ≠ peso alto)
- [x] 6 complejos con pesos
- [ ] complejo_activado_bool por complejo ← **AGREGAR** (crónico ≠ agudo)
- [x] Big Five + rasgos clínicos
- [x] módulos neurales
- [x] estado emocional
- [x] memoria episódica
- [ ] sociabilidad_necesaria ← **AGREGAR**
- [ ] seguridad_percibida ← **AGREGAR**

### Capa Social ✅
- [x] vínculos con bond_strength
- [x] entrelazamientos
- [x] rol social
- [x] status
- [x] deudas de reciprocidad

### Capa Tecnológica ✅
- [ ] tecnologias_conocidas (lista) ← **AGREGAR al agente**
- [ ] intentos_fallidos (dict) ← **AGREGAR al agente**
- [ ] dataset technology_log ← **NUEVO**
- [ ] dataset knowledge_transmission_log ← **NUEVO**

### Escenario ✅
- [ ] dataset scenario_state_log ← **NUEVO**
- [ ] tracking fauna por especie ← **AGREGAR**
- [ ] tracking degradación de zonas ← **AGREGAR**

### Campo Colectivo ✅
- [x] símbolos con carga
- [ ] velocidad de cambio de símbolos ← **AGREGAR**
- [ ] símbolos en umbral de cristalización ← **AGREGAR**
- [ ] coherencia del campo ← **AGREGAR**
- [ ] agentes_resonantes_porcentaje ← **AGREGAR**

### Persistencia ✅
- [ ] Sistema de checkpoint ← **NUEVO Y CRÍTICO**
- [ ] session_log ← **NUEVO**
- [ ] Handlers de cierre graceful ← **NUEVO**
- [ ] Write buffer con flush ← **NUEVO**

---

## VII. RESPUESTA DIRECTA A LA PREGUNTA

> *¿Estamos seguros de que establecimos las variables correctas?*

**Lo que estaba bien:**
Los datasets de análisis (snapshots, interacciones, campo, eventos, etc.)
cubren bien lo que *ocurre* durante la simulación.

**Lo que faltaba y ahora está:**
- Sistema de checkpoint para reanudar sesiones
- Variables de activación aguda vs. crónica (complejo_activado ≠ complejo_peso)
- Sed como necesidad biológica crítica
- Árbol tecnológico con transmisión y pérdida
- Estado del escenario como serie temporal
- Propagación de símbolos como dataset propio
- Rituales como entidades detectables
- Velocidad y coherencia del campo colectivo
- Session log para metadata de ejecución

**Lo que se puede agregar después sin romper nada:**
- Análisis estadísticos derivados (vistas sobre los datasets)
- Exportaciones específicas para visualización
- Métricas agregadas por período

**Garantía de no perder datos:**
Con checkpoint cada 10 días + checkpoint en cierre + emergency save,
la pérdida máxima posible es de 10 días simulados (10 minutos reales).
En la práctica, si usás Ctrl+C para cerrar, la pérdida es cero.

---

*Psyche Simulacra — Auditoría de Persistencia v1.0*  
*Revisar antes de escribir la primera línea de código de persistencia*
