# Handoff — 2026-09-21 (continuación, máquina de oficina)

Continuación de `handoffs/2026-09-21.md` en modo autónomo, sobre una máquina
distinta a la de la sesión original (2 núcleos lógicos — dato relevante para
lo que sigue). Rama de trabajo: `feature/ecuacion-personal-continuacion`,
creada desde `main` en `466ec65`. **11 commits, pusheados a `origin`
(autorización explícita del usuario). `main` no se tocó.**

---

## 1. Fix — `ZeroDivisionError` intermitente en `SimulationClock`

`get_performance_metrics()` dividía por `elapsed_real` sin piso mínimo. En
esta máquina, 50 ticks headless (sin I/O real) pueden completarse dentro de
la resolución del reloj monotónico y medir `elapsed_real == 0.0`, lanzando
`ZeroDivisionError` — reproducido en
`tests/test_agent.py::TestPerformance::test_metricas_disponibles_tras_correr`,
no es una regresión de la sesión anterior, depende de la velocidad del
hardware. Corregido con un piso de `1e-6`s; verificado estable en 5 corridas
consecutivas.

**Commit:** `0bd0432 fix(clock): evitar ZeroDivisionError en get_performance_metrics`

---

## 2. Extendida `on_social_transmission` a más tipos de encuentro

Pendiente de prioridad media dejado por `handoffs/2026-09-21.md` §7: solo el
choque violento (competencia-competencia) empujaba coherencia hacia la
cristalización de un `ProtoMito`. Se conectó también cooperación pura
(intensity=0.25) y conflicto/explotación (intensity=0.5), proporcional a la
magnitud emocional ya codificada en cada rama de `resolve_encounter`. No se
conectó manipulación (fuera de alcance, contaminación afectiva ambigua). Los
tres pesos quedaron overridables por variable de entorno
(`MYTH_TRANSMISSION_*`) para poder calibrarlos sin recompilar — mismo patrón
que `MYTH_CONTEXT_THRESHOLD`.

2 tests nuevos verifican la intensidad relativa correcta;
`test_social.py` 117/117 y `test_culture_r7.py` 8/8 (incluido el test de
cobertura mítica que este fix repara indirectamente) pasan.

**Commits:** `a5f87e3`, `6988e09`

### Hallazgo: los pesos elegidos a priori sobre-producen mitos

El smoke test de `scripts/myth_calibration.py` (semilla 42, 600 días,
`rich_culture_100.yaml`) mostró **primera cristalización en el día 2** y
**3 mitos totales para el día 600** — el objetivo original del Roadmap 7 era
ese mismo total (≥3) recién entre los días 3000 y 6000, es decir, 5-10x más
rápido de lo pretendido. Confirmado también de forma narrativa inspeccionando
el vault de Obsidian que generó esa corrida (ver §6 abajo). **No se fijó un
peso nuevo** — eso violaría el mismo principio de "no ajustar a ciegas" que
guió la sesión anterior. El barrido de calibración (baseline choque-solo vs.
pesos reducidos) quedó lanzado pero se interrumpió por hardware (§5).

---

## 3. Bug sistémico — `UnicodeEncodeError` en consola Windows cp1252

Reproducido corriendo `scripts/myth_calibration.py`: la consola de Windows
por defecto usa cp1252, que no puede imprimir el emoji narrativo de varios
subsistemas (objetos sagrados, deidades — `agent_core._try_create_objects`,
`_apply_myth_effects`, etc.). Cualquier simulación suficientemente larga
como para disparar uno de estos eventos crasheaba con `UnicodeEncodeError`
— un error totalmente ajeno a la lógica que estuviera corriendo en ese
momento, y que habría afectado también a la sesión original si sus semillas
hubieran tocado ese código.

Corregido forzando `sys.stdout`/`stderr` a UTF-8 (con `errors="replace"`)
al inicio de todos los entry points reales: `main.py`, `run_simulation.py`,
`run_overnight.py`, `run_robustness.py`, `ab_interpretive.py`,
`myth_calibration.py`.

**Commit:** `b82fee1 fix(runtime): UTF-8 en stdout/stderr para entry points headless`

---

## 4. Nueva métrica — `behavioral_intra_tribe_dispersion`

