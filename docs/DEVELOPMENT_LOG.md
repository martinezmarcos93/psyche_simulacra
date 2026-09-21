# Bitácora de desarrollo

Registro técnico sesión a sesión. No es un changelog de features (eso está en los
mensajes de commit) — es el registro de *qué se verificó, qué resultó, qué queda
pendiente*, para que la próxima sesión no tenga que re-derivar el contexto.

---

## 2026-09-21 — Consolidación post-`xperiment`: cierre de Fase 1, auditoría, documentación

**Punto de partida**: `xperimento-ps` (checkout separado, mismo remoto, rama
`xperiment`) tenía 12 commits sin fusionar por delante de `main`, implementando
la Fase 1 (`InterpretiveFilter`) y Fase 2 (`MentalVault`) del roadmap "Ecuación
Personal", ambas desactivadas por defecto y sin experimento A/B ejecutado nunca.

### Hecho

1. **Housekeeping de git**: fusión fast-forward de `xperiment` (y `culture`, que
   no aportaba nada nuevo) a `main`; borrado de ramas `culture`/`evolution`/
   `xperiment` (local y remoto, verificado que las tres estaban 100% contenidas
   en `main` antes de borrar); eliminación de la carpeta `xperimento-ps` local
   (verificado HEAD == punta ya mergeada, cero pérdida); descarte de un stash de
   ruido CRLF/LF pre-existente (confirmado contenido idéntico, no había trabajo
   real).
2. **Entorno**: creado `.venv` local (el proyecto vive en un disco NTFS/fuseblk
   sin bit de ejecución — hay que invocar `pip` como `python3 -m pip`, nunca el
   script `.venv/bin/pip` directamente).
3. **Experimento A/B de la Fase 1** (`scripts/ab_interpretive.py`, headless: sin
   BD/narrativa/Obsidian, ~0.5s/día simulado — mucho más rápido que el modo
   completo): 3 condiciones (OFF / filtro / filtro+vault) × 5 semillas (42-46) ×
   300 días, más una corrida adicional de 600 días para descartar efecto de
   "arranque lento" del vocabulario emergente. Ver
   `experiments/2026-09-21-fase1-ecuacion-personal.md` para el resultado
   completo — **resumen: el filtro NO produjo un aumento medible de divergencia
   cultural/conductual/arquetípica en ninguna de las métricas instrumentadas,
   con diferencias pareadas por semilla consistentemente dentro del ruido**.
4. **Completado el código de la Fase 1**: `attributed_cause` y `moral_judgment`
   del `PerceivedEvent` estaban declarados (`core/interface/perceived_event.py`)
   pero **nunca se llenaban en ningún punto del código** — solo `narrative_frame`
   tenía mecanismo de préstamo. Se implementó:
   - `attributed_cause` ← `PerceptionSystem.strongest_cause()` (nuevo método;
     consulta la asociación causal más fuerte que el propio agente ya formó vía
     `check_causal_bias`, umbral 0.40).
   - `moral_judgment` ← el `name` del `MythCrystal` de tipo `"mito_moral"` ya
     cristalizado cuyo `par` coincide con lo que se activó ese tick
     (`MythologyEngine.active_myths`, pasado como parámetro nuevo opcional a
     través de `Agent.decide_action()` → `_decide_via_collapse()` →
     `InterpretiveFilter.interpret()`).
   - Ninguno de los dos cambia ninguna métrica ya medida (`MentalVault.accumulate`
     no lee esos slots) — se verificó antes de decidir no re-correr el
     experimento completo por esto.
   - 6 tests nuevos en `tests/test_interpretive_filter.py` cubriendo présamo y
     no-préstamo de ambos slots.
5. **Test filosófico** (auditoría manual del roadmap, obligatoria antes de
   avanzar a Fase 2 — aunque Fase 2 ya estaba implementada, se auditó
   igual): se revisó línea por línea `interpretive_filter.py`, `mental_vault.py`,
   `neuron.py` y `collapse.py`. Ningún operador devuelve contenido simbólico
   directamente; todo préstamo está gateado por la existencia previa de
   vocabulario cristalizado en otro sistema. Ver `docs/EMERGENCE.md`.
