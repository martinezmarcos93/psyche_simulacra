# PSYCHE SIMULACRA — Alcance Beta
## Tiempo, Escala y Complejidad Mínima Viable

---

## ESCALA TEMPORAL CORREGIDA

### El problema con 1 día = 10 minutos

```
Sesión de 2 horas → 12 días simulados
Ver 1 año         → 30 horas de sesiones
Ver cultura nacer → meses de trabajo
```

Eso hace imposible observar arcos narrativos en una sola sesión.

### Ratio propuesto para beta

```
1 minuto real  =  1 día simulado
1 hora real    = 60 días simulados  (~2 meses)
2 horas reales = 120 días simulados (~4 meses)

─────────────────────────────────────────────
Semana de sesiones (5 × 2h):
→ 600 días simulados → casi 2 años

Mes de sesiones (20 × 2h):
→ 2400 días simulados → ~6.5 años
─────────────────────────────────────────────
```

### Granularidad interna del tick

El motor no corre en tiempo real continuo.
Corre en **ticks discretos** que se procesan lo más rápido posible.

```python
# 1 tick = 1 hora simulada
# 1 día  = 24 ticks
# El motor procesa todos los ticks del día antes de avanzar

TICKS_PER_DAY = 24
DAYS_PER_REAL_MINUTE = 1  # Ratio beta

# Objetivo de performance:
# Procesar 1 día simulado (24 ticks × N agentes) en < 1 segundo real
# Con 25 agentes beta: 24 × 25 = 600 operaciones mínimas por "minuto real"
```

### Punto de guardado

La simulación guarda estado completo al final de cada día simulado.
Al cerrar, el vault de Obsidian queda actualizado.
Al reabrir, se retoma exactamente donde se dejó.

```
Sesión 1 (2h) → Días 1–120  → Vault actualizado → Cerrar
Sesión 2 (2h) → Días 121–240 → Vault actualizado → Cerrar
```

---

## COMPLEJIDAD BETA — LO QUE ENTRA Y LO QUE NO

### Criterio de corte

Una feature entra en beta si cumple **todas** estas condiciones:
1. Es necesaria para que algo *psicológicamente interesante* pueda emerger
2. No requiere un subsistema propio de 500+ líneas
3. Su ausencia haría la simulación trivial o imposible de observar

---

### ✅ ENTRA EN BETA

#### Agentes y psicología
- Vector arquetípico jungiano (12 arquetipos, pesos dinámicos)
- Complejos activables por contexto (4–5 complejos core)
- Rasgos dimensionales básicos (Big Five simplificado)
- Estado emocional dinámico (humor, energía, ansiedad)
- Memoria episódica simplificada (últimos N eventos)
- Sueños básicos (procesamiento de trauma, genera proto-símbolo)

#### Rutinas y tiempo
- Schedule diario por rol (dormir, buscar alimento, interactuar, descansar)
- Necesidades básicas: hambre, fatiga, sociabilidad
- Si las necesidades no se satisfacen → stress → afecta arquetipos

#### Interacciones
- Mecánica cuántica simplificada: superposición de 3–4 estados conductuales
- Colapso por contexto + arquetipos + complejos activos
- Resultado: cooperar / conflictuar / ignorar / compartir
- Actualización de vínculo tras cada interacción

#### Red social
- Un grafo único (emocional/social)
- bond_strength entre pares (-1 → 1)
- Entrelazamiento cuando ocurre evento de alta carga compartido

#### Campo colectivo
- Símbolos con carga numérica que sube/baja
- Umbral de cristalización → proto-mito
- Retroalimentación al comportamiento individual

#### Economía arcaica
- Reciprocidad directa (sin moneda)
- Tracking de deuda percibida entre agentes
- Redistribución por el agente de mayor status
- Surplus ocasional como evento, no como sistema permanente

#### Clima básico
- Temperatura y precipitación (dos variables)
- Ciclo estacional simple (4 estaciones)
- Efecto sobre humor y productividad
- Sin microclimas, sin eventos extremos en beta

#### Capa A (inconsciente colectivo base)
- Aversión al incesto (efecto Westermarck en módulo de apego)
- Override de supervivencia cuando amenaza > umbral
- Cuidado de la cría (activación automática)
- Tracking de reciprocidad
- Respuesta existencial ante la muerte (genera proto-símbolo)

#### Obsidian sync
- Lectura de perfiles al iniciar
- Escritura de estado al final de cada día simulado
- Log de eventos significativos en nota del agente

---

### ❌ FUERA DE BETA

Estas features son importantes para versiones futuras pero no para beta:

