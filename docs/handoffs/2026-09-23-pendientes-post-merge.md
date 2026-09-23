# Handoff — 2026-09-23 (pendientes tras mergear todo a main)

Este documento existe porque `feature/ecuacion-personal-continuacion` se
mergeó a `main` con trabajo experimental sin cerrar (decisión explícita del
usuario: mergear igual, dejar anotado qué falta). El detalle completo del
trabajo de esa rama está en `docs/handoffs/2026-09-21-continuacion.md` — acá
solo el resumen accionable para retomar desde `main`.

## Qué quedó sin terminar (ninguno es un bug — son experimentos de calibración)

### 1. Repetición del A/B de Fase 1 con n=15 semillas
Interrumpida por hardware (máquina de 2 núcleos). Comando exacto para
retomar (es resumible, `--append` salta lo ya calculado):

```
python scripts/run_ab_batch.py --seeds 42-56 --days 300 \
    --output data/metrics/ab_interpretive_fase1_n15_2026-09-21.jsonl
```

Actualizar después `docs/experiments/2026-09-21-fase1-n15-repeticion.md` con
los resultados reales y decidir si la conclusión original de la Fase 1
("sin efecto medible") se sostiene, se revisa, o sigue inconclusa.

### 2. Barrido de calibración de mitología
Comparar baseline (choque-solo, con `MYTH_TRANSMISSION_COOPERACION_PURA=0`
y `MYTH_TRANSMISSION_CONFLICTO_EXPLOTACION=0`) contra los pesos reducidos,
1200 días, seed 42. El hallazgo que motiva esto: el smoke test de
`scripts/myth_calibration.py` mostró sobre-cristalización temprana
(primera cristalización día 2, 3 mitos totales para el día 600 — el
objetivo original era ese mismo total recién entre los días 3000-6000).
Los pesos en `core/social/interaction.py::_MYTH_TRANSMISSION_INTENSITY`
**no se ajustaron a ciegas** — necesitan este barrido primero.

### 3. "Eco del Multiverso" — hipótesis sin confirmar
Observado inspeccionando el vault de Obsidian de una corrida de 500 días:
el arquetipo `muerte` resonando a intensidad máxima simultáneamente en 14
tribus, idéntico día tras día (497-500) — un feedback positivo real y
diseñado (`core/liminal/collective_echo.py`) que converge lo suficiente
entre tribus como para amplificarse globalmente. Hipótesis abierta: la
sobre-cristalización temprana del punto 2 pudo haber sido la chispa que
arrancó este monocultivo simbólico. Es correlación observada, no causalidad
confirmada — requiere investigación aparte.

## Qué NO quedó pendiente (ya resuelto en este merge)

- `ZeroDivisionError` intermitente en `SimulationClock.get_performance_metrics`
  — arreglado, verificado corriendo el test específico tras el merge.
- `UnicodeEncodeError` en consola Windows cp1252 para corridas headless
  largas — arreglado (UTF-8 forzado en stdout/stderr de todos los entry
  points).
- `on_social_transmission` ahora conecta cooperación pura y
  conflicto/explotación además de choque violento, con intensidad relativa
  calibrable por env var.
- `behavioral_intra_tribe_dispersion` — métrica nueva ya instrumentada y
  expuesta como `behavioral_intra_q4` en `ab_interpretive.py`.

## Limitación cosmética conocida, no bloqueante

Los archivos de vault por tribu/persona (`vault/Tribus/`, `vault/Personas/`)
se congelan tras el primer reclustering (día ~30, `DAYS_UNTIL_CLUSTERING`)
— las tribus fundadoras se disuelven y el sistema no genera archivos nuevos
para las tribus que emergen después. `Cronica.md` sí sigue actualizándose
con los nombres nuevos. No afecta la simulación, solo la observabilidad vía
Obsidian. No investigado a fondo.