6. **Suite completa de tests**: 427 tests, 426 pasan. Un test falla
   (`tests/test_culture_r7.py::TestMythCoverage::test_cobertura_mitica_rich_culture`)
   — **se confirmó que el fallo es preexistente** (falla igual con y sin los
   cambios de esta sesión, aislado con `git stash`).

   **Causa raíz encontrada y corregida**: `MythologyEngine.on_social_transmission()`
   —el método que hace avanzar la `coherencia` de un `ProtoMito` hacia la
   cristalización— está definido desde el commit `c3118ef` (muy anterior al
   Roadmap 7) pero **nunca fue llamado desde ningún punto del código**, ni
   siquiera desde `core/social/interaction.py`, pese a que el propio docstring
   del método dice "llamado por interaction.py cuando dos agentes comparten una
   experiencia emocional significativa". Verificado con un diagnóstico manual
   (500 días, seed 42, `rich_culture_100.yaml`): 3 proto-mitos se crean con
   normalidad, pero los tres quedan con `coherencia = 0.0` para siempre —
   **ningún `MythCrystal` de este sistema (N-dimensional, `ProtoMito`→
   `MythCrystal`, 5 tipos Campbell) pudo haber cristalizado jamás, en ninguna
   simulación de este proyecto, desde su implementación original.** El sistema
   de "Héroe vs Monstruo" (`get_myth_hero_monster`, más antiguo, sí visible en
   los vaults archivados) es un mecanismo distinto y no está afectado.

   **Corrección aplicada** (`core/social/interaction.py`,
   `resolve_encounter`, caso competencia-competencia / "choque violento"): se
   añadió la llamada `mythology_engine.on_social_transmission(collective_field)`
   en el caso de encuentro más intenso emocionalmente (elección conservadora —
   deliberadamente no se conectó en los otros 5 casos de encuentro para no
   arriesgar una cristalización demasiado frecuente sin validar el impacto en
   el resto de la suite; ver "Trabajo futuro" en el experimento). Se agregó
   `tests/test_social.py::test_choque_violento_transmite_al_proto_mito` como
   test de regresión explícito. Verificado: el test que fallaba ahora pasa
   (`1 passed in 256.66s`), y la suite `test_culture_r7.py` completa se corrió
   de nuevo para descartar efectos colaterales.
7. **Documentación arquitectónica nueva**: `docs/ARCHITECTURE.md`,
   `docs/AGENT_BRAIN.md`, `docs/ARCHETYPES.md`, `docs/MENTAL_VAULT.md`,
   `docs/EMERGENCE.md` — describen el sistema completo desde el tick hasta el
   mito, y trazan explícitamente qué está diseñado vs. qué emerge.
8. **Limitación arquitectónica documentada** (no un bug, una discrepancia
   README↔código): `MythologyEngine` es una única instancia global en
   `AgentCore`, no una por tribu como sugiere el README — ver `EMERGENCE.md` §5.

### Verificado

- Merge fast-forward limpio (`c0a8c2e..1678701`), sin conflictos.
- Los 6 tests nuevos de `attributed_cause`/`moral_judgment` pasan.
- El cambio de firma de `decide_action()`/`_decide_via_collapse()` es
  retrocompatible (`mythology_engine` opcional, default `None`) — no rompió
  ningún caller existente (`tests/test_quantum.py`, `tests/test_bug_fixes.py`).
- Comparación pareada por semilla (no solo promedios de grupo) para controlar el
  ruido entre corridas, siguiendo el propio diseño del arnés
  ("mismo seed → mismas condiciones iniciales").

### Resultado experimental (resumen — detalle en `experiments/`)

**Evidencia desfavorable a la hipótesis de la Fase 1** tal como está calibrada
hoy (peso del canal `interpretive_influence` = 0.15, 300-600 días, 100 agentes):
ninguna métrica de divergencia (arquetípica, conductual, o de campo) mostró un
efecto positivo robusto del filtro por encima del ruido entre semillas. Esto
**no invalida la implementación** (el test filosófico la aprueba) ni el diseño
conceptual — es evidencia de que, a esta escala de tiempo y con este peso de
canal, el efecto es indetectable o inexistente. Ver
`experiments/2026-09-21-fase1-ecuacion-personal.md` §Interpretación para las
hipótesis abiertas (peso de canal insuficiente, necesidad de más semillas para
poder estadístico, o que el efecto real esté en una dimensión no instrumentada).

### Pendiente al cierre de esta sesión

