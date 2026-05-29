# Roadmap 7.0 — Emergencia Cultural: Mitos, Generaciones y Memoria Viva

**Rama de trabajo:** `culture` — merge a `main` al completar bloque E.

**Objetivo:** hacer que una simulación de 3000–6000 días produzca de forma natural
>=5 nacimientos, >=3 mitos/leyendas distintos, >=20 estructuras culturales,
>=100 eventos culturales y al menos 2 generaciones vivas simultáneamente.

**Criterio de orden:** menor → mayor complejidad. Cada bloque es desplegable
independientemente.

---

## Bloque A — Determinismo del azar ✦ baja complejidad

> Sin reproducibilidad no hay forma de distinguir "buen ajuste" de "buena suerte".
> Este bloque no cambia nada visible, pero hace que el resto sea evaluable.

### A1 — Sembrar AgentCore._rng con el seed principal
- `AgentCore.__init__` crea `self._rng = random.Random()` sin semilla.
- Pasar `seed` a `AgentCore` y usar `random.Random(seed + 1)` allí.
- Verificar que `AgentCore.from_yaml` propague el seed al constructor.

### A2 — Sembrar MythologyEngine y CulturalMemory
- `MythologyEngine` usa `random.random()` global en varios puntos de cristalización.
- Reemplazar por instancia `self._rng = random.Random(seed + 2)`.
- Mismo ajuste para `CulturalMemory._rng`.

### A3 — Test de reproducibilidad de corrida corta
- Añadir test que corre la sim 200 días dos veces con el mismo seed y compara
  día de primer nacimiento, primer proto-mito y primera estructura construida.
- Target: resultados idénticos.

---

## Bloque B — Fertilidad generacional ✦ baja complejidad

> Sin generaciones no hay distorsión cultural real: solo hay biografía de una sola capa.

### B1 — Relajar condiciones de reproducción
- `_BOND_REPRO_MIN`: bajar de `0.70` → `0.55`
- `_PROB_REPRO_DIARIA`: subir de `0.003` → `0.007`
- `_REPRO_COOLDOWN_DIAS`: bajar de `300` → `180`
- `_REPRO_HUNGER_MAX` / `_REPRO_THIRST_MAX`: subir de `0.30` → `0.45`
- Exponer estas 4 constantes como variables de entorno (igual que `CHECKPOINT_INTERVAL`).

### B2 — Semillas iniciales favorables a generaciones
- Crear `data/seeds/rich_culture_100.yaml`: 90–110 agentes, distribución de edad
  concentrada en 12–35 años, mayoría arquetipos Madre/Padre/Hijo_Divino/Heroe/
  Trickster; pocos viejos (>50) como "ancestros fundadores".
- Agrupar agentes por bioma en el YAML para que las tribus emerjan naturalmente.
- Exponer como opción en el selector de semillas del launcher.

### B3 — Registro cultural de nacimientos
- Cada nacimiento exitoso debe generar un evento en `CulturalMemory` con tipo
  `"nacimiento"` y los ids de ambos padres + tribu.
- Sirve como dato narrativo y como trigger potencial para proto-mitos.

---

## Bloque C — Mortalidad: trauma simbólico > extinción ✦ media complejidad

> Los eventos deben lastimar la interpretación más que los cuerpos.

### C1 — Separar mortalidad directa de presión simbólica en catástrofes
- `catastrophe.py`: añadir param `lethality_factor` (default `1.0`; preset
  `rich_culture` usará `0.5`).
- Las catástrofes con `lethality_factor < 1.0` reducen mortalidad directa pero
  duplican `myth_pressure` y `confusion` sobre los sobrevivientes.
- Meta: que una sequía mate 2–3 agentes y deje a los demás con trauma fuerte
  en lugar de matar 8–10 y dejar pocos con trauma débil.

### C2 — Fauna simbólica: reducir kills, aumentar encuentros
- `fauna_symbolic.py`: bajar probabilidad de muerte por depredador en un 40%.
- Subir probabilidad de encuentro no-letal que deja `myth_pressure += 0.15`.
- Un encuentro con la fauna debería ser más "relato" que "muerte".

### C3 — Liminal: suspensión completa de necesidades
- Verificar que agentes `in_liminal = True` no acumulen hambre/sed/fatiga.
- Ya está implementado en `agent_core.py`; agregar test que confirma que
  tras 100 ticks liminales los valores de necesidades no cambian.

---

## Bloque D — Mitología: variedad y accesibilidad ✦ media complejidad

> Varios mitos distintos en una corrida requieren umbral más bajo y menor
> restricción de unicidad por tipo.

### D1 — Bajar umbral de cristalización
- `MythologyEngine`: `_CONTEXT_THRESHOLD` de `0.35` → `0.25`
- Transmisiones necesarias para cristalizar: de `5` → `3`
- Coherencia mínima de `0.60` → `0.50`

