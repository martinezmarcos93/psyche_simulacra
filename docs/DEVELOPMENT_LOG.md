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