- Considerar si conviene conectar `on_social_transmission` también en otros
  casos de encuentro (`conflicto_explotacion`, `cooperacion_pura`) — se dejó
  fuera de alcance por precaución (riesgo de acelerar demasiado la
  cristalización sin más validación); requeriría repetir el experimento de
  robustez (`scripts/run_robustness.py`) para calibrar el ritmo resultante
  contra el objetivo original del Roadmap 7 (3000-6000 días → ≥3 mitos).
- Fase 3 del roadmap Ecuación Personal (observabilidad: tab "Mentes", métrica
  de coherencia individual en el dashboard) — no iniciada; es explícitamente
  opcional y de menor prioridad que la validación experimental (ya cerrada)
  según el orden de prioridades de esta sesión.
- No se hizo `git push` — instrucción explícita del usuario, commits solo
  locales.

---

## 2026-09-21 (continuación) — Modo autónomo: pendientes de prioridad media del handoff anterior

**Punto de partida**: repo re-clonado en una máquina nueva (mismo remoto,
`main` limpio en el commit `466ec65`), rama de trabajo
`feature/ecuacion-personal-continuacion` creada desde `main`. Objetivo:
resolver, en modo autónomo y sin pausar por aprobación intermedia, los tres
pendientes de prioridad media dejados en `handoffs/2026-09-21.md` §7.

### Hecho

1. **Entorno**: `.venv` con miniconda Python 3.9.12, dependencias instaladas
   vía el workaround de certificado CA de Avast (ver Ley Red-y-SSL del vault
   del estudio — no aplica a este proyecto personal, pero el mismo mecanismo
   de exportar el store de Windows a PEM funcionó igual).
2. **Baseline confirmado**: 431/434 tests pasan antes de tocar nada; 1 fallo
   (`TestPerformance::test_metricas_disponibles_tras_correr`, `ZeroDivisionError`
   intermitente en `SimulationClock.get_performance_metrics()` — 50 ticks
   headless pueden medir `elapsed_real == 0.0` en esta máquina). No es
   regresión de la sesión anterior, es dependiente de la velocidad del
   hardware. **Corregido** con un piso de `1e-6`s (commit `0bd0432`);
   verificado estable en 5 corridas consecutivas.
3. **Extendida `on_social_transmission`** (commit `a5f87e3`) a cooperación
   pura (intensity=0.25) y conflicto/explotación (intensity=0.5), además del
   choque violento ya conectado (intensity=1.0) — proporcional a la magnitud
   emocional ya codificada en cada rama de `resolve_encounter`. No se tocó
   manipulación (fuera de alcance, contaminación afectiva ambigua). 2 tests
   nuevos verifican la intensidad relativa; `test_social.py` 117/117 y
   `test_culture_r7.py` 8/8 (incluido el test de cobertura mítica) pasan.
4. **Bug sistémico encontrado y corregido**: cualquier simulación headless
   suficientemente larga crashea con `UnicodeEncodeError` al imprimir el
   emoji narrativo de objetos sagrados/deidades en una consola Windows
   cp1252. Reproducido con `scripts/myth_calibration.py` (script nuevo, ver
   punto 6). **Corregido** (commit `b82fee1`) forzando UTF-8 en
   stdout/stderr al inicio de todos los entry points reales: `main.py`,
   `run_simulation.py`, `run_overnight.py`, `run_robustness.py`,
   `ab_interpretive.py`, `myth_calibration.py`.
5. **Nueva métrica `behavioral_intra_tribe_dispersion`** (commit `575a9d8`):
   entropía normalizada de la acción conductual *dentro* de cada tribu,
   contraparte de `behavioral_kl_mean` (que solo mide *entre* tribus).
   Resuelve la ambigüedad que dejó abierta el experimento A/B de la Fase 1:
   si el filtro aumenta idiosincrasia individual sin separar tribus entre sí,
   ahora es visible. Expuesta como `behavioral_intra_q4` en
   `ab_interpretive.py`. 5 tests nuevos, `test_metrics.py` 29/29 pasan.
6. **Arnés `scripts/myth_calibration.py`** (commit `f13d0ee`): mide, por
   semilla, día de primera cristalización y total de `MythCrystal` al final,
   para calibrar la extensión del punto 3 contra el objetivo original del
   Roadmap 7 (3000-6000 días → ≥3 mitos/leyendas) sin adivinar a ciegas.

### En curso al momento de escribir esta entrada