### D2 — Permitir múltiples mitos del mismo tipo
- Quitar la restricción que impide crear un proto-mito si ya existe uno activo
  del mismo `narrative_type`.
- Reemplazar por: no permitir duplicados exactos del mismo par
  `(narrative_type, pair_id)`. Dos tribus distintas pueden tener su propio
  mito Héroe independiente.

### D3 — Mitos tribales: anclar a tribu de origen
- Al cristalizar un mito, registrar `tribe_id` de la tribu con mayor
  `myth_pressure` acumulada.
- Mostrar en el vault y en el inspector de mitos a qué tribu pertenece cada leyenda.

### D4 — Test de cobertura mítica
- Test que corre la sim 1500 días con `rich_culture_100.yaml` (seed fijo) y
  verifica que haya >= 2 proto-mitos creados y >= 1 cristalizado.

---

## Bloque E — Cultura material viva ✦ media complejidad

> Las estructuras deben volverse relato, no solo geometría en el mapa.

### E1 — Reducir cooldown de construcción
- `CultureEngine._CONSTRUCCION_COOLDOWN`: de `50` → `25` días.
- Bajar mínimo de miembros por tribu para construir: de `3` → `2`.

### E2 — Construcción como evento cultural
- Cada estructura construida (altar, tótem, muralla, hoguera) debe generar
  un evento en `CulturalMemory` con tipo `"construccion"` e incluir tipo de
  estructura, tribu constructora y día.
- Ese evento puede ser input para proto-mitos ("el altar que protegió a los nuestros").

### E3 — Degradación narrativa de estructuras
- Cuando una estructura expira, generar evento `"ruina"` en `CulturalMemory`.
- Las ruinas aumentan `myth_pressure` leve (+0.05) en la tribu que la construyó.
- Mostrar ruinas en el mapa con símbolo distinto al de estructuras activas.

### E4 — Memoria cultural expandida
- `CulturalMemory`: subir `max_records` de `30` → `100` por tribu.
- Probabilidad diaria de transmisión de relatos: subir de valor actual → `×1.5`.
- Distorsión pasiva: bajar período de `360` → `180` días
  (los relatos mutan más rápido en corridas medianas).

---

## Bloque F — Observabilidad narrativa ✦ baja-media complejidad

> Para evaluar si el mundo es culturalmente rico, necesitamos métricas visibles.

### F1 — Panel "Pulso cultural" en tab Resumen
- Añadir 4 métricas en tiempo real junto al ICL:
  - Nacimientos totales en esta sesión
  - Proto-mitos activos / Mitos cristalizados
  - Estructuras activas
  - Eventos en CulturalMemory (total acumulado)

### F2 — Timeline narrativo en tab Civilización
- Lista scrollable de los últimos N eventos culturales ordenados por día:
  nacimientos, construcciones, cristalizaciones, ruinas, muertes fundacionales.
- Cada ítem con icono, día y nombre de tribu.

### F3 — Exportar crónica al vault
- Al cerrar simulación (o cada 100 días), volcar los últimos 50 eventos de
  `CulturalMemory` a `vault/Colectivo/Cronica.md` en formato legible.
- No reemplaza las leyendas del narrador; es el registro "en bruto" de eventos.

---

## Bloque G — Preset y herramienta de evaluación ✦ baja complejidad

### G1 — Preset rich_culture en .env.example
```
# Preset experimental — emergencia cultural
CHECKPOINT_INTERVAL=20
DAYS_UNTIL_CLUSTERING=20
BOND_REPRO_MIN=0.55
PROB_REPRO_DIARIA=0.007
REPRO_COOLDOWN_DIAS=180
LETHALITY_FACTOR=0.5
MYTH_CONTEXT_THRESHOLD=0.25
```

### G2 — Métrica de riqueza cultural en scripts/
- `scripts/eval_culture.py`: carga el checkpoint más reciente y calcula un
  score 0–100 basado en nacimientos, mitos, estructuras, eventos y generaciones.
- Output: tabla en terminal con los valores y el score.
- Objetivo de diseño: una corrida "tipo Sim 02" debería puntuar > 70.

---

## Orden de implementación sugerido

```
A1 → A2 → A3          (determinismo — prerequisito de todo lo demás)
B1 → B2 → B3          (fertilidad — impacto más visible en corridas cortas)
D1 → D2 → D3 → D4     (mitología — núcleo narrativo)
E1 → E2 → E3 → E4     (cultura material)
C1 → C2               (mortalidad — ajustar solo si B+D no alcanzan)
F1 → F2 → F3          (observabilidad)
G1 → G2               (preset + evaluación)
```