Pendiente de prioridad media dejado por `handoffs/2026-09-21.md` §7:
"instrumentar divergencia intra-tribu vs. inter-tribu por separado".
`behavioral_kl_mean` (existente) solo mide inter-tribu; si el
`InterpretiveFilter` aumenta la idiosincrasia individual sin separar tribus
entre sí, esa métrica se queda plana y es indistinguible de "no hay efecto"
— exactamente la ambigüedad que dejó abierta el experimento A/B original.

`behavioral_intra_tribe_dispersion` agrega entropía de Shannon normalizada
[0,1] de la acción conductual *dentro* de cada tribu, promediada entre
tribus. Mismo patrón que ya usa el módulo para `vfe_tribe_mean` (intra) vs.
`field_kl_mean` (inter) sobre el campo simbólico. Expuesta como
`behavioral_intra_q4` en `ab_interpretive.py`.

5 tests nuevos; `test_metrics.py` 29/29 pasan.

**Commit:** `575a9d8 feat(metrics): behavioral_intra_tribe_dispersion`

---

## 5. Repetición del A/B de Fase 1 con n=15 — interrumpida por hardware

Pendiente de prioridad media dejado por `handoffs/2026-09-21.md` §7:
"repetir el experimento A/B de la Fase 1 con más poder estadístico
(n≥15-20 semillas)". Se lanzó un batch de 15 semillas (42-56) × 3
condiciones × 300 días, ya instrumentado con `behavioral_intra_q4` (§4).

**Interrumpida**: esta máquina tiene solo 2 núcleos lógicos. Cada corrida de
300 días tarda ~470-500s (no los ~150s de la sesión original en otra
máquina) — con solo 3-4 de 45 corridas completadas tras más de una hora,
proyectando >5h para terminar. Se reemplazó el bash one-off no versionado
por `scripts/run_ab_batch.py`: portable (Python puro, no depende de Git
Bash) y **resumible** con `--append` (salta combinaciones seed/condición ya
calculadas), para poder retomar en otra máquina sin perder lo ya corrido.

```
python scripts/run_ab_batch.py --seeds 42-56 --days 300 \
    --output data/metrics/ab_interpretive_fase1_n15_2026-09-21.jsonl
```

**Commits:** `f13d0ee` (`myth_calibration.py`, script hermano usado para el
smoke test de §2), `1dda8be` (`run_ab_batch.py`), `a6f2db2` / `90b4391`
(esqueleto y actualización del documento de experimento).

---

## 6. Hallazgo adicional — inspección del vault de Obsidian

Mientras se esperaban las corridas largas, se inspeccionó manualmente el
vault que generó el smoke test de `myth_calibration.py` (600 días, seed 42)
— resulta que aunque el arnés se autodenomina "headless", el motor
narrativo escribe directo a `vault/` de todas formas.

- **Mitología**: confirma en formato narrativo la sobre-cristalización de
  §2 — `Mito_moral_dia2` (Héroe Kairos vs. Monstruo Moros), `Cosmogonia_dia3`
  (Arete vs. Moros), `Mito_moral_dia7` (Kairos vs. Moros de nuevo).
- **Símbolos** (foto ~día 30): Sombra dominante (1.00), Trickster y Muerte
  muy cargados (0.94), Héroe y Madre altos (0.92) — un inconsciente
  polarizado hacia sombra/muerte/trickster desde temprano.
- **Civilización temprana**: 8 tribus fundadoras (Arete, Bios, Chara, Doron,
  Elpis, Iris, Kore, Leon), mitos fundacionales por plantilla, una elegía
  real (Leon, jefe tribal, murió de inanición día 28).
- **Hallazgo más importante**: la `Cronica.md` exportada al día 500 muestra
  un patrón saturado y perfectamente repetido — **"Eco del Multiverso"**
  (`core/liminal/collective_echo.py`), el arquetipo `muerte` resonando a
  intensidad máxima (1.00) simultáneamente en 14 tribus, idéntico día tras
  día (497-500). Es un feedback positivo real y diseñado: un símbolo que
  converge lo suficiente entre tribus se amplifica globalmente, facilitando
  que vuelva a converger. **Hipótesis abierta, no confirmada**: la
  sobre-cristalización temprana de §2 pudo haber sido la chispa que arrancó
  este loop de monocultivo simbólico.
- **Limitación observada** (no bug confirmado, no investigado a fondo): los
  archivos por tribu/persona/meta del vault se congelan en el día ~30 —
  probablemente porque las tribus fundadoras se disuelven en el primer
  reclustering del escenario (`DAYS_UNTIL_CLUSTERING=30`) y el sistema no
  genera archivos nuevos de Obsidian para las tribus que emergen después
  (`Cronica.md` sí sigue actualizándose, con nombres de tribus nuevos que no
  tienen archivo propio en `vault/Tribus/`).