- **Calibración de mitología**: corrida headless en background
  (`scripts/myth_calibration.py --seeds 42 --days 600` como smoke test;
  corridas más largas de 4000-6000 días planeadas a continuación). Resultado
  pendiente de completar — se documentará en `docs/experiments/` cuando
  termine.
- **Repetición del experimento A/B de la Fase 1 con más poder estadístico**:
  batch headless en background, 20 semillas (42-61) × 3 condiciones (OFF /
  filtro / filtro+vault) × 300 días, ya incluyendo `behavioral_intra_q4`.
  Reemplaza la corrida original de n=5 semillas por la potencia estadística
  que el handoff anterior pedía (n≥15-20) antes de descartar la hipótesis de
  la Fase 1 con más confianza. Resultado pendiente — se documentará en
  `docs/experiments/` cuando termine, actualizando
  `2026-09-21-fase1-ecuacion-personal.md` con la conclusión revisada.

### Cierre de esta sesión (máquina de oficina) — handoff a máquina personal

Autorizado explícitamente por el usuario (`autorizo el push`): rama
`feature/ecuacion-personal-continuacion` pusheada a `origin` (11 commits,
`a5f87e3`..`90b4391`). `main` no se tocó.

Ambas corridas largas (calibración de mitología, repetición A/B n=15) se
**interrumpieron**: la máquina de oficina tiene solo 2 núcleos lógicos y cada
corrida de 300 días tarda ~470-500s (no los ~150s de la sesión original) —
proyectando >5h para el batch completo, inviable en esa máquina. Se
reemplazó el bash one-off no versionado por `scripts/run_ab_batch.py`
(commit `1dda8be`), portable y resumible con `--append`, para continuar en
la máquina personal:

```
python scripts/run_ab_batch.py --seeds 42-56 --days 300 \
    --output data/metrics/ab_interpretive_fase1_n15_2026-09-21.jsonl
```

**Hallazgo adicional durante la espera** (inspección manual del vault de
Obsidian generado por el smoke test de `myth_calibration.py`, 600 días,
seed 42): confirma en formato narrativo la sobre-cristalización ya medida
numéricamente (3 mitos para el día 7: `Mito_moral_dia2`, `Cosmogonia_dia3`,
`Mito_moral_dia7`). Más interesante — la `Cronica.md` exportada al día 500
muestra un patrón saturado y perfectamente repetido: **"Eco del
Multiverso"**, el arquetipo `muerte` resonando a intensidad máxima (1.00)
simultáneamente en 14 tribus, idéntico día tras día (497-500). El mecanismo
(`core/liminal/collective_echo.py`) es un feedback positivo real y
diseñado: un símbolo que converge lo suficiente entre tribus se amplifica
globalmente, lo cual facilita que vuelva a converger. Hipótesis abierta (no
confirmada): la sobre-cristalización temprana de la extensión de
`on_social_transmission` pudo haber sido la chispa que arrancó este loop de
monocultivo simbólico — otra señal a favor de que los pesos actuales
(commit `a5f87e3`) están mal calibrados, más allá del conteo de mitos.
También se observó que los archivos por tribu/persona/meta del vault se
congelan en el día ~30 (probablemente porque las tribus fundadoras se
disuelven en el primer reclustering del escenario y el sistema no genera
archivos nuevos para las tribus post-reclustering) — anotado como
limitación conocida, no investigado a fondo por estar fuera de alcance.

### Pendiente (para la sesión en la máquina personal)

- Terminar y documentar el batch A/B n=15 (`run_ab_batch.py`, arriba).
- Terminar el barrido de calibración de mitología (baseline choque-only vs.
  pesos reducidos, 1200 días, seed 42 — comando en
  `docs/experiments/` una vez se redacte ese documento) y fijar los pesos de
  `_MYTH_TRANSMISSION_INTENSITY` con el resultado, no a ciegas.
- Investigar si el "Eco del Multiverso" está relacionado causalmente con la
  sobre-cristalización de la extensión de mitología (correlación observada,
  no probada).
- Fase 3 del roadmap Ecuación Personal (observabilidad) sigue sin iniciar —
  condicionada a que la repetición del A/B muestre impacto medible.
- `attributed_cause`/`moral_judgment` siguen sin ser leídos por
  `MentalVault.accumulate()` — sin cambios desde la sesión anterior.
