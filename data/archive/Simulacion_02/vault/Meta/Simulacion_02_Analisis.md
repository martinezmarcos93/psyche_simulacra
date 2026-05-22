# Análisis Estadístico — Simulación 02

**Duración real:** ~8 horas  
**Días simulados:** 27.675  
**Fecha de análisis:** 2026-05-21  
**Estado al cierre:** 3 supervivientes vivos

---

## Sesión

| Campo | Valor |
|---|---|
| Días procesados (última sesión) | 19 (27657–27675) |
| Razón de fin | normal |
| Versión del motor | 0.1.0 |
| Nacimientos totales | 8 |
| Muertes registradas | 105 |

> La tabla `session_log` guarda solo la última sesión. Los 8 nacimientos ocurrieron en sesiones anteriores.

---

## Demografía — Colapso poblacional

| Día | Vivos | | Día | Vivos |
|---|---|---|---|---|
| 0 | 100 | | 8.000 | 24 |
| 500 | 55 | | 12.000 | 17 |
| 1.000 | 49 | | 18.000 | 8 |
| 3.000 | 35 | | 25.000 | 6 |
| 7.500 | 24 | | **27.500** | **3** |

- **Máximo:** 100 (día 0)
- **Mínimo al cierre:** 3 (días 27500–27675)
- **Sin nacimientos posteriores al día 12.761**

---

## Muertes — Causas

| Causa | N | % | Primer día | Último día | Día promedio |
|---|---|---|---|---|---|
| **Deshidratación** | **69** | **65.7%** | 10 | 12.170 | 1.153 |
| Vejez | 36 | 34.3% | 915 | 27.500 | 10.783 |
| **Total** | **105** | | | | |

### Clusters de deshidratación

**Cluster 1 — días 10–27 (10 muertos)**  
Aglaia, Graia, Galen, Alethea, Hakon, Drex, Xanthe, Uritha, Velia, Theron.  
Mortalidad masiva en el primer mes. Probable bug o desbalance de agua inicial.

**Cluster 2 — días 200–700 (~40 muertos)**  
El período más letal. Entre días 300–360, 20 agentes mueren en 60 días consecutivos.  
Posible cruce con estación de sequía (verano: precipitación avg 0.298).

**Muertes tardías por deshidratación:**  
Caso notable: Adrasteia (hijo_003, generación 1) muere de deshidratación en el día 12.170.

---

## Nacimientos y Genealogía

### Los 8 nacidos durante la simulación

| ID interno | Nombre | Primer snap | Rol | Padres | Generación |
|---|---|---|---|---|---|
| hijo_000 | Chloris | día 312 | genérico | — | Gen 1 |
| hijo_001 | Euphrosyne | día 556 | genérico | — | Gen 1 |
| hijo_002 | Morpheus | día 1.396 | recolector | — | Gen 1 |
| hijo_003 | Adrasteia | día 1.773 | recolector | — | Gen 1 |
| hijo_004 | Calais | día 2.309 | recolector | — | Gen 1 |
| hijo_005 | **Bia** | día 2.871 | recolector | erytheis + xeron | Gen 1 |
| hijo_006 | **Tyche** | día 11.900 | recolector | hijo_002 + hijo_004 | **Gen 2** |
| hijo_007 | **Zelos** | día 12.761 | recolector | hijo_002 + hijo_004 | **Gen 2** |

> Bia, Tyche y Zelos son los 3 supervivientes al cierre de la simulación.

### Árbol genealógico de los supervivientes

```
GEN 0 (fundadores originales)
├── Erytheis ──────────────────────────┐
├── Xeron ─────────────────────────────┤
│                                       ▼
│                               hijo_005 = Bia (Gen 1) ← VIVA día 27675
│
├── [padre de hijo_002] ────────────────┐
│                                       ▼
│                               hijo_002 = Morpheus (Gen 1)
│                                    │
├── [padre de hijo_004] ────────────────┐
│                                       ▼
│                               hijo_004 = Calais (Gen 1)
│                                    │
│                        ┌────────────┴────────────┐
│                        ▼                         ▼
│                hijo_006 = Tyche (Gen 2)   hijo_007 = Zelos (Gen 2)
│                ← VIVA día 27675              ← VIVO día 27675
```