No hay commit asociado a este punto — es una observación registrada para la
próxima sesión, no una corrección de código.

---

## 7. Documentación

- `docs/ARCHETYPES.md` §4.3 corregido — ya no describe `on_social_transmission`
  como si siempre sumara +1.0; explica el mecanismo de intensidad variable.
- `docs/DEVELOPMENT_LOG.md` — segunda entrada de la fecha, con el detalle
  técnico completo de esta sesión y el handoff a la máquina personal.
- `docs/experiments/2026-09-21-fase1-n15-repeticion.md` — esqueleto del
  experimento (hipótesis, variables, método), resultados marcados como
  interrumpidos con los comandos exactos para retomar.
- `README.md` — sección nueva "Ecuación Personal" (antes ausente por
  completo pese a estar implementada desde la sesión previa), tabla de
  documentación de diseño con los docs arquitectónicos nuevos, variables de
  entorno de mitología/Ecuación Personal, conteo de tests actualizado
  (390→434).

**Commits:** `c646b5b`, `687423c`, y el commit de `README.md` de esta misma sesión.

---

## 8. Estado de tests

- Al iniciar esta sesión: 434 tests, 431 pasan, 1 falla (el de §1),
  2 skipped.
- Verificado tras cada cambio en los módulos tocados:
  `test_social.py` 117/117, `test_metrics.py` 29/29,
  `test_culture_r7.py` 8/8, `TestPerformance` 5/5 corridas consecutivas.
- **No se corrió la suite completa una vez más** tras los últimos cambios
  (`interaction.py` con overrides de env var, `run_ab_batch.py`) — costo de
  CPU incompatible con las corridas largas que ya estaban en marcha. Queda
  como primer paso de la próxima sesión, antes de considerar mergear a `main`.

---

## 9. Todo lo pendiente (para la próxima sesión, en la máquina personal)

### Prioridad alta (bloqueante para cerrar esta rama)
- Correr la suite completa de tests una vez más (última vez fue al
  comienzo de esta sesión) antes de proponer merge a `main`.

### Prioridad media
- **Terminar el A/B de Fase 1 con n=15** (`run_ab_batch.py`, comando en §5)
  y actualizar `docs/experiments/2026-09-21-fase1-n15-repeticion.md` con
  los resultados reales — decidir si la conclusión original ("sin efecto
  medible") se sostiene, se revisa, o sigue inconclusa.
- **Terminar el barrido de calibración de mitología** (baseline
  choque-solo vs. pesos reducidos, 1200 días, seed 42 — usar
  `MYTH_TRANSMISSION_COOPERACION_PURA`/`MYTH_TRANSMISSION_CONFLICTO_EXPLOTACION`
  en 0 para el baseline) y fijar `_MYTH_TRANSMISSION_INTENSITY` con el
  resultado, documentando la calibración en `docs/experiments/`.
- Investigar si el "Eco del Multiverso" (§6) está causalmente ligado a la
  sobre-cristalización — por ahora es solo correlación observada.

### Prioridad baja / explícitamente opcional
- Fase 3 del roadmap Ecuación Personal (observabilidad) — sigue sin
  iniciar, condicionada a que la repetición del A/B muestre impacto medible.
- `attributed_cause`/`moral_judgment` siguen sin ser leídos por
  `MentalVault.accumulate()` — sin cambios desde la sesión anterior.
- Investigar por qué los archivos de vault por tribu/persona se congelan
  tras el primer reclustering (§6) — cosmético, no afecta la simulación en
  sí, solo la observabilidad vía Obsidian.

### No es trabajo pendiente, es contexto para no repetir
- Esta máquina tiene 2 núcleos lógicos — cualquier corrida headless larga
  (>500 días o >10 semillas) es mejor lanzarla en una máquina con más
  núcleos, o aceptar varias horas de cómputo real.
- `data/metrics/ab_interpretive_fase1_n15_2026-09-21.jsonl` (parcial, 3-4
  líneas) quedó en esta máquina, gitignored — no se transfiere solo; en la
  máquina personal, `run_ab_batch.py --append` puede seguir sobre un
  archivo nuevo o sobre uno copiado manualmente si se quiere conservar.