| Feature | Por qué espera |
|---------|---------------|
| Depredadores | Subsistema propio: IA de amenaza, respuesta de grupo, trauma |
| Amenazas pandémicas | Modelo de contagio completo, efectos en red |
| Domesticación de animales | Economía de crianza, surplus animal, nuevos roles |
| Ciclos de vida (nacimiento/muerte por edad) | Herencia de arquetipos, crianza, luto estructural |
| Múltiples grupos / contacto intertribal | Diplomacia, guerra, sincretismo cultural |
| Sistema económico con moneda | Emerge después de que el surplus sea estable |
| Lenguaje memético / rumores | Requiere modelo de propagación de información |
| Arte y producción cultural | Requiere surplus y roles especializados estables |
| Enfermedades psicológicas emergentes | Requiere más historia de agente acumulada |
| Dashboard avanzado | Se construye sobre la beta que funciona |
| 100 agentes | Escalar solo cuando el modelo de 15–25 sea sólido |

---

## GRUPO BETA — 15 AGENTES

### Por qué 15 y no 12 ni 25

- 12 es el mínimo para dinámicas interesantes, pero poco margen
- 25 es realista pero más difícil de debuggear y observar
- 15 permite: 2–3 "familias" nucleares, 1–2 líderes emergentes, 1–2 marginados

### Diversidad arquetípica mínima necesaria

Para que algo interesante emerja, el grupo beta necesita tensión interna.
No todos pueden ser equilibrados — eso produce una sociedad sin drama.

```
Distribución sugerida para los 15 agentes iniciales:

PERFILES EXTREMOS (generan eventos):
  1 × héroe muy alto (0.85+)    → candidato a primer lider narrativo
  1 × sombra muy alta (0.85+)   → candidato a primer chivo expiatorio
  1 × trickster alto (0.75+)    → perturbador del orden, fuente de cambio
  1 × sabio alto (0.80+)        → portador de proto-rituales

PERFILES MEDIOS (masa crítica, hacen que los extremos importen):
  4 × perfiles equilibrados con ligera tendencia héroe/madre
  3 × perfiles equilibrados con ligera tendencia sumisión/conformidad
  
PERFILES VULNERABLES (generan necesidad de protección y mito):
  2 × ansiedad alta + vínculos débiles (candidatos a trauma)
  1 × apertura muy alta (primer artista/vidente sin saberlo)
  2 × rol de "cría/joven" (activan módulo de cuidado en adultos)
```

---

## LO QUE DEBERÍA PODER VERSE EN BETA

Al cabo de 600 días simulados (una semana de sesiones de 2h),
si el modelo funciona, deberían observarse al menos:

### Fenómenos esperados

```
SEMANA 1 (Días 1–120)
  → Jerarquía situacional emerge sin programarla
  → Primer conflicto significativo y su resolución
  → Primera muerte (por hambre extrema o conflicto)
  → Primeros proto-símbolos activados por la muerte
  → Vínculos fuertes y vínculos negativos establecidos

SEMANA 2 (Días 121–240)
  → Campo colectivo con al menos 2–3 símbolos cargados
  → Primer umbral de cristalización (si las condiciones se dan)
  → Patrones de reciprocidad establecidos (quién da, quién acumula)
  → Primer rol especializado emergente (el que cura, el que narra)

SEMANA 3–4 (Días 241–480)
  → Posible primer proto-mito documentado en vault
  → Posible primer tabú verbalizado
  → Posible proto-ritual (comportamiento repetido que reduce ansiedad)
  → Transformación arquetípica en al menos 1 agente (historia acumulada)
```

### Señal de que el modelo no funciona

Si al día 120 simulado:
- Todos los agentes tienen la misma emoción dominante → falta varianza
- No hay ningún vínculo negativo → falta tensión
- El campo colectivo está vacío → los eventos no alimentan el campo
- Ningún agente cambió su arquetipo dominante → falta transformación

---

## CHECKLIST DE INICIO — Antes de correr la primera simulación

```
[ ] 15 agentes definidos en YAML con diversidad arquetípica real
[ ] Motor de tick corriendo sin errores (1 día = 24 ticks)
[ ] Rutinas básicas funcionando (dormir, buscar alimento, interactuar)
[ ] Al menos 1 muerte posible (por hambre si necesidades no se satisfacen)
[ ] Campo colectivo recibiendo input de interacciones
[ ] Vault de Obsidian sincronizando al final de cada día
[ ] SQLite guardando snapshots (agent_snapshots + interactions)
[ ] El motor puede pausarse y reanudarse sin perder estado
```

---

*Beta scope v1.0 — revisar tras primeras 2 semanas de simulación*