> Tyche y Zelos son hermanos — mismos padres (Morpheus + Calais), nacidos con 861 días de diferencia.  
> La especie alcanzó al menos 2 generaciones de profundidad antes del cierre.

---

## Vitales — Promedios globales (agentes vivos)

| Vital | Promedio | Min | Max |
|---|---|---|---|
| **Sed** | **0.4075** | 0.000 | 1.000 |
| Ansiedad | 0.3677 | 0.000 | 1.000 |
| Fatiga | 0.3161 | 0.000 | 1.000 |
| Energía | 0.6200 | 0.000 | 1.000 |
| Humor | 0.8158 | 0.030 | 1.136 |
| Hambre | 0.0834 | 0.000 | 1.000 |

### Evolución inicio → fin

| Vital | Días ≤ 10 | Días ≥ 27.665 | Tendencia |
|---|---|---|---|
| Sed | 0.390 | 0.429 | ↑ crónica |
| Fatiga | 0.321 | 0.335 | ↑ leve |
| Energía | 0.649 | 0.578 | ↓ declive |
| Humor | 0.806 | 0.824 | ↑ adaptación |
| Hambre | 0.100 | 0.081 | ↓ resuelta |
| Ansiedad | 0.372 | 0.371 | estable |

### Vitales de los 3 supervivientes (día 27.675)

| Nombre | Sed | Hambre | Fatiga | Humor |
|---|---|---|---|---|
| Bia (hijo_005) | 0.295 | 0.084 | 0.335 | 0.896 |
| Zelos (hijo_007) | 0.135 | 0.144 | 0.335 | 0.920 |
| **Tyche (hijo_006)** | **0.575** | 0.104 | 0.335 | 0.737 |

> Tyche tiene la sed más alta de los tres — en riesgo potencial si la simulación continuara.

---

## Roles al cierre (día 27.675)

| Rol | Total agentes | Vivos | Tasa supervivencia |
|---|---|---|---|
| **Recolector** | 29 | **3** | **10.3%** |
| Genérico | 41 | 0 | 0% |
| Cazador | 14 | 0 | 0% |
| Guardián | 12 | 0 | 0% |
| Explorador | 12 | 0 | 0% |

> Los 3 supervivientes son todos recolectores. El único rol con acceso directo constante a recursos fue el que persistió.

---

## Clima

| Estación | Temp. avg | Precipitación avg | Survival risk avg | Mood modifier |
|---|---|---|---|---|
| Invierno | 1.5°C | 0.464 | **0.0196** | **-0.2089** |
| Otoño | 11.5°C | 0.659 | 0.0075 | -0.0953 |
| Primavera | 14.0°C | 0.562 | 0.0100 | +0.0093 |
| Verano | 26.5°C | **0.298** | 0.0024 | +0.0384 |

### Eventos climáticos

| Evento | Ocurrencias |
|---|---|
| Tormenta | 28.359 |
| Helada | 20.243 |
| Sequía | 20.176 |

> El verano tiene la menor precipitación (0.298) y concentra las sequías — correlaciona con los clusters de deshidratación.  
> El invierno es la estación más peligrosa por survival_risk y mood negativo.  
> **El fuego nunca se activó durante toda la simulación** (0 días con fuego activo).

---

## Escenario

| Métrica | Valor |
|---|---|
| Resource pressure promedio | 0.0388 |
| Resource pressure máxima | 0.3948 |
| Carrying capacity promedio | 163.253 |
| Carrying capacity mínima | 840 (día 0, 19 hexes) |
| Carrying capacity máxima | 163.610 (4.800 hexes) |
| Dias con fuego activo | 0 |
| Hexes explorados al máximo | 4.800 |

> La exploración fue casi instantánea: de 19 hexes (día 0) a 4.800 hexes (día 2.000) y se mantuvo estable.  
> La resource pressure no fue críticamente alta — el problema de agua es de acceso, no de escasez global.

---

## Preguntas abiertas

- [ ] ¿Por qué mueren 10 agentes en los primeros 27 días de sed? ¿Bug de balance o comportamiento real?
- [ ] ¿Por qué no hubo nacimientos después del día 12.761? ¿Población demasiado pequeña o condición de cooldown?
- [ ] ¿Por qué el fuego nunca se activó?
- [ ] ¿Qué rol tenían los padres de hijo_000 a hijo_004 (Chloris, Euphrosyne, Morpheus, Adrasteia, Calais)?
